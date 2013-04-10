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

        self.columns = ['Name', 'Symbol', 'StockExchange', ]
        self.data = [u'ADEL BRTN FPO', u'ABC.AX', u'ASX', ]
        self.data_dict = dict(zip(self.columns, self.data))

    def test_good_code(self):
        """get_yahoo_quote should return True given a valid code."""
        ret, quote = get_yahoo_quote(self.good_code)
        self.assertTrue(ret)

    def test_bad_code(self):
        """get_yahoo_quote should raise an Exception given an invalid code."""
        self.assertRaises(Exception, get_yahoo_quote, self.bad_code)

    def test_get_columns(self):
        """get_yahoo_quote should return the requested column only."""
        ret, quote = get_yahoo_quote(self.good_code, self.columns)

        for key, value in self.data_dict.items():
            self.assertTrue(key in quote)
            self.assertEqual(quote[key], self.data_dict[key])


if __name__ == '__main__':
    unittest.main()

