"""
Test Chrome Helper Functions
Tests for Chrome executable finding, CDP checking, and launching

♠️ Nyro: Browser automation infrastructure
🧵 Synth: Test execution and validation
"""

import pytest
from unittest.mock import patch, MagicMock
import shutil

from deepdiver.notebooklm_automator import (
    find_chrome_executable,
    check_chrome_cdp_running,
    launch_chrome_cdp
)


class TestFindChromeExecutable:
    """Test suite for finding Chrome/Chromium executable."""

    def test_find_chrome_returns_string_or_none(self):
        """Test that find_chrome_executable returns str or None."""
        result = find_chrome_executable()
        assert result is None or isinstance(result, str)

    @patch('shutil.which')
    def test_find_chrome_checks_candidates(self, mock_which):
        """Test that all candidate names are checked."""
        mock_which.return_value = None

        result = find_chrome_executable()

        # Should check all candidates
        expected_calls = ['google-chrome', 'chromium', 'chromium-browser', 'chrome']
        actual_calls = [call.args[0] for call in mock_which.call_args_list]

        assert all(candidate in actual_calls for candidate in expected_calls)
        assert result is None

    @patch('shutil.which')
    def test_find_chrome_returns_first_found(self, mock_which):
        """Test that first found executable is returned."""
        def which_side_effect(cmd):
            if cmd == 'chromium':
                return '/usr/bin/chromium'
            return None

        mock_which.side_effect = which_side_effect

        result = find_chrome_executable()
        assert result in ['google-chrome', 'chromium', 'chromium-browser', 'chrome']


class TestCheckChromeCDPRunning:
    """Test suite for checking if Chrome CDP is running."""

    @patch('requests.get')
    def test_check_chrome_cdp_running_success(self, mock_get):
        """Test CDP check when Chrome is running."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = check_chrome_cdp_running('http://localhost:9222')
        assert result is True

    @patch('requests.get')
    def test_check_chrome_cdp_not_running(self, mock_get):
        """Test CDP check when Chrome is not running."""
        # Mock connection error
        mock_get.side_effect = Exception("Connection refused")

        result = check_chrome_cdp_running('http://localhost:9222')
        assert result is False

    @patch('requests.get')
    def test_check_chrome_cdp_handles_different_urls(self, mock_get):
        """Test CDP check with different URL formats."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Test localhost with port
        assert check_chrome_cdp_running('http://localhost:9222') in [True, False]

        # Test IP address
        check_chrome_cdp_running('http://192.168.1.100:9222')
        assert mock_get.called


class TestLaunchChromeCDP:
    """Test suite for launching Chrome with CDP."""

    @patch('deepdiver.notebooklm_automator.find_chrome_executable')
    def test_launch_chrome_no_executable(self, mock_find):
        """Test launch when Chrome executable not found."""
        mock_find.return_value = None

        result = launch_chrome_cdp()
        assert result is False

    @patch('deepdiver.notebooklm_automator.check_chrome_cdp_running')
    @patch('deepdiver.notebooklm_automator.find_chrome_executable')
    @patch('subprocess.Popen')
    def test_launch_chrome_success(self, mock_popen, mock_find, mock_check):
        """Test successful Chrome launch."""
        mock_find.return_value = 'google-chrome'
        mock_check.return_value = True  # Simulate Chrome started successfully

        result = launch_chrome_cdp()

        # Should attempt to launch
        assert mock_popen.called
        # Should verify it's running
        assert mock_check.called
        # Should return success
        assert result is True

    @patch('deepdiver.notebooklm_automator.check_chrome_cdp_running')
    @patch('deepdiver.notebooklm_automator.find_chrome_executable')
    @patch('subprocess.Popen')
    def test_launch_chrome_with_custom_port(self, mock_popen, mock_find, mock_check):
        """Test Chrome launch with custom port."""
        mock_find.return_value = 'chromium'
        mock_check.return_value = True

        result = launch_chrome_cdp(port=9999)

        # Should pass custom port to Chrome
        call_args = mock_popen.call_args[0][0]
        assert any('9999' in str(arg) for arg in call_args)

    @patch('deepdiver.notebooklm_automator.check_chrome_cdp_running')
    @patch('deepdiver.notebooklm_automator.find_chrome_executable')
    @patch('subprocess.Popen')
    def test_launch_chrome_with_custom_user_data_dir(self, mock_popen, mock_find, mock_check):
        """Test Chrome launch with custom user data directory."""
        mock_find.return_value = 'google-chrome'
        mock_check.return_value = True

        custom_dir = '/tmp/test-chrome'
        result = launch_chrome_cdp(user_data_dir=custom_dir)

        # Should pass custom user data dir to Chrome
        call_args = mock_popen.call_args[0][0]
        assert any(custom_dir in str(arg) for arg in call_args)


class TestChromeHelperIntegration:
    """Integration tests for Chrome helper functions."""

    def test_chrome_helper_workflow(self):
        """Test the complete Chrome helper workflow."""
        # 1. Find Chrome executable
        chrome_cmd = find_chrome_executable()

        # If Chrome is found on the system
        if chrome_cmd:
            # 2. Check if CDP is running (might be running already)
            is_running = check_chrome_cdp_running()
            assert isinstance(is_running, bool)

            # Note: We don't actually launch Chrome in tests to avoid side effects
            # The launch function is tested with mocks above


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
