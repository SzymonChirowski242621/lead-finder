import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import csv
import time
import os
from typing import List, Dict

# Import your existing logic
from search_clients import get_search_results
from scraper import setup_driver, scrape_domain


class LeadScraperApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Robotic Intern - Lead Scraper")
        self.root.geometry("600x600")  # Made slightly taller for new inputs

        # --- Style ---
        style = ttk.Style()
        style.configure("TButton", font=("Helvetica", 10), padding=5)
        style.configure("TLabel", font=("Helvetica", 10))

        # --- Input Frame ---
        input_frame = ttk.LabelFrame(root, text="Configuration", padding=10)
        input_frame.pack(fill="x", padx=10, pady=5)

        # 1. Search Query
        ttk.Label(input_frame, text="Search Query:").pack(anchor="w")
        self.keyword_entry = ttk.Entry(input_frame, width=50)
        self.keyword_entry.pack(fill="x", pady=(0, 10))
        self.keyword_entry.insert(0, "Firma budowlana Warszawa")

        # 2. Max Results
        ttk.Label(input_frame, text="Max Results:").pack(anchor="w")
        self.limit_entry = ttk.Entry(input_frame, width=15)
        self.limit_entry.pack(anchor="w", pady=(0, 10))
        self.limit_entry.insert(0, "5")

        # 3. Output Location (NEW)
        ttk.Label(input_frame, text="Save Location:").pack(anchor="w")

        file_frame = ttk.Frame(input_frame)
        file_frame.pack(fill="x", pady=(0, 10))

        self.filepath_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_frame, textvariable=self.filepath_var)
        self.file_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        browse_btn = ttk.Button(file_frame, text="Browse...", command=self.browse_file)
        browse_btn.pack(side="right")

        # Set a default "Auto" filename initially
        self.generate_default_filename()

        # Start Button
        self.start_btn = ttk.Button(
            input_frame, text="Start Scraping", command=self.start_thread
        )
        self.start_btn.pack(fill="x", pady=5)

        # --- Log Section ---
        log_frame = ttk.LabelFrame(root, text="Process Log", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.log_area = scrolledtext.ScrolledText(
            log_frame, state="disabled", height=15, font=("Consolas", 9)
        )
        self.log_area.pack(fill="both", expand=True)

        # Status Bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(
            root, textvariable=self.status_var, relief="sunken", anchor="w"
        )
        self.status_bar.pack(fill="x", side="bottom")

    def generate_default_filename(self) -> None:
        """Sets the default filename with a timestamp."""
        default_name = f"leads_{int(time.time())}.csv"
        # Use absolute path to avoid confusion
        full_path = os.path.join(os.getcwd(), default_name)
        self.filepath_var.set(full_path)

    def browse_file(self) -> None:
        """Opens a dialog to choose save location."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            initialfile=f"leads_{int(time.time())}.csv",
            title="Save Leads As",
        )
        if filename:
            self.filepath_var.set(filename)

    def log(self, message: str) -> None:
        def _update() -> None:
            self.log_area.config(state="normal")
            self.log_area.insert(tk.END, message + "\n")
            self.log_area.see(tk.END)
            self.log_area.config(state="disabled")

        self.root.after(0, _update)

    def start_thread(self) -> None:
        keyword = self.keyword_entry.get()
        filepath = self.filepath_var.get()

        try:
            limit = int(self.limit_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Limit must be a number.")
            return

        if not keyword:
            messagebox.showerror("Error", "Please enter a search query.")
            return

        if not filepath:
            messagebox.showerror("Error", "Please define a save location.")
            return

        self.start_btn.config(state="disabled")
        self.status_var.set("Running...")
        self.log_area.config(state="normal")
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state="disabled")

        thread = threading.Thread(
            target=self.run_process, args=(keyword, limit, filepath), daemon=True
        )
        thread.start()

    def run_process(self, keyword: str, limit: int, filepath: str) -> None:
        results: List[Dict[str, str]] = []

        try:
            self.log(f"--- Phase 1: Finding Companies for '{keyword}' ---")
            domains = get_search_results(keyword, num_results=limit)
            self.log(f"Found {len(domains)} unique companies.")

            if not domains:
                self.log("No domains found. Stopping.")
                return

            self.log("\n--- Phase 2: Extracting Contact Info ---")
            driver = setup_driver()

            try:
                for i, domain in enumerate(domains):
                    self.log(f"[{i+1}/{len(domains)}] Visiting {domain}...")

                    data = scrape_domain(driver, domain)

                    row = {
                        "Domain": domain,
                        "Emails": ", ".join(data["emails"]),
                        "Phones": ", ".join(data["phones"]),
                        "Address Snippet": (
                            list(data["address"])[0] if data["address"] else ""
                        ),
                    }
                    results.append(row)

                    if data["emails"]:
                        self.log(f"   + Emails: {row['Emails']}")
                    if data["phones"]:
                        self.log(f"   + Phones: {row['Phones']}")

                    time.sleep(1)

            finally:
                driver.quit()
                self.log("Browser closed.")

            self.save_to_csv(results, filepath)
            self.log(f"\n[SUCCESS] Saved data to: {filepath}")
            messagebox.showinfo("Success", f"Done! Saved {len(results)} leads.")

        except Exception as e:
            self.log(f"CRITICAL ERROR: {e}")
            messagebox.showerror("Error", str(e))

        finally:
            self.root.after(0, lambda: self.start_btn.config(state="normal"))
            self.root.after(0, lambda: self.status_var.set("Ready"))
            # Update the default filename for the next run so we don't overwrite
            self.root.after(0, self.generate_default_filename)

    def save_to_csv(self, data: List[Dict[str, str]], filename: str) -> None:
        if not data:
            return
        headers = ["Domain", "Emails", "Phones", "Address Snippet"]
        try:
            with open(filename, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                for row in data:
                    writer.writerow(row)
        except IOError as e:
            self.log(f"Error saving file: {e}")
            raise


if __name__ == "__main__":
    root = tk.Tk()
    app = LeadScraperApp(root)
    root.mainloop()
