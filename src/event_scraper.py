import logging
import os
import sys
import tkinter.messagebox
from typing import Callable, List, Set
from urllib.parse import urlparse

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
        if not url or "javascript" in url or "mailto" in url:
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
    for el in elements:
        try:
            url = el.get_attribute("href")
            domain = clean_domain(url)
            # Filter out the event's own links (avoid self-loops)
            current_host = driver.current_url.split("/")[2]
            if domain and domain not in current_host:
                found.add(domain)
        except Exception:
            continue
    return found


def get_event_domains(
    target_url: str, log_callback: Callable[[str], None] = print
) -> List[str]:
    """
    Visits an event URL, hunts for iframes,
    and returns a list of unique company domains.
    """
    if not target_url.startswith("http"):
        target_url = "https://" + target_url

    driver = setup_driver()
    all_domains: Set[str] = set()

    try:
        log_callback(f"Visiting event page: {target_url}")
        driver.get(target_url)

        # --- PAUSE FOR USER ---
        log_callback("⏳ Waiting for you to setup the page...")

        # This will freeze the script until you click OK
        tkinter.messagebox.showinfo(
            "Browser Paused",
            "Please go to the Chrome window:\n"
            "1. Accept Cookies.\n"
            "2. Scroll down so the Exhibitor List is VISIBLE.\n"
            "3. Wait for the list to fully load.\n\n"
            "Click OK here when ready to scrape.",
        )

        log_callback("Resuming scan...")
        # ----------------------

        # --- STRATEGY 1: Scrape Main Page ---
        log_callback("Scanning main page for links...")
        main_links = scan_page_for_links(driver)
        log_callback(f"Found {len(main_links)} links on main page.")
        all_domains.update(main_links)

        # --- STRATEGY 2: Iframe Hunting ---
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        log_callback(f"Found {len(iframes)} iframes. checking them...")

        for i, iframe in enumerate(iframes):
            try:
                # Scroll iframe into view just in case
                driver.execute_script("arguments[0].scrollIntoView(true);", iframe)

                driver.switch_to.frame(iframe)
                iframe_links = scan_page_for_links(driver)
                if iframe_links:
                    log_callback(
                        f"   [Iframe {i + 1}] Found {len(iframe_links)} links!"
                    )
                    all_domains.update(iframe_links)
                driver.switch_to.default_content()
            except Exception:
                driver.switch_to.default_content()

    except Exception as e:
        log_callback(f"Error extracting event domains: {e}")
    finally:
        driver.quit()

    return list(all_domains)
