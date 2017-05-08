#!/usr/bin/python3

import unittest
from datetime import datetime
from hacglist import Article, FeedDatabase


class TestFeedDatabase(unittest.TestCase):

    @classmethod
    def setUp(cls):
        cls.target = FeedDatabase()

    def test_singleton(self):
        actual = FeedDatabase()
        self.assertIsInstance(actual, FeedDatabase)
        self.assertEqual(self.target, actual)

    def test_push_and_peek(self):
        article = Article(1, "title", "http://localhost/feed", "Test content", None, datetime.now().isoformat())
        self.target.push(article)
        actual = list(self.target.peek())
        self.assertEqual(actual[0].title, "title")

    


if __name__ == "__main__":
    unittest.main(verbosity=2)
