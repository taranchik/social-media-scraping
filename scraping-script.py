from Crawler.reddit_scraper import RedditScraper
from Crawler.twitter_scraper import TwitterScraper
from dotenv import dotenv_values
from pymongo import MongoClient
import schedule
import time
import os


# Load environment variables from .env file
env = dotenv_values('.env')
# Load environment variable from docker-compose.yml file
MONGO_URI = os.environ.get('MONGO_URI')

client = MongoClient(MONGO_URI)
db = client['social_media_data']

twitter_tweets_collection = db['twitter_tweets']
twitter_tweets_collection.create_index([("tweet_id", 1)], unique=True)
twitter_profile_collection = db['twitter_profile_tweets']
twitter_profile_collection.create_index([("author", 1)], unique=True)
twitter_hashtag_collection = db['twitter_hashtag_tweets']
twitter_hashtag_collection.create_index([("hashtag", 1)], unique=True)

reddit_subreddit_posts_collection = db['reddit_subreddit_posts']
reddit_subreddit_posts_collection.create_index([("subreddit", 1)], unique=True)
reddit_posts_collection = db['reddit_posts']
reddit_posts_collection.create_index([("post_id", 1)], unique=True)

twitter = TwitterScraper(twitter_tweets_collection, twitter_profile_collection, twitter_hashtag_collection)
reddit = RedditScraper(reddit_posts_collection, reddit_subreddit_posts_collection)

def run_twitter_scraper():
    twitter.open()
    twitter.signIn(env['TWITTER_USERNAME'], env['TWITTER_PASSWORD'])
    twitter.retreive_lastest_profile_tweets('donaldtusk')
    twitter.retreive_popular_tweets('holiday')
    twitter.close()

def run_reddit_scraper():
    print("REDDIT")
    reddit.open()
    reddit.retreive_subreddit_posts('investing', {"number_of_comments": {"min": 100}})
    reddit.retreive_subreddit_posts('investing')
    reddit.retreive_subreddit_posts('layer_two')
    reddit.close()

def schedule_tasks():
    schedule.every().hour.do(run_reddit_scraper)
    schedule.every().hour.do(run_twitter_scraper)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    schedule_tasks()
