from bs4 import BeautifulSoup
import requests
import pandas as pd
import json
import re
from datetime import date


class PageScraper:

    def __init__(self, url):
        self.url = url

    def get_data(self):
        resp = requests.get(self.url)
        html = resp.text
        soup = BeautifulSoup(html, 'lxml')
        self.data = json.loads(soup.find("script", type="application/ld+json").contents[0])

    def get_post(self):
        try:
            return self.data['caption']
        except:
            return None

    def get_date(self):
        return self.data['uploadDate']

    def get_location(self):
        try:
            return self.data['contentLocation']['name']
        except:
            return None

    def get_author(self):
        return self.data['author']['alternateName']

    def get_comment_counter(self):
        return self.data['commentCount']

    def get_likes_counter(self):
        return self.data['interactionStatistic']['userInteractionCount']

    def df_constructor(self, keys_list):
        self.get_data()
        getters = {
            'post': self.get_post(),
            'date': self.get_date(),
            'location': self.get_location(),
            'author': self.get_author(),
            'comment': self.get_comment_counter(),
            'like': self.get_likes_counter()
        }
        d = {}
        for key in keys_list:
            d[key] = [getters[key]]
        return pd.DataFrame(data=d, index=None)


class LinksScraper:

    def __init__(self, url):
        self.url = url

    def get_profile(self):
        resp = requests.get(self.url)
        html = resp.text
        soup = BeautifulSoup(html, 'lxml')
        data = soup.findAll("script", type="text/javascript")[3]
        jsonValue = '{%s}' % (data.contents[0].partition('{')[2].rpartition('}')[0],)
        value = json.loads(jsonValue)
        entry_data = value['entry_data']
        profile = entry_data['ProfilePage'][0]
        return profile

    def get_followers(self, profile):
        return profile['graphql']['user']['edge_followed_by']['count']

    def get_links(self, profile):
        urls = []
        for k in profile['graphql']['user']['edge_owner_to_timeline_media']['edges']:
            shortcode = k['node']['shortcode']
            page_url = '/'.join([re.sub(r'/$', '', self.url), 'p', shortcode])
            urls.append(page_url)
        return urls



if __name__ == '__main__':
    cols = ['date', 'like', 'post', 'location']
    df = pd.DataFrame(columns=cols, index=None)
    url = 'https://www.instagram.com/lisaneradovskaya/'
    scraper = LinksScraper(url)
    profile_data = scraper.get_profile()
    urls = scraper.get_links(profile_data)
    author = re.findall(r'https://www.instagram.com/(\w+)/?', url)[0]
    for url in urls:
        p = PageScraper(url)
        df = df.append(p.df_constructor(cols), ignore_index=True)
    print(df)
    today = date.today()
    df.to_csv(f'output_{author}_{today}.csv')
