"""
NotebookLM Automation Module
Part of DeepDiver - NotebookLM Podcast Automation System

This module handles browser automation for NotebookLM interactions,
including login, document upload, podcast generation, and file management.

Assembly Team: Jerry ⚡, Nyro ♠️, Aureon 🌿, JamAI 🎸, Synth 🧵
"""

import asyncio
import logging
import os
import re
import shutil
import subprocess
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

import yaml
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from .outline import plan_is_empty, record_proceed, save_feedback, save_outline
from .studio_artifacts import (
    ARTIFACT_CARD_SELECTOR,
    ARTIFACT_TYPES,
    GENERATING_CARD_MARKER,
    PENDING_REVIEW_MARKER,
    PLAN_SELECTOR,
    REVIEW_BUTTON_SELECTOR,
    completed_card_selectors,
    family_label_from_icon,
    get_artifact_spec,
    normalize_artifact_format,
    normalize_artifact_type,
    normalize_report_template,
)


# Map language inputs to NotebookLM display text (with regional variants).
# Shared by every Studio customization dialog.
LANGUAGE_DISPLAY_MAP = {
    'english': 'English',
    'spanish': 'español',
    'french': 'français (Canada)',  # Use Canadian French variant
    'german': 'Deutsch',
    'portuguese': 'português',
    'italian': 'italiano',
    'japanese': '日本語',
    'korean': '한국어',
    'chinese': '中文',
    'hindi': 'हिन्दी',
    'arabic': 'العربية',
    'russian': 'русский',
    'danish': 'dansk',
    'dutch': 'Nederlands',
    'finnish': 'suomi',
    'czech': 'čeština'
}


# notebooklm.google.com now redirects to notebook.google.com (Gemini Notebook
# rebrand); both hosts serve the same app.
NOTEBOOKLM_HOSTS = ('notebooklm.google.com', 'notebook.google.com')


def _is_notebooklm_host(url: Optional[str]) -> bool:
    from urllib.parse import urlparse
    try:
        return urlparse(url or '').hostname in NOTEBOOKLM_HOSTS
    except Exception:
        return False


def _is_notebook_url(url: Optional[str]) -> bool:
    from urllib.parse import urlparse
    return _is_notebooklm_host(url) and urlparse(url or '').path.startswith('/notebook/')


def _is_google_signin_url(url: Optional[str]) -> bool:
    from urllib.parse import urlparse
    try:
        return urlparse(url or '').hostname == 'accounts.google.com'
    except Exception:
        return False


def source_url_key(url: Optional[str]) -> str:
    """One key for the forms a source URL takes. Gemini Notebook titles a
    YouTube source it could not import with https://www.youtube.com/watch?v=<id>
    even when https://youtu.be/<id> was given (2026-10-15), so both map to yt:<id>."""
    from urllib.parse import urlparse, parse_qs
    u = (url or '').strip()
    try:
        parsed = urlparse(u)
        host = (parsed.hostname or '').lower()
        if host.startswith('www.'):
            host = host[4:]
        if host.startswith('m.'):
            host = host[2:]
        if host == 'youtu.be' and parsed.path.strip('/'):
            return 'yt:' + parsed.path.strip('/').split('/')[0]
        if host in ('youtube.com', 'music.youtube.com'):
            vid = parse_qs(parsed.query).get('v', [''])[0]
            if vid:
                return 'yt:' + vid
            if parsed.path.startswith(('/shorts/', '/live/')):
                return 'yt:' + parsed.path.split('/')[2]
        if host:
            return f"{host}{parsed.path.rstrip('/')}" + (f"?{parsed.query}" if parsed.query else '')
    except Exception:
        pass
    return u.rstrip('/')


def match_source_titles(titles: List[str], wanted: str) -> List[int]:
    """Positions of the source rows a removal names: the exact title first, then
    the same URL in another form (a YouTube source is titled with its watch URL
    whatever form was given). Several matches are returned as they are, so the
    caller can refuse to guess."""
    want = (wanted or '').strip()
    exact = [i for i, t in enumerate(titles) if (t or '').strip() == want]
    if exact:
        return exact
    key = source_url_key(want)
    if want.startswith(('http://', 'https://')):
        return [i for i, t in enumerate(titles) if source_url_key((t or '').strip()) == key]
    return []


def card_is_held(card: Dict[str, Any], entries: List[Dict[str, Any]]) -> bool:
    """Does a manifest entry already hold this Studio card?

    By the card's id. Only a card or an entry with no id falls back to its
    title, since Gemini Notebook can give two cards one title.
    """
    card_id = card.get('artifact_id')
    for entry in entries:
        entry_id = entry.get('artifact_id')
        if card_id and entry_id:
            if card_id == entry_id:
                return True
        elif card.get('title') and card.get('title') == entry.get('title'):
            return True
    return False


def match_studio_cards(cards: List[Dict[str, Any]], ref: str) -> List[Dict[str, Any]]:
    """The Studio cards an iterate names: by artifact id, else by exact title."""
    want = (ref or '').strip()
    by_id = [c for c in cards if c.get('artifact_id') and c.get('artifact_id') == want]
    if by_id:
        return by_id
    return [c for c in cards if (c.get('title') or '').strip() == want]


BLANK_TAB_URLS = ('about:blank', 'chrome://newtab/', 'chrome://new-tab-page/')

# Playwright attaches to every tab when it connects over CDP, and one tab whose
# page stopped answering stalls that forever (2026-10-15: an AI Studio app tab
# in DeepDiver's Chrome). Give up after this long and say why.
CDP_ATTACH_TIMEOUT_MS = 30000

# A generation that started shows a generating card within seconds. With no
# such card after this long, nothing is being generated (2026-10-29: 902 s and
# 1802 s spent waiting on generations that never started).
# STUDIO_SETTINGS.<family>.generation_start_timeout overrides it.
GENERATION_START_TIMEOUT_S = 120
# A tile's Customize dialog normally opens within a second (0.3 to 0.6 s, 2026-11-05).
TILE_DIALOG_WAIT_MS = 8000


def wake_background_tabs(cdp_url: str, pause: float = 1.0) -> int:
    """Bring each tab to the front once, then the first one again, through the
    DevTools HTTP endpoint (/json/activate). Chrome freezes background tabs, and
    a frozen tab never answers Playwright's attach (2026-10-16: an Author's Desk
    tab and a New Tab, both woken this way). Returns how many tabs it touched.
    """
    base = cdp_url.rstrip('/')
    try:
        pages = [t for t in requests.get(f"{base}/json", timeout=3).json() if t.get('type') == 'page']
    except Exception:
        return 0
    for tab in pages + pages[:1]:
        try:
            requests.get(f"{base}/json/activate/{tab['id']}", timeout=3)
        except Exception:
            pass
        time.sleep(pause)
    return len(pages)


def keyring_prompt_message(processes: List[Any], window_titles: List[str]) -> Optional[str]:
    """What to tell a person when a GNOME keyring prompt holds Chrome, or None.

    After a reboot Chrome waits behind "Unlock Login Keyring" (gcr-prompter) to
    decrypt its stored sign-in, and only a person can type that password
    (gaia, 2026-10-25). `processes` are (pid, name) pairs.
    """
    pids = [str(pid) for pid, name in processes if name == 'gcr-prompter']
    windows = [w for w in window_titles if re.search(r'unlock .*keyring|keyring', w or '', re.I)]
    if not pids and not windows:
        return None
    where = f"gcr-prompter, pid {', '.join(pids)}" if pids else f"window \"{windows[0]}\""
    return (f"A GNOME keyring prompt is open on the desktop ({where}). Chrome waits behind it to "
            "decrypt its stored sign-in, and only a person can unlock it: type the login keyring "
            "password in the \"Unlock Login Keyring\" window, then retry.")


def find_keyring_prompt() -> Optional[str]:
    """Look for a keyring prompt on this host: a gcr-prompter process, or its window."""
    processes = []
    try:
        for entry in os.listdir('/proc'):
            if entry.isdigit():
                try:
                    with open(f'/proc/{entry}/comm') as fh:
                        processes.append((int(entry), fh.read().strip()))
                except OSError:
                    continue
    except OSError:
        pass
    titles = []
    if shutil.which('wmctrl'):
        try:
            env = dict(os.environ)
            env.setdefault('DISPLAY', ':0')
            out = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True, timeout=3, env=env).stdout
            titles = [line.split(None, 3)[3] for line in out.splitlines() if len(line.split(None, 3)) == 4]
        except Exception:
            pass
    return keyring_prompt_message(processes, titles)


def describe_attach_timeout(cdp_url: str) -> str:
    """What to tell a person when Playwright cannot attach: a keyring prompt when one is open,
    else the open tabs, since one of them hangs."""
    keyring = find_keyring_prompt()
    if keyring:
        return keyring
    try:
        tabs = requests.get(f"{cdp_url.rstrip('/')}/json", timeout=3).json()
        urls = [t.get('url', '') for t in tabs if t.get('type') == 'page']
    except Exception:
        urls = []
    listed = '; '.join(u[:80] for u in urls) or 'the tab list did not answer either'
    return (f"Chrome did not let DeepDiver attach within {CDP_ATTACH_TIMEOUT_MS // 1000} s. "
            f"A tab whose page stopped answering blocks it. Open tabs: {listed}. "
            "Reload or close the tab that hangs (it may be a person's own work), then retry.")


def pick_deepdiver_page(pages: List[Any]) -> Optional[Any]:
    """The tab DeepDiver may drive: one already on Gemini Notebook, else a blank one.

    Never a tab on another site. The Chrome on 9222 is also a person's browser
    (on 2026-10-15 it held AI Studio, an episode room and a notebook), and
    taking the first tab would navigate their page away.
    """
    for page in pages:
        if _is_notebooklm_host(getattr(page, 'url', '')):
            return page
    for page in pages:
        if (getattr(page, 'url', '') or '') in BLANK_TAB_URLS:
            return page
    return None


_DAILY_LIMIT_RE = re.compile(r"You have reached your daily ([A-Za-z][A-Za-z ]{0,40}?) limit", re.I)


def daily_limit_message(page_text: Optional[str]) -> Optional[str]:
    """Gemini Notebook's own words when a family's daily quota is spent, or None.

    Seen 2026-10-15 on an Infographic tile: no customization dialog opens, the
    page says "You have reached your daily Infographic limit.", and nothing is
    generated.
    """
    m = _DAILY_LIMIT_RE.search(page_text or "")
    return m.group(0) if m else None


def _is_signed_out_url(url: Optional[str]) -> bool:
    """True for the pages a signed-out profile lands on.

    Google's sign-in (accounts.google.com), and the Gemini Notebook landing
    page /trynow, which a signed-out profile is sent to instead of the notebook
    list (2026-10-09: a cloned profile opened notebook.google.com/trynow).
    """
    from urllib.parse import urlparse
    if _is_google_signin_url(url):
        return True
    try:
        return _is_notebooklm_host(url) and urlparse(url or '').path.startswith('/trynow')
    except Exception:
        return False


# The button that opens the add-source dialog. Never a bare
# button:has-text("Add"): the header's "Create notebook" button renders its
# icon ligature as text ("add_2 Create notebook"), so that substring match
# creates a new notebook instead (three empty notebooks, 2026-10-06).
ADD_SOURCE_BUTTON_SELECTORS = [
    'button[aria-label="Add source"]',
    'button.add-source-button',
    'button[mattooltip="Add source"]',
    'button[mat-stroked-button]:text-is("Add")',
    'button:has-text("+ Add")',
]


# ═══════════════════════════════════════════════════════════════
# CONFIG FILE DISCOVERY
# ♠️ Nyro: Multi-location config discovery for flexible deployment
# ═══════════════════════════════════════════════════════════════

def find_config_file(config_path: str = None) -> Optional[str]:
    """
    Find the DeepDiver configuration file by checking multiple locations.

    Priority order:
    1. Explicit path provided (if given)
    2. Current working directory: ./deepdiver/deepdiver.yaml
    3. User config directory: ~/.config/deepdiver/config.yaml
    4. User home directory: ~/deepdiver/deepdiver.yaml
    5. Package installation directory
    6. Return None (system will use defaults)

    Args:
        config_path: Optional explicit path to config file

    Returns:
        Path to config file if found, None otherwise

    Examples:
        >>> find_config_file()  # Auto-discover
        '/home/user/.config/deepdiver/config.yaml'

        >>> find_config_file('/custom/path.yaml')  # Explicit path
        '/custom/path.yaml'
    """
    search_paths = []

    # 1. Explicit path (if provided and exists)
    if config_path:
        if os.path.exists(config_path):
            return config_path
        # If explicit path doesn't exist, still add to search list for error reporting
        search_paths.append(config_path)

    # 2. Current working directory
    search_paths.append("deepdiver/deepdiver.yaml")
    search_paths.append("./deepdiver/deepdiver.yaml")

    # 3. User config directory (XDG Base Directory specification)
    config_dir = os.path.expanduser("~/.config/deepdiver")
    search_paths.append(os.path.join(config_dir, "config.yaml"))
    search_paths.append(os.path.join(config_dir, "deepdiver.yaml"))

    # 4. User home directory
    home_dir = os.path.expanduser("~")
    search_paths.append(os.path.join(home_dir, "deepdiver", "deepdiver.yaml"))
    search_paths.append(os.path.join(home_dir, ".deepdiver.yaml"))

    # 5. Package installation directory
    try:
        # Get the directory where this module is installed
        module_dir = os.path.dirname(os.path.abspath(__file__))
        search_paths.append(os.path.join(module_dir, "deepdiver.yaml"))
        search_paths.append(os.path.join(module_dir, "..", "deepdiver", "deepdiver.yaml"))
    except:
        pass

    # Search all paths
    for path in search_paths:
        expanded_path = os.path.expanduser(path)
        if os.path.exists(expanded_path) and os.path.isfile(expanded_path):
            return expanded_path

    # No config file found
    return None


# ═══════════════════════════════════════════════════════════════
# CDP URL RESOLUTION - Chrome DevTools Protocol
# ♠️ Nyro: Three-tier priority chain for multi-network support
# ═══════════════════════════════════════════════════════════════

def get_cdp_url(override: str = None, config_path: str = "deepdiver/deepdiver.yaml") -> str:
    """
    Get CDP (Chrome DevTools Protocol) URL using priority chain

    Priority order:
    1. override parameter (highest - explicit function call)
    2. DEEPDIVER_CDP_URL environment variable (session-specific)
    3. CDP_URL from config file (persistent user config)
    4. http://localhost:9222 (fallback default)

    Args:
        override: Explicit CDP URL (e.g., from --cdp-url flag)
        config_path: Path to configuration file

    Returns:
        CDP URL string

    Examples:
        # Command-line override (highest priority)
        get_cdp_url('http://192.168.1.100:9222')

        # Environment variable
        export DEEPDIVER_CDP_URL=http://10.0.0.5:9222
        get_cdp_url()  # → http://10.0.0.5:9222

        # Config file
        # deepdiver.yaml contains: CDP_URL: http://server:9222
        get_cdp_url()  # → http://server:9222

        # Fallback
        get_cdp_url()  # → http://localhost:9222
    """
    # Priority 1: Explicit override parameter
    if override:
        return override

    # Priority 2: Environment variable
    env_cdp = os.environ.get('DEEPDIVER_CDP_URL')
    if env_cdp:
        return env_cdp

    # Priority 3: Config file (with smart discovery)
    found_config = find_config_file(config_path)
    if found_config:
        try:
            with open(found_config, 'r') as f:
                config = yaml.safe_load(f)
                if config and 'BROWSER_SETTINGS' in config:
                    cdp_url = config['BROWSER_SETTINGS'].get('cdp_url')
                    if cdp_url:
                        return cdp_url
        except Exception:
            pass  # Fall through to default

    # Priority 4: Default localhost (Chrome DevTools Protocol standard port)
    return 'http://localhost:9222'


# ═══════════════════════════════════════════════════════════════
# CHROME CDP HELPER FUNCTIONS
# ♠️🌿🎸🧵 G.Music Assembly - Auto-launch Chrome for init
# ═══════════════════════════════════════════════════════════════

def find_chrome_executable() -> Optional[str]:
    """
    Find Chrome/Chromium executable on the system

    Returns:
        str: Chrome command name, or None if not found
    """
    candidates = ['google-chrome', 'chromium', 'chromium-browser', 'chrome']
    for cmd in candidates:
        if shutil.which(cmd):
            return cmd
    return None


def check_chrome_cdp_running(cdp_url: str = 'http://localhost:9222') -> bool:
    """
    Check if Chrome CDP is running at specified URL

    Args:
        cdp_url: CDP URL to check (default: http://localhost:9222)

    Returns:
        bool: True if Chrome CDP is accessible, False otherwise
    """
    try:
        # Extract host and port from CDP URL
        if '://' in cdp_url:
            cdp_url = cdp_url.split('://')[1]

        # Handle localhost vs IP
        if cdp_url.startswith('localhost:'):
            port = cdp_url.split(':')[1]
            test_url = f'http://localhost:{port}/json/version'
        else:
            test_url = f'http://{cdp_url}/json/version'

        response = requests.get(test_url, timeout=2)
        return response.status_code == 200
    except:
        return False


def get_cdp_version_info(cdp_url: str = 'http://localhost:9222') -> Optional[Dict[str, Any]]:
    """
    Probe the CDP /json/version endpoint and return its payload.

    Unlike check_chrome_cdp_running(), this returns the actual browser
    identity (Browser, Protocol-Version, webSocketDebuggerUrl) so callers
    can report real CDP health instead of assuming it.

    Returns:
        Dict with the /json/version payload, or None if CDP is unreachable.
    """
    try:
        base = cdp_url.rstrip('/')
        if not base.startswith('http'):
            base = f'http://{base}'
        response = requests.get(f'{base}/json/version', timeout=3)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None


def clone_chrome_profile(source_profile: str,
                         profile_root: str = None,
                         dest_dir: str = None) -> Optional[str]:
    """
    Clone an authenticated Chrome profile into a disposable user-data-dir.

    Copies 'Local State' plus the named profile directory (e.g. 'Profile 3')
    so automation can reuse the login WITHOUT touching the live profile.

    Args:
        source_profile: Profile directory name inside the profile root
                        (e.g. 'Default', 'Profile 3')
        profile_root: Chrome config root (default: ~/.config/google-chrome)
        dest_dir: Destination user-data-dir (default: temp dir)

    Returns:
        Path to the cloned user-data-dir, or None on failure.
    """
    try:
        if profile_root is None:
            profile_root = os.path.expanduser('~/.config/google-chrome')

        local_state = os.path.join(profile_root, 'Local State')
        profile_dir = os.path.join(profile_root, source_profile)

        if not os.path.isfile(local_state) or not os.path.isdir(profile_dir):
            return None

        if dest_dir is None:
            import tempfile
            dest_dir = tempfile.mkdtemp(prefix='deepdiver-chrome-')
        else:
            if os.path.exists(dest_dir):
                shutil.rmtree(dest_dir)
            os.makedirs(dest_dir, exist_ok=True)

        shutil.copy2(local_state, os.path.join(dest_dir, 'Local State'))
        shutil.copytree(profile_dir, os.path.join(dest_dir, source_profile))
        return dest_dir
    except Exception:
        return None


# DeepDiver's own Chrome home. A person signs in to Google here once, and every
# later launch reuses it. Cloning a profile into a fresh folder on each launch
# did not carry the Google session (2026-10-09), so each run asked for a new
# sign-in.
DEFAULT_USER_DATA_DIR = os.path.expanduser('~/.chrome-deepdiver')


def _user_data_dir_in_use(user_data_dir: str) -> bool:
    """True when a Chrome holds this user-data-dir (its SingletonLock exists)."""
    return os.path.lexists(os.path.join(user_data_dir, 'SingletonLock'))


def adopt_user_data_dir(source_dir: str, dest_dir: str = None) -> Optional[str]:
    """
    Move a user-data-dir that is already signed in to Google into DeepDiver's
    home, so later launches reuse that sign-in.

    Refuses (returns None) when the source is not a Chrome user-data-dir, when
    a Chrome still holds it, or when the destination already exists. Nothing
    is overwritten or merged.
    """
    dest_dir = os.path.expanduser(dest_dir or DEFAULT_USER_DATA_DIR)
    source_dir = os.path.expanduser(source_dir)
    if not os.path.isfile(os.path.join(source_dir, 'Local State')):
        return None
    if _user_data_dir_in_use(source_dir):
        return None
    if os.path.exists(dest_dir):
        return None
    os.makedirs(os.path.dirname(dest_dir) or '.', exist_ok=True)
    shutil.move(source_dir, dest_dir)
    return dest_dir


