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
import shutil
import subprocess
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

import yaml
from playwright.async_api import async_playwright, Browser, BrowserContext, Page


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


def launch_chrome_cdp(port: int = 9222, user_data_dir: str = None) -> bool:
    """
    Launch Chrome with CDP enabled

    Args:
        port: CDP port number (default: 9222)
        user_data_dir: Chrome user data directory

    Returns:
        bool: True if Chrome launched successfully, False otherwise
    """
    chrome_cmd = find_chrome_executable()
    if not chrome_cmd:
        return False

    if user_data_dir is None:
        user_data_dir = os.path.expanduser('~/.chrome-deepdiver')

    try:
        subprocess.Popen([
            chrome_cmd,
            f'--remote-debugging-port={port}',
            f'--user-data-dir={user_data_dir}'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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
    
    def __init__(self, config_path: str = "deepdiver/deepdiver.yaml", cdp_url_override: str = None):
        """
        Initialize the NotebookLM automator with configuration.

        Args:
            config_path: Path to configuration file
            cdp_url_override: Optional CDP URL override (highest priority)
        """
        # Set up logger FIRST so other methods can use it
        self.logger = self._setup_logging()

        self.config_path = config_path
        self.config = self._load_config(config_path)
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

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
            
            playwright = await async_playwright().start()
            
            # Connect to existing browser
            self.browser = await playwright.chromium.connect_over_cdp(self.cdp_url)
            
            # Get the first available context
            contexts = self.browser.contexts
            if contexts:
                self.context = contexts[0]
            else:
                self.context = await self.browser.new_context()
            
            # Get the first available page or create new one
            pages = self.context.pages
            if pages:
                self.page = pages[0]
            else:
                self.page = await self.context.new_page()
            
            self.logger.info("✅ Successfully connected to Chrome browser")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to connect to browser: {e}")
            return False
    
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
            
            # Wait for a selector that indicates the main interface is loaded
            ready_selector = 'button[aria-label="Create new notebook"]';
            await self.page.wait_for_selector(ready_selector, timeout=navigation_timeout)
            
            # Check if we're on the correct page
            current_url = self.page.url
            if 'notebooklm.google.com' in current_url:
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
            add_button_selectors = [
                'button.add-source-button',                          # Specific class
                'button[aria-label="Add source"]',                   # Exact aria-label
                'button[mattooltip="Add source"]',                   # Mat tooltip
                'button[mat-stroked-button]:has-text("Add")',        # Mat stroked button with Add text
                'button:has-text("Add")',                            # Fallback
            ]

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
                # Click upload button to activate file dialog
                await upload_element.click()
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
            add_button_selectors = [
                'button:has-text("Add")',
                'button[aria-label*="Add"]',
                'button:has-text("+ Add")'
            ]

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

            # Detect URL type and select appropriate chip
            # ♠️ Jerry: YouTube URLs need YouTube chip, others need Website chip
            is_youtube = 'youtube.com' in url.lower() or 'youtu.be' in url.lower()

            if is_youtube:
                chip_type = "YouTube"
                chip_selectors = [
                    'mat-chip:has-text("YouTube")',
                    'button:has-text("YouTube")',
                    'mat-chip:has(mat-icon:has-text("video_youtube"))',
                    '[aria-label*="YouTube"]'
                ]
            else:
                chip_type = "Website"
                chip_selectors = [
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

            self.logger.info("✅ URL source added successfully")
            self.logger.info(f"📋 Added to notebook: {current_notebook_id}")
            return current_notebook_id

        except Exception as e:
            self.logger.error(f"❌ Failed to add URL source: {e}")
            return None

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
            # Capitalize language for proper matching (e.g., "french" -> "French")
            language_capitalized = language.capitalize()
            self.logger.info(f"⚙️ Selecting language: {language_capitalized}")
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

                # Try Playwright's get_by_role first (most reliable for Material dropdowns)
                try:
                    option = self.page.get_by_role('option', name=language_capitalized, exact=True)
                    if await option.count() > 0:
                        await option.click()
                        await self.page.wait_for_timeout(500)
                        self.logger.info(f"✅ Language selected: {language_capitalized} (via role)")
                        language_selected = True
                except Exception as e:
                    self.logger.debug(f"get_by_role failed: {e}")

                # Fallback: Try case-insensitive role match
                if not language_selected:
                    try:
                        option = self.page.get_by_role('option', name=language_capitalized)
                        if await option.count() > 0:
                            await option.first.click()
                            await self.page.wait_for_timeout(500)
                            self.logger.info(f"✅ Language selected: {language_capitalized} (via role fuzzy)")
                            language_selected = True
                    except Exception as e:
                        self.logger.debug(f"get_by_role fuzzy failed: {e}")

                # Fallback: Try locator with text
                if not language_selected:
                    try:
                        option = self.page.locator(f'mat-option:has-text("{language_capitalized}")')
                        if await option.count() > 0:
                            await option.first.click()
                            await self.page.wait_for_timeout(500)
                            self.logger.info(f"✅ Language selected: {language_capitalized} (via locator)")
                            language_selected = True
                    except Exception as e:
                        self.logger.debug(f"locator failed: {e}")

                # Fallback: Try CSS selectors
                if not language_selected:
                    language_option_selectors = [
                        f'.cdk-overlay-pane mat-option:has-text("{language_capitalized}")',
                        f'mat-option:has-text("{language_capitalized}")',
                        f'.mat-mdc-option:has-text("{language_capitalized}")',
                        f'[role="option"]:has-text("{language_capitalized}")'
                    ]

                    for selector in language_option_selectors:
                        try:
                            option = await self.page.wait_for_selector(selector, timeout=3000, state='visible')
                            if option:
                                await option.click()
                                await self.page.wait_for_timeout(500)
                                self.logger.info(f"✅ Language selected: {language_capitalized} (via selector)")
                                language_selected = True
                                break
                        except:
                            continue

                if not language_selected:
                    # Close the overlay by pressing Escape to prevent it blocking other clicks
                    self.logger.warning(f"⚠️ Could not select language '{language_capitalized}', using default")
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
                polling_interval
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

    async def _monitor_audio_generation(
        self,
        start_time: float,
        timeout: int,
        polling_interval: int
    ) -> Optional[Dict[str, Any]]:
        """
        Monitor Audio Overview generation status.

        🔥 West (Action): Patient watching for creation to complete.

        Args:
            start_time (float): When generation started (time.time())
            timeout (int): Maximum wait time in seconds
            polling_interval (int): How often to check status (seconds)

        Returns:
            Optional[Dict[str, Any]]: Artifact metadata if completed, None if timeout/error
        """
        try:
            last_log_time = start_time

            while time.time() - start_time < timeout:
                elapsed = int(time.time() - start_time)

                # Log progress every 30 seconds
                if time.time() - last_log_time >= 30:
                    self.logger.info(f"⏳ Still generating... ({elapsed}s elapsed)")
                    last_log_time = time.time()

                # Look for completed artifact in Studio panel
                # Completion indicated by "Load" button appearing
                artifact_selectors = [
                    '.studio-artifact:has(button:has-text("Load"))',
                    '[data-artifact-type="audio_overview"]:has(button:has-text("Load"))',
                    '.artifact-card:has(button:has-text("Load"))'
                ]

                for selector in artifact_selectors:
                    try:
                        artifact_element = await self.page.query_selector(selector)
                        if artifact_element:
                            is_visible = await artifact_element.is_visible()
                            if is_visible:
                                # Found completed artifact!
                                generation_time = int(time.time() - start_time)
                                self.logger.info(f"✅ Generation completed in {generation_time}s")

                                # Extract metadata
                                artifact_data = await self._extract_artifact_metadata(artifact_element)
                                artifact_data['generation_time'] = generation_time
                                artifact_data['status'] = 'completed'
                                artifact_data['type'] = 'audio_overview'

                                return artifact_data
                    except:
                        continue

                # Wait before polling again
                await self.page.wait_for_timeout(polling_interval * 1000)

            # Timeout reached
            elapsed = int(time.time() - start_time)
            self.logger.error(f"❌ Generation timeout after {elapsed}s")
            return None

        except Exception as e:
            self.logger.error(f"❌ Error monitoring generation: {e}")
            return None

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

            return {
                'artifact_id': artifact_id,
                'created_at': created_at
            }

        except Exception as e:
            self.logger.warning(f"⚠️ Could not extract full metadata: {e}")
            # Return minimal metadata
            import hashlib
            timestamp = datetime.now().isoformat()
            return {
                'artifact_id': hashlib.md5(timestamp.encode()).hexdigest()[:12],
                'created_at': timestamp
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
    
    async def download_audio(self, output_path: str) -> bool:
        """
        Download the generated audio file.
        
        Args:
            output_path (str): Path where to save the audio file
            
        Returns:
            bool: True if download successful, False otherwise
        """
        try:
            if not self.page:
                self.logger.error("❌ No browser page available")
                return False
            
            self.logger.info(f"⬇️ Downloading audio to: {output_path}")
            
            # Look for download button
            download_selectors = [
                'button:has-text("Download")',
                'button:has-text("Save")',
                'a[download]',
                '[data-testid="download-button"]',
                '.download-button'
            ]
            
            download_button = None
            for selector in download_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=10000)
                    if element:
                        download_button = element
                        break
                except:
                    continue
            
            if not download_button:
                self.logger.error("❌ Could not find download button")
                return False
            
            # Set up download handling
            async with self.page.expect_download() as download_info:
                await download_button.click()
            
            download = await download_info.value
            await download.save_as(output_path)
            
            self.logger.info("✅ Audio download completed")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to download audio: {e}")
            return False
    
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

            # Navigate to the notebook URL
            await self.page.goto(target_url, timeout=30000)

            # Wait for load state (use 'load' instead of 'networkidle' - networkidle can hang with background polling)
            try:
                await self.page.wait_for_load_state('load', timeout=10000)
            except:
                # If load state times out, continue anyway - URL check below will verify
                self.logger.warning("⚠️ Load state timeout, but continuing with URL verification...")

            # Verify notebook loaded successfully
            # First check if URL contains /notebook/ - most reliable indicator
            current_url = self.page.url
            if '/notebook/' in current_url:
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
                'input[type="email"]',
                'input[aria-label*="email"]',
                'input[aria-label*="Add people"]',
                'input[placeholder*="email"]',
                'input.share-email-input'
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
                'button:has-text("Send")',
                'button:has-text("Share")',
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
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            
            self.logger.info("🔒 Browser connections closed")
        except Exception as e:
            self.logger.error(f"❌ Error closing browser: {e}")


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
