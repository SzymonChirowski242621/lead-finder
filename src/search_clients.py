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
    """
    Extracts 'https://example.com' from 'https://www.example.com/page?q=1'.
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        protocol = parsed.scheme
        if protocol:
            domain = f"{protocol}://{domain}"
        # Handle cases where url might be missing scheme (e.g. "example.com")
        if not domain:
            domain = parsed.path

        # Remove 'www.' if present for cleaner storage
        if domain.startswith("www."):
            domain = domain[4:]

        return domain
    except Exception:
        return ""


def is_valid_domain(domain: str) -> bool:
    """Check if the DOMAIN is not in our ignore list."""
    if not domain:
        return False

    domain_lower = domain.lower()
    for ignored in IGNORE_DOMAINS:
        if ignored in domain_lower:
            return False
    return True


def get_search_results(query: str, num_results: int = 10) -> List[str]:
    """
    Perform a search using DuckDuckGo and return a CLEAN list of domains.
    """
    print(f"Searching for: {query}...")
    # Use a set to automatically handle duplicates (e.g. home page + contact page)
    results: Set[str] = set()

    try:
        with DDGS() as ddgs:
            # We ask for 2x results because we expect to filter out junk
            search_generator = ddgs.text(
                query,
                max_results=num_results * 2,
            )

            for result in search_generator:
                url = result.get("href")
                if not url:
                    continue

                # 1. Extract Domain
                domain = extract_clean_domain(url)

                # 2. Filter & Deduplicate
                if is_valid_domain(domain):
                    if domain not in results:
                        results.add(domain)
                        print(f"Found (Clean): {domain}")
                else:
                    print(f"Skipped (Junk): {domain}")

                # Stop once we have enough CLEAN results
                if len(results) >= num_results:
                    break

    except Exception as e:
        print(f"Error during search: {e}")

    return list(results)


if __name__ == "__main__":
    TARGET_QUERY = "Firma budowlana Warszawa"
    domains = get_search_results(TARGET_QUERY, num_results=5)

    print("\n--- Final Clean Domains ---")
    for d in domains:
        print(d)
