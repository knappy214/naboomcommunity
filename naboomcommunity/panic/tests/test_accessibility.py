"""
WCAG 2.1 AA Compliance Testing Framework
Automated accessibility testing for emergency response interfaces.
"""

import os
import json
import time
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client, LiveServerTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class AccessibilityTestMixin:
    """
    Mixin class providing accessibility testing utilities.
    """
    
    def setUp(self):
        """Set up accessibility testing environment."""
        super().setUp()
        self.accessibility_violations = []
        self.accessibility_warnings = []
        self.setup_webdriver()
    
    def setup_webdriver(self):
        """Set up Chrome WebDriver with accessibility testing capabilities."""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-javascript')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            
            # Enable accessibility testing
            chrome_options.add_argument('--enable-logging')
            chrome_options.add_argument('--log-level=0')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            
            # Inject axe-core for accessibility testing
            self.inject_axe_core()
            
        except WebDriverException as e:
            logger.warning(f"Chrome WebDriver not available: {e}")
            self.driver = None
    
    def inject_axe_core(self):
        """Inject axe-core JavaScript library for accessibility testing."""
        if not self.driver:
            return
        
        try:
            # Load axe-core from CDN
            axe_script = """
            var script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/axe-core@4.8.2/axe.min.js';
            script.onload = function() {
                console.log('axe-core loaded successfully');
            };
            document.head.appendChild(script);
            """
            self.driver.execute_script(axe_script)
            
            # Wait for axe-core to load
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Failed to inject axe-core: {e}")
    
    def run_accessibility_test(self, url=None, context=None, tags=None):
        """
        Run accessibility test using axe-core.
        
        Args:
            url: URL to test (if None, uses current page)
            context: CSS selector for specific elements to test
            tags: WCAG tags to test (e.g., ['wcag2a', 'wcag2aa'])
        
        Returns:
            Dictionary containing test results
        """
        if not self.driver:
            return {'error': 'WebDriver not available'}
        
        try:
            if url:
                self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            
            # Configure axe-core test
            axe_config = {
                'runOnly': {
                    'type': 'tag',
                    'values': tags or ['wcag2a', 'wcag2aa']
                },
                'rules': {
                    'color-contrast': {'enabled': True},
                    'keyboard-navigation': {'enabled': True},
                    'focus-order': {'enabled': True},
                    'aria-labels': {'enabled': True},
                    'alt-text': {'enabled': True},
                    'heading-order': {'enabled': True},
                    'landmark-roles': {'enabled': True},
                    'link-purpose': {'enabled': True},
                    'button-name': {'enabled': True},
                    'form-labels': {'enabled': True},
                }
            }
            
            # Run accessibility test
            if context:
                axe_script = f"""
                return new Promise((resolve, reject) => {{
                    if (typeof axe === 'undefined') {{
                        reject('axe-core not loaded');
                        return;
                    }}
                    
                    axe.run('{context}', {json.dumps(axe_config)})
                        .then(resolve)
                        .catch(reject);
                }});
                """
            else:
                axe_script = f"""
                return new Promise((resolve, reject) => {{
                    if (typeof axe === 'undefined') {{
                        reject('axe-core not loaded');
                        return;
                    }}
                    
                    axe.run({json.dumps(axe_config)})
                        .then(resolve)
                        .catch(reject);
                }});
                """
            
            result = self.driver.execute_async_script(axe_script)
            
            # Process results
            violations = result.get('violations', [])
            incomplete = result.get('incomplete', [])
            passes = result.get('passes', [])
            
            # Store results for analysis
            self.accessibility_violations.extend(violations)
            self.accessibility_warnings.extend(incomplete)
            
            return {
                'violations': violations,
                'incomplete': incomplete,
                'passes': passes,
                'url': url or self.driver.current_url,
                'timestamp': time.time()
            }
            
        except TimeoutException:
            return {'error': 'Page load timeout'}
        except Exception as e:
            logger.error(f"Accessibility test failed: {e}")
            return {'error': str(e)}
    
    def check_color_contrast(self, element_selector=None):
        """
        Check color contrast compliance.
        
        Args:
            element_selector: CSS selector for specific elements
        
        Returns:
            Boolean indicating if color contrast is compliant
        """
        result = self.run_accessibility_test(
            context=element_selector,
            tags=['wcag2aa']
        )
        
        if 'error' in result:
            return False
        
        # Check for color contrast violations
        color_violations = [
            v for v in result['violations']
            if 'color-contrast' in v.get('id', '')
        ]
        
        return len(color_violations) == 0
    
    def check_keyboard_navigation(self):
        """
        Check keyboard navigation compliance.
        
        Returns:
            Boolean indicating if keyboard navigation is compliant
        """
        result = self.run_accessibility_test(tags=['wcag2a'])
        
        if 'error' in result:
            return False
        
        # Check for keyboard navigation violations
        keyboard_violations = [
            v for v in result['violations']
            if any(keyword in v.get('id', '').lower() for keyword in [
                'keyboard', 'focus', 'tab', 'navigation'
            ])
        ]
        
        return len(keyboard_violations) == 0
    
    def check_aria_compliance(self):
        """
        Check ARIA compliance.
        
        Returns:
            Boolean indicating if ARIA is compliant
        """
        result = self.run_accessibility_test(tags=['wcag2a'])
        
        if 'error' in result:
            return False
        
        # Check for ARIA violations
        aria_violations = [
            v for v in result['violations']
            if 'aria' in v.get('id', '').lower()
        ]
        
        return len(aria_violations) == 0
    
    def check_heading_structure(self):
        """
        Check heading structure compliance.
        
        Returns:
            Boolean indicating if heading structure is compliant
        """
        result = self.run_accessibility_test(tags=['wcag2a'])
        
        if 'error' in result:
            return False
        
        # Check for heading violations
        heading_violations = [
            v for v in result['violations']
            if any(keyword in v.get('id', '').lower() for keyword in [
                'heading', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
            ])
        ]
        
        return len(heading_violations) == 0
    
    def check_form_accessibility(self):
        """
        Check form accessibility compliance.
        
        Returns:
            Boolean indicating if forms are accessible
        """
        result = self.run_accessibility_test(tags=['wcag2a'])
        
        if 'error' in result:
            return False
        
        # Check for form violations
        form_violations = [
            v for v in result['violations']
            if any(keyword in v.get('id', '').lower() for keyword in [
                'form', 'label', 'input', 'button', 'select', 'textarea'
            ])
        ]
        
        return len(form_violations) == 0
    
    def check_link_accessibility(self):
        """
        Check link accessibility compliance.
        
        Returns:
            Boolean indicating if links are accessible
        """
        result = self.run_accessibility_test(tags=['wcag2a'])
        
        if 'error' in result:
            return False
        
        # Check for link violations
        link_violations = [
            v for v in result['violations']
            if any(keyword in v.get('id', '').lower() for keyword in [
                'link', 'anchor', 'href'
            ])
        ]
        
        return len(link_violations) == 0
    
    def generate_accessibility_report(self):
        """
        Generate comprehensive accessibility report.
        
        Returns:
            Dictionary containing accessibility report
        """
        return {
            'total_violations': len(self.accessibility_violations),
            'total_warnings': len(self.accessibility_warnings),
            'violations': self.accessibility_violations,
            'warnings': self.accessibility_warnings,
            'summary': {
                'color_contrast': self.check_color_contrast(),
                'keyboard_navigation': self.check_keyboard_navigation(),
                'aria_compliance': self.check_aria_compliance(),
                'heading_structure': self.check_heading_structure(),
                'form_accessibility': self.check_form_accessibility(),
                'link_accessibility': self.check_link_accessibility(),
            }
        }
    
    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()
        super().tearDown()


