from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=False)  # Set headless=True to run without UI
    context = browser.new_context()
    page = context.new_page()

    # Navigate to Spotify login page
    page.goto('https://www.spotify.com/login')

    # Fill in the login form
    page.fill('input[data-testid="login-username"]', 'samarsingh7266@gmail.com')  # Replace with your username
    page.fill('input[data-testid="login-password"]', 'Samar@12345')  # Replace with your password

    # Wait for the login button to be visible
    page.wait_for_selector('button[data-testid="login-button"]')

    # Click the login button
    page.click('button[data-testid="login-button"]')

    # Wait for the page to load after login
    page.wait_for_load_state('networkidle')  # Wait for network activity to finish

    # Check if login was successful by looking for a specific element
    is_logged_in = page.is_visible('div[class*="profile-name"]')  # Replace with a valid selector

    if is_logged_in:
        print('Login successful!')
    else:
        print('Login failed.')

    # Close the browser
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