def resolve_launch_dir(user_data_dir: str = None, clone_from_profile: str = None,
                       profile_root: str = None, fresh: bool = False) -> Optional[str]:
    """
    Decide which user-data-dir a launch uses, seeding it from a profile only
    when it does not exist yet.

    - fresh: clone into a new temporary folder (the old behaviour).
    - otherwise the folder is user_data_dir, or DeepDiver's home. If it holds a
      'Local State' it is reused as it is, signed-in session included. If not,
      and a profile to clone is named, it is seeded from that profile once.
    """
    if fresh and clone_from_profile:
        return clone_chrome_profile(clone_from_profile, profile_root=profile_root)
    target = os.path.expanduser(user_data_dir or DEFAULT_USER_DATA_DIR)
    if os.path.isfile(os.path.join(target, 'Local State')):
        return target
    if clone_from_profile:
        if os.path.exists(target) and os.listdir(target):
            return None  # a non-empty folder that is not a Chrome home: never replaced
        return clone_chrome_profile(clone_from_profile, profile_root=profile_root,
                                    dest_dir=target)
    return target


async def _probe_signed_in(cdp_url: str) -> Optional[bool]:
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(cdp_url, timeout=CDP_ATTACH_TIMEOUT_MS)
        try:
            context = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = await context.new_page()
            try:
                await page.goto('https://notebook.google.com/', timeout=30000)
                try:
                    await page.wait_for_load_state('load', timeout=10000)
                except Exception:
                    pass
                return not _is_signed_out_url(page.url)
            finally:
                await page.close()
        finally:
            await browser.close()


def check_signed_in(cdp_url: str = 'http://localhost:9222') -> Optional[bool]:
    """
    Is the Chrome on this CDP address signed in to Gemini Notebook?

    Opens the notebook home in a new tab, reads where it lands, and closes
    that tab. True when it stays on the notebook list, False when it lands on
    Google's sign-in or /trynow, None when CDP does not answer.
    """
    if not check_chrome_cdp_running(cdp_url):
        return None
    try:
        return asyncio.run(_probe_signed_in(cdp_url))
    except Exception:
        return None


