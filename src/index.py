import asyncio
import os
from pathlib import Path
import random
from playwright.async_api import async_playwright

from config import CONFIG
from Utils.log import log
from Utils import recMail


async def start():
    os.system('cls' if os.name == 'nt' else 'clear')
    log("Starting...", "green")

    log("Fetching Fingerprint...", "yellow")
    # TODO: integrate fingerprint service
    log("Fingerprint fetched and applied", "green")

    proxy = None
    if CONFIG['USE_PROXY']:
        log("Applying proxy settings...", "green")
        proxy = {
            'server': f"{CONFIG['PROXY_USERNAME']}:{CONFIG['PROXY_PASSWORD']}@{CONFIG['PROXY_IP']}:{CONFIG['PROXY_PORT']}"
        }
        log("Proxy settings applied", "green")

    log("Launching browser...", "green")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, proxy=proxy)
        page = await browser.new_page()
        page.set_default_timeout(3600000)

        viewport = await page.evaluate(
            "() => ({width: document.documentElement.clientWidth, height: document.documentElement.clientHeight})"
        )
        log(f"Viewport: [Width: {viewport['width']} Height: {viewport['height']}]", "green")

        await create_account(page)
        await browser.close()


def delay(time: int):
    return asyncio.sleep(time / 1000)


async def create_account(page):
    await page.goto("https://outlook.live.com/owa/?nlp=1&signup=1")

    username_input = page.get_by_role("textbox", name="Create a new email address")
    await username_input.wait_for()

    personal_info = await generate_personal_info()

    await username_input.fill(personal_info['username'])
    await username_input.press("Enter")

    password = await generate_password()
    password_input = page.get_by_role("textbox", name="Create password")
    await password_input.wait_for()
    await password_input.fill(password)
    await password_input.press("Enter")

    first_name_input = page.get_by_test_id("firstNameInput")
    last_name_input = page.get_by_test_id("lastNameInput")
    await first_name_input.wait_for()
    await first_name_input.fill(personal_info['randomFirstName'])
    await last_name_input.fill(personal_info['randomLastName'])
    await last_name_input.press("Enter")

    birth_day_input = page.get_by_test_id("BirthDay")
    birth_month_input = page.get_by_test_id("BirthMonth")
    birth_year_input = page.get_by_test_id("BirthYear")
    await birth_day_input.wait_for()
    await delay(1000)
    await birth_day_input.select_option(personal_info['birthDay'])
    await birth_month_input.select_option(personal_info['birthMonth'])
    await birth_year_input.fill(personal_info['birthYear'])
    await birth_year_input.press("Enter")

    email = await page.inner_text(SELECTORS['EMAIL_DISPLAY'])
    await page.wait_for_selector(SELECTORS['FUNCAPTCHA'], timeout=60000)
    log("Please solve the captcha", "yellow")
    await page.wait_for_selector(SELECTORS['FUNCAPTCHA'], state="hidden")
    log("Captcha Solved!", "green")

    try:
        await page.wait_for_selector(SELECTORS['DECLINE_BUTTON'], timeout=10000)
        await page.click(SELECTORS['DECLINE_BUTTON'])
    except Exception:
        log("DECLINE_BUTTON not found within 10 seconds, checking for POST_REDIRECT_FORM...", "yellow")
        if await page.query_selector(SELECTORS['POST_REDIRECT_FORM']):
            log("POST_REDIRECT_FORM found, checking for CLOSE_BUTTON...", "green")
            await page.wait_for_selector(SELECTORS['CLOSE_BUTTON'])
            log("CLOSE_BUTTON found, clicking...", "green")
            await page.click(SELECTORS['CLOSE_BUTTON'])
        else:
            log("Neither DECLINE_BUTTON nor POST_REDIRECT_FORM found.", "red")
    await page.wait_for_selector(SELECTORS['OUTLOOK_PAGE'])

    if CONFIG['ADD_RECOVERY_EMAIL']:
        log("Adding Recovery Email...", "yellow")
        await page.goto("https://account.live.com/proofs/Manage")
        await page.wait_for_selector(SELECTORS['RECOVERY_EMAIL_INPUT'])
        recovery_email = await recMail.get_email()
        await page.fill(SELECTORS['RECOVERY_EMAIL_INPUT'], recovery_email['email'])
        await page.keyboard.press("Enter")
        await page.wait_for_selector(SELECTORS['EMAIL_CODE_INPUT'])
        log("Waiting for Email Code... (first verify)", "yellow")
        firstCode = await recMail.get_message(recovery_email)
        log(f"Email Code Received! Code: {firstCode}", "green")
        await page.fill(SELECTORS['EMAIL_CODE_INPUT'], firstCode)
        await page.keyboard.press("Enter")
        await delay(5000)
        if await page.query_selector(SELECTORS['VERIFICATION_ERROR']):
            log("Verification Error, resending code...", "red")
            await resend_code(page, recovery_email)
        try:
            await page.wait_for_selector(SELECTORS['INTERRUPT_CONTAINER'], timeout=10000)
        except Exception:
            log("INTERRUPT_CONTAINER not found within 10 seconds, checking for AFTER_CODE...", "yellow")
            if await page.query_selector(SELECTORS['AFTER_CODE']):
                log("Second Verify Needed", "yellow")
                await page.click(SELECTORS['AFTER_CODE'])
                await page.wait_for_selector(SELECTORS['DOUBLE_VERIFY_EMAIL'])
                await page.fill(SELECTORS['DOUBLE_VERIFY_EMAIL'], recovery_email['email'])
                await page.keyboard.press("Enter")
                await page.wait_for_selector(SELECTORS['DOUBLE_VERIFY_CODE'])
                log("Waiting for Email Code... (second verify)", "yellow")
                secondCode = await recMail.get_message(recovery_email)
                log(f"Email Code Received! Code: {secondCode}", "green")
                await page.fill(SELECTORS['DOUBLE_VERIFY_CODE'], secondCode)
                await page.keyboard.press("Enter")
                await delay(5000)
                if await page.query_selector(SELECTORS['VERIFICATION_ERROR']):
                    log("Verification Error, resending code...", "red")
                    await resend_code(page, recovery_email)
                await page.wait_for_selector(SELECTORS['INTERRUPT_CONTAINER'])
            else:
                log("Neither INTERRUPT_CONTAINER nor AFTER_CODE found.", "red")

    await write_credentials(email, password)


