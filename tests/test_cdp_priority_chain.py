"""
Test CDP URL Priority Chain
Tests the 4-tier CDP URL resolution: override > env > config > default

♠️ Nyro: Infrastructure validation patterns
🧵 Synth: Test execution framework
"""

import os
import tempfile
import pytest
import yaml

from deepdiver.notebooklm_automator import get_cdp_url


class TestCDPPriorityChain:
    """Test suite for CDP URL resolution priority chain."""

    def setup_method(self):
        """Clean environment before each test."""
        # Remove environment variable if it exists
        if 'DEEPDIVER_CDP_URL' in os.environ:
            del os.environ['DEEPDIVER_CDP_URL']

    def teardown_method(self):
        """Clean environment after each test."""
        # Remove environment variable if it exists
        if 'DEEPDIVER_CDP_URL' in os.environ:
            del os.environ['DEEPDIVER_CDP_URL']

    def test_cdp_default(self):
        """Test Priority 4: Default fallback."""
        # When no override, env var, or config file
        result = get_cdp_url(config_path='/nonexistent/path.yaml')
        assert result == 'http://localhost:9222'

    def test_cdp_config_file(self):
        """Test Priority 3: Config file resolution."""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config = {
                'BROWSER_SETTINGS': {
                    'cdp_url': 'http://config-file:9222'
                }
            }
            yaml.dump(config, f)
            config_path = f.name

        try:
            result = get_cdp_url(config_path=config_path)
            assert result == 'http://config-file:9222'
        finally:
            os.unlink(config_path)

    def test_cdp_env_variable(self):
        """Test Priority 2: Environment variable (higher than config)."""
        # Create temporary config file with different URL
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config = {
                'BROWSER_SETTINGS': {
                    'cdp_url': 'http://config-file:9222'
                }
            }
            yaml.dump(config, f)
            config_path = f.name

        try:
            # Set environment variable
            os.environ['DEEPDIVER_CDP_URL'] = 'http://env-var:9222'

            # Env var should override config file
            result = get_cdp_url(config_path=config_path)
            assert result == 'http://env-var:9222'
        finally:
            os.unlink(config_path)
            del os.environ['DEEPDIVER_CDP_URL']

    def test_cdp_override(self):
        """Test Priority 1: Override parameter (highest priority)."""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config = {
                'BROWSER_SETTINGS': {
                    'cdp_url': 'http://config-file:9222'
                }
            }
            yaml.dump(config, f)
            config_path = f.name

        try:
            # Set environment variable
            os.environ['DEEPDIVER_CDP_URL'] = 'http://env-var:9222'

            # Override should win over both config and env var
            result = get_cdp_url(override='http://override:9222', config_path=config_path)
            assert result == 'http://override:9222'
        finally:
            os.unlink(config_path)
            del os.environ['DEEPDIVER_CDP_URL']

    def test_cdp_priority_chain_complete(self):
        """Test complete priority chain in order."""
        # 1. Test default (nothing set)
        assert get_cdp_url(config_path='/nonexistent.yaml') == 'http://localhost:9222'

        # 2. Add config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config = {'BROWSER_SETTINGS': {'cdp_url': 'http://config:9222'}}
            yaml.dump(config, f)
            config_path = f.name

        try:
            assert get_cdp_url(config_path=config_path) == 'http://config:9222'

            # 3. Add env var (should override config)
            os.environ['DEEPDIVER_CDP_URL'] = 'http://env:9222'
            assert get_cdp_url(config_path=config_path) == 'http://env:9222'

            # 4. Add override (should override all)
            assert get_cdp_url(override='http://override:9222', config_path=config_path) == 'http://override:9222'
        finally:
            os.unlink(config_path)
            if 'DEEPDIVER_CDP_URL' in os.environ:
                del os.environ['DEEPDIVER_CDP_URL']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
