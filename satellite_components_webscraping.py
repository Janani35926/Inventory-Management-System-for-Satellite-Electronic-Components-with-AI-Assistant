from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from bs4 import BeautifulSoup
import json
import time
import os

def extract_product_details(driver, js_code):
    """Extracts product details from the current page."""
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        product = {}

        # Extract Part Number
        part_number_element = soup.select_one('div.d-block.detail p')
        product['Part Number'] = part_number_element.text.split(':')[1].strip() if part_number_element else None

        # Extract Manufacturer
        manufacturer_element = soup.select_one('div#CatByManu')
        if manufacturer_element:
            manufacturer_text = manufacturer_element.text.split('by')[1].strip().split('\n')[0].strip()
            product['Manufacturer'] = manufacturer_text
        else:
            product['Manufacturer'] = None

        # Extract Description
        description_element = soup.select_one('span#ContentPlaceHolder1_lblPartDescription')
        product['Description'] = description_element.text.strip() if description_element else None

        # Extract Product Name
        product_name_element = soup.select_one('div.d-block.detail h1')
        product['Product Name'] = product_name_element.text.strip() if product_name_element else None

        # Extract General Parameters (using JavaScript)
        general_parameters_json = driver.execute_script(js_code)
        general_parameters = json.loads(general_parameters_json)

        # Map extracted parameters to desired names
        parameter_mapping = {
            "Segment": "Segment",
            "Type": "Type",
            "Polarization": "Polarization",
            "Deployment": "Deployment",
            "Tx Frequency": "Tx Frequency",
            "Rx Frequency": "Rx Frequency",
            "Tx Gain": "Tx Gain",
            "Rx Gain": "Rx Gain",
            "Axial Ratio": "Axial Ratio",
            "Cross Polarization on Axis": "Cross Polarization on Axis",
            "Horizontal Beamwidth": "Horizontal Beam Width",
            "Noise Temp": "Noise Temperature",
            "Reflector": "Reflector",
            "Vertical Beamwidth": "Vertical Bandwidth",
            "VSWR": "VSWR",
            "Wind rating": "Wind Rating",
            "Isolation": "Isolation",
            "Mounting": "Mounting",
            "Weight": "Weight",
            "Dimension": "Dimension",
            "Operating Temperature": "Operating Temperature",
            "Application": "Application",
        }

        mapped_parameters = {}
        for key, value in general_parameters.items():
            if key in parameter_mapping:
                mapped_parameters[parameter_mapping[key]] = value
            elif key == "Tx" and "Gain" in general_parameters:
                mapped_parameters["Tx Gain"] = general_parameters["39.3 to 39.5 dB(C), 42 dB(X), 46.6"]
            elif key == "Rx" and "Gain" in general_parameters:
                mapped_parameters["Rx Gain"] = general_parameters["35.4 dB(C), 41.3 dB(X), 45.3"]
            elif key == "Axial" and "Ratio" in general_parameters:
                mapped_parameters["Axial Ratio"] = general_parameters["2.3 to 3 dB(C), 1.5"]
            elif key == "Cross Polarization on" and "Axis" in general_parameters:
                mapped_parameters["Cross Polarization on Axis"] = general_parameters["-30 to -15.3 dB(C), -21.3 dB(X), -30 to -23"]
            elif key == "Horizontal" and "Beamwidth" in general_parameters:
                mapped_parameters["Horizontal Beam Width"] = general_parameters["± 35° continuous fine adjustment (360°"]
            elif key == "Noise" and "Temp" in general_parameters:
                mapped_parameters["Noise Temperature"] = general_parameters["36 to 41 K(C), 56 to 60 K(X), 50 to 55"]
            elif key == "Vertical" and "Beamwidth" in general_parameters:
                mapped_parameters["Vertical Bandwidth"] = general_parameters["0 to 90"]
            elif key == "Wind" and "rating" in general_parameters:
                mapped_parameters["Wind Rating"] = general_parameters["Operational : 30 mph Gusting to 40 mph ( 48 kph G 64"]
            elif key == "Operating" and "Temperature" in general_parameters:
                mapped_parameters["Operating Temperature"] = general_parameters["-30 to 60 Degrees"]
            elif key == "Tx" and "Frequency" in general_parameters:
                mapped_parameters["Tx Frequency"] = general_parameters["5.85 to 6.425 GHz(C)/ 7.9 to 8.4 GHz(X)/ 13.75 to 14.5"]
            elif key == "Rx" and "Frequency" in general_parameters:
                mapped_parameters["Rx Frequency"] = general_parameters["3.4 to 4.20 GHz(C)/ 7.25 to 7.75 GHz(X)/ 10.7 to 12.75"]
            elif key == "Reflector" in general_parameters:
                mapped_parameters["Reflector"] = general_parameters["1.8 meters (70.87 in) Glass Fiber Reinforced Polyester"]
            elif key == "VSWR" in general_parameters:
                mapped_parameters["VSWR"] = general_parameters["1.30:1, 1.50:1(C), 1.30:1(X), 1.30:1, 1.50:1(Ku)"]
            elif key == "Isolation" in general_parameters:
                mapped_parameters["Isolation"] = general_parameters["-110 to -35 dB"]
            elif key == "Mounting" in general_parameters:
                mapped_parameters["Mounting"] = general_parameters["Tripod Mount"]
            elif key == "Weight" in general_parameters:
                mapped_parameters["Weight"] = general_parameters["177 lbs (80.5 kg)"]
            elif key == "Dimension" in general_parameters:
                mapped_parameters["Dimension"] = general_parameters["39\" x 41\" x 13 1/2\""]
            elif key == "Application" in general_parameters:
                mapped_parameters["Application"] = general_parameters["commercial or military"]

        product['general_parameters'] = mapped_parameters

        # Extract Notes
        notes_element = soup.select_one('div.featured-native-bottom div.featured-text')
        product['notes'] = notes_element.text.strip() if notes_element else None

        return product
    except Exception as e:
        print(f"An error occurred while extracting product details: {e}")
        return None

