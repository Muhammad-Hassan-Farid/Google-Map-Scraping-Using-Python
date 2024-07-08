# Web Scraping GUI

This Python application utilizes Selenium and BeautifulSoup for web scraping, along with Tkinter for creating a graphical user interface (GUI). The program is designed to scrape data from Google Maps search results based on user input.

## Features

- **Search Query**: Allows the user to specify a search query.
- **Location**: Allows the user to specify a location for the search.
- **Chrome Profile**: Option to use a specific Chrome user profile for scraping.
- **Start Scraping**: Initiates the scraping process using Selenium to interact with Google Maps.
- **Display Data**: Displays scraped data in a table using Tkinter's Treeview widget.
- **Progress Bar**: Shows the progress of scraping operation.
- **Error Logging**: Logs errors encountered during scraping to `scraping.log`.

## Dependencies

- **Python Libraries**:
  - `tkinter`: GUI library for Python.
  - `selenium`: Web automation library for Python.
  - `beautifulsoup4`: Library for parsing HTML and XML documents.
  - `pandas`: Data manipulation library for Python.
  - `requests`: HTTP library for Python.
  - `webdriver_manager`: Helps manage WebDriver binaries.

## Installation

1. **Install Python**: Make sure you have Python installed. You can download it from [python.org](https://www.python.org/downloads/).

2. **Install Required Packages**: Use the following command to install necessary Python packages:

```bash
pip install selenium beautifulsoup4 pandas requests webdriver_manager
````
3. **Chrome WebDriver**: Ensure you have Chrome WebDriver installed. If not, it will be automatically managed by `webdriver_manager`.

## Usage

1. **Run the Application**: Execute the script by running `python main.py`

2. **Input Search Query and Location**: Enter a search query and location in the respective fields.

3. **Start Scraping**: Click on the "Start Scraping" button to begin the scraping process.

4. **Display Data**: After scraping, click on the "Display Data" button to view the scraped data in the table.

## Notes

- **Chrome Profile**: If you have a specific Chrome user profile you want to use, specify its path in the "Chrome Profile" field. This will load your saved settings, extensions, and history into the scraping session.
- **Logging**: Errors encountered during scraping are logged to `scraping.log` for debugging purposes.
- **Headless Mode**: By default, scraping runs in headless mode (without opening a visible browser window). Remove the `headless` argument in Chrome options (`start_scraping` function) to view the browser interaction.
