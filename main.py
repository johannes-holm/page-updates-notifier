import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def get_first_car_data(driver):
    """
    Extracts the first car listing from the auto24 site and returns a dictionary.
    Returns None if there's no listing or something unexpected.
    """
    # Grab the HTML source from the already-loaded Selenium page
    html_source = driver.page_source
    soup = BeautifulSoup(html_source, "html.parser")

    container = soup.find("div", id="usedVehiclesSearchResult-flex")
    if not container:
        return None

    listings = container.find_all("div", class_="result-row")
    if not listings:
        return None

    first_listing = listings[0]

    # We can also get the data-hsh attribute for a unique ID
    unique_id = first_listing.get("data-hsh", None)

    # brand / model / engine
    title_anchor = first_listing.find("a", class_="main")
    if not title_anchor:
        return None
    
    brand = None
    model = None
    engine = None

    spans_in_title = title_anchor.find_all("span", recursive=False)
    if len(spans_in_title) > 0:
        brand = spans_in_title[0].get_text(strip=True)
    
    model_span = title_anchor.find("span", class_="model")
    if model_span:
        model = model_span.get_text(strip=True)

    engine_span = title_anchor.find("span", class_="engine")
    if engine_span:
        engine = engine_span.get_text(strip=True)
    
    # year, mileage
    extra_div = first_listing.find("div", class_="extra")
    year = None
    mileage = None
    if extra_div:
        year_span = extra_div.find("span", class_="year")
        if year_span:
            year = year_span.get_text(strip=True)

        mileage_span = extra_div.find("span", class_="mileage")
        if mileage_span:
            mileage = mileage_span.get_text(strip=True)

    # price
    finance_div = first_listing.find("div", class_="finance")
    price = None
    if finance_div:
        price_span = finance_div.find("span", class_="price")
        if price_span:
            price = price_span.get_text(strip=True)

    car_data = {
        "unique_id": unique_id,
        "brand": brand,
        "model": model,
        "engine": engine,
        "year": year,
        "mileage": mileage,
        "price": price
    }

    return car_data


def check_for_new_first_listing():
    # Path to your ChromeDriver (or the driver for the browser of your choice)
    service = Service('chromedriver.exe')
    options = webdriver.ChromeOptions()
    # options.headless = True  # Uncomment to run in headless mode

    driver = webdriver.Chrome(service=service, options=options)
    try:
        url = "https://www.auto24.ee/kasutatud/nimekiri.php?bn=3&a=100&ae=1&af=50&aa=1&ssid=221671000&ak=0"
        driver.get(url)

        # Wait for cookie banner and click "Reject All"
        wait = WebDriverWait(driver, 15)
        reject_button = wait.until(
            EC.element_to_be_clickable((By.ID, "onetrust-reject-all-handler"))
        )
        reject_button.click()

        # Wait until the cookie banner is gone
        wait.until(EC.invisibility_of_element_located((By.ID, "onetrust-banner-sdk")))

        # Get data for first listing
        old_car_data = get_first_car_data(driver)
        if not old_car_data:
            print("No initial listing found.")
            return

        print("Initial car data:", old_car_data)

        # Now you can run a loop that checks periodically for changes
        while True:
            time.sleep(20)  # Wait 60 seconds between checks (adjust as needed)

            # Refresh the page (or re-navigate):
            driver.refresh()

            # Wait a moment for listings to load if needed
            time.sleep(5)

            # Check the *new* first listing
            new_car_data = get_first_car_data(driver)
            if not new_car_data:
                print("Could not find a new listing or page structure changed.")
                continue

            # Compare by unique ID or entire dictionary
            # If the data-hsh attribute is different, it's definitely a different listing
            if new_car_data["unique_id"] != old_car_data["unique_id"]:
                print("New car is available!")
                print("New car data:", new_car_data)
                # Optionally update old_car_data or break the loop:
                old_car_data = new_car_data
                # break  # If you just want to exit after one detection
            
            else:
                print("No new listing, still the same. Checking again soon...")

    finally:
        driver.quit()


if __name__ == "__main__":
    check_for_new_first_listing()
