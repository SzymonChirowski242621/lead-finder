import csv
import time
from typing import List, Dict
from search_clients import get_search_results
from scraper import setup_driver, scrape_domain


def save_to_csv(data: List[Dict[str, str]], filename: str = "leads.csv") -> None:
    """Saves the list of dictionaries to a CSV file."""
    if not data:
        print("No data to save.")
        return

    # Define headers
    headers = ["Domain", "Emails", "Phones", "Address Snippet"]

    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

    print(f"\n[SUCCESS] Saved {len(data)} leads to '{filename}'")


def main() -> None:
    # 1. Ask for input
    keyword = input("Enter search query (e.g. 'Hurtownia zabawek Poznań'): ")

    # Simple input validation
    limit_str = input("How many leads do you want? (e.g. 5): ")
    try:
        limit = int(limit_str)
    except ValueError:
        print("Invalid number, defaulting to 5.")
        limit = 5

    # 2. Find Domains
    print("\n--- Phase 1: Finding Companies ---")
    domains = get_search_results(keyword, num_results=limit)
    print(f"Found {len(domains)} unique companies.")

    # 3. Scrape Data
    print("\n--- Phase 2: Extracting Contact Info ---")
    driver = setup_driver()
    results: List[Dict[str, str]] = []

    try:
        for i, domain in enumerate(domains):
            print(f"[{i+1}/{len(domains)}] Processing {domain}...")

            # Run the scraper
            data = scrape_domain(driver, domain)

            # Format for CSV (convert sets to strings)
            # We explicitly cast to str to keep mypy happy
            emails_str = ", ".join(data["emails"])
            phones_str = ", ".join(data["phones"])

            # Take the first address snippet if multiple found
            address_list = list(data["address"])
            addr_str = address_list[0] if address_list else ""

            row = {
                "Domain": domain,
                "Emails": emails_str,
                "Phones": phones_str,
                "Address Snippet": addr_str,
            }
            results.append(row)

            # Be polite to servers
            time.sleep(1)

    finally:
        driver.quit()

    # 4. Save
    save_to_csv(results)


if __name__ == "__main__":
    main()
