# Web Scraping

> The application is composed of an advanced Python script that will scrape the 100 latest posts from two chosen subreddits on Reddit and the latest tweets from a specified Twitter profile. Additionally, it will retrieve the 20 most popular tweets related to a specific hashtag on Twitter.

---

### Table of Contents

- [Description](#description)
- [How To Use](#how-to-use)
- [References](#references)
- [Author Info](#author-info)

---

## Description

The application developed using Python utilizing Selenium WebDriver. All scraped data is stored in a NoSQL database, such as MongoDB. Easy deployment is facilitated through Docker containers. Docker is utilized to package the scraper into a container, allowing for seamless deployment and execution across various environments. The script is designed to automatically schedule and execute data scraping tasks every hour. Additionally, optional filtering of Reddit posts is integrated to precede their storage in the database, operating according to specific criteria such as minimum number of comments and rating.

---

## How To Use

#### Installation

Copy and paste the following commands into the terminal.

1. Fetch the **web-scraping** in the current directory.

```
git clone https://github.com/taranchik/web-scraping
```

2. Navigate to the application directory.

```
cd web-scraping
```

3. Rename env-example to .env.

```
mv env-example .env
```

4. Edit the file using nano or any other editor of your choice to fill in the empty fields.

```
nano .env
```

5. Easily deploy the application using **Docker**.

```
docker-compose up -d
```

---

## References

[Python](https://www.python.org/)

[Selenium WebDriver](https://www.selenium.dev/documentation/webdriver/)

[MongoDB](https://www.mongodb.com/)

[Docker](https://www.docker.com/)

---

## Author Info

- LinkedIn - [Viacheslav Taranushenko](https://www.linkedin.com/in/viacheslav-taranushenko-727466187/)
- GitHub - [@taranchik](https://github.com/taranchik)
- GitLab - [@taranchik](https://gitlab.com/taranchik)
- Twitter - [@viataranushenko](https://twitter.com/viataranushenko)

[Back To The Top](#website-elements)