def launch_chrome_cdp(port: int = 9222, user_data_dir: str = None,
                      profile_directory: str = None,
                      clone_from_profile: str = None,
                      profile_root: str = None,
                      display: str = None,
                      fresh: bool = False) -> bool:
    """
    Launch Chrome with CDP enabled.

    Launching from SSH/tmux contexts fails without explicit X env, so this
    passes DISPLAY/XAUTHORITY through when available. The debug address is
    bound to 127.0.0.1 to keep CDP private to the host.

    Args:
        port: CDP port number (default: 9222)
        user_data_dir: Chrome user data directory
        profile_directory: --profile-directory value inside user_data_dir
                           (e.g. 'Profile 3')
        clone_from_profile: Seed DeepDiver's home (or user_data_dir) from this
                            profile when that folder does not exist yet. An
                            existing home is reused as it is, sign-in included.
        profile_root: Chrome config root for cloning
                      (default: ~/.config/google-chrome)
        display: X display to use (default: existing $DISPLAY or ':0')
        fresh: Clone into a new temporary folder instead of DeepDiver's home
               (a fresh clone is not signed in to Google)

    Returns:
        bool: True if Chrome launched and CDP answers, False otherwise
    """
    chrome_cmd = find_chrome_executable()
    if not chrome_cmd:
        return False

    resolved = resolve_launch_dir(user_data_dir, clone_from_profile,
                                  profile_root=profile_root, fresh=fresh)
    if not resolved:
        return False
    user_data_dir = resolved
    if clone_from_profile and not profile_directory and \
            os.path.isdir(os.path.join(user_data_dir, clone_from_profile)):
        profile_directory = clone_from_profile

    env = os.environ.copy()
    env.setdefault('DISPLAY', display or ':0')
    if display:
        env['DISPLAY'] = display
    xauthority = os.path.expanduser('~/.Xauthority')
    if os.path.exists(xauthority):
        env.setdefault('XAUTHORITY', xauthority)

    cmd = [
        chrome_cmd,
        '--remote-debugging-address=127.0.0.1',
        f'--remote-debugging-port={port}',
        f'--user-data-dir={user_data_dir}',
    ]
    if profile_directory:
        cmd.append(f'--profile-directory={profile_directory}')
    # A cloned or fresh user-data-dir has no 'First Run' sentinel; without
    # these flags Chrome opens its Terms of Service window and the DevTools
    # server never starts.
    cmd.append('--no-first-run')
    # Keep background tabs awake: a frozen tab stops Playwright from attaching
    # (2026-10-16). These are the flags Playwright itself passes when it launches.
    cmd.append('--disable-renderer-backgrounding')
    cmd.append('--disable-background-timer-throttling')
    cmd.append('--disable-backgrounding-occluded-windows')
    cmd.append('--no-default-browser-check')
    cmd.append('--new-window')
    cmd.append('about:blank')

    try:
        subprocess.Popen(cmd, env=env,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Wait for Chrome to start
        time.sleep(3)
        return check_chrome_cdp_running(f'http://localhost:{port}')
    except Exception:
        return False


class NotebookLMAutomator:
    """
    Main automation class for NotebookLM interactions.
    
    Handles browser automation, authentication, document upload,
    podcast generation, and file management through Playwright.
    """
    
    def __init__(self, config_path: str = "deepdiver/deepdiver.yaml", cdp_url_override: str = None,
                 session_tracker=None):
        """
        Initialize the NotebookLM automator with configuration.

        Args:
            config_path: Path to configuration file
            cdp_url_override: Optional CDP URL override (highest priority)
            session_tracker: Optional SessionTracker instance so generation
                             and resume flows can record notebook metadata.
                             Always defined on the instance (None when absent).
        """
        # Set up logger FIRST so other methods can use it
        self.logger = self._setup_logging()

        self.config_path = config_path
        self.config = self._load_config(config_path)
        self.session_tracker = session_tracker
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.last_source_errors: List[Dict[str, str]] = []
        self.playwright = None
        self._connected_over_cdp = False
        self._owns_context = False
        self._owns_page = False

        # NotebookLM specific settings
        self.base_url = self.config.get('NOTEBOOKLM_SETTINGS', {}).get('base_url', 'https://notebooklm.google.com')

        # Browser settings - Use CDP URL priority chain
        self.cdp_url = get_cdp_url(override=cdp_url_override, config_path=config_path)
        self.user_data_dir = self.config.get('BROWSER_SETTINGS', {}).get('user_data_dir', '/tmp/chrome-deepdiver')
        self.headless = self.config.get('BROWSER_SETTINGS', {}).get('headless', False)

        # General timeout from browser settings (in seconds), converted to ms
        self.timeout = self.config.get('BROWSER_SETTINGS', {}).get('timeout', 30) * 1000

        self.logger.info("♠️🌿🎸🧵 NotebookLMAutomator initialized")
        self.logger.info(f"🔗 CDP URL: {self.cdp_url}")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file with smart discovery."""
        # Try to find config file in multiple locations
        found_config = find_config_file(config_path)

        if found_config:
            try:
                with open(found_config, 'r') as f:
                    config = yaml.safe_load(f)
                    self.logger.info(f"✅ Loaded configuration from: {found_config}")
                    return config if config else {}
            except yaml.YAMLError as e:
                self.logger.error(f"Error parsing configuration: {e}")
                return {}
        else:
            # No config file found - use defaults
            self.logger.info("📝 No configuration file found, using defaults")
            self.logger.info("💡 To create a config file, run: deepdiver init")
            return {}
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        logger = logging.getLogger('NotebookLMAutomator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def connect_to_browser(self) -> bool:
        """
        Connect to existing Chrome browser via Chrome DevTools Protocol.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.logger.info("🔗 Connecting to Chrome browser via CDP...")

            # Verify CDP actually answers before Playwright attaches, so the
            # failure message names the real problem (port down vs app state).
            version_info = get_cdp_version_info(self.cdp_url)
            if version_info:
                self.logger.info(f"✅ CDP endpoint live: {version_info.get('Browser', 'unknown browser')}")
            else:
                self.logger.error(f"❌ CDP endpoint not answering at {self.cdp_url}/json/version")
                self.logger.error("💡 Launch Chrome with: google-chrome --remote-debugging-port=9222")
                return False

            self.playwright = await async_playwright().start()

            # Connect to existing browser
            try:
                self.browser = await self.playwright.chromium.connect_over_cdp(
                    self.cdp_url, timeout=CDP_ATTACH_TIMEOUT_MS)
            except Exception as e:
                if not ('Timeout' in type(e).__name__ or 'Timeout' in str(e)):
                    raise
                # A frozen background tab is the usual cause: wake every tab once, try once more.
                woke = wake_background_tabs(self.cdp_url)
                self.logger.warning(f"⚠️ Attach timed out; brought {woke} tab(s) forward once to wake frozen ones, retrying")
                try:
                    self.browser = await self.playwright.chromium.connect_over_cdp(
                        self.cdp_url, timeout=CDP_ATTACH_TIMEOUT_MS)
                except Exception as e2:
                    if 'Timeout' in type(e2).__name__ or 'Timeout' in str(e2):
                        self.logger.error(f"❌ {describe_attach_timeout(self.cdp_url)}")
                        return False
                    raise
            self._connected_over_cdp = True
            
            # Get the first available context
            contexts = self.browser.contexts
            if contexts:
                self.context = contexts[0]
                self._owns_context = False
            else:
                self.context = await self.browser.new_context()
                self._owns_context = True
            
            # Drive a notebook tab or a blank one; never take over a tab on
            # another site. A tab opened here stays for the next command.
            pages = self.context.pages
            page = pick_deepdiver_page(pages)
            if page:
                self.page = page
                self._owns_page = False
            elif pages:
                self.page = await self.context.new_page()
                self._owns_page = False
            else:
                self.page = await self.context.new_page()
                self._owns_page = True
            
            self.logger.info("✅ Successfully connected to Chrome browser")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to browser: {e}")
            return False

    async def dismiss_rebrand_modal(self) -> bool:
        """
        Dismiss the blocking first-run/rebrand modal if present.

        NotebookLM may present as 'Gemini Notebook' behind a welcome modal
        ("NotebookLM is now Gemini Notebook" / "Let's go") whose backdrop
        intercepts pointer events: the create button stays visible while
        every click times out. Dismissing it must happen before concluding
        the automator is broken.

        Returns:
            bool: True if a modal was found and dismissed, False otherwise
        """
        if not self.page:
            return False

        confirm_selectors = [
            '.cdk-overlay-pane button:has-text("Let\'s go")',
            'button:has-text("Let\'s go")',
            '.cdk-overlay-pane button:has-text("Got it")',
            'button:has-text("Got it")',
            '.cdk-overlay-pane button:has-text("Continue")',
            'div[role="dialog"] button:has-text("Continue")',
        ]

        for selector in confirm_selectors:
            try:
                element = await self.page.query_selector(selector)
                if element and await element.is_visible():
                    self.logger.info(f"👋 Dismissing welcome/rebrand modal via: {selector}")
                    await element.click(force=True)
                    await self.page.wait_for_timeout(1000)
                    return True
            except Exception:
                continue

        return False

    async def find_open_notebook_page(self, notebook_id: str = None) -> Optional[Page]:
        """
        Find an already-open NotebookLM notebook tab in the live browser.

        When attached over CDP the user may already have the target notebook
        open; reusing that tab preserves its state instead of navigating the
        first page away from whatever it was doing.

        Args:
            notebook_id: Prefer the tab showing this notebook. When None,
                         any open /notebook/ tab matches.

        Returns:
            The matching Page, or None if no notebook tab is open.
        """
        if not self.browser:
            return None

        try:
            if notebook_id:
                for context in self.browser.contexts:
                    for page in context.pages:
                        if notebook_id in (page.url or ''):
                            return page
            for context in self.browser.contexts:
                for page in context.pages:
                    if _is_notebook_url(page.url):
                        return page
        except Exception as e:
            self.logger.debug(f"find_open_notebook_page failed: {e}")

        return None

    async def _wait_for_first_selector(self, selectors: List[str], timeout: int = 5000,
                                       state: Any = 'visible'):
        """Return the first matching selector/element pair from a list."""
        if not self.page:
            return None, None

        for selector in selectors:
            try:
                element = await self.page.wait_for_selector(selector, timeout=timeout, state=state)
                if element:
                    return selector, element
            except Exception:
                continue

        return None, None

    async def _open_audio_download_menu(self) -> bool:
        """Open the audio artifact/player overflow menu that contains Download."""
        if not self.page:
            return False

        # Never a page-wide aria-label="More": the source list renders one per
        # source row before the Studio panel, so it opens a source's menu.
        menu_button_selectors = [
            'button[aria-label="See more options for audio player"]',
            'button[aria-label="More options"]',
        ]

        for selector in menu_button_selectors:
            try:
                button = await self.page.wait_for_selector(selector, timeout=3000, state='visible')
                if not button:
                    continue

                await button.click()
                await self.page.wait_for_timeout(500)
                return True
            except Exception:
                continue

        return False

    async def _open_audio_player(self) -> bool:
        """Open or focus the current audio artifact player before downloading."""
        if not self.page:
            return False

        play_selectors = [
            'button[aria-label="Play"]',
            'button[aria-label="Play audio"]',
            'button:has-text("play_arrow")',
        ]

        selector, button = await self._wait_for_first_selector(play_selectors, timeout=3000)
        if not button:
            return False

        try:
            await button.click()
            await self.page.wait_for_timeout(1500)
            self.logger.info(f"▶️ Opened audio player using: {selector}")
            return True
        except Exception:
            return False

    async def _prepare_download_target(self):
        """Find the visible Download control for the current audio artifact."""
        if not self.page:
            return None, None

        download_selectors = [
            'a[download]:has-text("Download")',
            'a[role="menuitem"][download]',
            'a[download]',
            'a[role="menuitem"]:has-text("Download")',
            '[role="menuitem"]:has-text("Download")',
            'button[role="menuitem"]:has-text("Download")',
            'button:has-text("Download")',
            'button[aria-label="Download"]',
            '[data-testid="download-button"]',
            '.download-button',
        ]

        selector, element = await self._wait_for_first_selector(download_selectors, timeout=2000)
        if element:
            return selector, element

        if await self._open_audio_player():
            selector, element = await self._wait_for_first_selector(download_selectors, timeout=1500)
            if element:
                return selector, element

        if await self._open_audio_download_menu():
            selector, element = await self._wait_for_first_selector(download_selectors, timeout=5000)
            if element:
                return selector, element

        return None, None

    async def _capture_download(self, trigger, output_path: str,
                                timeout: Optional[int] = None,
                                start_timeout: int = 60):
        """
        Run ``trigger()`` and save the download it starts.

        The current Studio UI starts downloads outside any page frame that
        Playwright tracks, so ``page.expect_download()`` never fires even
        though Chrome saves the file. Browser-level CDP download events see
        every download: Chrome writes it into the output directory under its
        GUID, and it is renamed to the caller's stem plus the extension of the
        browser's suggested filename, so the name never lies about the
        container.

        Returns:
            (saved_path, None) on success, (None, reason) otherwise.
        """
        if not self.browser:
            return None, 'no browser connection'
        if timeout is None:
            timeout = self.config.get('STUDIO_SETTINGS', {}).get('download_timeout', 600)

        out_dir = os.path.abspath(os.path.dirname(output_path) or '.')
        os.makedirs(out_dir, exist_ok=True)

        loop = asyncio.get_running_loop()
        began = loop.create_future()
        done = loop.create_future()

        def on_begin(event):
            if not began.done():
                began.set_result(event)

        def on_progress(event):
            if event.get('state') not in ('completed', 'canceled') or done.done():
                return
            if began.done() and event.get('guid') != began.result().get('guid'):
                return
            done.set_result(event)

        console_lines: List[str] = []

        def on_console(message):
            try:
                console_lines.append(message.text)
            except Exception:
                pass

        if self.page:
            self.page.on('console', on_console)
        cdp = await self.browser.new_browser_cdp_session()
        try:
            cdp.on('Browser.downloadWillBegin', on_begin)
            cdp.on('Browser.downloadProgress', on_progress)
            await cdp.send('Browser.setDownloadBehavior', {
                'behavior': 'allowAndName',
                'downloadPath': out_dir,
                'eventsEnabled': True,
            })

            await trigger()

            try:
                start = await asyncio.wait_for(began, start_timeout)
            except asyncio.TimeoutError:
                if any('active file chooser' in line for line in console_lines):
                    return None, ('download blocked: a file picker is open in Chrome '
                                  '(close the "Open Files" window, then retry)')
                return None, 'download did not start'
            suggested = start.get('suggestedFilename') or ''
            self.logger.info(f"📥 Browser suggested filename: {suggested}")

            try:
                progress = await asyncio.wait_for(done, timeout)
            except asyncio.TimeoutError:
                return None, f'download did not finish within {timeout}s'
            if progress.get('state') != 'completed':
                return None, 'download canceled'

            temp_path = progress.get('filePath') or os.path.join(out_dir, start['guid'])
            stem, current_ext = os.path.splitext(output_path)
            suggested_ext = os.path.splitext(suggested)[1]
            final_path = stem + suggested_ext if suggested_ext else output_path
            if suggested_ext and suggested_ext.lower() != current_ext.lower() and current_ext:
                self.logger.info(
                    f"🔤 Adjusting extension {current_ext} → {suggested_ext} "
                    f"to match the downloaded container"
                )
            shutil.move(temp_path, final_path)

            if not os.path.exists(final_path) or os.path.getsize(final_path) == 0:
                return None, 'download finished but the file is empty'
            return final_path, None
        finally:
            if self.page:
                try:
                    self.page.remove_listener('console', on_console)
                except Exception:
                    pass
            try:
                await cdp.detach()
            except Exception:
                pass

    async def ask_notebook(self, question: str, notebook_id: str = None,
                           timeout: int = 180) -> Optional[Dict[str, Any]]:
        """
        Ask the notebook's chat a question and return its answer as Markdown.

        The answer is complete when its card shows "Copy model response to
        clipboard"; citations are kept as [n] (observed 2026-10-06).
        """
        from .report_export import REPORT_TO_MARKDOWN_JS
        if notebook_id and not await self.navigate_to_notebook(notebook_id=notebook_id):
            return None
        box = self.page.locator('textarea[aria-label="Query box"]')
        if await box.count() == 0:
            self.logger.error("❌ Chat query box not found")
            return None
        done_marker = '.to-user-container button[aria-label="Copy model response to clipboard"]'
        answered_before = await self.page.locator(done_marker).count()
        await box.first.fill(question)
        await box.first.press('Enter')
        self.logger.info(f"💬 Asked: {question[:80]}")

        start = time.time()
        while time.time() - start < timeout:
            await self.page.wait_for_timeout(2000)
            if await self.page.locator(done_marker).count() > answered_before:
                break
        else:
            self.logger.error(f"❌ No answer within {timeout}s")
            return None

        content = self.page.locator('.to-user-container .message-content').last
        answer = (await content.evaluate(REPORT_TO_MARKDOWN_JS)).strip()
        if not answer:
            answer = (await content.inner_text()).strip()
        return {
            'question': question,
            'answer': answer,
            'answer_seconds': int(time.time() - start),
            'asked_at': datetime.now().isoformat(),
        }

    async def open_artifact_card(self, card, play: bool = False) -> bool:
        """
        Open a Studio card in its viewer, as a person would on screen.

        With ``play`` an Audio or Video Overview card is started with its
        own Play button instead. An Interactive report opens full-screen as a
        guided view with a table of contents and its embedded studio items.
        """
        if play:
            play_button = await card.query_selector('button[aria-label="Play"]')
            if play_button:
                await play_button.click()
                await self.page.wait_for_timeout(1500)
                return True
        opener = await card.query_selector('button.artifact-stretched-button')
        if not opener:
            return False
        await opener.click()
        await self.page.wait_for_timeout(2000)
        return True

    # Each Studio family's viewer has its own close button. The infographic
    # viewer says "Close infographic" (2026-10-20, notebook 5a00e2d8): left
    # open, it covers the Studio panel, so later generations, the report tile
    # and `studio list` find nothing.
    ARTIFACT_VIEWER_CLOSE_SELECTORS = (
        'button[aria-label="Close report viewer"]',
        'button[aria-label="Close infographic"]',
        'button[aria-label="Close slide deck"]',
        'button[aria-label="Close mind map"]',
        'button[aria-label="Close data table"]',
        'button[aria-label^="Close "][aria-label$="overview"]',
        'artifact-viewer button[aria-label="Close"]',
        # A paused plan (producer notes, an outline) opened by `studio outline`
        # fills the Studio panel; its header button is "Close" (collapse_content).
        # Only while a Proceed button shows, so the normal panel is never collapsed
        # (2026-11-10, notebook 7bf33cea: two generations found no dialog).
        'section.studio-panel:has(button:has-text("Proceed")) .panel-header button[aria-label="Close"]',
    )

    async def close_open_artifact_viewer(self) -> bool:
        """Close an artifact viewer if one is open; press nothing otherwise."""
        for selector in self.ARTIFACT_VIEWER_CLOSE_SELECTORS:
            button = self.page.locator(selector)
            if await button.count() > 0:
                try:
                    await button.first.click(timeout=3000)
                    await self.page.wait_for_timeout(800)
                    self.logger.info(f"🗙 Closed an open artifact viewer: {selector}")
                    return True
                except Exception:
                    continue
        return False

    async def close_artifact_viewer(self) -> None:
        """Close whatever artifact viewer or player is open in the Studio panel."""
        if not await self.close_open_artifact_viewer():
            await self.page.keyboard.press('Escape')

    async def save_report_card(self, card, output_stem: str, title: str = None):
        """
        Save a Report card's content as Markdown and HTML.

        Reports have no file download (Document reports only export to
        Google Docs/Sheets), so the content is read from the open viewer.

        Returns:
            ({'path': <md>, 'html_path': <html>}, None) on success,
            (None, reason) otherwise.
        """
        from .report_export import (
            REPORT_TO_MARKDOWN_JS, REPORT_VIEWER_SELECTOR, report_html_document,
        )
        if not await self.open_artifact_card(card):
            return None, 'card cannot be opened'
        try:
            viewer = self.page.locator(REPORT_VIEWER_SELECTOR)
            try:
                await viewer.first.wait_for(state='visible', timeout=20000)
            except Exception:
                return None, 'report viewer did not open'
            markdown = await viewer.first.evaluate(REPORT_TO_MARKDOWN_JS)
            inner_html = await viewer.first.inner_html()
            if not markdown.strip():
                return None, 'report viewer was empty'
            os.makedirs(os.path.dirname(os.path.abspath(output_stem)), exist_ok=True)
            md_path, html_path = output_stem + '.md', output_stem + '.html'
            heading = f'# {title}\n\n' if title and not markdown.startswith('# ') else ''
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(heading + markdown)
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(report_html_document(title or 'Report', inner_html))
            return {'path': md_path, 'html_path': html_path}, None
        finally:
            await self.close_artifact_viewer()

    _NOT_DOWNLOADABLE_REASONS = ('card has no More menu', 'no Download item in card menu')

    async def _download_card_via_menu(self, card, output_path: str,
                                      timeout: Optional[int] = None):
        """
        Download one Studio card through its own More > Download menu item.

        The card-scoped menu is the one download control every downloadable
        family shares (audio, video, infographic as of 2026-10-06), and it
        needs no player, so it cannot act on the wrong card.

        Returns:
            (saved_path, None) on success, (None, reason) otherwise.
        """
        more = await card.query_selector('button[aria-label="More"]')
        if not more:
            return None, 'card has no More menu'
        await more.click()

        item = None
        for selector in (
            '[role="menu"] button:has-text("Download")',
            '[role="menu"] [role="menuitem"]:has-text("Download")',
            '.mat-mdc-menu-panel button:has-text("Download")',
        ):
            try:
                item = await self.page.wait_for_selector(selector, timeout=2000, state='visible')
                if item:
                    break
            except Exception:
                continue
        if not item:
            await self.page.keyboard.press('Escape')
            return None, 'no Download item in card menu'

        return await self._capture_download(item.click, output_path, timeout=timeout)

    async def _find_artifact_card(self, family_label: str, title: Optional[str] = None):
        """
        Locate a Studio card by title, else the newest card of a family.

        The Studio list is newest-first, so without a title the first card of
        the family is the one a generation just produced.
        """
        try:
            cards = await self.page.query_selector_all(ARTIFACT_CARD_SELECTOR)
        except Exception:
            return None

        for card in cards:
            try:
                if not await card.is_visible():
                    continue
                if title:
                    title_el = await card.query_selector('.artifact-title')
                    if title_el and (await title_el.inner_text()).strip() == title.strip():
                        return card
                    continue
                if await self._card_family_label(card) == family_label:
                    return card
            except Exception:
                continue
        return None
    
    async def navigate_to_notebooklm(self) -> bool:
        """
        Navigate to NotebookLM and verify the page loaded correctly.
        
        Returns:
            bool: True if navigation successful, False otherwise
        """
        try:
            if not self.page:
                self.logger.error("❌ No browser page available")
                return False
            
            self.logger.info(f"🌐 Navigating to {self.base_url}...")
            # Use a longer timeout for navigation, and wait for a specific element
            navigation_timeout = self.config.get('NOTEBOOKLM_SETTINGS', {}).get('login_timeout', 60) * 1000
            
            await self.page.goto(self.base_url, timeout=navigation_timeout)

            # A first-run/rebrand modal can block every click on the page;
            # clear it before waiting on the main interface.
            await self.dismiss_rebrand_modal()

            # Wait for a selector that indicates the main interface is loaded
            # The home page button reads "New notebook" since the Gemini
            # Notebook UI (observed 2026-10-06); older builds said "Create new notebook".
            ready_selector = 'button[aria-label="New notebook"], button[aria-label="Create new notebook"]'
            await self.page.wait_for_selector(ready_selector, timeout=navigation_timeout)
            
            # Check if we're on the correct page
            current_url = self.page.url
            if _is_notebooklm_host(current_url):
                self.logger.info("✅ Successfully navigated to NotebookLM")
                return True
            else:
                self.logger.warning(f"⚠️ Unexpected URL: {current_url}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Failed to navigate to NotebookLM: {e}")
            if self.page:
                screenshot_path = "failed_navigation_screenshot.png"
                await self.page.screenshot(path=screenshot_path)
                self.logger.info(f"📸 Screenshot saved to {screenshot_path}")
            return False
    
    async def check_authentication(self) -> bool:
        """
        Check if user is authenticated with Google account.
        
        Returns:
            bool: True if authenticated, False otherwise
        """
        try:
            if not self.page:
                return False
            
            # Look for user profile indicators first, as they are a stronger signal
            profile_indicators = [
                'button[aria-label*="Google Account"]', # More specific
                'button[data-testid="user-menu"]',
                '.user-avatar',
                '[data-cy="user-menu"]'
            ]
            
            for selector in profile_indicators:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element:
                        self.logger.info("✅ User appears to be authenticated")
                        return True
                except:
                    continue

            # If no profile indicators are found, then check for sign-in buttons
            auth_indicators = [
                'button[data-testid="sign-in"]',
                'button:has-text("Sign in")'
                # Removed 'a[href*="accounts.google.com"]' as it can be a false positive
            ]
            
            for selector in auth_indicators:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element:
                        self.logger.warning("⚠️ Authentication required - user not signed in")
                        if self.page:
                            screenshot_path = "auth_failed_screenshot.png"
                            await self.page.screenshot(path=screenshot_path)
                            self.logger.info(f"📸 Screenshot saved to {screenshot_path}")
                        return False
                except:
                    continue
            
            self.logger.warning("⚠️ Authentication status unclear, assuming authenticated for now.")
            # If neither profile nor sign-in indicators are found, it's ambiguous.
            # Let's assume the user is logged in and let the next steps fail if they are not.
            # This is better than getting stuck in a loop here.
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error checking authentication: {e}")
            if self.page:
                screenshot_path = "auth_error_screenshot.png"
                await self.page.screenshot(path=screenshot_path)
                self.logger.info(f"📸 Screenshot saved to {screenshot_path}")
            return False
    
    async def upload_document(self, file_path: str, notebook_id: str = None) -> Optional[str]:
        """
        Upload a document to NotebookLM.

        Args:
            file_path (str): Path to the document to upload
            notebook_id (str): Optional. If provided, add source to this existing notebook.
                               If None, create a new notebook (legacy behavior).

        Returns:
            Optional[str]: Notebook ID where document was uploaded, or None if upload failed
        """
        try:
            if not self.page:
                self.logger.error("❌ No browser page available")
                return None

            if not os.path.exists(file_path):
                self.logger.error(f"❌ File not found: {file_path}")
                return None

            self.logger.info(f"📄 Uploading document: {file_path}")

            current_notebook_id = notebook_id

            # If notebook_id provided, navigate to that notebook
            if notebook_id:
                self.logger.info(f"📓 Navigating to existing notebook: {notebook_id}")
                if not await self.navigate_to_notebook(notebook_id=notebook_id):
                    self.logger.error(f"❌ Failed to navigate to notebook {notebook_id}")
                    return None
            else:
                # Check if we are on the main page by looking for "Recent notebooks"
                try:
                    recent_notebooks_header = await self.page.is_visible('h2:has-text("Recent notebooks")')
                except:
                    recent_notebooks_header = False

                if recent_notebooks_header:
                    try:
                        self.logger.info("📓 On main page, creating a new notebook...")

                        # Use create_notebook() to capture notebook ID
                        notebook_data = await self.create_notebook()
                        if not notebook_data:
                            self.logger.error("❌ Failed to create new notebook")
                            return None

                        current_notebook_id = notebook_data['id']
                        self.logger.info(f"✅ New notebook created with ID: {current_notebook_id}")

                    except Exception as e:
                        self.logger.error(f"❌ Failed to create a new notebook: {e}")
                        if self.page:
                            await self.page.screenshot(path="create_notebook_failed.png")
                            self.logger.info("📸 Screenshot saved to create_notebook_failed.png")
                        return None
                else:
                    # Already in a notebook, try to extract ID from URL
                    current_url = self.page.url
                    if '/notebook/' in current_url:
                        parts = current_url.split('/notebook/')
                        if len(parts) > 1:
                            current_notebook_id = parts[1].split('?')[0].split('#')[0].split('/')[0]
                            self.logger.info(f"📓 Already in notebook: {current_notebook_id}")
                    else:
                        self.logger.warning("⚠️ Not on main page and not in a notebook, URL: {current_url}")

            # ═══════════════════════════════════════════════════════════════
            # SOURCES TAB NAVIGATION
            # ♠️ Jerry: After first upload, NotebookLM switches to Chat tab
            # We need to navigate back to Sources tab to find upload button
            # ═══════════════════════════════════════════════════════════════

            # Find Sources tab
            sources_tab_selector = 'div[role="tab"]:has-text("Sources")'
            try:
                sources_tab = await self.page.wait_for_selector(sources_tab_selector, timeout=5000)
                if sources_tab:
                    # Check if already active
                    is_active = await sources_tab.get_attribute('aria-selected')
                    if is_active != 'true':
                        self.logger.info("📑 Switching to Sources tab...")
                        await sources_tab.click()
                        await self.page.wait_for_timeout(500)  # Wait for tab switch animation
                        self.logger.info("✅ On Sources tab")
                    else:
                        self.logger.info("✅ Already on Sources tab")
            except Exception as e:
                self.logger.warning(f"⚠️ Could not find Sources tab: {e}")
                # Continue anyway - might already be on Sources tab

            # Check if notebook already has sources - if so, click "+ Add" button first
            # ♠️ Jerry: When sources exist, need to click Add button to show upload options
            add_button_selectors = ADD_SOURCE_BUTTON_SELECTORS

            for selector in add_button_selectors:
                try:
                    add_button = await self.page.wait_for_selector(selector, timeout=2000)
                    if add_button:
                        is_visible = await add_button.is_visible()
                        if is_visible:
                            self.logger.info("➕ Clicking Add button to show source options...")
                            await add_button.click()
                            await self.page.wait_for_timeout(1000)
                            break
                except:
                    continue

            # Now we should be inside a notebook on Sources tab, look for the upload button.
            # ♠️ Nyro: Real NotebookLM upload button selector from Jerry ⚡
            upload_selectors = [
                'button[xapscottyuploadertrigger]',                    # Primary upload trigger
                'button[aria-label="Upload sources from your computer"]', # Upload button aria label
                'mat-card.create-new-action-button',                   # Legacy selector
                'button:has-text("Upload sources")',                   # Upload dialog button
                'button:has-text("Add source")',                       # Alternative text
                'mat-chip:has-text("Upload")',                         # Upload chip after Add button
                'input[type="file"]',                                  # Direct file input
            ]
            
            upload_element = None
            for selector in upload_selectors:
                try:
                    # Use a longer timeout for finding the upload element
                    element = await self.page.wait_for_selector(selector, timeout=30000)
                    if element:
                        upload_element = element
                        break
                except:
                    continue
            
            if not upload_element:
                self.logger.error("❌ Could not find upload element")
                if self.page:
                    await self.page.screenshot(path="upload_element_not_found.png")
                    self.logger.info("📸 Screenshot saved to upload_element_not_found.png")
                return False
            
            self.logger.info(f"Found upload element: {upload_element}")
            upload_element_tag_name = await upload_element.evaluate('el => el.tagName')
            self.logger.info(f"Upload element tag name: {upload_element_tag_name}")

            # Handle file input
            if upload_element_tag_name == 'INPUT':
                # Direct file input element
                await upload_element.set_input_files(file_path)
            else:
                # Prefer the hidden input the button drives, without clicking
                # the button. Clicking opens the native picker (through the
                # desktop portal, even with Playwright's interception), it stays
                # open after the files are set, and while it is open Chrome
                # blocks window.open, the call every Studio Download uses
                # ("window.open blocked due to active file chooser", 2026-10-06).
                hidden_input = await self.page.query_selector('input[type="file"][name="Filedata"]')
                if hidden_input:
                    await hidden_input.set_input_files(file_path)
                    self.logger.info("✅ File set on the hidden input, no picker opened")
                    await self.page.wait_for_timeout(5000)
                    self.logger.info("✅ Document upload completed")
                    self.logger.info(f"📋 Uploaded to notebook: {current_notebook_id}")
                    return current_notebook_id
                try:
                    async with self.page.expect_file_chooser(timeout=5000) as chooser_info:
                        await upload_element.click()
                    chooser = await chooser_info.value
                    await chooser.set_files(file_path)
                    self.logger.warning("⚠️ Uploaded through the file picker; if a picker window "
                                        "stays open, Studio downloads are blocked until it is closed")
                    await self.page.wait_for_timeout(5000)
                    return current_notebook_id
                except Exception as e:
                    self.logger.info(f"ℹ️ No file chooser opened ({e}); using the hidden input")
                await self.page.wait_for_timeout(1000)

                # Find hidden file input (NotebookLM uses hidden input with aria-hidden="true")
                # Don't wait for visibility - set files directly on hidden input
                file_input_selectors = [
                    'input[type="file"][name="Filedata"]',  # NotebookLM specific
                    'input[type="file"]',                   # Generic fallback
                ]

                file_input = None
                for selector in file_input_selectors:
                    try:
                        # Use query_selector to get element even if hidden
                        file_input = await self.page.query_selector(selector)
                        if file_input:
                            self.logger.info(f"✅ Found file input: {selector}")
                            break
                    except:
                        continue

                if file_input:
                    # Set files on hidden input directly
                    await file_input.set_input_files(file_path)
                else:
                    self.logger.error("❌ Could not find file input element")
                    return None
            
            # Wait for upload to complete
            await self.page.wait_for_timeout(5000)

            self.logger.info("✅ Document upload completed")
            self.logger.info(f"📋 Uploaded to notebook: {current_notebook_id}")
            return current_notebook_id

        except Exception as e:
            self.logger.error(f"❌ Failed to upload document: {e}")
            return None

    async def add_url_source(self, url: str, notebook_id: str = None) -> Optional[str]:
        """
        Add a URL source (website, YouTube, etc.) to NotebookLM.

        Args:
            url (str): URL to add as source (SimExp session, website, YouTube, etc.)
            notebook_id (str): Optional. If provided, add source to this existing notebook.
                               If None, create a new notebook.

        Returns:
            Optional[str]: Notebook ID where URL was added, or None if add failed
        """
        try:
            if not self.page:
                self.logger.error("❌ No browser page available")
                return None

            self.logger.info(f"🔗 Adding URL source: {url}")

            current_notebook_id = notebook_id

            # Navigate to notebook or create new one (same logic as file upload)
            if notebook_id:
                self.logger.info(f"📓 Navigating to existing notebook: {notebook_id}")
                if not await self.navigate_to_notebook(notebook_id=notebook_id):
                    self.logger.error(f"❌ Failed to navigate to notebook {notebook_id}")
                    return None
            else:
                # Check if on main page or in notebook
                try:
                    recent_notebooks_header = await self.page.is_visible('h2:has-text("Recent notebooks")')
                except:
                    recent_notebooks_header = False

                if recent_notebooks_header:
                    # Create new notebook
                    notebook_data = await self.create_notebook()
                    if not notebook_data:
                        self.logger.error("❌ Failed to create new notebook")
                        return None
                    current_notebook_id = notebook_data['id']
                else:
                    # Extract ID from current URL
                    current_url = self.page.url
                    if '/notebook/' in current_url:
                        parts = current_url.split('/notebook/')
                        if len(parts) > 1:
                            current_notebook_id = parts[1].split('?')[0].split('#')[0].split('/')[0]

            # Check if "Add sources" dialog is already open (happens with new notebooks)
            # If so, we can skip navigating to Sources tab
            dialog_already_open = False
            try:
                existing_dialog = await self.page.query_selector('.cdk-overlay-pane')
                if existing_dialog:
                    is_visible = await existing_dialog.is_visible()
                    if is_visible:
                        self.logger.info("✅ Add sources dialog already open, skipping Sources tab navigation")
                        dialog_already_open = True
            except:
                pass

            # Navigate to Sources tab only if dialog is not already open
            if not dialog_already_open:
                sources_tab_selector = 'div[role="tab"]:has-text("Sources")'
                try:
                    sources_tab = await self.page.wait_for_selector(sources_tab_selector, timeout=5000)
                    if sources_tab:
                        is_active = await sources_tab.get_attribute('aria-selected')
                        if is_active != 'true':
                            self.logger.info("📑 Switching to Sources tab...")
                            await sources_tab.click()
                            await self.page.wait_for_timeout(500)
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not find Sources tab: {e}")

            # Check if notebook already has sources - if so, click "+ Add" button first
            # ♠️ Jerry: When sources exist, need to click Add button to show upload options
            add_button_selectors = ADD_SOURCE_BUTTON_SELECTORS

            for selector in add_button_selectors:
                try:
                    add_button = await self.page.wait_for_selector(selector, timeout=2000)
                    if add_button:
                        is_visible = await add_button.is_visible()
                        if is_visible:
                            self.logger.info("➕ Clicking Add button to show source options...")
                            await add_button.click()
                            await self.page.wait_for_timeout(1000)
                            break
                except:
                    continue

            sources_before = await self._count_sources()
            urls_given = len(url.split())

            # Detect URL type and select appropriate chip
            # ♠️ Jerry: YouTube URLs need YouTube chip, others need Website chip
            # Since the Gemini Notebook UI (observed 2026-10-06) one "Websites"
            # option takes Website and YouTube URLs alike, several at once.
            is_youtube = 'youtube.com' in url.lower() or 'youtu.be' in url.lower()

            if is_youtube:
                chip_type = "YouTube"
                chip_selectors = [
                    'button:has-text("Websites")',
                    'mat-chip:has-text("YouTube")',
                    'button:has-text("YouTube")',
                    'mat-chip:has(mat-icon:has-text("video_youtube"))',
                    '[aria-label*="YouTube"]'
                ]
            else:
                chip_type = "Website"
                chip_selectors = [
                    'button:has-text("Websites")',
                    'mat-chip:has-text("Website")',
                    'button:has-text("Website")',
                    '[aria-label*="Website"]'
                ]

            self.logger.info(f"🔍 Looking for {chip_type} chip...")
            source_chip = None
            for selector in chip_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element:
                        source_chip = element
                        self.logger.info(f"✅ Found {chip_type} chip: {selector}")
                        break
                except:
                    continue

            if not source_chip:
                self.logger.error(f"❌ Could not find {chip_type} chip")
                return None

            # Click the appropriate chip
            self.logger.info(f"🖱️ Clicking {chip_type} chip...")
            await source_chip.click()

            # Wait for dialog/modal to appear
            self.logger.info("⏳ Waiting for URL dialog to appear...")
            dialog_appeared = False
            dialog_selectors = [
                'div[role="dialog"]',
                '.cdk-overlay-pane',
                '.mat-dialog-container',
                'mat-dialog-container'
            ]

            dialog = None
            for selector in dialog_selectors:
                try:
                    dialog = await self.page.wait_for_selector(selector, timeout=10000, state='visible')
                    if dialog:
                        dialog_appeared = True
                        self.logger.info(f"✅ Dialog appeared: {selector}")
                        break
                except:
                    continue

            if not dialog_appeared:
                self.logger.warning("⚠️ Dialog did not appear, will try to find input anyway...")
                await self.page.wait_for_timeout(3000)  # Wait a bit more

            # Find URL input field - search more broadly including within dialog
            self.logger.info("🔍 Looking for URL input field...")
            url_input_selectors = [
                # NotebookLM uses a textarea for URL input!
                'textarea[formcontrolname="urls"]',
                '.cdk-overlay-pane textarea',
                'div[role="dialog"] textarea',
                'textarea[formcontrolname="newUrl"]',
                'textarea#mat-input-0',
                'textarea.text-area',
                # Fallback to inputs
                '.cdk-overlay-pane input',
                'div[role="dialog"] input',
                '.mat-dialog-container input',
                # Then try specific attributes
                'input[placeholder*="URL"]',
                'textarea[placeholder*="URL"]',
                'input[placeholder*="paste"]',
                'textarea[placeholder*="paste"]',
            ]

            url_input = None
            for selector in url_input_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    for element in elements:
                        try:
                            is_visible = await element.is_visible()
                            if is_visible:
                                # Check if it's in the dialog if we found one
                                if dialog_appeared and dialog:
                                    # Try to see if this element is within the dialog
                                    try:
                                        bounding_box = await element.bounding_box()
                                        if bounding_box:
                                            url_input = element
                                            self.logger.info(f"✅ Found URL input in dialog: {selector}")
                                            break
                                    except:
                                        pass
                                else:
                                    # No dialog, just use first visible
                                    url_input = element
                                    self.logger.info(f"✅ Found URL input: {selector}")
                                    break
                        except:
                            continue
                    if url_input:
                        break
                except:
                    continue

            if not url_input:
                self.logger.error("❌ Could not find URL input field")
                # Save screenshot for debugging
                await self.page.screenshot(path="debug/url_input_not_found.png")
                self.logger.info("📸 Screenshot saved: debug/url_input_not_found.png")
                return None

            # Enter URL
            self.logger.info(f"⌨️ Typing URL: {url}")
            await url_input.click()
            await self.page.wait_for_timeout(500)
            await url_input.fill(url)  # Use fill instead of keyboard.type - it's faster and more reliable
            await self.page.wait_for_timeout(1000)

            # Click Insert button instead of pressing Enter
            self.logger.info("🔍 Looking for Insert button...")
            insert_button_selectors = [
                'button:has-text("Insert")',
                'button.mdc-button:has-text("Insert")',
                '.cdk-overlay-pane button:has-text("Insert")',
                'button[type="submit"]',
                'button:has(.mdc-button__label:has-text("Insert"))'
            ]

            insert_button = None
            for selector in insert_button_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element:
                        is_visible = await element.is_visible()
                        if is_visible:
                            insert_button = element
                            self.logger.info(f"✅ Found Insert button: {selector}")
                            break
                except:
                    continue

            if insert_button:
                self.logger.info("🖱️ Clicking Insert button...")
                await insert_button.click()
                await self.page.wait_for_timeout(5000)  # Wait for URL to be processed
            else:
                # Fallback: press Enter if Insert button not found
                self.logger.warning("⚠️ Insert button not found, trying Enter key...")
                await self.page.keyboard.press('Enter')
                await self.page.wait_for_timeout(5000)

            # Insert closes the dialog before the import finishes; a URL that
            # cannot be imported (private or very recent video, paywall)
            # never becomes a source row.
            sources_after = sources_before
            for _ in range(30):
                sources_after = await self._count_sources()
                if sources_after >= sources_before + urls_given:
                    break
                await self.page.wait_for_timeout(2000)
            added = sources_after - sources_before
            if added <= 0:
                self.logger.error("❌ No source appeared after Insert")
                return None
            # A URL that cannot be imported still gets a row, marked as an
            # error, titled with the bare URL (observed 2026-10-06 for videos
            # uploaded the same day: "Transcript not available"). A video can
            # take a minute to fail (2026-10-15: 3 s was too early, and the
            # row's title was the youtube.com/watch form of a youtu.be URL), so
            # wait until no given URL is still a bare, unprocessed row.
            given = {source_url_key(u): u for u in url.split()}
            errors = []
            for _ in range(18):
                await self.page.wait_for_timeout(5000)
                errors = [dict(e, title=given[source_url_key(e['title'])])
                          for e in await self._source_errors() if source_url_key(e['title']) in given]
                failed = {source_url_key(e['title']) for e in errors}
                titles = {source_url_key(x) for x in await self.page.locator('.source-title').all_inner_texts()}
                if not any(k in titles and k not in failed for k in given):
                    break
            self.last_source_errors = errors
            for error in self.last_source_errors:
                self.logger.error(f"❌ Not imported: {error['title']} — {error['reason']}")
            imported = added - len(self.last_source_errors)
            if imported <= 0:
                return None
            if imported < urls_given:
                self.logger.warning(f"⚠️ {imported} of {urls_given} URLs became sources")
            self.logger.info(f"✅ URL source added successfully ({imported} new)")
            self.logger.info(f"📋 Added to notebook: {current_notebook_id}")
            return current_notebook_id

        except Exception as e:
            self.logger.error(f"❌ Failed to add URL source: {e}")
            return None

    async def list_source_titles(self) -> List[str]:
        """The titles of the Sources panel's rows, in order."""
        titles = []
        rows = self.page.locator('.single-source-container')
        for i in range(await rows.count()):
            try:
                titles.append((await rows.nth(i).locator('.source-title').first.inner_text()).strip())
            except Exception:
                titles.append('')
        return titles

    async def remove_source(self, title: str, notebook_id: str = None) -> Dict[str, Any]:
        """
        Remove one source from a notebook by its title in the Sources panel.

        A revised source replaces its old copy this way (screenwalk 2610221013,
        07:22: remove the outdated sources, add the revised ones, regenerate).
        Opens the row's More menu, chooses Remove, confirms, and succeeds only
        when the row is gone. Refuses a title that matches several rows.

        Returns {'removed': bool, 'title': str, 'reason': str}.
        """
        if not self.page:
            return {'removed': False, 'title': title, 'reason': 'no browser page'}
        if notebook_id and not await self.navigate_to_notebook(notebook_id=notebook_id):
            return {'removed': False, 'title': title, 'reason': f'could not open notebook {notebook_id}'}

        titles = await self.list_source_titles()
        matches = match_source_titles(titles, title)
        if not matches:
            return {'removed': False, 'title': title, 'reason': 'no source has this title'}
        if len(matches) > 1:
            return {'removed': False, 'title': title,
                    'reason': f'{len(matches)} sources have this title; nothing removed'}
        found = titles[matches[0]]
        row = self.page.locator('.single-source-container').nth(matches[0])

        try:
            more = row.locator('button[aria-label="More"], button:has(mat-icon:text-is("more_vert"))').first
            await more.click(timeout=5000)
            item = self.page.get_by_role('menuitem', name=re.compile(r'(remove|delete)', re.I)).first
            await item.click(timeout=5000)
            # The "Delete <title>?" dialog renders after the menu closes. Counting its
            # button at once found none, left the dialog open, and its backdrop
            # blocked every later removal (Episode 297, 2026-10-25: 0 of 8).
            dialogs = self.page.locator('mat-dialog-container, [role="dialog"]')
            confirm = dialogs.get_by_role('button', name=re.compile(r'^\s*(delete|remove|confirm)', re.I)).first
            try:
                await confirm.wait_for(state='visible', timeout=10000)
                await confirm.click(timeout=5000)
            except Exception:
                await self._close_dialog(dialogs)
                return {'removed': False, 'title': found,
                        'reason': 'the confirm dialog showed no Delete button within 10 s; it was closed'}
        except Exception as e:
            try:
                await self.page.keyboard.press('Escape')
            except Exception:
                pass
            return {'removed': False, 'title': found, 'reason': f'the remove control was not found: {e}'}

        for _ in range(20):
            await self.page.wait_for_timeout(750)
            if found not in await self.list_source_titles():
                self.logger.info(f"🗑️ Removed source: {found}")
                return {'removed': True, 'title': found, 'reason': ''}
        return {'removed': False, 'title': found, 'reason': 'the row is still there after confirming'}

    async def _close_dialog(self, dialogs) -> None:
        """Close an open dialog, Cancel first, else Escape, so its backdrop blocks nothing after it."""
        try:
            cancel = dialogs.get_by_role('button', name=re.compile(r'^\s*(cancel|close)', re.I)).first
            if await cancel.count() > 0 and await cancel.is_visible():
                await cancel.click(timeout=3000)
                return
        except Exception:
            pass
        try:
            await self.page.keyboard.press('Escape')
        except Exception:
            pass

    async def _count_sources(self) -> int:
        """Source rows in the Sources panel."""
        try:
            return await self.page.locator('.single-source-container').count()
        except Exception:
            return 0

    async def _source_errors(self) -> List[Dict[str, str]]:
        """Source rows marked as errors, with the reason their tooltip gives."""
        errors = []
        rows = self.page.locator('.single-source-error-container')
        for i in range(await rows.count()):
            row = rows.nth(i)
            title = ''
            try:
                title = await row.locator('.source-title').first.inner_text()
            except Exception:
                pass
            reason = 'cannot be imported'
            try:
                await self.page.mouse.move(0, 0)
                await self.page.wait_for_timeout(300)
                await row.locator('mat-icon', has_text='info').first.hover(timeout=3000)
                for _ in range(10):
                    await self.page.wait_for_timeout(300)
                    tips = [t.strip() for t in
                            await self.page.locator('.mat-mdc-tooltip, [role=tooltip]').all_inner_texts()
                            if t.strip()]
                    if tips:
                        reason = tips[-1]
                        break
            except Exception:
                pass
            errors.append({'title': title.strip(), 'reason': reason})
        return errors

    async def add_source(self, source: str, notebook_id: str = None) -> Optional[str]:
        """
        Smart source addition - automatically detects source type and routes appropriately.

        This is the recommended high-level method for adding any source to NotebookLM.
        It intelligently detects whether the source is a URL or file path and calls
        the appropriate underlying method.

        Args:
            source (str): Source to add - can be:
                         - URL (http://..., https://...)
                         - File path (relative or absolute)
            notebook_id (str): Optional. If provided, add source to this existing notebook.
                              If None, create a new notebook.

        Returns:
            Optional[str]: Notebook ID where source was added, or None if add failed

        Examples:
            # Add URL source
            await automator.add_source("https://example.com/article")

            # Add file source
            await automator.add_source("/path/to/document.pdf")

            # Add to existing notebook
            await automator.add_source("research.pdf", notebook_id="abc123")
        """
        try:
            # Detect source type by checking for URL prefix
            if source.startswith(('http://', 'https://')):
                self.logger.info(f"🔍 Detected URL source: {source}")
                return await self.add_url_source(source, notebook_id)
            else:
                self.logger.info(f"🔍 Detected file source: {source}")
                return await self.upload_document(source, notebook_id)

        except Exception as e:
            self.logger.error(f"❌ Failed to add source: {e}")
            return None

    async def generate_audio_overview(
        self,
        format: str = None,
        language: str = None,
        length: str = None,
        focus_prompt: str = None,
        notebook_id: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generate an Audio Overview (podcast) with advanced customization.

        🌸 Miette: This is the ceremony of giving voice to content.
        🔥 West (Action): Where the code speaks and creates.

        Args:
            format (str): Podcast format - deep_dive, brief, critique, debate
                         Default from config or 'deep_dive'
            language (str): Podcast language - English, Spanish, French, etc.
                           Default from config or 'English'
            length (str): Podcast length - short, default, long
                         Default from config or 'default'
            focus_prompt (str): Custom focus instructions for AI hosts (max 5000 chars)
                               Optional - guides the conversation direction
            notebook_id (str): Target notebook ID (navigates if provided)
                              Uses current notebook if None

        Returns:
            Optional[Dict[str, Any]]: Artifact metadata if successful:
                {
                    'artifact_id': 'xyz-789',
                    'type': 'audio_overview',
                    'format': 'deep_dive',
                    'language': 'English',
                    'length': 'default',
                    'focus_prompt': '...',
                    'status': 'completed',
                    'created_at': '2025-01-15T14:30:00',
                    'generation_time': 245
                }
            Returns None if generation failed

        Examples:
            # Basic generation with defaults
            await automator.generate_audio_overview()

            # Deep dive format
            await automator.generate_audio_overview(format='deep_dive', length='long')

            # Brief summary
            await automator.generate_audio_overview(format='brief', length='short')

            # Critique with focus
            await automator.generate_audio_overview(
                format='critique',
                focus_prompt='Analyze strengths and weaknesses of the research methodology'
            )

            # Multilingual
            await automator.generate_audio_overview(language='Spanish', length='default')
        """
        try:
            if not self.page:
                self.logger.error("❌ No browser page available")
                return None

            # Get defaults from config
            studio_config = self.config.get('STUDIO_SETTINGS', {}).get('audio_overview', {})
            format = format or studio_config.get('default_format', 'deep_dive')
            language = language or studio_config.get('default_language', 'English')
            length = length or studio_config.get('default_length', 'default')
            generation_timeout = studio_config.get('generation_timeout', 600)
            polling_interval = studio_config.get('polling_interval', 5)

            # Validate and normalize format
            format_map = {
                'deep_dive': 'Deep Dive',
                'brief': 'Brief',
                'critique': 'Critique',
                'debate': 'Debate'
            }
            format_normalized = format.lower().replace(' ', '_')
            if format_normalized not in format_map:
                self.logger.warning(f"⚠️ Unknown format '{format}', using 'deep_dive'")
                format_normalized = 'deep_dive'
            format_display = format_map[format_normalized]

            # Normalize length
            length_normalized = length.lower()
            if length_normalized not in ['short', 'default', 'long']:
                self.logger.warning(f"⚠️ Unknown length '{length}', using 'default'")
                length_normalized = 'default'
            length_display = length_normalized.capitalize()

            self.logger.info(f"🎙️ Generating Audio Overview")
            self.logger.info(f"   Format: {format_display}")
            self.logger.info(f"   Language: {language}")
            self.logger.info(f"   Length: {length_display}")
            if focus_prompt:
                preview = focus_prompt[:50] + '...' if len(focus_prompt) > 50 else focus_prompt
                self.logger.info(f"   Focus: {preview}")

            # Navigate to notebook if ID provided
            if notebook_id:
                self.logger.info(f"📓 Navigating to notebook: {notebook_id}")
                await self.navigate_to_notebook(notebook_id)

            # Ensure we're on Sources tab (where Studio panel is located)
            await self._ensure_sources_tab_active()

            # Snapshot pre-existing completed Audio Overview cards so a repeat
            # generation returns the NEW card's metadata, not a stale match.
            baseline_snapshot = await self._completed_card_snapshot('audio_overview')
            baseline_count = len(baseline_snapshot)
            baseline_keys = {c['card_key'] for c in baseline_snapshot}

            # Step 1: Look for the edit/pencil icon next to Audio Overview in Studio panel
            # This is the correct entry point for customization
            self.logger.info("🔍 Looking for Audio Overview customization icon (pencil/edit)...")

            customize_icon_selectors = [
                # Primary: Edit button on Audio Overview card
                '.create-artifact-button-container:has-text("Audio Overview") button.edit-button',
                '.create-artifact-button-container:has-text("Audio Overview") .edit-button-always-visible',
                '.create-artifact-button-container:has-text("Audio Overview") button[data-edit-button-type="1"]',
                # Backup: Generic edit button with Audio Overview nearby
                'button.edit-button:has(mat-icon .edit-button-icon)',
                '.mat-label-medium:has-text("Audio Overview") button.edit-button',
                # Fallback: Material icon approach
                'button:has(mat-icon:has-text("edit"))',
                'button.edit-button-always-visible',
                # Last resort: any edit button
                'button[mat-icon-button]:has(mat-icon:has-text("edit"))'
            ]

            customize_button = None
            for selector in customize_icon_selectors:
                try:
                    # Wait for element to appear (up to 10 seconds)
                    customize_button = await self.page.wait_for_selector(
                        selector,
                        timeout=10000,
                        state='visible'
                    )
                    if customize_button:
                        self.logger.info(f"✅ Found customize icon: {selector}")
                        break
                except:
                    continue

            if not customize_button:
                # Fallback: Try clicking main Audio Overview button (may trigger quick generation)
                self.logger.warning("⚠️ Could not find customize icon, trying main Audio Overview button...")
                studio_button_selectors = [
                    'button:has-text("Audio Overview")',
                    '[aria-label*="Audio Overview"]',
                    '.studio-panel button:has-text("Audio")'
                ]

                for selector in studio_button_selectors:
                    try:
                        element = await self.page.wait_for_selector(selector, timeout=5000)
                        if element:
                            is_visible = await element.is_visible()
                            if is_visible:
                                customize_button = element
                                self.logger.info(f"✅ Found Audio Overview button (fallback): {selector}")
                                break
                    except:
                        continue

            if not customize_button:
                self.logger.error("❌ Could not find Audio Overview customization icon or button")
                return None

            # Click the customize icon (or fallback button)
            self.logger.info("🖱️ Clicking Audio Overview customize icon...")
            await customize_button.click()
            await self.page.wait_for_timeout(2000)

            # Step 2: Look for customization dialog or Customize button
            self.logger.info("⏳ Waiting for customization dialog or button...")

            # Check if customization dialog already appeared
            dialog = None
            try:
                dialog = await self.page.wait_for_selector(
                    '.mat-mdc-dialog-container',
                    timeout=5000,
                    state='visible'
                )
                if dialog:
                    self.logger.info("✅ Customization dialog appeared")
            except:
                # Dialog didn't appear, look for Customize button
                self.logger.info("🔍 Looking for Customize button...")
                customize_selectors = [
                    'button:has-text("Customize")',
                    'button:has-text("Customization")',
                    '[aria-label*="Customize"]'
                ]

                for selector in customize_selectors:
                    try:
                        customize_button = await self.page.wait_for_selector(selector, timeout=5000)
                        if customize_button:
                            is_visible = await customize_button.is_visible()
                            if is_visible:
                                self.logger.info(f"✅ Found Customize button: {selector}")
                                await customize_button.click()
                                await self.page.wait_for_timeout(2000)

                                # Now dialog should appear
                                dialog = await self.page.wait_for_selector(
                                    '.mat-mdc-dialog-container',
                                    timeout=10000,
                                    state='visible'
                                )
                                if dialog:
                                    self.logger.info("✅ Customization dialog appeared")
                                break
                    except:
                        continue

            if not dialog:
                self.logger.error("❌ Could not find customization dialog")
                return None

            # Step 3: Configure format (radio button tile)
            self.logger.info(f"⚙️ Selecting format: {format_display}")
            format_selectors = [
                f'mat-radio-button .tile-label:has-text("{format_display}")',
                f'mat-radio-button:has-text("{format_display}")',
                f'[aria-label*="{format_display}"]'
            ]

            format_tile = None
            for selector in format_selectors:
                try:
                    elements = await dialog.query_selector_all(selector)
                    for element in elements:
                        try:
                            is_visible = await element.is_visible()
                            if is_visible:
                                format_tile = element
                                break
                        except:
                            continue
                    if format_tile:
                        break
                except:
                    continue

            if format_tile:
                await format_tile.click()
                await self.page.wait_for_timeout(500)
                self.logger.info(f"✅ Format selected: {format_display}")
            else:
                self.logger.warning(f"⚠️ Could not find format tile for '{format_display}', using default")

            # Step 4: Configure language (dropdown)
            # Get the display language name
            language_lower = language.lower()
            language_display = LANGUAGE_DISPLAY_MAP.get(language_lower, language.capitalize())

            self.logger.info(f"⚙️ Selecting language: {language_display} (input: {language})")
            language_selectors = [
                'mat-select[role="combobox"]',  # Primary: role-based
                '.mat-mdc-select',              # Class-based
                'mat-select',                   # Generic mat-select
                'mat-select[aria-label*="language"]',  # Fallback
                'mat-select[aria-label*="Language"]'
            ]

            language_select = None
            for selector in language_selectors:
                try:
                    # Wait for language selector to appear (up to 5 seconds)
                    language_select = await dialog.wait_for_selector(
                        selector,
                        timeout=5000,
                        state='visible'
                    )
                    if language_select:
                        break
                except:
                    continue

            if language_select:
                # Click to open dropdown
                await language_select.click()
                await self.page.wait_for_timeout(1000)

                # Wait for overlay to appear (language options appear in CDK overlay)
                await self.page.wait_for_timeout(1500)  # Give overlay time to fully render

                language_selected = False

                # Try matching the primary text span (most specific)
                try:
                    option = self.page.locator(f'mat-option .mdc-list-item__primary-text:has-text("{language_display}")')
                    if await option.count() > 0:
                        # Click the parent mat-option element
                        parent = option.locator('xpath=ancestor::mat-option').first
                        await parent.click()
                        await self.page.wait_for_timeout(500)
                        self.logger.info(f"✅ Language selected: {language_display} (via primary-text)")
                        language_selected = True
                except Exception as e:
                    self.logger.debug(f"primary-text selector failed: {e}")

                # Fallback: Try Playwright's get_by_role with exact match
                if not language_selected:
                    try:
                        option = self.page.get_by_role('option', name=language_display, exact=False)
                        if await option.count() > 0:
                            await option.first.click()
                            await self.page.wait_for_timeout(500)
                            self.logger.info(f"✅ Language selected: {language_display} (via role)")
                            language_selected = True
                    except Exception as e:
                        self.logger.debug(f"get_by_role failed: {e}")

                # Fallback: Try locator with text (partial match)
                if not language_selected:
                    try:
                        option = self.page.locator(f'mat-option:has-text("{language_display}")')
                        if await option.count() > 0:
                            await option.first.click()
                            await self.page.wait_for_timeout(500)
                            self.logger.info(f"✅ Language selected: {language_display} (via locator)")
                            language_selected = True
                    except Exception as e:
                        self.logger.debug(f"locator failed: {e}")

                # Fallback: Try CSS selectors
                if not language_selected:
                    language_option_selectors = [
                        f'.cdk-overlay-pane mat-option:has-text("{language_display}")',
                        f'mat-option:has-text("{language_display}")',
                        f'.mat-mdc-option:has-text("{language_display}")',
                        f'[role="option"]:has-text("{language_display}")'
                    ]

                    for selector in language_option_selectors:
                        try:
                            option = await self.page.wait_for_selector(selector, timeout=3000, state='visible')
                            if option:
                                await option.click()
                                await self.page.wait_for_timeout(500)
                                self.logger.info(f"✅ Language selected: {language_display} (via selector)")
                                language_selected = True
                                break
                        except:
                            continue

                if not language_selected:
                    # Close the overlay by pressing Escape to prevent it blocking other clicks
                    self.logger.warning(f"⚠️ Could not select language '{language_display}', using default")
                    await self.page.keyboard.press('Escape')
                    await self.page.wait_for_timeout(500)
            else:
                self.logger.warning("⚠️ Could not find language selector, using default")

            # Step 5: Configure length (toggle button group)
            self.logger.info(f"⚙️ Selecting length: {length_display}")
            length_selectors = [
                f'mat-button-toggle:has-text("{length_display}") button',  # Primary: button inside toggle
                f'button.mat-button-toggle-button:has-text("{length_display}")',  # Direct button class
                f'.mat-button-toggle-group button:has-text("{length_display}")',  # Group context
                f'mat-button-toggle button >> text="{length_display}"',  # Playwright text selector
                f'button:has(.mat-button-toggle-label-content:has-text("{length_display}"))'  # Via label span
            ]

            length_button = None
            for selector in length_selectors:
                try:
                    # Wait for button to appear (up to 5 seconds)
                    length_button = await dialog.wait_for_selector(
                        selector,
                        timeout=5000,
                        state='visible'
                    )
                    if length_button:
                        break
                except:
                    continue

            if length_button:
                await length_button.click()
                await self.page.wait_for_timeout(500)
                self.logger.info(f"✅ Length selected: {length_display}")
            else:
                self.logger.warning(f"⚠️ Could not find length button for '{length_display}', using default")

            # Step 6: Enter focus prompt if provided
            if focus_prompt:
                self.logger.info("⚙️ Entering focus prompt...")
                focus_selectors = [
                    'textarea[aria-label*="focus"]',
                    'textarea[aria-label*="Focus"]',
                    'textarea[placeholder*="focus"]',
                    'textarea[placeholder*="Focus"]',
                    '.focus-prompt textarea'
                ]

                focus_textarea = None
                for selector in focus_selectors:
                    try:
                        element = await dialog.query_selector(selector)
                        if element:
                            is_visible = await element.is_visible()
                            if is_visible:
                                focus_textarea = element
                                break
                    except:
                        continue

                if focus_textarea:
                    # Truncate if too long (5000 char limit)
                    focus_text = focus_prompt[:5000] if len(focus_prompt) > 5000 else focus_prompt
                    await focus_textarea.fill(focus_text)
                    await self.page.wait_for_timeout(500)
                    self.logger.info(f"✅ Focus prompt entered ({len(focus_text)} chars)")
                else:
                    self.logger.warning("⚠️ Could not find focus prompt textarea")

            # Step 7: Click Generate button
            self.logger.info("🚀 Clicking Generate button...")
            generate_selectors = [
                'button:has-text("Generate")',
                'button .mdc-button__label:has-text("Generate")',
                'button[aria-label*="Generate"]'
            ]

            generate_button = None
            for selector in generate_selectors:
                try:
                    element = await dialog.query_selector(selector)
                    if element:
                        is_visible = await element.is_visible()
                        if is_visible:
                            generate_button = element
                            break
                except:
                    continue

            if not generate_button:
                self.logger.error("❌ Could not find Generate button")
                return None

            # Click Generate and wait for dialog to close
            generation_start_time = time.time()
            await generate_button.click()
            await self.page.wait_for_timeout(3000)  # Wait for dialog to close

            self.logger.info("🔄 Audio Overview generation started...")
            self.logger.info(f"⏳ Monitoring generation (timeout: {generation_timeout}s)...")

            # Step 8: Monitor generation status
            # NotebookLM generates in background, shows status in Studio panel
            artifact_data = await self._monitor_audio_generation(
                generation_start_time,
                generation_timeout,
                polling_interval,
                baseline_count=baseline_count,
                baseline_keys=baseline_keys,
            )

            if artifact_data:
                # Add our configuration to the metadata
                artifact_data['format'] = format_normalized
                artifact_data['language'] = language
                artifact_data['length'] = length_normalized
                artifact_data['focus_prompt'] = focus_prompt if focus_prompt else None

                self.logger.info("✅ Audio Overview generated successfully!")
                self.logger.info(f"📋 Artifact ID: {artifact_data.get('artifact_id', 'unknown')}")
                self.logger.info(f"⏱️ Generation time: {artifact_data.get('generation_time', 0)}s")

                # Track artifact in session if notebook_id is available
                # 🌸 Miette: Recording the voice we created
                if notebook_id and self.session_tracker:
                    try:
                        success = self.session_tracker.add_artifact_to_notebook(
                            notebook_id,
                            artifact_data
                        )
                        if success:
                            self.logger.info(f"📝 Artifact tracked in session for notebook {notebook_id}")
                    except Exception as e:
                        self.logger.warning(f"⚠️ Could not track artifact in session: {e}")

                return artifact_data
            else:
                self.logger.error("❌ Audio Overview generation failed or timed out")
                return None

        except Exception as e:
            self.logger.error(f"❌ Failed to generate Audio Overview: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None

    async def detect_completed_artifact(self, artifact_type: str = 'audio_overview') -> Optional[Dict[str, Any]]:
        """
        Detect an ALREADY-COMPLETED artifact card in the Studio panel.

        A finished artifact may no longer expose the legacy completion
        controls, so a generation "timeout" can be a false negative. The
        durable cues live on the <artifact-library-item> card:
        aria-description naming the family, a Play button, a More button,
        and .artifact-title/.artifact-details metadata. When this returns a
        card, prefer download-and-reconcile over regenerating blindly.

        Args:
            artifact_type: Registry key (audio_overview, slide_deck, ...)

        Returns:
            Artifact metadata dict (status='completed') or None.
        """
        if not self.page:
            return None

        spec = get_artifact_spec(artifact_type)
        label = spec['label'] if spec else None
        type_key = normalize_artifact_type(artifact_type) or artifact_type

        for selector in completed_card_selectors(label):
            try:
                artifact_element = await self.page.query_selector(selector)
                if artifact_element and await artifact_element.is_visible():
                    artifact_data = await self._extract_artifact_metadata(artifact_element)
                    artifact_data['status'] = 'completed'
                    artifact_data['type'] = type_key
                    return artifact_data
            except Exception:
                continue

        return None

    async def list_studio_artifacts(self) -> List[Dict[str, Any]]:
        """
        List every artifact card currently visible in the Studio panel.

        Each returned dict carries a ``dom_index`` — the card's position in
        the UNFILTERED ``artifact-library-item`` list — so a later download
        pass can re-locate the exact same card by that stable key instead of
        by its ordinal in this visibility-filtered list. The two lists only
        align when nothing was filtered; ``dom_index`` keeps identity honest
        when a non-visible/virtualized card precedes visible ones.

        Returns:
            List of artifact metadata dicts with title/details, the
            aria-description family label when the card exposes one, and the
            card's ``dom_index`` in the full DOM list.
        """
        artifacts: List[Dict[str, Any]] = []
        if not self.page:
            return artifacts

        try:
            cards = await self.page.query_selector_all('artifact-library-item')
            for dom_index, card in enumerate(cards):
                try:
                    if not await card.is_visible():
                        continue
                    data = await self._extract_artifact_metadata(card)
                    data['dom_index'] = dom_index
                    try:
                        data['family_label'] = await self._card_family_label(card)
                    except Exception:
                        data['family_label'] = None
                    try:
                        play_button = await card.query_selector('button[aria-label="Play"]')
                        data['playable'] = play_button is not None
                    except Exception:
                        data['playable'] = False
                    try:
                        data['generating'] = await card.query_selector(GENERATING_CARD_MARKER) is not None
                    except Exception:
                        data['generating'] = False
                    try:
                        data['awaiting_review'] = await card.query_selector(PENDING_REVIEW_MARKER) is not None
                    except Exception:
                        data['awaiting_review'] = False
                    artifacts.append(data)
                except Exception:
                    continue
        except Exception as e:
            self.logger.warning(f"⚠️ Could not list Studio artifacts: {e}")

        return artifacts

    async def _monitor_artifact_generation(
        self,
        start_time: float,
        timeout: int,
        polling_interval: int,
        artifact_type: str = 'audio_overview',
        baseline_count: int = 0,
        baseline_keys: Optional[set] = None,
        start_timeout: Optional[int] = None,
        stop_at_review: Optional[set] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Monitor Studio artifact generation until a completed card appears.

        It stops early, with the reason in ``self.last_generation_refusal``,
        when the page says the daily limit is reached, or when no card of the
        family is generating and none completed within ``start_timeout``
        seconds. On 2026-10-29 an Infographic and a Video Overview each waited
        out their whole timeout (902 s, 1802 s) with no card ever started,
        and the next Video Overview was refused by the daily limit.

        🔥 West (Action): Patient watching for creation to complete.

        Args:
            start_time (float): When generation started (time.time())
            timeout (int): Maximum wait time in seconds
            polling_interval (int): How often to check status (seconds)
            artifact_type: Registry key of the family being generated
            baseline_count: Completed cards of this family present BEFORE
                            generation started, so a pre-existing artifact
                            is not mistaken for the new one.
            baseline_keys: Stable identity keys of those pre-existing cards.
                            When a new card appears (baseline_count > 0), the
                            NEW card is identified by set-difference against
                            these keys so the returned metadata describes the
                            freshly generated artifact — not whichever card the
                            completion selectors happened to match first.
            stop_at_review: Ids of the cards already paused at a plan. When
                            given, the watch ends at the first OTHER paused card
                            of this family, with status 'awaiting_review'.

        Returns:
            Optional[Dict[str, Any]]: Artifact metadata if completed, None if timeout/error
        """
        self.last_generation_refusal = None
        if start_timeout is None:
            start_timeout = GENERATION_START_TIMEOUT_S
        try:
            last_log_time = start_time
            started = False

            while time.time() - start_time < timeout:
                elapsed = int(time.time() - start_time)

                if not started:
                    started = await self._generation_in_progress()
                    # A limit counts only while nothing is generating: a card
                    # already under way is not undone by the sentence.
                    limit = None if started else await self._daily_limit_on_page(artifact_type)
                    if limit:
                        self.logger.error(f"❌ Gemini Notebook says: {limit}. Nothing was generated; try again tomorrow.")
                        self.last_generation_refusal = limit
                        return None

                # Log progress every 30 seconds
                if time.time() - last_log_time >= 30:
                    self.logger.info(f"⏳ Still generating... ({elapsed}s elapsed)")
                    last_log_time = time.time()

                if stop_at_review is not None:
                    paused = await self._new_paused_card(artifact_type, stop_at_review)
                    if paused:
                        paused['generation_time'] = int(time.time() - start_time)
                        self.logger.info(f"⏸️ Plan ready for review after {paused['generation_time']}s")
                        return paused

                detected = await self.detect_completed_artifact(artifact_type)
                if detected:
                    current_count = await self._count_completed_cards(artifact_type)
                    if current_count > baseline_count:
                        result = await self._resolve_new_artifact(
                            detected, artifact_type, baseline_count, baseline_keys
                        )
                        generation_time = int(time.time() - start_time)
                        self.logger.info(f"✅ Generation completed in {generation_time}s")
                        result['generation_time'] = generation_time
                        return result

                if not started and elapsed >= start_timeout:
                    self.logger.error(
                        f"❌ No {artifact_type} card started generating within {elapsed}s; nothing was generated"
                    )
                    self.last_generation_refusal = 'did not start'
                    return None

                # Wait before polling again
                await self.page.wait_for_timeout(polling_interval * 1000)

            # Timeout reached — do a final drift-aware sweep before giving
            # up: the artifact may have finished without the expected cues
            # appearing during polling.
            elapsed = int(time.time() - start_time)
            detected = await self.detect_completed_artifact(artifact_type)
            # Only a card that was not there before counts: on 2026-10-15 an
            # Infographic that never started "recovered" the notebook's video.
            if detected and await self._count_completed_cards(artifact_type) <= baseline_count:
                self.logger.error(f"❌ Timeout after {elapsed}s and no new {artifact_type} card appeared")
                detected = None
            if detected:
                result = await self._resolve_new_artifact(
                    detected, artifact_type, baseline_count, baseline_keys
                )
                self.logger.warning(
                    f"⚠️ Timeout after {elapsed}s but a completed {artifact_type} card is present — recovering it"
                )
                result['generation_time'] = elapsed
                result['recovered_after_timeout'] = True
                return result

            self.logger.error(f"❌ Generation timeout after {elapsed}s")
            return None

        except Exception as e:
            self.logger.error(f"❌ Error monitoring generation: {e}")
            return None

    async def _daily_limit_on_page(self, artifact_type: Optional[str] = None) -> Optional[str]:
        """The page's daily-limit sentence, read while a generation is watched.

        With ``artifact_type``, only a sentence naming that family counts
        ("Video Overview and Infographic" names both), so a limit left on the
        page by another family does not stop a Report.
        """
        try:
            limit = daily_limit_message(await self.page.inner_text('body'))
        except Exception:
            return None
        if limit and artifact_type:
            label = ARTIFACT_TYPES.get(artifact_type, {}).get('label')
            if label and label.lower() not in limit.lower():
                return None
        return limit

    async def _generation_in_progress(self) -> bool:
        """True when any Studio card is still generating (its main button disabled)."""
        try:
            return await self.page.query_selector(
                f'{ARTIFACT_CARD_SELECTOR} {GENERATING_CARD_MARKER}'
            ) is not None
        except Exception:
            return False

    async def _card_family_label(self, card) -> Optional[str]:
        """
        The family a Studio card belongs to: its aria-description when that
        names a known family, else the family its .artifact-icon names
        (Mind Map cards say only "Artifact").
        """
        label = None
        described = await card.query_selector('[aria-description]')
        if described:
            label = await described.get_attribute('aria-description')
        spec = get_artifact_spec(label or '')
        if spec:
            return spec['label']
        icon_el = await card.query_selector('.artifact-icon')
        icon = (await icon_el.inner_text()).strip() if icon_el else None
        return family_label_from_icon(icon) or label

    async def _ready_family_cards(self, artifact_type: str) -> list:
        """Visible cards of a family that have finished generating."""
        spec = get_artifact_spec(artifact_type)
        label = spec['label'] if spec else None
        if not label or not self.page:
            return []
        try:
            cards = await self.page.query_selector_all(ARTIFACT_CARD_SELECTOR)
        except Exception:
            return []
        ready = []
        for card in cards:
            try:
                if not await card.is_visible():
                    continue
                if await card.query_selector(GENERATING_CARD_MARKER):
                    continue
                if await card.query_selector(PENDING_REVIEW_MARKER):
                    continue
                if await self._card_family_label(card) == label:
                    ready.append(card)
            except Exception:
                continue
        return ready

    async def _paused_cards(self, artifact_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """The Studio cards stopped at a plan, of one family when it is named."""
        spec = get_artifact_spec(artifact_type) if artifact_type else None
        return [c for c in await self.list_studio_artifacts()
                if c.get('awaiting_review') and (not spec or c.get('family_label') == spec['label'])]

    async def _new_paused_card(self, artifact_type: str, known: set) -> Optional[Dict[str, Any]]:
        """A card of this family paused at a plan that was not paused before, newest first."""
        for card in await self._paused_cards(artifact_type):
            if card.get('artifact_id') not in known:
                card['status'] = 'awaiting_review'
                card['type'] = normalize_artifact_type(artifact_type) or artifact_type
                return card
        return None

    async def _count_completed_cards(self, artifact_type: str) -> int:
        """Count visible completed cards for an artifact family."""
        return len(await self._ready_family_cards(artifact_type))

    async def _card_identity(self, card) -> str:
        """
        Stable per-card identity that survives across two DOM snapshots.

        Prefers a real DOM id (data-artifact-id / data-id / id). Note the
        metadata extractor falls back to a RANDOM hash when the DOM exposes
        no id, and a random hash is not stable between snapshots — so identity
        here is instead computed directly from the element as a
        family+title+details fingerprint when no DOM id exists.
        """
        for attr in ('data-artifact-id', 'data-id', 'id'):
            try:
                value = await card.get_attribute(attr)
                if value:
                    return f'{attr}:{value}'
            except Exception:
                continue

        artifact_uuid = await self._card_artifact_uuid(card)
        if artifact_uuid:
            return f'artifact:{artifact_uuid}'

        # Title only: the details line carries a relative time ("· 2m ago")
        # that changes between two snapshots.
        parts: List[str] = []
        try:
            described = await card.query_selector('[aria-description]')
            if described:
                parts.append((await described.get_attribute('aria-description')) or '')
        except Exception:
            pass
        try:
            title_el = await card.query_selector('.artifact-title')
            if title_el:
                parts.append((await title_el.inner_text()).strip())
        except Exception:
            pass
        return 'fp:' + '|'.join(parts)

    @staticmethod
    async def _card_artifact_uuid(card) -> Optional[str]:
        """The artifact's UUID, carried by an inner id="artifact-labels-<uuid>"."""
        try:
            labels = await card.query_selector('[id^="artifact-labels-"]')
            if labels:
                return (await labels.get_attribute('id'))[len('artifact-labels-'):] or None
        except Exception:
            pass
        return None

    async def _completed_card_snapshot(self, artifact_type: str) -> List[Dict[str, Any]]:
        """
        Snapshot every visible completed card of a family with its identity.

        Each entry is the card's extracted metadata plus a ``card_key`` (from
        :meth:`_card_identity`), enabling a baseline-vs-current set diff that
        names the NEW card instead of the first-matched one.
        """
        type_key = normalize_artifact_type(artifact_type) or artifact_type
        snapshot: List[Dict[str, Any]] = []
        if not self.page:
            return snapshot

        for card in await self._ready_family_cards(artifact_type):
            try:
                meta = await self._extract_artifact_metadata(card)
                meta['status'] = 'completed'
                meta['type'] = type_key
                meta['card_key'] = await self._card_identity(card)
                snapshot.append(meta)
            except Exception:
                continue
        return snapshot

    async def _resolve_new_artifact(
        self,
        detected: Dict[str, Any],
        artifact_type: str,
        baseline_count: int,
        baseline_keys: Optional[set],
    ) -> Dict[str, Any]:
        """
        Return the metadata of the NEWLY generated card.

        On a fresh notebook (baseline_count == 0) ``detected`` is already the
        only card of the family. On a repeat generation, ``detected`` may be a
        pre-existing card (DOM-order first match); diff the current completed
        set against ``baseline_keys`` and return the ADDED card so session
        tracking never binds a fresh generation to a stale artifact's id/title.
        """
        # Diff even when the family had no card before: ``detected`` comes
        # from completion selectors whose generic fallbacks can match another
        # family's card (a report run once returned the video beside it).
        if baseline_keys is not None:
            snapshot = await self._completed_card_snapshot(artifact_type)
            added = [c for c in snapshot if c.get('card_key') not in baseline_keys]
            if added:
                # The Studio list is newest-first.
                new_card = added[0]
                new_card.pop('card_key', None)
                return new_card
        return detected

    async def _monitor_audio_generation(
        self,
        start_time: float,
        timeout: int,
        polling_interval: int,
        baseline_count: int = 0,
        baseline_keys: Optional[set] = None,
    ) -> Optional[Dict[str, Any]]:
        """Backward-compatible wrapper around _monitor_artifact_generation."""
        return await self._monitor_artifact_generation(
            start_time, timeout, polling_interval, artifact_type='audio_overview',
            baseline_count=baseline_count, baseline_keys=baseline_keys,
        )

    async def generate_studio_artifact(
        self,
        artifact_type: str,
        format: str = None,
        language: str = None,
        length: str = None,
        focus_prompt: str = None,
        notebook_id: str = None,
        template: str = None,
        review: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Generate any Studio artifact through its tile + customization dialog.

        Reports have their own dialog ("Create report"): a format
        (Interactive or Document), a template, and a Customize Report form
        with a language and a free prompt; ``template`` names the template.

        Covers the whole current Studio family: Slide Deck, Video Overview,
        Mind Map, Reports, Flashcards, Quiz, Infographic, Data Table.
        Audio Overview delegates to generate_audio_overview(), whose entry
        point (the pencil/edit icon) differs from the tile-dialog flow.

        The dialog flow follows the proven pattern: open the tile, work
        INSIDE the dialog locator (a globally-searched button can hit a
        background control instead), select format/language/length, fill the
        free-text prompt, click the dialog's Generate, then watch for the
        completed <artifact-library-item> card.

        Args:
            artifact_type: Registry key or display label (slide_deck, "Slide Deck", ...)
            format: Family-specific format (e.g. presenter/detailed for slide decks)
            language: Output language (display-mapped like Audio Overview)
            length: Length option where the family supports one
            focus_prompt: Free-text guidance for the generator
            notebook_id: Target notebook (navigates if provided)
            review: Turn on the dialog's review switch and stop at the plan
                (Slide Deck and Video Overview), status 'awaiting_review'.

        Returns:
            Artifact metadata dict, or None on failure.
        """
        type_key = normalize_artifact_type(artifact_type)
        if type_key is None:
            self.logger.error(f"❌ Unknown Studio artifact type: {artifact_type}")
            self.logger.info(f"💡 Known types: {', '.join(ARTIFACT_TYPES.keys())}")
            return None

        if type_key == 'audio_overview':
            return await self.generate_audio_overview(
                format=format, language=language, length=length,
                focus_prompt=focus_prompt, notebook_id=notebook_id
            )

        spec = get_artifact_spec(type_key)
        label = spec['label']

        if review and not spec.get('review_switch'):
            self.logger.error(f"❌ {label} has no review step; only Slide Deck and Video Overview have one")
            return None

        try:
            if not self.page:
                self.logger.error("❌ No browser page available")
                return None

            studio_config = self.config.get('STUDIO_SETTINGS', {}).get(type_key, {})
            generation_timeout = studio_config.get('generation_timeout', 900)
            polling_interval = studio_config.get('polling_interval', 5)
            format_display = normalize_artifact_format(type_key, format or studio_config.get('default_format'))
            language = language or studio_config.get('default_language')

            self.logger.info(f"🎨 Generating Studio artifact: {label}")
            if format_display:
                self.logger.info(f"   Format: {format_display}")
            if language:
                self.logger.info(f"   Language: {language}")
            if focus_prompt:
                preview = focus_prompt[:50] + '...' if len(focus_prompt) > 50 else focus_prompt
                self.logger.info(f"   Focus: {preview}")

            if notebook_id:
                if not await self.navigate_to_notebook(notebook_id=notebook_id):
                    return None

            await self.dismiss_rebrand_modal()
            await self._ensure_sources_tab_active()

            baseline_snapshot = await self._completed_card_snapshot(type_key)
            baseline_count = len(baseline_snapshot)
            baseline_keys = {c['card_key'] for c in baseline_snapshot}
            paused_before = (
                {c.get('artifact_id') for c in await self._paused_cards(type_key)} if review else None
            )

            generation_start_time = time.time()
            if type_key == 'reports':
                started = await self._drive_report_dialog(
                    format_display, template, language, focus_prompt)
            else:
                started = await self._drive_tile_dialog(
                    label, spec, format_display, language, length, focus_prompt, review=review)
            if not started:
                return None

            await self.page.wait_for_timeout(3000)
            self.logger.info(f"🔄 {label} generation started...")
            self.logger.info(f"⏳ Monitoring generation (timeout: {generation_timeout}s)...")

            artifact_data = await self._monitor_artifact_generation(
                generation_start_time,
                generation_timeout,
                polling_interval,
                artifact_type=type_key,
                baseline_count=baseline_count,
                baseline_keys=baseline_keys,
                start_timeout=studio_config.get('generation_start_timeout', GENERATION_START_TIMEOUT_S),
                stop_at_review=paused_before,
            )

            if not artifact_data:
                self.logger.error(f"❌ {label} generation failed or timed out")
                return None

            artifact_data['format'] = format_display
            if template:
                artifact_data['template'] = template
            artifact_data['language'] = language
            artifact_data['length'] = length
            artifact_data['focus_prompt'] = focus_prompt if focus_prompt else None

            if artifact_data.get('status') == 'awaiting_review':
                self.logger.info(f"⏸️ {label}: plan ready, nothing rendered yet")
            else:
                self.logger.info(f"✅ {label} generated successfully!")
            self.logger.info(f"📋 Artifact ID: {artifact_data.get('artifact_id', 'unknown')}")

            if notebook_id and self.session_tracker:
                try:
                    if self.session_tracker.add_artifact_to_notebook(notebook_id, artifact_data):
                        self.logger.info(f"📝 Artifact tracked in session for notebook {notebook_id}")
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not track artifact in session: {e}")

            return artifact_data

        except Exception as e:
            self.logger.error(f"❌ Failed to generate {label}: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None

    async def _open_iterate_dialog(self, card) -> Dict[str, Any]:
        """
        From one Studio card, open "View prompt and sources" and press its
        Iterate button (aria-label "Iterate", observed 2026-10-26 on a Video
        Overview card). Iterate opens the family's Customize dialog with the
        card's own prompt already in it.

        Returns {'dialog': locator or None, 'previous_prompt': str}. A card
        whose prompt dialog has no Iterate button returns dialog None, after
        closing what it opened.
        """
        dialogs = self.page.locator('mat-dialog-container, [role="dialog"]')
        await card.locator('button:has(mat-icon:text-is("more_vert")), button[aria-label*="More"]').first.click(timeout=5000)
        await self.page.get_by_role('menuitem', name=re.compile(r'view prompt', re.I)).first.click(timeout=5000)
        prompt_dialog = dialogs.last
        await prompt_dialog.wait_for(state='visible', timeout=10000)
        previous = ''
        try:
            previous = (await prompt_dialog.inner_text()).strip()
        except Exception:
            pass
        iterate = prompt_dialog.locator('button[aria-label="Iterate"], button.iterate-button').first
        if await iterate.count() == 0:
            await self._close_dialog(dialogs)
            return {'dialog': None, 'previous_prompt': previous}
        await iterate.click(timeout=5000)
        customize = dialogs.filter(has=self.page.locator('textarea')).last
        await customize.wait_for(state='visible', timeout=10000)
        try:
            previous = await customize.locator('textarea').first.input_value()
        except Exception:
            pass
        return {'dialog': customize, 'previous_prompt': previous}

    async def iterate_studio_artifact(self, ref: str, instruction: str, notebook_id: str = None,
                                      dry_run: bool = False, review: bool = False) -> Optional[Dict[str, Any]]:
        """
        Make a new version of a Studio artifact from its own prompt, revised.

        William, 2026-10-26: use "Iterate" from an existing video explainer to
        create a new version of an explainer. The card is named by artifact id
        or exact title. Where the card's prompt dialog has an Iterate button,
        its Customize dialog is filled with ``instruction`` and generated;
        otherwise the card's family is generated afresh with ``instruction``
        as its prompt. ``dry_run`` fills the dialog, reads it back and closes
        it without generating.
        """
        if not self.page:
            self.logger.error("❌ No browser page available")
            return None
        if notebook_id and not await self.navigate_to_notebook(notebook_id=notebook_id):
            return None
        await self.dismiss_rebrand_modal()

        cards = await self.list_studio_artifacts()
        matches = match_studio_cards(cards, ref)
        if not matches:
            self.logger.error(f"❌ No Studio card is titled or identified '{ref}'")
            return None
        if len(matches) > 1:
            self.logger.error(f"❌ {len(matches)} Studio cards are titled '{ref}'; name one by its artifact id")
            return None
        source = matches[0]
        type_key = normalize_artifact_type(source.get('family_label') or '')
        card = self.page.locator(ARTIFACT_CARD_SELECTOR).nth(source['dom_index'])

        opened = await self._open_iterate_dialog(card)
        base = {'iterated_from': {'artifact_id': source.get('artifact_id'), 'title': source.get('title'),
                                  'family_label': source.get('family_label')},
                'previous_prompt': opened['previous_prompt'], 'instruction': instruction}
        dialogs = self.page.locator('mat-dialog-container, [role="dialog"]')

        if opened['dialog'] is None:
            if dry_run or type_key is None:
                return {**base, 'mode': 'generate', 'dry_run': dry_run,
                        'reason': 'this card has no Iterate; a new one is generated from the instruction'}
            self.logger.info("ℹ️ No Iterate for this card: generating its family from the instruction")
            result = await self.generate_studio_artifact(type_key, focus_prompt=instruction, review=review)
            return {**result, **base, 'mode': 'generate'} if result else None

        textarea = opened['dialog'].locator('textarea').first
        await textarea.fill(instruction[:5000])
        spec = get_artifact_spec(type_key) if type_key else None
        if review:
            if not (spec and spec.get('review_switch')):
                self.logger.error("❌ This card's family has no review step; nothing generated")
                await self._close_dialog(dialogs)
                return None
            if not await self._turn_on_review(opened['dialog'], spec):
                await self._close_dialog(dialogs)
                return None
        if dry_run:
            filled = await textarea.input_value()
            await self._close_dialog(dialogs)
            return {**base, 'mode': 'iterate', 'dry_run': True, 'filled': filled, 'review': review}

        baseline_snapshot = await self._completed_card_snapshot(type_key) if type_key else []
        paused_before = {c.get('artifact_id') for c in await self._paused_cards(type_key)} if review else None
        start = time.time()
        await opened['dialog'].get_by_role('button', name=re.compile(r'^\s*generate', re.I)).first.click(timeout=10000)
        studio_config = self.config.get('STUDIO_SETTINGS', {}).get(type_key or '', {}) if hasattr(self, 'config') else {}
        result = await self._monitor_artifact_generation(
            start, studio_config.get('generation_timeout', 900), studio_config.get('polling_interval', 5),
            artifact_type=type_key, baseline_count=len(baseline_snapshot),
            baseline_keys={c['card_key'] for c in baseline_snapshot}, stop_at_review=paused_before)
        if not result:
            self.logger.error("❌ The iterated version did not appear")
            return None
        return {**result, **base, 'mode': 'iterate', 'focus_prompt': instruction}

    async def _drive_tile_dialog(self, label: str, spec: Dict[str, Any],
                                 format_display: Optional[str], language: Optional[str],
                                 length: Optional[str], focus_prompt: Optional[str],
                                 review: bool = False) -> bool:
        """Open a Studio tile, fill its customization dialog and press Generate."""
        # Open the tile → customization dialog.
        dialog = self.page.get_by_role('dialog').filter(has_text=label)
        if await dialog.count() == 0:
            tile_candidates = [
                self.page.get_by_role('button', name=label, exact=False),
                self.page.get_by_text(label, exact=False),
            ]
            # A family with options has a dialog to wait for. Mind Map starts from
            # its tile, so it keeps the short wait.
            expects_dialog = bool(spec.get('formats') or spec.get('supports_focus_prompt'))
            dialog_wait_ms = TILE_DIALOG_WAIT_MS if expects_dialog else 1500
            for tile in tile_candidates:
                try:
                    if await tile.count() > 0:
                        await tile.first.click(timeout=10000)
                        dialog = self.page.get_by_role('dialog').filter(has_text=label)
                        waited = 0
                        while waited < dialog_wait_ms and await dialog.count() == 0:
                            await self.page.wait_for_timeout(250)
                            waited += 250
                        if await dialog.count() > 0:
                            break
                except Exception:
                    continue

        dialog_open = await dialog.count() > 0

        if dialog_open:
            dialog = dialog.first

            if format_display:
                selected = False
                for option in [
                    dialog.get_by_role('radio', name=format_display, exact=False),
                    dialog.get_by_text(format_display, exact=False),
                ]:
                    try:
                        if await option.count() > 0:
                            await option.first.click(timeout=5000)
                            await self.page.wait_for_timeout(400)
                            selected = True
                            break
                    except Exception:
                        continue
                if selected:
                    self.logger.info(f"✅ Format selected: {format_display}")
                else:
                    self.logger.warning(f"⚠️ Could not select format '{format_display}', using default")

            if language and spec.get('supports_language'):
                await self._select_dialog_language(dialog, language)

            if length and spec.get('supports_length'):
                length_display = length.strip().capitalize()
                try:
                    # A segmented toggle whose buttons have role "radio" (2026-11-05).
                    toggle = dialog.get_by_role('radio', name=length_display, exact=True)
                    if await toggle.count() == 0:
                        toggle = dialog.get_by_role('button', name=length_display, exact=False)
                    if await toggle.count() > 0:
                        await toggle.first.click(timeout=5000)
                        self.logger.info(f"✅ Length selected: {length_display}")
                    else:
                        self.logger.warning(f"⚠️ Could not find length option '{length_display}'")
                except Exception:
                    self.logger.warning(f"⚠️ Could not select length '{length_display}'")

            if focus_prompt and spec.get('supports_focus_prompt'):
                focus_text = focus_prompt[:5000]
                filled = False
                try:
                    textarea = dialog.locator('textarea')
                    if await textarea.count() > 0:
                        await textarea.first.fill(focus_text)
                        filled = True
                except Exception:
                    pass
                if not filled:
                    try:
                        textboxes = dialog.get_by_role('textbox')
                        count = await textboxes.count()
                        if count > 0:
                            # Prefer the last textbox in case search fields precede it.
                            await textboxes.nth(count - 1).fill(focus_text)
                            filled = True
                    except Exception:
                        pass
                if filled:
                    self.logger.info(f"✅ Focus prompt entered ({len(focus_text)} chars)")
                else:
                    self.logger.warning("⚠️ Could not find prompt field in dialog")

            if review and not await self._turn_on_review(dialog, spec):
                await self._close_dialogs()
                return False

            # Generate — resolved INSIDE the dialog, never globally.
            clicked = False
            for generate in [
                dialog.get_by_role('button', name='Generate', exact=False),
                dialog.get_by_text('Generate', exact=False),
            ]:
                try:
                    if await generate.count() > 0:
                        await generate.first.click(timeout=10000)
                        clicked = True
                        break
                except Exception:
                    continue

            if not clicked:
                self.logger.error("❌ Could not click Generate in dialog")
                return False
        else:
            # The cause of this is not known yet (2026-11-05, twice, each on a tab
            # already used; not reproduced in replays), so say what the page shows.
            on_page = await self._overlay_text()
            if on_page:
                self.logger.warning(f"⚠️ No dialog for {label}; the page shows: {on_page}")
            if review:
                # A tile that started on its own has no plan to stop at.
                try:
                    limit = daily_limit_message(await self.page.inner_text('body'))
                except Exception:
                    limit = None
                self.logger.error(f"❌ {limit or 'No customization dialog opened'}; the review switch was not set")
                return False
            # Some tiles start generation immediately without a dialog;
            # continue to monitoring rather than treating this as failure.
            try:
                limit = daily_limit_message(await self.page.inner_text('body'))
            except Exception:
                limit = None
            if limit:
                self.logger.error(f"❌ Gemini Notebook says: {limit}. Nothing was generated; try again tomorrow.")
                return False
            self.logger.info("ℹ️ No customization dialog appeared — assuming generation started from tile")
        return True

    async def _overlay_text(self) -> str:
        """What a toast, an alert or an overlay is saying, for a failure's log line."""
        try:
            lines = await self.page.evaluate("""() => [...document.querySelectorAll(
                '.cdk-overlay-pane, mat-snack-bar-container, [role="alert"]')]
                .filter(e => e.offsetWidth || e.offsetHeight)
                .map(e => (e.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 160)).filter(Boolean)""")
            return ' | '.join(lines)
        except Exception:
            return ''

    async def _turn_on_review(self, dialog, spec: Dict[str, Any]) -> bool:
        """Turn on a Customize dialog's review switch, and read it back on."""
        name = spec.get('review_switch') or 'review'
        switch = dialog.locator('button[role="switch"]').first
        try:
            if await dialog.locator('button[role="switch"]').count() == 0:
                self.logger.error(f"❌ This dialog has no '{name}' switch; nothing generated")
                return False
            if await switch.get_attribute('aria-checked') != 'true':
                await switch.click(timeout=5000)
            for _ in range(10):
                if await switch.get_attribute('aria-checked') == 'true':
                    self.logger.info(f"✅ {name}: on")
                    return True
                await self.page.wait_for_timeout(300)
        except Exception as e:
            self.logger.error(f"❌ Could not turn on '{name}': {e}")
            return False
        self.logger.error(f"❌ '{name}' did not turn on; nothing generated")
        return False

    # ------------------------------------------------------------------
    # The review step: a plan read, saved, and sent on to render.
    # ------------------------------------------------------------------

    def _studio_panel(self):
        return self.page.locator('section.studio-panel, .studio-panel, studio-panel').first

    async def _find_paused_card(self, ref: Optional[str]) -> Optional[Dict[str, Any]]:
        """One card stopped at a plan: by artifact id, or the only one when none is named."""
        paused = await self._paused_cards()
        if ref:
            paused = [c for c in paused if c.get('artifact_id') == ref.strip()]
            if not paused:
                self.logger.error(f"❌ No Studio card {ref} is waiting for review")
                return None
            return paused[0]
        if len(paused) == 1:
            return paused[0]
        if not paused:
            self.logger.error("❌ No Studio card is waiting for review")
        else:
            ids = ', '.join(str(c.get('artifact_id')) for c in paused)
            self.logger.error(f"❌ {len(paused)} cards are waiting for review; name one: {ids}")
        return None

    async def _open_review_panel(self, paused: Dict[str, Any]) -> bool:
        """Press a paused card's Review. The plan opens in the Studio panel, not in a dialog."""
        cards = await self.page.query_selector_all(ARTIFACT_CARD_SELECTOR)
        index = paused.get('dom_index')
        if index is None or index >= len(cards):
            self.logger.error("❌ The paused card disappeared")
            return False
        button = await cards[index].query_selector(REVIEW_BUTTON_SELECTOR)
        if not button:
            self.logger.error("❌ The paused card has no Review button")
            return False
        await button.click()
        try:
            await self.page.wait_for_selector(PLAN_SELECTOR, timeout=15000, state='visible')
        except Exception:
            self.logger.error("❌ Review opened no plan")
            return False
        return True

    async def _read_review_panel(self) -> Dict[str, Any]:
        """The plan on screen: its step name, title, items, and its whole text."""
        return await self.page.evaluate("""() => {
            const clean = el => (el ? el.innerText : '').trim();
            const plan = document.querySelector('.plan-viewer-container .a2ui-plan-container');
            const active = document.querySelector('.plan-viewer-container .step-item-active .step-title');
            const items = [...document.querySelectorAll('.plan-viewer-container .a2ui-outline-item')]
                .map(item => clean(item.querySelector('.a2ui-outline-text') || item));
            return {
                step: clean(active),
                steps: [...document.querySelectorAll('.plan-viewer-container .step-title')].map(clean),
                title: clean(document.querySelector('.plan-viewer-container .a2ui-card-title-text')),
                items,
                text: clean(plan),
            };
        }""")

    async def _close_review_panel(self) -> None:
        """Leave the plan unsent: the panel's Close, which keeps the card paused."""
        try:
            close = self._studio_panel().locator('button[aria-label="Close"]').first
            if await close.count():
                await close.click(timeout=3000)
                await self.page.wait_for_timeout(600)
        except Exception as e:
            self.logger.warning(f"⚠️ Could not close the review panel: {e}")

    async def review_outline(self, ref: Optional[str], output_dir: str, notebook_id: str = None,
                             seeded_from: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Read a paused card's plan and save it. Studio is left as it was, still paused."""
        if not self.page:
            self.logger.error("❌ No browser page available")
            return None
        if notebook_id and not await self.navigate_to_notebook(notebook_id=notebook_id):
            return None
        await self.dismiss_rebrand_modal()
        paused = await self._find_paused_card(ref)
        if not paused or not await self._open_review_panel(paused):
            return None
        try:
            plan = await self._read_review_panel()
        finally:
            await self._close_review_panel()
        if plan_is_empty(plan):
            self.logger.error("❌ The plan on screen is empty; nothing saved")
            return None
        entry = save_outline(output_dir, plan, paused.get('artifact_id'), paused.get('family_label') or 'Artifact',
                             notebook_id=notebook_id, seeded_from=seeded_from)
        self.logger.info(f"📝 Plan saved: {entry['path']}")
        return {'card': paused, 'plan': plan, 'entry': entry}

    async def proceed_review(self, ref: str, output_dir: str, notebook_id: str = None,
                             feedback: Optional[str] = None, wait: bool = True) -> Optional[Dict[str, Any]]:
        """
        Send a paused card on to render, with feedback or without.

        This cannot be taken back: the deck or video renders at once and the
        plan cannot be refined after. Sending feedback IS proceeding: Enter in
        the feedback field closes the panel and renders with the feedback
        applied, with no second plan to read (2026-11-05). So the plan and the
        feedback are saved first, and nothing is pressed if either save fails.
        """
        if not self.page:
            self.logger.error("❌ No browser page available")
            return None
        if notebook_id and not await self.navigate_to_notebook(notebook_id=notebook_id):
            return None
        await self.dismiss_rebrand_modal()
        paused = await self._find_paused_card(ref)
        if not paused:
            return None
        family = paused.get('family_label') or 'Artifact'
        type_key = normalize_artifact_type(family) or family
        # Read the finished cards now: the panel hides them, and a baseline taken
        # behind it is empty, so the watch would return an older deck as the new one.
        baseline = await self._completed_card_snapshot(type_key)
        if not await self._open_review_panel(paused):
            return None

        plan = await self._read_review_panel()
        if plan_is_empty(plan):
            self.logger.error("❌ The plan on screen is empty; nothing saved and nothing sent")
            await self._close_review_panel()
            return None
        try:
            outline = save_outline(output_dir, plan, paused.get('artifact_id'), family, notebook_id=notebook_id)
            kept_feedback = save_feedback(output_dir, outline, feedback) if feedback else None
        except OSError as e:
            self.logger.error(f"❌ Could not save the plan, so nothing was sent: {e}")
            await self._close_review_panel()
            return None
        self.logger.info(f"📝 Plan saved: {outline['path']}")

        started_at = time.time()
        if feedback:
            field = self.page.locator(f'{PLAN_SELECTOR} textarea').first
            await field.fill(feedback)
            await field.press('Enter')
        else:
            await self.page.locator(PLAN_SELECTOR).get_by_role('button', name='Proceed').first.click(timeout=5000)

        # The card goes back to generating. Still paused means it was not accepted.
        accepted = False
        for _ in range(20):
            await self.page.wait_for_timeout(1500)
            if not await self.page.query_selector(PLAN_SELECTOR):
                still = [c for c in await self._paused_cards() if c.get('artifact_id') == paused.get('artifact_id')]
                if not still:
                    accepted = True
                    break
        if not accepted:
            limit = await self._daily_limit_on_page(type_key)
            self.logger.error(f"❌ {limit or 'The card is still waiting for review'}; nothing was rendered")
            self.last_generation_refusal = limit
            await self._close_review_panel()
            return None

        stamp = datetime.now().isoformat(timespec='seconds')
        record_proceed(output_dir, outline, proceeded_at=stamp, feedback_sent=bool(feedback))
        result: Dict[str, Any] = {'outline': outline, 'feedback': kept_feedback, 'card': paused,
                                  'proceeded_at': stamp, 'artifact': None}
        if not wait:
            return result

        studio_config = self.config.get('STUDIO_SETTINGS', {}).get(type_key, {}) if hasattr(self, 'config') else {}
        artifact = await self._monitor_artifact_generation(
            started_at, studio_config.get('generation_timeout', 1800), studio_config.get('polling_interval', 5),
            artifact_type=type_key, baseline_count=len(baseline),
            baseline_keys={c['card_key'] for c in baseline},
            start_timeout=studio_config.get('generation_start_timeout', GENERATION_START_TIMEOUT_S))
        if not artifact:
            self.logger.error("❌ The plan was sent on, and no finished card appeared within the watch")
            return None
        record_proceed(output_dir, outline, rendered_as={'artifact_id': artifact.get('artifact_id'),
                                                         'title': artifact.get('title')})
        result['artifact'] = artifact
        return result

    async def _drive_report_dialog(self, format_display: Optional[str], template: Optional[str],
                                   language: Optional[str], focus_prompt: Optional[str]) -> bool:
        """
        Fill and submit the "Create report" dialog (observed 2026-10-06).

        Format cards: Interactive ("An interactive report with embedded
        studio content", default) and Document ("A structured text-only
        document"). Each template is a div.option-card holding a
        button.primary-action-button named after it and, except Create Your
        Own, a "Customize Report" pencil that opens a language select and a
        prompt textarea. Generate is the dialog's nb-button.generate-button.
        """
        spec = ARTIFACT_TYPES['reports']
        dialog = self.page.get_by_role('dialog').filter(has_text=spec['dialog_title'])
        if await dialog.count() == 0:
            tile = self.page.locator('[role=button]:has-text("Reports")')
            if await tile.count() == 0:
                self.logger.error("❌ Reports tile not found in the Studio panel")
                return False
            await tile.first.click(timeout=10000)
            await self.page.wait_for_timeout(1500)
            if await dialog.count() == 0:
                self.logger.error("❌ The Create report dialog did not open")
                return False
        dialog = dialog.first

        format_display = format_display or 'Interactive'
        format_blurbs = {
            'Interactive': 'An interactive report with embedded studio content',
            'Document': 'A structured text-only document',
        }
        await dialog.locator(f'div:has-text("{format_blurbs[format_display]}")').last.click()
        await self.page.wait_for_timeout(1200)
        self.logger.info(f"✅ Report format: {format_display}")

        if not template:
            template = 'Learning Overview' if format_display == 'Interactive' else (
                'Create Your Own' if focus_prompt else 'Briefing Doc')
        template = normalize_report_template(template)
        card = dialog.locator(f'div.option-card:has(button.primary-action-button[aria-label="{template}"])')
        if await card.count() == 0:
            offered = await dialog.locator('button.primary-action-button').evaluate_all(
                "els => els.map(e => e.getAttribute('aria-label'))")
            self.logger.error(f"❌ Template '{template}' not offered; offered: {offered}")
            await self._close_dialogs()
            return False
        card = card.first

        if focus_prompt or language:
            pencil = card.locator('button[aria-label="Customize Report"]')
            if await pencil.count() > 0:
                await pencil.first.click()
            else:
                # Create Your Own has no pencil: the card itself opens the form.
                await card.locator('button.primary-action-button').first.click()
            await self.page.wait_for_timeout(1500)
            form = self.page.get_by_role('dialog').last
            if language:
                await self._select_dialog_language(form, language)
            if focus_prompt:
                prompt_box = form.locator('textarea')
                if await prompt_box.count() == 0:
                    self.logger.error("❌ The Customize Report form has no prompt field")
                    await self._close_dialogs()
                    return False
                await prompt_box.first.fill(focus_prompt[:5000])
                self.logger.info(f"✅ Report prompt entered ({len(focus_prompt[:5000])} chars)")
            generate = form.get_by_role('button', name='Generate')
        else:
            await card.locator('button.primary-action-button').first.click()
            await self.page.wait_for_timeout(600)
            generate = dialog.locator('nb-button.generate-button button')
            if await self.page.get_by_role('dialog').count() == 0:
                # Some templates start generation as soon as they are picked.
                self.logger.info(f"✅ Report template '{template}' started generation")
                return True

        self.logger.info(f"✅ Report template: {template}")
        if await generate.count() == 0:
            self.logger.error("❌ Generate button not found in the report dialog")
            await self._close_dialogs()
            return False
        await generate.first.click(timeout=10000)
        return True

    async def _close_dialogs(self) -> None:
        """Close any open dialog by its Close button."""
        for _ in range(3):
            close = self.page.get_by_role('dialog').locator(
                'button[aria-label="Close"], button[aria-label="Close dialog"]')
            if await close.count() == 0:
                return
            try:
                await close.first.click(timeout=3000)
                await self.page.wait_for_timeout(500)
            except Exception:
                return

    async def _select_dialog_language(self, dialog, language: str) -> bool:
        """Select an output language inside a Studio customization dialog."""
        language_display = LANGUAGE_DISPLAY_MAP.get(language.lower(), language.capitalize())
        try:
            select = dialog.locator('mat-select')
            if await select.count() == 0:
                self.logger.warning("⚠️ No language selector in dialog, using default")
                return False

            await select.first.click(timeout=5000)
            await self.page.wait_for_timeout(1500)

            option = self.page.locator(f'mat-option:has-text("{language_display}")')
            if await option.count() > 0:
                await option.first.click()
                await self.page.wait_for_timeout(500)
                self.logger.info(f"✅ Language selected: {language_display}")
                return True

            option = self.page.get_by_role('option', name=language_display, exact=False)
            if await option.count() > 0:
                await option.first.click()
                await self.page.wait_for_timeout(500)
                self.logger.info(f"✅ Language selected: {language_display}")
                return True

            # Close the overlay so it doesn't block later clicks.
            self.logger.warning(f"⚠️ Could not select language '{language_display}', using default")
            await self.page.keyboard.press('Escape')
            await self.page.wait_for_timeout(500)
            return False
        except Exception as e:
            self.logger.warning(f"⚠️ Language selection failed: {e}")
            return False

    async def resume_notebook(
        self,
        notebook_id: str,
        source_paths: List[str] = None,
        upload_attempts: int = 3,
    ) -> Dict[str, Any]:
        """
        Resume an existing notebook: upload only the sources it is missing.

        Prefer resume over recreate. The session tracker is the continuity
        layer: its per-notebook source list is diffed against source_paths,
        and only missing files are uploaded (with retry). Already-uploaded
        names are skipped so a partially-completed run continues instead of
        starting over.

        Args:
            notebook_id: The notebook to resume
            source_paths: Local files that SHOULD be in the notebook
            upload_attempts: Retries per file before recording failure

        Returns:
            Summary dict: notebook_id, existing/uploaded/failed source lists.
        """
        from .session_tracker import compute_missing_sources

        source_paths = source_paths or []
        summary: Dict[str, Any] = {
            'notebook_id': notebook_id,
            'existing_sources': [],
            'uploaded': [],
            'failed': [],
            'skipped': [],
        }

        existing_filenames = set()
        if self.session_tracker:
            notebook = self.session_tracker.get_notebook_by_id(notebook_id)
            if notebook:
                existing_filenames = {
                    src.get('filename') for src in notebook.get('sources', [])
                    if src.get('filename')
                }
        summary['existing_sources'] = sorted(existing_filenames)

        missing = compute_missing_sources(existing_filenames, source_paths)
        summary['skipped'] = [
            os.path.basename(p) for p in source_paths
            if os.path.basename(p) not in {os.path.basename(m) for m in missing}
        ]

        if not await self.navigate_to_notebook(notebook_id=notebook_id):
            summary['error'] = f'Failed to navigate to notebook {notebook_id}'
            return summary

        await self.dismiss_rebrand_modal()

        for path in missing:
            name = os.path.basename(path)
            uploaded_to = None
            last_error = None
            for attempt in range(1, upload_attempts + 1):
                try:
                    self.logger.info(f"📤 Uploading missing source ({attempt}/{upload_attempts}): {name}")
                    uploaded_to = await self.upload_document(path, notebook_id=notebook_id)
                    if uploaded_to:
                        break
                    last_error = 'upload_document returned no notebook id'
                except Exception as exc:
                    last_error = repr(exc)
                await asyncio.sleep(3)

            if uploaded_to:
                summary['uploaded'].append(name)
                if self.session_tracker:
                    try:
                        self.session_tracker.add_source_to_notebook(notebook_id, {
                            'filename': name,
                            'path': path,
                            'type': Path(path).suffix.lstrip('.').lower() or 'unknown',
                            'size': os.path.getsize(path) if os.path.exists(path) else 0,
                        })
                    except Exception as e:
                        self.logger.warning(f"⚠️ Could not track source in session: {e}")
            else:
                summary['failed'].append({'filename': name, 'error': last_error})
                self.logger.error(f"❌ Upload failed for {name}: {last_error}")

        if self.session_tracker and summary['uploaded']:
            try:
                notebook = self.session_tracker.get_notebook_by_id(notebook_id) or {}
                self.session_tracker.update_notebook(notebook_id, {
                    'status': 'sources_uploaded',
                    'source_count': len(notebook.get('sources', [])),
                })
            except Exception:
                pass

        return summary

    async def _extract_artifact_metadata(self, artifact_element) -> Dict[str, Any]:
        """
        Extract metadata from a completed artifact element.

        Args:
            artifact_element: Playwright element handle for artifact

        Returns:
            Dict[str, Any]: Artifact metadata
        """
        try:
            # Try to extract artifact ID from element attributes
            artifact_id = None
            for attr in ['data-artifact-id', 'data-id', 'id']:
                try:
                    artifact_id = await artifact_element.get_attribute(attr)
                    if artifact_id:
                        break
                except:
                    continue

            if not artifact_id:
                artifact_id = await self._card_artifact_uuid(artifact_element)

            # If no ID attribute, generate one
            if not artifact_id:
                import hashlib
                timestamp = datetime.now().isoformat()
                artifact_id = hashlib.md5(timestamp.encode()).hexdigest()[:12]

            # Extract timestamp if available
            created_at = datetime.now().isoformat()
            try:
                timestamp_element = await artifact_element.query_selector('.timestamp, .created-at, [data-timestamp]')
                if timestamp_element:
                    timestamp_text = await timestamp_element.inner_text()
                    if timestamp_text:
                        created_at = timestamp_text
            except:
                pass

            artifact_title = None
            artifact_details = None
            try:
                title_element = await artifact_element.query_selector('.artifact-title, .title-container .artifact-title')
                if title_element:
                    artifact_title = (await title_element.inner_text()).strip()
            except:
                pass

            try:
                details_element = await artifact_element.query_selector('.artifact-details')
                if details_element:
                    artifact_details = ' '.join((await details_element.inner_text()).split())
            except:
                pass

            return {
                'artifact_id': artifact_id,
                'created_at': created_at,
                'title': artifact_title,
                'details': artifact_details,
            }

        except Exception as e:
            self.logger.warning(f"⚠️ Could not extract full metadata: {e}")
            # Return minimal metadata
            import hashlib
            timestamp = datetime.now().isoformat()
            return {
                'artifact_id': hashlib.md5(timestamp.encode()).hexdigest()[:12],
                'created_at': timestamp,
                'title': None,
                'details': None,
            }

    async def _ensure_sources_tab_active(self):
        """
        Ensure the Sources tab is active (where Studio panel is located).

        Helper method used by Studio artifact generation.
        """
        try:
            sources_tab_selectors = [
                'button[role="tab"]:has-text("Sources")',
                '[role="tab"][aria-label*="Sources"]',
                '.tab-button:has-text("Sources")'
            ]

            for selector in sources_tab_selectors:
                try:
                    sources_tab = await self.page.wait_for_selector(selector, timeout=5000)
                    if sources_tab:
                        is_active = await sources_tab.get_attribute('aria-selected')
                        if is_active != 'true':
                            self.logger.info("📑 Switching to Sources tab...")
                            await sources_tab.click()
                            await self.page.wait_for_timeout(1000)
                        return
                except:
                    continue

        except Exception as e:
            self.logger.warning(f"⚠️ Could not ensure Sources tab: {e}")
    
    async def download_audio(self, output_path: str,
                             artifact: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Download the generated audio file.

        The Audio Overview card's own More > Download menu is tried first
        (matched by ``artifact['title']`` when given, else the newest Audio
        Overview card). The player/overflow-menu path below remains for the
        older UI.

        The final extension is derived from the browser's suggested filename
        (NotebookLM commonly hands back an ``.m4a`` container) rather than the
        hardcoded ``.mp3`` the caller may have requested: the caller's stem is
        kept, only the extension is swapped when the browser disagrees, so the
        saved filename never lies about its container.

        Args:
            output_path (str): Desired path (stem is honored; extension may be
                               corrected to match the download).

        Returns:
            Optional[str]: The REAL path the file was saved to on success (so
                           callers/manifests reflect the true file), or None
                           on failure.
        """
        try:
            if not self.page:
                self.logger.error("❌ No browser page available")
                return None

            self.logger.info(f"⬇️ Downloading audio to: {output_path}")

            card = await self._find_artifact_card(
                'Audio Overview', title=(artifact or {}).get('title'))
            if card is not None:
                saved_path, reason = await self._download_card_via_menu(card, output_path)
                if saved_path:
                    self.logger.info(f"✅ Audio download completed → {saved_path}")
                    return saved_path
                self.logger.warning(f"⚠️ Card menu download failed ({reason}); trying player controls")

            selector, download_target = await self._prepare_download_target()
            if not download_target:
                self.logger.error("❌ Could not find download button")
                return None

            if selector and selector.startswith('a'):
                await download_target.evaluate(
                    """(el) => {
                        el.removeAttribute('target');
                        el.setAttribute('target', '_self');
                    }"""
                )

            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

            # Set up download handling
            async with self.page.expect_download() as download_info:
                await download_target.click()

            download = await download_info.value
            suggested = getattr(download, 'suggested_filename', None)
            self.logger.info(f"📥 Browser suggested filename: {suggested}")

            # Honor the real container: keep the caller's stem, swap the
            # extension when the browser's suggestion differs.
            final_path = output_path
            if suggested:
                suggested_ext = os.path.splitext(suggested)[1]
                current_ext = os.path.splitext(output_path)[1]
                if suggested_ext and suggested_ext.lower() != current_ext.lower():
                    stem = os.path.splitext(output_path)[0]
                    final_path = stem + suggested_ext
                    self.logger.info(
                        f"🔤 Adjusting extension {current_ext or '(none)'} → {suggested_ext} "
                        f"to match the downloaded container"
                    )

            os.makedirs(os.path.dirname(final_path) or '.', exist_ok=True)
            await download.save_as(final_path)

            if not os.path.exists(final_path) or os.path.getsize(final_path) == 0:
                self.logger.error("❌ Download finished but no file was saved")
                return None

            self.logger.info(f"✅ Audio download completed → {final_path}")
            return final_path

        except Exception as e:
            self.logger.error(f"❌ Failed to download audio: {e}")
            return None
    
    @staticmethod
    def _probe_media(path: str) -> Optional[Dict[str, Any]]:
        """
        Sanity-check a downloaded media file with ffprobe when available.

        A zero-byte check alone can pass on a corrupt download; codec +
        duration from ffprobe is the stronger signal the skills workflow
        relied on. Returns None when ffprobe is absent or probing fails.
        """
        try:
            if not shutil.which('ffprobe'):
                return None
            import json as _json
            result = subprocess.run(
                ['ffprobe', '-v', 'quiet', '-print_format', 'json',
                 '-show_format', '-show_streams', path],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                return None
            data = _json.loads(result.stdout or '{}')
            fmt = data.get('format', {})
            streams = data.get('streams', [])
            codec = streams[0].get('codec_name') if streams else None
            return {
                'duration_seconds': float(fmt['duration']) if fmt.get('duration') else None,
                'codec': codec,
            }
        except Exception:
            return None

    @staticmethod
    def _sha256_file(path: str) -> Optional[str]:
        """Compute sha256 of a file for the download manifest."""
        try:
            import hashlib
            h = hashlib.sha256()
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b''):
                    h.update(chunk)
            return h.hexdigest()
        except Exception:
            return None

    def _read_prior_manifest(self, manifest_path: str) -> Dict[str, Any]:
        """The folder's manifest.json, or nothing when it has none or cannot be read."""
        import json as _json

        if not os.path.exists(manifest_path):
            return {}
        try:
            with open(manifest_path, encoding='utf-8') as f:
                prior = _json.load(f)
            return prior if isinstance(prior, dict) else {}
        except (OSError, ValueError) as e:
            self.logger.warning(f"⚠️ Could not read {manifest_path}: {e}")
            return {}

    async def download_all_artifacts(
        self,
        output_dir: str,
        notebook_id: str = None,
    ) -> Dict[str, Any]:
        """
        Download every downloadable artifact in the Studio panel.

        The end-of-run export: every card is offered its own More > Download
        menu item, and the cards whose menu has none (Mind Map) are skipped
        with that reason. Files land in output_dir next to a manifest.json
        recording title, path, sha256, and byte size — the shape cross-device
        sync tooling needs to ship artifacts to other nodes.

        A folder whose manifest.json already holds a card is not sent it again:
        only new cards are downloaded, and they join the manifest's downloads
        (2026-10-30 and 2026-11-03: every run fetched and re-encoded each
        artifact under a new name and overwrote the manifest). A new folder
        gets everything.

        Args:
            output_dir: Directory for downloaded files + manifest.json
            notebook_id: Navigate to this notebook first (uses current page
                         if None)

        Returns:
            Manifest dict: notebook_id, downloads[], skipped[], manifest_path,
            and for the caller, not written to the file, fresh[] (this run's
            downloads) and already[] (titles the folder holds).
        """
        import json as _json

        os.makedirs(output_dir, exist_ok=True)
        manifest_path = os.path.join(output_dir, 'manifest.json')
        prior = self._read_prior_manifest(manifest_path)
        manifest: Dict[str, Any] = {
            'notebook_id': notebook_id,
            'created_at': prior.get('created_at') or datetime.now().isoformat(),
            'downloads': list(prior.get('downloads') or []),
            'skipped': [],   # the card offers no Download
            'failed': [],    # a download was attempted and did not land
        }
        held = list(manifest['downloads'])
        already: List[str] = []

        if notebook_id:
            if not await self.navigate_to_notebook(notebook_id=notebook_id):
                manifest['error'] = f'Failed to navigate to notebook {notebook_id}'
                return manifest
            await self.dismiss_rebrand_modal()

        artifacts = await self.list_studio_artifacts()
        self.logger.info(f"📦 Found {len(artifacts)} artifact card(s) in Studio panel")

        for index, artifact in enumerate(artifacts):
            title = artifact.get('title') or f'artifact-{index + 1}'
            family_label = artifact.get('family_label') or 'Artifact'

            if card_is_held(artifact, held):
                already.append(title)
                continue

            safe_title = ''.join(
                ch if ch.isalnum() or ch in ('-', '_') else '-' for ch in title.strip()
            ).strip('-') or f'artifact-{index + 1}'
            timestamp = datetime.now().strftime('%Y%m%dT%H%M%S')
            # No extension: _capture_download appends the one the browser's
            # suggested filename carries (.m4a, .mp4, .png, ...).
            output_path = os.path.join(output_dir, f'{safe_title}-{timestamp}')

            try:
                # Re-locate the SAME card by its stable DOM index, never by this
                # loop's ordinal (which counts a visibility-filtered list while
                # the DOM list is unfiltered — the wrong-artifact bug).
                dom_index = artifact.get('dom_index')
                cards = await self.page.query_selector_all(ARTIFACT_CARD_SELECTOR)
                if dom_index is None or dom_index >= len(cards):
                    manifest['failed'].append({'title': title, 'reason': 'card disappeared'})
                    continue

                if artifact.get('generating'):
                    manifest['skipped'].append({'title': title, 'reason': f'{family_label}: still generating'})
                    continue

                if artifact.get('awaiting_review'):
                    manifest['skipped'].append({
                        'title': title, 'artifact_id': artifact.get('artifact_id'),
                        'reason': f'{family_label}: waiting for review, nothing rendered yet; `studio outline` saves its plan',
                    })
                    continue

                if family_label == 'Reports':
                    saved, reason = await self.save_report_card(cards[dom_index], output_path, title=title)
                    if not saved:
                        manifest['failed'].append({'title': title, 'reason': f'{family_label}: {reason}'})
                        continue
                    entry = {
                        'title': title,
                        'family_label': family_label,
                        'artifact_id': artifact.get('artifact_id'),
                        'path': saved['path'],
                        'html_path': saved['html_path'],
                        'size': os.path.getsize(saved['path']),
                        'sha256': self._sha256_file(saved['path']),
                        'downloaded_at': datetime.now().isoformat(),
                    }
                    manifest['downloads'].append(entry)
                    self.logger.info(f"✅ Saved report: {title} → {saved['path']}")
                    continue

                # The card's own menu decides: a family is downloadable exactly
                # when its menu offers Download (Mind Map, for one, does not).
                saved_path, reason = await self._download_card_via_menu(cards[dom_index], output_path)
                if not saved_path:
                    bucket = 'skipped' if reason in self._NOT_DOWNLOADABLE_REASONS else 'failed'
                    self.logger.info(f"⏭️ {title}: {reason}")
                    manifest[bucket].append({'title': title, 'reason': f'{family_label}: {reason}'})
                    continue

                entry = {
                    'title': title,
                    'family_label': artifact.get('family_label'),
                    'artifact_id': artifact.get('artifact_id'),
                    'path': saved_path,
                    'size': os.path.getsize(saved_path),
                    'sha256': self._sha256_file(saved_path),
                    'downloaded_at': datetime.now().isoformat(),
                }
                media_info = self._probe_media(saved_path)
                if media_info:
                    entry['media'] = media_info
                manifest['downloads'].append(entry)
                self.logger.info(f"✅ Downloaded: {title} → {saved_path}")

                if notebook_id and self.session_tracker:
                    try:
                        self.session_tracker.record_artifact_download(
                            notebook_id, artifact.get('artifact_id'), entry
                        )
                    except Exception as e:
                        self.logger.warning(f"⚠️ Could not record download in session: {e}")
            except Exception as e:
                manifest['failed'].append({'title': title, 'reason': repr(e)})
                self.logger.warning(f"⚠️ Download failed for {title}: {e}")

        try:
            with open(manifest_path, 'w', encoding='utf-8') as f:
                _json.dump(manifest, f, indent=2, ensure_ascii=False)
            manifest['manifest_path'] = manifest_path
            manifest['fresh'] = manifest['downloads'][len(held):]
            manifest['already'] = already
            self.logger.info(f"🗂️ Manifest written: {manifest_path}")
        except Exception as e:
            self.logger.warning(f"⚠️ Could not write manifest: {e}")

        return manifest

    async def create_notebook(self) -> Optional[Dict[str, Any]]:
        """
        Create a new notebook and capture its identity.

        Returns:
            Optional[Dict[str, Any]]: Notebook metadata including id, url, and created_at
                                       Returns None if creation fails
        """
        try:
            if not self.page:
                self.logger.error("❌ No browser page available")
                return None

            # Store the current URL to detect navigation
            initial_url = self.page.url

            # Multi-selector strategy for create button
            create_selectors = [
                'button[aria-label="New notebook"]',
                'button[aria-label="Create new notebook"]',
                'button:has-text("Create new notebook")',
                'button:has-text("New notebook")',
                '[data-testid="create-notebook"]',
                'button.create-notebook-btn'
            ]

            create_button = None
            for selector in create_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element:
                        create_button = element
                        self.logger.info(f"✅ Found create button: {selector}")
                        break
                except:
                    continue

            if not create_button:
                self.logger.error("❌ Could not find 'Create new notebook' button")
                screenshot_path = "debug/create_button_not_found.png"
                await self.page.screenshot(path=screenshot_path)
                self.logger.info(f"📸 Screenshot saved to {screenshot_path}")
                return None

            self.logger.info("📓 Creating new notebook...")
            await create_button.click()

            # Wait for navigation and page load (using load instead of networkidle for better reliability)
            try:
                await self.page.wait_for_load_state('load', timeout=15000)
            except:
                # If load state times out, continue anyway - the navigation might still have worked
                self.logger.warning("⚠️ Load state timeout, but continuing...")
                pass

            # The app first routes to /notebook/creating and only then to
            # /notebook/<uuid>; reloading the transient route hangs on
            # "Creating your notebook..." (observed 2026-10-06).
            try:
                await self.page.wait_for_url(
                    re.compile(r'/notebook/[0-9a-f]{8}-[0-9a-f]{4}-'), timeout=60000)
            except Exception:
                self.logger.warning(f"⚠️ Notebook URL has no ID yet: {self.page.url}")

            # Get the new URL
            new_url = self.page.url

            # Verify we navigated away from the initial URL
            if new_url == initial_url:
                self.logger.warning("⚠️ URL did not change after clicking create button")
                # Wait a bit more and try again
                await asyncio.sleep(2)
                new_url = self.page.url

            # Extract notebook ID from URL
            # Expected format: https://notebooklm.google.com/notebook/{notebook_id}
            notebook_id = None
            if '/notebook/' in new_url:
                parts = new_url.split('/notebook/')
                if len(parts) > 1:
                    # Get the ID (might have query params, so split on ? first)
                    notebook_id = parts[1].split('?')[0].split('#')[0]

            if not notebook_id:
                self.logger.warning("⚠️ Could not extract notebook ID from URL")
                self.logger.info(f"Current URL: {new_url}")
                # Try alternative extraction methods
                # Some URLs might be like: /notebook/abc123/sources or /notebook/abc123/overview
                if '/notebook/' in new_url:
                    path_parts = new_url.split('/')
                    notebook_idx = path_parts.index('notebook')
                    if len(path_parts) > notebook_idx + 1:
                        notebook_id = path_parts[notebook_idx + 1]

            # Wait for notebook UI to be ready
            try:
                await self.page.wait_for_selector('mat-card.create-new-action-button', timeout=15000)
                self.logger.info("✅ Notebook UI loaded successfully")
            except:
                self.logger.warning("⚠️ Notebook UI selector not found, but continuing...")

            # Create metadata object
            from datetime import datetime
            notebook_data = {
                'id': notebook_id or 'unknown',
                'url': new_url,
                'created_at': datetime.now().isoformat(),
                'title': 'Untitled Notebook',  # Can be updated later
                'sources': [],
                'active': True
            }

            self.logger.info(f"✅ Notebook created successfully!")
            self.logger.info(f"📋 Notebook ID: {notebook_data['id']}")
            self.logger.info(f"🔗 Notebook URL: {notebook_data['url']}")

            return notebook_data

        except Exception as e:
            self.logger.error(f"❌ Failed to create notebook: {e}")
            if self.page:
                try:
                    screenshot_path = "debug/create_notebook_error.png"
                    await self.page.screenshot(path=screenshot_path, timeout=5000)
                    self.logger.info(f"📸 Screenshot saved to {screenshot_path}")
                except:
                    self.logger.warning("⚠️ Could not save screenshot")
            return None

    async def navigate_to_notebook(self, notebook_id: str = None, notebook_url: str = None) -> bool:
        """
        Navigate to an existing notebook by ID or URL.

        Args:
            notebook_id (str): The notebook ID to navigate to
            notebook_url (str): The full notebook URL (alternative to notebook_id)

        Returns:
            bool: True if navigation successful, False otherwise
        """
        try:
            if not self.page:
                self.logger.error("❌ No browser page available")
                return False

            # Construct URL if only ID is provided
            target_url = notebook_url
            if not target_url and notebook_id:
                target_url = f"{self.base_url}/notebook/{notebook_id}"

            if not target_url:
                self.logger.error("❌ Must provide either notebook_id or notebook_url")
                return False

            self.logger.info(f"🔄 Navigating to notebook: {target_url}")

            # Prefer a tab that already has this notebook open: reusing it
            # preserves live state (player, generation progress). A goto on the
            # reused tab would reload it and destroy exactly that state, so the
            # goto runs ONLY when we are not already there.
            existing_page = await self.find_open_notebook_page(notebook_id)
            already_here = bool(
                existing_page and notebook_id and notebook_id in (existing_page.url or '')
            )
            if already_here:
                self.page = existing_page
                await existing_page.bring_to_front()
                self.logger.info("♻️ Reusing already-open notebook tab (skipping reload to preserve live state)")
            else:
                # Navigate to the notebook URL
                await self.page.goto(target_url, timeout=30000)

            # Wait for load state (use 'load' instead of 'networkidle' - networkidle can hang with background polling)
            try:
                await self.page.wait_for_load_state('load', timeout=10000)
            except:
                # If load state times out, continue anyway - URL check below will verify
                self.logger.warning("⚠️ Load state timeout, but continuing with URL verification...")

            # Clear the welcome/rebrand modal before any interaction.
            await self.dismiss_rebrand_modal()
            # A viewer left open by an earlier command survives a navigation
            # to the same notebook and hides the Studio panel.
            try:
                await self.close_open_artifact_viewer()
            except Exception as e:
                self.logger.warning(f"⚠️ Could not check for an open artifact viewer: {e}")

            # Verify notebook loaded successfully
            # First check if URL contains /notebook/ - most reliable indicator
            current_url = self.page.url
            # A signed-out profile lands on accounts.google.com with the
            # notebook URL in its continue= parameter; a substring test on
            # '/notebook/' accepted that page (2026-10-07).
            if _is_signed_out_url(current_url):
                self.logger.error("❌ Not signed in to Google in this Chrome profile: "
                                  "sign in at the Chrome window, then retry")
                return False
            if _is_notebook_url(current_url):
                self.logger.info(f"✅ Notebook URL verified: {current_url}")
                self.logger.info(f"✅ Successfully navigated to notebook")
                return True

            # Multi-selector strategy for notebook verification
            notebook_indicators = [
                'mat-card.create-new-action-button',  # Sources panel
                'h2:has-text("Add sources")',          # Add sources dialog header
                'div[role="dialog"]',                  # Any dialog (add sources)
                'button:has-text("Audio Overview")',  # Audio Overview button
                '[data-testid="notebook-content"]',   # Notebook content area
                '.notebook-title',                     # Notebook title
                'div.sources-panel'                    # Sources panel
            ]

            notebook_loaded = False
            for selector in notebook_indicators:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=10000)
                    if element:
                        self.logger.info(f"✅ Notebook verified: {selector}")
                        notebook_loaded = True
                        break
                except:
                    continue

            if not notebook_loaded:
                self.logger.warning("⚠️ Could not verify notebook UI elements")
                screenshot_path = "debug/notebook_verification_failed.png"
                await self.page.screenshot(path=screenshot_path)
                self.logger.info(f"📸 Screenshot saved to {screenshot_path}")
                # Don't fail completely - URL navigation might still have worked
                return True

            current_url = self.page.url
            self.logger.info(f"✅ Successfully navigated to notebook")
            self.logger.info(f"🔗 Current URL: {current_url}")

            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to navigate to notebook: {e}")
            if self.page:
                screenshot_path = "debug/navigate_notebook_error.png"
                await self.page.screenshot(path=screenshot_path)
                self.logger.info(f"📸 Screenshot saved to {screenshot_path}")
            return False

    async def _dismiss_preexisting_dialogs(self) -> bool:
        """Dismiss blocking NotebookLM overlays before clicking page-level controls."""
        if not self.page:
            return False

        overlay_selectors = [
            '.cdk-overlay-backdrop',
            '.cdk-overlay-pane',
            'div[role="dialog"]',
        ]

        overlay_visible = False
        for selector in overlay_selectors:
            try:
                element = await self.page.query_selector(selector)
                if element and await element.is_visible():
                    overlay_visible = True
                    self.logger.info(f"⚠️ Dismissing blocking overlay before share: {selector}")
                    break
            except:
                continue

        if not overlay_visible:
            return False

        try:
            await self.page.keyboard.press('Escape')
            await self.page.wait_for_timeout(500)
            return True
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to dismiss overlay with Escape: {e}")
            return False

    async def _dismiss_nested_overlay_backdrop(self) -> bool:
        """Dismiss transient Angular/Material backdrops without closing the main share dialog."""
        if not self.page:
            return False

        backdrop_selectors = [
            '.cdk-overlay-backdrop.cdk-overlay-backdrop-showing',
            '.cdk-overlay-backdrop',
        ]

        for selector in backdrop_selectors:
            try:
                element = await self.page.query_selector(selector)
                if element and await element.is_visible():
                    self.logger.info(f"⚠️ Dismissing nested share overlay backdrop: {selector}")
                    await self.page.keyboard.press('Escape')
                    await self.page.wait_for_timeout(500)
                    return True
            except Exception:
                continue

        return False

    async def share_notebook(self, email: str, role: str = 'editor') -> bool:
        """
        Share the current notebook with a collaborator via email.

        Args:
            email (str): Email address of the person to share with
            role (str): Role to grant ('editor' or 'viewer')

        Returns:
            bool: True if sharing successful, False otherwise
        """
        try:
            if not self.page:
                self.logger.error("❌ No browser page available")
                return False

            self.logger.info(f"👥 Sharing notebook with {email} as {role}...")
            await self._dismiss_preexisting_dialogs()

            # Multi-selector strategy for share button
            share_button_selectors = [
                'button[aria-label="Share"]',
                'button:has-text("Share")',
                'button[title="Share"]',
                '[data-testid="share-button"]',
                'button.share-button'
            ]

            # Find and click share button
            share_button = None
            for selector in share_button_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element:
                        share_button = element
                        self.logger.info(f"✅ Found share button: {selector}")
                        break
                except:
                    continue

            if not share_button:
                self.logger.error("❌ Could not find share button")
                screenshot_path = "debug/share_button_not_found.png"
                await self.page.screenshot(path=screenshot_path, timeout=5000)
                self.logger.info(f"📸 Screenshot saved to {screenshot_path}")
                return False

            # Click share button
            await share_button.click()
            await asyncio.sleep(1)

            # Wait for share dialog to appear
            dialog_selectors = [
                'div[role="dialog"]',
                '.share-dialog',
                '[data-testid="share-dialog"]',
                'div.modal'
            ]

            dialog_found = False
            for selector in dialog_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    dialog_found = True
                    self.logger.info(f"✅ Share dialog opened: {selector}")
                    break
                except:
                    continue

            if not dialog_found:
                self.logger.warning("⚠️ Could not verify share dialog opened")

            # Find email input field
            email_input_selectors = [
                'mat-dialog-container input#mat-input-1',
                'mat-dialog-container input[peoplekitautocomplete]',
                'input[type="email"]',
                'input[aria-label*="email"]',
                'input[aria-label*="Add people"]',
                'input[aria-label*="people and groups"]',
                'input[placeholder*="email"]',
                'input.share-email-input',
                'mat-dialog-container input',
                'div[role="dialog"] input',
                'div[role="dialog"] [role="combobox"]',
                'div[role="dialog"] [contenteditable="true"]',
                'label:has-text("Add people and groups") + div input',
                'label:has-text("Add people and groups") + div [role="combobox"]'
            ]

            email_input = None
            for selector in email_input_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element:
                        email_input = element
                        self.logger.info(f"✅ Found email input: {selector}")
                        break
                except:
                    continue

            if not email_input:
                self.logger.error("❌ Could not find email input field")
                screenshot_path = "debug/email_input_not_found.png"
                await self.page.screenshot(path=screenshot_path, timeout=5000)
                self.logger.info(f"📸 Screenshot saved to {screenshot_path}")
                return False

            # Type email address
            await email_input.click()
            await asyncio.sleep(0.5)
            await self.page.keyboard.type(email, delay=50)
            await asyncio.sleep(1)

            # Google share dialogs often need Enter to convert typed text into a recipient chip.
            try:
                await self.page.keyboard.press('Enter')
                await asyncio.sleep(1)
            except:
                pass

            # Select role if dropdown available
            if role != 'editor':
                role_selectors = [
                    'select[aria-label*="role"]',
                    'button[aria-label*="Can edit"]',
                    '.role-selector'
                ]

                for selector in role_selectors:
                    try:
                        role_element = await self.page.wait_for_selector(selector, timeout=3000)
                        if role_element:
                            await role_element.click()
                            await asyncio.sleep(0.5)

                            # Click viewer option
                            viewer_selectors = [
                                'li:has-text("Can view")',
                                'button:has-text("Viewer")',
                                '[data-value="viewer"]'
                            ]

                            for viewer_sel in viewer_selectors:
                                try:
                                    viewer_option = await self.page.wait_for_selector(viewer_sel, timeout=2000)
                                    if viewer_option:
                                        await viewer_option.click()
                                        break
                                except:
                                    continue
                            break
                    except:
                        continue

            # Send/Submit invitation
            send_button_selectors = [
                'mat-dialog-container button:has-text("Save")',
                'mat-dialog-container button:has-text("Send")',
                'mat-dialog-container button:has-text("Share")',
                'mat-dialog-container button:has-text("Invite")',
                'mat-dialog-container button[aria-label="Send"]',
                'mat-dialog-container button[type="submit"]',
                'div[role="dialog"] button:has-text("Save")',
                'div[role="dialog"] button:has-text("Send")',
                'div[role="dialog"] button:has-text("Share")',
                'div[role="dialog"] button:has-text("Invite")',
                'div[role="dialog"] button[aria-label="Send"]',
                'div[role="dialog"] button[type="submit"]',
                'button:has-text("Save")',
                'button:has-text("Send")',
                'button:has-text("Invite")',
                'button[aria-label="Send"]',
                'button[type="submit"]'
            ]

            send_button = None
            for selector in send_button_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element:
                        # Check if button is enabled
                        is_disabled = await element.get_attribute('disabled')
                        if not is_disabled:
                            send_button = element
                            self.logger.info(f"✅ Found send button: {selector}")
                            break
                except:
                    continue

            if not send_button:
                self.logger.error("❌ Could not find send button")
                # Try pressing Enter as fallback
                self.logger.info("⚡ Trying Enter key as fallback...")
                await self.page.keyboard.press('Enter')
                await asyncio.sleep(2)
            else:
                try:
                    await send_button.click()
                except Exception as click_error:
                    if 'intercepts pointer events' not in str(click_error):
                        raise

                    self.logger.warning(
                        f"⚠️ Send button click intercepted by overlay; retrying after Escape: {click_error}"
                    )
                    await self._dismiss_nested_overlay_backdrop()
                    await send_button.click()
                await asyncio.sleep(2)

            self.logger.info(f"✅ Notebook shared with {email}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to share notebook: {e}")
            if self.page:
                try:
                    screenshot_path = "debug/share_error.png"
                    await self.page.screenshot(path=screenshot_path, timeout=5000)
                    self.logger.info(f"📸 Screenshot saved to {screenshot_path}")
                except:
                    pass
            return False

    async def get_page_content(self) -> Optional[str]:
        """
        Get the HTML content of the current page.

        Returns:
            Optional[str]: The HTML content of the page, or None if an error occurs.
        """
        try:
            if not self.page:
                self.logger.error("❌ No browser page available")
                return None

            content = await self.page.content()
            return content

        except Exception as e:
            self.logger.error(f"❌ Failed to get page content: {e}")
            return None

    async def close(self):
        """Close browser connections and cleanup resources."""
        try:
            if self.page and self._owns_page:
                await self.page.close()
            if self.context and self._owns_context:
                await self.context.close()
            if self.browser and not self._connected_over_cdp:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            
            self.logger.info("🔒 Browser connections closed")
        except Exception as e:
            self.logger.error(f"❌ Error closing browser: {e}")
        finally:
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None
            self._connected_over_cdp = False
            self._owns_context = False
            self._owns_page = False


# Example usage and testing
async def test_notebooklm_connection():
    """Test function to verify NotebookLM automation setup."""
    automator = NotebookLMAutomator()
    
    try:
        # Test browser connection
        if await automator.connect_to_browser():
            print("✅ Browser connection successful")
            
            # Test navigation
            if await automator.navigate_to_notebooklm():
                print("✅ NotebookLM navigation successful")
                
                # Test authentication check
                auth_status = await automator.check_authentication()
                print(f"🔐 Authentication status: {'✅ Authenticated' if auth_status else '❌ Not authenticated'}")
            else:
                print("❌ NotebookLM navigation failed")
        else:
            print("❌ Browser connection failed")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    finally:
        await automator.close()


if __name__ == "__main__":
    # Run test if executed directly
    asyncio.run(test_notebooklm_connection())
