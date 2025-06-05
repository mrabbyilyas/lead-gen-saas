"""Data cleaning utilities for text, addresses, and general data normalization."""

import re
import logging
from typing import Dict, List, Any
from dataclasses import dataclass, field
import unicodedata
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


@dataclass
class CleaningResult:
    """Result of data cleaning operation."""

    original_value: str
    cleaned_value: str
    changes_made: List[str]
    confidence_score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Field is already initialized with default_factory
        pass


class TextCleaner:
    """Advanced text cleaning and normalization."""

    def __init__(self):
        # Common text cleaning patterns
        self.patterns = {
            "extra_whitespace": re.compile(r"\s+"),
            "special_chars": re.compile(r"[^\w\s\-\.@]"),
            "html_tags": re.compile(r"<[^>]+>"),
            "email_pattern": re.compile(
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
            ),
            "phone_pattern": re.compile(r"[\+]?[1-9]?[0-9]{7,15}"),
            "url_pattern": re.compile(
                r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
            ),
        }

        # Common business suffixes
        self.business_suffixes = {
            "inc",
            "inc.",
            "incorporated",
            "corp",
            "corp.",
            "corporation",
            "llc",
            "l.l.c.",
            "ltd",
            "ltd.",
            "limited",
            "co",
            "co.",
            "company",
            "lp",
            "l.p.",
            "llp",
            "l.l.p.",
            "pllc",
            "p.l.l.c.",
            "gmbh",
            "ag",
            "sa",
            "srl",
            "bv",
            "nv",
            "oy",
            "ab",
            "as",
        }

        # Stop words for company names
        self.stop_words = {
            "the",
            "and",
            "or",
            "of",
            "in",
            "at",
            "to",
            "for",
            "with",
            "by",
            "from",
            "on",
            "as",
            "is",
            "was",
            "are",
            "were",
        }

    def clean_text(self, text: str, preserve_case: bool = False) -> CleaningResult:
        """Clean and normalize text with comprehensive cleaning."""
        if not text or not isinstance(text, str):
            return CleaningResult(
                original_value=str(text) if text else "",
                cleaned_value="",
                changes_made=["Empty or invalid input"],
            )

        original = text
        changes = []

        # Remove HTML tags
        if self.patterns["html_tags"].search(text):
            text = self.patterns["html_tags"].sub("", text)
            changes.append("Removed HTML tags")

        # Normalize unicode characters
        normalized = unicodedata.normalize("NFKD", text)
        if normalized != text:
            text = normalized
            changes.append("Normalized unicode characters")

        # Remove extra whitespace
        cleaned_whitespace: str = self.patterns["extra_whitespace"].sub(" ", text).strip()
        if cleaned_whitespace != text:
            text = cleaned_whitespace
            changes.append("Normalized whitespace")

        # Case normalization
        if not preserve_case:
            if text.isupper() or text.islower():
                text = text.title()
                changes.append("Normalized case")

        # Calculate confidence based on changes
        confidence = max(0.5, 1.0 - (len(changes) * 0.1))

        return CleaningResult(
            original_value=original,
            cleaned_value=text,
            changes_made=changes,
            confidence_score=confidence,
            metadata={"length_change": len(text) - len(original)},
        )

    def clean_company_name(self, name: str) -> CleaningResult:
        """Clean company name with business-specific rules."""
        if not name or not isinstance(name, str):
            return CleaningResult(
                original_value=str(name) if name else "",
                cleaned_value="",
                changes_made=["Empty or invalid company name"],
            )

        original = name
        changes = []

        # Basic text cleaning
        basic_result = self.clean_text(name, preserve_case=True)
        name = basic_result.cleaned_value
        changes.extend(basic_result.changes_made)

        # Remove common prefixes
        prefixes = ["the ", "a ", "an "]
        for prefix in prefixes:
            if name.lower().startswith(prefix):
                name = name[len(prefix) :]
                changes.append(f"Removed prefix '{prefix.strip()}'")
                break

        # Normalize business suffixes
        words = name.split()
        if words:
            last_word = words[-1].lower().rstrip(".")
            if last_word in self.business_suffixes:
                # Standardize common suffixes
                suffix_map = {
                    "inc": "Inc.",
                    "corp": "Corp.",
                    "llc": "LLC",
                    "ltd": "Ltd.",
                    "co": "Co.",
                }
                if last_word in suffix_map:
                    words[-1] = suffix_map[last_word]
                    name = " ".join(words)
                    changes.append("Standardized business suffix")

        # Remove duplicate words
        words = name.split()
        unique_words = []
        seen = set()
        for word in words:
            word_lower = word.lower()
            if word_lower not in seen:
                unique_words.append(word)
                seen.add(word_lower)
            else:
                changes.append(f"Removed duplicate word '{word}'")

        if len(unique_words) != len(words):
            name = " ".join(unique_words)

        # Final cleanup
        name = name.strip()

        confidence = max(0.6, 1.0 - (len(changes) * 0.05))

        return CleaningResult(
            original_value=original,
            cleaned_value=name,
            changes_made=changes,
            confidence_score=confidence,
            metadata={
                "word_count": len(name.split()),
                "has_suffix": any(
                    word.lower().rstrip(".") in self.business_suffixes
                    for word in name.split()
                ),
            },
        )

    def clean_person_name(self, name: str) -> CleaningResult:
        """Clean person name with name-specific rules."""
        if not name or not isinstance(name, str):
            return CleaningResult(
                original_value=str(name) if name else "",
                cleaned_value="",
                changes_made=["Empty or invalid name"],
            )

        original = name
        changes = []

        # Basic text cleaning
        basic_result = self.clean_text(name)
        name = basic_result.cleaned_value
        changes.extend(basic_result.changes_made)

        # Remove titles and suffixes
        titles = ["mr", "mrs", "ms", "dr", "prof", "sir", "madam"]
        suffixes = ["jr", "sr", "ii", "iii", "iv", "phd", "md", "esq"]

        words = name.split()
        cleaned_words = []

        for word in words:
            word_clean = word.lower().rstrip(".")
            if word_clean not in titles and word_clean not in suffixes:
                cleaned_words.append(word)
            else:
                changes.append(f"Removed title/suffix '{word}'")

        if len(cleaned_words) != len(words):
            name = " ".join(cleaned_words)

        # Capitalize properly
        name = " ".join(word.capitalize() for word in name.split())

        confidence = max(0.7, 1.0 - (len(changes) * 0.1))

        return CleaningResult(
            original_value=original,
            cleaned_value=name,
            changes_made=changes,
            confidence_score=confidence,
            metadata={"word_count": len(name.split())},
        )

    def extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text."""
        if not text:
            return []
        return self.patterns["email_pattern"].findall(text)

    def extract_phones(self, text: str) -> List[str]:
        """Extract phone numbers from text."""
        if not text:
            return []
        return self.patterns["phone_pattern"].findall(text)

    def extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text."""
        if not text:
            return []
        return self.patterns["url_pattern"].findall(text)


