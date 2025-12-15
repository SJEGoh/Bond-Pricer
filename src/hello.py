from selenium.webdriver.chrome.options import Options
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import re
import pandas as pd

class get_Pages:
    def __init__(self, driver, url):
        self.driver = driver
        self.url = url
        self.JSON_list = []

    def get(self, wait_for):
        self.driver.get(self.url)
        try:
            _ = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, wait_for))
            )
        except:
            self.driver.quit()
            raise ValueError("Unsuccessful retrieval")

        for request in self.driver.requests:
            if request.response and request.response.status_code == 200 and re.search("\w*/bond/\w*", request.url):
                self.JSON_list.append(request.url)
            
        print(f"Retrieved: {len(self.JSON_list)}")
        self.driver.quit()
        return True
                    
    def get_list(self):
        return self.JSON_list
            

def main():
    driver = webdriver.Chrome()
    getter = get_Pages(driver, "https://www.bondsupermart.com/bsm/bond-selector")
    getter.get("a.link-primary")
    # Compiles websites containing bond sites
    # Go into each one, return list of bond IDs
    rfr = 0.02
    js = getter.get_list() # Returns list of URLS

    r = requests.get(js[0])
    j = r.json()
    data = j["Data"]

    df = pd.DataFrame.from_dict(data, orient="index")[['0', '111752', '100006', '110023', '110153']]
    # For bond pricing formula 
    # face value = 100
    # redemption = 100
    # P = (coupon * sum(face value)/(rate of dispersement))/
    df.columns = ['name', 'id', 'ask', 'coupon', 'maturity']
    print(df.head())
    # 0: name of bond
    # 111752: ID of bond (can use to access factsheet)
    # 100006: Ask price
    # 110023: Coupon rate
    # 110153: Maturity date
    # Get frequency from here: https://www.bondsupermart.com/main/ws/bond-calculator/calculate-price-from-yield?issueCode=US91282CDJ71&settlementDate=17%20Dec%202025&yieldPercentage=1.375&yieldType=YTM


if __name__ == "__main__":
    main()


'''
https://www.bondsupermart.com/main/ws/
bond-calculator/calculate-price-from-yield?
issueCode=US91282CDJ71&settlementDate=17%
20Dec%202025&yieldPercentage=1.375&yieldType=YTM

f"https://www.bondsupermart.com/main/ws/
bond-calculator/calculate-price-from-yield?
issueCode={bond_id}&settlementDate="
'''
