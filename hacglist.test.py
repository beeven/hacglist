#!/usr/bin/python3

import unittest
from datetime import datetime
from hacglist import Article, FeedDatabase, Feed


class TestFeedDatabase(unittest.TestCase):

    @classmethod
    def setUp(cls):
        cls.target = FeedDatabase()

    def test_singleton(self):
        actual = FeedDatabase()
        self.assertIsInstance(actual, FeedDatabase)
        self.assertEqual(self.target, actual)

    def test_push_and_peek(self):
        article1 = Article(1, "title 1", "http://localhost/feed", "Test content 1", None, datetime(2017,5,9,17,0,0))
        article2 = Article(1, "title 2", "http://localhost/feed", "Test content 2", None, datetime(2017,5,9,18,0,0))
        article3 = Article(1, "title 3", "http://localhost/feed", "Test content 3", None, datetime(2017,5,9,19,0,0))
        self.target.push(article1)
        self.target.push(article2)
        self.target.push(article3)
        actual = list(self.target.peek(2))
        self.assertEqual(len(actual), 2)
        self.assertEqual(actual[0].title, "title 3")

        actual = list(self.target.peek(-1))
        self.assertEqual(len(actual), 3)


    def test_clear(self):
        article1 = Article(1, "title 1", "http://localhost/feed", "Test content 1", None, datetime(2017,5,9,17,0,0))
        article2 = Article(1, "title 2", "http://localhost/feed", "Test content 2", None, datetime(2017,5,9,18,0,0))
        article3 = Article(1, "title 3", "http://localhost/feed", "Test content 3", None, datetime(2017,5,9,19,0,0))
        self.target.push(article1)
        self.target.push(article2)
        self.target.push(article3)
        self.target.clear(2)
        actual = list(self.target.peek())
        self.assertEqual(len(actual), 2)
        self.assertEqual(actual[1].title, "title 2")

        self.target.clear(-5)
        actual = list(self.target.peek())
        self.assertEqual(len(actual), 0)

    def test_set_and_get_last_updated(self):
        expect = datetime(2017, 5, 9, 12, 42, 0, 35)
        self.target.set_last_updated(expect)
        actual = self.target.get_last_updated()
        self.assertEqual(expect, actual)

    def test_set_and_get_feed(self):
        expect = Feed(1, "test feed", "http://localhost/feed", datetime(2017,5,9,17,0,0))
        self.target.set_feed(expect)
        actual = self.target.get_feed()
        self.assertEqual(actual.name, "test feed")
        self.assertEqual(actual.last_updated, expect.last_updated)
    


if __name__ == "__main__":
    unittest.main(verbosity=2)
