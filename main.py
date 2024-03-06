from Crawler.twitter_scraper import TwitterScraper
from dotenv import dotenv_values

# Load environment variables from .env file
env = dotenv_values('.env')

if __name__ == "__main__":
    twitter = TwitterScraper()
    twitter.signIn(env['TWITTER_USERNAME'], env['TWITTER_PASSWORD'])
    # twitter.retreive_lastest_profile_tweets('donaldtusk')
    twitter.retreive_popular_tweets('Poland')