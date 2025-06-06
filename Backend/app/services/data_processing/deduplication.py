"""Data deduplication utilities for companies and contacts."""

import re
import logging
from typing import Dict, List, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from difflib import SequenceMatcher
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class MatchType(Enum):
    """Types of matches for deduplication."""

    EXACT = "exact"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NO_MATCH = "no_match"


class MergeStrategy(Enum):
    """Strategies for merging duplicate records."""

    KEEP_FIRST = "keep_first"
    KEEP_LAST = "keep_last"
    MERGE_ALL = "merge_all"
    KEEP_MOST_COMPLETE = "keep_most_complete"
    KEEP_HIGHEST_CONFIDENCE = "keep_highest_confidence"


@dataclass
class MatchResult:
    """Result of duplicate detection."""

    record1_id: str
    record2_id: str
    match_type: MatchType
    confidence_score: float
    matching_fields: List[str] = field(default_factory=list)
    conflicting_fields: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeduplicationResult:
    """Result of deduplication process."""

    original_count: int
    deduplicated_count: int
    duplicates_found: int
    matches: List[MatchResult] = field(default_factory=list)
    merged_records: List[Dict[str, Any]] = field(default_factory=list)
    removed_records: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SimilarityCalculator:
    """Calculate similarity between different data types."""

    @staticmethod
    def string_similarity(str1: str, str2: str, normalize: bool = True) -> float:
        """Calculate similarity between two strings."""
        if not str1 or not str2:
            return 0.0

        if normalize:
            str1 = SimilarityCalculator._normalize_string(str1)
            str2 = SimilarityCalculator._normalize_string(str2)

        if str1 == str2:
            return 1.0

        return SequenceMatcher(None, str1, str2).ratio()

    @staticmethod
    def email_similarity(email1: str, email2: str) -> float:
        """Calculate similarity between email addresses."""
        if not email1 or not email2:
            return 0.0

        email1 = email1.lower().strip()
        email2 = email2.lower().strip()

        if email1 == email2:
            return 1.0

        # Check if same domain
        try:
            domain1 = email1.split("@")[1]
            domain2 = email2.split("@")[1]

            if domain1 == domain2:
                # Same domain, check username similarity
                user1 = email1.split("@")[0]
                user2 = email2.split("@")[0]
                return 0.5 + (
                    SimilarityCalculator.string_similarity(user1, user2) * 0.5
                )
        except IndexError:
            pass

        return SimilarityCalculator.string_similarity(email1, email2)

    @staticmethod
    def phone_similarity(phone1: str, phone2: str) -> float:
        """Calculate similarity between phone numbers."""
        if not phone1 or not phone2:
            return 0.0

        # Normalize phone numbers
        normalized1 = SimilarityCalculator._normalize_phone(phone1)
        normalized2 = SimilarityCalculator._normalize_phone(phone2)

        if normalized1 == normalized2:
            return 1.0

        # Check if one is a subset of the other (different formats)
        if normalized1 in normalized2 or normalized2 in normalized1:
            return 0.8

        return SimilarityCalculator.string_similarity(normalized1, normalized2)

    @staticmethod
    def url_similarity(url1: str, url2: str) -> float:
        """Calculate similarity between URLs."""
        if not url1 or not url2:
            return 0.0

        # Normalize URLs
        normalized1 = SimilarityCalculator._normalize_url(url1)
        normalized2 = SimilarityCalculator._normalize_url(url2)

        if normalized1 == normalized2:
            return 1.0

        # Extract domains
        try:
            domain1 = urlparse(normalized1).netloc.lower()
            domain2 = urlparse(normalized2).netloc.lower()

            # Remove www prefix
            domain1 = domain1.replace("www.", "")
            domain2 = domain2.replace("www.", "")

            if domain1 == domain2:
                return 0.9
        except Exception:
            pass

        return SimilarityCalculator.string_similarity(normalized1, normalized2)

    @staticmethod
    def _normalize_string(text: str) -> str:
        """Normalize string for comparison."""
        if not text:
            return ""

        # Convert to lowercase
        text = text.lower()

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # Remove common punctuation
        text = re.sub(r'[.,;:!?"\'-]', "", text)

        # Remove common business suffixes
        suffixes = ["inc", "llc", "ltd", "corp", "corporation", "company", "co"]
        for suffix in suffixes:
            text = re.sub(rf"\b{suffix}\b", "", text)

        return text.strip()

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        """Normalize phone number for comparison."""
        if not phone:
            return ""

        # Remove all non-digit characters
        digits_only = re.sub(r"\D", "", phone)

        # Remove leading 1 for US numbers
        if len(digits_only) == 11 and digits_only.startswith("1"):
            digits_only = digits_only[1:]

        return digits_only

    @staticmethod
    def _normalize_url(url: str) -> str:
        """Normalize URL for comparison."""
        if not url:
            return ""

        url = url.lower().strip()

        # Add protocol if missing
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        # Remove trailing slash
        url = url.rstrip("/")

        return url


