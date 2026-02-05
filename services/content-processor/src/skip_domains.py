#!/usr/bin/env python3
"""
Skip domains configuration for content processing
Contains list of website URL prefixes to skip during content fetching
"""

SKIP_DOMAINS = [
    "https://www.ft.com",
    "https://ndtv.in/videos",
    "https://phys.org"
]

def should_skip_url(url: str) -> bool:
    """
    Check if a URL should be skipped based on domain prefixes
    
    Args:
        url (str): The URL to check
        
    Returns:
        bool: True if the URL should be skipped, False otherwise
    """
    if not url:
        return True
    
    # Convert to lowercase for case-insensitive matching
    url_lower = url.lower()
    
    # Check if URL starts with any of the skip domains
    for skip_domain in SKIP_DOMAINS:
        if url_lower.startswith(skip_domain.lower()):
            return True
    
    return False

def get_skip_domains() -> list:
    """
    Get the list of domains to skip
    
    Returns:
        list: List of domain prefixes to skip
    """
    return SKIP_DOMAINS.copy()

def add_skip_domain(domain: str) -> None:
    """
    Add a new domain to the skip list
    
    Args:
        domain (str): The domain prefix to add
    """
    if domain and domain not in SKIP_DOMAINS:
        SKIP_DOMAINS.append(domain)

def remove_skip_domain(domain: str) -> None:
    """
    Remove a domain from the skip list
    
    Args:
        domain (str): The domain prefix to remove
    """
    if domain in SKIP_DOMAINS:
        SKIP_DOMAINS.remove(domain)

if __name__ == "__main__":
    # Test the skip functionality
    test_urls = [
        "https://www.ndtv.com/some-article",
        "https://www.example.com/good-article",
        "https://www.wsj.com/paywall-article",
        "https://www.github.com/open-source-article",
        "https://feeds.feedburner.com/some-feed",
    ]
    
    print("Testing URL skip functionality:")
    for url in test_urls:
        should_skip = should_skip_url(url)
        print(f"URL: {url}")
        print(f"Should skip: {should_skip}")
        print("-" * 50)
