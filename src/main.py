from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def main():
    driver = webdriver.Chrome()

    driver.get("https://www.bondsupermart.com/bsm/bond-selector")

    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.link-primary"))
        )
    except:
        driver.quit()
        
    for request in driver.requests:
        if request.response and request.response.status_code == 200 and request.response.headers["Content-Type"] == "application/json;charset=UTF-8":
            print(
                request.url
            )
    driver.quit()

if __name__ == "__main__":
    main()
