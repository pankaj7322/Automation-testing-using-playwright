from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.cache import cache_control
from django.contrib.auth.models import User
from django.contrib import messages
from asgiref.sync import async_to_sync
from playwright.async_api import async_playwright
import asyncio
import time

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        confirm_password = request.POST['password1']

        if password != confirm_password:
            messages.error(request, "Password do not match")
            return render(request, 'register.html', {'error':'Password do not match'})
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return render(request, 'register.html',{'error':"Username already exists"})

        user = User.objects.create_user(username=username, password=password)
        user.save()

        login(request,user)

        return render(request, 'register.html', {'error': "User Registered Successfully"})
    else:
        return render(request, 'register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')  # Redirect to home after login
        else:
            # Handle invalid login
            return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')


@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def home(request):
    # Render your welcome page for logged-in users
    return render(request, 'welcome.html')


def logout_view(request):
    logout(request)
    return redirect('login')

def navigation(request):
    return render(request, 'navigation_form.html')


def test(request):
    return render(request, 'test_website.html')

def result(request):
    return render(request, 'test_report.html')

def form_test(request):
    return render(request, 'form_test.html')

async def detect_field(page, field_type):
    """
    Attempts to detect the input field based on common selectors.
    :param page: The Playwright page object.
    :param field_type: "username" or "password".
    :return: The detected input field or None if not found.
    """
    selectors = {
        'username': [
            'input[name="username"]',
            'input[name*="user"]',
            'input[name*="email"]',
            'input[id*="user"]',
            'input[id*="email"]',
            'input[name*="login"]'
        ],
        'password': [
            'input[type="password"]',
            'input[name="password"]',
            'input[name*="pass"]',
            'input[id*="pass"]'
        ]
    }
    
    for selector in selectors[field_type]:
        field = await page.query_selector(selector)
        if field:
            return field
    return None

async def run_playwright_test(url, username, password, browser_name):
    async with async_playwright() as p:
        # Launch the browser based on the browser_name
        browser = await getattr(p, browser_name).launch(headless=False)
        page = await browser.new_page()

        start_time = time.time()  # Start timing
        try:
            print(f"Navigating to {url} on {browser_name}...")
            await page.goto(url)

            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(1000)

            # Detect username and password fields
            username_field = await detect_field(page, 'username')
            if username_field:
                await username_field.fill(username)
            else:
                return {
                    'result': f"Username field not found for {url}",
                    'time_taken': time.time() - start_time,
                    'error_details': None
                }

            password_field = await detect_field(page, 'password')
            if password_field:
                await password_field.fill(password)
            else:
                return {
                    'result': f"Password field not found for {url}",
                    'time_taken': time.time() - start_time,
                    'error_details': None
                }

            # Detect and click the submit button
            submit_button = await page.query_selector('button[type="submit"], input[type="submit"], button:has-text("Login"), button:has-text("Log in"), button[id="submit"], button[id="login"]')
            if submit_button:
                await submit_button.click()
            else:
                return {
                    'result': f"Submit button not found for {url}",
                    'time_taken': time.time() - start_time,
                    'error_details': None
                }

            await page.wait_for_load_state('networkidle')

            # Check for successful login (similar logic as before)
            current_url = page.url
            success_indicators = ['div.dashboard', 'div.user-welcome', 'nav', 'h1', 'footer']
            success_found = any([await page.query_selector(indicator) for indicator in success_indicators])

            result_text = f"Login {'successful' if success_found else 'failed'} for {url}"
            return {
                'result': result_text,
                'time_taken': time.time() - start_time,
                'error_details': None
            }

        except Exception as e:
            return {
                'result': f"Test failed for {url}: {str(e)}",
                'time_taken': time.time() - start_time,
                'error_details': str(e)
            }

        finally:
            await browser.close()



def run_tests_view(request):
    if request.method == 'POST':
        urls = request.POST.getlist('url[]')
        usernames = request.POST.getlist('username[]')
        passwords = request.POST.getlist('password[]')

        browsers = ['chromium', 'firefox', 'webkit']  # Automatically run on all browsers

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        tasks = [
            run_playwright_test(url, username, password, browser)
            for url, username, password in zip(urls, usernames, passwords)
            for browser in browsers
        ]

        try:
            results = loop.run_until_complete(asyncio.gather(*tasks))
        except Exception as e:
            return render(request, 'test_report.html', {'error': str(e)})

        test_results = [
            {
                'url': url,
                'username': username,
                'browser': browser,
                'result': result['result'],
                'time_taken': result['time_taken'],
                'error_details': result['error_details']
            }
            for i, (url, username, password) in enumerate(zip(urls, usernames, passwords))
            for browser, result in zip(browsers, results[i*len(browsers):(i+1)*len(browsers)])
        ]

        return render(request, 'test_report.html', {'test_results': test_results})

    return render(request, 'welcome.html')

# *****************************************************************************************

