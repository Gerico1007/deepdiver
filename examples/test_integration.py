#!/usr/bin/env python3
"""
DeepDiver + Langfuse Integration Test Suite
Tests the integration between DeepDiver and Langfuse tracing

♠️🌿🎸🧵 G.Music Assembly Team - Integration Tests
"""

import asyncio
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Any
from unittest.mock import Mock, AsyncMock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from deepdiver.session_tracker import SessionTracker
from deepdiver.langfuse_tracer import LangfuseTracer
from deepdiver.assembly_prompts import AssemblyPromptManager


class MockMCPTools:
    """Mock MCP tools for testing without actual Langfuse connection."""

    def __init__(self):
        self.traces_created = []
        self.observations_created = []
        self.trace_updates = []

    async def coaia_fuse_trace_create(self, **kwargs):
        """Mock trace creation."""
        self.traces_created.append(kwargs)
        return {'success': True, 'trace_id': kwargs['trace_id']}

    async def coaia_fuse_add_observation(self, **kwargs):
        """Mock observation creation."""
        self.observations_created.append(kwargs)
        return {'success': True, 'observation_id': kwargs['observation_id']}

    async def coaia_fuse_trace_patch_output(self, **kwargs):
        """Mock trace output update."""
        self.trace_updates.append(kwargs)
        return {'success': True}

    async def coaia_fuse_trace_get(self, **kwargs):
        """Mock trace retrieval."""
        trace_id = kwargs['trace_id']
        # Find matching trace
        for trace in self.traces_created:
            if trace['trace_id'] == trace_id:
                return {
                    'trace_id': trace_id,
                    'name': trace['name'],
                    'input_data': trace['input_data'],
                    'metadata': trace['metadata']
                }
        return None

    async def coaia_fuse_prompts_get(self, **kwargs):
        """Mock prompt retrieval."""
        return {
            'name': kwargs['name'],
            'content': f"Mock prompt for {kwargs['name']}",
            'version': '1.0.0'
        }

    async def coaia_fuse_prompts_list(self):
        """Mock prompts list."""
        return [
            {'name': 'deepdiver-jerry', 'version': '1.0.0'},
            {'name': 'deepdiver-nyro', 'version': '1.0.0'},
            {'name': 'deepdiver-aureon', 'version': '1.0.0'},
            {'name': 'deepdiver-jamai', 'version': '1.0.0'},
            {'name': 'deepdiver-synth', 'version': '1.0.0'}
        ]


class TestLangfuseTracer(unittest.TestCase):
    """Test LangfuseTracer functionality."""

    def setUp(self):
        """Set up test environment."""
        self.config = {
            'LANGFUSE_SETTINGS': {
                'enabled': True,
                'verbosity': 'standard'
            }
        }
        self.tracer = LangfuseTracer(config=self.config)
        self.mcp_tools = MockMCPTools()

    def test_tracer_initialization(self):
        """Test tracer initializes correctly."""
        self.assertTrue(self.tracer.is_enabled())
        self.assertEqual(self.tracer.verbosity, 'standard')

    def test_set_verbosity(self):
        """Test verbosity level changes."""
        self.tracer.set_verbosity('minimal')
        self.assertEqual(self.tracer.verbosity, 'minimal')

        self.tracer.set_verbosity('detailed')
        self.assertEqual(self.tracer.verbosity, 'detailed')

    async def test_create_session_trace(self):
        """Test session trace creation."""
        session_data = {
            'session_id': 'test-session-123',
            'ai_assistant': 'claude',
            'agents': ['Jerry ⚡', 'Nyro ♠️'],
            'issue_number': 42,
            'created_at': '2025-11-16T10:00:00',
            'assembly_team': {'leader': 'Jerry ⚡'}
        }

        trace_id = await self.tracer.create_session_trace(
            session_data=session_data,
            mcp_tools=self.mcp_tools
        )

        self.assertEqual(trace_id, 'test-session-123')
        self.assertEqual(len(self.mcp_tools.traces_created), 1)

        trace = self.mcp_tools.traces_created[0]
        self.assertEqual(trace['trace_id'], 'test-session-123')
        self.assertIn('ai_assistant', trace['input_data'])
        self.assertEqual(trace['input_data']['ai_assistant'], 'claude')

    async def test_add_notebook_observation(self):
        """Test notebook observation creation."""
        notebook_data = {
            'id': 'nb-test-001',
            'url': 'https://notebooklm.google.com/notebook/nb-test-001',
            'title': 'Test Notebook',
            'sources': []
        }

        obs_id = await self.tracer.add_notebook_observation(
            trace_id='test-session-123',
            notebook_data=notebook_data,
            mcp_tools=self.mcp_tools
        )

        self.assertEqual(obs_id, 'nb-test-001')
        self.assertEqual(len(self.mcp_tools.observations_created), 1)

        obs = self.mcp_tools.observations_created[0]
        self.assertEqual(obs['observation_type'], 'SPAN')
        self.assertIn('notebook_id', obs['input_data'])

    async def test_add_source_observation(self):
        """Test source observation creation."""
        source_data = {
            'source_id': 'src-test-001',
            'filename': 'test.md',
            'path': './test.md',
            'type': 'md',
            'size': 1024
        }

        obs_id = await self.tracer.add_source_observation(
            trace_id='test-session-123',
            notebook_id='nb-test-001',
            source_data=source_data,
            mcp_tools=self.mcp_tools
        )

        self.assertEqual(obs_id, 'src-test-001')
        self.assertEqual(len(self.mcp_tools.observations_created), 1)

        obs = self.mcp_tools.observations_created[0]
        self.assertEqual(obs['observation_type'], 'EVENT')
        self.assertEqual(obs['parent_id'], 'nb-test-001')


