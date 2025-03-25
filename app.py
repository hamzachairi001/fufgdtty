from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
import logging
import os
import re
import requests
import json
from functools import lru_cache

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# API configuration
NINJAS_API_KEY = 'YOUR_API_KEY'  # You'll need to get an API key from api-ninjas.com
CITIES_CACHE_FILE = 'cities_cache.json'

# German names data
GERMAN_MALE_FIRST_NAMES = [
    "Alexander", "Andreas", "Benjamin", "Christian", "Daniel", "David", "Erik", "Felix", 
    "Florian", "Hans", "Jan", "Johannes", "Klaus", "Lars", "Lukas", "Martin", "Michael", 
    "Niklas", "Oliver", "Peter", "Sebastian", "Stefan", "Thomas", "Tim", "Wolfgang"
]

GERMAN_FEMALE_FIRST_NAMES = [
    "Anna", "Brigitte", "Christina", "Diana", "Elena", "Emma", "Franziska", "Hannah", 
    "Heike", "Ingrid", "Julia", "Katharina", "Laura", "Lisa", "Maria", "Marie", "Nina", 
    "Paula", "Sabine", "Sandra", "Sofia", "Susanne", "Tanja", "Ursula", "Victoria"
]

GERMAN_LAST_NAMES = [
    "Bauer", "Fischer", "Hoffmann", "Klein", "Koch", "Krause", "Lange", "Lehmann", 
    "Meyer", "Müller", "Neumann", "Peters", "Richter", "Schmidt", "Schneider", "Schröder", 
    "Schulz", "Schwarz", "Wagner", "Weber", "Werner", "Wolf", "Zimmermann"
]

