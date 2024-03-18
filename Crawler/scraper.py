from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class Scraper():
  def __init__(self):
    self.options = Options()
    self.options.add_argument('--no-sandbox')
    self.options.add_argument('--headless')
    self.options.add_argument('--disable-dev-shm-usage')

    self._driver = None

  def open(self):
    self._driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.options)
    self._driver.maximize_window()

  def close(self):
     self._driver.close()