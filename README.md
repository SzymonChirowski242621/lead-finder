# Lead Finder (The Robotic Intern) 🤖

A specialized B2B lead generation tool designed to automate the process of finding contact information for business niches and trade show exhibitors.

It acts as a **Fleet of Robotic Interns**: it searches for companies, visits their websites simultaneously (multi-threaded), scans for contact details (emails, phone numbers, addresses), and saves everything to a neat CSV file.

---

## 🚀 Features

* **⚡ Fleet Mode (Multi-Threading):**
  Launches multiple browsers (bots) at once to scrape 5x–10x faster. Includes a smart *Traffic Light* warning system to prevent PC freezes.

* **🌍 Universal Event Scraper:**
  Specialized mode to scrape exhibitor lists from trade show websites. Handles hidden **iframes** and waits for you to clear cookies manually.

* **Smart Search:**
  Uses DuckDuckGo to find company domains while avoiding Google anti bot bans.

* **Junk Filtering:**
  Automatically ignores directories (Oferteo, Yelp, OLX), social media, and aggregators to focus on real company websites.

* **Battery Included:**
  Simple click to run launcher (`start.bat`) that handles installation automatically.

---

## 📦 How to Use (For Users)

### Prerequisites

1. **Google Chrome** must be installed.
2. **Python 3.10 or newer** must be installed
   Download: [https://www.python.org/downloads/](https://www.python.org/downloads/)
   Make sure to check **Add Python to PATH** during installation.

### 🟢 For Windows Users
1.  Double-click **`start.bat`**.
2.  Wait for the installation to finish.
3.  The app will open automatically.

### 🍎 For macOS Users
1.  Open the folder.
2.  **First time only:** You might need to allow the script to run.
    * Open Terminal, type `chmod +x ` (with a space at the end), drag the `start.command` file into the window, and hit Enter.
3.  Double-click **`start.command`**.
4.  The app will open automatically.
---

### Running the Tool

#### 1. Get the Code

* Click the green **Code** button and select **Download ZIP**, then extract it
* Or clone via terminal:

```
git clone https://github.com/SzymonChirowski242621/lead-finder.git
```

#### 2. Start the App

* Double click **start.bat**
* First run may take 1–2 minutes to install dependencies

#### 3. Choose Your Mode

**Option A: Keyword Search**

* Enter a niche (e.g. `construction companies in Berlin`)
* Set **Max Results** (e.g. 50)

**Option B: Scrape Event URL**

* Paste an exhibitor list URL (e.g. [https://example-trade-show.com/exhibitors](https://example-trade-show.com/exhibitors))
* A browser window will open
* Manually accept cookies and scroll until the list is visible (follow on-screen instructions in the pop-up)
* Click **OK** so the bots can take over

#### 4. Configure the Fleet

**Active Bots**

* ✅ 1–4: Safe mode (recommended for laptops)
* ⚠️ 5–9: High performance (8 bots requires around 16GB of free RAM)
* 🔥 10+: Danger zone (may freeze your PC)

#### 5. Start

* Click **Start Robotic Intern Fleet**
* Watch logs as bots work in parallel
* Results are saved as a `.csv` file
* Done! You can import the CSV file into Excel for easy viewing.

---

## 🛠️ Developer Setup

### 1. Installation

```
git clone https://github.com/SzymonChirowski242621/lead-finder.git
cd lead-finder

pip install -r requirements.txt
```

Or using **uv**:

```
uv sync
```

---

### 2. Code Quality

```
pre-commit install
pre-commit run --all-files
```

Tools used:

* **Black** – formatting
* **Flake8** – style
* **Mypy** – static typing

---

## 🍻 Support

If this tool saved you time (or money on leads), you can buy me a beer when you meet me in person! Cheers! 🍺

---

## ⚠️ Legal & Ethical Notice

* **GDPR:**
  Collects publicly available business data. Generic business emails are generally allowed for B2B outreach in the EU. Personal emails might require consent.

* **Terms of Service:**
  Automated scraping may violate website ToS. Use responsibly.
* **License:** This project is open-source under the MIT License. Use at your own risk. See LICENSE file for details.
