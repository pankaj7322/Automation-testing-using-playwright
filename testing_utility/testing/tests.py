from playwright.sync_api import sync_playwright

def test_pagination(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # You can set headless=True for server environments
        page = browser.new_page()
        
        # Navigate to the initial URL
        page.goto(url)
        
        # Check for the "Next" button or pagination links
        next_button_selector = 'a[rel="next"]'  # Commonly used HTML attribute for "Next" buttons
        pagination_selector = 'ul.pagination li a'  # Example for numbered pagination links
        
        pagination_working = False
        
        try:
            # Option 1: Check if a "Next" button exists
            if page.is_visible(next_button_selector):
                print("Next button found.")
                page.click(next_button_selector)
                page.wait_for_load_state('networkidle')
                print(f"Navigated to next page: {page.url}")
                pagination_working = True
            # Option 2: Check for numbered pagination links
            elif page.is_visible(pagination_selector):
                print("Pagination links found.")
                # Find all pagination links
                pagination_links = page.query_selector_all(pagination_selector)
                for link in pagination_links:
                    print(f"Link: {link.inner_text()}")
                
                # Example: Click the next page link (2nd page)
                page.click(pagination_selector)
                page.wait_for_load_state('networkidle')
                print(f"Navigated to next page: {page.url}")
                pagination_working = True
            else:
                print("No pagination controls found.")
        
        except Exception as e:
            print(f"Error during pagination test: {e}")
        
        finally:
            browser.close()
        
        return pagination_working

# Example usage:
url_to_test = "https://example.com/articles"
pagination_result = test_pagination(url_to_test)
if pagination_result:
    print("Pagination is working.")
else:
    print("Pagination is not working or not found.")
