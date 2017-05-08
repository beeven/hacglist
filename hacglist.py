#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import feedparser
import sqlite3


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Article(object):
    def __init__(self, feed_id, title, url, summary, thumbnail, pub_date):
        self.feed_id = feed_id
        self.title = title
        self.url = url
        self.summary = summary
        self.thumbnail = thumbnail
        self.pub_date = pub_date

class FeedDatabase(object, metaclass=Singleton):
    def __init__(self):
        self.conn = sqlite3.connect("feeds.sqlite")
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
                feed_id integer,
                title text,
                url text,
                summary text,
                thumbnail blob,
                pub_date text
            )
            """)

    def close(self):
        self.conn.close()

    def push(self, article):
        self.conn.execute("""insert into articles (feed_id, title, url, summary, thumbnail, pub_date) values (?,?,?,?,?,?)""",(article.feed_id, article.title, article.url, article.summary, article.thumbnail, article.pub_date))
        self.conn.commit()

    def peek(self, top=3):
        cursor = self.conn.cursor()
        ret = []
        for c in cursor.execute("""select article_id, feed_id, title, url, summary, thumbnail, pub_date from articles order by article_id desc limit ?""",(top,)):
            ret.insert(0,Article(c[1], c[2], c[3], c[4], c[5], c[6]))
        cursor.close()
        return ret

    def clear(self, skip=3):
        self.conn.execute("""delete from articles order by article_id offset ?""",(skip,))
        self.conn.commit()

    def get_last_updated(self, feed_id):
        cursor = self.conn.cursor()
        cursor.execute("""select last_updated from feeds where feed_id = ?""",(feed_id))
        r = cursor.fetchone()
        if r:
            return r[0]
        else:
            return None

    def set_feed_last_updated(self, feed_id, last_updated):
        pass

class HACGFetcher(object):
    def __init__(self):
        pass
    def load_cached(self):
        pass
    def fetch(self):
        r = requests.get("http://www.hacg.wiki/wp/feed")