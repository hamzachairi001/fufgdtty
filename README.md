# Google Maps Business Finder

A web application that scrapes real business information from Google Maps for a specified city and search query.

## Features

- Search for businesses in any city
- Automatically retrieves real business information including:
  - Business name
  - Address
  - Phone number
- Modern and responsive UI
- Random selection from available results

## Prerequisites

- Python 3.7 or higher
- Chrome browser installed
- pip (Python package manager)

## Installation

1. Clone this repository or download the files
2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the Flask application:
   ```bash
   python app.py
   ```
2. Open your web browser and navigate to `http://localhost:5000`
3. Enter a city (default is Hamburg) and a search query (default is "barber")
4. Click the "Search" button to get random business information

## Note

This application uses Selenium WebDriver to scrape Google Maps data. Please be mindful of Google's terms of service and rate limiting when using this application. 