class CompanyDeduplicator:
    """Deduplicate company records."""

    def __init__(
        self,
        name_threshold: float = 0.85,
        domain_threshold: float = 0.9,
        email_threshold: float = 0.8,
        phone_threshold: float = 0.8,
    ):
        self.name_threshold = name_threshold
        self.domain_threshold = domain_threshold
        self.email_threshold = email_threshold
        self.phone_threshold = phone_threshold
        self.similarity_calc = SimilarityCalculator()

    def find_duplicates(self, companies: List[Dict[str, Any]]) -> List[MatchResult]:
        """Find duplicate companies in the list."""
        matches = []

        for i in range(len(companies)):
            for j in range(i + 1, len(companies)):
                company1 = companies[i]
                company2 = companies[j]

                match_result = self._compare_companies(
                    company1, company2, str(i), str(j)
                )
                if match_result.match_type != MatchType.NO_MATCH:
                    matches.append(match_result)

        return matches

    def deduplicate(
        self,
        companies: List[Dict[str, Any]],
        strategy: MergeStrategy = MergeStrategy.KEEP_MOST_COMPLETE,
    ) -> DeduplicationResult:
        """Deduplicate company records."""
        original_count = len(companies)
        matches = self.find_duplicates(companies)

        if not matches:
            return DeduplicationResult(
                original_count=original_count,
                deduplicated_count=original_count,
                duplicates_found=0,
                merged_records=companies.copy(),
            )

        # Group matches by connected components
        duplicate_groups = self._group_duplicates(matches, len(companies))

        # Merge duplicates within each group
        merged_records = []
        removed_records = []
        processed_indices = set()

        for group in duplicate_groups:
            if len(group) > 1:
                # Get companies in this group
                group_companies = [companies[i] for i in group]

                # Merge the group
                merged_company = self._merge_companies(group_companies, strategy)
                merged_records.append(merged_company)

                # Mark all but the merged one as removed
                processed_indices.update(group)
                removed_records.extend([str(i) for i in group[1:]])
            else:
                # Single company, keep as is
                merged_records.append(companies[group[0]])
                processed_indices.add(group[0])

        # Add companies that weren't part of any duplicate group
        for i, company in enumerate(companies):
            if i not in processed_indices:
                merged_records.append(company)

        return DeduplicationResult(
            original_count=original_count,
            deduplicated_count=len(merged_records),
            duplicates_found=original_count - len(merged_records),
            matches=matches,
            merged_records=merged_records,
            removed_records=removed_records,
            metadata={
                "duplicate_groups": len(duplicate_groups),
                "strategy_used": strategy.value,
            },
        )

    def _compare_companies(
        self, company1: Dict[str, Any], company2: Dict[str, Any], id1: str, id2: str
    ) -> MatchResult:
        """Compare two companies for similarity."""
        matching_fields = []
        conflicting_fields = []
        scores = {}

        # Compare company names
        name1 = company1.get("name", "")
        name2 = company2.get("name", "")
        if name1 and name2:
            name_similarity = self.similarity_calc.string_similarity(name1, name2)
            scores["name"] = name_similarity
            if name_similarity >= self.name_threshold:
                matching_fields.append("name")
            elif name_similarity < 0.3:
                conflicting_fields.append("name")

        # Compare domains/websites
        domain1 = company1.get("domain") or company1.get("website", "")
        domain2 = company2.get("domain") or company2.get("website", "")
        if domain1 and domain2:
            domain_similarity = self.similarity_calc.url_similarity(domain1, domain2)
            scores["domain"] = domain_similarity
            if domain_similarity >= self.domain_threshold:
                matching_fields.append("domain")
            elif domain_similarity < 0.3:
                conflicting_fields.append("domain")

        # Compare emails
        email1 = company1.get("email", "")
        email2 = company2.get("email", "")
        if email1 and email2:
            email_similarity = self.similarity_calc.email_similarity(email1, email2)
            scores["email"] = email_similarity
            if email_similarity >= self.email_threshold:
                matching_fields.append("email")
            elif email_similarity < 0.3:
                conflicting_fields.append("email")

        # Compare phone numbers
        phone1 = company1.get("phone", "")
        phone2 = company2.get("phone", "")
        if phone1 and phone2:
            phone_similarity = self.similarity_calc.phone_similarity(phone1, phone2)
            scores["phone"] = phone_similarity
            if phone_similarity >= self.phone_threshold:
                matching_fields.append("phone")
            elif phone_similarity < 0.3:
                conflicting_fields.append("phone")

        # Calculate overall confidence
        if not scores:
            confidence = 0.0
            match_type = MatchType.NO_MATCH
        else:
            confidence = sum(scores.values()) / len(scores)

            # Determine match type
            if confidence >= 0.9 or "domain" in matching_fields:
                match_type = MatchType.EXACT
            elif confidence >= 0.8:
                match_type = MatchType.HIGH
            elif confidence >= 0.6:
                match_type = MatchType.MEDIUM
            elif confidence >= 0.4:
                match_type = MatchType.LOW
            else:
                match_type = MatchType.NO_MATCH

        return MatchResult(
            record1_id=id1,
            record2_id=id2,
            match_type=match_type,
            confidence_score=confidence,
            matching_fields=matching_fields,
            conflicting_fields=conflicting_fields,
            metadata={"field_scores": scores},
        )

    def _group_duplicates(
        self, matches: List[MatchResult], total_records: int
    ) -> List[List[int]]:
        """Group duplicate matches into connected components."""
        # Create adjacency list
        graph: Dict[int, Set[int]] = {i: set() for i in range(total_records)}

        for match in matches:
            if match.match_type in [MatchType.EXACT, MatchType.HIGH]:
                id1 = int(match.record1_id)
                id2 = int(match.record2_id)
                graph[id1].add(id2)
                graph[id2].add(id1)

        # Find connected components using DFS
        visited: Set[int] = set()
        groups: List[List[int]] = []

        for node in range(total_records):
            if node not in visited:
                group: List[int] = []
                self._dfs(graph, node, visited, group)
                groups.append(group)

        return groups

    def _dfs(
        self, graph: Dict[int, Set[int]], node: int, visited: Set[int], group: List[int]
    ):
        """Depth-first search for connected components."""
        visited.add(node)
        group.append(node)

        for neighbor in graph[node]:
            if neighbor not in visited:
                self._dfs(graph, neighbor, visited, group)

    def _merge_companies(
        self, companies: List[Dict[str, Any]], strategy: MergeStrategy
    ) -> Dict[str, Any]:
        """Merge multiple company records into one."""
        if len(companies) == 1:
            return companies[0]

        if strategy == MergeStrategy.KEEP_FIRST:
            return companies[0]
        elif strategy == MergeStrategy.KEEP_LAST:
            return companies[-1]
        elif strategy == MergeStrategy.KEEP_MOST_COMPLETE:
            return self._keep_most_complete_company(companies)
        elif strategy == MergeStrategy.MERGE_ALL:
            return self._merge_all_companies(companies)
        else:
            return companies[0]

    def _keep_most_complete_company(
        self, companies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Keep the company record with the most complete information."""
        best_company = companies[0]
        best_score = self._calculate_completeness_score(best_company)

        for company in companies[1:]:
            score = self._calculate_completeness_score(company)
            if score > best_score:
                best_company = company
                best_score = score

        return best_company

    def _merge_all_companies(self, companies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge all company records into a single comprehensive record."""
        merged = {}

        # Priority fields (prefer non-empty values)
        priority_fields = ["name", "domain", "website", "email", "phone", "address"]

        for field_name in priority_fields:
            for company in companies:
                value = company.get(field_name)
                if value and value.strip():
                    merged[field_name] = value
                    break

        # Merge other fields
        all_fields: Set[str] = set()
        for company in companies:
            all_fields.update(company.keys())

        for field_name in all_fields:
            if field_name not in merged:
                for company in companies:
                    value = company.get(field_name)
                    if value is not None:
                        merged[field_name] = value
                        break

        # Merge list fields (like social media links)
        list_fields = ["social_links", "technologies"]
        for field_name in list_fields:
            merged_list = []
            for company in companies:
                if field_name in company and isinstance(company[field_name], list):
                    merged_list.extend(company[field_name])
            if merged_list:
                merged[field_name] = list(set(merged_list))  # Remove duplicates

        return merged

    def _calculate_completeness_score(self, company: Dict[str, Any]) -> float:
        """Calculate completeness score for a company record."""
        important_fields = [
            "name",
            "domain",
            "website",
            "email",
            "phone",
            "address",
            "description",
        ]
        score = 0

        for field_name in important_fields:
            value = company.get(field_name)
            if value and str(value).strip():
                score += 1

        return score / len(important_fields)


class ContactDeduplicator:
    """Deduplicate contact records."""

    def __init__(
        self,
        name_threshold: float = 0.85,
        email_threshold: float = 0.9,
        phone_threshold: float = 0.8,
    ):
        self.name_threshold = name_threshold
        self.email_threshold = email_threshold
        self.phone_threshold = phone_threshold
        self.similarity_calc = SimilarityCalculator()

    def find_duplicates(self, contacts: List[Dict[str, Any]]) -> List[MatchResult]:
        """Find duplicate contacts in the list."""
        matches = []

        for i in range(len(contacts)):
            for j in range(i + 1, len(contacts)):
                contact1 = contacts[i]
                contact2 = contacts[j]

                match_result = self._compare_contacts(
                    contact1, contact2, str(i), str(j)
                )
                if match_result.match_type != MatchType.NO_MATCH:
                    matches.append(match_result)

        return matches

    def deduplicate(
        self,
        contacts: List[Dict[str, Any]],
        strategy: MergeStrategy = MergeStrategy.KEEP_MOST_COMPLETE,
    ) -> DeduplicationResult:
        """Deduplicate contact records."""
        original_count = len(contacts)
        matches = self.find_duplicates(contacts)

        if not matches:
            return DeduplicationResult(
                original_count=original_count,
                deduplicated_count=original_count,
                duplicates_found=0,
                merged_records=contacts.copy(),
            )

        # Group matches by connected components
        duplicate_groups = self._group_duplicates(matches, len(contacts))

        # Merge duplicates within each group
        merged_records = []
        removed_records = []
        processed_indices = set()

        for group in duplicate_groups:
            if len(group) > 1:
                # Get contacts in this group
                group_contacts = [contacts[i] for i in group]

                # Merge the group
                merged_contact = self._merge_contacts(group_contacts, strategy)
                merged_records.append(merged_contact)

                # Mark all but the merged one as removed
                processed_indices.update(group)
                removed_records.extend([str(i) for i in group[1:]])
            else:
                # Single contact, keep as is
                merged_records.append(contacts[group[0]])
                processed_indices.add(group[0])

        # Add contacts that weren't part of any duplicate group
        for i, contact in enumerate(contacts):
            if i not in processed_indices:
                merged_records.append(contact)

        return DeduplicationResult(
            original_count=original_count,
            deduplicated_count=len(merged_records),
            duplicates_found=original_count - len(merged_records),
            matches=matches,
            merged_records=merged_records,
            removed_records=removed_records,
            metadata={
                "duplicate_groups": len(duplicate_groups),
                "strategy_used": strategy.value,
            },
        )

    def _compare_contacts(
        self, contact1: Dict[str, Any], contact2: Dict[str, Any], id1: str, id2: str
    ) -> MatchResult:
        """Compare two contacts for similarity."""
        matching_fields = []
        conflicting_fields = []
        scores = {}

        # Compare full names
        name1 = self._get_full_name(contact1)
        name2 = self._get_full_name(contact2)
        if name1 and name2:
            name_similarity = self.similarity_calc.string_similarity(name1, name2)
            scores["name"] = name_similarity
            if name_similarity >= self.name_threshold:
                matching_fields.append("name")
            elif name_similarity < 0.3:
                conflicting_fields.append("name")

        # Compare emails
        email1 = contact1.get("email", "")
        email2 = contact2.get("email", "")
        if email1 and email2:
            email_similarity = self.similarity_calc.email_similarity(email1, email2)
            scores["email"] = email_similarity
            if email_similarity >= self.email_threshold:
                matching_fields.append("email")
            elif email_similarity < 0.3:
                conflicting_fields.append("email")

        # Compare phone numbers
        phone1 = contact1.get("phone", "")
        phone2 = contact2.get("phone", "")
        if phone1 and phone2:
            phone_similarity = self.similarity_calc.phone_similarity(phone1, phone2)
            scores["phone"] = phone_similarity
            if phone_similarity >= self.phone_threshold:
                matching_fields.append("phone")
            elif phone_similarity < 0.3:
                conflicting_fields.append("phone")

        # Calculate overall confidence
        if not scores:
            confidence = 0.0
            match_type = MatchType.NO_MATCH
        else:
            confidence = sum(scores.values()) / len(scores)

            # Determine match type
            if confidence >= 0.9 or "email" in matching_fields:
                match_type = MatchType.EXACT
            elif confidence >= 0.8:
                match_type = MatchType.HIGH
            elif confidence >= 0.6:
                match_type = MatchType.MEDIUM
            elif confidence >= 0.4:
                match_type = MatchType.LOW
            else:
                match_type = MatchType.NO_MATCH

        return MatchResult(
            record1_id=id1,
            record2_id=id2,
            match_type=match_type,
            confidence_score=confidence,
            matching_fields=matching_fields,
            conflicting_fields=conflicting_fields,
            metadata={"field_scores": scores},
        )

    def _get_full_name(self, contact: Dict[str, Any]) -> str:
        """Get full name from contact record."""
        if "full_name" in contact:
            return str(contact["full_name"]) if contact["full_name"] is not None else ""

        first_name = contact.get("first_name", "")
        last_name = contact.get("last_name", "")

        return f"{first_name} {last_name}".strip()

    def _group_duplicates(
        self, matches: List[MatchResult], total_records: int
    ) -> List[List[int]]:
        """Group duplicate matches into connected components."""
        # Create adjacency list
        graph: Dict[int, Set[int]] = {i: set() for i in range(total_records)}

        for match in matches:
            if match.match_type in [MatchType.EXACT, MatchType.HIGH]:
                id1 = int(match.record1_id)
                id2 = int(match.record2_id)
                graph[id1].add(id2)
                graph[id2].add(id1)

        # Find connected components using DFS
        visited: Set[int] = set()
        groups: List[List[int]] = []

        for node in range(total_records):
            if node not in visited:
                group: List[int] = []
                self._dfs(graph, node, visited, group)
                groups.append(group)

        return groups

    def _dfs(
        self, graph: Dict[int, Set[int]], node: int, visited: Set[int], group: List[int]
    ):
        """Depth-first search for connected components."""
        visited.add(node)
        group.append(node)

        for neighbor in graph[node]:
            if neighbor not in visited:
                self._dfs(graph, neighbor, visited, group)

    def _merge_contacts(
        self, contacts: List[Dict[str, Any]], strategy: MergeStrategy
    ) -> Dict[str, Any]:
        """Merge multiple contact records into one."""
        if len(contacts) == 1:
            return contacts[0]

        if strategy == MergeStrategy.KEEP_FIRST:
            return contacts[0]
        elif strategy == MergeStrategy.KEEP_LAST:
            return contacts[-1]
        elif strategy == MergeStrategy.KEEP_MOST_COMPLETE:
            return self._keep_most_complete_contact(contacts)
        elif strategy == MergeStrategy.MERGE_ALL:
            return self._merge_all_contacts(contacts)
        else:
            return contacts[0]

    def _keep_most_complete_contact(
        self, contacts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Keep the contact record with the most complete information."""
        best_contact = contacts[0]
        best_score = self._calculate_completeness_score(best_contact)

        for contact in contacts[1:]:
            score = self._calculate_completeness_score(contact)
            if score > best_score:
                best_contact = contact
                best_score = score

        return best_contact

    def _merge_all_contacts(self, contacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge all contact records into a single comprehensive record."""
        merged = {}

        # Priority fields (prefer non-empty values)
        priority_fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "job_title",
            "company",
        ]

        for field_name in priority_fields:
            for contact in contacts:
                value = contact.get(field_name)
                if value and str(value).strip():
                    merged[field_name] = value
                    break

        # Merge other fields
        all_fields: Set[str] = set()
        for contact in contacts:
            all_fields.update(contact.keys())

        for field_name in all_fields:
            if field_name not in merged:
                for contact in contacts:
                    value = contact.get(field_name)
                    if value is not None:
                        merged[field_name] = value
                        break

        return merged

    def _calculate_completeness_score(self, contact: Dict[str, Any]) -> float:
        """Calculate completeness score for a contact record."""
        important_fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "job_title",
            "company",
        ]
        score = 0

        for field_name in important_fields:
            value = contact.get(field_name)
            if value and str(value).strip():
                score += 1

        return score / len(important_fields)