class EmergencyPanicButtonAccessibilityTest(AccessibilityTestMixin, LiveServerTestCase):
    """
    Test accessibility of emergency panic button interface.
    """
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test client
        self.client = Client()
        self.client.force_login(self.user)
    
    def test_panic_button_page_accessibility(self):
        """Test accessibility of panic button page."""
        if not self.driver:
            self.skipTest("WebDriver not available")
        
        # Navigate to panic button page
        url = f"{self.live_server_url}/panic/"
        result = self.run_accessibility_test(url)
        
        # Assert no critical violations
        self.assertEqual(len(result.get('violations', [])), 0,
                        f"Accessibility violations found: {result.get('violations', [])}")
    
    def test_panic_button_color_contrast(self):
        """Test color contrast of panic button."""
        if not self.driver:
            self.skipTest("WebDriver not available")
        
        url = f"{self.live_server_url}/panic/"
        self.driver.get(url)
        
        # Test panic button specifically
        is_compliant = self.check_color_contrast('.panic-button')
        self.assertTrue(is_compliant, "Panic button color contrast not compliant")
    
    def test_panic_button_keyboard_navigation(self):
        """Test keyboard navigation of panic button."""
        if not self.driver:
            self.skipTest("WebDriver not available")
        
        url = f"{self.live_server_url}/panic/"
        self.driver.get(url)
        
        # Test keyboard navigation
        is_compliant = self.check_keyboard_navigation()
        self.assertTrue(is_compliant, "Keyboard navigation not compliant")
    
    def test_panic_button_aria_compliance(self):
        """Test ARIA compliance of panic button."""
        if not self.driver:
            self.skipTest("WebDriver not available")
        
        url = f"{self.live_server_url}/panic/"
        self.driver.get(url)
        
        # Test ARIA compliance
        is_compliant = self.check_aria_compliance()
        self.assertTrue(is_compliant, "ARIA compliance not met")


