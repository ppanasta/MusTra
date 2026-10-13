"""End-to-end check of the built web app in headless Chromium.

    python mobile/tests/smoke.py http://127.0.0.1:8765/ [screenshot_dir]

Boots Pyodide, opens each tab, saves a song correction and checks that it
survives a reload (IndexedDB persistence).
"""

import os
import sys

from playwright.sync_api import expect, sync_playwright

URL = sys.argv[1]
SHOTS = sys.argv[2] if len(sys.argv) > 2 else None


def shot(page, name):
    if SHOTS:
        page.screenshot(path=os.path.join(SHOTS, f"{name}.png"), full_page=False)


def main():
    exe = os.environ.get("CHROMIUM_PATH")
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2,
                                  is_mobile=True, has_touch=True)
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(URL)
        expect(page.locator("#start")).to_be_enabled(timeout=120_000)
        shot(page, "1-welcome")

        page.click("#start")
        expect(page.locator(".result-title")).to_have_text("Matzore", timeout=30_000)
        page.select_option("#name", "ousak")
        expect(page.locator(".result-title")).to_have_text("Ousak")
        expect(page.locator(".tips")).to_contain_text("Arabic Bayati")
        expect(page.locator("#song .title")).not_to_be_empty()
        shot(page, "2-ousak")

        page.click(".chip:has-text('Arabic Bayati')")
        expect(page.locator(".result-title")).to_have_text("Maqam Bayati")
        expect(page.locator("table").first).to_contain_text("E½♭")
        shot(page, "3-bayati")

        page.click(".tabs button[data-mode='makam']")
        page.select_option("#name", "hicaz")
        expect(page.locator(".result-title")).to_have_text("Makam Hicaz")

        page.click(".tabs button[data-mode='identify']")
        page.fill("#notes", "D Ed F G")
        page.click("#controls button[type='submit']")
        expect(page.locator("#result")).to_contain_text("Bayati Shuri")
        shot(page, "4-identify")

        # report a song and suggest another, then reload: both must persist
        page.click(".tabs button[data-mode='dromos']")
        page.select_option("#name", "sabah")
        title = page.locator("#song .title").inner_text()
        page.click("#song button:has-text('Wrong?')")
        page.select_option("#report-scale", "houzam")
        page.fill("#report-title", "Smoke test song")
        page.click("#report-save")
        expect(page.locator("#song")).to_contain_text("really dromos Houzam")
        shot(page, "5-reported")

        page.reload()
        expect(page.locator("#start")).to_be_enabled(timeout=120_000)
        page.click("#start")
        page.select_option("#name", "sabah")
        page.click("#song summary")
        expect(page.locator("#song")).to_contain_text("Smoke test song")
        page.select_option("#name", "houzam")
        page.click("#song summary")
        expect(page.locator("#song .song-list")).to_contain_text(title)

        # suggest a theory correction, check it persists, then roll back
        page.select_option("#name", "ousak")
        page.click(".theory button")
        expect(page.locator("#correct-banner")).to_contain_text("future release")
        page.select_option("#correct-makam", "kurdi")
        page.fill("#correct-comment", "Smoke test: compare with Kürdi")
        page.click("#correct-save")
        expect(page.locator(".theory")).to_contain_text("Parent makam: Uşşak → Kürdi")
        expect(page.locator("table").first).to_contain_text("Kürdi")
        shot(page, "6-corrected")
        page.reload()
        expect(page.locator("#start")).to_be_enabled(timeout=120_000)
        page.click("#start")
        page.select_option("#name", "ousak")
        expect(page.locator(".theory")).to_contain_text("Parent makam: Uşşak → Kürdi")
        page.click(".theory button")
        expect(page.locator("#correct-history")).to_contain_text("Version 1")
        shot(page, "7-history")
        page.click("#correct-history button:has-text('Back to the original')")
        expect(page.locator(".theory")).not_to_contain_text("Kürdi")
        page.click(".theory button")
        expect(page.locator("#correct-history")).to_contain_text("Version 2")
        page.click("#correct-dialog button[value='cancel']")

        assert not errors, errors
        browser.close()
    print("smoke test passed")


if __name__ == "__main__":
    main()
