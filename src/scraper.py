import logging
import os
import re
import sys
import time
from typing import Dict, Set, Any

# --- FIX FOR PYINSTALLER NOCONSOLE CRASH ---
os.environ["WDM_LOG"] = str(logging.NOTSET)
os.environ["WDM_PROGRESS_BAR"] = "0"

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")
# -------------------------------------------

from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402
from selenium.webdriver.chrome.service import Service  # noqa: E402
from selenium.webdriver.common.by import By  # noqa: E402
from webdriver_manager.chrome import ChromeDriverManager  # noqa: E402

# --- Regex Patterns ---
EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
PHONE_REGEX = r"(?:\+|00)[1-9]\d{0,3}[ .-]?(?:\(?\d+\)?[ .-]?)?\d{2,4}[ .-]?(?:\d{2,4}[ .-]?)?\d{2,9}"  # noqa: E501
ZIP_CODE_REGEX = r"\d{2}-\d{3}|\d{5}"


def setup_driver() -> webdriver.Chrome:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    )
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


def extract_info_from_text(text: str) -> Dict[str, Set[str]]:
    results = {
        "emails": set(re.findall(EMAIL_REGEX, text)),
        "phones": set(re.findall(PHONE_REGEX, text)),
        "address": set(),
    }
    for match in re.finditer(ZIP_CODE_REGEX, text):
        start = max(0, match.start() - 50)
        end = min(len(text), match.end() + 50)
        snippet = re.sub(r"\s+", " ", text[start:end].replace("\n", " ").strip())
        results["address"].add(snippet)
    return results


def extract_info_from_links(driver: webdriver.Chrome) -> Dict[str, Set[str]]:
    results: Dict[str, Set[str]] = {
        "emails": set(),
        "phones": set(),
        "address": set(),
    }
    try:
        # Mailto
        for el in driver.find_elements(By.XPATH, '//a[starts-with(@href, "mailto:")]'):
            href = el.get_attribute("href")
            if href:
                email = href.replace("mailto:", "").split("?")[0].strip()
                if email:
                    results["emails"].add(email)
        # Tel
        for el in driver.find_elements(By.XPATH, '//a[starts-with(@href, "tel:")]'):
            href = el.get_attribute("href")
            if href:
                phone = href.replace("tel:", "").split("?")[0].strip()
                if phone:
                    results["phones"].add(phone)
    except Exception:
        pass
    return results


def get_company_name(driver: webdriver.Chrome) -> str:
    """Attempts to find the company name from H1 or Title."""
    try:
        # Strategy 1: H1 (Most profile pages use H1 for the name)
        h1 = driver.find_element(By.TAG_NAME, "h1").text.strip()
        if h1:
            return str(h1)
    except Exception:
        pass

    try:
        # Strategy 2: Page Title (cleanup " | Event Name")
        title = driver.title
        if "|" in title:
            return str(title.split("|")[0].strip())
        return str(title)
    except Exception:
        return "Unknown"


def scrape_domain(driver: webdriver.Chrome, domain: str) -> Dict[str, Any]:
    url = domain if domain.startswith("http") else f"https://{domain}"
    print(f"   Visiting: {url}...")

    data: Dict[str, Any] = {
        "name": "",
        "emails": set(),
        "phones": set(),
        "address": set(),
    }

    def update(new_data: Dict[str, Set[str]]) -> None:
        for k in ["emails", "phones", "address"]:
            data[k].update(new_data.get(k, set()))

    try:
        driver.get(url)
        time.sleep(3)

        # 1. Get Name
        data["name"] = get_company_name(driver)

        # 2. Get Data
        page_text = driver.find_element(By.TAG_NAME, "body").text
        update(extract_info_from_text(page_text))
        update(extract_info_from_links(driver))

        # 3. Fallback to Contact Page if empty
        if not data["emails"]:
            for path in ["/kontakt", "/contact", "/about", "/o-nas"]:
                try:
                    if path in url:
                        continue
                    base_url = "/".join(url.split("/")[:3])
                    driver.get(f"{base_url}{path}")
                    time.sleep(2)
                    update(
                        extract_info_from_text(
                            driver.find_element(By.TAG_NAME, "body").text
                        )
                    )
                    update(extract_info_from_links(driver))
                    if data["emails"]:
                        break
                except Exception:
                    continue

    except Exception as e:
        print(f"   Error: {e}")

    return data
