"""
SUPER VISIBLE TEST - You'll definitely see this one!
Adds page alerts and longer pauses.
"""

import asyncio
import sys
from deepdiver.notebooklm_automator import NotebookLMAutomator

async def very_visible_test():
    """Test with visual indicators you can't miss."""

    print("\n" + "="*70)
    print("🎬 SUPER VISIBLE TEST")
    print("="*70)
    print("\n📺 Look at your Chrome browser NOW!")
    print("   We'll add a visible message on the page...")
    print("\n⏰ Starting in 5 seconds...\n")
    await asyncio.sleep(5)

    automator = NotebookLMAutomator()

    try:
        # Connect
        print("1️⃣  Connecting to browser...")
        if not await automator.connect_to_browser():
            return False
        print("✅ Connected!")

        # Add a big visible message to the page
        print("\n2️⃣  Adding visible indicator to browser...")
        await automator.page.evaluate("""
            const div = document.createElement('div');
            div.id = 'deepdiver-indicator';
            div.innerHTML = '🤖 DEEPDIVER TEST RUNNING 🤖<br>Watch this space!';
            div.style.cssText = `
                position: fixed;
                top: 20px;
                left: 50%;
                transform: translateX(-50%);
                background: #FF6B6B;
                color: white;
                padding: 20px 40px;
                border-radius: 10px;
                font-size: 24px;
                font-weight: bold;
                z-index: 999999;
                text-align: center;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                animation: pulse 1s infinite;
            `;
            const style = document.createElement('style');
            style.textContent = '@keyframes pulse { 0%, 100% { transform: translateX(-50%) scale(1); } 50% { transform: translateX(-50%) scale(1.05); } }';
            document.head.appendChild(style);
            document.body.appendChild(div);
        """)
        print("✅ Big red banner added to page - YOU SHOULD SEE IT!")
        await asyncio.sleep(3)

        # Navigate to NotebookLM
        print("\n3️⃣  Navigating to NotebookLM...")
        await automator.page.evaluate("""
            document.getElementById('deepdiver-indicator').innerHTML =
                '🤖 Step 3: Going to NotebookLM...';
        """)

        if not await automator.navigate_to_notebooklm():
            return False
        print("✅ At NotebookLM!")
        await asyncio.sleep(2)

        # Update indicator
        await automator.page.evaluate("""
            const div = document.createElement('div');
            div.id = 'deepdiver-indicator';
            div.innerHTML = '🤖 Step 4: Creating notebook...<br>WATCH THE BUTTON CLICK!';
            div.style.cssText = `
                position: fixed;
                top: 20px;
                left: 50%;
                transform: translateX(-50%);
                background: #4ECDC4;
                color: white;
                padding: 20px 40px;
                border-radius: 10px;
                font-size: 24px;
                font-weight: bold;
                z-index: 999999;
                text-align: center;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            `;
            document.body.appendChild(div);
        """)
        await asyncio.sleep(3)

        # Create notebook
        print("\n4️⃣  Creating notebook NOW - WATCH THE SCREEN!")
        notebook_data = await automator.create_notebook()

        if not notebook_data:
            print("❌ Failed")
            return False

        print(f"\n✅ SUCCESS! Notebook created: {notebook_data['id']}")
        print(f"   URL: {notebook_data['url']}")

        # Success message on page
        await asyncio.sleep(2)
        await automator.page.evaluate("""
            const div = document.getElementById('deepdiver-indicator');
            if (div) {
                div.innerHTML = '✅ NOTEBOOK CREATED!<br>Check the terminal 👇';
                div.style.background = '#95E1D3';
            }
        """)
        await asyncio.sleep(5)

        # Remove indicator
        await automator.page.evaluate("""
            const div = document.getElementById('deepdiver-indicator');
            if (div) div.remove();
        """)

        print("\n" + "="*70)
        print("🎉 TEST COMPLETE!")
        print("="*70)

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        print("\n🔒 Closing...")
        await automator.close()


if __name__ == "__main__":
    print("\n♠️🌿🎸🧵 SUPER VISIBLE TEST")
    print("Look at your Chrome browser window RIGHT NOW! 👀\n")

    result = asyncio.run(very_visible_test())

    if result:
        print("\n✅ Did you see it this time?")
        sys.exit(0)
    else:
        print("\n❌ Test failed")
        sys.exit(1)
