import unittest
import yql

from datetime import date
from decimal import Decimal

from quote import get_yahoo_quote, validate_date_range


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


class ValidateDateRangeTestCase(unittest.TestCase):
    """Test Case for the `validate_date_range` function.

    The `validate_date_range` function will return True if the given date range
    validates against a set of custom rules.  Date ranges are used to extract
    historical data for a given stock.

    A valid date range is a list of two elements; each element may be a date
    object or a string representation of the date.

    """
    def setUp(self):
        # The valid date range, which good date range inputs must match
        self.valid_date = [date(2013, 4, 10), date(2013, 4, 12)]

        # Some good date range inputs
        self.good_dates = [
            [date(2013, 4, 10), date(2013, 4, 12)],
            ['2013-04-10', '2013-04-12'],
            ['2013-04-10', date(2013, 4, 12)],
        ]

        # Some bad date range inputs
        self.bad_date_not_list = [2013, {}, '']
        self.bad_date_wrong_length = [
            [], ['2013-04-10'], ['2013-04-10', '2013-04-11', '2013-04-12', ]
        ]
        self.bad_date_wrong_types = [[2013, ''], [None, Decimal('2013')], ]
        self.bad_date_wrong_format = [date(2013, 4, 10), '12-04-2013']
        self.bad_date_backwards = ['2013-04-12', date(2013, 4, 10)]
        self.bad_date_future = [date(2020, 4, 10), '2020-04-12']

    def test_good_date(self):
        """validate_date_range should return True given valid date ranges."""
        for good_date in self.good_dates:
            ret, date_range = validate_date_range(good_date)

            # Check function returned True
            self.assertTrue(ret)

            # Check data returned matches valid date range
            self.assertEqual(self.valid_date, date_range)

    def test_bad_date_not_list(self):
        """validate_date_range should raise a TypeError given a non-list date range."""
        [self.assertRaises(TypeError, validate_date_range, not_list)
            for not_list in self.bad_date_not_list]

    def test_bad_date_wrong_length(self):
        """validate_date_range should raise a ValueError given a list of incorrect length."""
        [self.assertRaises(ValueError, validate_date_range, wrong_length)
            for wrong_length in self.bad_date_wrong_length]

    def test_bad_date_wrong_type(self):
        """validate_date_range should raise a TypeError given a list with wrong types."""
        self.assertRaises(TypeError, validate_date_range, self.bad_date_wrong_types)

    def test_bad_date_wrong_format(self):
        """validate_date_range should raise a TypeError given a list with wrong format."""
        self.assertRaises(ValueError, validate_date_range, self.bad_date_wrong_format)

    def test_bad_date_backwards(self):
        """validate_date_range should raise an Exception given a backwards date range."""
        self.assertRaises(ValueError, validate_date_range, self.bad_date_backwards)

    def test_bad_date_future(self):
        """validate_date_range should raise an Exception given a future date range."""
        self.assertRaises(ValueError, validate_date_range, self.bad_date_future)


if __name__ == '__main__':
    unittest.main()

