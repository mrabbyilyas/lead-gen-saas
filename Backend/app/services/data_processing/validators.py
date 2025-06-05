"""Data validation utilities for email, phone, and general data validation."""

import re
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberFormat
from email_validator import validate_email, EmailNotValidError

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Validation status enumeration."""

    VALID = "valid"
    INVALID = "invalid"
    UNCERTAIN = "uncertain"
    DISPOSABLE = "disposable"
    ROLE_BASED = "role_based"


@dataclass
class ValidationResult:
    """Result of data validation."""

    is_valid: bool
    status: ValidationStatus
    normalized_value: Optional[str] = None
    confidence_score: float = 0.0
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Fields are already initialized with default_factory
        pass


class EmailValidator:
    """Advanced email validation with business email detection."""

    def __init__(self):
        self.disposable_domains = {
            "10minutemail.com",
            "guerrillamail.com",
            "mailinator.com",
            "tempmail.org",
            "yopmail.com",
            "throwaway.email",
            "temp-mail.org",
            "getnada.com",
            "maildrop.cc",
        }

        self.role_based_prefixes = {
            "admin",
            "administrator",
            "info",
            "contact",
            "support",
            "sales",
            "marketing",
            "noreply",
            "no-reply",
            "help",
            "service",
            "office",
            "team",
            "general",
            "mail",
        }

        self.business_domains = {
            "gmail.com",
            "yahoo.com",
            "hotmail.com",
            "outlook.com",
            "aol.com",
            "icloud.com",
            "live.com",
            "msn.com",
        }

    def validate(self, email: str) -> ValidationResult:
        """Validate email address with comprehensive checks."""
        if not email or not isinstance(email, str):
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID,
                errors=["Email is required and must be a string"],
            )

        email = email.strip().lower()

        try:
            # Basic email validation
            validated_email = validate_email(email)
            normalized_email = validated_email.email

            # Extract domain
            domain = normalized_email.split("@")[1]
            local_part = normalized_email.split("@")[0]

            # Check for disposable email
            if domain in self.disposable_domains:
                return ValidationResult(
                    is_valid=False,
                    status=ValidationStatus.DISPOSABLE,
                    normalized_value=normalized_email,
                    errors=["Disposable email address"],
                    metadata={"domain": domain, "type": "disposable"},
                )

            # Check for role-based email
            if local_part in self.role_based_prefixes:
                return ValidationResult(
                    is_valid=True,
                    status=ValidationStatus.ROLE_BASED,
                    normalized_value=normalized_email,
                    confidence_score=0.6,
                    metadata={"domain": domain, "type": "role_based"},
                )

            # Determine if it's a business email
            is_business = domain not in self.business_domains
            confidence = 0.9 if is_business else 0.7

            return ValidationResult(
                is_valid=True,
                status=ValidationStatus.VALID,
                normalized_value=normalized_email,
                confidence_score=confidence,
                metadata={
                    "domain": domain,
                    "is_business": is_business,
                    "type": "business" if is_business else "personal",
                },
            )

        except EmailNotValidError as e:
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID,
                errors=[str(e)],
                metadata={"original_email": email},
            )
        except Exception as e:
            logger.error(f"Unexpected error validating email {email}: {e}")
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID,
                errors=["Validation error occurred"],
                metadata={"original_email": email},
            )

    def is_business_email(self, email: str) -> bool:
        """Check if email is likely a business email."""
        result = self.validate(email)
        return result.is_valid and result.metadata.get("is_business", False)

    def batch_validate(self, emails: List[str]) -> Dict[str, ValidationResult]:
        """Validate multiple emails at once."""
        results = {}
        for email in emails:
            results[email] = self.validate(email)
        return results


class PhoneValidator:
    """Phone number validation with international support."""

    def __init__(self, default_region: str = "US"):
        self.default_region = default_region

    def validate(self, phone: str, region: Optional[str] = None) -> ValidationResult:
        """Validate phone number with region detection."""
        if not phone or not isinstance(phone, str):
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID,
                errors=["Phone number is required and must be a string"],
            )

        phone = phone.strip()
        region = region or self.default_region

        try:
            # Parse phone number
            parsed_number = phonenumbers.parse(phone, region)

            # Validate number
            if not phonenumbers.is_valid_number(parsed_number):
                return ValidationResult(
                    is_valid=False,
                    status=ValidationStatus.INVALID,
                    errors=["Invalid phone number format"],
                    metadata={"original_phone": phone},
                )

            # Get formatted versions
            international = phonenumbers.format_number(
                parsed_number, PhoneNumberFormat.INTERNATIONAL
            )
            national = phonenumbers.format_number(
                parsed_number, PhoneNumberFormat.NATIONAL
            )
            e164 = phonenumbers.format_number(parsed_number, PhoneNumberFormat.E164)

            # Get number type
            number_type = phonenumbers.number_type(parsed_number)
            type_name = {
                phonenumbers.PhoneNumberType.MOBILE: "mobile",
                phonenumbers.PhoneNumberType.FIXED_LINE: "landline",
                phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "fixed_or_mobile",
                phonenumbers.PhoneNumberType.TOLL_FREE: "toll_free",
                phonenumbers.PhoneNumberType.PREMIUM_RATE: "premium",
                phonenumbers.PhoneNumberType.VOIP: "voip",
            }.get(number_type, "unknown")

            # Calculate confidence based on type
            confidence = {
                "mobile": 0.9,
                "landline": 0.8,
                "fixed_or_mobile": 0.85,
                "voip": 0.7,
                "toll_free": 0.6,
            }.get(type_name, 0.5)

            return ValidationResult(
                is_valid=True,
                status=ValidationStatus.VALID,
                normalized_value=e164,
                confidence_score=confidence,
                metadata={
                    "international": international,
                    "national": national,
                    "e164": e164,
                    "type": type_name,
                    "country_code": parsed_number.country_code,
                    "region": phonenumbers.region_code_for_number(parsed_number),
                },
            )

        except NumberParseException as e:
            error_messages = {
                NumberParseException.INVALID_COUNTRY_CODE: "Invalid country code",
                NumberParseException.NOT_A_NUMBER: "Not a valid number",
                NumberParseException.TOO_SHORT_NSN: "Number too short",
                NumberParseException.TOO_LONG: "Number too long",
            }

            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID,
                errors=[error_messages.get(e.error_type, "Invalid phone number")],
                metadata={"original_phone": phone, "error_type": str(e.error_type)},
            )
        except Exception as e:
            logger.error(f"Unexpected error validating phone {phone}: {e}")
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID,
                errors=["Validation error occurred"],
                metadata={"original_phone": phone},
            )

    def is_mobile(self, phone: str, region: Optional[str] = None) -> bool:
        """Check if phone number is a mobile number."""
        result = self.validate(phone, region)
        return result.is_valid and result.metadata.get("type") == "mobile"

    def batch_validate(
        self, phones: List[str], region: Optional[str] = None
    ) -> Dict[str, ValidationResult]:
        """Validate multiple phone numbers at once."""
        results = {}
        for phone in phones:
            results[phone] = self.validate(phone, region)
        return results


class DataValidator:
    """General data validation for various field types."""

    def __init__(self):
        self.email_validator = EmailValidator()
        self.phone_validator = PhoneValidator()

        # URL validation pattern
        self.url_pattern = re.compile(
            r"^https?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+"  # domain...
            r"(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # host...
            r"localhost|"  # localhost...
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )

    def validate_url(self, url: str) -> ValidationResult:
        """Validate URL format."""
        if not url or not isinstance(url, str):
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID,
                errors=["URL is required and must be a string"],
            )

        url = url.strip()

        # Add protocol if missing
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        if self.url_pattern.match(url):
            return ValidationResult(
                is_valid=True,
                status=ValidationStatus.VALID,
                normalized_value=url,
                confidence_score=0.9,
                metadata={"protocol": url.split("://")[0]},
            )
        else:
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID,
                errors=["Invalid URL format"],
                metadata={"original_url": url},
            )

    def validate_domain(self, domain: str) -> ValidationResult:
        """Validate domain name."""
        if not domain or not isinstance(domain, str):
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID,
                errors=["Domain is required and must be a string"],
            )

        domain = domain.strip().lower()

        # Remove protocol if present
        if "://" in domain:
            domain = domain.split("://", 1)[1]

        # Remove path if present
        if "/" in domain:
            domain = domain.split("/", 1)[0]

        # Domain pattern
        domain_pattern = re.compile(
            r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+"  # subdomains
            r"[a-zA-Z]{2,}$"  # TLD
        )

        if domain_pattern.match(domain):
            return ValidationResult(
                is_valid=True,
                status=ValidationStatus.VALID,
                normalized_value=domain,
                confidence_score=0.9,
                metadata={"tld": domain.split(".")[-1]},
            )
        else:
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID,
                errors=["Invalid domain format"],
                metadata={"original_domain": domain},
            )

    def validate_linkedin_url(self, url: str) -> ValidationResult:
        """Validate LinkedIn profile URL."""
        if not url or not isinstance(url, str):
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID,
                errors=["LinkedIn URL is required and must be a string"],
            )

        url = url.strip()

        # LinkedIn URL patterns
        linkedin_patterns = [
            r"^https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9-]+/?$",  # Personal
            r"^https?://(?:www\.)?linkedin\.com/company/[a-zA-Z0-9-]+/?$",  # Company
        ]

        for pattern in linkedin_patterns:
            if re.match(pattern, url, re.IGNORECASE):
                profile_type = "company" if "/company/" in url else "personal"
                return ValidationResult(
                    is_valid=True,
                    status=ValidationStatus.VALID,
                    normalized_value=url,
                    confidence_score=0.95,
                    metadata={"type": profile_type},
                )

        return ValidationResult(
            is_valid=False,
            status=ValidationStatus.INVALID,
            errors=["Invalid LinkedIn URL format"],
            metadata={"original_url": url},
        )

    def validate_company_name(self, name: str) -> ValidationResult:
        """Validate company name."""
        if not name or not isinstance(name, str):
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID,
                errors=["Company name is required and must be a string"],
            )

        name = name.strip()

        # Basic validation
        if len(name) < 2:
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID,
                errors=["Company name too short"],
            )

        if len(name) > 200:
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID,
                errors=["Company name too long"],
            )

        # Check for suspicious patterns
        suspicious_patterns = [
            r"^[0-9]+$",  # Only numbers
            r"^[^a-zA-Z]*$",  # No letters
            r"test|example|sample|demo",  # Test data
        ]

        confidence = 0.9
        warnings = []

        for pattern in suspicious_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                confidence = 0.3
                warnings.append("Suspicious company name pattern")
                break

        return ValidationResult(
            is_valid=True,
            status=(
                ValidationStatus.VALID
                if confidence > 0.5
                else ValidationStatus.UNCERTAIN
            ),
            normalized_value=name,
            confidence_score=confidence,
            errors=warnings,
            metadata={"length": len(name)},
        )

    def validate_contact_name(
        self, first_name: str, last_name: str
    ) -> ValidationResult:
        """Validate contact name components."""
        errors = []

        if not first_name or not isinstance(first_name, str):
            errors.append("First name is required")
        elif len(first_name.strip()) < 1:
            errors.append("First name cannot be empty")

        if not last_name or not isinstance(last_name, str):
            errors.append("Last name is required")
        elif len(last_name.strip()) < 1:
            errors.append("Last name cannot be empty")

        if errors:
            return ValidationResult(
                is_valid=False, status=ValidationStatus.INVALID, errors=errors
            )

        # Name pattern validation
        name_pattern = re.compile(r"^[a-zA-Z\s\-\'\.À-\u017F]+$")

        first_valid = name_pattern.match(first_name.strip())
        last_valid = name_pattern.match(last_name.strip())

        if not first_valid or not last_valid:
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID,
                errors=["Invalid characters in name"],
            )

        return ValidationResult(
            is_valid=True,
            status=ValidationStatus.VALID,
            normalized_value=f"{first_name.strip()} {last_name.strip()}",
            confidence_score=0.9,
            metadata={"first_name": first_name.strip(), "last_name": last_name.strip()},
        )

    def validate_all(self, data: Dict[str, Any]) -> Dict[str, ValidationResult]:
        """Validate multiple fields at once."""
        results = {}

        # Email validation
        if "email" in data:
            results["email"] = self.email_validator.validate(data["email"])

        # Phone validation
        if "phone" in data:
            results["phone"] = self.phone_validator.validate(data["phone"])

        # URL validation
        if "website" in data:
            results["website"] = self.validate_url(data["website"])

        # Domain validation
        if "domain" in data:
            results["domain"] = self.validate_domain(data["domain"])

        # LinkedIn validation
        if "linkedin_url" in data:
            results["linkedin_url"] = self.validate_linkedin_url(data["linkedin_url"])

        # Company name validation
        if "company_name" in data:
            results["company_name"] = self.validate_company_name(data["company_name"])

        # Contact name validation
        if "first_name" in data and "last_name" in data:
            results["contact_name"] = self.validate_contact_name(
                data["first_name"], data["last_name"]
            )

        return results


class URLValidator:
    @staticmethod
    def validate(url: str) -> ValidationResult:
        """Validate URL format"""
        try:
            from urllib.parse import urlparse
            result = urlparse(url)
            is_valid = all([result.scheme, result.netloc])
            return ValidationResult(
                is_valid=is_valid,
                status=ValidationStatus.VALID if is_valid else ValidationStatus.INVALID,
                normalized_value=url if is_valid else None,
                confidence_score=1.0 if is_valid else 0.0
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID,
                errors=[str(e)]
            )


class DomainValidator:
    @staticmethod
    def validate(domain: str) -> ValidationResult:
        """Validate domain format"""
        pattern = r'^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.([a-zA-Z]{2,}|xn--[a-zA-Z0-9]+)$'
        is_valid = bool(re.match(pattern, domain.strip()))
        return ValidationResult(
            is_valid=is_valid,
            status=ValidationStatus.VALID if is_valid else ValidationStatus.INVALID,
            normalized_value=domain.strip() if is_valid else None,
            confidence_score=1.0 if is_valid else 0.0
        )


class LinkedInURLValidator:
    @staticmethod
    def validate(url: str) -> ValidationResult:
        """Validate LinkedIn URL"""
        is_linkedin = 'linkedin.com' in url
        url_result = URLValidator.validate(url)
        is_valid = is_linkedin and url_result.is_valid
        return ValidationResult(
            is_valid=is_valid,
            status=ValidationStatus.VALID if is_valid else ValidationStatus.INVALID,
            normalized_value=url if is_valid else None,
            confidence_score=1.0 if is_valid else 0.0
        )


class CompanyNameValidator:
    @staticmethod
    def validate(name: str) -> ValidationResult:
        """Validate company name"""
        cleaned_name = name.strip()
        is_valid = 2 <= len(cleaned_name) <= 255
        return ValidationResult(
            is_valid=is_valid,
            status=ValidationStatus.VALID if is_valid else ValidationStatus.INVALID,
            normalized_value=cleaned_name if is_valid else None,
            confidence_score=1.0 if is_valid else 0.0
        )


class ContactNameValidator:
    @staticmethod
    def validate(name: str) -> ValidationResult:
        """Validate contact name"""
        cleaned_name = name.strip()
        is_valid = 2 <= len(cleaned_name) <= 100
        return ValidationResult(
            is_valid=is_valid,
            status=ValidationStatus.VALID if is_valid else ValidationStatus.INVALID,
            normalized_value=cleaned_name if is_valid else None,
            confidence_score=1.0 if is_valid else 0.0
        )