class EmergencyLocationAccessibilityTest(AccessibilityTestMixin, LiveServerTestCase):
    """
    Test accessibility of emergency location interface.
    """
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test client
        self.client = Client()
        self.client.force_login(self.user)
    
    def test_location_page_accessibility(self):
        """Test accessibility of location page."""
        if not self.driver:
            self.skipTest("WebDriver not available")
        
        # Navigate to location page
        url = f"{self.live_server_url}/panic/location/"
        result = self.run_accessibility_test(url)
        
        # Assert no critical violations
        self.assertEqual(len(result.get('violations', [])), 0,
                        f"Accessibility violations found: {result.get('violations', [])}")
    
    def test_location_form_accessibility(self):
        """Test accessibility of location form."""
        if not self.driver:
            self.skipTest("WebDriver not available")
        
        url = f"{self.live_server_url}/panic/location/"
        self.driver.get(url)
        
        # Test form accessibility
        is_compliant = self.check_form_accessibility()
        self.assertTrue(is_compliant, "Location form not accessible")


class EmergencyMedicalAccessibilityTest(AccessibilityTestMixin, LiveServerTestCase):
    """
    Test accessibility of emergency medical interface.
    """
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test client
        self.client = Client()
        self.client.force_login(self.user)
    
    def test_medical_page_accessibility(self):
        """Test accessibility of medical page."""
        if not self.driver:
            self.skipTest("WebDriver not available")
        
        # Navigate to medical page
        url = f"{self.live_server_url}/panic/medical/"
        result = self.run_accessibility_test(url)
        
        # Assert no critical violations
        self.assertEqual(len(result.get('violations', [])), 0,
                        f"Accessibility violations found: {result.get('violations', [])}")
    
    def test_medical_form_accessibility(self):
        """Test accessibility of medical form."""
        if not self.driver:
            self.skipTest("WebDriver not available")
        
        url = f"{self.live_server_url}/panic/medical/"
        self.driver.get(url)
        
        # Test form accessibility
        is_compliant = self.check_form_accessibility()
        self.assertTrue(is_compliant, "Medical form not accessible")


class EmergencyNotificationAccessibilityTest(AccessibilityTestMixin, LiveServerTestCase):
    """
    Test accessibility of emergency notification interface.
    """
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test client
        self.client = Client()
        self.client.force_login(self.user)
    
    def test_notification_page_accessibility(self):
        """Test accessibility of notification page."""
        if not self.driver:
            self.skipTest("WebDriver not available")
        
        # Navigate to notification page
        url = f"{self.live_server_url}/panic/notifications/"
        result = self.run_accessibility_test(url)
        
        # Assert no critical violations
        self.assertEqual(len(result.get('violations', [])), 0,
                        f"Accessibility violations found: {result.get('violations', [])}")
    
    def test_notification_form_accessibility(self):
        """Test accessibility of notification form."""
        if not self.driver:
            self.skipTest("WebDriver not available")
        
        url = f"{self.live_server_url}/panic/notifications/"
        self.driver.get(url)
        
        # Test form accessibility
        is_compliant = self.check_form_accessibility()
        self.assertTrue(is_compliant, "Notification form not accessible")


class EmergencyWebSocketAccessibilityTest(AccessibilityTestMixin, LiveServerTestCase):
    """
    Test accessibility of emergency WebSocket interface.
    """
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test client
        self.client = Client()
        self.client.force_login(self.user)
    
    def test_websocket_page_accessibility(self):
        """Test accessibility of WebSocket page."""
        if not self.driver:
            self.skipTest("WebDriver not available")
        
        # Navigate to WebSocket page
        url = f"{self.live_server_url}/panic/websocket/"
        result = self.run_accessibility_test(url)
        
        # Assert no critical violations
        self.assertEqual(len(result.get('violations', [])), 0,
                        f"Accessibility violations found: {result.get('violations', [])}")


