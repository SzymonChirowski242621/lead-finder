import re
import time
from typing import Dict, Set

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# --- Regex Patterns ---
EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

# Updated to catch:
# 1. Mobile: 500 123 456
# 2. Landline: 25 753 20 40 (The format you found)
PHONE_REGEX = r"(?:\+48)?[ -]?(?:\(?\d{2,3}\)?)?[ -]?(?:\d{3}[ -]?\d{3}[ -]?\d{3}|\d{2}[ -]?\d{3}[ -]?\d{2}[ -]?\d{2})"  # noqa E501

ZIP_CODE_REGEX = r"\d{2}-\d{3}"


def setup_driver() -> webdriver.Chrome:
    """Sets up a headless Chrome browser."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--log-level=3")  # Hide Selenium logs
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
    )
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


def extract_info(text: str) -> Dict[str, Set[str]]:
    results = {
        "emails": set(re.findall(EMAIL_REGEX, text)),
        "phones": set(re.findall(PHONE_REGEX, text)),
        "address": set(),
    }

    # Improved Address Logic
    for match in re.finditer(ZIP_CODE_REGEX, text):
        # Expand the window to capture full street names
        start = max(0, match.start() - 50)
        end = min(len(text), match.end() + 50)
        snippet = text[start:end].replace("\n", " ").strip()
        snippet = re.sub(r"\s+", " ", snippet)  # Clean double spaces
        results["address"].add(snippet)

    return results


def scrape_domain(driver: webdriver.Chrome, domain: str) -> Dict[str, Set[str]]:
    if not domain.startswith("http"):
        url = f"https://{domain}"
    else:
        url = domain

    print(f"   Visiting: {url}...")
    collected_data: Dict[str, set[str]] = {
        "emails": set(),
        "phones": set(),
        "address": set(),
    }

    def update_data(new_data: Dict[str, Set[str]]) -> None:
        for key in collected_data:
            collected_data[key].update(new_data.get(key, set()))

    try:
        driver.get(url)
        time.sleep(2)
        page_text = driver.find_element(By.TAG_NAME, "body").text
        update_data(extract_info(page_text))

        # Heuristic: if missing critical info, check /kontakt
        if not collected_data["emails"] or not collected_data["phones"]:
            # Polish common paths
            for path in ["/kontakt", "/contact", "/o-nas", "/stopka"]:
                try:
                    contact_url = f"{url.rstrip('/')}{path}"
                    driver.get(contact_url)
                    time.sleep(1)
                    page_text = driver.find_element(By.TAG_NAME, "body").text
                    found = extract_info(page_text)

                    if found["emails"] or found["phones"]:
                        update_data(found)
                        print(f"     > Found info on {path}")
                        break
                except Exception:
                    continue

    except Exception as e:
        print(f"   Error: {e}")

    return collected_data


if __name__ == "__main__":
    # Test on the problem site
    test_domain = "ecconstruction.pl"
    driver = setup_driver()
    try:
        data = scrape_domain(driver, test_domain)
        print(f"\n--- Result for {test_domain} ---")
        print(f"Emails: {data['emails']}")
        print(f"Phones: {data['phones']}")
    finally:
        driver.quit()