async def resend_code(page, recovery_email):
    await page.click(SELECTORS['RESEND_CODE'])
    await page.wait_for_selector(SELECTORS['EMAIL_CODE_INPUT'])
    log("Waiting for Email Code...", "yellow")
    code = await recMail.get_message(recovery_email)
    log(f"Email Code Received! Code: {code}", "green")
    await page.fill(SELECTORS['EMAIL_CODE_INPUT'], code)
    await page.keyboard.press("Enter")


def write_credentials(email: str, password: str):
    account = f"{email}:{password}"
    log(account, "green")
    with open(CONFIG['ACCOUNTS_FILE'], 'a') as f:
        f.write("\n" + account)


async def generate_personal_info():
    names = Path(CONFIG['NAMES_FILE']).read_text().splitlines()
    randomFirstName = random.choice(names).strip()
    randomLastName = random.choice(names).strip()
    username = f"{randomFirstName}{randomLastName}{random.randint(0, 9999)}"
    birthDay = str(random.randint(1, 28))
    birthMonth = str(random.randint(1, 12))
    birthYear = str(random.randint(1990, 1999))
    return {
        'username': username,
        'randomFirstName': randomFirstName,
        'randomLastName': randomLastName,
        'birthDay': birthDay,
        'birthMonth': birthMonth,
        'birthYear': birthYear,
    }


async def generate_password():
    return f"SomawDev{random.randint(1000, 99999)}"


SELECTORS = {
    'EMAIL_DISPLAY': '#userDisplayName',
    'DECLINE_BUTTON': '#declineButton',
    'OUTLOOK_PAGE': '#mainApp',
    'RECOVERY_EMAIL_INPUT': '#EmailAddress',
    'EMAIL_CODE_INPUT': '#iOttText',
    'AFTER_CODE': '#idDiv_SAOTCS_Proofs_Section',
    'DOUBLE_VERIFY_EMAIL': '#idTxtBx_SAOTCS_ProofConfirmation',
    'DOUBLE_VERIFY_CODE': '#idTxtBx_SAOTCC_OTC',
    'INTERRUPT_CONTAINER': '#interruptContainer',
    'VERIFICATION_ERROR': '#iVerificationErr',
    'RESEND_CODE': '#iShowSendCode',
    'POST_REDIRECT_FORM': 'form[data-testid="post-redirect-form"]',
    'CLOSE_BUTTON': '#close-button',
    'FUNCAPTCHA': '#enforcementFrame',
}

if __name__ == '__main__':
    asyncio.run(start())
