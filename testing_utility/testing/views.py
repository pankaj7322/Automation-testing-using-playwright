from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.cache import cache_control
from django.contrib.auth.models import User
from .forms import RegisterForm
from django.contrib import messages
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
import subprocess
import asyncio
import os
from django.conf import settings
import datetime

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

async def run_playwright_test(url, username, password):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        try:
            print(f"Navigating to {url}...")
            await page.goto(url)

            # Wait for the page to fully load
            await page.wait_for_load_state('networkidle')

            # Wait a bit more for the fields to be available
            await page.wait_for_timeout(1000)

            # Detect username and password fields
            username_field = await detect_field(page, 'username')
            if username_field:
                await username_field.fill(username)
                print(f"Filled username: {username}")
            else:
                return f"Username field not found for {url}"

            password_field = await detect_field(page, 'password')
            if password_field:
                await password_field.fill(password)
                print("Filled password.")
            else:
                return f"Password field not found for {url}"

            # Detect and click submit button
            submit_button = await page.query_selector('button[type="submit"], input[type="submit"], button:has-text("Login"), button:has-text("Log in"), button[id="submit"], button[id="login"]')
            if submit_button:
                await submit_button.click()
                print("Clicked submit button.")
            else:
                return f"Submit button not found for {url}"

            # Wait for navigation
            await page.wait_for_load_state('networkidle')

            # Check for URL change
            current_url = page.url
            print(f"Current URL after login: {current_url}")

            # Check for common elements that signify a successful login
            # You can define a list of common elements that may appear on successful login
            success_indicators = [
                'div.dashboard',  # Adjust according to the expected element
                'div.user-welcome',  # Example for a user welcome message
                'nav',  # Common navigation element for logged-in users
                'h1',  # Check for headers that typically appear
                'footer'  # Check for footer elements as an additional indicator
            ]

            success_found = False
            for indicator in success_indicators:
                element = await page.query_selector(indicator)
                if element:
                    success_found = True
                    break
            
            if success_found:
                return f"Login successful for {url}"
            else:
                return f"Login failed for {url}: No success indicators found."

        except Exception as e:
            return f"Test failed for {url}: {str(e)}"

        finally:
            await browser.close()





def run_tests_view(request):
    if request.method == 'POST':
        urls = request.POST.getlist('url[]')
        usernames = request.POST.getlist('username[]')
        passwords = request.POST.getlist('password[]')

        # Create an event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Prepare tasks for parallel execution
        tasks = [
            run_playwright_test(url, username, password)
            for url, username, password in zip(urls, usernames, passwords)
        ]

        try:
            # Run all tests asynchronously
            results = loop.run_until_complete(asyncio.gather(*tasks))
        except Exception as e:
            return render(request, 'test_report.html', {'error': str(e)})

        # Create a structured data format for table display
        test_results = [
            {'url': url, 'username': username, 'result': result}
            for url, username, result in zip(urls, usernames, results)
        ]

        # Pass the structured results to the template
        return render(request, 'test_report.html', {'test_results': test_results})

    return render(request, 'welcome.html')
