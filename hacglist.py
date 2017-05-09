#!/usr/bin/env python3

import requests
import datetime
from bs4 import BeautifulSoup
import feedparser
import sqlite3
import dateutil.parser
from PIL import Image
from io import BytesIO


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Article(object):
    def __init__(self, article_id, title=None, url=None, summary=None, thumbnail=None, pub_date=None, feed_id=1):
        self.article_id = article_id
        self.title = title
        self.url = url
        self.summary = summary
        self.thumbnail = thumbnail
        self.pub_date = pub_date
        self.feed_id = feed_id

class Feed(object):
    def __init__(self, feed_id, name, url, last_updated):
        self.feed_id = feed_id
        self.name = name
        self.url = url
        if isinstance(last_updated, datetime.datetime):
            self.last_updated = last_updated
        elif last_updated is None:
            self.last_updated = dateutil.parser.parse("2017-05-08T00:00:00Z")
        else:
            self.last_updated = dateutil.parser.parse(last_updated)

class FeedDatabase(object, metaclass=Singleton):

    def __init__(self, filename=":memory:"):
        self.conn = sqlite3.connect(filename)
        self.conn.execute("""
            create table if not exists feeds (
                feed_id integer primary key,
                name text,
                url text,
                last_updated text
            )""")
        self.conn.execute("""
            create table if not exists articles (
                article_id integer primary key,
                title text,
                url text,
                summary text,
                thumbnail blob,
                pub_date text,
                feed_id integer
            )
            """)

        # currently only support hacg
        self.conn.execute("""
            insert or ignore into feeds (feed_id, name, url) values (1, "hacg", "http://www.hacg.wiki/wp/feed") 
        """)

    def close(self):
        self.conn.close()

    def push(self, article):
        self.conn.execute("""insert into articles (feed_id, title, url, summary, thumbnail, pub_date) values (?,?,?,?,?,?)""", (article.feed_id, article.title, article.url, article.summary, article.thumbnail, article.pub_date))
        self.conn.commit()

    def peek(self, top=3):
        cursor = self.conn.cursor()
        if top >= 0:
            for c in cursor.execute("""select article_id, title, url, summary, thumbnail, pub_date, feed_id from articles order by article_id desc limit ?""",(top,)):
                yield Article(*c)
        else:
            for c in cursor.execute("""select article_id, title, url, summary, thumbnail, pub_date, feed_id from articles order by article_id"""):
                yield Article(*c)
        cursor.close()

    def clear(self, skip=3):
        if skip >= 0:
            self.conn.execute("""delete from articles where article_id not in (select article_id from articles order by article_id desc limit ?)""", (skip,))
        else:
            self.conn.execute("""delete from articles""")
        self.conn.commit()

    def get_articles_needing_image(self):
        cursor = self.conn.cursor()
        for c in cursor.execute("""select article_id, url from articles where thumbnail is Null """):
            yield Article(article_id=c[0], url=c[1])
        cursor.close()

    def update_article_image(self, article):
        self.conn.execute("""update articles set thumbnail = ? where article_id = ?""", (article.thumbnail, article.article_id))
        self.conn.commit()

    def get_last_updated(self, feed_id=1):
        cursor = self.conn.cursor()
        cursor.execute("""select last_updated from feeds where feed_id = ?""", (feed_id,))
        r = cursor.fetchone()
        if r:
            return dateutil.parser.parse(r[0])
        else:
            return None

    def set_last_updated(self, last_updated, feed_id=1):
        cursor = self.conn.cursor()
        cursor.execute("""update feeds set last_updated = ? where feed_id = ?""", (last_updated, feed_id))
        cursor.close()
        self.conn.commit()
        pass

    def get_feed(self, feed_id=1):
        cursor = self.conn.cursor()
        cursor.execute("""select feed_id, name, url, last_updated from feeds where feed_id = ?""", (feed_id,))
        r = cursor.fetchone()
        if r:
            return Feed(*r)
        else:
            return None

    def set_feed(self, feed):
        self.conn.execute("""update feeds set name = ?, url = ?, last_updated = ? where feed_id = ?""",(feed.name, feed.url, feed.last_updated, feed.feed_id))
        self.conn.commit()



class HACGFetcher(object):
    def __init__(self, db_file=":memory:"):
        self.db = FeedDatabase(db_file)
        pass

    def load_cached(self):
        return list(self.db.peek())

    def fetch(self):
        new_feed = feedparser.parse(self.db.get_feed().url)
        old_feed = self.db.get_feed()
        new_feed_time = dateutil.parser.parse(new_feed['updated'])
        print("New_feed_time: {0}".format(new_feed_time))
        print("Old_feed_time: {0}".format(old_feed.last_updated))
        if new_feed_time <= old_feed.last_updated:
            print("no need to update")
            return

        entries = new_feed['entries']
        self.db.clear(3-len(entries))
        for entry in entries:
            article = Article(None, entry['title'], entry['link'], entry['summary'], None, dateutil.parser.parse(entry['published']))
            self.db.push(article)


        self.db.set_last_updated(new_feed_time)

        self.load_images()

    def load_images(self):
        for article in self.db.get_articles_needing_image():
            print("loading web page of {0}".format(article.article_id))
            r = requests.get(article.url)
            if not r.ok:
                return
            html = BeautifulSoup(r.content, "html.parser")
            img_elem = html.find("article").find("img")
            if not img_elem:
                return

            print("loading image of {0}".format(article.article_id))
            img_url = img_elem["src"]
            r = requests.get(img_url)
            if not r.ok: return
            img = Image.open(BytesIO(r.content))

            img.thumbnail((300, 300))
            img_data = BytesIO()
            img.save(img_data, "JPEG")
            img.close()
            article.thumbnail = img_data.getvalue()
            img_data.close()
            self.db.update_article_image(article)



if __name__ == "__main__":
    fetcher = HACGFetcher(db_file="feeds.sqlite")
    fetcher.fetch()
