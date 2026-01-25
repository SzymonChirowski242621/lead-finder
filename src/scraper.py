import logging
import os
import re
import sys
import time
from typing import Any, Dict, Set

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


def setup_driver() -> webdriver.Chrome:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


def extract_info_from_text(text: str) -> Dict[str, Set[str]]:
    return {
        "emails": set(re.findall(EMAIL_REGEX, text)),
    }


def extract_info_from_links(driver: webdriver.Chrome) -> Dict[str, Set[str]]:
    results: Dict[str, Set[str]] = {"emails": set()}
    try:
        # Mailto
        for el in driver.find_elements(By.XPATH, '//a[starts-with(@href, "mailto:")]'):
            href = el.get_attribute("href")
            if href:
                email = href.replace("mailto:", "").split("?")[0].strip()
                if email:
                    results["emails"].add(email)
    except Exception:
        pass
    return results


def handle_event_profile(driver: webdriver.Chrome) -> Dict[str, Set[str]]:
    """
    Specific extractor for EuroShop / Messe Frankfurt / Light+Building profiles.
    """
    results: Dict[str, Set[str]] = {"emails": set()}

    try:
        # 1. Try to click "Company data" tab button
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            txt = btn.text.lower()
            if "company data" in txt or "unternehmensdaten" in txt:
                try:
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(1)
                except Exception:
                    pass

        # 2. Extract Email from class="exh-contact__email"
        emails = driver.find_elements(By.CLASS_NAME, "exh-contact__email")
        for e in emails:
            clean = e.text.replace("E-mail:", "").replace("E-Mail:", "").strip()
            if "@" in clean:
                results["emails"].add(clean)

    except Exception as e:
        print(f"   [Event Profile Logic Error]: {e}")

    return results


def get_company_name(driver: webdriver.Chrome) -> str:
    name = "Unknown"
    try:
        h1 = driver.find_element(By.CSS_SELECTOR, "h1.profile-head__name").text.strip()
        if h1:
            name = h1
    except Exception:
        pass

    if name == "Unknown":
        try:
            h1 = driver.find_element(By.TAG_NAME, "h1").text.strip()
            if h1:
                name = h1
        except Exception:
            pass

    if name == "Unknown":
        try:
            title = driver.title
            if "|" in title:
                name = title.split("|")[0].strip()
            else:
                name = title
        except Exception:
            pass

    # Sanitize for CSV
    return name.replace("\n", " ").replace("\r", "").replace("\t", " ").strip()


def scrape_domain(driver: webdriver.Chrome, domain: str) -> Dict[str, Any]:
    url = domain if domain.startswith("http") else f"https://{domain}"
    print(f"   Visiting: {url}...")

    data: Dict[str, Any] = {
        "name": "",
        "emails": set(),
    }

    def update(new_data: Dict[str, Set[str]]) -> None:
        data["emails"].update(new_data.get("emails", set()))

    try:
        driver.get(url)
        time.sleep(3)  # Wait for SPA load

        # 1. Get Name
        data["name"] = get_company_name(driver)

        # 2. Run Specialized Event Extractor (EuroShop/Messe)
        update(handle_event_profile(driver))

        # 3. Generic Scrape (Visible Text)
        try:
            page_text = driver.find_element(By.TAG_NAME, "body").text
            update(extract_info_from_text(page_text))
        except Exception:
            pass

        # 4. Deep Scrape (Hidden HTML)
        try:
            html_source = driver.page_source
            update(extract_info_from_text(html_source))
        except Exception:
            pass

        # 5. Link Attributes (mailto)
        update(extract_info_from_links(driver))

        # 6. Fallback: Contact Pages
        if "messe" not in url and "euroshop" not in url:
            if not data["emails"]:
                for path in ["/kontakt", "/contact", "/about", "/o-nas", "/impressum"]:
                    try:
                        if path in url:
                            continue
                        base_url = "/".join(url.split("/")[:3])
                        driver.get(f"{base_url}{path}")
                        time.sleep(2)

                        update(extract_info_from_text(driver.page_source))
                        update(extract_info_from_links(driver))
                        if data["emails"]:
                            break
                    except Exception:
                        continue

    except Exception as e:
        print(f"   Error: {e}")

    return data
