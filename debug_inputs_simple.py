"""
Simple debug - just find all inputs after clicking Website
"""

import asyncio
from deepdiver.notebooklm_automator import NotebookLMAutomator


async def find_inputs():
    automator = NotebookLMAutomator()

    await automator.connect_to_browser()
    notebook_id = "a2423014-54a2-4473-8799-824a17af2091"
    await automator.navigate_to_notebook(notebook_id=notebook_id)
    await asyncio.sleep(1)

    # Navigate to Sources tab
    sources_tab = await automator.page.wait_for_selector('div[role="tab"]:has-text("Sources")')
    is_active = await sources_tab.get_attribute('aria-selected')
    if is_active != 'true':
        await sources_tab.click()
        await asyncio.sleep(1)

    # Click Add
    add_button = await automator.page.wait_for_selector('button:has-text("Add")')
    await add_button.click()
    await asyncio.sleep(1)

    # Click Website
    website_chip = await automator.page.wait_for_selector('mat-chip:has-text("Website")')
    await website_chip.click()
    await asyncio.sleep(2)

    print("Finding all inputs...")
    inputs = await automator.page.query_selector_all('input')
    print(f"Total inputs found: {len(inputs)}")

    for i, inp in enumerate(inputs):
        visible = await inp.is_visible()
        if visible:
            inp_type = await inp.get_attribute('type') or ''
            placeholder = await inp.get_attribute('placeholder') or ''
            name = await inp.get_attribute('name') or ''
            aria = await inp.get_attribute('aria-label') or ''
            print(f"  [{i}] VISIBLE - type={inp_type}, placeholder='{placeholder}', name='{name}', aria='{aria}'")


if __name__ == "__main__":
    asyncio.run(find_inputs())
