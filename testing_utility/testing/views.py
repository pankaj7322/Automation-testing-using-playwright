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
            return render(request, 'register.html', {'error': 'Password do not match'})
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return render(request, 'register.html', {'error': "Username already exists"})

        user = User.objects.create_user(username=username, password=password)
        user.save()

        login(request, user)

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


#****************************************** Login ****************************************

async def detect_field(page, field_type):
    """
    Attempts to detect the input field based on common selectors.
    :param page: The Playwright page object.
    :param field_type: "username" or "password".
    :return: The detected input field or None if not found.
    """
    selectors = {
        'username': [
            'input[type="text"]',
            'input[name="username"]',
            'input[name*="user"]',
            'input[name*="email"]',
            'input[id*="user"]',
            'input[id*="email"]',
            'input[name*="login"]',
            'input[name*="l_emailval"]',
            
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
        browser = await getattr(p, browser_name).launch(headless=False)
        page = await browser.new_page()

        start_time = time.time()
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

            # Click the submit button
            submit_button = await page.query_selector('button[type="submit"], input[type="submit"], input[type="button"], button:has-text("Log In"), button:has-text("Log in")')
            if submit_button:
                await submit_button.click()
            else:
                return {
                    'result': f"Submit button not found for {url}",
                    'time_taken': time.time() - start_time,
                    'error_details': None
                }

            # Wait for a brief moment to allow the page to respond
            await page.wait_for_timeout(2000)

            # Check for error messages
            error_message_selector = 'div[data-testid="login-error"], div.alert, .login-error'
            error_message = await page.query_selector(error_message_selector)

            if error_message:
                error_text = await error_message.inner_text()
                return {
                    'result': f"Login failed for {url}",
                    'time_taken': time.time() - start_time,
                    'error_details': error_text.strip()
                }

            # Wait for user-specific elements indicating a successful login
            # success_indicators = ['img[data-testid="user-profile-picture"]', 'div.dashboard']
            # success_indicators = ['div']
            # success_indicators = ['Your Library']
            success_indicators = ['div.body-drag-top','html.spotify__container--is-web body', 'login_head_menu']
            for indicator in success_indicators:
                try:
                    await page.wait_for_selector(indicator, timeout=5000)  # Wait for each success indicator
                    return {
                        'result': f"Login successful for {url}",
                        'time_taken': time.time() - start_time,
                        'error_details': None
                    }
                except Exception:
                    continue  # Ignore if the element is not found

            return {
                'result': f"Login failed for {url} (no success indicators found)",
                'time_taken': time.time() - start_time,
                'error_details': "No success indicators found"
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

        # Automatically run on all browsers
        browsers = ['chromium', 'firefox', 'webkit']

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

# **************************************** Login END *************************************************************

# ***********************************************************************************************
# View to handle the navigation test using Playwright


async def test_navigation_for_browser(url, menu_paths, browser_name):
    results = []
    async with async_playwright() as p:
        # Launch the specified browser
        browser = await getattr(p, browser_name).launch(headless=False)
        page = await browser.new_page()

        try:
            await page.goto(url)
            # Wait until the page is fully loaded
            await page.wait_for_load_state('networkidle')

            for menu_path in menu_paths:
                try:
                    start_time = time.time()
                    # Try to click on the menu path
                    await page.click(menu_path)
                    # Wait for the page navigation
                    await page.wait_for_load_state('networkidle')
                    time_taken = (time.time() - start_time) * \
                        1000  # Time taken in ms

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
    tasks = [test_navigation_for_browser(
        url, menu_paths, browser) for browser in browsers]
    results = await asyncio.gather(*tasks)  # Run all tests in parallel
    # Flatten the list
    return [result for browser_results in results for result in browser_results]

# Django view to handle form submission


def navigation_view(request):
    if request.method == 'POST':
        url = request.POST.get('url')  # Get the website URL
        # Get the list of menu path selectors
        menu_paths = request.POST.getlist('menu_paths[]')

        # Convert the async function to sync using async_to_sync
        try:
            test_results = async_to_sync(test_navigation)(url, menu_paths)
            return render(request, 'navigation_result.html', {'test_results': test_results, 'url': url})
        except Exception as e:
            return render(request, 'navigation_result.html', {'error': str(e)})

    return render(request, 'navigation_form.html')


# ******************************************************************************************************
# Helper function to handle the end-to-end test, login, aria-label collection, and search actions
async def end_to_end_test_for_browser(url, browser_name):
    results = []
    async with async_playwright() as p:
        # Launch the specified browser
        browser = await getattr(p, browser_name).launch(headless=False)
        page = await browser.new_page()

        try:
            start_time = time.time()
            await page.goto(url)
            await page.wait_for_load_state('networkidle')
            end_time = time.time()
            results.append({
                'browser': browser_name,
                'step': 'Page Load',
                'status': 'Success',
                'time_taken': end_time - start_time
            })
            
            # Perform the login process
            try:
                start_time = time.time()
                await page.fill("input[type='text']", "samarsingh7266@gmail.com")  # Replace with your username
                await page.fill("input[type='password']", "Samar@12345")  # Replace with your password
                await page.click("button[id='login-button']")  # Replace with the login button selector

                # Wait for a selector to confirm successful login
                try:
                    await page.wait_for_selector("span[class='fmZ0hU6ImbDQi5qGWLvF']")  # Replace with a unique selector after login
                except Exception as e:
                    results.append({
                        'browser': browser_name,
                        'step': 'Login',
                        'status': 'Error',
                        'error_details': f"Login failed: {str(e)}"
                    })
                    return results
                
                end_time = time.time()
                results.append({
                    'browser': browser_name,
                    'step': 'Login',
                    'status': 'Success',
                    'time_taken': end_time - start_time
                })
            except Exception as e:
                results.append({
                    'browser': browser_name,
                    'step': 'Login',
                    'status': 'Error',
                    'error_details': f"Login failed: {str(e)}"
                })
                return results

            # Wait to ensure all target elements are fully loaded
            await page.wait_for_timeout(5000)  # Adjust timeout if needed (2 seconds)

            # Collect elements with aria-labelledby attribute starting with "card-title-spotify:show:"
            start_time = time.time()
            try:
                elements = await page.query_selector_all('.CardButton-sc-g9vf2u-0.eWZOJQ')  # Select elements with this class
                labels = [await element.get_attribute("aria-labelledby") for element in elements]
            except Exception as e:
                results.append({
                    'browser': browser_name,
                    'step': 'Collect Albums',
                    'status': 'Error',
                    'error_details': f"Failed to collect labels: {str(e)}"
                })
                return results
            end_time = time.time()

            if labels:
                results.append({
                    'browser': browser_name,
                    'step': 'Collect Albums',
                    'status': 'Success',
                    'labels': labels[:2],  # Print the first 2 labels
                    'time_taken': end_time - start_time
                })
            else:
                results.append({
                    'browser': browser_name,
                    'step': 'Collect Albums',
                    'status': 'No Albums Found',
                    'time_taken': end_time - start_time
                })

            # Perform interactions on the first two labels if they exist
            for i, label in enumerate(labels[:2]):
                try:
                    label_selector = f"[aria-labelledby='{label}']"
                    start_time = time.time()
                    await page.wait_for_selector(label_selector)
                    await page.click(label_selector)
                    await page.wait_for_load_state('load')
                    end_time = time.time()

                    results.append({
                        'browser': browser_name,
                        'step': f'Click on Label: {label}',
                        'status': 'Success',
                        'time_taken': end_time - start_time
                    })
                    
                    # Go back to the previous page and wait for it to load
                    await page.wait_for_timeout(5000)
                    await page.go_back()
                    await page.wait_for_load_state('load')  # Wait for the previous page to load completely
                    results.append({
                        'browser': browser_name,
                        'step': 'Go Back',
                        'status': 'Success',
                        'time_taken': time.time() - end_time
                    })

                except Exception as e:
                    results.append({
                        'browser': browser_name,
                        'step': f'Click on Label {label}',
                        'status': 'Error',
                        'error_details': f"Failed to click label {label}: {str(e)}"
                    })

            # Perform a search after login
            try:
                start_time = time.time()
                await page.wait_for_selector("input[data-encore-id='formInput']")  # Wait for the search input field to appear
                await page.fill("input[data-encore-id='formInput']", "Justin Bieber Top 10")  # Example search term
                end_time = time.time()

                results.append({
                    'browser': browser_name,
                    'step': 'Search',
                    'status': 'Success',
                    'search_term': 'Justin Bieber Top 10',
                    'time_taken': end_time - start_time
                })

                # Wait for search results to load
                await page.wait_for_selector(".ouEZqTcvcvMfvezimm_J")  # Adjust selector if necessary to wait for search results
                await page.wait_for_timeout(5000)

                # Click on the first search result
                start_time = time.time()
                await page.click(".ouEZqTcvcvMfvezimm_J")
                await page.wait_for_load_state('load')
                end_time = time.time()

                results.append({
                    'browser': browser_name,
                    'step': 'Click on First Search Result',
                    'status': 'Success',
                    'time_taken': end_time - start_time
                })
            except Exception as e:
                results.append({
                    'browser': browser_name,
                    'step': 'Search',
                    'status': 'Error',
                    'error_details': f"Search failed: {str(e)}"
                })

            # Click a button after the search result
            try:
                start_time = time.time()
                await page.wait_for_selector("button[aria-label='Save to Your Library']")  # Replace with actual button selector
                await page.click("button[aria-label='Save to Your Library']")
                end_time = time.time()

                results.append({
                    'browser': browser_name,
                    'step': 'Click Save to Library',
                    'status': 'Success',
                    'time_taken': end_time - start_time
                })
            except Exception as e:
                results.append({
                    'browser': browser_name,
                    'step': 'Click Save to Library',
                    'status': 'Error',
                    'error_details': f"Failed to click save button: {str(e)}"
                })

            # Wait 2 seconds before going back
            await page.wait_for_timeout(5000)

            # Click on multiple songs to like them
            try:
                start_time = time.time()
                like_buttons = await page.query_selector_all("button[aria-label='Add to Liked Songs'][aria-checked='false']")
                for index, button in enumerate(like_buttons[:5]):
                    await button.click()
                    await page.wait_for_timeout(2000)  # Wait for 2 seconds after clicking each button
                end_time = time.time()

                results.append({
                    'browser': browser_name,
                    'step': 'Like Songs',
                    'status': 'Success',
                    'time_taken': end_time - start_time
                })
            except Exception as e:
                results.append({
                    'browser': browser_name,
                    'step': 'Like Songs',
                    'status': 'Error',
                    'error_details': f"Failed to like songs: {str(e)}"
                })

            # Go back to the previous page and wait for it to load
            try:
                start_time = time.time()
                await page.go_back()
                await page.wait_for_load_state('load')
                end_time = time.time()

                results.append({
                    'browser': browser_name,
                    'step': 'Go Back After Liking Songs',
                    'status': 'Success',
                    'time_taken': end_time - start_time
                })
            except Exception as e:
                results.append({
                    'browser': browser_name,
                    'step': 'Go Back After Liking Songs',
                    'status': 'Error',
                    'error_details': f"Failed to go back: {str(e)}"
                })

            await page.wait_for_timeout(5000)

            # --- Click on Profile Section ---
            try:
                await page.wait_for_selector("button[data-testid='user-widget-link'][aria-label='Samar Singh']")
                await page.click("button[data-testid='user-widget-link'][aria-label='Samar Singh']")
                await page.wait_for_timeout(5000)
            except Exception as e:
                results.append({
                    'browser': browser_name,
                    'step': 'Profile Section',
                    'status': 'Error',
                    'error_details': f"Failed to click profile button: {str(e)}"
                })

            # --- Log Out Functionality ---
            try:
                await page.wait_for_selector("button[data-testid='user-widget-dropdown-logout']")
                await page.click("button[data-testid='user-widget-dropdown-logout']")
                await page.wait_for_timeout(3000)
                await page.wait_for_selector("button[data-testid='login-button']")
                results.append({
                    'browser': browser_name,
                    'step': 'Logout',
                    'status': 'Success',
                    'time_taken': None
                })
            except Exception as e:
                results.append({
                    'browser': browser_name,
                    'step': 'Logout',
                    'status': 'Error',
                    'error_details': f"Failed to log out: {str(e)}"
                })

            # Close browser
            await browser.close()

            # Append successful navigation result
            results.append({
                'browser': browser_name,
                'step': 'Test Complete',
                'status': 'Success',
                'new_url': page.url,
                'time_taken': None,
                'error_details': None
            })

        except Exception as e:
            results.append({
                'browser': browser_name,
                'step': 'Error',
                'status': 'Error',
                'error_details': str(e)
            })

        await browser.close()

    return results



# Async function to test all browsers
async def run_end_to_end_tests(url):
    browsers = ['chromium', 'firefox', 'webkit']  # List of browsers to test
    tasks = [end_to_end_test_for_browser(url, browser) for browser in browsers]
    results = await asyncio.gather(*tasks)  # Run all tests in parallel
    # Flatten the list
    return [result for browser_results in results for result in browser_results]

# Django view to handle form submission
def navigation_view_new(request):
    if request.method == 'POST':
        url = request.POST.get('url')  # Get the website URL

        # Convert the async function to sync using async_to_sync
        try:
            test_results = async_to_sync(run_end_to_end_tests)(url)
            return render(request, 'end_to_end.html', {'test_results': test_results, 'url': url})
        except Exception as e:
            return render(request, 'end_to_end.html', {'error': str(e)})

    return render(request, 'end_to_end.html')