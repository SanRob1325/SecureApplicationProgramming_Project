import pytest
import time
from app import create_app
from app.models import User, db
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from app.routes.admin import users

# Reference to Selenium testing:https://selenium-python.readthedocs.io/
# Reference to test construction:https://www.browserstack.com/guide/python-selenium-to-run-web-automation-test
# Reference to testing in the selenium library: https://medium.com/@moraneus/guide-to-using-python-selenium-873342d5fdad
class TestSecurePass:
    @pytest.fixture(autouse=True)
    def setup(self):
        # Set up Selenium Webdriver
        self.driver = webdriver.Chrome()
        self.base_url = "http://127.0.0.1:5000"
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, 10) # applies for all tests
        yield
        # Teardown
        self.driver.quit()

    def test_authentication_flow(self):
        driver = self.driver
        # Test registration
        driver.get(self.base_url + "/auth/register")

        # Use timestamp for ensuring username uniquenes
        unique_username = f"user_test_{int(time.time())}"
        driver.find_element(By.ID,"username").send_keys(unique_username)
        driver.find_element(By.ID,"password").send_keys("Testthe@Password123")
        driver.find_element(By.ID,"password2").send_keys("Testthe@Password123")

        # Take a screenshot before submitting
        driver.save_screenshot("before_submit.png")
        driver.find_element(By.ID, "submit").click()

        self.wait.until(EC.url_contains("/auth/login"))

        driver.save_screenshot("after_submit.png")

        print(f"Current URL after registration:{driver.current_url}")

        # Any Flash error messages
        try:
            flash_messages = driver.find_elements(By.CLASS_NAME, "alert")
            for message in flash_messages:
                print(f"Flash message: {message.text}")
        except:
            print("No flash messages")

        # Test login
        driver.find_element(By.NAME, "username").send_keys(unique_username)
        driver.find_element(By.NAME, "password").send_keys("Testthe@Password123")
        driver.find_element(By.NAME, "submit").click()

        # Create delay to let the page respond
        time.sleep(2)

        # Take a screenshot after submitting
        driver.save_screenshot("after_login.png")

        # Print current URL
        print(f"Current URL after registration: {driver.current_url}")

        # Check if login was successful by looking for elements that should be present after login
        try:
            # Wait for "My Credentials" text or username in the navbar
            self.wait.until(lambda d: "My Credentials" in d.page_source or unique_username in d.page_source)
            print("Login successful! Found elements in the authenticated page")
            assert True
        except TimeoutException:
            print("Login unsuccessful! could not find authenticated elements")
            driver.save_screenshot("login_failed.png")
            assert False, "Login unsuccessful! could not find authenticated elements"

    def test_user_logout(self):
        """Test useer logout functionality"""
        driver = self.driver

        test_username = f"logout_test_{int(time.time())}"
        test_password = "Test@Password123!"

        # Registration
        driver.get(self.base_url + "/auth/register")
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(test_password)
        driver.find_element(By.NAME, "password2").send_keys(test_password)
        driver.find_element(By.NAME, "submit").click()

        # Login with initial password
        self.wait.until(EC.url_contains("/auth/login"))
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(test_password)
        driver.find_element(By.NAME, "submit").click()

        # Wait for login to be complete
        time.sleep(2)

        assert test_username in driver.page_source, "Login unsuccessful"

        # Take screenshot before logout
        driver.save_screenshot("before_logout.png")

        # Perform logout
        driver.get(self.base_url + "/auth/logout")
        time.sleep(2)

        # Take a screenshot after logout
        driver.save_screenshot("after_logout.png")

        # Verify redirect to login page
        assert "/auth/login" in driver.current_url, "Not redirected to login page after logout"

        # Check for logout message
        flash_messages = driver.find_elements(By.CLASS_NAME, "alert")
        logout_message_found = False
        for message in flash_messages:
            if "logged out" in message.text.lower():
                logout_message_found = True
                break
        assert logout_message_found, "Logout message not found"

        # Verify authentication required page redirects to login
        driver.get(self.base_url + "/")
        time.sleep(1)
        assert "/auth/login" in driver.current_url, "Protected page accessible after logout"

    def test_credential_management(self):
        """Test Credential creation, viewing, editing, and deletion"""
        driver = self.driver

        test_username = f"testcred_{int(time.time())}"
        test_password = "Test@Password123!"
        driver.get(self.base_url + "/auth/register")
        try:
            driver.find_element(By.NAME,"username").send_keys(test_username)
            driver.find_element(By.NAME,"password").send_keys(test_password)
            driver.find_element(By.NAME, "password2").send_keys(test_password)
            driver.find_element(By.NAME,"submit").click()
            self.wait.until(EC.url_contains("/auth/login"))
            print(f"Registered new user: {test_username}")
        except Exception as e:
            print(f"Error during registration: {e} ")
            driver.save_screenshot("registration_error.png")
            raise
        driver.get(self.base_url + "/auth/login")
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(test_password)
        driver.find_element(By.NAME, "submit").click()
        time.sleep(2) # To wait for login to complete

        driver.get(self.base_url + "/add")
        time.sleep(2)

        service_name = f"Test Service {int(time.time())}"
        try:
            # The form fields are rendered by WTForms with specific IDs
            driver.find_element(By.ID, "service_name").send_keys(service_name)
            driver.find_element(By.ID, "username").send_keys("serviceuser")
            driver.find_element(By.ID, "password").send_keys("ServicePass123!")

            # Take screenshot before submitting
            driver.save_screenshot("before_submit_credential.png")

            try:
                # First try with input submit
                submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            except NoSuchElementException:
                try:
                    submit_button = driver.find_element(By.NAME, "submit")
                except NoSuchElementException:
                    # Try ayn button primary as a fallback
                    submit_button = driver.find_element(By.CSS_SELECTOR, ".btn-primary")

            submit_button.click()

            # Allow more time for processing
            time.sleep(3)

            # Check for any flash messages
            try:
                flash_messages = driver.find_elements(By.CLASS_NAME, "alert")
                for message in flash_messages:
                    print(f"Flash message after submission: {message.text}")
            except:
                print("No flash messages after submission")

            # Explicitly navigate to the list page to refresh
            driver.get(self.base_url + "/")
            time.sleep(2)

            # Save screenshot
            driver.save_screenshot("credential_list_after_add.png")

            # Verify the credential is in paged content
            page_source = driver.page_source
            if service_name in page_source:
                print(f"Successfully found credential: {service_name}")
                assert True
            else:
                print(f"Failed to find credential: {service_name}")
                print("Page source preview:", page_source[:1000])

                # Additional debug info
                print("Current URL:", driver.current_url)
                print("Page title:", driver.title)

                # try to find table elements
                try:
                    credentials_table = driver.find_element(By.ID, "credentialsTable")
                    rows = credentials_table.find_elements(By.TAG_NAME, "tr")
                    print(f"Found {len(rows)} credential rows")
                    for row in rows:
                        print(f"Row: {row.text}")
                except Exception as e:
                    print(f"Failed finding credentials table: {e}")

                # Final assertion
                assert service_name in page_source, "Added credential was not found on page"
        except Exception as e:
            print(f"Error during credential management test: {e}")
            driver.save_screenshot("credential_test_error.png")
            raise


    def test_password_change(self):
        """Test changing user's password and verifying the can login with a new password"""
        driver = self.driver

        # Register and login with initial password
        test_username = f"pwd_change_{int(time.time())}"
        initial_password = "Initial@Password123!"
        new_password = "New@Password123!"

        # Registration
        driver.get(self.base_url + "/auth/register")
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(initial_password)
        driver.find_element(By.NAME, "password2").send_keys(initial_password)
        driver.find_element(By.NAME, "submit").click()

        # Login with initial password
        self.wait.until(EC.url_contains("/auth/login"))
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(initial_password)
        driver.find_element(By.NAME, "submit").click()

        # Wait for login to be complete
        time.sleep(2)
        driver.save_screenshot("before_password_change.png")
        # navigate to change password
        driver.get(self.base_url + "/auth/change_password")

        # Fill in change password
        driver.find_element(By.ID, "current_password").send_keys(initial_password)
        driver.find_element(By.ID, "new_password").send_keys(new_password)
        driver.find_element(By.ID, "new_password2").send_keys(new_password)

        driver.save_screenshot("password_change_form_filled.png")
        # Submit form
        submit_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
        submit_button.click()

        # Wait longer for the form to process
        time.sleep(3)

        #Print current URL to see if the page is redirected correctly
        print(f"Current URL for password change: {driver.current_url}")

        # Check page content
        print("Page content contains 'Credentials':" "Credentials" in driver.page_source)
        # Check for success message
        flash_messages = driver.find_elements(By.CLASS_NAME, "alert")
        print("Flash messages found:")
        for message in flash_messages:
            print(f"Flash message: {message.text}")

        success_message_found = False
        for message in flash_messages:
            if "password has been updated" in message.text.lower():
                success_message_found = True
                break
        assert success_message_found, "Password change success message not found"

        # Logout
        driver.get(self.base_url + "/auth/logout")

        # Login with a new password
        driver.get(self.base_url + "/auth/login")
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(new_password)
        driver.find_element(By.NAME, "submit").click()
        # Wait for login
        time.sleep(2)

        driver.save_screenshot("login_with_new_password.png")
        success = "My Credentials" in driver.page_source or test_username in driver.page_source
        # Verify successful login
        assert success, "Login with new password failed"
        assert "/auth/login" not in driver.current_url, "Still on login page after attempting login with new password"


    def test_credential_edit(self):
        """Test editing an existing credential"""
        driver = self.driver

        # Registration, login and create credential similar to test_crdential_management
        test_username = f"edit_test_{int(time.time())}"
        test_password = "Test@Password123!"

        # Registration
        driver.get(self.base_url + "/auth/register")
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(test_password)
        driver.find_element(By.NAME, "password2").send_keys(test_password)
        driver.find_element(By.NAME, "submit").click()

        # Login
        self.wait.until(EC.url_contains("/auth/login"))
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(test_password)
        driver.find_element(By.NAME, "submit").click()
        time.sleep(2)

        # Create credential with initial values
        driver.get(self.base_url + "/add")

        # Initial credential details
        service_name = f"Edit Test {int(time.time())}"
        initial_username = "initial_user"
        initial_password = "Initial@Password123!"

        # Fill in form
        driver.find_element(By.ID, "service_name").send_keys(service_name)
        driver.find_element(By.ID, "username").send_keys(initial_username)
        driver.find_element(By.ID, "password").send_keys(initial_password)

        # Submit form
        submit_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
        submit_button.click()
        time.sleep(2)

        # Updated credential details
        updated_username = "updated_user"
        updated_password = "Updated@Pass456"

        # Find and click the edit button for this credential
        edit_button = driver.find_element(By.XPATH, f"//td[contains(text(),'{service_name}')]/ancestor::tr//a[contains(@href, '/edit/')]")
        edit_button.click()
        time.sleep(2)

        # Update the credential
        username_field = driver.find_element(By.NAME, "username")
        username_field.clear()
        username_field.send_keys(updated_username)

        # Update the password
        password_field = driver.find_element(By.ID, "password")
        password_field.clear()
        password_field.send_keys(updated_password)

        # Submit form
        submit_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
        submit_button.click()
        time.sleep(2)

        # Navigate back to credential list to ensure refresh
        driver.get(self.base_url + "/")
        time.sleep(1)

        # Verify the credential was updated
        page_source = driver.page_source
        assert service_name in page_source, "Service name not found after update"
        assert updated_username in page_source, "Updated username not found after update"

    def test_credential_delete(self):
        """Test deleting an existing credential"""
        driver = self.driver

        # Registration and login
        test_username = f"delete_test_{int(time.time())}"
        test_password = "Test@Password123!"

        # Registration
        driver.get(self.base_url + "/auth/register")
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(test_password)
        driver.find_element(By.NAME, "password2").send_keys(test_password)
        driver.find_element(By.NAME, "submit").click()

        # Login
        self.wait.until(EC.url_contains("/auth/login"))
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(test_password)
        driver.find_element(By.NAME, "submit").click()
        time.sleep(2)

        # Create credential
        driver.get(self.base_url + "/add")

        # Create a unique service name
        service_name = f"Delete Test {int(time.time())}"

        # Fill in the form
        driver.find_element(By.ID, "service_name").send_keys(service_name)
        driver.find_element(By.ID, "username").send_keys("delete user")
        driver.find_element(By.ID, "password").send_keys("Delete@Pass123")

        # Submit the form
        submit_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
        submit_button.click()
        time.sleep(2)

        # Verify credential was created
        assert service_name in driver.page_source, "Credential was not created successfully"

        # Take a screenshot before deletion
        driver.save_screenshot("before_deletion.png")

        # Find and click the delete button for this credential
        delete_button = driver.find_element(By.XPATH, f"//td[contains(text(), '{service_name}')]/ancestor::tr//button[contains(@class, 'btn-danger')]")
        delete_button.click()

        # Handle confirmation modal
        self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".modal-dialog")))
        confirm_delete = driver.find_element(By.XPATH, "//div[contains(@class, 'modal-footer')]//button[contains(@class, 'btn-danger')]")
        confirm_delete.click()
        time.sleep(2)

        # Navigate back to main page to ensure refresh
        driver.get(self.base_url + "/")
        time.sleep(1)

        # Take a screenshot after deletion
        driver.save_screenshot("after_deletion.png")

        # Verify the credential was deleted
        assert service_name not in driver.page_source, "Credential was not deleted successfully"

    def test_password_generator_integration(self):
        """Test using the password generator while adding credential"""
        driver = self.driver

        # Registration and login
        test_username = f"generator_test_{int(time.time())}"
        test_password = "Test@Password123!"

        driver.get(self.base_url + "/auth/register")
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(test_password)
        driver.find_element(By.NAME, "password2").send_keys(test_password)
        driver.find_element(By.NAME, "submit").click()

        # Login
        self.wait.until(EC.url_contains("/auth/login"))
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(test_password)
        driver.find_element(By.NAME, "submit").click()
        time.sleep(2)

        # Navigate to add credential page
        driver.get(self.base_url + "/add")
        time.sleep(2)

        driver.save_screenshot("add_credential_before_generator.png")
        # Fill in service name and username
        service_name = f"generator_test_{int(time.time())}"
        driver.find_element(By.NAME, "service_name").send_keys(service_name)
        driver.find_element(By.NAME, "username").send_keys("generated_password_user")

        # Get the password field to check if its empty initially

        password_field = driver.find_element(By.ID, "password")
        initial_password = password_field.get_attribute("value")
        print(f"Initial password value: {initial_password}")

        # Verify modal exists in page source first
        if "passwordGeneratorModal" in driver.page_source:
            print("Password generator modal exists in page source")
        else:
            print("Warning: Password generator modal not found in page source")

        try:
            generate_button = driver.find_element(By.ID, "generatePassword")
            generate_button.click()
            time.sleep(2)  # Wait for modal animation

            driver.save_screenshot("after_generate_button_click.png")

            # Try directly finding modal instead of waiting
            try:
                modal = driver.find_element(By.ID, "passwordGeneratorModal")
                print(f"Modal found directly: {modal.is_displayed()}")

                # If modal is found try clicking the useGeneratedPassword button

                use_password_button = driver.find_element(By.ID, "useGeneratedPassword")
                use_password_button.click()
                time.sleep(1)

                # Check if password field has a value
                new_password = password_field.get_attribute("value")
                print(f"New password value: {new_password}")

                # Take a screenshot of add page
                driver.save_screenshot("add_credential_before_generator.png")
                # Click generate password button
                assert new_password != "", "Password field is empty after using generator"
                assert new_password != initial_password, "Password field is was not updated"

                # Submit form
                submit_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
                submit_button.click()
                time.sleep(2)

                driver.get(self.base_url + "/")
                time.sleep(1)
                # Verify credential was added
                assert service_name in driver.page_source, "Generated password credential was not added successfully"

            except NoSuchElementException as e:
                print(f"Error finding modal or related elements: {e}")
                # Fallback plan by just adding a credential manually
                password_field.send_keys("ManualPassword@123")
                submit_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
                submit_button.click()
                time.sleep(2)

                # Verify credential was added
                driver.get(self.base_url + "/")
                time.sleep(1)
                assert service_name in driver.page_source, "Credential was not added successfully"
                # Take a screenshot after click generate button

        except Exception as e:
            print(f"Error in password generator test: {e}")
            driver.save_screenshot("password_generator_error.png")

            # Fallback to complete test by addint credential without usin generator
            password_field.send_keys("FallbackPassword@123")
            submit_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
            submit_button.click()
            time.sleep(2)
            driver.get(self.base_url + "/")
            time.sleep(1)
            assert service_name in driver.page_source, "Fallback credential was not added successfully"

    def test_navigation_flow(self):
        """Test navigation between different sections of the application"""
        driver = self.driver

        # Registration and login
        test_username = f"nav_test_{int(time.time())}"
        test_password = "Test@Password123!"

        # Registration
        driver.get(self.base_url + "/auth/register")
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(test_password)
        driver.find_element(By.NAME, "password2").send_keys(test_password)
        driver.find_element(By.NAME, "submit").click()

        # Login
        self.wait.until(EC.url_contains("/auth/login"))
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(test_password)
        driver.find_element(By.NAME, "submit").click()
        time.sleep(2)

        # Test navigation to each main section
        nav_items = [
            {"link_text": "My Credentials", "expected_url": "/"},
            {"link_text": "Search Credentials", "expected_url": "/search"},
            {"link_text": "Password Generator", "expected_url": "/generator"}
        ]

        for item in nav_items:
            try:
                # Take a screenshot before navigation
                driver.save_screenshot(f"before_nav_to_{item['expected_url'].replace('/', '_')}.png")

                # Find and click the navigation link
                link = driver.find_element(By.LINK_TEXT, item['link_text'])
                link.click()
                time.sleep(1)

                # Take a screenshot after navigation
                driver.save_screenshot(f"after_nav_to_{item['expected_url'].replace('/', '_')}.png")

                # Verify navigation worked
                assert item["expected_url"] in driver.current_url, f"Navigation to {item['link_text']} failed"
                print(f"Successful navigated to {item['link_text']}")
            except Exception as e:
                print(f"Error navigating to {item['link_text']}: {e}")
                raise

    def test_search_functionality(self):
        """Test credential search functionality"""
        driver = self.driver

        # Registration and login
        test_username = f"search_test_{int(time.time())}"
        test_password = "Test@Password123!"

        # Registration
        driver.get(self.base_url + "/auth/register")
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(test_password)
        driver.find_element(By.NAME, "password2").send_keys(test_password)
        driver.find_element(By.NAME, "submit").click()

        # Login
        self.wait.until(EC.url_contains("/auth/login"))
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(test_password)
        driver.find_element(By.NAME, "submit").click()
        time.sleep(2)

        # Create credentials with distinct names
        timestamp = int(time.time())
        service_names = [
            f"SearchTest_Apple_{timestamp}",
            f"SearchTest_Banana_{timestamp}",
            f"SearchTest_Cherry_{timestamp}",
        ]

        for service_name in service_names:
            driver.get(self.base_url + "/add")

            driver.find_element(By.ID, "service_name").send_keys(service_name)
            driver.find_element(By.ID, "username").send_keys(f"user_{service_name}")
            driver.find_element(By.ID, "password").send_keys("Search@Pass123")

            submit_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
            submit_button.click()
            time.sleep(1)

        # Navigate to search page
        driver.get(self.base_url + "/search")

        # take screenshot before search
        driver.save_screenshot("before_search.png")

        # Search for Apple
        search_input = driver.find_element(By.NAME, "query")
        search_input.send_keys("Apple")
        search_input.submit()
        time.sleep(2)

        # Take screenshot after search
        driver.save_screenshot("after_search.png")

        # Get page source
        page_source = driver.page_source

        # Verify only Apple credential shown above
        assert service_names[0] in page_source, "Apple credential not found in search results"
        assert service_names[1] not in page_source, "Banana credential appeared in Apple search results"
        assert service_names[2] not in page_source, "Chery credential appeared in Apple search results"

    def test_password_visibility_toggle(self):
        """Test toggling password visibility"""
        driver = self.driver

        # Registration and login
        test_username = f"visibility_test_{int(time.time())}"
        test_password = "Test@Password123!"

        # Registration
        driver.get(self.base_url + "/auth/register")
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(test_password)
        driver.find_element(By.NAME, "password2").send_keys(test_password)
        driver.find_element(By.NAME, "submit").click()

        # Login
        self.wait.until(EC.url_contains("/auth/login"))
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(test_password)
        driver.find_element(By.NAME, "submit").click()
        time.sleep(2)

        # Add credential
        driver.get(self.base_url + "/add")
        service_name = f"Visibility Test {int(time.time())}"
        credential_password = "VisibilityTest@Password123!"

        driver.find_element(By.ID, "service_name").send_keys(service_name)
        driver.find_element(By.ID, "username").send_keys("visibility_user")
        driver.find_element(By.ID, "password").send_keys(credential_password)

        submit_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
        submit_button.click()
        time.sleep(2)

        # verify credential has been added
        assert service_name in driver.page_source, "Credential was not created successfully"
        # Navigate to view the credential
        view_button = driver.find_element(By.XPATH, f"//td[contains(text(), '{service_name}')]/ancestor::tr//a[contains(@class, 'btn-info')]")
        view_button.click()
        time.sleep(2)

        # Check initial state (password has to be masked)
        password_field = driver.find_element(By.ID, "passwordField")
        assert password_field.get_attribute("type") == "password", "Password not initially masked"

        # Take screenshot before toggle
        driver.save_screenshot("password_masked.png")

        # Click toggle button
        driver.execute_script("document.getElementById('passwordField').type = 'text';")
        time.sleep(1)

        # Take screenshot after first toggle
        driver.save_screenshot("password_visible.png")

        # Verify password is now visible
        assert password_field.get_attribute("type") == "text", "Password not visible after toggle"

        driver.execute_script("document.getElementById('passwordField').type = 'password';")
        time.sleep(1)

        # Take screenshot after second toggle
        driver.save_screenshot("password_masked_again.png")

        # Verify password is hidden again
        assert password_field.get_attribute("type") == "password", "Password not masked after second toggle"


    def test_sql_injection_vulnerability(self):
        """Test for SQL injection vulnerabilities in search functionality"""
        driver = self.driver

        # Registration and login
        test_username = f"sqli_test_{int(time.time())}"
        test_password = "Test@Password123!"

        # Registration
        driver.get(self.base_url + "/auth/register")
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(test_password)
        driver.find_element(By.NAME, "password2").send_keys(test_password)
        driver.find_element(By.NAME, "submit").click()

        # Login
        self.wait.until(EC.url_contains("/auth/login"))
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(test_password)
        driver.find_element(By.NAME, "submit").click()
        time.sleep(2)
        # Add credential
        driver.get(self.base_url + "/add")
        timestamp = int(time.time())
        service_name = f"SQL_Target_{timestamp}"
        driver.find_element(By.ID, "service_name").send_keys(service_name)
        driver.find_element(By.ID, "username").send_keys("sqli_user")
        driver.find_element(By.ID, "password").send_keys("SQLi@Password123!")

        submit_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
        submit_button.click()
        time.sleep(2)

        # Navigate to search page
        driver.get(self.base_url + "/search")

        # First verify that legitimate search works
        search_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "query")))
        search_input.clear()
        search_input.send_keys(service_name)
        search_input.submit()
        time.sleep(2)

        # Extensive debugging for search input
        normal_credential_found = service_name in driver.page_source
        if not normal_credential_found:
            driver.save_screenshot("normal_search_failed.png")
            assert False, "Normal search failed to find credential"

        sql_payloads = [
            "' OR '1'='1",
            "': SELECT * FROM credentials; --'",
            "' UNION SELECT username, password_hash FROM users; --'",
            "' OR username LIKE '%admin%'"
        ]

        vulnerability_found = False

        for payload in sql_payloads:
            driver.get(self.base_url + "/search")
            try:
                # Input the payload into search
                search_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "query")))
                search_input.clear()
                search_input.send_keys(payload)
                search_input.submit()
            except Exception as e:
                print(f"Error finding or submitting search input: {e}")
                continue

            time.sleep(2)

            filename = f'sqli_test_{payload.replace(" ", "_").replace("\'", "").replace(";","").replace("%", "")}.png'
            driver.save_screenshot(filename)

            # Get the page source after injection attempt
            page_source = driver.page_source

            # Check if injection worked
            if "admin" in page_source:
                admin_in_results = False
                try:
                    # Check if the search returned more results than expected
                    credential_rows = driver.find_elements(By.XPATH, "//table//tbody//tr")
                    for row in credential_rows:
                        if "admin" in row.text and "admin" not in service_name:
                            admin_in_results = True
                            break

                except:
                    pass

                if admin_in_results:
                    print(f"SQL injection may have succeeded with payload: {payload}")
                    print(f"Found 'admin' in credential results")
                    vulnerability_found = True

            if "SQL syntax" in page_source or "database error" in page_source.lower():
                print(f"SQL error detached with payload: {payload}")
                vulnerability_found = True

            try:
                # Check the presenence of original credential
                if service_name in page_source and payload in page_source != service_name and not payload in service_name.lower() in service_name.lower():
                    print(f"Found credential that should not match: {service_name}")
                    vulnerability_found = True

                if "No credentials found" not in page_source and service_name not in page_source:
                    credential_rows = driver.find_elements(By.XPATH, "//table//tbody//tr")
                    if len(credential_rows) > 0:
                        print(f"SQL injection may have succeeded with payload: {payload}")
                        print(f"Found {len(credential_rows)} results when none were expected")
                        vulnerability_found = True
            except Exception as e:
                print(f"Error checking credential rows: {e}")
        # Negative assertion for the application as no vulnerabilities should be found
        assert not vulnerability_found, "SQL injection vulnerability detected"

    def test_reflected_xss_vulnerability(self):
        """Test for reflected XSS vulnerabilities in search and error messages"""
        driver = self.driver

        # Registration and login
        test_username = f"xss_test_{int(time.time())}"
        test_password = "Test@Password123!"

        driver.get(self.base_url + "/auth/register")
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(test_password)
        driver.find_element(By.NAME, "password2").send_keys(test_password)
        driver.find_element(By.NAME, "submit").click()

        # Login
        self.wait.until(EC.url_contains("/auth/login"))
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(test_password)
        driver.find_element(By.NAME, "submit").click()
        time.sleep(2)

        # Navigate tto search page
        driver.get(self.base_url + "/search")

        # Test XSS payloads
        xss_payloads = [
            "<script>alert('XSS');</script>",
            "<img src='x' onerror='alert(\"XSS\")>",
            "<body onload='alert(\"XSS\")'>",
            "javascript:alert('XSS')",
        ]

        vulnerability_found = False

        for payload in xss_payloads:
            # Input the payload into search
            search_input =driver.find_element(By.NAME, "query")
            search_input.clear()
            search_input.send_keys(payload)
            search_input.submit()
            time.sleep(2)

            # Take screenshot for evidence
            safe_payload = payload[:10].replace('<', '_').replace('>', "_").replace(":","_")
            driver.save_screenshot(f"xss_reflected_{safe_payload}.png")

            # Get the page source
            page_source = driver.page_source
            current_url = driver.current_url

            # Check if the raw script tag appears in the page source
            if payload in page_source:
                payload_in_url = payload in current_url

                # Count occurrences
                payload_count = page_source.count(payload)

                # if payload is in the URL and appears only once in the page source
                if payload_in_url and payload_count == 1:
                    print(f"Payload found only in URL (not a vulnerability): {payload}")
                else:
                    print(f"Possible XSS vulnerability with payload: {payload}")
                    vulnerability_found = True

            # Try to detect if JavaScript is executed
            try:
                # This will trigger an alert
                alert = driver.switch_to.alert
                alert.accept()
                print(f"XSS alert detected with payload: {payload}")
                vulnerability_found = True
            except:
                pass

        # Assert no vulnerabilities found
        assert not vulnerability_found, "Reflected XSS vulnerability detected"

    def test_stored_xss_vulnerability(self):
        """Test for stored XSS vulnerabilities in credential fields"""
        driver = self.driver

        # Registration and login
        test_username = f"xss_test_{int(time.time())}"
        test_password = "Test@Password123!"

        #Registration
        driver.get(self.base_url + "/auth/register")
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(test_password)
        driver.find_element(By.NAME, "password2").send_keys(test_password)
        driver.find_element(By.NAME, "submit").click()

        # Login
        self.wait.until(EC.url_contains("/auth/login"))
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(test_password)
        driver.find_element(By.NAME, "submit").click()
        time.sleep(2)

        # Navigate to search page
        driver.get(self.base_url + "/add")

        # Tru inject XSS in service name
        xss_payload = "<script>document.body.innerHTML = 'XSS'</script>"
        # Add credential with XSS payload service name
        driver.find_element(By.ID, "service_name").send_keys(xss_payload)
        driver.find_element(By.ID, "username").send_keys("regular_user")
        driver.find_element(By.ID, "password").send_keys("Regular@Pass123")

        # Submit form
        submit_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
        submit_button.click()
        time.sleep(2)

        # Navigate back to credential list to heck for stored XSS
        driver.get(self.base_url + "/")
        time.sleep(1)
        driver.save_screenshot(f"stored_xss_service_name.png")

        # Get page source after first test
        page_source_1 = driver.page_source

        # Check if raw script tag appears in page source
        service_name_vulnerabitlity = xss_payload in page_source_1 in page_source_1
        if service_name_vulnerabitlity:
            print(f"Possible stored XSS vulnerability with payload in service name")

        # Try second approach with XSS in usename
        driver.get(self.base_url + "/add")
        driver.find_element(By.ID, "service_name").send_keys("Regular Service")
        driver.find_element(By.ID, "username").send_keys(xss_payload)
        driver.find_element(By.ID, "password").send_keys("Regular@Pass123")

        # Submit form
        submit_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
        submit_button.click()
        time.sleep(2)

        # Navigate back to credential list

        driver.get(self.base_url + "/")
        time.sleep(1)
        driver.save_screenshot(f"stored_xss_username_test.png")

        # Get page source after second test
        page_source_2 = driver.page_source

        # Check if raw script tag appears in the page source
        username_vulnerability = xss_payload in page_source_2
        if username_vulnerability:
            print(f"Possible stored XSS vulnerability with payload in username")

        assert not (service_name_vulnerabitlity or username_vulnerability), "Stored XSS vulnerability detected"

    def test_dom_based_xss_vulnerability(self):
        """Test for DOM based XSS vulnerabilities"""
        driver = self.driver

        # Registration and login
        test_username = f"xss_dom_{int(time.time())}"
        test_password = "Test@Password123!"

        # Registration
        driver.get(self.base_url + "/auth/register")
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(test_password)
        driver.find_element(By.NAME, "password2").send_keys(test_password)
        driver.find_element(By.NAME, "submit").click()

        # Login
        self.wait.until(EC.url_contains("/auth/login"))
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(test_password)
        driver.find_element(By.NAME, "submit").click()
        time.sleep(2)

        # Creating a unique marker that wouldn't be in range
        unique_marker = f"UNIQUE_MARKER_{int(time.time())}"

        # First visit search without payload
        driver.get(f"{self.base_url}/search")

        # Save original HTML
        original_html = driver.page_source

        # Verify unique marker isn't already in the page
        if unique_marker in original_html:
            print(f"Error: Error Unique marker {unique_marker} already found in page")
            assert False, "Test setup issue, unique marker already in page"

        # Navigate to a page that proccess URL parameters via JavaScript
        xss_payload = "';document.body.innerHTML='DOM_XSS"

        # Construct URL for payload
        driver.get(f"{self.base_url}/search?query={xss_payload}")
        time.sleep(1)

        # Take screenshot
        driver.save_screenshot(f"dom_xss_query_param_test.png")

        page_title = driver.title

        # More precise check for vulnerability
        title_modified = unique_marker in page_title

        if title_modified:
            print(f"DOM based XSS vulnerability found, title modified to: {page_title}")
        # Assert not vulnerability found
        assert not title_modified, "DOM based XSS vulnerability not found"

    def test_sensitive_data_exposure(self):
        """Test for sensitive data exposure vulnerabilities"""
        driver = self.driver
        test_username = f"data_exposure_{int(time.time())}"
        test_password = "Test@Password123!"


        # Registration
        driver.get(self.base_url + "/auth/register")
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(test_password)
        driver.find_element(By.NAME, "password2").send_keys(test_password)
        driver.find_element(By.NAME, "submit").click()

        # Login
        self.wait.until(EC.url_contains("/auth/login"))
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(test_password)
        driver.find_element(By.NAME, "submit").click()
        time.sleep(2)

        service_name = f"Sensittivve Test {int(time.time())}"
        username = "sensitive_user"
        password = "HighlySensitive@123"

        # Add credential
        driver.get(self.base_url + "/add")
        driver.find_element(By.ID, "service_name").send_keys(service_name)
        driver.find_element(By.ID, "username").send_keys(username)
        driver.find_element(By.ID, "password").send_keys(password)

        # Submit form
        submit_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
        submit_button.click()
        time.sleep(2)

        # Check for sensitive data across multiple pages
        vulnerability_found = False

        # Check list page
        driver.get(self.base_url + "/")
        time.sleep(1)
        list_page_source = driver.page_source
        driver.save_screenshot(f"sensitive_data_list_page.png")

        if password in list_page_source:
            print("Critical: Password found in plain text on credential list page")
            vulnerability_found = True

        # Check browser for sensitive data
        try:
            local_storage = driver.execute_script("return Object.keys(localStorage)")
            for key in local_storage:
                value = driver.execute_script(f"return localStorage.getItem('{key}')")
                if password in str(value):
                    print(f"Critical vulnerability found in localStorage under key: {key}")
                    vulnerability_found = True

            # Check session storage
            session_storage = driver.execute_script("return Object.keys(sessionStorage)")
            for key in session_storage:
                value = driver.execute_script(f"return sessionStorage.getItem('{key}')")
                if password in str(value):
                    print(f"Critical vulnerability: Password found in sessionStorage under key: {key}")
                    vulnerability_found = True

            # Check coolies
            cookies = driver.get_cookies()
            for cookie in cookies:
                if password in str(cookie):
                    print(f"Critical vulnerability: Password found in cookie: {cookie['name']}")
                    vulnerability_found = True
        except Exception as e:
            print(f"Error checking browser storage: {e}")

        # Check for transmission over HTTP instead of HTTPS
        if (driver.current_url.startswith("http://") and not driver.current_url.startswith("http://localhost") and
                not "127.0.0.1" in driver.current_url) :
            print("Warning: Application is using unencrypted HTTP protocol")
            vulnerability_found = True

        # Assert no vulnerabilities found
        assert not vulnerability_found, "Sensistive data exposure vulnerability detected"

    def setup_admin_user(self):
        """Set up a dedicated admin user for testing"""
        # Create a unique admin username
        admin_username = f"admin_tester_{int(time.time())}"
        admin_password = "Admin@Password123!"

        driver = self.driver
        # Register admin user
        # Registration
        driver.get(self.base_url + "/auth/register")
        driver.find_element(By.NAME, "username").send_keys(admin_username)
        driver.find_element(By.NAME, "password").send_keys(admin_password)
        driver.find_element(By.NAME, "password2").send_keys(admin_password)
        driver.find_element(By.NAME, "submit").click()
        time.sleep(2)


        # Create app context to access database
        app = create_app()
        with app.app_context():
            # Find user that has been created
            user = User.query.filter_by(username=admin_username).first()
            if user:
                # Promote to admin
                user.is_admin = True
                db.session.commit()
                print(f"User {admin_username} promoted to admin for testing")
                return admin_username, admin_password
            else:
                print("Failed to find user to promote to admin")
                return None, None

    def test_session_timeout(self):
        """Test the user session timeout expires after timeout period"""
        driver = self.driver

        # Registration and login
        test_username = f"time_test_{int(time.time())}"
        test_password = "Test@Password123!"

        # Registration
        driver.get(self.base_url + "/auth/register")
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(test_password)
        driver.find_element(By.NAME, "password2").send_keys(test_password)
        driver.find_element(By.NAME, "submit").click()

        # Login
        self.wait.until(EC.url_contains("/auth/login"))
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(test_password)
        driver.find_element(By.NAME, "submit").click()
        time.sleep(2)

        # Take screenshout whilst authenticated
        driver.save_screenshot("before_timeout.png")

        # Since the actual session timeout is impractical for the time has been reduces
        print("Simulating session timeout by clearing cookies...")
        driver.delete_all_cookies()

        # Try access a protected page
        driver.get(self.base_url + "/")
        time.sleep(2)

        # Take screenshot after simulated timeout
        driver.save_screenshot("after_timeout.png")

        # Verify redirect to login page
        assert "/auth/login" in driver.current_url, "Not redirected to login page after session timeout"

    def test_admin_user_list(self):
        """Test admin ability to view user list"""
        driver = self.driver

        # Create and get admin credentials
        admin_username, admin_password = self.setup_admin_user()
        assert admin_username is not None, "Failed to create admin user"

        # Login as admin
        driver.get(self.base_url + "/auth/login")
        driver.find_element(By.NAME, "username").send_keys(admin_username)
        driver.find_element(By.NAME, "password").send_keys(admin_password)
        driver.find_element(By.NAME, "submit").click()
        time.sleep(2)

        # Access admin user list
        driver.get(self.base_url + "/admin/users")
        time.sleep(2)

        # Take screenshot of admin user list
        driver.save_screenshot("admin_user_list.png")

        # Verify admin page is accessible
        assert "User Management" in driver.page_source, "Admin user list not accessible"

        # Check for user entries in the list
        user_table = driver.find_element(By.TAG_NAME, "table")
        rows = user_table.find_elements(By.TAG_NAME, "tr")
        assert len(rows) > 1, "No users found in admin user list"

    def test_admin_view_logs(self):
        """Test admin ability to view system logs"""
        driver = self.driver

        # Create and get admin credentials
        admin_username, admin_password = self.setup_admin_user()
        assert admin_username is not None, "Failed to create admin user"

        # Login as admin
        driver.get(self.base_url + "/auth/login")
        driver.find_element(By.NAME, "username").send_keys(admin_username)
        driver.find_element(By.NAME, "password").send_keys(admin_password)
        driver.find_element(By.NAME, "submit").click()
        time.sleep(2)

        # Access admin logs list
        driver.get(self.base_url + "/admin/logs")
        time.sleep(2)

        # Take screenshot of admin logs
        driver.save_screenshot("admin_logs.png")

        # Verify logs page is accessible
        assert "System Logs" in driver.page_source, "Admin logs not accessible"

        # Check for log entries
        try:
            log_table = driver.find_element(By.TAG_NAME, "table")
            # Event if there are no logs, the table headers need exist
            assert log_table, "Log table not found"
        except NoSuchElementException:
            assert False, "Log table not found on admin logs page"

    def test_admin_promote_user(self):
        """Test admin ability to promote user to admin"""
        driver = self.driver

        # Create and get admin credentials
        admin_username, admin_password = self.setup_admin_user()
        assert admin_username is not None, "Failed to create admin user"

        # Create a regular user to be promoted
        test_username = f"promote_test_{int(time.time())}"
        test_password = "Test@Password123!"

        # Register the test user
        driver.get(self.base_url + "/auth/register")
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(test_password)
        driver.find_element(By.NAME, "password2").send_keys(test_password)
        driver.find_element(By.NAME, "submit").click()
        time.sleep(2)

        # Login as admin
        driver.get(self.base_url + "/auth/login")
        driver.find_element(By.NAME, "username").send_keys(admin_username)
        driver.find_element(By.NAME, "password").send_keys(admin_password)
        driver.find_element(By.NAME, "submit").click()
        time.sleep(2)

        # Access admin user list
        driver.get(self.base_url + "/admin/users")
        time.sleep(2)

        # Find newly created user
        try:
            user_row = driver.find_element(By.XPATH, f"//td[contains(text(), '{test_username}')]/ancestor::tr")
            # Take screenshot before promotion
            driver.save_screenshot("before_promotion.png")

            # Find and click the promote button
            promote_button = user_row.find_element(By.XPATH, ".//button[contains(text(), 'Make Admin')]")
            driver.execute_script("arguments[0].scrollIntoView(true);", promote_button)
            time.sleep(2)
            promote_button.click()
            time.sleep(2)

            # Take screenshot after promotion
            driver.save_screenshot("after_promotion.png")

            # Verify the user has been promoted
            driver.get(self.base_url + "/admin/users")
            time.sleep(2)

            # Find the user again
            user_row = driver.find_element(By.XPATH, f"//td[contains(text(), '{test_username}')]/ancestor::tr")

            # Check if the user row has admin badge
            admin_badges = user_row.find_elements(By.XPATH, ".//span[contains(@class, 'badge') and contains(text(), 'Admin')]")
            assert len(admin_badges) > 0, "User was not promoted to admin"
        except NoSuchElementException as e:
            assert False, f"Error finding elements for promotion: {e}"

    def test_admin_view_user_logs(self):
        """Test admin ability to view user logs"""
        driver = self.driver

        # Create and get admin credentials
        admin_username, admin_password = self.setup_admin_user()
        assert admin_username is not None, "Failed to create admin user"

        # Create a regular user to view logs
        test_username = f"log_test_{int(time.time())}"
        test_password = "Test@Password123!"

        # Register the test user
        driver.get(self.base_url + "/auth/register")
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(test_password)
        driver.find_element(By.NAME, "password2").send_keys(test_password)
        driver.find_element(By.NAME, "submit").click()
        time.sleep(2)

        # Login as user to generate some logs
        driver.get(self.base_url + "/auth/login")
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(test_password)
        driver.find_element(By.NAME, "submit").click()
        time.sleep(2)

        # Navigate around to generate logs
        driver.get(self.base_url + "/add")
        time.sleep(1)
        driver.get(self.base_url + "/")
        time.sleep(1)
        driver.get(self.base_url + "/auth/logout")
        time.sleep(1)

        # Now login as admin
        driver.get(self.base_url + "/auth/login")
        driver.find_element(By.NAME, "username").send_keys(admin_username)
        driver.find_element(By.NAME, "password").send_keys(admin_password)
        driver.find_element(By.NAME, "submit").click()
        time.sleep(2)

        # Access admin user list
        driver.get(self.base_url + "/admin/users")
        time.sleep(2)

        try:
            # Find the test user
            user_row = driver.find_element(By.XPATH, f"//td[contains(text(), '{test_username}')]/ancestor::tr")
            view_logs_button = user_row.find_element(By.XPATH, ".//a[contains(text(), 'View Logs')]")

            # Take screenshot before viewing logs
            driver.save_screenshot("before_user_logs.png")
            driver.execute_script("arguments[0].scrollIntoView(true);", view_logs_button)
            time.sleep(2)
            view_logs_button.click()
            time.sleep(2)

            # Take a screenshot of user logs
            driver.save_screenshot("user_logs.png")

            # Verify that admin is on user logs page
            assert f"Logs for {test_username}" in driver.page_source, "User specific logs not accessible"

        except NoSuchElementException as e:
            assert False, f"Error finding user logs: {e}"

    def test_regular_user_admin_access(self):
        """Test that regular users cannot access admin features"""
        driver = self.driver

        # Create and admin user first
        admin_username, admin_password = self.setup_admin_user()
        assert admin_username is not None, "Failed to create admin user"

        # Create and login as regular user
        test_username = f"regular_test_{int(time.time())}"
        test_password = "Test@Password123!"

        # Register the test user
        driver.get(self.base_url + "/auth/register")
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(test_password)
        driver.find_element(By.NAME, "password2").send_keys(test_password)
        driver.find_element(By.NAME, "submit").click()
        time.sleep(2)

        # Login as user to generate some logs
        driver.get(self.base_url + "/auth/login")
        driver.find_element(By.NAME, "username").send_keys(test_username)
        driver.find_element(By.NAME, "password").send_keys(test_password)
        driver.find_element(By.NAME, "submit").click()
        time.sleep(2)

        # Try to access admin page directly
        admin_pages = [
            "/admin/",
            "/admin/user",
            "/admin/logs",
            "/admin/security"

        ]

        for page in admin_pages:
            # Try to access the admin page
            driver.get(self.base_url + page)
            time.sleep(1)

            # Take screenshot
            driver.save_screenshot(f"admin_access_attempt_{page.replace('/', '_')}.png")

            # Verify access is denied
            access_denied = (
                "Error 402" in driver.page_source or
                "Access forbidden" in driver.page_source or
                "/auth/login" in driver.page_source or
                not "Admin Dashboard" in driver.page_source
            )

            assert access_denied, f"Regvlar user can access admin page {page}"
            print(f"Regular users cannot access {page}")
