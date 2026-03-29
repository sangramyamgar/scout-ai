"""
Guardrails for protecting sensitive data and handling out-of-scope queries.
"""

import re
from typing import List, Optional, Tuple

from langchain_core.documents import Document


class PIIGuard:
    """
    Detect and mask Personally Identifiable Information (PII).
    Uses regex patterns for common PII types.
    """

    # Common PII patterns
    PATTERNS = {
        "email": (
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "[EMAIL REDACTED]",
        ),
        "phone_india": (
            r"\b(?:\+91[-\s]?)?[6-9]\d{9}\b",
            "[PHONE REDACTED]",
        ),
        "phone_us": (
            r"\b(?:\+1[-\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
            "[PHONE REDACTED]",
        ),
        "ssn": (
            r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b",
            "[SSN REDACTED]",
        ),
        "pan_india": (
            r"\b[A-Z]{5}\d{4}[A-Z]\b",
            "[PAN REDACTED]",
        ),
        "aadhaar": (
            r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
            "[AADHAAR REDACTED]",
        ),
        "credit_card": (
            r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
            "[CARD REDACTED]",
        ),
        "salary_amount": (
            r"\b(?:salary|compensation|pay)[\s:]*(?:INR|Rs\.?|₹|\$)?\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?\b",
            "[SALARY REDACTED]",
        ),
    }

    def __init__(self, mask_in_response: bool = True):
        """
        Initialize PII guard.

        Args:
            mask_in_response: Whether to mask PII in LLM responses
        """
        self.mask_in_response = mask_in_response
        self._compiled_patterns = {
            name: (re.compile(pattern, re.IGNORECASE), replacement)
            for name, (pattern, replacement) in self.PATTERNS.items()
        }

    def detect_pii(self, text: str) -> List[dict]:
        """
        Detect PII in text.

        Returns:
            List of detected PII with type and position
        """
        findings = []

        for pii_type, (pattern, _) in self._compiled_patterns.items():
            for match in pattern.finditer(text):
                findings.append({
                    "type": pii_type,
                    "value": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                })

        return findings

    def mask_pii(self, text: str) -> Tuple[str, List[dict]]:
        """
        Mask PII in text.

        Returns:
            Tuple of (masked_text, list_of_masked_items)
        """
        masked_text = text
        masked_items = []

        for pii_type, (pattern, replacement) in self._compiled_patterns.items():
            matches = list(pattern.finditer(masked_text))
            for match in matches:
                masked_items.append({
                    "type": pii_type,
                    "original": match.group(),
                })
            masked_text = pattern.sub(replacement, masked_text)

        return masked_text, masked_items

    def filter_documents(self, documents: List[Document]) -> List[Document]:
        """
        Mask PII in retrieved documents before sending to LLM.
        """
        filtered = []
        for doc in documents:
            masked_content, _ = self.mask_pii(doc.page_content)
            filtered.append(
                Document(
                    page_content=masked_content,
                    metadata=doc.metadata,
                )
            )
        return filtered


class ScopeGuard:
    """
    Detect out-of-scope queries that shouldn't be answered.
    """

    # Topics that are out of scope for a corporate chatbot
    OUT_OF_SCOPE_PATTERNS = [
        # Personal advice
        r"\b(medical|health|legal|financial)\s+advice\b",
        r"\b(should\s+i|recommend|suggest)\s+(invest|buy|sell)\b",

        # Harmful content
        r"\b(hack|exploit|bypass|crack)\b",
        r"\b(illegal|fraud|scam)\b",

        # Personal information requests (for others)
        r"\b(someone'?s?|other\s+employee'?s?)\s+(salary|address|phone)\b",

        # Off-topic
        r"\b(weather|sports|movies|games|recipe)\b",
        r"\b(joke|funny|entertain)\b",

        # Prompt injection attempts
        r"ignore\s+(previous|above|all)\s+(instructions?|prompts?)",
        r"you\s+are\s+now\s+a",
        r"pretend\s+(to\s+be|you'?re)",
        r"system\s*prompt",
        r"jailbreak",
    ]

    def __init__(self):
        self._compiled_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.OUT_OF_SCOPE_PATTERNS
        ]

    def is_out_of_scope(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a query is out of scope.

        Returns:
            Tuple of (is_out_of_scope, reason)
        """
        for pattern in self._compiled_patterns:
            if pattern.search(query):
                return True, f"Query appears to be out of scope for this assistant"

        return False, None

    def is_prompt_injection(self, query: str) -> bool:
        """Check specifically for prompt injection attempts."""
        injection_patterns = [
            r"ignore\s+(previous|above|all)\s+(instructions?|prompts?)",
            r"you\s+are\s+now\s+a",
            r"pretend\s+(to\s+be|you'?re)",
            r"system\s*prompt",
            r"reveal\s+(your|the)\s+(instructions?|prompt)",
            r"\[system\]|\[assistant\]|\[user\]",
        ]

        for pattern in injection_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True

        return False


class InputSanitizer:
    """
    Sanitize user input to prevent injection attacks.
    """

    def sanitize(self, text: str) -> str:
        """
        Sanitize user input.

        - Remove potential control characters
        - Limit length
        - Strip excessive whitespace
        """
        # Remove control characters
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

        # Limit length (prevent resource exhaustion)
        max_length = 2000
        if len(text) > max_length:
            text = text[:max_length] + "..."

        # Normalize whitespace
        text = " ".join(text.split())

        return text.strip()


class GuardrailsManager:
    """
    Central manager for all guardrails.
    """

    def __init__(self):
        self.pii_guard = PIIGuard()
        self.scope_guard = ScopeGuard()
        self.sanitizer = InputSanitizer()

    def process_query(self, query: str) -> Tuple[str, dict]:
        """
        Process a user query through all guardrails.

        Returns:
            Tuple of (processed_query, guardrails_result)
        """
        result = {
            "blocked": False,
            "reason": None,
            "warnings": [],
        }

        # Sanitize input
        query = self.sanitizer.sanitize(query)

        # Check for prompt injection
        if self.scope_guard.is_prompt_injection(query):
            result["blocked"] = True
            result["reason"] = "Query appears to contain a prompt injection attempt"
            return query, result

        # Check if out of scope
        is_oos, reason = self.scope_guard.is_out_of_scope(query)
        if is_oos:
            result["blocked"] = True
            result["reason"] = reason
            return query, result

        # Check for PII in query (warn but don't block)
        pii_findings = self.pii_guard.detect_pii(query)
        if pii_findings:
            result["warnings"].append(
                f"Query contains potential PII: {[f['type'] for f in pii_findings]}"
            )

        return query, result

    def process_response(self, response: str) -> str:
        """
        Process LLM response through guardrails (mask PII).
        """
        masked_response, _ = self.pii_guard.mask_pii(response)
        return masked_response

    def filter_context(self, documents: List[Document]) -> List[Document]:
        """
        Filter context documents (mask PII before sending to LLM).
        """
        return self.pii_guard.filter_documents(documents)


# Global guardrails instance
_guardrails: Optional[GuardrailsManager] = None


def get_guardrails() -> GuardrailsManager:
    """Get or create the global guardrails manager."""
    global _guardrails
    if _guardrails is None:
        _guardrails = GuardrailsManager()
    return _guardrails
