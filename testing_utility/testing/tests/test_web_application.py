import pytest
from playwright.sync_api import sync_playwright

@pytest.mark.parametrize("browser_type", ["chromium", "firefox"])
def test_web_application(browser_type, url, username, password):
    with sync_playwright() as p:
        browser = getattr(p, browser_type).launch(headless=False)
        page = browser.new_page()
        page.goto(url)

        # Login Test
        assert run_login_test(page, username, password) == "Login Successful"
        # Additional tests can go here
        browser.close()

def run_login_test(page, username, password):
    # Fill in the username and password
    page.fill('input[name*="user"], input[id*="user"]', username)
    page.fill('input[name*="pass"], input[id*="pass"]', password)
    page.click('button[type="submit"], input[type="submit"]')
    page.wait_for_load_state("networkidle")

    # Check if login was successful
    return "Login Successful" if "dashboard" in page.url or "welcome" in page.content() else "Login Failed"
