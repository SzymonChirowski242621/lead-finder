import logging
import os
import sys

# --- FIX FOR PYINSTALLER NOCONSOLE CRASH ---
# prevent webdriver_manager from writing to NoneType stdout
os.environ["WDM_LOG"] = str(logging.NOTSET)
os.environ["WDM_PROGRESS_BAR"] = "0"

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")
# -------------------------------------------

import re  # noqa: E402
import time  # noqa: E402
from typing import Dict, Set  # noqa: E402

from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402
from selenium.webdriver.chrome.service import Service  # noqa: E402
from selenium.webdriver.common.by import By  # noqa: E402
from webdriver_manager.chrome import ChromeDriverManager  # noqa: E402

# --- Regex Patterns ---
EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

# Split long regex into verbose mode for readability and linting
PHONE_REGEX = (
    r"(?:\+48)?[ -]?(?:\(?\d{2,3}\)?)?[ -]?"
    r"(?:\d{3}[ -]?\d{3}[ -]?\d{3}|\d{2}[ -]?\d{3}[ -]?\d{2}[ -]?\d{2})"
)

ZIP_CODE_REGEX = r"\d{2}-\d{3}"


def setup_driver() -> webdriver.Chrome:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--log-level=3")
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
    for match in re.finditer(ZIP_CODE_REGEX, text):
        start = max(0, match.start() - 50)
        end = min(len(text), match.end() + 50)
        snippet = re.sub(r"\s+", " ", text[start:end].replace("\n", " ").strip())
        results["address"].add(snippet)
    return results


def scrape_domain(driver: webdriver.Chrome, domain: str) -> Dict[str, Set[str]]:
    url = f"https://{domain}" if not domain.startswith("http") else domain
    print(f"   Visiting: {url}...")

    # Explicit type annotation for mypy
    data: Dict[str, Set[str]] = {"emails": set(), "phones": set(), "address": set()}

    def update(new_data: Dict[str, Set[str]]) -> None:
        for k in data:
            data[k].update(new_data.get(k, set()))

    try:
        driver.get(url)
        time.sleep(2)
        page_text = driver.find_element(By.TAG_NAME, "body").text
        update(extract_info(page_text))

        if not data["emails"] or not data["phones"]:
            for path in ["/kontakt", "/contact", "/o-nas", "/stopka"]:
                try:
                    driver.get(f"{url.rstrip('/')}{path}")
                    time.sleep(1)
                    page_text = driver.find_element(By.TAG_NAME, "body").text
                    update(extract_info(page_text))
                    if data["emails"] or data["phones"]:
                        break
                except Exception:
                    continue
    except Exception as e:
        print(f"   Error: {e}")

    return data
