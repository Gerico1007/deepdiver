"""
Debug script to inspect the Sources panel UI when sources already exist
"""

import asyncio
from deepdiver.notebooklm_automator import NotebookLMAutomator


async def debug_sources_ui():
    """Debug the Sources UI to find the correct selectors."""

    automator = NotebookLMAutomator()

    try:
        # Connect
        await automator.connect_to_browser()

        # The notebook from the test
        notebook_id = "153f7bde-44c6-4e01-9fac-e5cfcafacbc2"

        # Navigate to it
        await automator.navigate_to_notebook(notebook_id=notebook_id)
        await asyncio.sleep(2)

        # Try to find Sources tab
        sources_tab_selector = 'div[role="tab"]:has-text("Sources")'
        sources_tab = await automator.page.wait_for_selector(sources_tab_selector, timeout=5000)

        is_active = await sources_tab.get_attribute('aria-selected')
        print(f"Sources tab active: {is_active}")

        if is_active != 'true':
            print("Clicking Sources tab...")
            await sources_tab.click()
            await asyncio.sleep(1)

        # Take screenshot
        await automator.page.screenshot(path="debug/sources_panel_with_content.png")
        print("Screenshot saved: debug/sources_panel_with_content.png")

        # Get page HTML for inspection
        content = await automator.page.content()
        with open("debug/sources_panel.html", "w") as f:
            f.write(content)
        print("HTML saved: debug/sources_panel.html")

        # Try to find various add source elements
        print("\nSearching for add source elements:")

        selectors_to_try = [
            'button:has-text("Add source")',
            'button[aria-label*="Add"]',
            'button:has-text("+")',
            'mat-chip:has-text("Website")',
            '[data-testid="add-source"]',
            'button[xapscottyuploadertrigger]'
        ]

        for selector in selectors_to_try:
            try:
                elements = await automator.page.query_selector_all(selector)
                print(f"  {selector}: Found {len(elements)} elements")
                if elements:
                    for i, el in enumerate(elements[:3]):  # First 3
                        text = await el.text_content()
                        visible = await el.is_visible()
                        print(f"    [{i}] visible={visible}, text='{text}'")
            except Exception as e:
                print(f"  {selector}: Error - {e}")

    finally:
        print("\nBrowser left open for manual inspection")


if __name__ == "__main__":
    asyncio.run(debug_sources_ui())
