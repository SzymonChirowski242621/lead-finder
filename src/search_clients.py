from typing import List, Set
from urllib.parse import urlparse
from ddgs import DDGS

# --- Polish Blocklist ---
IGNORE_DOMAINS = [
    # --- Global Social Media ---
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "twitter.com",
    "x.com",
    "youtube",
    "tiktok",
    "pinterest",
    # --- Global Directories ---
    "clutch.co",
    "upwork",
    "glassdoor",
    "tripadvisor",
    "yelp",
    "trustpilot",
    "behance",
    "dribbble",
    # --- Polish Aggregators (The "SEO Trash" in PL) ---
    "oferteo.pl",  # The biggest service aggregator to avoid
    "fixly.pl",  # Services (owned by OLX)
    "firmy.net",  # Business directory
    "olx.pl",  # Classifieds
    "allegro.pl",  # E-commerce
    "pkt.pl",  # Polskie Książki Telefoniczne (Yellow Pages)
    "panoramafirm.pl",  # Major business directory
    "aleo.com",  # Business database
    "gowork.pl",  # Employer reviews
    "pracuj.pl",  # Job board
    "baza-firm",  # Generic directory
    "favore.pl",  # Directory
    "cylex-polska.pl",  # Directory
    "biznesfinder.pl",  # Directory
    "useme.com",  # Freelance platform
    "yellowpages.pl",  # Yellow Pages
    "tabelaofert.pl",  # Offer comparison site
]


def extract_clean_domain(url: str) -> str:
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        if not domain:
            domain = parsed.path
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


def is_valid_domain(domain: str) -> bool:
    if not domain:
        return False
    domain_lower = domain.lower()
    for ignored in IGNORE_DOMAINS:
        if ignored in domain_lower:
            return False
    return True


def get_search_results(query: str, num_results: int = 10) -> List[str]:
    print(f"Searching for: {query}...")
    results: Set[str] = set()

    # NOTE: No try/except block here! We want errors (like missing libraries)
    # to bubble up so the GUI can log them as "CRITICAL ERROR".
    with DDGS() as ddgs:
        search_generator = ddgs.text(query, max_results=num_results * 2)

        for result in search_generator:
            url = result.get("href")
            if not url:
                continue

            domain = extract_clean_domain(url)

            if is_valid_domain(domain):
                if domain not in results:
                    results.add(domain)
                    print(f"Found (Clean): {domain}")

            if len(results) >= num_results:
                break

    return list(results)


if __name__ == "__main__":
    TARGET_QUERY = "Firma budowlana Warszawa"
    domains = get_search_results(TARGET_QUERY, num_results=5)

    print("\n--- Final Clean Domains ---")
    for d in domains:
        print(d)
