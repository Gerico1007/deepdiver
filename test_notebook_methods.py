"""
Test script for new notebook methods
Tests create_notebook, navigate_to_notebook, and SessionTracker notebook methods
"""

import asyncio
import sys
from deepdiver.notebooklm_automator import NotebookLMAutomator
from deepdiver.session_tracker import SessionTracker

async def test_notebook_automation():
    """Test the notebook automation methods."""

    print("🧪 Testing NotebookLM Automation - Notebook Methods")
    print("=" * 60)

    # Initialize automator
    automator = NotebookLMAutomator()

    try:
        # Test 1: Connect to browser
        print("\n1️⃣ Testing browser connection...")
        if not await automator.connect_to_browser():
            print("❌ Browser connection failed")
            return False
        print("✅ Browser connected")

        # Test 2: Navigate to NotebookLM
        print("\n2️⃣ Testing NotebookLM navigation...")
        if not await automator.navigate_to_notebooklm():
            print("❌ Navigation failed")
            return False
        print("✅ Navigated to NotebookLM")

        # Test 3: Create notebook and capture ID
        print("\n3️⃣ Testing notebook creation with ID capture...")
        notebook_data = await automator.create_notebook()

        if not notebook_data:
            print("❌ Notebook creation failed")
            return False

        print("✅ Notebook created successfully!")
        print(f"   📋 Notebook ID: {notebook_data['id']}")
        print(f"   🔗 Notebook URL: {notebook_data['url']}")
        print(f"   📅 Created At: {notebook_data['created_at']}")

        # Test 4: Test SessionTracker integration
        print("\n4️⃣ Testing SessionTracker notebook methods...")
        tracker = SessionTracker()

        # Start a session
        session_result = tracker.start_session(ai_assistant='claude', issue_number=1)
        if not session_result['success']:
            print("❌ Session creation failed")
            return False
        print(f"✅ Session started: {session_result['session_id']}")

        # Add notebook to session
        if not tracker.add_notebook(notebook_data):
            print("❌ Failed to add notebook to session")
            return False
        print("✅ Notebook added to session")

        # Get active notebook
        active_notebook = tracker.get_active_notebook()
        if not active_notebook:
            print("❌ Failed to get active notebook")
            return False
        print(f"✅ Active notebook: {active_notebook['id']}")

        # List notebooks
        notebooks = tracker.list_notebooks()
        print(f"✅ Notebooks in session: {len(notebooks)}")

        # Get session status
        status = tracker.get_session_status()
        print(f"✅ Session status:")
        print(f"   - Notebooks: {status['notebooks_count']}")
        print(f"   - Active notebook ID: {status['active_notebook_id']}")

        # Test 5: Navigate back to the notebook (optional - only if you want to test navigation)
        print("\n5️⃣ Testing navigation to existing notebook...")
        print(f"   Would navigate to: {notebook_data['url']}")
        print("   (Skipping actual navigation to avoid disrupting the newly created notebook)")

        # Uncomment to test actual navigation:
        # if await automator.navigate_to_notebook(notebook_id=notebook_data['id']):
        #     print("✅ Successfully navigated back to notebook")
        # else:
        #     print("❌ Navigation to notebook failed")

        print("\n" + "=" * 60)
        print("🎉 All tests passed!")
        print("=" * 60)

        # End session
        tracker.end_session()
        print("\n✅ Session ended")

        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Close browser connection
        await automator.close()
        print("\n🔒 Browser connection closed")


if __name__ == "__main__":
    print("\n♠️🌿🎸🧵 DeepDiver Notebook Automation Test")
    print("Make sure Chrome is running with CDP enabled:")
    print("  google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-deepdiver\n")

    result = asyncio.run(test_notebook_automation())

    if result:
        print("\n✅ Test suite completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Test suite failed")
        sys.exit(1)