class TestAssemblyPromptManager(unittest.TestCase):
    """Test AssemblyPromptManager functionality."""

    def setUp(self):
        """Set up test environment with temporary prompts directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            'LANGFUSE_SETTINGS': {'enabled': True},
            'ASSEMBLY_PROMPTS': {
                'langfuse_namespace': 'deepdiver',
                'personas': ['jerry', 'nyro', 'aureon', 'jamai', 'synth']
            }
        }
        self.prompt_mgr = AssemblyPromptManager(
            config=self.config,
            prompts_dir=self.temp_dir
        )
        self.mcp_tools = MockMCPTools()

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_list_personas(self):
        """Test persona listing."""
        personas = self.prompt_mgr.list_personas()
        self.assertEqual(len(personas), 5)

        persona_keys = [p['key'] for p in personas]
        self.assertIn('jerry', persona_keys)
        self.assertIn('nyro', persona_keys)

    def test_get_persona_info(self):
        """Test getting persona metadata."""
        jerry_info = self.prompt_mgr.get_persona_info('jerry')
        self.assertIsNotNone(jerry_info)
        self.assertEqual(jerry_info['glyph'], '⚡')
        self.assertEqual(jerry_info['role'], 'Creative Technical Leader')

    def test_save_and_get_prompt(self):
        """Test saving and retrieving prompts."""
        content = "This is a test prompt for Jerry."
        success = self.prompt_mgr.save_prompt('jerry', content, version="1.0.0")
        self.assertTrue(success)

        # Verify file was created
        prompt_file = Path(self.temp_dir) / "jerry.md"
        self.assertTrue(prompt_file.exists())

        # Retrieve prompt
        retrieved = self.prompt_mgr.get_prompt('jerry', use_cache=False)
        self.assertIsNotNone(retrieved)
        self.assertIn(content, retrieved)

    def test_create_default_prompts(self):
        """Test creating default prompts for all personas."""
        success = self.prompt_mgr.create_default_prompts()
        self.assertTrue(success)

        # Verify all prompt files were created
        for persona_key in ['jerry', 'nyro', 'aureon', 'jamai', 'synth']:
            persona_info = self.prompt_mgr.get_persona_info(persona_key)
            prompt_file = Path(self.temp_dir) / persona_info['prompt_file']
            self.assertTrue(prompt_file.exists())

    async def test_list_langfuse_prompts(self):
        """Test listing prompts from Langfuse."""
        prompts = await self.prompt_mgr.list_langfuse_prompts(self.mcp_tools)
        self.assertIsNotNone(prompts)
        self.assertGreater(len(prompts), 0)


class TestSessionTrackerIntegration(unittest.TestCase):
    """Test SessionTracker with Langfuse integration."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            'SESSION_TRACKING': {
                'session_dir': self.temp_dir,
                'auto_save': True
            },
            'LANGFUSE_SETTINGS': {
                'enabled': True,
                'verbosity': 'standard'
            }
        }
        self.mcp_tools = MockMCPTools()
        self.tracker = SessionTracker(config=self.config, mcp_tools=self.mcp_tools)

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_session_tracker_initialization(self):
        """Test SessionTracker initializes with Langfuse support."""
        self.assertIsNotNone(self.tracker.langfuse_tracer)
        self.assertTrue(self.tracker.langfuse_tracer.is_enabled())

    def test_start_session(self):
        """Test session creation."""
        result = self.tracker.start_session(
            ai_assistant='claude',
            issue_number=101
        )

        self.assertTrue(result['success'])
        self.assertIn('session_id', result)
        self.assertIsNotNone(self.tracker.current_session)

        # Verify session file was created
        session_file = Path(self.temp_dir) / 'current_session.json'
        self.assertTrue(session_file.exists())

    def test_add_notebook(self):
        """Test adding notebook to session."""
        # Start session first
        self.tracker.start_session(ai_assistant='claude')

        notebook_data = {
            'id': 'nb-test-001',
            'url': 'https://notebooklm.google.com/notebook/nb-test-001',
            'title': 'Test Notebook',
            'sources': []
        }

        success = self.tracker.add_notebook(notebook_data)
        self.assertTrue(success)

        # Verify notebook was added
        notebooks = self.tracker.list_notebooks()
        self.assertEqual(len(notebooks), 1)
        self.assertEqual(notebooks[0]['id'], 'nb-test-001')

    def test_add_source_to_notebook(self):
        """Test adding source to notebook."""
        # Start session and add notebook
        self.tracker.start_session(ai_assistant='claude')
        notebook_data = {
            'id': 'nb-test-001',
            'url': 'https://notebooklm.google.com/notebook/nb-test-001',
            'title': 'Test Notebook',
            'sources': []
        }
        self.tracker.add_notebook(notebook_data)

        # Add source
        source_data = {
            'filename': 'test.md',
            'path': './test.md',
            'type': 'md',
            'size': 1024
        }

        success = self.tracker.add_source_to_notebook('nb-test-001', source_data)
        self.assertTrue(success)

        # Verify source was added
        sources = self.tracker.list_notebook_sources('nb-test-001')
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]['filename'], 'test.md')