# Country and city data
COUNTRIES_AND_CITIES = {
    "United Kingdom": [
        "London", "Manchester", "Birmingham", "Leeds", "Liverpool", 
        "Newcastle upon Tyne", "Sheffield", "Nottingham", "Bristol", 
        "Leicester", "Cardiff", "Belfast", "Edinburgh", "Aberdeen"
    ],
    "United States": [
        "New York", "Los Angeles", "Chicago", "Houston", "Phoenix", 
        "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose",
        "Austin", "Jacksonville", "Fort Worth", "Columbus", "San Francisco",
        "Charlotte", "Indianapolis", "Seattle", "Denver", "Boston"
    ],
    "Germany": [
        "Berlin", "Hamburg", "Munich", "Cologne", "Frankfurt am Main",
        "Stuttgart", "Düsseldorf", "Leipzig", "Dortmund", "Essen",
        "Bremen", "Dresden", "Hanover", "Nuremberg", "Duisburg",
        "Bochum", "Wuppertal", "Bielefeld", "Bonn", "Münster"
    ],
    "France": [
        "Paris", "Marseille", "Lyon", "Toulouse", "Nice",
        "Nantes", "Strasbourg", "Montpellier", "Bordeaux", "Lille",
        "Rennes", "Reims", "Saint-Étienne", "Toulon", "Le Havre",
        "Grenoble", "Dijon", "Angers", "Nîmes", "Villeurbanne"
    ],
    "Spain": [
        "Madrid", "Barcelona", "Valencia", "Seville", "Zaragoza",
        "Málaga", "Murcia", "Palma de Mallorca", "Las Palmas", "Bilbao",
        "Alicante", "Córdoba", "Valladolid", "Vigo", "Gijón",
        "L'Hospitalet", "Vitoria-Gasteiz", "Granada", "Elche", "Oviedo"
    ],
    "Italy": [
        "Rome", "Milan", "Naples", "Turin", "Palermo",
        "Genoa", "Bologna", "Florence", "Bari", "Catania",
        "Venice", "Verona", "Messina", "Padua", "Trieste",
        "Brescia", "Parma", "Taranto", "Prato", "Modena"
    ],
    "Netherlands": [
        "Amsterdam", "Rotterdam", "The Hague", "Utrecht", "Eindhoven",
        "Groningen", "Tilburg", "Almere", "Breda", "Nijmegen",
        "Enschede", "Haarlem", "Arnhem", "Zaanstad", "Amersfoort",
        "Apeldoorn", "Hertogenbosch", "Hoofddorp", "Maastricht", "Leiden"
    ],
    "Poland": [
        "Warsaw", "Kraków", "Łódź", "Wrocław", "Poznań",
        "Gdańsk", "Szczecin", "Bydgoszcz", "Lublin", "Katowice",
        "Białystok", "Gdynia", "Częstochowa", "Radom", "Sosnowiec",
        "Toruń", "Kielce", "Rzeszów", "Gliwice", "Zabrze"
    ],
    "Sweden": [
        "Stockholm", "Gothenburg", "Malmö", "Uppsala", "Västerås",
        "Örebro", "Linköping", "Helsingborg", "Jönköping", "Norrköping",
        "Lund", "Umeå", "Gävle", "Borås", "Södertälje",
        "Eskilstuna", "Halmstad", "Växjö", "Karlstad", "Sundsvall"
    ],
    "Norway": [
        "Oslo", "Bergen", "Trondheim", "Stavanger", "Drammen",
        "Fredrikstad", "Kristiansand", "Sandnes", "Tromsø", "Sarpsborg",
        "Skien", "Ålesund", "Sandefjord", "Haugesund", "Moss",
        "Porsgrunn", "Tønsberg", "Bodø", "Arendal", "Hamar"
    ],
    "Denmark": [
        "Copenhagen", "Aarhus", "Odense", "Aalborg", "Frederiksberg",
        "Esbjerg", "Gentofte", "Gladsaxe", "Randers", "Kolding",
        "Horsens", "Vejle", "Roskilde", "Herning", "Høje-Taastrup",
        "Silkeborg", "Næstved", "Greve", "Køge", "Holbæk"
    ],
    "Finland": [
        "Helsinki", "Espoo", "Tampere", "Vantaa", "Oulu",
        "Turku", "Jyväskylä", "Lahti", "Kuopio", "Pori",
        "Kouvola", "Joensuu", "Lappeenranta", "Hämeenlinna", "Vaasa",
        "Seinäjoki", "Rovaniemi", "Mikkeli", "Kotka", "Salo"
    ],
    "Ireland": [
        "Dublin", "Cork", "Limerick", "Galway", "Waterford",
        "Drogheda", "Dundalk", "Swords", "Bray", "Navan",
        "Kilkenny", "Ennis", "Carlow", "Tralee", "Naas",
        "Sligo", "Newbridge", "Mullingar", "Celbridge", "Athlone"
    ],
    "Portugal": [
        "Lisbon", "Porto", "Vila Nova de Gaia", "Amadora", "Braga",
        "Coimbra", "Funchal", "Setúbal", "Almada", "Agualva-Cacém",
        "Queluz", "Guimarães", "Odivelas", "Aveiro", "Viseu",
        "Leiria", "Évora", "Faro", "Portimão", "Santarém"
    ],
    "Austria": [
        "Vienna", "Graz", "Linz", "Salzburg", "Innsbruck",
        "Klagenfurt", "Villach", "Wels", "Sankt Pölten", "Dornbirn",
        "Wiener Neustadt", "Steyr", "Feldkirch", "Bregenz", "Leonding",
        "Baden", "Wolfsberg", "Leoben", "Krems", "Traun"
    ]
}

def generate_german_name():
    gender = random.choice(["male", "female"])
    if gender == "male":
        first_name = random.choice(GERMAN_MALE_FIRST_NAMES)
    else:
        first_name = random.choice(GERMAN_FEMALE_FIRST_NAMES)
    
    last_name = random.choice(GERMAN_LAST_NAMES)
    return {
        "first_name": first_name,
        "last_name": last_name,
        "gender": gender
    }

