import logging
import os
import sys
import time
import tkinter.messagebox
from typing import Callable, List, Set
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# --- FIX FOR PYINSTALLER/CONSOLE ---
os.environ["WDM_LOG"] = str(logging.NOTSET)
os.environ["WDM_PROGRESS_BAR"] = "0"

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")
# -----------------------------------


def setup_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def clean_domain(url: str) -> str:
    """Extracts just the 'company.com' part from a messy link."""
    try:
        if not url or "javascript" in url.lower() or "mailto" in url.lower():
            return ""
        parsed = urlparse(url)
        domain = parsed.netloc
        if not domain:
            return ""
        return domain.replace("www.", "")
    except Exception:
        return ""


def scan_page_for_links(driver: webdriver.Chrome) -> Set[str]:
    """Grabs all links from the current view."""
    found = set()
    elements = driver.find_elements(By.TAG_NAME, "a")

    try:
        current_host = urlparse(driver.current_url).netloc.replace("www.", "")
    except Exception:
        current_host = ""

    for el in elements:
        try:
            url = el.get_attribute("href")
            if not url:
                continue

            domain = clean_domain(url)

            # Strategy 1: External Website
            if domain and domain not in current_host:
                found.add(domain)

            # Strategy 2: Internal Profile Page
            elif domain and domain in current_host:
                keywords = [
                    "detail",
                    "profile",
                    "exhibitor",
                    "wystawca",
                    "company",
                    "entry",
                ]
                if any(k in url.lower() for k in keywords):
                    found.add(url)

        except Exception:
            continue
    return found


def try_pagination_click(
    driver: webdriver.Chrome, log_callback: Callable[[str], None]
) -> bool:
    """Fallback: Attempts to find and click the 'Next' button."""
    xpaths = [
        "//a[contains(@class, 'next')]",
        "//li[contains(@class, 'next')]/a",
        "//button[contains(@class, 'next')]",
        "//a[contains(@aria-label, 'Next')]",
        "//a[contains(text(), 'Next')]",
        "//a[contains(text(), '>')]",
    ]

    for xpath in xpaths:
        try:
            next_btn = driver.find_element(By.XPATH, xpath)
            if next_btn.is_displayed():
                log_callback(f"   >>> Clicking 'Next' button ({xpath})...")
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", next_btn
                )
                time.sleep(1)
                driver.execute_script("arguments[0].click();", next_btn)
                time.sleep(5)
                return True
        except Exception:
            continue
    return False


def get_next_page_url(base_url: str, page_num: int) -> str:
    """Updates the 'page' query parameter in a URL."""
    parsed = urlparse(base_url)
    query = parse_qs(parsed.query)
    query["page"] = [str(page_num)]
    new_query = urlencode(query, doseq=True)
    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment,
        )
    )


def get_event_domains(
    target_url: str, max_pages: int = 5, log_callback: Callable[[str], None] = print
) -> List[str]:
    if not target_url.startswith("http"):
        target_url = "https://" + target_url

    driver = setup_driver()
    all_domains: Set[str] = set()

    # DETECT PAGINATION MODE
    # If URL contains "page=", we use URL manipulation mode.
    use_url_pagination = "page=" in target_url
    if use_url_pagination:
        log_callback(f"Detected URL pagination mode (Max: {max_pages} pages)")

    try:
        if not use_url_pagination:
            # Standard Mode (Click Buttons)
            log_callback(f"Visiting: {target_url}")
            driver.get(target_url)
            log_callback("⏳ Waiting for manual setup...")
            tkinter.messagebox.showinfo(
                "Browser Paused",
                "Please setup the page (Cookies, Scroll).\nClick OK to start.",
            )

        for page_num in range(1, max_pages + 1):
            if use_url_pagination:
                # URL Mode: Navigate directly
                current_url = get_next_page_url(target_url, page_num)
                log_callback(f"--- Visiting Page {page_num}: {current_url} ---")
                driver.get(current_url)
                if page_num == 1:
                    time.sleep(5)  # Wait longer on first page
                else:
                    time.sleep(3)
            else:
                # Button Mode
                log_callback(f"--- Processing Page {page_num} ---")

            # Scrape
            new_links = scan_page_for_links(driver)
            log_callback(f"   Found {len(new_links)} links.")
            all_domains.update(new_links)

            # Check iframes
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            if iframes:
                for i, iframe in enumerate(iframes):
                    try:
                        driver.switch_to.frame(iframe)
                        iframe_links = scan_page_for_links(driver)
                        if iframe_links:
                            all_domains.update(iframe_links)
                        driver.switch_to.default_content()
                    except Exception:
                        driver.switch_to.default_content()

            # Handle Transition
            if not use_url_pagination:
                if not try_pagination_click(driver, log_callback):
                    log_callback("--- No 'Next' button found. Stopping. ---")
                    break

    except Exception as e:
        log_callback(f"Error: {e}")
    finally:
        driver.quit()

    return list(all_domains)
