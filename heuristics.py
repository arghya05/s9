# modules/heuristics.py

from typing import Dict, List, Optional, Tuple, Union
import re
import datetime
import json

class QueryHeuristics:
    """Collection of heuristics to validate and process user queries and agent responses."""
    
    @staticmethod
    def validate_and_fix_query(query: str) -> Tuple[str, List[str]]:
        """
        Apply all heuristics to a query, returning the processed query and a list of applied fixes.
        """
        original_query = query
        applied_fixes = []
        
        # Apply each heuristic in sequence
        for heuristic_fn in [
            QueryHeuristics.fix_typos,
            QueryHeuristics.remove_banned_words,
            QueryHeuristics.normalize_date_formats,
            QueryHeuristics.validate_email_format,
            QueryHeuristics.detect_unsafe_commands,
            QueryHeuristics.validate_urls,
            QueryHeuristics.normalize_numeric_values,
            QueryHeuristics.detect_pii,
            QueryHeuristics.remove_excessive_whitespace,
            QueryHeuristics.limit_query_length
        ]:
            query, fixes = heuristic_fn(query)
            applied_fixes.extend(fixes)
            
        return query, applied_fixes
    
    @staticmethod
    def fix_typos(query: str) -> Tuple[str, List[str]]:
        """Heuristic 1: Fix common typos in user queries."""
        fixes = []
        common_typos = {
            "clendar": "calendar",
            "calander": "calendar",
            "schedual": "schedule",
            "scedule": "schedule",
            "emaill": "email",
            "emial": "email",
            "docuemnt": "document",
            "documnet": "document",
            "serach": "search",
            "summery": "summary",
            "summerize": "summarize"
        }
        
        corrected_query = query
        for typo, correction in common_typos.items():
            if re.search(r'\b' + re.escape(typo) + r'\b', corrected_query, re.IGNORECASE):
                corrected_query = re.sub(r'\b' + re.escape(typo) + r'\b', correction, corrected_query, flags=re.IGNORECASE)
                fixes.append(f"Corrected typo: '{typo}' to '{correction}'")
                
        return corrected_query, fixes
    
    @staticmethod
    def remove_banned_words(query: str) -> Tuple[str, List[str]]:
        """Heuristic 2: Remove banned or unsafe words from queries."""
        fixes = []
        banned_words = [
            "hack", "exploit", "vulnerability", "illegal", "password", 
            "credit card", "ssn", "social security", "porn", "xxx"
        ]
        
        clean_query = query
        for word in banned_words:
            if re.search(r'\b' + re.escape(word) + r'\b', clean_query, re.IGNORECASE):
                clean_query = re.sub(r'\b' + re.escape(word) + r'\b', "[FILTERED]", clean_query, flags=re.IGNORECASE)
                fixes.append(f"Removed banned word: '{word}'")
                
        return clean_query, fixes
    
    @staticmethod
    def normalize_date_formats(query: str) -> Tuple[str, List[str]]:
        """Heuristic 3: Normalize date formats for consistency."""
        fixes = []
        
        # Convert mm/dd/yy to ISO format (yyyy-mm-dd)
        date_pattern = r'(\d{1,2})/(\d{1,2})/(\d{2}|\d{4})'
        
        def date_replacer(match):
            month, day, year = match.groups()
            month = month.zfill(2)  # Ensure 2 digits
            day = day.zfill(2)      # Ensure 2 digits
            
            # Handle 2-digit years
            if len(year) == 2:
                current_year = datetime.datetime.now().year
                century = str(current_year)[:2]
                year = f"{century}{year}"
                
            fixes.append(f"Normalized date format: {month}/{day}/{year[-2:]} to {year}-{month}-{day}")
            return f"{year}-{month}-{day}"
        
        normalized_query = re.sub(date_pattern, date_replacer, query)
        
        return normalized_query, fixes
    
    @staticmethod
    def validate_email_format(query: str) -> Tuple[str, List[str]]:
        """Heuristic 4: Validate and flag potentially invalid email formats."""
        fixes = []
        
        # Simple regex for email validation
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, query)
        
        validated_query = query
        for email in emails:
            # Check for common typos in domain names
            domain = email.split('@')[1]
            common_domains = {
                "gmal.com": "gmail.com",
                "gamil.com": "gmail.com",
                "gmial.com": "gmail.com",
                "hotmial.com": "hotmail.com",
                "yaho.com": "yahoo.com",
                "outlok.com": "outlook.com"
            }
            
            for typo_domain, correct_domain in common_domains.items():
                if domain == typo_domain:
                    corrected_email = email.replace(typo_domain, correct_domain)
                    validated_query = validated_query.replace(email, corrected_email)
                    fixes.append(f"Corrected email domain: '{email}' to '{corrected_email}'")
        
        return validated_query, fixes
    
    @staticmethod
    def detect_unsafe_commands(query: str) -> Tuple[str, List[str]]:
        """Heuristic 5: Detect and flag potentially unsafe shell commands."""
        fixes = []
        
        # Patterns for potentially unsafe shell commands
        unsafe_patterns = [
            r'\brm\s+-rf\b', 
            r'\bsudo\b', 
            r'\bchmod\b\s+777',
            r'\bdd\b.*\bif=/dev\b',
            r'\bmkfs\b',
            r'\bformat\b.*\bdisk\b'
        ]
        
        for pattern in unsafe_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                fixes.append(f"WARNING: Potentially unsafe command detected: {pattern}")
        
        return query, fixes
    
    @staticmethod
    def validate_urls(query: str) -> Tuple[str, List[str]]:
        """Heuristic 6: Validate and clean URLs in the query."""
        fixes = []
        
        # Simple URL pattern
        url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
        urls = re.findall(url_pattern, query)
        
        clean_query = query
        for url in urls:
            # Check if URL contains suspicious patterns
            suspicious_patterns = [
                r'malware', 
                r'phish',
                r'hack',
                r'crack',
                r'warez',
                r'porn',
                r'xxx'
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    clean_query = clean_query.replace(url, "[FILTERED_URL]")
                    fixes.append(f"Removed suspicious URL containing '{pattern}'")
                    break
        
        return clean_query, fixes
    
    @staticmethod
    def normalize_numeric_values(query: str) -> Tuple[str, List[str]]:
        """Heuristic 7: Normalize and validate numeric values in queries."""
        fixes = []
        
        # Match numeric values with commas or currency symbols
        currency_pattern = r'[$€£¥](\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?'
        
        def currency_replacer(match):
            # Extract just the numeric part
            value = match.group(0)
            symbol = value[0]
            numeric_part = value[1:].replace(',', '')
            
            fixes.append(f"Normalized currency value: {value} to {symbol}{numeric_part}")
            return f"{symbol}{numeric_part}"
        
        normalized_query = re.sub(currency_pattern, currency_replacer, query)
        
        return normalized_query, fixes
    
    @staticmethod
    def detect_pii(query: str) -> Tuple[str, List[str]]:
        """Heuristic 8: Detect and redact potential Personally Identifiable Information."""
        fixes = []
        
        # Credit card number pattern (simplified)
        cc_pattern = r'\b(?:\d{4}[-\s]?){3}\d{4}\b'
        if re.search(cc_pattern, query):
            query = re.sub(cc_pattern, "[REDACTED_CARD_NUMBER]", query)
            fixes.append("Redacted potential credit card number")
        
        # Social Security Number pattern (US)
        ssn_pattern = r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b'
        if re.search(ssn_pattern, query):
            query = re.sub(ssn_pattern, "[REDACTED_SSN]", query)
            fixes.append("Redacted potential Social Security Number")
        
        return query, fixes
    
    @staticmethod
    def remove_excessive_whitespace(query: str) -> Tuple[str, List[str]]:
        """Heuristic 9: Clean up excessive whitespace in queries."""
        fixes = []
        
        # Replace multiple spaces with a single space
        cleaned_query = re.sub(r'\s+', ' ', query).strip()
        if cleaned_query != query:
            fixes.append("Removed excessive whitespace")
        
        return cleaned_query, fixes
    
    @staticmethod
    def limit_query_length(query: str, max_length: int = 500) -> Tuple[str, List[str]]:
        """Heuristic 10: Limit query length to prevent token abuse."""
        fixes = []
        
        if len(query) > max_length:
            truncated_query = query[:max_length] + "..."
            fixes.append(f"Truncated query from {len(query)} to {max_length} characters")
            return truncated_query, fixes
        
        return query, fixes


class ResultHeuristics:
    """Collection of heuristics to validate and process agent responses."""
    
    @staticmethod
    def validate_tool_output(tool_name: str, output: str) -> Tuple[bool, Optional[str], List[str]]:
        """
        Validate tool output based on expected format and content.
        Returns: (is_valid, fixed_output, list_of_messages)
        """
        messages = []
        
        # Handle JSON validation for tools that return JSON
        if tool_name.endswith("_json") or "json" in tool_name:
            try:
                json_output = json.loads(output) if isinstance(output, str) else output
                return True, json.dumps(json_output), messages
            except json.JSONDecodeError:
                messages.append(f"Invalid JSON output from {tool_name}")
                return False, None, messages
        
        # Add specific validation for other tool types as needed
        # For now, pass through other tool outputs
        return True, output, messages
    
    @staticmethod
    def check_for_hallucinations(query: str, response: str) -> Tuple[bool, List[str]]:
        """
        Check for potential hallucinations in agent responses by comparing with the query.
        Returns: (contains_hallucination, list_of_reasons)
        """
        reasons = []
        
        # If response mentions entities not in query or related context
        # This is a simplified check - would need knowledge base integration for real implementation
        query_terms = set(re.findall(r'\b[A-Za-z]+\b', query.lower()))
        
        # Check for definitive statements about entities not mentioned in query
        entities_pattern = r'(?:(?:the|an?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*))'
        mentioned_entities = re.findall(entities_pattern, response)
        
        for entity in mentioned_entities:
            entity_terms = set(re.findall(r'\b[A-Za-z]+\b', entity.lower()))
            if not entity_terms.intersection(query_terms):
                reasons.append(f"Response mentions '{entity}' which was not in the original query")
        
        return len(reasons) > 0, reasons


# Integration function to use in the agent loop
def apply_heuristics(query: str) -> Tuple[str, List[str]]:
    """
    Apply all query heuristics and return processed query with list of applied fixes.
    This function can be called before passing the query to the LLM.
    """
    return QueryHeuristics.validate_and_fix_query(query)


def validate_result(tool_name: str, output: str) -> Tuple[bool, Optional[str], List[str]]:
    """
    Validate tool output using result heuristics.
    This function can be called after receiving tool output before processing it.
    """
    return ResultHeuristics.validate_tool_output(tool_name, output) 