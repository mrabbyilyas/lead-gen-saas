"""General website scraper for extracting company and contact information."""

import re
import time
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag
from pydantic import HttpUrl

from app.models.schemas import CompanyCreate, ContactCreate
from .base_scraper import (
    BaseScraper,
    ScrapingResult,
    ScrapingSource,
    ScrapingStatus,
    ScrapingConfig,
    RateLimitError,
)


class WebsiteScraper(BaseScraper):
    """General website scraper for extracting business information."""

    def __init__(self, config: Optional[ScrapingConfig] = None):
        super().__init__(config)
        self.visited_urls: set[str] = set()
        self.contact_patterns = self._compile_contact_patterns()

    def get_source(self) -> ScrapingSource:
        return ScrapingSource.WEBSITE

    def _compile_contact_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for extracting contact information."""
        return {
            "email": re.compile(
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", re.IGNORECASE
            ),
            "phone": re.compile(
                r"\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b"
            ),
            "address": re.compile(
                r"\d+\s+[A-Za-z0-9\s,.-]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct)\s*,?\s*[A-Za-z\s]+,?\s*[A-Z]{2}\s*\d{5}",
                re.IGNORECASE,
            ),
            "social_media": re.compile(
                r"(?:https?://)?(?:www\.)?(facebook|twitter|linkedin|instagram|youtube)\.com/[A-Za-z0-9._-]+",
                re.IGNORECASE,
            ),
        }

    def validate_query(self, query: str) -> bool:
        """Validate if the query is a valid URL or domain."""
        if not query:
            return False

        # Check if it's a valid URL or domain
        if query.startswith(("http://", "https://")):
            try:
                parsed = urlparse(query)
                return bool(parsed.netloc)
            except Exception:
                return False
        else:
            # Assume it's a domain
            domain_pattern = re.compile(
                r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+"
                r"[a-zA-Z]{2,}$"
            )
            return bool(domain_pattern.match(query))

    async def scrape(self, query: str, **kwargs) -> ScrapingResult:
        """Scrape a website for company and contact information."""
        start_time = time.time()
        result = ScrapingResult(source=self.get_source(), status=ScrapingStatus.RUNNING)

        if not self.validate_query(query):
            result.status = ScrapingStatus.FAILED
            result.add_error(f"Invalid URL or domain: {query}")
            return result

        try:
            # Normalize URL
            base_url = self._normalize_url(query)

            # Check robots.txt
            if not self._can_fetch(base_url):
                result.status = ScrapingStatus.FAILED
                result.add_error(f"Robots.txt disallows scraping: {base_url}")
                return result

            # Scrape main page
            await self._scrape_page(base_url, result)

            # Find and scrape additional relevant pages
            additional_pages = await self._find_relevant_pages(base_url, result)

            for page_url in additional_pages[: self.config.max_pages]:
                if page_url not in self.visited_urls:
                    await self._scrape_page(page_url, result)
                    self._wait_between_requests()

            # Create company object from collected data
            company = self._create_company_from_website_data(base_url, result)
            if company:
                result.add_company(company)

            result.status = ScrapingStatus.COMPLETED
            result.execution_time = time.time() - start_time

        except RateLimitError as e:
            result.status = ScrapingStatus.RATE_LIMITED
            result.add_error(f"Rate limited: {e}")
        except Exception as e:
            result.status = ScrapingStatus.FAILED
            result.add_error(f"Website scraping failed: {e}")
            self.logger.exception("Website scraping failed")

        return result

    def _normalize_url(self, url: str) -> str:
        """Normalize URL to ensure it has proper protocol."""
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        return url

    def _can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched based on robots.txt"""
        try:
            from urllib.robotparser import RobotFileParser
            rp = RobotFileParser()
            robots_url = f"{url.rstrip('/')}/robots.txt"
            rp.set_url(robots_url)
            rp.read()
            return rp.can_fetch("*", url)
        except Exception:
            return True  # Default to allowing if check fails

    async def _scrape_page(self, url: str, result: ScrapingResult) -> Dict:
        """Scrape a single page for information."""
        if url in self.visited_urls:
            return {}

        self.visited_urls.add(url)
        page_data = {}

        try:
            self.logger.info(f"Scraping page: {url}")

            response = self._make_request(url)
            soup = self._parse_html(response.text, url)

            # Extract basic page information
            page_data["url"] = url
            page_data["title"] = self._extract_title(soup)
            page_data["description"] = self._extract_description(soup)

            # Extract contact information
            contacts = self._extract_contacts_from_page(soup, url)
            for contact in contacts:
                result.add_contact(contact)

            # Extract company information
            company_info = self._extract_company_info_from_page(soup, url)
            page_data.update(company_info)

            # Store raw data
            if not hasattr(result, "raw_data") or not result.raw_data:
                result.raw_data = {"pages": []}
            result.raw_data["pages"].append(page_data)

            result.total_pages_scraped += 1

        except Exception as e:
            result.add_warning(f"Failed to scrape page {url}: {e}")

        return page_data

    async def _find_relevant_pages(
        self, base_url: str, result: ScrapingResult
    ) -> List[str]:
        """Find relevant pages to scrape (contact, about, etc.)."""
        relevant_pages = []

        try:
            response = self._make_request(base_url)
            soup = self._parse_html(response.text, base_url)

            # Look for common contact/about page patterns
            relevant_keywords = [
                "contact",
                "about",
                "team",
                "staff",
                "people",
                "leadership",
                "management",
                "directory",
                "employees",
                "our-team",
                "meet-team",
            ]

            links = soup.find_all("a", href=True)

            for link in links:
                href = link.get("href", "").lower()
                text = link.get_text(strip=True).lower()

                # Check if link or text contains relevant keywords
                if any(
                    keyword in href or keyword in text for keyword in relevant_keywords
                ):
                    full_url = urljoin(base_url, link["href"])

                    # Ensure it's from the same domain
                    if self._is_same_domain(base_url, full_url):
                        relevant_pages.append(full_url)

            # Remove duplicates and limit
            relevant_pages = list(set(relevant_pages))[:10]

        except Exception as e:
            result.add_warning(f"Failed to find relevant pages: {e}")

        return relevant_pages

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.get_text(strip=True)

        # Fallback to h1
        h1_tag = soup.find("h1")
        if h1_tag:
            return h1_tag.get_text(strip=True)

        return ""

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract page description."""
        # Try meta description first
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and hasattr(meta_desc, 'get') and meta_desc.get("content"):
            content = meta_desc.get("content")
            if isinstance(content, str):
                return content.strip()

        # Fallback to first paragraph
        first_p = soup.find("p")
        if first_p:
            return first_p.get_text(strip=True)[:200] + "..."

        return ""

    def _extract_contacts_from_page(
        self, soup: BeautifulSoup, url: str
    ) -> List[ContactCreate]:
        """Extract contact information from a page."""
        contacts = []
        page_text = soup.get_text()

        # Extract emails
        emails = self.contact_patterns["email"].findall(page_text)

        # Extract phones
        phone_matches = self.contact_patterns["phone"].findall(page_text)
        ["".join(match) for match in phone_matches]

        # Look for structured contact information
        contact_sections = self._find_contact_sections(soup)

        for section in contact_sections:
            contact_data = self._extract_contact_from_section(section)
            if contact_data:
                contact = ContactCreate(
                    first_name=contact_data.get("first_name", ""),
                    last_name=contact_data.get("last_name", ""),
                    full_name=contact_data.get("full_name", ""),
                    email=contact_data.get("email", ""),
                    phone=contact_data.get("phone", ""),
                    job_title=contact_data.get("job_title", ""),
                    department=contact_data.get("department", ""),
                    seniority_level=contact_data.get("seniority_level", ""),
                    twitter_handle=contact_data.get("twitter_handle", ""),
                    source=self.get_source().value,
                    experience_years=None,
                    contact_quality_score=None,
                    engagement_potential=None,
                )
                contacts.append(contact)

        # If no structured contacts found, create generic ones from emails/phones
        if not contacts:
            for email in emails[:5]:  # Limit to 5 emails
                if self._is_valid_business_email(email):
                    contact = ContactCreate(
                        first_name="",
                        last_name="",
                        full_name=None,
                        email=email,
                        phone="",
                        job_title="",
                        department=None,
                        seniority_level=None,
                        twitter_handle=None,
                        experience_years=None,
                        contact_quality_score=None,
                        engagement_potential=None,
                        source=self.get_source().value,
                    )
                    contacts.append(contact)

        return contacts

    def _find_contact_sections(self, soup: BeautifulSoup) -> List[Tag]:
        """Find sections that likely contain contact information."""
        contact_sections: List[Tag] = []

        # Look for common contact section patterns
        selectors = [
            ".contact",
            ".team-member",
            ".staff",
            ".employee",
            ".person",
            ".bio",
            ".profile",
            '[class*="contact"]',
            '[class*="team"]',
            '[class*="staff"]',
        ]

        for selector in selectors:
            sections = soup.select(selector)
            contact_sections.extend(sections)

        # Also look for divs/sections with contact-related text
        all_divs = soup.find_all(["div", "section", "article"])
        for div in all_divs:
            text = div.get_text().lower()
            if any(word in text for word in ["contact", "email", "phone", "call"]):
                if len(text) < 500:  # Avoid very large sections
                    contact_sections.append(div)

        return contact_sections[:20]  # Limit to avoid processing too many

    def _extract_contact_from_section(self, section: Tag) -> Optional[Dict]:
        """Extract contact information from a section."""
        try:
            contact_data = {}
            section_text = section.get_text()

            # Extract email
            email_match = self.contact_patterns["email"].search(section_text)
            if email_match:
                contact_data["email"] = email_match.group()

            # Extract phone
            phone_match = self.contact_patterns["phone"].search(section_text)
            if phone_match:
                contact_data["phone"] = "".join(phone_match.groups())

            # Try to extract name
            name = self._extract_name_from_section(section)
            if name:
                name_parts = name.split()
                if len(name_parts) >= 2:
                    contact_data["first_name"] = name_parts[0]
                    contact_data["last_name"] = " ".join(name_parts[1:])
                else:
                    contact_data["first_name"] = name

            # Try to extract job title
            job_title = self._extract_job_title_from_section(section)
            if job_title:
                contact_data["job_title"] = job_title

            return contact_data if contact_data else None

        except Exception as e:
            self.logger.warning(f"Failed to extract contact from section: {e}")
            return None

    def _extract_name_from_section(self, section: Tag) -> Optional[str]:
        """Extract person name from a section."""
        # Look for name in common patterns
        name_selectors = [
            "h1",
            "h2",
            "h3",
            "h4",
            ".name",
            ".title",
            ".person-name",
            '[class*="name"]',
            "strong",
            "b",
        ]

        for selector in name_selectors:
            element = section.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                # Simple name validation
                if 2 <= len(text.split()) <= 4 and text.replace(" ", "").isalpha():
                    return text

        return None

    def _extract_job_title_from_section(self, section: Tag) -> Optional[str]:
        """Extract job title from a section."""
        job_keywords = [
            "ceo",
            "president",
            "director",
            "manager",
            "coordinator",
            "specialist",
            "analyst",
            "engineer",
            "developer",
            "designer",
            "consultant",
            "advisor",
            "founder",
            "owner",
            "partner",
        ]

        text = section.get_text().lower()
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        for line in lines:
            if any(keyword in line for keyword in job_keywords):
                if len(line) < 100:  # Reasonable title length
                    return line.title()

        return None

    def _extract_company_info_from_page(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract company information from a page."""
        company_info: Dict[str, Any] = {}

        try:
            # Extract company name
            company_name = self._extract_company_name(soup)
            if company_name:
                company_info["name"] = company_name

            # Extract address
            address_match = self.contact_patterns["address"].search(soup.get_text())
            if address_match:
                company_info["address"] = address_match.group().strip()

            # Extract social media links
            social_links = self._extract_social_media_links(soup)
            if social_links:
                company_info["social_media"] = social_links

            # Extract business description
            description = self._extract_business_description(soup)
            if description:
                company_info["description"] = description

        except Exception as e:
            self.logger.warning(f"Failed to extract company info: {e}")

        return company_info

    def _extract_company_name(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract company name from page."""
        # Try multiple sources
        sources = [
            soup.find("title"),
            soup.find("h1"),
            soup.select_one(".company-name"),
            soup.select_one('[class*="company"]'),
            soup.select_one(".logo"),
        ]

        for source in sources:
            if source:
                text = source.get_text(strip=True)
                if text and len(text) < 100:
                    # Clean up common suffixes
                    text = re.sub(r"\s*[-|].*$", "", text)
                    return text

        return None

    def _extract_social_media_links(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract social media links."""
        social_links = {}

        links = soup.find_all("a", href=True)
        for link in links:
            href = link["href"]
            match = self.contact_patterns["social_media"].search(href)
            if match:
                platform = match.group(1)
                social_links[platform] = href

        return social_links

    def _extract_business_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract business description."""
        # Look for about sections
        about_selectors = [
            ".about",
            ".description",
            ".overview",
            ".company-info",
            '[class*="about"]',
            '[class*="description"]',
        ]

        for selector in about_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if 50 < len(text) < 500:
                    return text

        return None

    def _create_company_from_website_data(
        self, base_url: str, result: ScrapingResult
    ) -> Optional[CompanyCreate]:
        """Create a Company object from scraped website data."""
        try:
            # Aggregate data from all scraped pages
            all_data = {}
            if hasattr(result, "raw_data") and result.raw_data:
                for page_data in result.raw_data.get("pages", []):
                    all_data.update(page_data)

            # Extract domain
            parsed_url = urlparse(base_url)
            domain = parsed_url.netloc.lower().replace("www.", "")

            company_name = all_data.get("name", "")
            if not company_name:
                # Fallback to domain-based name
                company_name = domain.split(".")[0].title()

            return CompanyCreate(
                name=company_name,
                domain=domain,
                website=None if not base_url else HttpUrl(base_url),
                phone=self._get_primary_phone(result),
                address=all_data.get("address", ""),
                industry=None,
                company_size=None,
                founded_year=None,
                revenue_range=None,
                employee_count=None,
                data_quality_score=None,
                lead_score=None,
                description=all_data.get("description", ""),
                source=self.get_source().value,
                source_url=base_url,
            )

        except Exception as e:
            self.logger.warning(f"Failed to create company from website data: {e}")
            return None

    def _get_primary_phone(self, result: ScrapingResult) -> str:
        """Get the primary phone number from contacts."""
        if result.contacts:
            for contact in result.contacts:
                if contact.phone:
                    return contact.phone
        return ""

    def _is_valid_business_email(self, email: str) -> bool:
        """Check if email looks like a business email."""
        # Exclude common personal email domains
        personal_domains = {
            "gmail.com",
            "yahoo.com",
            "hotmail.com",
            "outlook.com",
            "aol.com",
            "icloud.com",
            "live.com",
            "msn.com",
        }

        domain = email.split("@")[1].lower()
        return domain not in personal_domains

    def _is_same_domain(self, base_url: str, target_url: str) -> bool:
        """Check if two URLs are from the same domain."""
        try:
            base_domain = urlparse(base_url).netloc.lower()
            target_domain = urlparse(target_url).netloc.lower()
            return base_domain == target_domain
        except Exception:
            return False
