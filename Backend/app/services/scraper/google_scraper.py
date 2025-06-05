"""Google My Business and Google Search scraper."""

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
    RateLimitError,
)


class GoogleScraper(BaseScraper):
    """Scraper for Google My Business and Google Search results."""

    def __init__(self, config: Optional[ScrapingConfig] = None):
        super().__init__(config)
        self.base_url = "https://www.google.com"
        self.maps_url = "https://maps.google.com"

    def get_source(self) -> ScrapingSource:
        return ScrapingSource.GOOGLE_MY_BUSINESS

    def validate_query(self, query: str) -> bool:
        """Validate if the query is suitable for Google scraping."""
        if not query or len(query.strip()) < 2:
            return False

        # Check for prohibited terms
        prohibited_terms = ["illegal", "adult", "gambling"]
        query_lower = query.lower()

        return not any(term in query_lower for term in prohibited_terms)

    async def scrape(self, query: str, location: str = "", **kwargs) -> ScrapingResult:
        """Scrape Google My Business listings."""
        start_time = time.time()
        result = ScrapingResult(source=self.get_source(), status=ScrapingStatus.RUNNING)

        if not self.validate_query(query):
            result.status = ScrapingStatus.FAILED
            result.add_error(f"Invalid query: {query}")
            return result

        try:
            # Try Google Maps first (more business data)
            maps_results = await self._scrape_google_maps(query, location, result)

            # Then try regular Google search for additional results
            search_results = await self._scrape_google_search(query, location, result)

            # Merge and deduplicate results
            self._merge_results(result, maps_results, search_results)

            result.status = ScrapingStatus.COMPLETED
            result.execution_time = time.time() - start_time

        except RateLimitError as e:
            result.status = ScrapingStatus.RATE_LIMITED
            result.add_error(f"Rate limited: {e}")
        except Exception as e:
            result.status = ScrapingStatus.FAILED
            result.add_error(f"Scraping failed: {e}")
            self.logger.exception("Google scraping failed")

        return result

    async def _scrape_google_maps(
        self, query: str, location: str, result: ScrapingResult
    ) -> List[Dict]:
        """Scrape Google Maps for business listings."""
        maps_results = []

        try:
            driver = self._get_driver()

            # Construct search URL
            search_query = f"{query} {location}".strip()
            maps_search_url = f"{self.maps_url}/search/{quote_plus(search_query)}"

            self.logger.info(f"Scraping Google Maps: {maps_search_url}")

            driver.get(maps_search_url)
            await asyncio.sleep(3)  # Wait for page load

            # Wait for results to load
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "[data-result-index]")
                    )
                )
            except TimeoutException:
                result.add_warning("No Google Maps results found")
                return maps_results

            # Scroll to load more results
            await self._scroll_maps_results(driver)

            # Extract business listings
            business_elements = driver.find_elements(
                By.CSS_SELECTOR, "[data-result-index]"
            )

            for element in business_elements[
                : self.config.max_pages * 10
            ]:  # Limit results
                try:
                    business_data = await self._extract_maps_business_data(
                        driver, element
                    )
                    if business_data:
                        maps_results.append(business_data)
                        result.total_pages_scraped += 1

                        # Convert to company object
                        company = self._create_company_from_maps_data(business_data)
                        if company:
                            result.add_company(company)

                        # Extract contacts if available
                        contacts = self._extract_contacts_from_maps_data(business_data)
                        for contact in contacts:
                            result.add_contact(contact)

                    self._wait_between_requests()

                except Exception as e:
                    result.add_warning(f"Failed to extract business data: {e}")
                    continue

        except Exception as e:
            result.add_error(f"Google Maps scraping failed: {e}")
            raise

        return maps_results

    async def _scrape_google_search(
        self, query: str, location: str, result: ScrapingResult
    ) -> List[Dict]:
        """Scrape regular Google search for business information."""
        search_results = []

        try:
            # Construct search query for businesses
            business_query = f'"{query}" {location} contact phone email'
            search_url = f"{self.base_url}/search?q={quote_plus(business_query)}"

            self.logger.info(f"Scraping Google Search: {search_url}")

            response = self._make_request(search_url)
            soup = self._parse_html(response.text, search_url)

            # Extract search results
            search_divs = soup.find_all("div", class_="g")

            for div in search_divs[:20]:  # Limit to first 20 results
                try:
                    search_data = self._extract_search_result_data(div)
                    if search_data:
                        search_results.append(search_data)

                        # Try to extract company information
                        company = self._create_company_from_search_data(search_data)
                        if company:
                            result.add_company(company)

                except Exception as e:
                    result.add_warning(f"Failed to extract search result: {e}")
                    continue

            self._wait_between_requests()

        except Exception as e:
            result.add_error(f"Google Search scraping failed: {e}")

        return search_results

    async def _scroll_maps_results(self, driver) -> None:
        """Scroll through Google Maps results to load more listings."""
        try:
            # Find the scrollable results container
            results_container = driver.find_element(
                By.CSS_SELECTOR, "[role='main'] [role='region']"
            )

            # Scroll down multiple times to load more results
            for _ in range(5):
                driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight",
                    results_container,
                )
                await asyncio.sleep(2)

        except Exception as e:
            self.logger.warning(f"Failed to scroll Maps results: {e}")

    async def _extract_maps_business_data(self, driver, element) -> Optional[Dict]:
        """Extract business data from a Google Maps listing element."""
        try:
            business_data = {}

            # Click on the business to get detailed info
            element.click()
            await asyncio.sleep(2)

            # Extract business name
            try:
                name_element = driver.find_element(By.CSS_SELECTOR, "h1")
                business_data["name"] = name_element.text.strip()
            except NoSuchElementException:
                return None

            # Extract rating and reviews
            try:
                rating_element = driver.find_element(
                    By.CSS_SELECTOR, "[data-value='Rating']"
                )
                business_data["rating"] = rating_element.text.strip()
            except NoSuchElementException:
                business_data["rating"] = None

            # Extract address
            try:
                address_element = driver.find_element(
                    By.CSS_SELECTOR, "[data-item-id='address'] .fontBodyMedium"
                )
                business_data["address"] = address_element.text.strip()
            except NoSuchElementException:
                business_data["address"] = None

            # Extract phone number
            try:
                phone_element = driver.find_element(
                    By.CSS_SELECTOR, "[data-item-id*='phone'] .fontBodyMedium"
                )
                business_data["phone"] = self._clean_phone(phone_element.text)
            except NoSuchElementException:
                business_data["phone"] = None

            # Extract website
            try:
                website_element = driver.find_element(
                    By.CSS_SELECTOR, "[data-item-id='authority'] a"
                )
                business_data["website"] = website_element.get_attribute("href")
            except NoSuchElementException:
                business_data["website"] = None

            # Extract business hours
            try:
                hours_elements = driver.find_elements(
                    By.CSS_SELECTOR, "[data-item-id='oh'] .fontBodyMedium"
                )
                business_data["hours"] = [elem.text.strip() for elem in hours_elements]
            except NoSuchElementException:
                business_data["hours"] = []

            # Extract business type/category
            try:
                category_element = driver.find_element(
                    By.CSS_SELECTOR, ".fontBodyMedium .fontBodyMedium"
                )
                business_data["category"] = category_element.text.strip()
            except NoSuchElementException:
                business_data["category"] = None

            return business_data

        except Exception as e:
            self.logger.warning(f"Failed to extract Maps business data: {e}")
            return None

    def _extract_search_result_data(self, div) -> Optional[Dict]:
        """Extract data from a Google search result."""
        try:
            result_data = {}

            # Extract title and URL
            title_link = div.find("h3")
            if title_link:
                parent_link = title_link.find_parent("a")
                if parent_link:
                    result_data["title"] = title_link.get_text(strip=True)
                    result_data["url"] = parent_link.get("href", "")

            # Extract snippet/description
            snippet_div = div.find("div", class_="VwiC3b")
            if snippet_div:
                result_data["snippet"] = snippet_div.get_text(strip=True)

            # Look for contact information in the snippet
            if "snippet" in result_data:
                snippet_text = result_data["snippet"]

                # Extract phone numbers
                phone_pattern = (
                    r"\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b"
                )
                phones = re.findall(phone_pattern, snippet_text)
                if phones:
                    result_data["phone"] = "".join(phones[0])

                # Extract email addresses
                email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
                emails = re.findall(email_pattern, snippet_text)
                if emails:
                    result_data["email"] = emails[0]

            return result_data if result_data else None

        except Exception as e:
            self.logger.warning(f"Failed to extract search result data: {e}")
            return None

    def _create_company_from_maps_data(self, data: Dict) -> Optional[CompanyCreate]:
        """Create a Company object from Google Maps data."""
        try:
            if not data.get("name"):
                return None

            # Extract domain from website
            domain = ""
            if data.get("website"):
                from urllib.parse import urlparse

                parsed = urlparse(data["website"])
                domain = parsed.netloc.lower().replace("www.", "")

            return CompanyCreate(
                name=data["name"],
                domain=domain,
                website=data.get("website", ""),
                phone=data.get("phone", ""),
                address=data.get("address", ""),
                industry=data.get("category", ""),
                description=f"Rating: {data.get('rating', 'N/A')}",
                source=self.get_source().value,
                source_url=self.maps_url,
            )

        except Exception as e:
            self.logger.warning(f"Failed to create company from Maps data: {e}")
            return None

    def _create_company_from_search_data(self, data: Dict) -> Optional[CompanyCreate]:
        """Create a Company object from Google search data."""
        try:
            if not data.get("title") or not data.get("url"):
                return None

            # Extract domain from URL
            domain = ""
            if data.get("url"):
                from urllib.parse import urlparse

                parsed = urlparse(data["url"])
                domain = parsed.netloc.lower().replace("www.", "")

            return CompanyCreate(
                name=data["title"],
                domain=domain,
                website=data.get("url", ""),
                phone=data.get("phone", ""),
                description=data.get("snippet", ""),
                source=self.get_source().value,
                source_url=data.get("url", ""),
            )

        except Exception as e:
            self.logger.warning(f"Failed to create company from search data: {e}")
            return None

    def _extract_contacts_from_maps_data(self, data: Dict) -> List[ContactCreate]:
        """Extract contact information from Google Maps data."""
        contacts = []

        # For now, we can only extract basic contact info
        # More advanced contact extraction would require additional scraping
        if data.get("phone") or data.get("email"):
            try:
                contact = ContactCreate(
                    first_name="",
                    last_name="",
                    email=data.get("email", ""),
                    phone=data.get("phone", ""),
                    job_title="",
                    source=self.get_source().value,
                )
                contacts.append(contact)
            except Exception as e:
                self.logger.warning(f"Failed to create contact: {e}")

        return contacts

    def _merge_results(
        self,
        result: ScrapingResult,
        maps_results: List[Dict],
        search_results: List[Dict],
    ) -> None:
        """Merge and deduplicate results from different sources."""
        # Store raw data
        result.raw_data = {
            "maps_results": maps_results,
            "search_results": search_results,
        }

        # Deduplicate companies by domain
        seen_domains = set()
        unique_companies = []

        for company in result.companies:
            if company.domain and company.domain not in seen_domains:
                seen_domains.add(company.domain)
                unique_companies.append(company)
            elif not company.domain:  # Keep companies without domains
                unique_companies.append(company)

        result.companies = unique_companies
        result.total_records_found = len(unique_companies)
