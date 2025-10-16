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

    # Priority 3: Config file
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
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
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.logger.warning(f"Configuration file {config_path} not found, using defaults")
            return {}
        except yaml.YAMLError as e:
            self.logger.error(f"Error parsing configuration: {e}")
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

            # Now we should be inside a notebook, look for the upload button.
            # ♠️ Nyro: Real NotebookLM upload button selector from Jerry ⚡
            upload_selectors = [
                'button[xapscottyuploadertrigger]',                    # Primary upload trigger
                'button[aria-label="Upload sources from your computer"]', # Upload button aria label
                'mat-card.create-new-action-button',                   # Legacy selector
                'button:has-text("Upload sources")',                   # Upload dialog button
                'button:has-text("Add source")',                       # Alternative text
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
    
    async def generate_audio_overview(self, title: str = "Generated Podcast") -> bool:
        """
        Generate an Audio Overview (podcast) from uploaded documents.
        
        Args:
            title (str): Title for the generated podcast
            
        Returns:
            bool: True if generation successful, False otherwise
        """
        try:
            if not self.page:
                self.logger.error("❌ No browser page available")
                return False
            
            self.logger.info(f"🎙️ Generating Audio Overview: {title}")
            
            # Look for Audio Overview button
            audio_selectors = [
                'button:has-text("Audio Overview")',
                'button:has-text("Generate Audio")',
                'button:has-text("Create Podcast")',
                '[data-testid="audio-overview"]',
                '.audio-overview-button'
            ]
            
            audio_button = None
            for selector in audio_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=10000)
                    if element:
                        audio_button = element
                        break
                except:
                    continue
            
            if not audio_button:
                self.logger.error("❌ Could not find Audio Overview button")
                return False
            
            # Click to start generation
            await audio_button.click()
            self.logger.info("🔄 Audio Overview generation started...")
            
            # Wait for generation to complete
            # This timeout should be adjusted based on actual generation time
            generation_timeout = self.config.get('NOTEBOOKLM_SETTINGS', {}).get('generation_timeout', 300000)
            await self.page.wait_for_timeout(generation_timeout)
            
            self.logger.info("✅ Audio Overview generation completed")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to generate Audio Overview: {e}")
            return False
    
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
