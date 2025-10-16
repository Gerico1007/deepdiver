"""
Debug what happens after clicking Website chip
"""

import asyncio
from deepdiver.notebooklm_automator import NotebookLMAutomator


async def debug_website_chip():
    """Debug the Website chip click flow."""

    automator = NotebookLMAutomator()

    try:
        await automator.connect_to_browser()

        notebook_id = "a2423014-54a2-4473-8799-824a17af2091"
        await automator.navigate_to_notebook(notebook_id=notebook_id)
        await asyncio.sleep(1)

        # Navigate to Sources tab
        sources_tab = await automator.page.wait_for_selector('div[role="tab"]:has-text("Sources")', timeout=5000)
        is_active = await sources_tab.get_attribute('aria-selected')
        if is_active != 'true':
            print("Clicking Sources tab...")
            await sources_tab.click()
            await asyncio.sleep(1)

        # Click Add button
        print("Clicking Add button...")
        add_button = await automator.page.wait_for_selector('button:has-text("Add")', timeout=5000)
        await add_button.click()
        await asyncio.sleep(1)

        # Click Website chip
        print("Clicking Website chip...")
        website_chip = await automator.page.wait_for_selector('mat-chip:has-text("Website")', timeout=5000)
        await website_chip.click()
        await asyncio.sleep(2)

        # Take screenshot
        await automator.page.screenshot(path="debug/after_website_click.png")
        print("Screenshot saved: debug/after_website_click.png")

        # Try to find input fields
        print("\nSearching for input elements:")
        selectors = [
            'input[type="url"]',
            'input[type="text"]',
            'input[placeholder*="URL"]',
            'input[placeholder*="url"]',
            'input[placeholder*="link"]',
            'input[aria-label*="URL"]',
            'textarea',
            'input'
        ]

        for selector in selectors:
            try:
                elements = await automator.page.query_selector_all(selector)
                print(f"  {selector}: Found {len(elements)} elements")
                for i, el in enumerate(elements[:3]):
                    visible = await el.is_visible()
                    placeholder = await el.get_attribute('placeholder') or ''
                    aria_label = await el.get_attribute('aria-label') or ''
                    input_type = await el.get_attribute('type') or ''
                    print(f"    [{i}] visible={visible}, type={input_type}, placeholder='{placeholder}', aria-label='{aria_label}'")
            except Exception as e:
                print(f"  {selector}: Error - {e}")

    finally:
        print("\nBrowser left open")


if __name__ == "__main__":
    asyncio.run(debug_website_chip())