class TestEndToEndWorkflow(unittest.TestCase):
    """Test complete end-to-end workflows."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            'SESSION_TRACKING': {
                'session_dir': self.temp_dir,
                'auto_save': True
            },
            'LANGFUSE_SETTINGS': {
                'enabled': True,
                'verbosity': 'standard'
            }
        }
        self.mcp_tools = MockMCPTools()

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    async def test_complete_session_workflow(self):
        """Test complete session creation, notebook addition, and finalization."""
        tracker = SessionTracker(config=self.config, mcp_tools=self.mcp_tools)
        tracer = LangfuseTracer(config=self.config)

        # Start session
        result = tracker.start_session(ai_assistant='claude', issue_number=202)
        self.assertTrue(result['success'])
        session_id = result['session_id']

        # Create Langfuse trace
        trace_id = await tracer.create_session_trace(
            session_data=result['session_data'],
            mcp_tools=self.mcp_tools
        )
        self.assertEqual(trace_id, session_id)

        # Add notebook
        notebook_data = {
            'id': 'nb-workflow-001',
            'url': 'https://notebooklm.google.com/notebook/nb-workflow-001',
            'title': 'Workflow Test Notebook',
            'sources': []
        }
        tracker.add_notebook(notebook_data)

        # Add notebook observation
        nb_obs_id = await tracer.add_notebook_observation(
            trace_id=trace_id,
            notebook_data=notebook_data,
            mcp_tools=self.mcp_tools
        )
        self.assertEqual(nb_obs_id, 'nb-workflow-001')

        # Add sources
        source1 = {
            'filename': 'doc1.md',
            'path': './doc1.md',
            'type': 'md',
            'size': 1024
        }
        tracker.add_source_to_notebook('nb-workflow-001', source1)

        # Add source observation
        src_obs_id = await tracer.add_source_observation(
            trace_id=trace_id,
            notebook_id='nb-workflow-001',
            source_data=source1,
            mcp_tools=self.mcp_tools
        )
        self.assertIsNotNone(src_obs_id)

        # Verify trace structure
        self.assertEqual(len(self.mcp_tools.traces_created), 1)
        self.assertEqual(len(self.mcp_tools.observations_created), 2)  # 1 notebook + 1 source

        # End session
        tracker.end_session()

        # Finalize trace
        final_session = result['session_data']
        final_session['status'] = 'ended'
        await tracer.finalize_session_trace(
            trace_id=trace_id,
            session_data=final_session,
            mcp_tools=self.mcp_tools
        )

        self.assertEqual(len(self.mcp_tools.trace_updates), 1)


def run_async_test(coro):
    """Helper to run async tests."""
    return asyncio.run(coro)


if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestLangfuseTracer))
    suite.addTests(loader.loadTestsFromTestCase(TestAssemblyPromptManager))
    suite.addTests(loader.loadTestsFromTestCase(TestSessionTrackerIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestEndToEndWorkflow))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*60)
    print("♠️🌿🎸🧵 Test Summary")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