class AddressCleaner:
    """Address cleaning and normalization."""

    def __init__(self):
        # Address component patterns
        self.patterns = {
            "street_suffixes": re.compile(
                r"\b(st|street|ave|avenue|rd|road|blvd|boulevard|dr|drive|ln|lane|ct|court|pl|place|way|cir|circle)\b",
                re.IGNORECASE,
            ),
            "unit_types": re.compile(
                r"\b(apt|apartment|unit|ste|suite|floor|fl|room|rm|#)\b", re.IGNORECASE
            ),
            "directions": re.compile(
                r"\b(n|north|s|south|e|east|w|west|ne|northwest|se|southeast|sw|southwest|nw|northwest)\b",
                re.IGNORECASE,
            ),
            "zip_code": re.compile(r"\b\d{5}(-\d{4})?\b"),
            "po_box": re.compile(
                r"\b(po|p\.o\.|post office)\s*box\s*\d+\b", re.IGNORECASE
            ),
        }

        # State abbreviations
        self.state_abbrev = {
            "alabama": "AL",
            "alaska": "AK",
            "arizona": "AZ",
            "arkansas": "AR",
            "california": "CA",
            "colorado": "CO",
            "connecticut": "CT",
            "delaware": "DE",
            "florida": "FL",
            "georgia": "GA",
            "hawaii": "HI",
            "idaho": "ID",
            "illinois": "IL",
            "indiana": "IN",
            "iowa": "IA",
            "kansas": "KS",
            "kentucky": "KY",
            "louisiana": "LA",
            "maine": "ME",
            "maryland": "MD",
            "massachusetts": "MA",
            "michigan": "MI",
            "minnesota": "MN",
            "mississippi": "MS",
            "missouri": "MO",
            "montana": "MT",
            "nebraska": "NE",
            "nevada": "NV",
            "new hampshire": "NH",
            "new jersey": "NJ",
            "new mexico": "NM",
            "new york": "NY",
            "north carolina": "NC",
            "north dakota": "ND",
            "ohio": "OH",
            "oklahoma": "OK",
            "oregon": "OR",
            "pennsylvania": "PA",
            "rhode island": "RI",
            "south carolina": "SC",
            "south dakota": "SD",
            "tennessee": "TN",
            "texas": "TX",
            "utah": "UT",
            "vermont": "VT",
            "virginia": "VA",
            "washington": "WA",
            "west virginia": "WV",
            "wisconsin": "WI",
            "wyoming": "WY",
        }

    def clean_address(self, address: str) -> CleaningResult:
        """Clean and normalize address."""
        if not address or not isinstance(address, str):
            return CleaningResult(
                original_value=str(address) if address else "",
                cleaned_value="",
                changes_made=["Empty or invalid address"],
            )

        original = address
        changes = []

        # Basic text cleaning
        text_cleaner = TextCleaner()
        basic_result = text_cleaner.clean_text(address, preserve_case=True)
        address = basic_result.cleaned_value
        changes.extend(basic_result.changes_made)

        # Normalize street suffixes
        suffix_map = {
            "st": "Street",
            "ave": "Avenue",
            "rd": "Road",
            "blvd": "Boulevard",
            "dr": "Drive",
            "ln": "Lane",
            "ct": "Court",
            "pl": "Place",
            "cir": "Circle",
            "way": "Way",
        }

        for abbrev, full in suffix_map.items():
            pattern = re.compile(r"\b" + abbrev + r"\b", re.IGNORECASE)
            if pattern.search(address):
                address = pattern.sub(full, address)
                changes.append(f"Expanded '{abbrev}' to '{full}'")

        # Normalize directions
        direction_map = {
            "n": "North",
            "s": "South",
            "e": "East",
            "w": "West",
            "ne": "Northeast",
            "se": "Southeast",
            "sw": "Southwest",
            "nw": "Northwest",
        }

        for abbrev, full in direction_map.items():
            pattern = re.compile(r"\b" + abbrev + r"\b", re.IGNORECASE)
            if pattern.search(address):
                address = pattern.sub(full, address)
                changes.append(f"Expanded direction '{abbrev}' to '{full}'")

        # Normalize state names
        for state_name, abbrev in self.state_abbrev.items():
            pattern = re.compile(r"\b" + state_name + r"\b", re.IGNORECASE)
            if pattern.search(address):
                address = pattern.sub(abbrev, address)
                changes.append(f"Abbreviated state '{state_name}' to '{abbrev}'")

        # Clean up spacing around commas
        address = re.sub(r"\s*,\s*", ", ", address)

        # Remove duplicate commas
        address = re.sub(r",+", ",", address)

        # Final cleanup
        address = address.strip().rstrip(",")

        confidence = max(0.7, 1.0 - (len(changes) * 0.05))

        return CleaningResult(
            original_value=original,
            cleaned_value=address,
            changes_made=changes,
            confidence_score=confidence,
            metadata={
                "has_zip": bool(self.patterns["zip_code"].search(address)),
                "is_po_box": bool(self.patterns["po_box"].search(address)),
            },
        )

    def parse_address_components(self, address: str) -> Dict[str, str]:
        """Parse address into components."""
        components = {
            "street": "",
            "city": "",
            "state": "",
            "zip_code": "",
            "country": "",
        }

        if not address:
            return components

        # Extract ZIP code
        zip_match = self.patterns["zip_code"].search(address)
        if zip_match:
            components["zip_code"] = zip_match.group()
            address = address.replace(zip_match.group(), "").strip()

        # Split by commas
        parts = [part.strip() for part in address.split(",")]

        if len(parts) >= 3:
            components["street"] = parts[0]
            components["city"] = parts[1]
            # Last part might be state or state + country
            state_part = parts[2]
            if state_part.upper() in self.state_abbrev.values():
                components["state"] = state_part.upper()
            elif state_part.lower() in self.state_abbrev:
                components["state"] = self.state_abbrev[state_part.lower()]
        elif len(parts) == 2:
            components["street"] = parts[0]
            components["city"] = parts[1]
        elif len(parts) == 1:
            components["street"] = parts[0]

        return components