def main():
    """Main function to orchestrate the scraping process."""
    # Configure Chrome options
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--headless=new")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")  # Disable sandbox
    chrome_options.add_argument("--disable-dev-shm-usage")  # Disable /dev/shm usage
    chrome_options.add_argument("--disable-gpu")  # Disable GPU

    # Initialize the driver (Selenium will find it in PATH)
    try:
        driver = webdriver.Chrome(options=chrome_options)
    except WebDriverException as e:
        print(f"Error initializing WebDriver: {e}")
        print("Please ensure that ChromeDriver is installed and added to your system's PATH.")
        return

    #base_url = r"https://www.satnow.com/latest-products/filters?category=na&company=na&tag=satellite&page=1"  # Replace with the base URL of the website
    base_url = r"https://www.satnow.com/products/satcom-antennas/sat-lite-technologies/23-49-1822-celero"
    all_products = []
    max_pages = 1
    current_page = 1
    js_code = """
        function extractGeneralParameters() {
          const specs = document.querySelector('div.specs');
          const parameters = {};
          if (specs) {
            const specsText = document.querySelector('div.specs span#ContentPlaceHolder1_lblValues').textContent;
            const lines = specsText.split('\\n');
            let currentCategory = null;

            for (let i = 0; i < lines.length; i++) {
              const line = lines[i].trim();
              if (line === '') continue;

              if (line.includes('General Parameters')) {
                currentCategory = 'General Parameters';
                continue;
              }
              if (line.includes('Product Details')) {
                currentCategory = 'Product Details';
                continue;
              }
              if (line.includes('Technical Documents')) {
                currentCategory = 'Technical Documents';
                continue;
              }

              if (currentCategory) {
                if (currentCategory === 'General Parameters') {
                  const parts = line.split(' ');
                  const key = parts.slice(0, parts.length - 1).join(' ').trim();
                  const value = parts[parts.length - 1].trim();
                  if (key && value) {
                    parameters[key] = value;
                  } else {
                    parameters[line] = lines[i+1].trim();
                    i++;
                  }
                } else if (currentCategory === 'Product Details') {
                  const parts = line.split(' ');
                  const key = parts.slice(0, parts.length - 1).join(' ').trim();
                  const value = parts[parts.length - 1].trim();
                  if (key && value) {
                    parameters[key] = value;
                  } else {
                    parameters[line] = lines[i+1].trim();
                    i++;
                  }
                }
              }
            }
          }
          return parameters;
        }
        return JSON.stringify(extractGeneralParameters());
    """

    try:
        while current_page <= max_pages:
            url = f"{base_url}"  # Modify the URL structure if needed
            driver.get(url)

            # Wait for the page to load (adjust the timeout if needed)
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.d-block.detail'))
                )
            except TimeoutException:
                print(f"Timeout waiting for page to load on page {current_page}. Skipping to next page.")
                current_page += 1
                continue
            except NoSuchElementException:
                print(f"Element not found on page {current_page}. Skipping to next page.")
                current_page += 1
                continue

            # Extract product details from the current page
            product = extract_product_details(driver, js_code)
            if product:
                all_products.append(product)
            current_page += 1

    except WebDriverException as e:
        print(f"A WebDriver error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        driver.quit()

    # Print or save the extracted data
    print(json.dumps(all_products, indent=4))

if __name__ == "__main__":
    main()






from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from bs4 import BeautifulSoup
import json
import time

# Column mapping for required parameters
COLUMN_MAPPING = {
    "Segment": "Segment",
    "Type": "Type",
    "Polarization": "Polarization",
    "Deployment": "Deployment",
    "Tx Frequency": "Tx Frequency",
    "Rx Frequency": "Rx Frequency",
    "Tx Gain": "Tx Gain",
    "Rx Gain": "Rx Gain",
    "Axial Ratio": "Axial Ratio",
    "Cross Polarization on Axis": "Cross Polarization on Axis",
    "Horizontal Beamwidth": "Horizontal Beam Width",
    "Noise Temp": "Noise Temperature",
    "Reflector": "Reflector",
    "Vertical Beamwidth": "Vertical Bandwidth",
    "VSWR": "VSWR",
    "Wind rating": "Wind Rating",
    "Isolation": "Isolation",
    "Mounting": "Mounting",
    "Weight": "Weight",
    "Dimension": "Dimension",
    "Operating Temperature": "Operating Temperature",
    "Application": "Application",
}

def extract_product_details(driver):
    """Extracts product details including General Parameters using JavaScript."""
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        product = {}

        # Extract Part Number
        part_number_element = soup.select_one('div.d-block.detail p')
        product['Part Number'] = part_number_element.text.split(':')[1].strip() if part_number_element else "N/A"

        # Extract Manufacturer
        manufacturer_element = soup.select_one('div#CatByManu')
        product['Manufacturer'] = manufacturer_element.text.split('by')[1].strip().split('\n')[0].strip() if manufacturer_element else "N/A"

        # Extract Description
        description_element = soup.select_one('span#ContentPlaceHolder1_lblPartDescription')
        product['Description'] = description_element.text.strip() if description_element else "N/A"

        # Extract Product Name
        product_name_element = soup.select_one('div.d-block.detail h1')
        product['Product Name'] = product_name_element.text.strip() if product_name_element else "N/A"

        # Extract General Parameters using JavaScript
        js_code = """
        let params = {};
        document.querySelectorAll('.spec-container ul.list-unstyled.m-0 li').forEach(item => {
            let key = item.querySelector('.field')?.innerText.trim();
            let value = item.querySelector('.value')?.innerText.trim();
            if (key && value) {
                params[key] = value;
            }
        });
        return JSON.stringify(params);
        """
        general_parameters_json = driver.execute_script(js_code)
        general_parameters = json.loads(general_parameters_json)

        # Map extracted parameters to desired names
        mapped_parameters = {COLUMN_MAPPING.get(k, k): v for k, v in general_parameters.items()}
        product['General Parameters'] = mapped_parameters if mapped_parameters else "N/A"

        # Extract Notes
        notes_element = soup.select_one('div.featured-native-bottom div.featured-text')
        product['Notes'] = notes_element.text.strip() if notes_element else "N/A"

        return product
    except Exception as e:
        print(f" Error extracting product details: {e}")
        return None

def main(urls):
    """Main function to scrape product details."""
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")  
    chrome_options.add_argument("--disable-dev-shm-usage")  
    chrome_options.add_argument("--disable-gpu")  

    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        print(f" Error initializing WebDriver: {e}")
        return

    all_products = []

    for url in urls:
        try:
            print(f" Processing: {url}")
            driver.get(url)
            time.sleep(3)  # Allow time for page to load

            # Extract product details
            product_details = extract_product_details(driver)

            if product_details:
                print(f" Successfully extracted: {product_details}")  # Debugging output
                all_products.append(product_details)
        except Exception as e:
            print(f"Skipping URL due to error: {e}")

    # Save results to JSON file
    if all_products:
        with open("electronic_component_data.json", "w", encoding="utf-8") as f:
            json.dump(all_products, f, indent=4)
        print(" Scraping completed! Data saved in 'electronic_component_data.json'.")
    else:
        print(" No data extracted. Please check your URLs or site structure.")

    driver.quit()

# Example list of product URLs
urls = ["https://www.satnow.com/products/analog-to-digital-converters/e2v-inc/11-16-ev12aq600",
"https://www.satnow.com/products/analog-to-digital-converters/analog-devices/11-8-ad9283s",
"https://www.satnow.com/products/analog-to-digital-converters/renesas-electronics/11-1084-isla112p25m",
"https://www.satnow.com/products/analog-to-digital-converters/stmicroelectronics/11-1089-rhfad128",
"https://www.satnow.com/products/analog-to-digital-converters/data-device-corporation/11-1091-9042",
"https://www.satnow.com/products/analog-to-digital-converters/analog-devices/11-8-ad9731s",
"https://www.satnow.com/products/analog-to-digital-converters/data-device-corporation/11-1091-7872a",
"https://www.satnow.com/products/analog-to-digital-converters/analog-devices/11-8-ad571s",
"https://www.satnow.com/products/analog-to-digital-converters/data-device-corporation/11-1091-9240lp",
"https://www.satnow.com/products/analog-to-digital-converters/analog-devices/11-8-ad9254s",
"https://www.satnow.com/products/analog-to-digital-converters/data-device-corporation/11-1091-9240lp",
"https://www.satnow.com/products/analog-to-digital-converters/analog-devices/11-8-ad571k",
"https://www.satnow.com/products/analog-to-digital-converters/data-device-corporation/11-1091-7809c",
"https://www.satnow.com/products/analog-to-digital-converters/analog-devices/11-8-ad768s",
"https://www.satnow.com/products/analog-to-digital-converters/data-device-corporation/11-1091-976b",
"https://www.satnow.com/products/analog-to-digital-converters/analog-devices/11-8-ad9254s",
"https://www.satnow.com/products/analog-to-digital-converters/analog-devices/11-8-ad9054s",
"https://www.satnow.com/products/analog-to-digital-converters/analog-devices/11-8-ad9246s",
"https://www.satnow.com/products/analog-to-digital-converters/analog-devices/11-8-ad1671s",
"https://www.satnow.com/products/analog-to-digital-converters/analog-devices/11-8-ad565as",
"https://www.satnow.com/products/analog-to-digital-converters/analog-devices/11-8-ad1672s",
"https://www.satnow.com/products/analog-to-digital-converters/analog-devices/11-8-ad667s",
"https://www.satnow.com/products/analog-to-digital-converters/analog-devices/11-8-ad561s",
"https://www.satnow.com/products/analog-to-digital-converters/analog-devices/11-8-ad670s",
"https://www.satnow.com/products/analog-to-digital-converters/analog-devices/11-8-ad574s",
"https://www.satnow.com/products/analog-to-digital-converters/analog-devices/11-8-ad571j",
"https://www.satnow.com/products/analog-phase-shifters/qorvo/18-7-cmd297p34",
"https://www.satnow.com/products/analog-phase-shifters/pasternack/18-1584-pe82p5017",
"https://www.satnow.com/products/analog-phase-shifters/crane-aerospace-electronics/18-11-peg-3e-series",
"https://www.satnow.com/products/analog-phase-shifters/rf-lambda/18-1107-rvpt0204gbc",
"https://www.satnow.com/products/analog-phase-shifters/qorvo/18-7-cmd297",
"https://www.satnow.com/products/analog-phase-shifters/pasternack/18-1584-pe82p2000",
"https://www.satnow.com/products/analog-phase-shifters/crane-aerospace-electronics/18-11-pep-4s-series",
"https://www.satnow.com/products/analog-phase-shifters/rf-lambda/18-1107-rvpt0204gbc-d",
"https://www.satnow.com/products/analog-phase-shifters/pasternack/18-1584-pe82p5015",
"https://www.satnow.com/products/analog-phase-shifters/crane-aerospace-electronics/18-11-pef-03a-series",
"https://www.satnow.com/products/analog-phase-shifters/pasternack/18-1584-pe82p5017",
"https://www.satnow.com/products/analog-phase-shifters/pasternack/18-1584-pe82p2000",
"https://www.satnow.com/products/analog-phase-shifters/rf-lambda/18-1107-rvpt0206gbc",
"https://www.satnow.com/products/analog-phase-shifters/rf-lambda/18-1107-rvpt0207gac",
"https://www.satnow.com/products/analog-phase-shifters/rf-lambda/18-1107-rvpt0220gac",
"https://www.satnow.com/products/analog-phase-shifters/rf-lambda/18-1107-rvpt0302gbs",
"https://www.satnow.com/products/analog-phase-shifters/rf-lambda/18-1107-rvpt0313gac",
"https://www.satnow.com/products/analog-phase-shifters/rf-lambda/18-1107-rvpt0408gac",
"https://www.satnow.com/products/analog-phase-shifters/rf-lambda/18-1107-rvpt0408gbc",
"https://www.satnow.com/products/analog-phase-shifters/rf-lambda/18-1107-rvpt0618gac",
"https://www.satnow.com/products/analog-phase-shifters/rf-lambda/18-1107-rvpt0818gac",
"https://www.satnow.com/products/analog-phase-shifters/rf-lambda/18-1107-rvpt0818gbc",
"https://www.satnow.com/products/analog-phase-shifters/rf-lambda/18-1107-rvpt1822gbc",
"https://www.satnow.com/products/analog-phase-shifters/rf-lambda/18-1107-rvpt2127gbc",
"https://www.satnow.com/products/analog-phase-shifters/rf-lambda/18-1107-rvpt2229gbc",
"https://www.satnow.com/products/analog-phase-shifters/rf-lambda/18-1107-rvpt2231gbc",
"https://www.satnow.com/products/analog-phase-shifters/rf-lambda/18-1107-rvpt1218gac",
"https://www.satnow.com/products/analog-phase-shifters/rf-lambda/18-1107-rvpt1725mac",
"https://www.satnow.com/products/analog-phase-shifters/rf-lambda/18-1107-rvpt1725mbc",
"https://www.satnow.com/products/analog-phase-shifters/rf-lambda/18-1107-rvpt350m450mbc",
"https://www.satnow.com/products/analog-phase-shifters/rf-lambda/18-1107-rvpt396m406mbc",
"https://www.satnow.com/products/analog-phase-shifters/rf-lambda/18-1107-rvpt1000mbsb",
"https://www.satnow.com/products/analog-phase-shifters/rf-lambda/18-1107-rvpt0501gac",
"https://www.satnow.com/products/analog-phase-shifters/rf-lambda/18-1107-rvpt0501gbc",
"https://www.satnow.com/products/analog-phase-shifters/rf-lambda/18-1107-rvpt0302gas",
"https://www.satnow.com/products/analog-phase-shifters/rf-lambda/18-1107-rvpt0205mac",
"https://www.satnow.com/products/analog-phase-shifters/rf-lambda/18-1107-rvpt0205mbc",
"https://www.satnow.com/products/analog-phase-shifters/rf-lambda/18-1107-rvpt0117mac",
"https://www.satnow.com/products/analog-phase-shifters/rf-lambda/18-1107-rvpt0117mbc",
"https://www.satnow.com/products/analog-phase-shifters/rf-lambda/18-1107-rvpt0117mcc",
"https://www.satnow.com/products/microwave-rf-baluns/mini-circuits/17-2-tcw2-272",
"https://www.satnow.com/products/microwave-rf-baluns/marki-microwave/17-1723-bals-0003smg",
"https://www.satnow.com/products/microwave-rf-baluns/macom/17-1725-maba-011115",
"https://www.satnow.com/products/microwave-rf-baluns/mini-circuits/17-2-tcn4-22",
"https://www.satnow.com/products/microwave-rf-baluns/marki-microwave/17-1723-bals-0006smg",
"https://www.satnow.com/products/microwave-rf-baluns/macom/17-1725-maba-011116",
"https://www.satnow.com/products/microwave-rf-baluns/mini-circuits/17-2-tcn2-122",
"https://www.satnow.com/products/microwave-rf-baluns/macom/17-1725-maba-011125",
"https://www.satnow.com/products/microwave-rf-baluns/mini-circuits/17-2-ncs4-232",
"https://www.satnow.com/products/microwave-rf-baluns/mini-circuits/17-2-ncs4-272",
"https://www.satnow.com/products/microwave-rf-baluns/mini-circuits/17-2-tcn4-162",
"https://www.satnow.com/products/microwave-rf-baluns/mini-circuits/17-2-ncs4-63",
"https://www.satnow.com/products/microwave-rf-baluns/mini-circuits/17-2-tcn1-152-75",
"https://www.satnow.com/products/microwave-rf-baluns/mini-circuits/17-2-ncs4-442",
"https://www.satnow.com/products/microwave-rf-baluns/mini-circuits/17-2-ncs2-771-75",
"https://www.satnow.com/products/microwave-rf-baluns/mini-circuits/17-2-ncs2-592",
"https://www.satnow.com/products/microwave-rf-baluns/mini-circuits/17-2-ncs2-83",
"https://www.satnow.com/products/microwave-rf-baluns/mini-circuits/17-2-ncs2-232",
"https://www.satnow.com/products/microwave-rf-baluns/mini-circuits/17-2-ncs3-72",
"https://www.satnow.com/products/microwave-rf-baluns/mini-circuits/17-2-ncs2-622",
"https://www.satnow.com/products/microwave-rf-baluns/mini-circuits/17-2-ncs3-272",
"https://www.satnow.com/products/microwave-rf-baluns/mini-circuits/17-2-ncs2-33",
"https://www.satnow.com/products/microwave-rf-baluns/mini-circuits/17-2-ncs2-392",
"https://www.satnow.com/products/microwave-rf-baluns/mini-circuits/17-2-ncs2-62",
"https://www.satnow.com/products/microwave-rf-baluns/mini-circuits/17-2-ncs2-222",
"https://www.satnow.com/products/microwave-rf-baluns/mini-circuits/17-2-ncs1-422",
"https://www.satnow.com/products/microwave-rf-baluns/mini-circuits/17-2-ncs1-23",
"https://www.satnow.com/products/microwave-rf-baluns/mini-circuits/17-2-ncs1-222-75",
"https://www.satnow.com/products/microwave-rf-baluns/mini-circuits/17-2-ncr2-113",
"https://www.satnow.com/products/microwave-rf-baluns/mini-circuits/17-2-ncs1-5-232",
"https://www.satnow.com/products/microwave-rf-baluns/mini-circuits/17-2-ncs1-112",
"https://www.satnow.com/products/microwave-rf-baluns/mini-circuits/17-2-ncs1-63",
"https://www.satnow.com/products/microwave-rf-baluns/mini-circuits/17-2-ncr2-123",
"https://www.satnow.com/products/microwave-rf-baluns/mini-circuits/17-2-ncs1-292",
"https://www.satnow.com/products/microwave-rf-baluns/mini-circuits/17-2-ncs4-102",
"https://www.satnow.com/products/rf-cable-assemblies/amphenol-rf/114-1342-095-820-124-05z",
"https://www.satnow.com/products/rf-cable-assemblies/rosenberger/114-1341-l70-336-102",
"https://www.satnow.com/products/rf-cable-assemblies/smiths-microwave/114-4-spacenxt-065qt",
"https://www.satnow.com/products/rf-cable-assemblies/radiall/114-1324-shf-2-4-ms",
"https://www.satnow.com/products/rf-cable-assemblies/times-microwave-systems/114-1344-spflt-310",
"https://www.satnow.com/products/rf-cable-assemblies/wl-gore-associates/114-1345-cable-type-26",
"https://www.satnow.com/products/rf-cable-assemblies/amphenol-cit/114-1737-mcj088d",
"https://www.satnow.com/products/rf-cable-assemblies/megaphase/114-1343-al047",
"https://www.satnow.com/products/rf-cable-assemblies/amphenol-rf/114-1342-095-820-124-25z",
"https://www.satnow.com/products/rf-cable-assemblies/rosenberger/114-1341-l70-323-102",
"https://www.satnow.com/products/rf-cable-assemblies/rosenberger/114-1341-l70-323-102",
"https://www.satnow.com/products/rf-cable-assemblies/amphenol-rf/114-1342-095-820-124-25z",
"https://www.satnow.com/products/rf-cable-assemblies/megaphase/114-1343-al141",
"https://www.satnow.com/products/rf-cable-assemblies/times-microwave-systems/114-1344-spflx-095",
"https://www.satnow.com/products/rf-cable-assemblies/wl-gore-associates/114-1345-cable-type-27",
"https://www.satnow.com/products/rf-cable-assemblies/amphenol-cit/114-1737-mcj115a",
"https://www.satnow.com/products/rf-cable-assemblies/smiths-microwave/114-4-spacenxt-100qt",
"https://www.satnow.com/products/rf-cable-assemblies/radiall/114-1324-shf-8-ms-etfe",
"https://www.satnow.com/products/rf-cable-assemblies/rosenberger/114-1341-h70w-w16-w16-00305",
"https://www.satnow.com/products/rf-cable-assemblies/amphenol-rf/114-1342-095-820-124-15z",
"https://www.satnow.com/products/rf-cable-assemblies/megaphase/114-1343-al086",
"https://www.satnow.com/products/rf-cable-assemblies/times-microwave-systems/114-1344-spflt-140",
"https://www.satnow.com/products/rf-cable-assemblies/wl-gore-associates/114-1345-cable-type-56",
"https://www.satnow.com/products/rf-cable-assemblies/amphenol-cit/114-1737-mcj142a",
"https://www.satnow.com/products/rf-cable-assemblies/rosenberger/114-1341-h70w-w16-vm-00305",
"https://www.satnow.com/products/rf-cable-assemblies/amphenol-rf/114-1342-095-820-124-20z",
"https://www.satnow.com/products/rf-cable-assemblies/wl-gore-associates/114-1345-cable-type-5g",
"https://www.satnow.com/products/rf-cable-assemblies/amphenol-cit/114-1737-mcj185a",
"https://www.satnow.com/products/rf-cable-assemblies/radiall/114-1324-shf-3-ms-etfe",
"https://www.satnow.com/products/rf-cable-assemblies/rosenberger/114-1341-h70w-w16-km-00305",
"https://www.satnow.com/products/rf-cable-assemblies/amphenol-rf/114-1342-095-820-124-30z",
"https://www.satnow.com/products/rf-cable-assemblies/times-microwave-systems/114-1344-spflt-200",
"https://www.satnow.com/products/rf-cable-assemblies/wl-gore-associates/114-1345-cable-type-41",
"https://www.satnow.com/products/rf-cable-assemblies/amphenol-cit/114-1737-mcj205a",
"https://www.satnow.com/products/rf-cable-assemblies/radiall/114-1324-c291-851-601",
"https://www.satnow.com/products/rf-cable-assemblies/times-microwave-systems/114-1344-sio2-cables-assemblies",
"https://www.satnow.com/products/rf-cable-assemblies/wl-gore-associates/114-1345-cable-type-5d",
"https://www.satnow.com/products/rf-cable-assemblies/amphenol-cit/114-1737-mcj311a",
"https://www.satnow.com/products/rf-cable-assemblies/radiall/114-1324-c291-861-661",
"https://www.satnow.com/products/rf-cable-assemblies/amphenol-rf/114-1342-095-820-124-10z",
"https://www.satnow.com/products/rf-cable-assemblies/amphenol-cit/114-1737-ut-085-ds",
"https://www.satnow.com/products/rf-cable-assemblies/radiall/114-1324-shf-3-ms",
"https://www.satnow.com/products/rf-cable-assemblies/amphenol-cit/114-1737-ut-085c-ll",
"https://www.satnow.com/products/rf-cable-assemblies/radiall/114-1324-shf-8ms",
"https://www.satnow.com/products/rf-cable-assemblies/wl-gore-associates/114-1345-cable-type-42",
"https://www.satnow.com/products/rf-cable-assemblies/amphenol-cit/114-1737-ut-141-ds",
"https://www.satnow.com/products/rf-cable-assemblies/radiall/114-1324-c291-859-661",
"https://www.satnow.com/products/rf-cable-assemblies/wl-gore-associates/114-1345-cable-type-28",
"https://www.satnow.com/products/rf-cable-assemblies/amphenol-cit/114-1737-ut-141c-ll",
"https://www.satnow.com/products/rf-cable-assemblies/radiall/114-1324-shf-5ms",
"https://www.satnow.com/products/rf-cable-assemblies/wl-gore-associates/114-1345-cable-type-89",
"https://www.satnow.com/products/rf-cable-assemblies/radiall/114-1324-c291-852-661",
"https://www.satnow.com/products/rf-cable-assemblies/wl-gore-associates/114-1345-cable-type-g4",
"https://www.satnow.com/products/rf-cable-assemblies/wl-gore-associates/114-1345-cable-type-4y",
"https://www.satnow.com/products/rf-cable-assemblies/wl-gore-associates/114-1345-cable-type-g5",
"https://www.satnow.com/products/rf-cable-assemblies/wl-gore-associates/114-1345-type-8s",
"https://www.satnow.com/products/capacitors/vishay/127-1092-mil-prf-123",
"https://www.satnow.com/products/capacitors/knowles/127-1112-high-reliability-radial-lead-capacitors",
"https://www.satnow.com/products/capacitors/exxelia-technologies/127-1378-cmr-series",
"https://www.satnow.com/products/capacitors/presidio-components/127-1379-high-reliability-extended-range-chip-capacitors",
"https://www.satnow.com/products/capacitors/kemet/127-1380-10hs20n270k",
"https://www.satnow.com/products/capacitors/kyocera-avx/127-1381-tbj-series",
"https://www.satnow.com/products/capacitors/quantic-evans/127-1575-tdb5060163",
"https://www.satnow.com/products/capacitors/johanson-dielectrics/127-1740-circular-arrays",
"https://www.satnow.com/products/capacitors/knowles/127-1112-high-temperature-radial-leaded-capacitors-encapsulated",
"https://www.satnow.com/products/capacitors/exxelia-technologies/127-1378-cm-series",
"https://www.satnow.com/products/capacitors/quantic-evans/127-1575-tdb4060123",
"https://www.satnow.com/products/capacitors/johanson-dielectrics/127-1740-discoidal-capacitors",
"https://www.satnow.com/products/capacitors/knowles/127-1112-s02a-space-grade-capacitors",
"https://www.satnow.com/products/capacitors/exxelia-technologies/127-1378-ca-series",
"https://www.satnow.com/products/capacitors/kemet/127-1380-10hs23n121kc",
"https://www.satnow.com/products/capacitors/kyocera-avx/127-1381-tbj-series",
"https://www.satnow.com/products/capacitors/quantic-evans/127-1575-tdb5060163",
"https://www.satnow.com/products/capacitors/johanson-dielectrics/127-1740-circular-arrays",
"https://www.satnow.com/products/capacitors/knowles/127-1112-high-reliability-radial-lead-capacitors",
"https://www.satnow.com/products/capacitors/exxelia-technologies/127-1378-mf-series",
"https://www.satnow.com/products/capacitors/kemet/127-1380-10hs20n270k",
"https://www.satnow.com/products/capacitors/kyocera-avx/127-1381-escc-3009-041-space-level-bme-x7r-multi-layer-ceramic-capacitors",
"https://www.satnow.com/products/capacitors/quantic-evans/127-1575-tdb1080212",
"https://www.satnow.com/products/capacitors/johanson-dielectrics/127-1740-rectangular-arrays",
"https://www.satnow.com/products/capacitors/knowles/127-1112-high-temperature-radial-leaded-capacitors-encapsulated",
"https://www.satnow.com/products/capacitors/exxelia-technologies/127-1378-ctc21e",
"https://www.satnow.com/products/capacitors/kemet/127-1380-20hs24n102k",
"https://www.satnow.com/products/capacitors/kyocera-avx/127-1381-mil-prf-32535-x7r-bme-multi-layer-ceramic-capacitors",
"https://www.satnow.com/products/capacitors/quantic-evans/127-1575-tdb2080422",
"https://www.satnow.com/products/rf-microwave-circulators/smiths-microwave/12-4-l-band-high-power-circulator",
"https://www.satnow.com/products/rf-microwave-circulators/renaissance-electronics-corporation/12-5-3a1ndk-s",
"https://www.satnow.com/products/rf-microwave-circulators/rf-lambda/12-1107-rflc101m33m40",
"https://www.satnow.com/products/rf-microwave-circulators/cobham-microwave/12-1744-bg3020",
"https://www.satnow.com/products/rf-microwave-circulators/ditom-microwave/12-15-dsc1722",
"https://www.satnow.com/products/rf-microwave-circulators/honeywell-aerospace/12-1202-lg10505",
"https://www.satnow.com/products/rf-microwave-circulators/renaissance-electronics-corporation/12-5-3a4npe",
"https://www.satnow.com/products/rf-microwave-circulators/rf-lambda/12-1107-rflc-101-1h-400-450s",
"https://www.satnow.com/products/rf-microwave-circulators/cobham-microwave/12-1744-bj3012",
"https://www.satnow.com/products/rf-microwave-circulators/ditom-microwave/12-15-dsc2731",
"https://www.satnow.com/products/rf-microwave-circulators/honeywell-aerospace/12-1202-sg10520",
"https://www.satnow.com/products/rf-microwave-circulators/rf-lambda/12-1107-rfc240b355m500w",
"https://www.satnow.com/products/rf-microwave-circulators/cobham-microwave/12-1744-fk1013",
"https://www.satnow.com/products/rf-microwave-circulators/renaissance-electronics-corporation/12-5-3a2nhy-s",
"https://www.satnow.com/products/rf-microwave-circulators/rf-lambda/12-1107-rfc214w1000m360n",
"https://www.satnow.com/products/rf-microwave-circulators/cobham-microwave/12-1744-nj3123-100",
"https://www.satnow.com/products/rf-microwave-circulators/honeywell-aerospace/12-1202-sg10521",
"https://www.satnow.com/products/rf-microwave-circulators/renaissance-electronics-corporation/12-5-3a4npf-s",
"https://www.satnow.com/products/rf-microwave-circulators/rf-lambda/12-1107-rflc101m36m44",
"https://www.satnow.com/products/rf-microwave-circulators/cobham-microwave/12-1744-fj1008",
"https://www.satnow.com/products/rf-microwave-circulators/honeywell-aerospace/12-1202-lg10500",
"https://www.satnow.com/products/rf-microwave-circulators/cobham-microwave/12-1744-bg3022",
"https://www.satnow.com/products/rf-microwave-circulators/honeywell-aerospace/12-1202-lg10501",
"https://www.satnow.com/products/rf-microwave-circulators/rf-lambda/12-1107-rflc-117-1-450m",
"https://www.satnow.com/products/rf-microwave-circulators/cobham-microwave/12-1744-bf3007",
"https://www.satnow.com/products/rf-microwave-circulators/honeywell-aerospace/12-1202-sg10522",
"https://www.satnow.com/products/rf-microwave-circulators/renaissance-electronics-corporation/12-5-3a4ndy",
"https://www.satnow.com/products/rf-microwave-circulators/rf-lambda/12-1107-rflc101m33m42",
"https://www.satnow.com/products/rf-microwave-circulators/cobham-microwave/12-1744-bg3025",
"https://www.satnow.com/products/rf-microwave-circulators/honeywell-aerospace/12-1202-lg10506",
"https://www.satnow.com/products/rf-microwave-circulators/rf-lambda/12-1107-rflc214w800m400s",
"https://www.satnow.com/products/rf-microwave-circulators/cobham-microwave/12-1744-bk3010",
"https://www.satnow.com/products/rf-microwave-circulators/honeywell-aerospace/12-1202-lg10507",
"https://www.satnow.com/products/rf-microwave-circulators/rf-lambda/12-1107-rflc-119-1-600m",
"https://www.satnow.com/products/rf-microwave-circulators/cobham-microwave/12-1744-bf3011",
"https://www.satnow.com/products/rf-microwave-circulators/honeywell-aerospace/12-1202-sg10523",
"https://www.satnow.com/products/rf-microwave-circulators/renaissance-electronics-corporation/12-5-3a4ndz",
"https://www.satnow.com/products/rf-microwave-circulators/rf-lambda/12-1107-rflc214w850m450n",
"https://www.satnow.com/products/rf-microwave-circulators/cobham-microwave/12-1744-bg3026",
"https://www.satnow.com/products/rf-microwave-circulators/honeywell-aerospace/12-1202-lg10508",
"https://www.satnow.com/products/rf-microwave-circulators/rf-lambda/12-1107-rflc214w900m500s",
"https://www.satnow.com/products/rf-microwave-circulators/cobham-microwave/12-1744-bk3013",
"https://www.satnow.com/products/rf-microwave-circulators/honeywell-aerospace/12-1202-lg10509",
"https://www.satnow.com/products/rf-microwave-circulators/rf-lambda/12-1107-rflc-121-1-700m",
"https://www.satnow.com/products/rf-microwave-circulators/cobham-microwave/12-1744-bf3015",
"https://www.satnow.com/products/rf-microwave-circulators/honeywell-aerospace/12-1202-sg10524",
"https://www.satnow.com/products/comparators/analog-devices/157-8-rh1016m",
"https://www.satnow.com/products/comparators/renesas-electronics/157-1084-cd4063bms",
"https://www.satnow.com/products/comparators/stmicroelectronics/157-1089-rhr801",
"https://www.satnow.com/products/comparators/cobham-advanced-electronic-solutions/157-1323-rhd5912",
"https://www.satnow.com/products/comparators/power-device-corporation/157-1477-903",
"https://www.satnow.com/products/comparators/analog-devices/157-8-rh119",
"https://www.satnow.com/products/comparators/renesas-electronics/157-1084-hs-139eh",
"https://www.satnow.com/products/comparators/analog-devices/157-8-rh1011",
"https://www.satnow.com/products/comparators/renesas-electronics/157-1084-hs-139rh",
"https://www.satnow.com/products/comparators/analog-devices/157-8-pm139",
"https://www.satnow.com/products/comparators/renesas-electronics/157-1084-isl7119eh",
"https://www.satnow.com/products/comparators/renesas-electronics/157-1084-isl7119rh",
"https://www.satnow.com/products/comparators/stmicroelectronics/157-1089-rhr801",
"https://www.satnow.com/products/comparators/cobham-advanced-electronic-solutions/157-1323-rhd5912",
"https://www.satnow.com/products/comparators/power-device-corporation/157-1477-903",
"https://www.satnow.com/products/comparators/honeywell-aerospace/157-1202-hmxcmp01",
"https://www.satnow.com/products/couplers/mini-circuits/173-2-zddc30-k0244",
  "https://www.satnow.com/products/couplers/mercury-systems/173-1083-s6118",
  "https://www.satnow.com/products/couplers/stellant-systems/173-1267-s-718-1",
  "https://www.satnow.com/products/couplers/crane-aerospace-electronics/173-11-csc-30-1-38g-sq",
  "https://www.satnow.com/products/couplers/krytar/173-6-101040010k-sq",
  "https://www.satnow.com/products/couplers/mountain-microwave-technology/173-1641-mm-ddc-060180-30",
  "https://www.satnow.com/products/couplers/wiran/173-1374-csa",
  "https://www.satnow.com/products/couplers/xma-corporation/173-1757-os2020-5005-06",
  "https://www.satnow.com/products/couplers/mini-circuits/173-2-zddc20-k0244",
  "https://www.satnow.com/products/couplers/stellant-systems/173-1267-p-706-1",
  "https://www.satnow.com/products/couplers/crane-aerospace-electronics/173-11-csc-30-405g-sq",
  "https://www.satnow.com/products/couplers/mountain-microwave-technology/173-1641-mm-ddc-010400-20",
  "https://www.satnow.com/products/couplers/wiran/173-1374-cla",
  "https://www.satnow.com/products/couplers/mini-circuits/173-2-zddc30-k0644",
  "https://www.satnow.com/products/couplers/krytar/173-6-4010265-sq",
  "https://www.satnow.com/products/couplers/crane-aerospace-electronics/173-11-csc-30-1-38g-sq",
  "https://www.satnow.com/products/couplers/stellant-systems/173-1267-s-718-1",
  "https://www.satnow.com/products/couplers/mountain-microwave-technology/173-1641-mm-ddc-060180-30",
  "https://www.satnow.com/products/couplers/wiran/173-1374-csa",
  "https://www.satnow.com/products/couplers/mini-circuits/173-2-zddc30-k0244",
  "https://www.satnow.com/products/couplers/mini-circuits/173-2-zddc20-k0244",
  "https://www.satnow.com/products/couplers/crane-aerospace-electronics/173-11-csc-10-1-5g-sq",
  "https://www.satnow.com/products/couplers/mountain-microwave-technology/173-1641-mm-ddc-040120-40",
  "https://www.satnow.com/products/couplers/crane-aerospace-electronics/173-11-csc-30-4-45g-sq",
  "https://www.satnow.com/products/couplers/mini-circuits/173-2-zddc30-k1844",
  "https://www.satnow.com/products/couplers/crane-aerospace-electronics/173-11-csm-30-6g-sq",
  "https://www.satnow.com/products/couplers/mini-circuits/173-2-bdca1-7-33-",
  "https://www.satnow.com/products/couplers/crane-aerospace-electronics/173-11-csm-8-6-1g-sq",
  "https://www.satnow.com/products/couplers/mini-circuits/173-2-zcdc10-e6653-",
  "https://www.satnow.com/products/couplers/crane-aerospace-electronics/173-11-csm-30-6-2g-sq",
  "https://www.satnow.com/products/couplers/mini-circuits/173-2-bdca1-6-22-",
  "https://www.satnow.com/products/couplers/crane-aerospace-electronics/173-11-csc-30-4-2g-sq",
  "https://www.satnow.com/products/couplers/mini-circuits/173-2-zddc10-k0244",
  "https://www.satnow.com/products/couplers/crane-aerospace-electronics/173-11-csc-30-3-7g-sq",
  "https://www.satnow.com/products/couplers/mini-circuits/173-2-bdca1-10-40-",
  "https://www.satnow.com/products/couplers/crane-aerospace-electronics/173-11-csm-30-12g-sq",
  "https://www.satnow.com/products/couplers/mini-circuits/173-2-zddc10-k5r44w",
  "https://www.satnow.com/products/couplers/crane-aerospace-electronics/173-11-csc-30-4g-sq",
  "https://www.satnow.com/products/couplers/crane-aerospace-electronics/173-11-csm-5-6-1g-sq",
  "https://www.satnow.com/products/couplers/crane-aerospace-electronics/173-11-csc-8-2-25g-sq",
  "https://www.satnow.com/products/couplers/crane-aerospace-electronics/173-11-csc-8-2-3g-sq",
  "https://www.satnow.com/products/couplers/crane-aerospace-electronics/173-11-csm-30-1-64g-sq",
  "https://www.satnow.com/products/couplers/crane-aerospace-electronics/173-11-csc-8-3-8g-sq",
  "https://www.satnow.com/products/couplers/crane-aerospace-electronics/173-11-csm-30-6-25g-sq",
  "https://www.satnow.com/products/couplers/crane-aerospace-electronics/173-11-csm-30-7-82g-sq",
  "https://www.satnow.com/products/couplers/crane-aerospace-electronics/173-11-csm-6-12-75g-sq",
  "https://www.satnow.com/products/couplers/crane-aerospace-electronics/173-11-csm-6-12g-sq",
  "https://www.satnow.com/products/couplers/crane-aerospace-electronics/173-11-qhf-2a-10-sq",
  "https://www.satnow.com/products/couplers/crane-aerospace-electronics/173-11-qhf-2a-100-sq",
  "https://www.satnow.com/products/couplers/crane-aerospace-electronics/173-11-qhf-2a-200-sq",
  "https://www.satnow.com/products/couplers/crane-aerospace-electronics/173-11-qhk-2-4-5g-sq",
  "https://www.satnow.com/products/couplers/crane-aerospace-electronics/173-11-qhk-4r-26-7g-sq",
  "https://www.satnow.com/products/couplers/crane-aerospace-electronics/173-11-qhm-2-1-5g-sq",
  "https://www.satnow.com/products/couplers/crane-aerospace-electronics/173-11-qhm-2-1-8g-sq",
  "https://www.satnow.com/products/couplers/crane-aerospace-electronics/173-11-qhm-2-11-7g-sq",
  "https://www.satnow.com/products/couplers/crane-aerospace-electronics/173-11-qhm-2-11-8g-sq",
  "https://www.satnow.com/products/couplers/crane-aerospace-electronics/173-11-qhdz-2h-2-1g-sq",
  "https://www.satnow.com/products/couplers/crane-aerospace-electronics/173-11-qhdz-2n-0-392g-sq"
  "https://www.satnow.com/products/dc-dc-converters/microchip-technology/28-1082-sa50-28-5s",
"https://www.satnow.com/products/dc-dc-converters/crane-aerospace-electronics/28-11-smsa2805d",
"https://www.satnow.com/products/dc-dc-converters/mercury-systems/28-1083-rh5210",
"https://www.satnow.com/products/dc-dc-converters/fei-zyfer/28-1080-385-4042-01",
"https://www.satnow.com/products/dc-dc-converters/modular-devices/28-1450-4690-t12",
"https://www.satnow.com/products/dc-dc-converters/microchip-technology/28-1082-sa50-28-3r3s",
"https://www.satnow.com/products/dc-dc-converters/crane-aerospace-electronics/28-11-smfl2805s",
"https://www.satnow.com/products/dc-dc-converters/fei-zyfer/28-1080-385-4117-01",
"https://www.satnow.com/products/dc-dc-converters/modular-devices/28-1450-4690-t05",
"https://www.satnow.com/products/dc-dc-converters/microchip-technology/28-1082-sa50-120-3r3-12t-a-h",
"https://www.satnow.com/products/dc-dc-converters/fei-zyfer/28-1080-385-4117-01",
"https://www.satnow.com/products/dc-dc-converters/microchip-technology/28-1082-sa50-120-5-15t-a-p",
"https://www.satnow.com/products/dc-dc-converters/modular-devices/28-1450-4690-t15",
"https://www.satnow.com/products/dc-dc-converters/crane-aerospace-electronics/28-11-smrt2812s",
"https://www.satnow.com/products/dc-dc-converters/fei-zyfer/28-1080-407-4022-02",
"https://www.satnow.com/products/dc-dc-converters/microchip-technology/28-1082-sa50-120-5-15t-a-h",
"https://www.satnow.com/products/dc-dc-converters/modular-devices/28-1450-8680-s05",
"https://www.satnow.com/products/dc-dc-converters/crane-aerospace-electronics/28-11-smflhp283r3s",
"https://www.satnow.com/products/dc-dc-converters/fei-zyfer/28-1080-385-4022-02",
"https://www.satnow.com/products/dc-dc-converters/microchip-technology/28-1082-sa50-120-5-12t-a-h",
"https://www.satnow.com/products/dc-dc-converters/modular-devices/28-1450-8680-s05-2",
"https://www.satnow.com/products/dc-dc-converters/crane-aerospace-electronics/28-11-smsa283r3s",
"https://www.satnow.com/products/dc-dc-converters/fei-zyfer/28-1080-385-4022-01",
"https://www.satnow.com/products/dc-dc-converters/microchip-technology/28-1082-sa50-120-3r3s-a-p",
"https://www.satnow.com/products/dc-dc-converters/modular-devices/28-1450-8680-s12",
"https://www.satnow.com/products/dc-dc-converters/crane-aerospace-electronics/28-11-smsa2805s",
"https://www.satnow.com/products/dc-dc-converters/modular-devices/28-1450-8680-s15",
"https://www.satnow.com/products/dc-dc-converters/crane-aerospace-electronics/28-11-smtr2805d",
"https://www.satnow.com/products/dc-dc-converters/microchip-technology/28-1082-sa50-120-3r3-15t-a-p",
"https://www.satnow.com/products/dc-dc-converters/modular-devices/28-1450-8680-s28",
"https://www.satnow.com/products/dc-dc-converters/crane-aerospace-electronics/28-11-smp12005s",
"https://www.satnow.com/products/dc-dc-converters/microchip-technology/28-1082-sa50-120-3r3s-a-h",
"https://www.satnow.com/products/dc-dc-converters/modular-devices/28-1450-8680-t05",
"https://www.satnow.com/products/dc-dc-converters/crane-aerospace-electronics/28-11-smfl2815d",
"https://www.satnow.com/products/dc-dc-converters/microchip-technology/28-1082-sa50-120-3r3-15t-a-h",
"https://www.satnow.com/products/dc-dc-converters/modular-devices/28-1450-8690-t05",
"https://www.satnow.com/products/dc-dc-converters/crane-aerospace-electronics/28-11-smtr2815d",
"https://www.satnow.com/products/dc-dc-converters/microchip-technology/28-1082-sa50-120-3r3-12t-a-p",
"https://www.satnow.com/products/dc-dc-converters/modular-devices/28-1450-8690-t12",
"https://www.satnow.com/products/dc-dc-converters/crane-aerospace-electronics/28-11-smflhp2805d",
"https://www.satnow.com/products/dc-dc-converters/microchip-technology/28-1082-sa50-120-28s-a-p",
"https://www.satnow.com/products/dc-dc-converters/modular-devices/28-1450-8680-t12",
"https://www.satnow.com/products/dc-dc-converters/crane-aerospace-electronics/28-11-smflhp2812d",
"https://www.satnow.com/products/dc-dc-converters/microchip-technology/28-1082-sa50-28-5s",
"https://www.satnow.com/products/dc-dc-converters/modular-devices/28-1450-4690-t12",
"https://www.satnow.com/products/dc-dc-converters/crane-aerospace-electronics/28-11-smsa2805d",
"https://www.satnow.com/products/dc-dc-converters/microchip-technology/28-1082-sa50-28-3r3s",
"https://www.satnow.com/products/dc-dc-converters/modular-devices/28-1450-4690-t05",
"https://www.satnow.com/products/dc-dc-converters/crane-aerospace-electronics/28-11-smfl2805s",
"https://www.satnow.com/products/dc-dc-converters/microchip-technology/28-1082-sa50-120-3r3-12t-a-h",
"https://www.satnow.com/products/dc-dc-converters/modular-devices/28-1450-5107-d15",
"https://www.satnow.com/products/dc-dc-converters/crane-aerospace-electronics/28-11-smtr2805s",
"https://www.satnow.com/products/dc-dc-converters/microchip-technology/28-1082-sa50-28-28s",
"https://www.satnow.com/products/dc-dc-converters/modular-devices/28-1450-5107-d3-3-5",
"https://www.satnow.com/products/dc-dc-converters/crane-aerospace-electronics/28-11-smhf2805s",
"https://www.satnow.com/products/dc-dc-converters/microchip-technology/28-1082-sa50-120-5s-a-h",
"https://www.satnow.com/products/dc-dc-converters/modular-devices/28-1450-5107-s02",
"https://www.satnow.com/products/dc-dc-converters/crane-aerospace-electronics/28-11-smhf285r2s",
"https://www.satnow.com/products/dc-dc-converters/microchip-technology/28-1082-sa50-120-15s-a-h",
"https://www.satnow.com/products/digital-phase-shifters/qorvo/15-7-cmd175p4",
"https://www.satnow.com/products/digital-phase-shifters/analog-devices/15-8-hmc1133lp5e",
"https://www.satnow.com/products/digital-phase-shifters/macom/15-1725-cgy2172xauh",
"https://www.satnow.com/products/digital-phase-shifters/pasternack/15-1584-pe82p5000",
"https://www.satnow.com/products/digital-phase-shifters/rf-lambda/15-1107-rfpsht1826n6usb",
"https://www.satnow.com/products/digital-phase-shifters/united-monolithic-semiconductors/15-1413-chp3010-qfg",
"https://www.satnow.com/products/digital-phase-shifters/qorvo/15-7-cmd176p4",
"https://www.satnow.com/products/digital-phase-shifters/analog-devices/15-8-hmc543alc4b",
"https://www.satnow.com/products/digital-phase-shifters/macom/15-1725-cgy2174uh",
"https://www.satnow.com/products/digital-phase-shifters/rf-lambda/15-1107-rfpsht1218n6usb",
"https://www.satnow.com/products/digital-phase-shifters/rf-lambda/15-1107-rfpsht1519n6usb",
"https://www.satnow.com/products/digital-phase-shifters/macom/15-1725-cgy2174uh",
"https://www.satnow.com/products/digital-phase-shifters/united-monolithic-semiconductors/15-1413-chp4012a98f",
"https://www.satnow.com/products/digital-phase-shifters/analog-devices/15-8-hmc644alc5",
"https://www.satnow.com/products/digital-phase-shifters/rf-lambda/15-1107-rfpsht2832d5usb",
"https://www.satnow.com/products/digital-phase-shifters/macom/15-1725-cgy2173uh",
"https://www.satnow.com/products/digital-phase-shifters/united-monolithic-semiconductors/15-1413-chp4010-99f",
"https://www.satnow.com/products/digital-phase-shifters/analog-devices/15-8-hmc642alc5",
"https://www.satnow.com/products/digital-phase-shifters/rf-lambda/15-1107-rfpsht3040d1usb",
"https://www.satnow.com/products/digital-phase-shifters/macom/15-1725-cgy2172xbuh",
"https://www.satnow.com/products/digital-phase-shifters/united-monolithic-semiconductors/15-1413-chp3015-99f",
"https://www.satnow.com/products/digital-phase-shifters/analog-devices/15-8-hmc648alp6e",
"https://www.satnow.com/products/digital-phase-shifters/rf-lambda/15-1107-rfpsht0102n6usb",
"https://www.satnow.com/products/digital-phase-shifters/macom/15-1725-cgy2177auh",
"https://www.satnow.com/products/digital-phase-shifters/united-monolithic-semiconductors/15-1413-chp3015-qdg",
"https://www.satnow.com/products/digital-phase-shifters/analog-devices/15-8-hmc647alp6e",
"https://www.satnow.com/products/digital-phase-shifters/rf-lambda/15-1107-rfpsht0204n6usb",
"https://www.satnow.com/products/digital-phase-shifters/macom/15-1725-cgy2392suh",
"https://www.satnow.com/products/digital-phase-shifters/analog-devices/15-8-hmc649alp6e",
"https://www.satnow.com/products/digital-phase-shifters/rf-lambda/15-1107-rfpsht0408n6usb",
"https://www.satnow.com/products/digital-phase-shifters/analog-devices/15-8-hmc936alp6e",
"https://www.satnow.com/products/digital-phase-shifters/rf-lambda/15-1107-rfpsht0618n6usb",
"https://www.satnow.com/products/digital-phase-shifters/analog-devices/15-8-adh936s",
"https://www.satnow.com/products/digital-phase-shifters/rf-lambda/15-1107-rfpsht0812n6usb",
"https://www.satnow.com/products/digital-phase-shifters/rf-lambda/15-1107-rfpsht0821n6usb",
"https://www.satnow.com/products/digital-phase-shifters/rf-lambda/15-1107-rfpsht450m1d8usb",
"https://www.satnow.com/products/digital-phase-shifters/rf-lambda/15-1107-rfpsht0210n6usbusb",
"https://www.satnow.com/products/microwave-rf-diplexers/mini-circuits/13-2-ldpg-272-492",
"https://www.satnow.com/products/microwave-rf-diplexers/honeywell-aerospace/13-1202-92511500-000",
"https://www.satnow.com/products/microwave-rf-diplexers/shf-communication-technologies/13-1742-shf-dx45r-hvc50-1000",
"https://www.satnow.com/products/microwave-rf-diplexers/wiran/13-1374-dsb",
"https://www.satnow.com/products/microwave-rf-diplexers/mini-circuits/13-2-ldp-1050-252",
"https://www.satnow.com/products/microwave-rf-diplexers/shf-communication-technologies/13-1742-shf-dx45r-hvc100-2000",
"https://www.satnow.com/products/microwave-rf-diplexers/wiran/13-1374-dxa",
"https://www.satnow.com/products/microwave-rf-diplexers/shf-communication-technologies/13-1742-shf-dx45r-x01",
"https://www.satnow.com/products/microwave-rf-diplexers/wiran/13-1374-dxb",
"https://www.satnow.com/products/microwave-rf-diplexers/shf-communication-technologies/13-1742-shf-dx45r-x02",
"https://www.satnow.com/products/microwave-rf-diplexers/shf-communication-technologies/13-1742-shf-dx45r-x01",
"https://www.satnow.com/products/microwave-rf-diplexers/shf-communication-technologies/13-1742-shf-dx45r-x02",
"https://www.satnow.com/products/microwave-rf-diplexers/shf-communication-technologies/13-1742-shf-dx65r",
"https://www.satnow.com/products/microwave-rf-diplexers/shf-communication-technologies/13-1742-shf-dx65r-hv100",
"https://www.satnow.com/products/microwave-rf-diplexers/shf-communication-technologies/13-1742-shf-dx110r"      
]

if __name__ == "__main__":
    main(urls)



from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Initialize Chrome WebDriver
driver = webdriver.Chrome()

# List to store all product URLs
all_product_urls = []

# Loop through pages 1 to 10
for page in range(1, 11):
    url = f"https://www.satnow.com/search/satellite-terminals/filters?page={page}&country=global"
    driver.get(url)

    try:
        # Wait until product links are available
        product_links = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//*[@id='pnlLatestProductsBox']/div[2]/div[1]/ul/li/a"))
        )

        # Extract product URLs and store them
        for link in product_links:
            product_url = link.get_attribute("href")
            all_product_urls.append(f'"{product_url}"')  # Wrap each URL in double quotes

    except Exception as e:
        print(f" Skipping page {page} due to error: {e}")

