from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from Crawler.browser import Browser


class TwitterScraper(Browser):
  def __init__(self, tweets_collection, profile_collection, hashtag_collection):
    super().__init__()
    
    self.load_timeout = 10

    self.tweets_collection = tweets_collection
    self.profile_collection = profile_collection
    self.hashtag_collection = hashtag_collection

  def get_tweets(self):
    attempts_to_load = 0

    while True:
        try:
            # Get all tweets on the page
            articles = WebDriverWait(self._driver, self.load_timeout).until(
                EC.presence_of_all_elements_located((By.XPATH, f"//article[@data-testid='tweet']"))
            )
            
            return articles
        except TimeoutException:
            if attempts_to_load > 3:
              return []
            else:
              attempts_to_load += 1
  
  def load_tweets(self, tweet):
    attempts_to_load = 0
    initial_scroll_position = self._driver.execute_script("return window.pageYOffset;")

    while True:
        try:
          # Scroll into tweet view
          self._driver.execute_script("arguments[0].scrollIntoView();", tweet)

          # Make sure the page has been fully loaded
          WebDriverWait(self._driver, self.load_timeout).until(
              EC.invisibility_of_element_located((By.XPATH, f"//div[@aria-label='Loading timeline']"))
          )

          new_scroll_position = self._driver.execute_script("return window.pageYOffset;")

          if new_scroll_position > initial_scroll_position or attempts_to_load > 3:
             break
          else:
             attempts_to_load += 1

        except TimeoutException:
          if attempts_to_load > 3:
            raise Exception("Time out for waiting posts to load.")
          else:
            attempts_to_load += 1

  def is_tweet(self, tweet):
    attempts_to_load = 0

    while True:
        try:
            tweet.find_element(By.XPATH, f".//a[contains(@href, '/status/')]/time")

            return True
        except NoSuchElementException:
            return False
        except StaleElementReferenceException:
            if attempts_to_load > 3:
              raise Exception("Time out for date posted retreiving.")
            else:
              attempts_to_load += 1
  
  def signIn(self, username, password):
    # Open Twitter
    self._driver.get("https://twitter.com/login")

    try:
        username_input = WebDriverWait(self._driver, self.load_timeout).until(
            EC.presence_of_element_located((By.XPATH, '//input[@autocomplete="username"]'))
        )
        username_input.send_keys(username)

        next_button = WebDriverWait(self._driver, self.load_timeout).until(
            EC.presence_of_element_located((By.XPATH, '//span[text()="Next"]'))
        )
        next_button.click()
    except TimeoutException:
        raise Exception("Time out waiting for log in form to load.")

    try:
        password_input = WebDriverWait(self._driver, self.load_timeout).until(
            EC.presence_of_element_located((By.XPATH, '//input[@autocomplete="current-password"]'))
        )
        password_input.send_keys(password)

        log_in_button = WebDriverWait(self._driver, self.load_timeout).until(
            EC.presence_of_element_located((By.XPATH, '//span[text()="Log in"]'))
        )
        log_in_button.click()
    except TimeoutException:
        raise Exception("Time out waiting for password form to load.")
    
    try:
      WebDriverWait(self._driver, self.load_timeout).until(
          EC.presence_of_element_located((By.XPATH, '//a[@aria-label="Profile"]'))
      )
    except TimeoutException:
      raise Exception("Time out waiting for log in.")
    
  def handle_statistics(self, container, xpath):
     try:
        text = container.find_element(By.XPATH, xpath).text

        return text
     except NoSuchElementException:
        return 0

  def retreive_tweet(self, tweet):
      attempts_to_load = 0

      while True:
          try:
              tweet_id = tweet.find_element(By.XPATH, ".//a[contains(@href, '/status/')]").get_attribute("href").split('/')[-1]
              author = tweet.find_element(By.XPATH, ".//div[@data-testid='User-Name']/div/div/a").get_attribute("href").split('/')[-1]
              date = tweet.find_element(By.XPATH, ".//a[contains(@href, '/status/')]/time").get_attribute("datetime")
              text = self.handle_statistics(tweet, ".//div[@data-testid='tweetText']")
              replies = self.handle_statistics(tweet, ".//div[@data-testid='reply']")
              reposts = self.handle_statistics(tweet, ".//div[@data-testid='retweet']")
              likes = self.handle_statistics(tweet, ".//div[@data-testid='like']")
              views = self.handle_statistics(tweet, ".//div[@data-testid='reply']/parent::div/parent::div/div[4]")
              
              return tweet_id, {"author": author, "date": date, "text": text, "replies": replies, "replies": replies, "reposts": reposts, "likes": likes, "views": views}
          except StaleElementReferenceException:
              if attempts_to_load > 3:
                raise Exception("Time out for tweet data retreival.")
              else:
                attempts_to_load += 1

  def retreive_tweets(self, number_of_tweets):
    tweets = self.get_tweets()
    tweet_index = len(tweets)
    tweets_data = {}
    tweet_ids = []
    last_author = ''
    
    while tweets and number_of_tweets != len(tweets_data):
        tweet_index -= 1
        is_tweet = self.is_tweet(tweets[tweet_index])

        if is_tweet:
            tweet_id, tweet = self.retreive_tweet(tweets[tweet_index])

            if not tweet_index or tweet_id in tweets_data:
                self.load_tweets(tweets[tweet_index])
                tweets = self.get_tweets()
                tweet_index = len(tweets)
            else:
                self.tweets_collection.update_one({"tweet_id": tweet_id}, { "$set": { "updated_at": datetime.utcnow(), **tweet}}, upsert=True)
                tweets_data[tweet_id] = tweet
                tweet_ids.append(tweet_id)
                last_author = tweet["author"]
        
    return tweet_ids, last_author
  
  def retreive_lastest_profile_tweets(self, username):
    self._driver.get(f"https://twitter.com/{username}")

    tweet_ids, author = self.retreive_tweets(4)

    self.profile_collection.update_one({"author": author}, {"$set": {"updated_at": datetime.utcnow(), "author": author, "tweet_ids": tweet_ids}}, upsert=True)

  def retreive_popular_tweets(self, hashtag):
    self._driver.get(f"https://twitter.com/search?q=(%23{hashtag})&src=typed_query")
    
    tweet_ids, _ = self.retreive_tweets(20)
   
    self.hashtag_collection.update_one({"hashtag": hashtag}, {"$set": {"updated_at": datetime.utcnow(), "tweet_ids": tweet_ids}}, upsert=True)

  def run_scraper(self, username, password):
    self.open()
    self.signIn(username, password)
    self.retreive_lastest_profile_tweets('donaldtusk')
    self.retreive_popular_tweets('holiday')
    self.close()