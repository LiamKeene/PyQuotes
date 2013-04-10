import unittest
import yql

from quote import get_yahoo_quote


class GetYahooQuoteTestCase(unittest.TestCase):
    """Test Case for the `get_yahoo_quote` function.

    The `get_yahoo_quote` function should query Yahoo's finance tables using YQL
    and return the latest quote for a particular stock (delayed by 20min).

    """
    def setUp(self):
        self.good_code = 'ABC'
        self.bad_code = 'A'

    def test_good_code(self):
        """get_yahoo_quote should return True given a valid code."""
        ret, quote = get_yahoo_quote(self.good_code)
        self.assertTrue(ret)

    def test_bad_code(self):
        """get_yahoo_quote should raise an Exception given an invalid code."""
        self.assertRaises(Exception, get_yahoo_quote, self.bad_code)


if __name__ == '__main__':
    unittest.main()

