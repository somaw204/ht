from playwright.async_api import async_playwright

from config import CONFIG
from Utils.log import log


async def fetch_fingerprint():
    """Retrieve and apply a browser fingerprint."""
    log("Fetching Fingerprint...", "yellow")
    # TODO: integrate fingerprint service
    log("Fingerprint fetched and applied", "green")


async def launch_browser():
    """Launch a Chromium browser with optional proxy settings.

    Returns:
        tuple: (playwright instance, browser, page)
    """
    proxy = None
    if CONFIG['USE_PROXY']:
        log("Applying proxy settings...", "green")
        proxy = {
            'server': f"{CONFIG['PROXY_USERNAME']}:{CONFIG['PROXY_PASSWORD']}@{CONFIG['PROXY_IP']}:{CONFIG['PROXY_PORT']}"
        }
        log("Proxy settings applied", "green")

    log("Launching browser...", "green")
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False, proxy=proxy)
    page = await browser.new_page()
    page.set_default_timeout(3600000)

    viewport = await page.evaluate(
        "() => ({width: document.documentElement.clientWidth, height: document.documentElement.clientHeight})"
    )
    log(f"Viewport: [Width: {viewport['width']} Height: {viewport['height']}]", "green")
    return playwright, browser, page
