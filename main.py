import tkinter as tk
from tkinter import ttk, messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, InvalidSessionIdException
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from bs4 import BeautifulSoup
import time
import pandas as pd
import os
import re
import logging
import requests
from urllib.parse import urljoin, urlparse
from threading import Thread

# Configure logging
logging.basicConfig(filename='scraping.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s: %(message)s')

filename = "data.csv"

# Function to extract email from a page
def extract_email_from_page(content):
    soup = BeautifulSoup(content, 'html.parser')
    email_element = soup.find('a', href=lambda href: href and href.startswith('mailto:'))
    if email_element:
        return email_element['href'].split(':')[1]
    return None

# Function to extract emails from the entire website
def extract_email_from_website(url):
    try:
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        email = extract_email_from_page(response.content)
        if email:
            return email

        links_to_visit = set()
        for link in soup.find_all('a', href=True):
            href = link['href']
            if urlparse(href).netloc:
                full_url = href
            else:
                full_url = urljoin(url, href)
            if urlparse(full_url).netloc == urlparse(url).netloc:
                links_to_visit.add(full_url)

        for link in links_to_visit:
            try:
                response = requests.get(link, headers=headers, timeout=10)
                response.raise_for_status()
                email = extract_email_from_page(response.content)
                if email:
                    return email
            except requests.RequestException as e:
                logging.error(f"Error fetching content from {link}: {e}")
                continue

        return "Email not found"
    except requests.RequestException as e:
        logging.error(f"Error fetching website content for {url}: {e}")
        return None

# Function to scroll through Google Maps search results and extract data
def scroll_and_extract_data(browser, progress_var, progress_bar, tree, display_button):
    try:
        if os.path.exists(filename):
            df = pd.read_csv(filename)
        else:
            df = pd.DataFrame(columns=['Name', 'Phone', 'Address', 'Website', 'Email']) 

        action = ActionChains(browser)
        WebDriverWait(browser, 90).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "hfpxzc")))

        records = []
        scraped_elements = set()

        total_elements = 0
        while True:
            elements = browser.find_elements(By.CLASS_NAME, "hfpxzc")
            total_elements += len(elements)
            elements = [el for el in elements if el not in scraped_elements]

            if not elements:
                break

            for element in elements:
                try:
                    scroll_origin = ScrollOrigin.from_element(element)
                    action.scroll_from_origin(scroll_origin, 0, 200).perform()
                    action.move_to_element(element).perform()

                    WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "hfpxzc")))
                    browser.execute_script("arguments[0].click();", element)
                    WebDriverWait(browser, 15).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "Io6YTe")))

                    source = browser.page_source
                    soup = BeautifulSoup(source, 'html.parser')

                    name_html = soup.find('h1', {"class": "DUwDvf lfPIob"})
                    name = name_html.text.strip() if name_html else "Not available"

                    divs = soup.findAll('div', {"class": "Io6YTe"})
                    phone = next((div.text for div in divs if div.text.startswith(("+", "03"))), "Not available")
                    address = next((div.text for div in divs if re.search(r'\d{1,4}\s[\w\s]+\s(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Square|Sq|Place|Pl|Court|Ct),?\s[\w\s]+,\s[A-Z]{2}\s\d{5}', div.text)), "Not available")
                    website = next((div.text for div in divs if re.search(r'\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b', div.text)), "Not available")

                    if website != "Not available":
                        email = extract_email_from_website(website)
                    else:
                        email = "Not available"

                    records.append({'Name': name, 'Phone': phone, 'Address': address, 'Website': website, 'Email': email})
                    scraped_elements.add(element)

                    # Insert the new data into the treeview
                    tree.insert("", "end", values=(name, phone, address, website, email))
                    progress_var.set((len(scraped_elements) / total_elements) * 100)
                    progress_bar.update()
                except (TimeoutException, StaleElementReferenceException) as e:
                    logging.error(f"Error: {e}. Retrying...")
                    continue
                except InvalidSessionIdException as e:
                    logging.error(f"Invalid session id: {e}. Exiting...")
                    return
                except Exception as e:
                    logging.error(f"Error: {e}. Skipping element.")
                    continue

            try:
                scroll_origin = ScrollOrigin.from_element(elements[-1])
                action.scroll_from_origin(scroll_origin, 0, 8000).perform()
                time.sleep(2)
            except (IndexError, StaleElementReferenceException) as e:
                logging.error(f"Error scrolling: {e}. Exiting...")
                break

        new_df = pd.DataFrame(records)
        df = pd.concat([df, new_df], ignore_index=True).drop_duplicates()
        df.to_csv(filename, index=False)
    except InvalidSessionIdException as e:
        logging.error(f"Invalid session id: {e}. Exiting...")
    finally:
        display_button.config(state=tk.NORMAL)  # Re-enable the display button after scraping is complete

# Function to start scraping
def start_scraping():
    search_query = search_entry.get()
    location = location_entry.get()
    if not search_query or not location:
        messagebox.showerror("Input Error", "Please enter both search query and location.")
        return

    link = f"https://www.google.com/maps/search/{search_query}+in+{location}"

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--log-level=3")

    try:
        browser = webdriver.Chrome(options=chrome_options)
        browser.get(str(link))
        progress_var.set(0)
        display_button.config(state=tk.DISABLED)  # Disable the display button during scraping
        scraping_thread = Thread(target=scroll_and_extract_data, args=(browser, progress_var, progress_bar, tree, display_button))
        scraping_thread.start()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load browser: {e}")

# Function to display data in the table
def display_data():
    # Check if data is currently displayed
    if not tree.get_children():
        # Data is not displayed, so display it
        if os.path.exists(filename):
            df = pd.read_csv(filename)
            for i, row in df.iterrows():
                tree.insert("", "end", values=list(row))
        else:
            messagebox.showerror("File Error", "No data available. Please start the scraping first.")
    else:
        # Data is currently displayed, so clear the treeview
        for i in tree.get_children():
            tree.delete(i)


# Set up the Tkinter window
window = tk.Tk()
window.title("Web Scraping GUI")
window.geometry("1200x800")

frame = ttk.Frame(window, padding="10")
frame.pack(fill="both", expand=True)

# Input fields
ttk.Label(frame, text="Search Query:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
search_entry = ttk.Entry(frame, width=40)
search_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

ttk.Label(frame, text="Location:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
location_entry = ttk.Entry(frame, width=40)
location_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

# Progress bar
progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(frame, variable=progress_var, maximum=100)
progress_bar.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

# Start button
start_button = ttk.Button(frame, text="Start Scraping", command=start_scraping)
start_button.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

# Display button
display_button = ttk.Button(frame, text="Display Data", command=display_data)
display_button.grid(row=3, column=2, padx=5, pady=5)

# Treeview for displaying data
columns = ("Name", "Phone", "Address", "Website", "Email")
tree = ttk.Treeview(frame, columns=columns, show="headings")
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, minwidth=0, width=120, stretch=True)
tree.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

# Make the table expandable
frame.grid_rowconfigure(4, weight=1)
frame.grid_columnconfigure(1, weight=1)

window.mainloop()