# Close the browser
driver.quit()

# Print all product URLs as double-quoted, comma-separated values
output_string = ",".join(all_product_urls)
print(output_string)

# Save the output to a CSV file
output_file = "satellite_terminals_urls.csv"
with open(output_file, mode="w", newline="", encoding="utf-8") as file:
    file.write(output_string)  # Writing URLs in double quotes, separated by commas

print(f" Scraping completed. Product URLs saved in {output_file}")


import sys
sys.stdout.reconfigure(encoding="utf-8")






from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv

# Initialize Chrome WebDriver
driver = webdriver.Chrome()

# CSV file to store results
output_file = "POWER_INDUCTORS_urls.csv"

# Open the file for writing (overwrite if exists)
with open(output_file, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file, quotechar='"', quoting=csv.QUOTE_MINIMAL)

    # Loop through pages 1 to 10
    for page in range(1, 201):
        url = f"https://www.satnow.com/search/power-inductors/filters?page={page}&country=global"
        driver.get(url)

        try:
            # Wait until product links are available
            product_links = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//*[@id='ContentPlaceHolder1_dListItems']/div/div[2]/div[1]/h3/a")
                )
            )

            # Extract and save product URLs
            for link in product_links:
                product_url = link.get_attribute("href")  # Extract href (Product URL)
                formatted_url = f'"{product_url}",'  # Ensure double quotes and comma
                writer.writerow([formatted_url])  # Write formatted URL to CSV
                print(formatted_url)  # Print output in required format

        except Exception as e:
            print(f"Skipping page {page} due to error: {e}")

# Close the browser
driver.quit()

print(f"Scraping completed. Product URLs saved in {output_file}")



