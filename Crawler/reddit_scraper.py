from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from Crawler.browser import Browser


class RedditScraper(Browser):
  def __init__(self, posts_collection, subreddit_posts_collection):
    super().__init__()
    
    self.load_timeout = 10

    self.posts_collection = posts_collection
    self.subreddit_posts_collection = subreddit_posts_collection

  def get_posts(self, initial_posts_length):
    attempts_to_load = 0

    while True:
        try:
            # Wait for the number of posts to increase
            WebDriverWait(self._driver, self.load_timeout).until(
                lambda d: len(d.find_elements(By.XPATH, "//article")) > initial_posts_length
            )

            # Get all articles on the page
            articles = WebDriverWait(self._driver, self.load_timeout).until(
                EC.presence_of_all_elements_located((By.XPATH, f"//article"))
            )
            
            return articles
        except TimeoutException:
            if attempts_to_load > 3:
              return []
            else:
              attempts_to_load += 1
    
  
  def load_posts(self, article):
    attempts_to_load = 0
    initial_scroll_position = self._driver.execute_script("return window.pageYOffset;")

    while True:
        try:
          # Scroll into post's article view
          self._driver.execute_script("arguments[0].scrollIntoView();", article)

          # Make sure the page has been fully loaded
          WebDriverWait(self._driver, self.load_timeout).until(
              EC.invisibility_of_element_located((By.XPATH, f"//faceplate-partial[@loading='programmatic' and @hasbeenloaded='true']"))
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
    
  def is_pinned_post(self, article):
    try:
        article.find_element(By.CSS_SELECTOR, f"shreddit-status-icons svg.hidden.stickied-status")

        return False
    except NoSuchElementException:
        return True

 
  def retreive_post(self, article):
      attempts_to_load = 0
      
      while True:
          try:
              post_id = article.find_element(By.XPATH, "./shreddit-post").get_attribute("id").split('_')[-1]
              title = article.get_attribute("aria-label")
              content = article.find_element(By.XPATH, ".//a[@slot='text-body']").text
              number_of_comments = article.find_element(By.XPATH, "./shreddit-post").get_attribute("comment-count")
              rating = article.find_element(By.XPATH, "./shreddit-post").get_attribute("score")
              
              return post_id, {"post_id": post_id, "title": title, "content": content, "number_of_comments": number_of_comments, "rating": rating}
          except StaleElementReferenceException:
              if attempts_to_load > 3:
                raise Exception("Time out for post data retreival.")
              else:
                attempts_to_load += 1

  def convert_to_number(self, str_number):
      suffixes = {
          'K': 1000,
          'M': 1000000,
          'B': 1000000000,
      }

      # If the value is None or str_number does not contain suffix
      if not str_number or not str_number[-1] in suffixes:
         return 0
      
      multiplier = 1

      if str_number[-1] in suffixes:
          multiplier = suffixes[str_number[-1]]
          str_number = str_number[:-1]  # Remove the suffix character
      
      try:
          return float(str_number) * multiplier
      except ValueError:
          # Handle the case where the input string is not a valid number
          return 0

  def match_the_filter(self, filter, value):
      valid_number = self.convert_to_number(value)

      if filter:
          if "min" in filter and "max" in filter:
              return filter["min"] <= valid_number <= filter["max"]
          elif "min" in filter:
                  return valid_number >= filter["min"]
          elif "max" in filter:
              return valid_number <= filter["max"]
      else:
         return True
              
      return False

  def retreive_posts(self, number_of_posts, filters={}):
    posts = self.get_posts(0)
    post_index = 0
    post_ids = []
    
    while posts and number_of_posts != len(post_ids):
        is_pinned = self.is_pinned_post(posts[post_index])
        
        if not is_pinned:
            post_id, post = self.retreive_post(posts[post_index])
            
            comments_filter_match = self.match_the_filter(filters.get("number_of_comments", {}), post["number_of_comments"])
            rating_filter_match = self.match_the_filter(filters.get("rating", {}), post["rating"])

            if comments_filter_match and rating_filter_match:
                self.posts_collection.update_one({"post_id": post_id},{ "$set": { "updated_at": datetime.utcnow(), **post}}, upsert=True)
                post_ids.append(post_id)
        
        post_index += 1

        if len(posts) == post_index:
          self.load_posts(posts[post_index - 1])
          posts = self.get_posts(len(posts))

    return post_ids
  
  def retreive_subreddit_posts(self, subreddit, filters={}):
    self._driver.get(f"https://www.reddit.com/r/{subreddit}/")
    
    post_ids = self.retreive_posts(100, filters)
   
    self.subreddit_posts_collection.update_one({"subreddit": subreddit}, {"$set": {"updated_at": datetime.utcnow(), "post_ids": post_ids}}, upsert=True)

  def run_scraper(self):
    self.open()
    # Example of Reddit filters (avaliable by rating and number_of_comments)
    # reddit.retreive_subreddit_posts('investing', {"number_of_comments": {"min": 100}})
    self.retreive_subreddit_posts('investing')
    self.retreive_subreddit_posts('layer_two')
    self.close()