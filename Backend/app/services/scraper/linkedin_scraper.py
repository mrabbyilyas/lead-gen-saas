"""LinkedIn scraper for company and contact information."""

import asyncio
import re
import time
from typing import Dict, List, Optional
from urllib.parse import quote_plus

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from app.models.schemas import CompanyCreate, ContactCreate
from .base_scraper import (
    BaseScraper,
    ScrapingResult,
    ScrapingSource,
    ScrapingStatus,
    ScrapingConfig,
    ScrapingError,
    RateLimitError,
    BlockedError,
)


class LinkedInScraper(BaseScraper):
    """Scraper for LinkedIn company and people data."""

    def __init__(self, config: Optional[ScrapingConfig] = None):
        super().__init__(config)
        self.base_url = "https://www.linkedin.com"
        self.is_logged_in = False
        self.login_credentials: Optional[Dict[str, str]] = None

    def get_source(self) -> ScrapingSource:
        return ScrapingSource.LINKEDIN

    def set_login_credentials(self, email: str, password: str) -> None:
        """Set LinkedIn login credentials."""
        self.login_credentials = {"email": email, "password": password}

    def validate_query(self, query: str) -> bool:
        """Validate if the query is suitable for LinkedIn scraping."""
        if not query or len(query.strip()) < 2:
            return False

        # LinkedIn has specific search limitations
        if len(query) > 100:
            return False

        return True

    async def scrape(self, query: str, location: str = "", **kwargs) -> ScrapingResult:
        """Scrape LinkedIn for company and contact information."""
        start_time = time.time()
        result = ScrapingResult(source=self.get_source(), status=ScrapingStatus.RUNNING)

        if not self.validate_query(query):
            result.status = ScrapingStatus.FAILED
            result.add_error(f"Invalid query: {query}")
            return result

        try:
            driver = self._get_driver()

            # Login if credentials are provided
            if self.login_credentials and not self.is_logged_in:
                await self._login(driver, result)

            # Search for companies
            await self._search_companies(driver, query, location, result)

            # Search for people (contacts)
            if self.is_logged_in:  # People search requires login
                await self._search_people(driver, query, location, result)
            else:
                result.add_warning("People search skipped - requires LinkedIn login")

            result.status = ScrapingStatus.COMPLETED
            result.execution_time = time.time() - start_time

        except BlockedError as e:
            result.status = ScrapingStatus.BLOCKED
            result.add_error(f"Blocked by LinkedIn: {e}")
        except RateLimitError as e:
            result.status = ScrapingStatus.RATE_LIMITED
            result.add_error(f"Rate limited: {e}")
        except Exception as e:
            result.status = ScrapingStatus.FAILED
            result.add_error(f"LinkedIn scraping failed: {e}")
            self.logger.exception("LinkedIn scraping failed")

        return result

    async def _login(self, driver, result: ScrapingResult) -> None:
        """Login to LinkedIn."""
        try:
            self.logger.info("Logging into LinkedIn")

            driver.get(f"{self.base_url}/login")
            await asyncio.sleep(3)

            # Check if already logged in
            if "feed" in driver.current_url:
                self.is_logged_in = True
                return

            # Enter email
            email_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_field.clear()
            if not self.login_credentials:
                raise ScrapingError("Login credentials not set")
            
            email_field.send_keys(self.login_credentials["email"])

            # Enter password
            password_field = driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(self.login_credentials["password"])

            # Click login button
            login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()

            await asyncio.sleep(5)

            # Check for CAPTCHA or security challenge
            if "challenge" in driver.current_url or "captcha" in driver.current_url:
                raise BlockedError("LinkedIn security challenge detected")

            # Check if login was successful
            if "feed" in driver.current_url or "in/" in driver.current_url:
                self.is_logged_in = True
                self.logger.info("Successfully logged into LinkedIn")
            else:
                raise ScrapingError("LinkedIn login failed")

        except Exception as e:
            result.add_error(f"LinkedIn login failed: {e}")
            raise

    async def _search_companies(
        self, driver, query: str, location: str, result: ScrapingResult
    ) -> List[Dict]:
        """Search for companies on LinkedIn."""
        companies: List[Dict] = []

        try:
            # Construct company search URL
            search_query = f"{query} {location}".strip()
            search_url = f"{self.base_url}/search/results/companies/?keywords={quote_plus(search_query)}"

            self.logger.info(f"Searching LinkedIn companies: {search_url}")

            driver.get(search_url)
            await asyncio.sleep(3)

            # Check if we're blocked
            if "authwall" in driver.current_url or "login" in driver.current_url:
                result.add_warning("LinkedIn company search requires login")
                return companies

            # Wait for search results
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, ".search-result__wrapper")
                    )
                )
            except TimeoutException:
                result.add_warning("No LinkedIn company results found")
                return companies

            # Scroll to load more results
            await self._scroll_search_results(driver)

            # Extract company results
            company_elements = driver.find_elements(
                By.CSS_SELECTOR, ".search-result__wrapper"
            )

            for element in company_elements[: self.config.max_pages * 10]:
                try:
                    company_data = await self._extract_company_data(driver, element)
                    if company_data:
                        companies.append(company_data)

                        # Convert to company object
                        company = self._create_company_from_linkedin_data(company_data)
                        if company:
                            result.add_company(company)

                        result.total_pages_scraped += 1

                    self._wait_between_requests()

                except Exception as e:
                    result.add_warning(f"Failed to extract company data: {e}")
                    continue

        except Exception as e:
            result.add_error(f"LinkedIn company search failed: {e}")

        return companies

    async def _search_people(
        self, driver, query: str, location: str, result: ScrapingResult
    ) -> List[Dict]:
        """Search for people on LinkedIn."""
        contacts: List[Dict] = []

        try:
            # Construct people search URL
            search_query = f"{query} {location}".strip()
            search_url = f"{self.base_url}/search/results/people/?keywords={quote_plus(search_query)}"

            self.logger.info(f"Searching LinkedIn people: {search_url}")

            driver.get(search_url)
            await asyncio.sleep(3)

            # Wait for search results
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, ".search-result__wrapper")
                    )
                )
            except TimeoutException:
                result.add_warning("No LinkedIn people results found")
                return contacts

            # Scroll to load more results
            await self._scroll_search_results(driver)

            # Extract people results
            people_elements = driver.find_elements(
                By.CSS_SELECTOR, ".search-result__wrapper"
            )

            for element in people_elements[: self.config.max_pages * 10]:
                try:
                    contact_data = await self._extract_contact_data(driver, element)
                    if contact_data:
                        contacts.append(contact_data)

                        # Convert to contact object
                        contact = self._create_contact_from_linkedin_data(contact_data)
                        if contact:
                            result.add_contact(contact)

                    self._wait_between_requests()

                except Exception as e:
                    result.add_warning(f"Failed to extract contact data: {e}")
                    continue

        except Exception as e:
            result.add_error(f"LinkedIn people search failed: {e}")

        return contacts

    async def _scroll_search_results(self, driver) -> None:
        """Scroll through LinkedIn search results to load more."""
        try:
            # Scroll down multiple times to load more results
            for _ in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                await asyncio.sleep(2)

                # Check if "Show more results" button exists and click it
                try:
                    show_more_button = driver.find_element(
                        By.CSS_SELECTOR, ".artdeco-pagination__button--next"
                    )
                    if show_more_button.is_enabled():
                        show_more_button.click()
                        await asyncio.sleep(3)
                except NoSuchElementException:
                    break

        except Exception as e:
            self.logger.warning(f"Failed to scroll LinkedIn results: {e}")

    async def _extract_company_data(self, driver, element) -> Optional[Dict]:
        """Extract company data from a LinkedIn search result element."""
        try:
            company_data = {}

            # Extract company name
            try:
                name_element = element.find_element(
                    By.CSS_SELECTOR, ".search-result__result-link"
                )
                company_data["name"] = name_element.text.strip()
                company_data["linkedin_url"] = name_element.get_attribute("href")
            except NoSuchElementException:
                return None

            # Extract company description/tagline
            try:
                desc_element = element.find_element(
                    By.CSS_SELECTOR, ".search-result__snippets"
                )
                company_data["description"] = desc_element.text.strip()
            except NoSuchElementException:
                company_data["description"] = ""

            # Extract industry
            try:
                industry_element = element.find_element(
                    By.CSS_SELECTOR,
                    ".search-result__snippets .search-result__snippet-text",
                )
                company_data["industry"] = industry_element.text.strip()
            except NoSuchElementException:
                company_data["industry"] = ""

            # Extract location
            try:
                location_element = element.find_element(
                    By.CSS_SELECTOR, ".subline-level-1"
                )
                company_data["location"] = location_element.text.strip()
            except NoSuchElementException:
                company_data["location"] = ""

            # Extract follower count
            try:
                followers_element = element.find_element(
                    By.CSS_SELECTOR, ".subline-level-2"
                )
                company_data["followers"] = followers_element.text.strip()
            except NoSuchElementException:
                company_data["followers"] = ""

            return company_data

        except Exception as e:
            self.logger.warning(f"Failed to extract LinkedIn company data: {e}")
            return None

    async def _extract_contact_data(self, driver, element) -> Optional[Dict]:
        """Extract contact data from a LinkedIn people search result."""
        try:
            contact_data = {}

            # Extract name
            try:
                name_element = element.find_element(
                    By.CSS_SELECTOR, ".search-result__result-link"
                )
                full_name = name_element.text.strip()
                contact_data["full_name"] = full_name
                contact_data["linkedin_url"] = name_element.get_attribute("href")

                # Split name into first and last
                name_parts = full_name.split()
                if len(name_parts) >= 2:
                    contact_data["first_name"] = name_parts[0]
                    contact_data["last_name"] = " ".join(name_parts[1:])
                else:
                    contact_data["first_name"] = full_name
                    contact_data["last_name"] = ""

            except NoSuchElementException:
                return None

            # Extract job title
            try:
                title_element = element.find_element(
                    By.CSS_SELECTOR, ".subline-level-1"
                )
                contact_data["job_title"] = title_element.text.strip()
            except NoSuchElementException:
                contact_data["job_title"] = ""

            # Extract company
            try:
                company_element = element.find_element(
                    By.CSS_SELECTOR, ".subline-level-2"
                )
                contact_data["company"] = company_element.text.strip()
            except NoSuchElementException:
                contact_data["company"] = ""

            # Extract location
            try:
                location_element = element.find_element(
                    By.CSS_SELECTOR, ".subline-level-3"
                )
                contact_data["location"] = location_element.text.strip()
            except NoSuchElementException:
                contact_data["location"] = ""

            return contact_data

        except Exception as e:
            self.logger.warning(f"Failed to extract LinkedIn contact data: {e}")
            return None

    def _create_company_from_linkedin_data(self, data: Dict) -> Optional[CompanyCreate]:
        """Create a Company object from LinkedIn data."""
        try:
            if not data.get("name"):
                return None

            # Extract LinkedIn company ID from URL
            if data.get("linkedin_url"):
                match = re.search(r"/company/([^/?]+)", data["linkedin_url"])
                if match:
                    match.group(1)

            return CompanyCreate(
                name=data["name"],
                domain="",  # LinkedIn doesn't provide direct domain info
                website=None,
                industry=data.get("industry", ""),
                company_size=None,
                founded_year=None,
                revenue_range=None,
                employee_count=None,
                data_quality_score=None,
                lead_score=None,
                description=data.get("description", ""),
                address=data.get("location", ""),
                linkedin_url=data.get("linkedin_url", ""),
                source=self.get_source().value,
                source_url=data.get("linkedin_url", ""),
            )

        except Exception as e:
            self.logger.warning(f"Failed to create company from LinkedIn data: {e}")
            return None

    def _create_contact_from_linkedin_data(self, data: Dict) -> Optional[ContactCreate]:
        """Create a Contact object from LinkedIn data."""
        try:
            if not data.get("full_name"):
                return None

            return ContactCreate(
                first_name=data.get("first_name", ""),
                last_name=data.get("last_name", ""),
                full_name=data.get("full_name", ""),
                email="",  # LinkedIn doesn't provide email in search results
                phone="",  # LinkedIn doesn't provide phone in search results
                job_title=data.get("job_title", ""),
                department=None,
                seniority_level=None,
                linkedin_url=data.get("linkedin_url", ""),
                twitter_handle=None,
                company=data.get("company", ""),
                source=self.get_source().value,
                experience_years=None,
                contact_quality_score=None,
                engagement_potential=None,
            )

        except Exception as e:
            self.logger.warning(f"Failed to create contact from LinkedIn data: {e}")
            return None

    async def scrape_company_details(self, company_url: str) -> Optional[Dict]:
        """Scrape detailed information from a LinkedIn company page."""
        if not self.is_logged_in:
            self.logger.warning("Company details scraping requires LinkedIn login")
            return None

        try:
            driver = self._get_driver()
            driver.get(company_url)
            await asyncio.sleep(3)

            company_details = {}

            # Extract company size
            try:
                size_element = driver.find_element(
                    By.CSS_SELECTOR, "[data-test-id='about-us-company-size'] dd"
                )
                company_details["company_size"] = size_element.text.strip()
            except NoSuchElementException:
                pass

            # Extract headquarters
            try:
                hq_element = driver.find_element(
                    By.CSS_SELECTOR, "[data-test-id='about-us-headquarters'] dd"
                )
                company_details["headquarters"] = hq_element.text.strip()
            except NoSuchElementException:
                pass

            # Extract founded year
            try:
                founded_element = driver.find_element(
                    By.CSS_SELECTOR, "[data-test-id='about-us-founded'] dd"
                )
                company_details["founded"] = founded_element.text.strip()
            except NoSuchElementException:
                pass

            # Extract website
            try:
                website_element = driver.find_element(
                    By.CSS_SELECTOR, "[data-test-id='about-us-website'] a"
                )
                href = website_element.get_attribute("href")
                if href:
                    company_details["website"] = href
            except NoSuchElementException:
                pass

            return company_details

        except Exception as e:
            self.logger.warning(f"Failed to scrape company details: {e}")
            return None

    def _detect_blocking(self, driver) -> bool:
        """Detect if we're being blocked by LinkedIn."""
        current_url = driver.current_url.lower()
        page_source = driver.page_source.lower()

        blocking_indicators = [
            "authwall" in current_url,
            "challenge" in current_url,
            "captcha" in current_url,
            "blocked" in page_source,
            "unusual activity" in page_source,
            "verify" in page_source and "human" in page_source,
        ]

        return any(blocking_indicators)
