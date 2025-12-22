import re

import pytest
from playwright.sync_api import Page, expect

from inclusive_world_portal.users.models import User
from inclusive_world_portal.users.tests.factories import UserFactory

# Mark all tests in this module as requiring a live server with transactional database
pytestmark = [pytest.mark.django_db(transaction=True)]

def test_home_page_title(page: Page, live_server):
    """
    Test that the home page redirects unauthenticated users to login.
    """
    page.goto(live_server.url)
    # The home page should redirect to login for unauthenticated users
    expect(page).to_have_title(re.compile(r"Sign In", re.IGNORECASE))
    # Verify we're on the login page
    expect(page).to_have_url(re.compile(r"/accounts/login/"))

def test_login_flow(page: Page, live_server):
    """
    Test the login flow.
    """
    user = UserFactory(password="password123")
    
    page.goto(f"{live_server.url}/accounts/login/")
    
    # Fill in the login form
    # Adjust selectors based on your actual templates (usually id_login and id_password)
    page.fill("input[name='login']", user.email)
    page.fill("input[name='password']", "password123")
    
    # Click the login button
    page.click("button[type='submit']")
    
    # Expect to be redirected or see a success message
    # For example, checking if "Sign Out" is visible
    # expect(page.get_by_text("Sign Out")).to_be_visible()
    # Or check URL
    # expect(page).to_have_url(f"{live_server.url}/")
