import pytest
from playwright.sync_api import sync_playwright

@pytest.mark.parametrize("browser_type", ["chromium", "firefox"])
def test_web_application(browser_type):
    # Replace these values with the values from form submission or from the frontend
    url = "https://example.com"
    username = "test_user"
    password = "test_password"

    with sync_playwright() as p:
        browser = getattr(p, browser_type).launch(headless=False)
        page = browser.new_page()
        page.goto(url)

        # Dynamic User Authentication
        login_result = run_login_test(page, username, password)
        assert login_result == "Login Successful", f"Login failed for {browser_type}"

        # Form validation
        form_result = run_form_submission_test(page)
        assert form_result == "Form Submitted", f"Form submission failed for {browser_type}"

        # Navigation Test
        navigation_result = run_navigation_test(page)
        assert navigation_result == "Navigation Successful", f"Navigation failed for {browser_type}"

        browser.close()

def run_login_test(page, username, password):
    # Find and fill the username
    username_input = page.query_selector('input[name*="user"], input[id*="user"]')
    if username_input:
        username_input.fill(username)
    else:
        return "Username field not found"

    # Find and fill the password
    password_input = page.query_selector('input[name*="pass"], input[id*="pass"]')
    if password_input:
        password_input.fill(password)
    else:
        return "Password field not found"

    # Submit the form
    submit_button = page.query_selector('button[type="submit"], input[type="submit"]')
    if submit_button:
        submit_button.click()
        page.wait_for_load_state("networkidle")
        if "dashboard" in page.url or "welcome" in page.content():
            return "Login Successful"
    return "Login Failed"

def run_form_submission_test(page):
    # Find form fields and fill them
    form_input = page.query_selector('input[name="form-field"]')  # Adjust selectors
    if form_input:
        form_input.fill("Sample Data")
        submit_form_button = page.query_selector('button[type="submit"]')
        if submit_form_button:
            submit_form_button.click()
            page.wait_for_load_state("networkidle")
            return "Form Submitted"
    return "Form Submission Failed"

def run_navigation_test(page):
    # Example for navigation to another page
    navigation_link = page.query_selector('a[href*="next-page"]')
    if navigation_link:
        navigation_link.click()
        page.wait_for_load_state("networkidle")
        if "next-page" in page.url:
            return "Navigation Successful"
    return "Navigation Failed"
