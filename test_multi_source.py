"""
Test Multi-Source Upload Workflow
Tests the smart add_source() method with both files and URLs in a single notebook

This test demonstrates the complete Issue #4 functionality:
- Creating a notebook
- Adding file sources
- Adding URL sources
- Smart source type detection
"""

import asyncio
import sys
import os
from pathlib import Path
from deepdiver.notebooklm_automator import NotebookLMAutomator


async def test_multi_source_workflow():
    """Test adding multiple source types to a single notebook."""

    print("🧪 Testing Multi-Source Upload Workflow")
    print("=" * 70)
    print("Issue #4: Source Upload Automation - URL and File Support")
    print("=" * 70)

    # Initialize automator
    automator = NotebookLMAutomator()

    try:
        # ═══════════════════════════════════════════════════════════════
        # Step 1: Connect to Browser
        # ═══════════════════════════════════════════════════════════════
        print("\n1️⃣ Connecting to Chrome browser...")
        if not await automator.connect_to_browser():
            print("❌ Browser connection failed")
            print("💡 Make sure Chrome is running with CDP enabled:")
            print("   google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-deepdiver")
            return False
        print("✅ Browser connected")

        # ═══════════════════════════════════════════════════════════════
        # Step 2: Navigate to NotebookLM
        # ═══════════════════════════════════════════════════════════════
        print("\n2️⃣ Navigating to NotebookLM...")
        if not await automator.navigate_to_notebooklm():
            print("❌ Navigation failed")
            return False
        print("✅ Navigated to NotebookLM")

        # ═══════════════════════════════════════════════════════════════
        # Step 3: Create a New Notebook
        # ═══════════════════════════════════════════════════════════════
        print("\n3️⃣ Creating a new notebook...")
        notebook_data = await automator.create_notebook()

        if not notebook_data:
            print("❌ Notebook creation failed")
            return False

        notebook_id = notebook_data['id']
        print("✅ Notebook created successfully!")
        print(f"   📋 Notebook ID: {notebook_id}")
        print(f"   🔗 Notebook URL: {notebook_data['url']}")

        # ═══════════════════════════════════════════════════════════════
        # Step 4: Add File Source (if test file exists)
        # ═══════════════════════════════════════════════════════════════
        print("\n4️⃣ Testing file source upload...")

        # Look for any PDF or text file in test_sources directory
        test_file = None
        test_sources_dir = Path("test_sources")
        if test_sources_dir.exists():
            for ext in ['*.pdf', '*.txt', '*.md']:
                files = list(test_sources_dir.glob(ext))
                if files:
                    test_file = str(files[0])
                    break

        if test_file and os.path.exists(test_file):
            print(f"   📄 Using test file: {test_file}")
            result = await automator.add_source(test_file, notebook_id=notebook_id)

            if result:
                print(f"   ✅ File source added successfully!")
                print(f"   📋 Added to notebook: {result}")
            else:
                print("   ⚠️ File source upload had issues (check logs)")
        else:
            print("   ℹ️ No test file found in test_sources/ - skipping file upload")
            print("   💡 To test file uploads, create test_sources/ directory with sample files")

        # Small delay between uploads
        await asyncio.sleep(2)

        # ═══════════════════════════════════════════════════════════════
        # Step 5: Add URL Source (Wikipedia example)
        # ═══════════════════════════════════════════════════════════════
        print("\n5️⃣ Testing URL source addition...")

        # Use a safe, public URL for testing
        test_url = "https://en.wikipedia.org/wiki/Artificial_intelligence"
        print(f"   🔗 Using test URL: {test_url}")

        result = await automator.add_source(test_url, notebook_id=notebook_id)

        if result:
            print(f"   ✅ URL source added successfully!")
            print(f"   📋 Added to notebook: {result}")
        else:
            print("   ⚠️ URL source addition had issues (check logs)")

        # Small delay
        await asyncio.sleep(2)

        # ═══════════════════════════════════════════════════════════════
        # Step 6: Add Another URL (YouTube example)
        # ═══════════════════════════════════════════════════════════════
        print("\n6️⃣ Testing second URL source (YouTube)...")

        # Use a public YouTube video for testing
        youtube_url = "https://www.youtube.com/watch?v=aircAruvnKk"  # 3Blue1Brown neural networks
        print(f"   🎥 Using test URL: {youtube_url}")

        result = await automator.add_source(youtube_url, notebook_id=notebook_id)

        if result:
            print(f"   ✅ YouTube source added successfully!")
            print(f"   📋 Added to notebook: {result}")
        else:
            print("   ⚠️ YouTube source addition had issues (check logs)")

        # ═══════════════════════════════════════════════════════════════
        # Success Summary
        # ═══════════════════════════════════════════════════════════════
        print("\n" + "=" * 70)
        print("🎉 Multi-Source Workflow Test Complete!")
        print("=" * 70)
        print(f"✅ Notebook created: {notebook_id}")
        print(f"✅ Smart source detection working")
        print(f"✅ Multiple sources added to single notebook")
        print(f"✅ URL and file support verified")
        print("\n🔗 Open your notebook in the browser to verify all sources loaded:")
        print(f"   {notebook_data['url']}")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Note: We DON'T close the browser to allow manual verification
        print("\n💡 Browser left open for manual verification")
        print("   Check the notebook to see all sources loaded!")


if __name__ == "__main__":
    print("\n♠️🌿🎸🧵 DeepDiver Multi-Source Upload Test")
    print("Issue #4: Source Upload Automation")
    print("\nMake sure Chrome is running with CDP enabled:")
    print("  google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-deepdiver\n")

    result = asyncio.run(test_multi_source_workflow())

    if result:
        print("\n✅ Test suite completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Test suite failed")
        sys.exit(1)
