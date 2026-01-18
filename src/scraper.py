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
PHONE_REGEX = r"(?:\+|00)[1-9]\d{0,3}[ .-]?(?:\(?\d+\)?[ .-]?)?\d{2,4}[ .-]?(?:\d{2,4}[ .-]?)?\d{2,9}"  # noqa: E501
ZIP_CODE_REGEX = r"\d{2}-\d{3}|\d{5}"


def setup_driver() -> webdriver.Chrome:
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Headless often fails on complex SPAs
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


def handle_event_profile(driver: webdriver.Chrome) -> Dict[str, Set[str]]:
    """
    Specific extractor for EuroShop / Messe Frankfurt / Light+Building profiles.
    Clicks 'Company data' and targets specific CSS classes.
    """
    results: Dict[str, Set[str]] = {"emails": set(), "phones": set(), "address": set()}

    try:
        # 1. Try to click "Company data" tab button
        # Look for buttons containing text 'Company data', 'Unternehmensdaten', 'Daten'
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            if (
                "company data" in btn.text.lower()
                or "unternehmensdaten" in btn.text.lower()
            ):
                try:
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(1)  # Wait for tab switch
                except Exception:
                    pass

        # 2. Extract from specific EuroShop/Messe classes
        # Email: class="exh-contact__email"
        emails = driver.find_elements(By.CLASS_NAME, "exh-contact__email")
        for e in emails:
            # Text is usually "E-mail: foo@bar.com"
            clean = e.text.replace("E-mail:", "").replace("E-Mail:", "").strip()
            if "@" in clean:
                results["emails"].add(clean)

        # Phone: class="exh-contact__phone"
        phones = driver.find_elements(By.CLASS_NAME, "exh-contact__phone")
        for p in phones:
            clean = p.text.replace("Phone:", "").replace("Telefon:", "").strip()
            if len(clean) > 5:
                results["phones"].add(clean)

        # Address: class="exh-address"
        addresses = driver.find_elements(By.CLASS_NAME, "exh-address")
        for a in addresses:
            results["address"].add(a.text.replace("\n", ", "))

        # External Website: class="exh-contact__link-lbl" sibling
        # Often inside .exh-contact__links a
        links = driver.find_elements(By.CSS_SELECTOR, ".exh-contact__links a")
        for l in links:  # noqa E741
            href = l.get_attribute("href")
            if href and "messe" not in href and "euroshop" not in href:
                pass

    except Exception as e:
        print(f"   [Event Profile Logic Error]: {e}")

    return results


def get_company_name(driver: webdriver.Chrome) -> str:
    try:
        # EuroShop H1 class
        h1 = driver.find_element(By.CSS_SELECTOR, "h1.profile-head__name").text.strip()
        if h1:
            return str(h1)
    except Exception:
        pass

    try:
        h1 = driver.find_element(By.TAG_NAME, "h1").text.strip()
        if h1:
            return str(h1)
    except Exception:
        pass

    try:
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

        # 4. Deep Scrape (Hidden HTML - finds emails in unclicked tabs)
        try:
            html_source = driver.page_source
            update(extract_info_from_text(html_source))
        except Exception:
            pass

        # 5. Link Attributes (mailto/tel)
        update(extract_info_from_links(driver))

        # 6. Fallback: Contact Pages (Only if not an event profile page)
        # We assume event profiles have data on the main page.
        # Deep crawling is for generic company sites.
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