class DataDeduplicator:
    """Main deduplication orchestrator."""

    def __init__(self):
        self.company_deduplicator = CompanyDeduplicator()
        self.contact_deduplicator = ContactDeduplicator()

    def deduplicate_companies(
        self,
        companies: List[Dict[str, Any]],
        strategy: MergeStrategy = MergeStrategy.KEEP_MOST_COMPLETE,
    ) -> DeduplicationResult:
        """Deduplicate company records."""
        try:
            result = self.company_deduplicator.deduplicate(companies, strategy)
            if isinstance(result, DeduplicationResult):
                return result
            return DeduplicationResult(original_count=len(companies), deduplicated_count=len(companies), duplicates_found=0)
        except Exception as e:
            logger.error(f"Error deduplicating companies: {e}")
            return DeduplicationResult(
                original_count=len(companies),
                deduplicated_count=len(companies),
                duplicates_found=0,
                merged_records=companies,
                errors=[f"Deduplication failed: {str(e)}"],
            )

    def deduplicate_contacts(
        self,
        contacts: List[Dict[str, Any]],
        strategy: MergeStrategy = MergeStrategy.KEEP_MOST_COMPLETE,
    ) -> DeduplicationResult:
        """Deduplicate contact records."""
        try:
            result = self.contact_deduplicator.deduplicate(contacts, strategy)
            if isinstance(result, DeduplicationResult):
                return result
            return DeduplicationResult(original_count=len(contacts), deduplicated_count=len(contacts), duplicates_found=0)
        except Exception as e:
            logger.error(f"Error deduplicating contacts: {e}")
            return DeduplicationResult(
                original_count=len(contacts),
                deduplicated_count=len(contacts),
                duplicates_found=0,
                merged_records=contacts,
                errors=[f"Deduplication failed: {str(e)}"],
            )

    def find_company_duplicates(
        self, companies: List[Dict[str, Any]]
    ) -> List[MatchResult]:
        """Find duplicate companies without merging."""
        result = self.company_deduplicator.find_duplicates(companies)
        return result if isinstance(result, list) else []

    def find_contact_duplicates(
        self, contacts: List[Dict[str, Any]]
    ) -> List[MatchResult]:
        """Find duplicate contacts without merging."""
        result = self.contact_deduplicator.find_duplicates(contacts)
        return result if isinstance(result, list) else []
