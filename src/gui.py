import csv
import os
import queue
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Dict, List, Optional, Set

# Import modules
from search_clients import get_search_results
from scraper import scrape_domain, setup_driver
from event_scraper import get_event_domains


class LeadScraperApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Robotic Intern - Lead Scraper (Multi-Threaded)")
        self.root.geometry("750x800")

        style = ttk.Style()
        style.configure("TButton", font=("Helvetica", 10), padding=5)

        # --- Input Frame ---
        input_frame = ttk.LabelFrame(root, text="Configuration", padding=10)
        input_frame.pack(fill="x", padx=10, pady=5)

        # 1. Mode Selection
        ttk.Label(input_frame, text="Source Mode:").pack(anchor="w")
        self.mode_var = tk.StringVar(value="Keyword Search")
        self.mode_combo = ttk.Combobox(
            input_frame,
            textvariable=self.mode_var,
            values=[
                "Keyword Search",
                "Scrape Event URL",
                "Import Domain List (CSV/TXT)",
            ],
            state="readonly",
            width=40,
        )
        self.mode_combo.pack(anchor="w", pady=(0, 10))
        self.mode_combo.bind("<<ComboboxSelected>>", self.toggle_inputs)

        # 2. Main Input Frame
        self.dynamic_frame = ttk.Frame(input_frame)
        self.dynamic_frame.pack(fill="x", pady=(0, 10))

        # Initialize Inputs
        self.input_entry = ttk.Entry(self.dynamic_frame, width=50)
        self.input_label = ttk.Label(self.dynamic_frame, text="Search Query:")
        self.browse_btn = ttk.Button(
            self.dynamic_frame, text="Browse...", command=self.browse_import_file
        )

        # Limit Input & Thread Input
        self.settings_frame = ttk.Frame(input_frame)
        self.settings_frame.pack(anchor="w", pady=(0, 10))

        # Max Results / Pages
        self.limit_lbl = ttk.Label(self.settings_frame, text="Max Results:")
        self.limit_entry = ttk.Entry(self.settings_frame, width=10)
        self.limit_entry.insert(0, "50")

        # Threads
        ttk.Label(self.settings_frame, text="   Active Bots (Threads):").pack(
            side="left"
        )
        self.thread_entry = ttk.Entry(self.settings_frame, width=5)
        self.thread_entry.insert(0, "4")
        self.thread_entry.pack(side="left", padx=5)

        self.thread_entry.bind("<KeyRelease>", self.update_thread_warning)

        # Dynamic Warning Label
        self.warning_label = tk.Label(
            self.settings_frame,
            text="✅ Safe Mode",
            fg="green",
            font=("Helvetica", 9, "bold"),
        )
        self.warning_label.pack(side="left", padx=10)

        # --- Output Format Options ---
        self.format_frame = ttk.Frame(input_frame)
        self.format_frame.pack(anchor="w", pady=(5, 0))

        # Checkbox 1: Explode (Excel Friendly)
        self.explode_var = tk.BooleanVar(value=True)
        self.explode_chk = ttk.Checkbutton(
            self.format_frame,
            text="Excel Friendly (One email per row)",
            variable=self.explode_var,
        )
        self.explode_chk.pack(side="left")

        # Checkbox 2: Deduplicate (NEW!)
        self.dedupe_var = tk.BooleanVar(value=True)
        self.dedupe_chk = ttk.Checkbutton(
            self.format_frame,
            text="Remove Duplicates",
            variable=self.dedupe_var,
        )
        self.dedupe_chk.pack(side="left", padx=10)

        # Default View
        self.toggle_inputs()

        # 3. Save Location
        ttk.Label(input_frame, text="Save Results To:").pack(anchor="w")
        save_file_row = ttk.Frame(input_frame)
        save_file_row.pack(fill="x", pady=(0, 10))

        self.save_path_var = tk.StringVar()
        self.save_entry = ttk.Entry(save_file_row, textvariable=self.save_path_var)
        self.save_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        ttk.Button(save_file_row, text="Browse...", command=self.browse_save_file).pack(
            side="right"
        )
        self.generate_default_filename()

        # Start Button
        self.start_btn = ttk.Button(
            input_frame, text="Start Robotic Intern Fleet", command=self.start_thread
        )
        self.start_btn.pack(fill="x", pady=10)

        # --- Log Section ---
        log_frame = ttk.LabelFrame(root, text="Process Log", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.log_area = scrolledtext.ScrolledText(
            log_frame, state="disabled", height=15, font=("Consolas", 9)
        )
        self.log_area.pack(fill="both", expand=True)

        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(
            root, textvariable=self.status_var, relief="sunken", anchor="w"
        )
        self.status_bar.pack(fill="x", side="bottom")

    def update_thread_warning(self, event: Optional[tk.Event] = None) -> None:
        try:
            val_str = self.thread_entry.get()
            if not val_str:
                self.warning_label.config(text="", fg="black")
                return
            val = int(val_str)
            if val <= 4:
                self.warning_label.config(text="✅ Safe Mode (Low RAM)", fg="green")
            elif 5 <= val <= 9:
                self.warning_label.config(
                    text="⚠️ High Performance (Fans might spin)", fg="#d35400"
                )
            else:
                self.warning_label.config(text="🔥 DANGER: May freeze PC!", fg="red")
        except ValueError:
            self.warning_label.config(text="❌ Invalid Number", fg="red")

    def toggle_inputs(self, event: Optional[tk.Event] = None) -> None:
        mode = self.mode_var.get()

        for widget in self.dynamic_frame.winfo_children():
            widget.pack_forget()

        self.limit_lbl.pack(side="left")
        self.limit_entry.pack(side="left", padx=5)

        if mode == "Keyword Search":
            self.input_label.config(text="Search Query:")
            self.input_label.pack(anchor="w")
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, "Firma budowlana Warszawa")
            self.input_entry.pack(fill="x")
            self.limit_lbl.config(text="Max Results:")

        elif mode == "Scrape Event URL":
            self.input_label.config(text="Event Website URL (with ?page=1):")
            self.input_label.pack(anchor="w")
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(
                0,
                "https://light-building.messefrankfurt.com/frankfurt/en/exhibitor-search.html?page=1",  # noqa E501
            )
            self.input_entry.pack(fill="x")
            self.limit_lbl.config(text="Pages to Scan:")
            self.limit_entry.delete(0, tk.END)
            self.limit_entry.insert(0, "5")

        elif "Import" in mode:
            self.input_label.config(text="Select File (.csv/.txt):")
            self.input_label.pack(anchor="w")
            self.input_entry.delete(0, tk.END)
            self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
            self.browse_btn.pack(side="right")
            self.limit_lbl.pack_forget()
            self.limit_entry.pack_forget()

    def generate_default_filename(self) -> None:
        default_name = f"leads_{int(time.time())}.csv"
        self.save_path_var.set(os.path.join(os.getcwd(), default_name))

    def browse_save_file(self) -> None:
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            initialfile=f"leads_{int(time.time())}.csv",
            title="Save Leads As",
        )
        if filename:
            self.save_path_var.set(filename)

    def browse_import_file(self) -> None:
        filename = filedialog.askopenfilename(
            filetypes=[("CSV/TXT Files", "*.csv *.txt"), ("All Files", "*.*")],
            title="Select Domain List",
        )
        if filename:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, filename)

    def log(self, message: str) -> None:
        def _update() -> None:
            self.log_area.config(state="normal")
            self.log_area.insert(tk.END, message + "\n")
            self.log_area.see(tk.END)
            self.log_area.config(state="disabled")

        self.root.after(0, _update)

    def start_thread(self) -> None:
        mode = self.mode_var.get()
        input_val = self.input_entry.get()
        save_path = self.save_path_var.get()
        limit = 0
        threads = 1

        if not input_val:
            messagebox.showerror("Error", "Input cannot be empty.")
            return

        try:
            threads = int(self.thread_entry.get())
            if threads < 1:
                threads = 1
            if threads >= 10:
                if not messagebox.askyesno(
                    "Warning",
                    f"⚠️ You chose {threads} bots.\nAre you sure you want to continue?",
                ):
                    return
        except ValueError:
            messagebox.showerror("Error", "Threads must be a number.")
            return

        if mode != "Import Domain List (CSV/TXT)":
            try:
                limit = int(self.limit_entry.get())
            except ValueError:
                messagebox.showerror("Error", "Limit/Pages must be a number.")
                return

        self.start_btn.config(state="disabled")
        self.status_var.set(f"Running with {threads} bots...")
        self.log_area.config(state="normal")
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state="disabled")

        explode = self.explode_var.get()
        dedupe = self.dedupe_var.get()

        thread = threading.Thread(
            target=self.run_process,
            args=(mode, input_val, limit, threads, save_path, explode, dedupe),
            daemon=True,
        )
        thread.start()

    def run_process(
        self,
        mode: str,
        input_val: str,
        limit: int,
        num_threads: int,
        save_path: str,
        explode_emails: bool,
        dedupe_emails: bool,
    ) -> None:
        results: List[Dict[str, str]] = []
        domains: List[str] = []

        # Shared memory for deduplication
        seen_emails: Set[str] = set()

        try:
            # --- PHASE 1 ---
            if mode == "Keyword Search":
                self.log(f"--- Phase 1: Keyword Search '{input_val}' ---")
                domains = get_search_results(input_val, num_results=limit)
            elif mode == "Scrape Event URL":
                self.log(f"--- Phase 1: Scraping Event ({limit} pages) ---")
                domains = get_event_domains(
                    input_val, max_pages=limit, log_callback=self.log
                )
            elif "Import" in mode:
                self.log("--- Phase 1: Loading File ---")
                try:
                    with open(input_val, "r", encoding="utf-8") as f:
                        reader = csv.reader(f)
                        for row in reader:
                            if row:
                                clean = (
                                    row[0]
                                    .replace("https://", "")
                                    .replace("www.", "")
                                    .strip()
                                )
                                if clean and "." in clean:
                                    domains.append(clean)
                    self.log(f"Loaded {len(domains)} domains.")
                except Exception as e:
                    self.log(f"File Error: {e}")
                    return

            if not domains:
                self.log("No domains found. Stopping.")
                return

            # --- PHASE 2 ---
            self.log(f"\n--- Phase 2: Launching {num_threads} Bots ---")

            domain_queue: queue.Queue[str] = queue.Queue()
            for d in domains:
                domain_queue.put(d)

            results_lock = threading.Lock()

            def worker(bot_id: int) -> None:
                driver = setup_driver()
                try:
                    while True:
                        try:
                            domain = domain_queue.get_nowait()
                        except queue.Empty:
                            break

                        self.log(f"[Bot-{bot_id}] Visiting {domain}...")
                        try:
                            data = scrape_domain(driver, domain)

                            company_name = data.get("name", "Unknown").replace(
                                "\n", " "
                            )

                            with results_lock:
                                # 1. Deduplication Logic
                                final_emails = []
                                if dedupe_emails:
                                    for email in data["emails"]:
                                        email_lower = email.lower()
                                        if email_lower not in seen_emails:
                                            seen_emails.add(email_lower)
                                            final_emails.append(email)
                                else:
                                    final_emails = list(data["emails"])

                                has_emails = bool(final_emails)
                                missing_flag = "NO" if has_emails else "YES"

                                # 2. Row Generation
                                rows_to_add = []

                                if explode_emails and has_emails:
                                    # Exploded Mode (One row per email)
                                    for email in final_emails:
                                        rows_to_add.append(
                                            {
                                                "Company Name": company_name,
                                                "Domain": domain,
                                                "Emails": email,
                                                "Email Missing": "NO",
                                            }
                                        )
                                else:
                                    # Compact Mode or No Emails
                                    rows_to_add.append(
                                        {
                                            "Company Name": company_name,
                                            "Domain": domain,
                                            "Emails": ", ".join(final_emails),
                                            "Email Missing": missing_flag,
                                        }
                                    )

                                results.extend(rows_to_add)

                            if has_emails:
                                self.log(
                                    f"[Bot-{bot_id}] + Emails Found: {len(final_emails)}"  # noqa E501
                                )

                        except Exception as e:
                            self.log(f"[Bot-{bot_id}] Error: {e}")
                        finally:
                            domain_queue.task_done()
                except Exception as e:
                    self.log(f"[Bot-{bot_id}] CRASHED: {e}")
                finally:
                    driver.quit()

            threads_list = []
            for i in range(num_threads):
                t = threading.Thread(target=worker, args=(i + 1,))
                t.start()
                threads_list.append(t)

            for t in threads_list:
                t.join()

            self.log("All bots finished.")
            self.save_to_csv(results, save_path)
            self.log(f"\n[SUCCESS] Saved {len(results)} rows to: {save_path}")
            messagebox.showinfo("Success", f"Done! Saved {len(results)} rows.")

        except Exception as e:
            self.log(f"CRITICAL ERROR: {e}")
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
        finally:
            self.root.after(0, lambda: self.start_btn.config(state="normal"))
            self.root.after(0, lambda: self.status_var.set("Ready"))

    def save_to_csv(self, data: List[Dict[str, str]], filename: str) -> None:
        if not data:
            return
        headers = ["Company Name", "Domain", "Emails", "Email Missing"]

        # USE SEMICOLON DELIMITER FOR EUROPEAN EXCEL COMPATIBILITY
        with open(filename, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers, delimiter=";")
            writer.writeheader()
            for row in data:
                writer.writerow(row)


if __name__ == "__main__":
    root = tk.Tk()
    app = LeadScraperApp(root)
    root.mainloop()
