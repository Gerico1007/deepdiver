"""
Visual test - Watch the automation happen on screen!
This test includes delays so you can see each step.
"""

import asyncio
import sys
from deepdiver.notebooklm_automator import NotebookLMAutomator
from deepdiver.session_tracker import SessionTracker

async def visual_test():
    """Visual test with delays to watch automation."""

    print("\n" + "="*70)
    print("🎬 VISUAL TEST - Watch the browser automation happen!")
    print("="*70)
    print("\n👀 Make sure you can see the Chrome browser window on your screen")
    print("   Chrome should be at: /tmp/chrome-mcp with port 9222\n")
    print("⏰ Starting in 3 seconds...")
    await asyncio.sleep(3)

    automator = NotebookLMAutomator()

    try:
        # Step 1: Connect
        print("\n" + "─"*70)
        print("1️⃣  Connecting to Chrome browser...")
        print("─"*70)
        if not await automator.connect_to_browser():
            print("❌ Connection failed")
            return False
        print("✅ Connected! You should see a new page/tab opening...")
        await asyncio.sleep(2)

        # Step 2: Navigate
        print("\n" + "─"*70)
        print("2️⃣  Navigating to NotebookLM...")
        print("─"*70)
        if not await automator.navigate_to_notebooklm():
            print("❌ Navigation failed")
            return False
        print("✅ Arrived at NotebookLM homepage!")
        print("👀 You should see the NotebookLM interface with 'Create new notebook' button")
        await asyncio.sleep(3)

        # Step 3: Create notebook
        print("\n" + "─"*70)
        print("3️⃣  Creating new notebook...")
        print("    👀 WATCH: The 'Create new notebook' button will be clicked")
        print("─"*70)
        await asyncio.sleep(2)

        notebook_data = await automator.create_notebook()

        if not notebook_data:
            print("❌ Notebook creation failed")
            return False

        print("✅ Notebook created successfully!")
        print(f"\n📋 Captured Information:")
        print(f"   • Notebook ID:  {notebook_data['id']}")
        print(f"   • URL:          {notebook_data['url']}")
        print(f"   • Created:      {notebook_data['created_at']}")

        print("\n👀 You should now see a fresh notebook ready for sources!")
        await asyncio.sleep(3)

        # Step 4: Session integration
        print("\n" + "─"*70)
        print("4️⃣  Integrating with SessionTracker...")
        print("─"*70)

        tracker = SessionTracker()
        session_result = tracker.start_session(ai_assistant='claude', issue_number=1)
        print(f"✅ Session started: {session_result['session_id'][:8]}...")

        tracker.add_notebook(notebook_data)
        print(f"✅ Notebook added to session")

        active = tracker.get_active_notebook()
        print(f"✅ Active notebook: {active['id']}")

        status = tracker.get_session_status()
        print(f"✅ Session has {status['notebooks_count']} notebook(s)")

        # Step 5: Show what we could do next
        print("\n" + "─"*70)
        print("5️⃣  What's possible now:")
        print("─"*70)
        print("   📄 We could upload documents to this notebook")
        print("   🔄 We could navigate back to it later")
        print("   🎙️  We could generate Audio Overview")
        print("   💾 Session is saved and survives restarts")

        tracker.end_session()

        print("\n" + "="*70)
        print("🎉 TEST COMPLETE - All automation working!")
        print("="*70)
        print(f"\n📝 The notebook you just saw created is ready at:")
        print(f"   {notebook_data['url']}\n")

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        print("\n🔒 Closing connection (browser stays open)...")
        await automator.close()


if __name__ == "__main__":
    print("\n♠️🌿🎸🧵 DeepDiver Visual Test")

    result = asyncio.run(visual_test())

    if result:
        print("\n✅ Visual test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Visual test failed")
        sys.exit(1)