async def validate_form(page):
    try:
        # Modify the error selector to capture specific error messages from the form
        validation_error_selector = 'span.error-message, .error, .invalid-feedback, div.error-message'
        
        # Wait for form submission
        await page.locator("form").evaluate("(form) => form.submit()")
        
        # Check if there are any validation error messages visible
        if await page.is_visible(validation_error_selector):
            errors = await page.locator(validation_error_selector).all_inner_texts()
            errors = [error for error in errors if error.strip()]  # Filter out empty errors
            return {"validation": False, "errors": errors}
        else:
            return {"validation": True, "errors": []}
    except Exception as e:
        # Handle any exceptions and return as error message
        return {"validation": False, "errors": [str(e)]}


async def open_website(url, xpaths, browser_name):
    async with async_playwright() as p:
        browser = await getattr(p, browser_name).launch(headless=False)
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_load_state('networkidle')

        results = []
        for field_xpath in xpaths:
            try:
                # Fill each field with test data
                await page.fill(field_xpath, "TestValue")
                # Store individual field status
                result = await validate_form(page)
                results.append({"field": field_xpath, "validation": result['validation'], "errors": result['errors']})
            except Exception as e:
                results.append({"field": field_xpath, "validation": False, "errors": [str(e)]})

        await page.click('button[type="submit"], input[type="submit"]')
        await browser.close()
        return results

async def run_cross_browser_tests(url, xpaths):
    browser_names = ['chromium', 'firefox', 'webkit']
    all_results = []

    for browser_name in browser_names:
        try:
            browser_results = await open_website(url, xpaths, browser_name)
            for result in browser_results:
                all_results.append({
                    "url": url,
                    "browser": browser_name.capitalize(),
                    "field": result["field"],
                    "validation": result["validation"],
                    "errors": result["errors"]
                })
        except Exception as e:
            all_results.append({
                "url": url,
                "browser": browser_name.capitalize(),
                "field": "N/A",
                "validation": False,
                "errors": [str(e)]
            })
    
    return all_results

def run_form_view(request):
    if request.method == 'POST':
        url = request.POST.get('url')
        xpaths = request.POST.getlist('xpath[]')

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            form_results = loop.run_until_complete(run_cross_browser_tests(url, xpaths))

            # Format the results for the HTML table
            return render(request, 'form_result.html', {'form_results': form_results})
        except Exception as e:
            return render(request, 'form_result.html', {'error': str(e)})

    return render(request, 'form_test.html')

#***********************************************************************************************
# View to handle the navigation test using Playwright
async def test_navigation_for_browser(url, menu_paths, browser_name):
    results = []
    async with async_playwright() as p:
        browser = await getattr(p, browser_name).launch(headless=False)  # Launch the specified browser
        page = await browser.new_page()

        try:
            await page.goto(url)
            await page.wait_for_load_state('networkidle')  # Wait until the page is fully loaded

            for menu_path in menu_paths:
                try:
                    start_time = time.time()
                    await page.click(menu_path)  # Try to click on the menu path
                    await page.wait_for_load_state('networkidle')  # Wait for the page navigation
                    time_taken = (time.time() - start_time) * 1000  # Time taken in ms

                    # Check if the page URL changed after the click (indicating a successful navigation)
                    if page.url != url:
                        results.append({
                            'browser': browser_name,
                            'menu_path': menu_path,
                            'status': 'Success',
                            'new_url': page.url,
                            'time_taken': time_taken,
                            'error_details': None
                        })
                    else:
                        # Optional: Check for a specific element on the new page
                        # e.g., Check if a known header or footer element exists
                        new_page_title = await page.title()
                        if new_page_title:  # This check can be modified based on your needs
                            results.append({
                                'browser': browser_name,
                                'menu_path': menu_path,
                                'status': 'Success',
                                'new_url': page.url,
                                'time_taken': time_taken,
                                'error_details': 'Page title changed, navigation is successful.'
                            })
                        else:
                            results.append({
                                'browser': browser_name,
                                'menu_path': menu_path,
                                'status': 'Error',
                                'new_url': url,
                                'time_taken': time_taken,
                                'error_details': 'No navigation occurred.'
                            })

                    # Navigate back to the original page to test the next menu
                    await page.go_back()
                except Exception as e:
                    results.append({
                        'browser': browser_name,
                        'menu_path': menu_path,
                        'status': 'Error',
                        'new_url': url,
                        'error_details': str(e)
                    })

        except Exception as e:
            results.append({
                'browser': browser_name,
                'status': 'Error',
                'new_url': url,
                'error_details': str(e)
            })

        await browser.close()
    
    return results

async def test_navigation(url, menu_paths):
    browsers = ['chromium', 'firefox', 'webkit']  # List of browsers to test
    tasks = [test_navigation_for_browser(url, menu_paths, browser) for browser in browsers]
    results = await asyncio.gather(*tasks)  # Run all tests in parallel
    return [result for browser_results in results for result in browser_results]  # Flatten the list

# Django view to handle form submission
def navigation_view(request):
    if request.method == 'POST':
        url = request.POST.get('url')  # Get the website URL
        menu_paths = request.POST.getlist('menu_paths[]')  # Get the list of menu path selectors

        # Convert the async function to sync using async_to_sync
        try:
            test_results = async_to_sync(test_navigation)(url, menu_paths)
            return render(request, 'navigation_result.html', {'test_results': test_results, 'url': url})
        except Exception as e:
            return render(request, 'navigation_result.html', {'error': str(e)})

    return render(request, 'navigation_form.html')



#******************************************************************************************************



