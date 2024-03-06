from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from pymongo import MongoClient

client = MongoClient('mongodb://127.0.0.1:27017/')
db = client['social_media_data']  # Use or create a database named 'social_media_data'

reddit_collection = db['reddit_posts']  # Use or create a collection for Reddit posts

twitter_profile_collection = db['twitter_profile_tweets']  # For tweets from a specific profile
twitter_profile_collection.create_index([("author_id", 1)], unique=True)

twitter_hashtag_collection = db['twitter_hashtag_tweets']  # For tweets related to a specific hashtag
twitter_hashtag_collection.create_index([("hashtag", 1)], unique=True)

# twitter_tweets_collection might grow over time and tweets in it might be not a subset of twitter_profile_collection or twitter_hashtag_collection
# Can be cleaned up a little bit over time based on tweet_ids subsets from twitter_profile_collection and twitter_hashtag_collection
twitter_tweets_collection = db['twitter_tweets']
twitter_tweets_collection.create_index([("tweet_id", 1)], unique=True)

class TwitterScraper():
  def __init__(self):
    self.load_timeout = 10

    self.profile_collection = twitter_profile_collection
    self.hashtag_collection = twitter_hashtag_collection
    self.tweets_collection = twitter_tweets_collection

    # Initialize the driver (assuming Chrome)
    self._driver = webdriver.Chrome()

  def get_articles_length(self):
    try:
        articles = WebDriverWait(self._driver, self.load_timeout).until(
            EC.presence_of_all_elements_located((By.XPATH, f"//div[@data-testid='cellInnerDiv']"))
        )
    except TimeoutException:
        return 0
    
    return len(articles)
  
  def has_tweet(self, index):
     try:
        # Skip if tweet is Ad (Ad tweet does not have time posted)
        WebDriverWait(self._driver, self.load_timeout).until(
            EC.presence_of_element_located((By.XPATH, f"//div[@data-testid='cellInnerDiv'][{index}]//article[@data-testid='tweet']//a[contains(@href, '/status/')]/time"))
        )

        # Wait for tweet loading or Skip if Container does not have Tweet inside
        WebDriverWait(self._driver, self.load_timeout).until(
            EC.presence_of_element_located((By.XPATH, f"//div[@data-testid='cellInnerDiv'][{index}]//article[@data-testid='tweet']"))
        )
     except TimeoutException:
        return False
     
     return True
  
  def find_tweet_index(self, previous_tweet_index, previous_tweet_id):
      for index in range(previous_tweet_index, 0, -1):
        tweet_id, _ = self.retreive_tweet(index)

        print(tweet_id, previous_tweet_id)
        print(index)
        print(type(tweet_id), type(previous_tweet_id))

        if tweet_id == previous_tweet_id:
           return index + 1
        
      raise Exception('Sufficient tweet_id not found')

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
        raise Exception("Timed out waiting for log in form to load.")

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
        raise Exception("Timed out waiting for password form to load.")
    
    try:
      WebDriverWait(self._driver, self.load_timeout).until(
          EC.presence_of_element_located((By.XPATH, '//a[@aria-label="Profile"]'))
      )
    except TimeoutException:
      raise Exception("Timed out waiting for log in.")

  def retreive_user_id(self, username):
    try:
      follow_button = WebDriverWait(self._driver, self.load_timeout).until(
          EC.presence_of_element_located((By.XPATH, f'//div[@aria-label="Follow @{username}"]'))
      )
      author_id = follow_button.get_attribute('data-testid').split('-')[0]
    except TimeoutException:
      raise Exception("Timed out waiting for follow button to appear.")

    return author_id
  
  def load_tweets(self, index):
    try:
      container = WebDriverWait(self._driver, self.load_timeout).until(
          EC.presence_of_element_located((By.XPATH, f"//div[@data-testid='cellInnerDiv'][{index}]"))
      )
      
      # Scroll the article into view
      self._driver.execute_script("arguments[0].scrollIntoView();", container)

      # Make sure the page has been loaded
      WebDriverWait(self._driver, self.load_timeout).until(
          EC.invisibility_of_element_located((By.XPATH, f"//div[@aria-label='Loading timeline']"))
      )
     
    except TimeoutException:
      raise Exception("Timed out waiting for tweet container with specified index to load.")
  
  def retreive_tweet(self, index):
    tweet_id = 0
    tweet = {}
    has_tweet = self.has_tweet(index)

    if not has_tweet:
       return tweet_id, tweet

    container_path = f"//div[@data-testid='cellInnerDiv'][{index}]//article[@data-testid='tweet']"

    try:
      container = WebDriverWait(self._driver, self.load_timeout).until(
          EC.element_to_be_clickable((By.XPATH, f"{container_path}"))
      )
      print(container.get_attribute('outerHTML'))
      
      tweet_id = WebDriverWait(container, self.load_timeout).until(
          EC.presence_of_element_located((By.XPATH, ".//a[contains(@href, '/status/')]"))).get_attribute("href").split('/')[-1]
      print(tweet_id)
      author = WebDriverWait(container, self.load_timeout).until(
          EC.presence_of_element_located((By.XPATH, ".//div[@data-testid='User-Name']/div/div/a"))).get_attribute("href").split('/')[-1]
      print(author)
      date = WebDriverWait(container, self.load_timeout).until(
          EC.presence_of_element_located((By.XPATH, ".//a[contains(@href, '/status/')]/time"))).get_attribute("datetime")
      print(date)
      text = WebDriverWait(container, self.load_timeout).until(
          EC.presence_of_element_located((By.XPATH, ".//div[@data-testid='tweetText']"))).text
      print(text)
      replies = WebDriverWait(container, self.load_timeout).until(
          EC.presence_of_element_located((By.XPATH, ".//div[@data-testid='reply']"))).text
      print("REPLIES: ", replies)
      reposts = WebDriverWait(container, self.load_timeout).until(
          EC.presence_of_element_located((By.XPATH, f".//div[@data-testid='retweet']"))).text
      print("REPOSTS: ", reposts)
      likes = WebDriverWait(container, self.load_timeout).until(
          EC.presence_of_element_located((By.XPATH, ".//div[@data-testid='like']"))).text
      print("LIKES: ", likes)
      views = WebDriverWait(container, self.load_timeout).until(
          EC.presence_of_element_located((By.XPATH, ".//div[@data-testid='reply']/parent::div/parent::div/div[4]"))).text
      print("VIEWS: ", views)
    except TimeoutException:
      raise Exception("Timed out waiting for tweet to load.")
    
    try:
        # Click on the article
        self._driver.execute_script("arguments[0].click();", container)

        # Make sure the page has been loaded
        WebDriverWait(self._driver, self.load_timeout).until(
            EC.invisibility_of_element_located((By.XPATH, f"//div[@aria-label='Loading timeline']"))
        )

        # Get author_id
        author_id = self.retreive_user_id(author)
        print(author_id)
        # Back on the article list
        self._driver.back()

        # Make sure the page has been loaded
        WebDriverWait(self._driver, self.load_timeout).until(
            EC.invisibility_of_element_located((By.XPATH, f"//div[@aria-label='Loading timeline']"))
        )
    except TimeoutException:
      raise Exception("Timed out waiting for going back from post page.")

    return tweet_id, {"author_id": author_id, "author": author, "date": date, "text": text, "replies": replies, "replies": replies, "reposts": reposts, "likes": likes, "views": views}
  
  def retreive_tweets(self, number_of_tweets):
    tweets_length = self.get_articles_length()
    tweet_index = 0
    tweet_ids = []
    last_author_id = ''
    last_author = ''
    
    while number_of_tweets != len(tweet_ids):
        tweet_index += 1
        print(tweet_index)

        if tweet_index > tweets_length:
            if not tweets_length:
              break
            else:
              # Scroll to the tweet_index
              self.load_tweets(tweet_index - 1)
              tweets_length = self.get_articles_length()
              tweet_index = self.find_tweet_index(tweets_length, tweet_ids[-1])

        tweet_id, tweet = self.retreive_tweet(tweet_index)

        if not tweet_id:
           continue

        print(tweet)
        self.tweets_collection.update_one({"tweet_id": tweet_id},{ "$set": { "updated_at": datetime.utcnow(), **tweet}}, upsert=True)
        tweet_ids.append(tweet_id)

        last_author_id = tweet["author_id"]
        last_author = tweet["author"]

    return tweet_ids, last_author_id, last_author
  
  def retreive_lastest_profile_tweets(self, username):
    self._driver.get(f"https://twitter.com/{username}")

    tweet_ids, author_id, author = self.retreive_tweets(20)

    self.profile_collection.update_one({"author_id": author_id}, {"$set": {"updated_at": datetime.utcnow(), "author": author, "tweet_ids": tweet_ids}}, upsert=True)

  def retreive_popular_tweets(self, hashtag):
    # For a hashtag search:
    self._driver.get(f"https://twitter.com/search?q=(%23{hashtag})&src=typed_query")
    
    tweet_ids, _, _ = self.retreive_tweets(20)
   
    self.hashtag_collection.update_one({"hashtag": hashtag}, {"$set": {"updated_at": datetime.utcnow(), "tweet_ids": tweet_ids}}, upsert=True)

  def close_scraper(self):
    # Close the driver
    self._driver.quit()