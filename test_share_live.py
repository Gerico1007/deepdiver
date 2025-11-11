"""
Live test for share command - Browser stays open!
Watch the automation happen without closing the browser.
"""

import asyncio
from deepdiver.notebooklm_automator import NotebookLMAutomator
from deepdiver.session_tracker import SessionTracker

async def test_share_live():
    """Test sharing with browser staying open."""

    print("\n" + "="*70)
    print("🎬 LIVE SHARE TEST - Browser will stay open!")
    print("="*70)

    automator = NotebookLMAutomator()
    tracker = SessionTracker()

    try:
        # Start session
        tracker.start_session(ai_assistant='claude')
        print("\n1️⃣  Session started")

        # Connect
        print("\n2️⃣  Connecting to Chrome...")
        if not await automator.connect_to_browser():
            print("❌ Connection failed")
            return False
        print("✅ Connected!")

        # Navigate to NotebookLM
        print("\n3️⃣  Navigating to NotebookLM...")
        if not await automator.navigate_to_notebooklm():
            print("❌ Navigation failed")
            return False
        print("✅ At NotebookLM!")
        await asyncio.sleep(2)

        # Create notebook
        print("\n4️⃣  Creating new notebook...")
        print("    👀 WATCH: The 'Create new notebook' button will be clicked")
        await asyncio.sleep(2)

        notebook = await automator.create_notebook()
        if not notebook:
            print("❌ Notebook creation failed")
            return False

        print(f"✅ Notebook created!")
        print(f"   ID: {notebook['id']}")
        print(f"   URL: {notebook['url']}")

        # Add to session
        tracker.add_notebook(notebook)
        await asyncio.sleep(3)

        # Share the notebook
        print("\n5️⃣  Sharing notebook with gmusic@jgwill.com...")
        print("    👀 WATCH: This will:")
        print("       • Click the 'Share' button")
        print("       • Type the email address")
        print("       • Click 'Send'")
        await asyncio.sleep(3)

        if await automator.share_notebook('gmusic@jgwill.com', 'editor'):
            print("\n✅ NOTEBOOK SHARED SUCCESSFULLY!")
            print(f"   📧 gmusic@jgwill.com will receive an invitation")
            print(f"   🔗 Notebook: {notebook['url']}")

            # Update session
            collaborators = [{'email': 'gmusic@jgwill.com', 'role': 'editor'}]
            tracker.update_notebook(notebook['id'], {'collaborators': collaborators})
        else:
            print("\n❌ Sharing failed")
            print("   Check the browser to see what happened")

        print("\n" + "="*70)
        print("🎉 TEST COMPLETE!")
        print("="*70)
        print("\n⚠️  Browser is still open - you can see the shared notebook!")
        print("    Close this script with Ctrl+C when done")

        # Keep the script alive so browser stays open
        print("\n⏸️  Keeping browser open... (Ctrl+C to exit)")
        await asyncio.sleep(300)  # Wait 5 minutes

        return True

    except KeyboardInterrupt:
        print("\n\n👋 Exiting... Browser will close now")
        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Only close when we're done or interrupted
        await automator.close()
        tracker.end_session()


if __name__ == "__main__":
    print("\n♠️🌿🎸🧵 DeepDiver Live Share Test")
    print("👀 Watch your Chrome browser for the automation!\n")

    try:
        asyncio.run(test_share_live())
    except KeyboardInterrupt:
        print("\n\n✅ Test ended")
