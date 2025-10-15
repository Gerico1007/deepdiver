"""
Test NotebookLM Connection
Part of DeepDiver - NotebookLM Podcast Automation System

This module tests the NotebookLM automation connection and basic functionality.

Assembly Team: Jerry ⚡, Nyro ♠️, Aureon 🌿, JamAI 🎸, Synth 🧵
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

# Add the parent directory to the path so we can import deepdiver
sys.path.insert(0, str(Path(__file__).parent.parent))

from deepdiver.notebooklm_automator import NotebookLMAutomator


class TestNotebookLMConnection:
    """Test class for NotebookLM automation functionality."""
    
    def __init__(self):
        """Initialize the test class."""
        self.automator = None
        self.test_results = {}
    
    async def setup(self):
        """Set up test environment."""
        print("🔧 Setting up test environment...")
        self.automator = NotebookLMAutomator()
        print("✅ Test environment ready")
    
    async def test_browser_connection(self) -> bool:
        """Test browser connection via Chrome DevTools Protocol."""
        print("\n🔗 Testing browser connection...")
        
        try:
            result = await self.automator.connect_to_browser()
            self.test_results['browser_connection'] = result
            
            if result:
                print("✅ Browser connection successful")
                return True
            else:
                print("❌ Browser connection failed")
                return False
                
        except Exception as e:
            print(f"❌ Browser connection test failed: {e}")
            self.test_results['browser_connection'] = False
            return False
    
    async def test_notebooklm_navigation(self) -> bool:
        """Test navigation to NotebookLM."""
        print("\n🌐 Testing NotebookLM navigation...")
        
        try:
            result = await self.automator.navigate_to_notebooklm()
            self.test_results['navigation'] = result
            
            if result:
                print("✅ NotebookLM navigation successful")
                return True
            else:
                print("❌ NotebookLM navigation failed")
                return False
                
        except Exception as e:
            print(f"❌ Navigation test failed: {e}")
            self.test_results['navigation'] = False
            return False
    
    async def test_authentication_check(self) -> bool:
        """Test authentication status check."""
        print("\n🔐 Testing authentication check...")
        
        try:
            result = await self.automator.check_authentication()
            self.test_results['authentication'] = result
            
            if result:
                print("✅ Authentication check successful - user appears authenticated")
                return True
            else:
                print("⚠️ Authentication check completed - user may need to sign in")
                return True  # This is not a failure, just a status check
                
        except Exception as e:
            print(f"❌ Authentication check test failed: {e}")
            self.test_results['authentication'] = False
            return False
    
    async def test_page_elements(self) -> bool:
        """Test if we can find key page elements."""
        print("\n🔍 Testing page elements detection...")
        
        try:
            if not self.automator.page:
                print("❌ No page available for element testing")
                return False
            
            # Test for common NotebookLM elements
            test_selectors = [
                'body',  # Basic page structure
                'main',  # Main content area
                'header',  # Header section
                'nav',  # Navigation
            ]
            
            found_elements = 0
            for selector in test_selectors:
                try:
                    element = await self.automator.page.wait_for_selector(selector, timeout=5000)
                    if element:
                        found_elements += 1
                        print(f"✅ Found element: {selector}")
                    else:
                        print(f"⚠️ Element not found: {selector}")
                except:
                    print(f"⚠️ Element not found: {selector}")
            
            # Consider test successful if we found at least basic elements
            success = found_elements >= 2
            self.test_results['page_elements'] = success
            
            if success:
                print(f"✅ Page elements test successful ({found_elements}/{len(test_selectors)} elements found)")
                return True
            else:
                print(f"❌ Page elements test failed ({found_elements}/{len(test_selectors)} elements found)")
                return False
                
        except Exception as e:
            print(f"❌ Page elements test failed: {e}")
            self.test_results['page_elements'] = False
            return False
    
    async def test_configuration_loading(self) -> bool:
        """Test configuration loading."""
        print("\n⚙️ Testing configuration loading...")
        
        try:
            config = self.automator.config
            required_keys = ['NOTEBOOKLM_SETTINGS', 'BROWSER_SETTINGS']
            
            config_ok = True
            for key in required_keys:
                if key not in config:
                    print(f"⚠️ Missing configuration key: {key}")
                    config_ok = False
                else:
                    print(f"✅ Configuration key found: {key}")
            
            self.test_results['configuration'] = config_ok
            
            if config_ok:
                print("✅ Configuration loading successful")
                return True
            else:
                print("❌ Configuration loading failed")
                return False
                
        except Exception as e:
            print(f"❌ Configuration test failed: {e}")
            self.test_results['configuration'] = False
            return False
    
    async def run_all_tests(self):
        """Run all tests and report results."""
        print("🧪 Starting NotebookLM Connection Tests")
        print("=" * 50)
        
        await self.setup()
        
        # Run tests
        tests = [
            self.test_configuration_loading,
            self.test_browser_connection,
            self.test_notebooklm_navigation,
            self.test_authentication_check,
            self.test_page_elements,
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if await test():
                    passed += 1
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {e}")
        
        # Report results
        print("\n" + "=" * 50)
        print("📊 Test Results Summary")
        print("=" * 50)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! NotebookLM automation is ready.")
        elif passed >= total * 0.8:
            print("⚠️ Most tests passed. Some issues may need attention.")
        else:
            print("❌ Multiple test failures. Please check configuration and setup.")
        
        return passed == total
    
    async def cleanup(self):
        """Clean up test resources."""
        print("\n🧹 Cleaning up test resources...")
        if self.automator:
            await self.automator.close()
        print("✅ Cleanup completed")


async def main():
    """Main test function."""
    tester = TestNotebookLMConnection()
    
    try:
        success = await tester.run_all_tests()
        return success
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