class DataCleaner:
    """Main data cleaning orchestrator."""

    def __init__(self):
        self.text_cleaner = TextCleaner()
        self.address_cleaner = AddressCleaner()

    def clean_url(self, url: str) -> CleaningResult:
        """Clean and normalize URL."""
        if not url or not isinstance(url, str):
            return CleaningResult(
                original_value=str(url) if url else "",
                cleaned_value="",
                changes_made=["Empty or invalid URL"],
            )

        original = url
        changes = []

        # Remove whitespace
        url = url.strip()

        # Add protocol if missing
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            changes.append("Added HTTPS protocol")

        # Parse and reconstruct URL
        try:
            parsed = urlparse(url)

            # Normalize domain
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
                changes.append("Removed www prefix")

            # Reconstruct URL
            scheme = "https" if parsed.scheme == "https" else "http"
            path = parsed.path.rstrip("/") if parsed.path != "/" else ""

            cleaned_url = f"{scheme}://{domain}{path}"

            if parsed.query:
                cleaned_url += f"?{parsed.query}"

            confidence = 0.9 if changes else 1.0

            return CleaningResult(
                original_value=original,
                cleaned_value=cleaned_url,
                changes_made=changes,
                confidence_score=confidence,
                metadata={
                    "domain": domain,
                    "scheme": scheme,
                    "has_path": bool(path),
                    "has_query": bool(parsed.query),
                },
            )

        except Exception as e:
            logger.error(f"Error parsing URL {url}: {e}")
            return CleaningResult(
                original_value=original,
                cleaned_value=url,
                changes_made=["URL parsing failed"],
                confidence_score=0.3,
            )

    def clean_phone(self, phone: str) -> CleaningResult:
        """Clean phone number format."""
        if not phone or not isinstance(phone, str):
            return CleaningResult(
                original_value=str(phone) if phone else "",
                cleaned_value="",
                changes_made=["Empty or invalid phone"],
            )

        original = phone
        changes = []

        # Remove all non-digit characters except + at the beginning
        cleaned = re.sub(r"[^\d+]", "", phone)

        # Ensure + is only at the beginning
        if "+" in cleaned:
            plus_count = cleaned.count("+")
            if plus_count > 1 or not cleaned.startswith("+"):
                cleaned = cleaned.replace("+", "")
                changes.append("Removed invalid + characters")

        # Format US numbers
        if len(cleaned) == 10 and not cleaned.startswith("+"):
            cleaned = f"+1{cleaned}"
            changes.append("Added US country code")
        elif (
            len(cleaned) == 11
            and cleaned.startswith("1")
            and not cleaned.startswith("+")
        ):
            cleaned = f"+{cleaned}"
            changes.append("Added + prefix")

        confidence = 0.9 if len(cleaned) >= 10 else 0.5

        return CleaningResult(
            original_value=original,
            cleaned_value=cleaned,
            changes_made=changes,
            confidence_score=confidence,
            metadata={"length": len(cleaned)},
        )

    def clean_email(self, email: str) -> CleaningResult:
        """Clean email address."""
        if not email or not isinstance(email, str):
            return CleaningResult(
                original_value=str(email) if email else "",
                cleaned_value="",
                changes_made=["Empty or invalid email"],
            )

        original = email
        changes = []

        # Basic cleaning
        email = email.strip().lower()

        # Remove spaces
        if " " in email:
            email = email.replace(" ", "")
            changes.append("Removed spaces")

        # Validate basic format
        if "@" not in email or email.count("@") != 1:
            return CleaningResult(
                original_value=original,
                cleaned_value=email,
                changes_made=changes + ["Invalid email format"],
                confidence_score=0.1,
            )

        confidence = 0.9 if changes else 1.0

        return CleaningResult(
            original_value=original,
            cleaned_value=email,
            changes_made=changes,
            confidence_score=confidence,
            metadata={"domain": email.split("@")[1] if "@" in email else ""},
        )

    def clean_all(self, data: Dict[str, Any]) -> Dict[str, CleaningResult]:
        """Clean multiple fields at once."""
        results = {}

        # Company name
        if "company_name" in data:
            results["company_name"] = self.text_cleaner.clean_company_name(
                data["company_name"]
            )

        # Contact names
        if "first_name" in data:
            results["first_name"] = self.text_cleaner.clean_person_name(
                data["first_name"]
            )

        if "last_name" in data:
            results["last_name"] = self.text_cleaner.clean_person_name(
                data["last_name"]
            )

        # Email
        if "email" in data:
            results["email"] = self.clean_email(data["email"])

        # Phone
        if "phone" in data:
            results["phone"] = self.clean_phone(data["phone"])

        # URL/Website
        if "website" in data:
            results["website"] = self.clean_url(data["website"])

        # Address
        if "address" in data:
            results["address"] = self.address_cleaner.clean_address(data["address"])

        # Job title
        if "job_title" in data:
            results["job_title"] = self.text_cleaner.clean_text(data["job_title"])

        # Industry
        if "industry" in data:
            results["industry"] = self.text_cleaner.clean_text(data["industry"])

        # Description
        if "description" in data:
            results["description"] = self.text_cleaner.clean_text(
                data["description"], preserve_case=True
            )

        return results