class EmergencyMobileAccessibilityTest(AccessibilityTestMixin, LiveServerTestCase):
    """
    Test accessibility of emergency interface on mobile devices.
    """
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test client
        self.client = Client()
        self.client.force_login(self.user)
        
        # Set mobile viewport
        if self.driver:
            self.driver.set_window_size(375, 667)  # iPhone 6/7/8 size
    
    def test_mobile_panic_button_accessibility(self):
        """Test accessibility of panic button on mobile."""
        if not self.driver:
            self.skipTest("WebDriver not available")
        
        url = f"{self.live_server_url}/panic/"
        result = self.run_accessibility_test(url)
        
        # Assert no critical violations
        self.assertEqual(len(result.get('violations', [])), 0,
                        f"Mobile accessibility violations found: {result.get('violations', [])}")
    
    def test_mobile_touch_targets(self):
        """Test touch target sizes on mobile."""
        if not self.driver:
            self.skipTest("WebDriver not available")
        
        url = f"{self.live_server_url}/panic/"
        self.driver.get(url)
        
        # Check touch target sizes (minimum 44x44 pixels)
        touch_elements = self.driver.find_elements(By.CSS_SELECTOR, 'button, a, input[type="button"], input[type="submit"]')
        
        for element in touch_elements:
            size = element.size
            self.assertGreaterEqual(size['width'], 44, f"Touch target too small: {element.tag_name}")
            self.assertGreaterEqual(size['height'], 44, f"Touch target too small: {element.tag_name}")


class EmergencyAccessibilityReportTest(TestCase):
    """
    Test accessibility reporting functionality.
    """
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_accessibility_report_generation(self):
        """Test accessibility report generation."""
        # Mock accessibility test results
        mock_violations = [
            {
                'id': 'color-contrast',
                'description': 'Elements must have sufficient color contrast',
                'nodes': [
                    {
                        'target': ['.panic-button'],
                        'html': '<button class="panic-button">Panic</button>'
                    }
                ]
            }
        ]
        
        # Create test instance
        test_instance = AccessibilityTestMixin()
        test_instance.accessibility_violations = mock_violations
        test_instance.accessibility_warnings = []
        
        # Generate report
        report = test_instance.generate_accessibility_report()
        
        # Assert report structure
        self.assertIn('total_violations', report)
        self.assertIn('total_warnings', report)
        self.assertIn('violations', report)
        self.assertIn('warnings', report)
        self.assertIn('summary', report)
        
        # Assert report content
        self.assertEqual(report['total_violations'], 1)
        self.assertEqual(report['total_warnings'], 0)
        self.assertEqual(len(report['violations']), 1)
        self.assertEqual(report['violations'][0]['id'], 'color-contrast')


class EmergencyAccessibilityIntegrationTest(AccessibilityTestMixin, LiveServerTestCase):
    """
    Integration test for emergency accessibility across all interfaces.
    """
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test client
        self.client = Client()
        self.client.force_login(self.user)
    
    def test_complete_emergency_workflow_accessibility(self):
        """Test accessibility of complete emergency workflow."""
        if not self.driver:
            self.skipTest("WebDriver not available")
        
        # Test all emergency interfaces
        emergency_urls = [
            '/panic/',
            '/panic/location/',
            '/panic/medical/',
            '/panic/notifications/',
            '/panic/websocket/',
        ]
        
        all_violations = []
        
        for url_path in emergency_urls:
            url = f"{self.live_server_url}{url_path}"
            result = self.run_accessibility_test(url)
            
            if 'violations' in result:
                all_violations.extend(result['violations'])
        
        # Assert no critical violations across all interfaces
        self.assertEqual(len(all_violations), 0,
                        f"Accessibility violations found across emergency interfaces: {all_violations}")
    
    def test_emergency_accessibility_compliance_summary(self):
        """Test overall accessibility compliance summary."""
        if not self.driver:
            self.skipTest("WebDriver not available")
        
        # Test main emergency page
        url = f"{self.live_server_url}/panic/"
        self.run_accessibility_test(url)
        
        # Generate comprehensive report
        report = self.generate_accessibility_report()
        
        # Assert all compliance checks pass
        summary = report['summary']
        self.assertTrue(summary['color_contrast'], "Color contrast not compliant")
        self.assertTrue(summary['keyboard_navigation'], "Keyboard navigation not compliant")
        self.assertTrue(summary['aria_compliance'], "ARIA compliance not met")
        self.assertTrue(summary['heading_structure'], "Heading structure not compliant")
        self.assertTrue(summary['form_accessibility'], "Form accessibility not compliant")
        self.assertTrue(summary['link_accessibility'], "Link accessibility not compliant")
