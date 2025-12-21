# Lead Finder (The Robotic Intern) 🤖

A specialized B2B lead generation tool designed to automate the process of finding contact information for business niches in Poland and the Netherlands.

It acts as a "Robotic Intern": it searches for companies, visits their websites, scans for contact details (Emails, Phone Numbers, Addresses), and saves everything to a neat CSV file.

---

## 🚀 Features

* **Smart Search:** Uses DuckDuckGo to find company domains while avoiding Google's anti-bot bans.
* **Junk Filtering:** Automatically ignores directories (Oferteo, Yelp, OLX), social media, and aggregators to focus on *real* company websites.
* **Deep Scraping:** Visits homepages and sub-pages (e.g., `/kontakt`, `/about`, `/o-nas`) to find hidden details.
* **Polish-Optimized:** Specialized Regex patterns to catch Polish phone formats (landlines & mobile) and addresses via Zip Codes.
* **Battery-Included:** Simple "Click-to-Run" launcher (`start.bat`) that handles installation automatically.

---

## 📦 How to Use (For Users)

**Prerequisites:**
1.  **Google Chrome** must be installed.
2.  **Python** (3.10 or newer) must be installed. [Download Here](https://www.python.org/downloads/) (Make sure to check *"Add Python to PATH"* during installation).

**Running the Tool:**

1.  **Get the Code:**
    * Click the green **Code** button on this page and select **Download ZIP** (then extract it).
    * *OR* Run in terminal: `git clone https://github.com/SzymonChirowski242621/lead-finder.git` and navigate into the folder.

2.  **Start the App:**
    * Open the folder.
    * Double-click the **`start.bat`** file.
    * *Note: The first time you run it, it will take 1-2 minutes to install necessary libraries.*

3.  **Use the Interface:**
    * **Search Query:** Enter a niche (e.g., *"Hurtownia zabawek Poznań"*).
    * **Max Results:** How many companies to find (start with 5-10 to test).
    * **Save Location:** Choose where to save your `.csv` file.
    * Click **Start Scraping**.

---

## 🛠️ Developer Setup

If you want to contribute or modify the code, this project follows modern Python standards using strict linting.

### 1. Installation
This project supports both standard `pip` and `uv` (faster).

```bash
# Clone the repository
git clone https://github.com/SzymonChirowski242621/lead-finder.git
cd lead-finder

# Install dependencies (Standard way)
pip install -r requirements.txt

# OR (Modern way with uv)
uv sync

```

### 2. Project Structure

```text
lead-finder/
├── src/
│   ├── gui.py             # The Tkinter User Interface
│   ├── main.py            # CLI Entry point (optional)
│   ├── scraper.py         # Selenium logic & Regex extraction
│   └── search_clients.py  # DuckDuckGo search & Domain filtering
├── start.bat              # Auto-installer & Launcher for end-users
├── requirements.txt       # Production dependencies
└── README.md              # Documentation

```

### 3. Code Quality

The code is enforced with strict linting rules. Before committing changes, run:

```bash
# Install hooks
pre-commit install

# Run checks manually
pre-commit run --all-files

```

* **Black:** Code formatting
* **Flake8:** Style guide enforcement
* **Mypy:** Static type checking

---

## ⚠️ Legal & Ethical Notice

* **GDPR Compliance:** This tool collects public business data. In the EU, emailing generic business addresses (`info@company.com`) is generally permissible for B2B outreach, but emailing personal addresses (`name.surname@company.com`) requires consent.
* **Terms of Service:** Automated scraping may violate the ToS of certain websites. Use responsibly. The bot includes built-in delays (`time.sleep`) to be polite to servers.
* **License:** This project is open-source under the MIT License. Use at your own risk. See `LICENSE` file for details.

---
## 🍻 Support

If this tool saved you time (or money on leads), you can buy me a beer when you meet me in person! Cheers! 🍺
