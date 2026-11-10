from django.test import SimpleTestCase
from django.urls import reverse


class LandingPageTests(SimpleTestCase):
    def test_home_page_renders_product_name_and_registration_action(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "InternTrack")
        self.assertContains(response, "Get started")
