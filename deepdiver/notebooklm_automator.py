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
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

import yaml
from playwright.async_api import async_playwright, Browser, BrowserContext, Page


class NotebookLMAutomator:
    """
    Main automation class for NotebookLM interactions.
    
    Handles browser automation, authentication, document upload,
    podcast generation, and file management through Playwright.
    """
    
    def __init__(self, config_path: str = "deepdiver/deepdiver.yaml"):
        """Initialize the NotebookLM automator with configuration."""
        self.config = self._load_config(config_path)
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.logger = self._setup_logging()
        
        # NotebookLM specific settings
        self.base_url = self.config.get('NOTEBOOKLM_SETTINGS', {}).get('base_url', 'https://notebooklm.google.com')
        
        # Browser settings
        self.cdp_url = self.config.get('BROWSER_SETTINGS', {}).get('cdp_url', 'http://localhost:9222')
        self.user_data_dir = self.config.get('BROWSER_SETTINGS', {}).get('user_data_dir', '/tmp/chrome-deepdiver')
        self.headless = self.config.get('BROWSER_SETTINGS', {}).get('headless', False)
        
        # General timeout from browser settings (in seconds), converted to ms
        self.timeout = self.config.get('BROWSER_SETTINGS', {}).get('timeout', 30) * 1000
        
        self.logger.info("♠️🌿🎸🧵 NotebookLMAutomator initialized")
    
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
            ready_selector = 'button:has-text("Create new")'
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
    
    async def upload_document(self, file_path: str) -> bool:
        """
        Upload a document to NotebookLM.
        
        Args:
            file_path (str): Path to the document to upload
            
        Returns:
            bool: True if upload successful, False otherwise
        """
        try:
            if not self.page:
                self.logger.error("❌ No browser page available")
                return False
            
            if not os.path.exists(file_path):
                self.logger.error(f"❌ File not found: {file_path}")
                return False
            
            self.logger.info(f"📄 Uploading document: {file_path}")

            # Check if we are on the main page by looking for "Recent notebooks"
            try:
                recent_notebooks_header = await self.page.is_visible('h2:has-text("Recent notebooks")')
            except:
                recent_notebooks_header = False

            if recent_notebooks_header:
                try:
                    self.logger.info("📓 On main page, creating a new notebook...")
                    await self.page.locator('button:has-text("Create new notebook")').first.click()
                    # Wait for the notebook to be created and ready for sources
                    await self.page.wait_for_selector('button:has-text("Add source")', timeout=15000)
                    self.logger.info("✅ New notebook created.")
                except Exception as e:
                    self.logger.error(f"❌ Failed to create a new notebook: {e}")
                    if self.page:
                        await self.page.screenshot(path="create_notebook_failed.png")
                        self.logger.info("📸 Screenshot saved to create_notebook_failed.png")
                    return False

            # Now we should be inside a notebook, look for the upload button.
            # This might be the same as the "Add source" button.
            upload_selectors = [
                'button:has-text("Add source")',
                'button:has-text("Upload")',
                'input[type="file"]',
            ]
            
            upload_element = None
            for selector in upload_selectors:
                try:
                    # Use a longer timeout for finding the upload element
                    element = await self.page.wait_for_selector(selector, timeout=20000)
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
            
            # Handle file input
            if upload_element.tag_name == 'input' and upload_element.get_attribute('type') == 'file':
                await upload_element.set_input_files(file_path)
            else:
                # Click upload button and handle file dialog
                await upload_element.click()
                await self.page.wait_for_timeout(1000)
                
                # Handle file dialog (this might need adjustment based on actual interface)
                file_input = await self.page.wait_for_selector('input[type="file"]', timeout=5000)
                if file_input:
                    await file_input.set_input_files(file_path)
            
            # Wait for upload to complete
            await self.page.wait_for_timeout(5000)
            
            self.logger.info("✅ Document upload completed")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to upload document: {e}")
            return False
    
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
