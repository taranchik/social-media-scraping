from dotenv import dotenv_values

# Load environment variables from .env file
env = dotenv_values('.env')

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time


class TwitterScraper():
  def __init__(self):
    # Initialize the driver (assuming Chrome)
    self._driver = webdriver.Chrome()

  def signIn(self, username, password):
    # Open Twitter
    self._driver.get("https://twitter.com/login")

    # Wait for the page to load
    time.sleep(5)

    # Log in (Replace 'your_username' and 'your_password' with your Twitter credentials)
    username_field = self._driver.find_element(By.NAME, "session[username_or_email]")
    password_field = self._driver.find_element(By.NAME, "session[password]")

    username_field.send_keys(username)
    password_field.send_keys(password)
    password_field.send_keys(Keys.RETURN)

    # Wait for login to complete
    time.sleep(5)

  def retreive_lastest_profile_tweets(self, username):
    # Navigate to a profile page or search for a hashtag
    # For a profile:
    self._driver.get(f"https://twitter.com/{username}")

    # Scroll to load tweets or find specific elements as needed
    # This is a simplistic way to scroll a bit; you may need more sophisticated scrolling logic
    self._driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # Add your logic here to parse tweets
    # This will depend on the structure of the page and can be quite complex

  def retreive_20_popular_tweets(self, hashtag):
    # For a hashtag search:
    self._driver.get(f"https://twitter.com/search?q=%23{hashtag}&src=typed_query")

  def close_scraper(self):
    # Close the driver
    self._driver.quit()

