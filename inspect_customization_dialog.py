"""
Inspect Audio Overview customization dialog
Clicks the edit/pencil icon and maps all available options.

This script:
1. Clicks the edit button on Audio Overview card
2. Waits for customization dialog to appear
3. Maps all options: formats, languages, lengths
4. Takes screenshots and saves HTML
5. DOES NOT click Generate (saves quota)

Usage:
    python inspect_customization_dialog.py <notebook-id>
"""

import asyncio
import sys
from playwright.async_api import async_playwright


async def inspect_dialog(notebook_id: str):
    """Click edit button and inspect the customization dialog."""

    print(f"🔍 Inspecting Audio Overview customization dialog")
    print(f"   Notebook: {notebook_id}\n")

    playwright = await async_playwright().start()
    browser = await playwright.chromium.connect_over_cdp('http://localhost:9222')
    context = browser.contexts[0]
    page = context.pages[0]

    # Navigate to notebook
    url = f"https://notebooklm.google.com/notebook/{notebook_id}"
    print(f"📍 Navigating to: {url}")
    await page.goto(url, timeout=60000)
    await page.wait_for_timeout(5000)

    # Click the edit button
    print("\n🖱️  Clicking Audio Overview edit button...")
    edit_button = await page.wait_for_selector(
        '.create-artifact-button-container:has-text("Audio Overview") button.edit-button',
        timeout=10000
    )
    await edit_button.click()
    await page.wait_for_timeout(2000)

    # Wait for dialog to appear
    print("⏳ Waiting for customization dialog...")
    dialog = await page.wait_for_selector('.mat-mdc-dialog-container', timeout=10000, state='visible')
    if not dialog:
        print("❌ Dialog did not appear!")
        return

    print("✅ Dialog appeared!\n")
    await page.wait_for_timeout(1000)

    # Take screenshot
    print("📸 Taking screenshot...")
    await page.screenshot(path='debug/customization_dialog.png', full_page=True)
    print("   Saved: debug/customization_dialog.png\n")

    # Save dialog HTML
    dialog_html = await dialog.inner_html()
    with open('debug/customization_dialog.html', 'w') as f:
        f.write(dialog_html)
    print("💾 Saved HTML: debug/customization_dialog.html\n")

    # === MAP FORMAT OPTIONS ===
    print("=" * 60)
    print("FORMAT OPTIONS (Radio Button Tiles)")
    print("=" * 60)

    format_tiles = await dialog.query_selector_all('mat-radio-button')
    print(f"Found {len(format_tiles)} format tiles:\n")

    for i, tile in enumerate(format_tiles, 1):
        try:
            # Get tile label
            label_elem = await tile.query_selector('.tile-label')
            if label_elem:
                label_text = await label_elem.inner_text()
                print(f"  {i}. {label_text}")

                # Get description if available
                desc_elem = await tile.query_selector('.tile-description')
                if desc_elem:
                    desc_text = await desc_elem.inner_text()
                    print(f"     Description: {desc_text}")

                # Get aria-checked status
                checked = await tile.get_attribute('aria-checked')
                if checked == 'true':
                    print(f"     ✓ SELECTED (default)")
                print()
        except Exception as e:
            print(f"  Error reading tile {i}: {e}")

    # === MAP LANGUAGE OPTIONS ===
    print("=" * 60)
    print("LANGUAGE OPTIONS (Dropdown)")
    print("=" * 60)

    language_select = await dialog.query_selector('mat-select[aria-label*="language"], mat-select[aria-label*="Language"]')
    if language_select:
        # Get current selection
        current_lang = await language_select.inner_text()
        print(f"Current selection: {current_lang}\n")

        # Click to open dropdown
        print("Opening language dropdown...")
        await language_select.click()
        await page.wait_for_timeout(1000)

        # Get all options
        options = await page.query_selector_all('mat-option')
        print(f"Found {len(options)} language options:\n")

        for i, option in enumerate(options, 1):
            try:
                text = await option.inner_text()
                selected = await option.get_attribute('aria-selected')
                marker = " ✓ SELECTED" if selected == 'true' else ""
                print(f"  {i}. {text}{marker}")
            except:
                pass

        # Close dropdown (press Escape)
        await page.keyboard.press('Escape')
        await page.wait_for_timeout(500)
        print()
    else:
        print("⚠️  Language selector not found\n")

    # === MAP LENGTH OPTIONS ===
    print("=" * 60)
    print("LENGTH OPTIONS (Toggle Buttons)")
    print("=" * 60)

    length_buttons = await dialog.query_selector_all('.mat-button-toggle-group button')
    print(f"Found {len(length_buttons)} length options:\n")

    for i, button in enumerate(length_buttons, 1):
        try:
            text = await button.inner_text()
            aria_pressed = await button.get_attribute('aria-pressed')
            selected = " ✓ SELECTED (default)" if aria_pressed == 'true' else ""
            print(f"  {i}. {text}{selected}")
        except Exception as e:
            print(f"  Error reading button {i}: {e}")
    print()

    # === MAP FOCUS PROMPT ===
    print("=" * 60)
    print("FOCUS PROMPT (Textarea)")
    print("=" * 60)

    focus_textarea = await dialog.query_selector('textarea')
    if focus_textarea:
        placeholder = await focus_textarea.get_attribute('placeholder')
        max_length = await focus_textarea.get_attribute('maxlength')
        aria_label = await focus_textarea.get_attribute('aria-label')

        print(f"Placeholder: {placeholder}")
        print(f"Max length: {max_length} characters")
        print(f"Aria-label: {aria_label}")
        print()
    else:
        print("⚠️  Focus textarea not found\n")

    # === MAP BUTTONS ===
    print("=" * 60)
    print("DIALOG BUTTONS")
    print("=" * 60)

    buttons = await dialog.query_selector_all('button')
    print(f"Found {len(buttons)} buttons:\n")

    for i, button in enumerate(buttons, 1):
        try:
            text = await button.inner_text()
            aria_label = await button.get_attribute('aria-label')
            classes = await button.get_attribute('class')

            if text and text.strip():
                print(f"  {i}. '{text}'")
                if aria_label:
                    print(f"     Aria-label: {aria_label}")
                if 'primary' in str(classes).lower():
                    print(f"     Type: PRIMARY (Generate)")
                elif 'cancel' in str(text).lower() or 'close' in str(text).lower():
                    print(f"     Type: CANCEL/CLOSE")
                print()
        except:
            pass

    print("=" * 60)
    print("✅ Inspection complete!")
    print("=" * 60)
    print("\nFiles saved:")
    print("  - debug/customization_dialog.png (screenshot)")
    print("  - debug/customization_dialog.html (HTML source)")
    print("\n⚠️  Dialog is still open - you can manually close it or press Escape")

    # Wait a moment before closing
    await page.wait_for_timeout(2000)

    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inspect_customization_dialog.py <notebook-id>")
        sys.exit(1)

    notebook_id = sys.argv[1]
    success = asyncio.run(inspect_dialog(notebook_id))

    if success:
        print("\n🎉 Successfully mapped all customization options!")
        sys.exit(0)
    else:
        print("\n❌ Failed to inspect dialog")
        sys.exit(1)