def setup_driver():
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--lang=de-DE,de')
        chrome_options.add_argument(f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6998.165 Safari/537.36')
        
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.add_experimental_option('prefs', {
            'profile.default_content_setting_values.notifications': 2,
            'profile.managed_default_content_settings.images': 1,
            'profile.default_content_setting_values.cookies': 1,
            'intl.accept_languages': 'de-DE,de'
        })

        try:
            # Try using local chromedriver first
            chrome_driver_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chromedriver.exe')
            if os.path.exists(chrome_driver_path):
                service = Service(chrome_driver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
                return driver
            else:
                # If local chromedriver doesn't exist, use ChromeDriverManager
                service = Service(ChromeDriverManager(version="134.0.6998.165").install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
                return driver
        except Exception as e:
            logger.error(f"Error creating Chrome driver: {str(e)}")
            raise Exception("Could not create Chrome driver. Please make sure Chrome is installed and updated.")

    except Exception as e:
        logger.error(f"Error in setup_driver: {str(e)}")
        raise

def wait_and_find_element(driver, by, value, timeout=10):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except Exception as e:
        logger.error(f"Error finding element {value}: {str(e)}")
        return None

def wait_and_find_elements(driver, by, value, timeout=10):
    try:
        elements = WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located((by, value))
        )
        return elements
    except Exception as e:
        logger.error(f"Error finding elements {value}: {str(e)}")
        return []

def extract_zip_code(address):
    # Pattern for German zip codes (5 digits)
    zip_pattern = r'\b\d{5}\b'
    match = re.search(zip_pattern, address)
    if match:
        return match.group(0)
    return "ZIP not found"

def generate_name_for_country(country):
    # Map country names to randomuser.me nationality codes
    nationality_map = {
        "Germany": "DE",
        "United States": "US",
        "United Kingdom": "GB",
        "France": "FR",
        "Spain": "ES",
        "Netherlands": "NL",
        "Denmark": "DK",
        "Norway": "NO",
        "Finland": "FI",
        "Australia": "AU",
        "Ireland": "IE",
        "New Zealand": "NZ",
        "Turkey": "TR",
        "Switzerland": "CH",
        "Brazil": "BR",
        "Canada": "CA",
        "Iran": "IR"
    }

    try:
        # Get the nationality code for the country
        nat_code = nationality_map.get(country, "DE")  # Default to German if country not found
        
        # Make request to randomuser.me API with specific nationality
        url = f"https://randomuser.me/api/?nat={nat_code}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data and "results" in data and len(data["results"]) > 0:
                person = data["results"][0]
                return {
                    "first_name": person["name"]["first"],
                    "last_name": person["name"]["last"],
                    "gender": person["gender"]
                }
        
        logger.warning(f"Failed to get random name from API for {country}, falling back to default")
    except Exception as e:
        logger.error(f"Error generating name from API: {str(e)}")
    
    # Fallback to default German names if API fails
    return generate_german_name()

def get_business_info(driver, result, country):
    try:
        # Scroll the result into view
        driver.execute_script("arguments[0].scrollIntoView(true);", result)
        time.sleep(1)
        
        # Try different methods to click
        try:
            result.click()
        except:
            try:
                driver.execute_script("arguments[0].click();", result)
            except:
                ActionChains(driver).move_to_element(result).click().perform()
        
        logger.info("Clicked on a result")
        
        # Wait for the details to load
        time.sleep(3)
        
        # Get business information
        name = "Name not available"
        address = "Address not available"
        phone = "Phone not available"
        zip_code = "ZIP not available"
        
        # Try to get business name
        name_element = wait_and_find_element(driver, By.CSS_SELECTOR, "h1.DUwDvf")
        if name_element:
            name = name_element.text
            logger.info(f"Found business name: {name}")
        
        # Try to get address and phone
        buttons = wait_and_find_elements(driver, By.CSS_SELECTOR, "button[data-item-id]")
        for button in buttons:
            try:
                item_id = button.get_attribute("data-item-id")
                if "address" in str(item_id).lower():
                    address = button.text
                    zip_code = extract_zip_code(address)
                    logger.info(f"Found address: {address}")
                elif "phone" in str(item_id).lower():
                    phone = button.text
                    logger.info(f"Found phone: {phone}")
            except:
                continue
        
        # If we didn't find the information in buttons, try alternative selectors
        if address == "Address not available":
            address_element = wait_and_find_element(driver, By.CSS_SELECTOR, "div[data-tooltip*='Copy address']")
            if address_element:
                address = address_element.text
                zip_code = extract_zip_code(address)
        
        if phone == "Phone not available":
            phone_element = wait_and_find_element(driver, By.CSS_SELECTOR, "div[data-tooltip*='Copy phone number']")
            if phone_element:
                phone = phone_element.text
        
        # Generate a random name based on the country
        person_info = generate_name_for_country(country)
        
        return {
            "name": name,
            "address": address,
            "phone": phone,
            "zip_code": zip_code,
            "contact_person": {
                "first_name": person_info["first_name"],
                "last_name": person_info["last_name"],
                "gender": person_info["gender"]
            }
        }
        
    except Exception as e:
        logger.error(f"Error extracting information: {str(e)}")
        return None

def scrape_google_maps(city, query, zip_code=None, country=None):
    driver = None
    try:
        logger.info(f"Starting search for {query} in {city}" + (f" with ZIP code {zip_code}" if zip_code else ""))
        driver = setup_driver()
        if not driver:
            return {"error": "Failed to initialize Chrome driver"}

        # Go to Google Maps
        driver.get("https://www.google.com/maps")
        logger.info("Navigated to Google Maps")
        
        # Wait for and find the search box
        search_box = wait_and_find_element(driver, By.NAME, "q")
        if not search_box:
            return {"error": "Could not find search box"}
        
        # Enter search query with ZIP code if provided
        search_query = f"{query} in {city}"
        if zip_code:
            search_query = f"{query} {zip_code} {city}"
        search_box.clear()
        search_box.send_keys(search_query)
        search_box.send_keys(Keys.RETURN)
        logger.info(f"Entered search query: {search_query}")
        
        # Wait for results to load
        time.sleep(5)
        
        # Wait for the results to be visible
        results_selector = "div.Nv2PK"
        results = wait_and_find_elements(driver, By.CSS_SELECTOR, results_selector)
        
        if not results:
            logger.warning("No results found with primary selector, trying alternative...")
            results = wait_and_find_elements(driver, By.CSS_SELECTOR, "div[role='article']")
        
        if not results:
            return {"error": "No results found. Please try a different search."}
        
        logger.info(f"Found {len(results)} results")
        
        # Get information for results
        businesses = []
        exact_matches = []  # For businesses matching the exact ZIP code
        city_matches = []   # For businesses in the same city but different ZIP
        used_indices = set()
        max_attempts = min(15, len(results))  # Try up to 15 results
        
        while len(used_indices) < max_attempts:
            available_indices = set(range(len(results))) - used_indices
            if not available_indices:
                break
                
            index = random.choice(list(available_indices))
            used_indices.add(index)
            result = results[index]
            
            business_info = get_business_info(driver, result, country)
            if business_info:
                # Check if the address contains the city name (case-insensitive)
                if city.lower() in business_info["address"].lower():
                    if zip_code and business_info["zip_code"] == zip_code:
                        exact_matches.append(business_info)
                    else:
                        city_matches.append(business_info)
            
            # Go back to results page
            back_button = wait_and_find_element(driver, By.CSS_SELECTOR, "button[jsaction='pane.back']")
            if back_button:
                back_button.click()
                time.sleep(2)
        
        # Combine results, prioritizing exact matches
        if zip_code:
            logger.info(f"Found {len(exact_matches)} exact ZIP matches and {len(city_matches)} city matches")
            businesses = exact_matches + city_matches
            if len(businesses) > 5:
                businesses = businesses[:5]
            
            if len(exact_matches) == 0 and len(businesses) > 0:
                logger.info("No exact ZIP matches found, showing results from the same city")
        else:
            businesses = city_matches[:5]
        
        if not businesses:
            return {"error": "Could not find any businesses in the specified city"}
        
        return {
            "businesses": businesses,
            "total_found": len(businesses),
            "exact_matches": len(exact_matches) if zip_code else 0
        }
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return {"error": f"An error occurred: {str(e)}"}
    finally:
        if driver:
            driver.quit()

def load_cached_cities():
    try:
        if os.path.exists(CITIES_CACHE_FILE):
            with open(CITIES_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading cached cities: {e}")
    return {}

def save_cached_cities(cities_dict):
    try:
        with open(CITIES_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cities_dict, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving cached cities: {e}")

def fetch_all_countries():
    try:
        # Using a more reliable endpoint for countries
        url = "https://countriesnow.space/api/v0.1/countries"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if not data.get("error", True):
                # Extract country names from the response
                countries = [country["country"] for country in data.get("data", [])]
                return sorted(countries)
    except Exception as e:
        logger.error(f"Error fetching countries: {e}")
    
    # Fallback to predefined list if API fails
    return sorted(COUNTRIES_AND_CITIES.keys())

@lru_cache(maxsize=50)
def fetch_cities_for_country(country):
    cached_cities = load_cached_cities()
    if country in cached_cities:
        return cached_cities[country]

    try:
        # Using the cities endpoint
        url = "https://countriesnow.space/api/v0.1/countries/cities"
        response = requests.post(url, json={"country": country})
        
        if response.status_code == 200:
            data = response.json()
            if not data.get("error", True):
                cities = data.get("data", [])
                if cities:
                    # Clean and format city names
                    cities = [city.strip().title() for city in cities if city.strip()]  # Clean and convert to title case
                    cities = list(set(cities))  # Remove duplicates
                    cities.sort()  # Sort alphabetically
                    
                    # Update cache
                    cached_cities[country] = cities
                    save_cached_cities(cached_cities)
                    return cities
        
        logger.warning(f"Failed to fetch cities from API for {country}, falling back to predefined list")
        return COUNTRIES_AND_CITIES.get(country, [])

    except Exception as e:
        logger.error(f"Error fetching cities: {e}")
        return COUNTRIES_AND_CITIES.get(country, [])

@app.route('/get_countries')
def get_countries():
    logger.info("Getting list of countries")
    countries = fetch_all_countries()
    return jsonify({"countries": countries})

@app.route('/get_cities/<country>')
def get_cities(country):
    logger.info(f"Getting cities for country: {country}")
    try:
        cities = fetch_cities_for_country(country)
        if not cities:
            # If no cities found, return an empty list instead of error
            return jsonify({"cities": []})
        return jsonify({"cities": cities})
    except Exception as e:
        logger.error(f"Error in get_cities route: {e}")
        return jsonify({"cities": []})

@app.route('/')
def home():
    logger.info("Home page accessed")
    return render_template('index.html')

def get_location_from_ip(ip_address):
    try:
        # First try ipapi.co
        url = f"https://ipapi.co/{ip_address}/json/"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Check if we got an error response
            if "error" not in data:
                return {
                    "country": data.get("country_name"),
                    "city": data.get("city"),
                    "zip_code": data.get("postal"),
                    "latitude": data.get("latitude"),
                    "longitude": data.get("longitude")
                }
            logger.warning(f"ipapi.co returned error: {data.get('error', 'Unknown error')}")

        # Fallback to ip-api.com
        url = f"http://ip-api.com/json/{ip_address}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                return {
                    "country": data.get("country"),
                    "city": data.get("city"),
                    "zip_code": data.get("zip"),
                    "latitude": data.get("lat"),
                    "longitude": data.get("lon")
                }
            logger.warning(f"ip-api.com returned error status: {data.get('message', 'Unknown error')}")

        # If both services fail, try one more fallback - ipstack.com
        # Note: You would need to replace 'YOUR_IPSTACK_API_KEY' with a real API key
        url = f"http://api.ipstack.com/{ip_address}?access_key=YOUR_IPSTACK_API_KEY"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if not data.get("error"):
                return {
                    "country": data.get("country_name"),
                    "city": data.get("city"),
                    "zip_code": data.get("zip"),
                    "latitude": data.get("latitude"),
                    "longitude": data.get("longitude")
                }

        # If all services fail, try to determine if it's a local IP
        if ip_address.startswith(("192.168.", "10.", "172.16.", "127.")):
            # For local IPs, default to a central location in Germany
            logger.info("Local IP detected, using default location in Germany")
            return {
                "country": "Germany",
                "city": "Berlin",
                "zip_code": "10115",
                "latitude": 52.52,
                "longitude": 13.405
            }

        raise Exception("All geolocation services failed")

    except requests.exceptions.Timeout:
        logger.error(f"Timeout while getting location from IP: {ip_address}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error while getting location from IP: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error getting location from IP: {str(e)}")
        return None

def get_location_from_zip(zip_code):
    try:
        # Using nominatim to get location from ZIP code
        url = f"https://nominatim.openstreetmap.org/search?postalcode={zip_code}&country=DE&format=json"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                location = data[0]
                return {
                    "country": "Germany",  # Default to Germany for ZIP codes
                    "city": location.get("display_name").split(",")[0],
                    "zip_code": zip_code,
                    "latitude": float(location.get("lat")),
                    "longitude": float(location.get("lon"))
                }
    except Exception as e:
        logger.error(f"Error getting location from ZIP: {str(e)}")
    return None

def scrape_google_maps_with_coordinates(query, latitude, longitude, radius_km=5):
    driver = None
    try:
        driver = setup_driver()
        if not driver:
            return {"error": "Failed to initialize Chrome driver"}

        # Construct Google Maps URL with coordinates
        search_url = f"https://www.google.com/maps/search/{query}/@{latitude},{longitude},{14}z"
        driver.get(search_url)
        logger.info(f"Navigated to search results with coordinates")
        
        time.sleep(5)
        
        # Rest of the scraping logic remains similar
        results = wait_and_find_elements(driver, By.CSS_SELECTOR, "div.Nv2PK") or \
                 wait_and_find_elements(driver, By.CSS_SELECTOR, "div[role='article']")
        
        if not results:
            return {"error": "No results found. Please try a different search."}
        
        logger.info(f"Found {len(results)} results")
        
        businesses = []
        used_indices = set()
        max_attempts = min(15, len(results))
        
        while len(used_indices) < max_attempts and len(businesses) < 5:
            available_indices = set(range(len(results))) - used_indices
            if not available_indices:
                break
                
            index = random.choice(list(available_indices))
            used_indices.add(index)
            result = results[index]
            
            business_info = get_business_info(driver, result, "Germany")  # Default to Germany
            if business_info:
                businesses.append(business_info)
            
            # Go back to results
            back_button = wait_and_find_element(driver, By.CSS_SELECTOR, "button[jsaction='pane.back']")
            if back_button:
                back_button.click()
                time.sleep(2)
        
        if not businesses:
            return {"error": "Could not find any businesses in the specified location"}
        
        return {
            "businesses": businesses[:5],
            "total_found": len(businesses)
        }
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return {"error": f"An error occurred: {str(e)}"}
    finally:
        if driver:
            driver.quit()

@app.route('/search', methods=['POST'])
def search():
    logger.info("Search request received")
    try:
        data = request.get_json()
        query = data.get('query', 'barber')
        ip_address = data.get('ip_address')
        zip_code = data.get('zip_code')
        country = data.get('country')
        city = data.get('city')
        
        # Case 1: Search by IP address
        if ip_address:
            # Validate IP address format
            if not re.match(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$', ip_address):
                return jsonify({"error": "Invalid IP address format"})
            
            logger.info(f"Searching by IP address: {ip_address}")
            location = get_location_from_ip(ip_address)
            if location:
                logger.info(f"Location found for IP {ip_address}: {location}")
                return jsonify(scrape_google_maps_with_coordinates(
                    query,
                    location["latitude"],
                    location["longitude"]
                ))
            return jsonify({"error": "Could not determine location from IP address. Please try a different search method."})
        
        # Case 2: Search by ZIP code only
        elif zip_code and not country and not city:
            if not re.match(r'^\d{5}$', zip_code):
                return jsonify({"error": "Invalid ZIP code format. Please enter a 5-digit ZIP code."})
            
            logger.info(f"Searching by ZIP code: {zip_code}")
            location = get_location_from_zip(zip_code)
            if location:
                return jsonify(scrape_google_maps_with_coordinates(
                    query,
                    location["latitude"],
                    location["longitude"]
                ))
            return jsonify({"error": "Could not determine location from ZIP code"})
        
        # Case 3: Search by country + city + optional ZIP code
        elif country and city:
            if zip_code and not re.match(r'^\d{5}$', zip_code):
                return jsonify({"error": "Invalid ZIP code format. Please enter a 5-digit ZIP code."})
            
            logger.info(f"Searching in {city}, {country}" + (f" with ZIP code {zip_code}" if zip_code else ""))
            return jsonify(scrape_google_maps(city, query, zip_code, country))
        
        else:
            return jsonify({"error": "Please provide either an IP address, ZIP code, or country and city"})
            
    except Exception as e:
        logger.error(f"Error in search route: {str(e)}")
        return jsonify({"error": "An error occurred while processing your request. Please try again."})

if __name__ == '__main__':
    logger.info("Starting Flask application")
    app.run(host='127.0.0.1', port=5000, debug=True) 