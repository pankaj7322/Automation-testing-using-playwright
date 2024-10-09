import asyncio
from playwright.async_api import async_playwright

async def validate_form(page):
    """
    Check for visible validation errors on the form after submitting.
    """
    # Look for any validation errors (customize the selector based on the form)
    error_selector = 'span.error-message, .error, .invalid-feedback'  # Example selectors for error messages
    if await page.is_visible(error_selector):
        errors = await page.locator(error_selector).all_inner_texts()
        return {"validation_passed": False, "errors": errors}
    return {"validation_passed": True, "errors": []}

async def test_form_validation(url):
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Navigate to the URL
        await page.goto(url)

        # Wait for the form and fill with invalid data
        await page.wait_for_selector('input[name="user-name"]')
        await page.fill('input[name="user-name"]', 'invalid_email')  # Input invalid email
        await page.fill('input[name="password"]', '123')  # Input too short password

        # Wait for the submit button to be available and click it
        await page.wait_for_selector('input[type="submit"]')
        await page.click('input[type="submit"]')

        # Optionally, you can force the form submission with Enter key
        # await page.press('input[name="password"]', 'Enter')

        # Check for validation errors
        validation_result = await validate_form(page)

        # Print results
        if validation_result['validation_passed']:
            print("Form validation passed.")
        else:
            print("Form validation failed.")
            print(f"Errors: {validation_result['errors']}")

        # Close browser
        await browser.close()

# Run the test
asyncio.run(test_form_validation("https://www.saucedemo.com/"))
