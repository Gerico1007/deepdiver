"""
Test script to verify Audio Overview edit button detection
without triggering generation (saves daily quota).

This script:
1. Connects to Chrome via CDP
2. Navigates to the notebook
3. Looks for the edit button on Audio Overview card
4. Reports if found (without clicking)

Usage:
    python test_edit_button_detection.py <notebook-id>
"""

import asyncio
import sys
from playwright.async_api import async_playwright


async def test_edit_button_detection(notebook_id: str):
    """Test if we can find the Audio Overview edit button."""

    print(f"🧪 Testing edit button detection for notebook: {notebook_id}")
    print("   (This won't trigger any generation)")

    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp('http://localhost:9222')
    context = browser.contexts[0]
    page = context.pages[0]

    # Navigate to notebook
    url = f"https://notebooklm.google.com/notebook/{notebook_id}"
    print(f"\n📍 Navigating to: {url}")
    await page.goto(url, timeout=60000)
    await page.wait_for_timeout(5000)  # Give page time to fully load

    # Navigate to Sources tab (where Studio panel is)
    print("\n📑 Ensuring Sources tab is active...")
    try:
        sources_tab = await page.wait_for_selector('button[role="tab"]:has-text("Sources")', timeout=10000)
        if sources_tab:
            is_active = await sources_tab.get_attribute('aria-selected')
            if is_active != 'true':
                await sources_tab.click()
                await page.wait_for_timeout(1000)
    except:
        print("   ⚠️ Could not find Sources tab, continuing anyway...")

    # Look for edit button using our selectors
    print("\n🔍 Looking for Audio Overview edit button...")

    selectors = [
        '.create-artifact-button-container:has-text("Audio Overview") button.edit-button',
        '.create-artifact-button-container:has-text("Audio Overview") .edit-button-always-visible',
        '.create-artifact-button-container:has-text("Audio Overview") button[data-edit-button-type="1"]',
        'button.edit-button:has(mat-icon .edit-button-icon)',
        '.mat-label-medium:has-text("Audio Overview") button.edit-button',
    ]

    found = False
    found_selector = None

    for i, selector in enumerate(selectors, 1):
        try:
            print(f"   Trying selector {i}: {selector[:60]}...")
            elements = await page.query_selector_all(selector)

            for element in elements:
                try:
                    is_visible = await element.is_visible()
                    if is_visible:
                        found = True
                        found_selector = selector

                        # Get button details
                        aria_label = await element.get_attribute('aria-label')
                        classes = await element.get_attribute('class')

                        print(f"\n   ✅ FOUND edit button!")
                        print(f"      Selector: {selector}")
                        print(f"      Aria-label: {aria_label}")
                        print(f"      Classes: {classes[:100]}...")
                        print(f"      Visible: {is_visible}")
                        break
                except:
                    continue

            if found:
                break

        except Exception as e:
            print(f"   ❌ Selector {i} failed: {e}")
            continue

    if not found:
        print("\n❌ Could not find edit button with any selector")
        print("   Taking screenshot for debugging...")
        await page.screenshot(path='debug/edit_button_not_found.png')
        print("   Screenshot saved: debug/edit_button_not_found.png")

        # List all buttons for debugging
        print("\n🔍 All visible buttons on page:")
        all_buttons = await page.query_selector_all('button')
        for i, btn in enumerate(all_buttons[:30]):
            try:
                visible = await btn.is_visible()
                if visible:
                    text = await btn.inner_text()
                    aria = await btn.get_attribute('aria-label')
                    if text or aria:
                        print(f"   Button {i}: text='{text[:30]}' aria='{aria}'")
            except:
                pass
    else:
        print(f"\n✅ SUCCESS: Edit button is detectable!")
        print(f"   Working selector: {found_selector}")
        print("\n📸 Taking screenshot of Studio panel...")
        await page.screenshot(path='debug/edit_button_found.png')
        print("   Screenshot saved: debug/edit_button_found.png")

    return found, found_selector


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_edit_button_detection.py <notebook-id>")
        sys.exit(1)

    notebook_id = sys.argv[1]
    found, selector = asyncio.run(test_edit_button_detection(notebook_id))

    if found:
        print(f"\n🎉 Test PASSED - Edit button is detectable")
        print(f"   Best selector: {selector}")
        sys.exit(0)
    else:
        print(f"\n⚠️ Test FAILED - Could not find edit button")
        print("   Check debug/edit_button_not_found.png for UI state")
        sys.exit(1)
