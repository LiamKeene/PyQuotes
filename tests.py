import unittest
import yql

from datetime import date, datetime, timedelta
from decimal import Decimal

from quote import get_yahoo_quote, get_yahoo_quote_history
from quote import date_range_generator, validate_date_range, LOOKBACK_DAYS


class GetYahooQuoteTestCase(unittest.TestCase):
    """Test Case for the `get_yahoo_quote` and `get_yahoo_quote_history` functions.

    The `get_yahoo_quote` function should query Yahoo's finance tables using YQL
    and return the latest quote for a particular stock (delayed by 20min).

     The `get_yahoo_quote_history` function should query Yahoo's finance tables
    using YQL and return the historical quote data for a particular stock over
    a given date range.

    The date range must be a list containing the start and end dates.  The dates
    may be date objects (with year, month and day specified), strings or empty.
    If the start date is empty a reasonable default is used.  If the end date is
    empty the current date is used.

    """
    def setUp(self):
        self.good_code = 'ABC'
        self.bad_code = 'A'

        self.columns = ['Name', 'Symbol', 'StockExchange', ]
        self.data = [u'ADEL BRTN FPO', u'ABC.AX', u'ASX', ]
        self.data_dict = dict(zip(self.columns, self.data))

        self.test_dates = [date(2013, 4, 10), date(2013, 4, 12)]
        self.test_date_range = ['2013-04-12', '2013-04-11', '2013-04-10']

    def test_quote_good_code(self):
        """get_yahoo_quote should return True given a valid code."""
        ret, quote = get_yahoo_quote(self.good_code)
        self.assertTrue(ret)

    def test_quote_bad_code(self):
        """get_yahoo_quote should raise an Exception given an invalid code."""
        self.assertRaises(Exception, get_yahoo_quote, self.bad_code)

    def test_quote_get_columns(self):
        """get_yahoo_quote should return the requested column only."""
        ret, quote = get_yahoo_quote(self.good_code, self.columns)

        for key, value in self.data_dict.items():
            self.assertTrue(key in quote)
            self.assertEqual(quote[key], self.data_dict[key])

    def test_history_good_code(self):
        """get_yahoo_quote_history should return True given a valid code."""
        ret, quotes = get_yahoo_quote_history(self.good_code, self.test_dates)

        self.assertTrue(ret)
        self.assertEqual(type(quotes), list)
        self.assertEqual(len(quotes), len(self.test_date_range))

        for i in range(len(quotes)):
            self.assertEqual(quotes[i]['Date'], self.test_date_range[i])


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
        # Valid date ranges can be the same day
        self.good_date_same_day = [date(2013, 4, 10), '2013-04-10']
        self.valid_date_same_day = [date(2013, 4, 10), date(2013, 4, 10)]

        # Number of days to lookback when no start_date is given
        self.lookback_days = LOOKBACK_DAYS

        # Define an end_date and start_date to reuse when required for other tests
        self.start_date = date(2013, 4, 10)
        self.end_date = date(2013, 4, 12)

        # Define start and end dates to be used when they are not specified
        self.no_end_date = datetime.today().date()
        self.no_start_date = self.end_date - timedelta(days=self.lookback_days)
        self.no_start_date_no_end_date = self.no_end_date - timedelta(days=self.lookback_days)

        # Test date range for when no start_date is given
        self.good_date_no_start = [None, self.end_date]
        # Test date range for when no end_date is given
        self.good_date_no_end = [self.start_date, '']
        # Test date range for when no start or end date is given
        self.good_date_no_start_no_end = ['', None]

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

    def test_good_date_same_day(self):
        """validate_date_range should return True given valid date range (same day)."""
        ret, date_range = validate_date_range(self.good_date_same_day)

        # Check function returned True
        self.assertTrue(ret)

        # Check data returned matches valid date range
        self.assertEqual(self.valid_date_same_day, date_range)

    def test_good_date_no_start(self):
        """validate_date_range should return True even without range start."""
        ret, date_range = validate_date_range(self.good_date_no_start)

        # Check function returned True
        self.assertTrue(ret)

        # Check data returned matches valid date range
        self.assertEqual(date_range, [self.no_start_date, self.end_date])

    def test_good_date_no_end(self):
        """validate_date_range should return True even without range end."""
        ret, date_range = validate_date_range(self.good_date_no_end)

        # Check function returned True
        self.assertTrue(ret)

        # Check data returned matches valid date range
        self.assertEqual(date_range, [self.start_date, self.no_end_date])

    def test_good_date_no_start_no_end(self):
        """validate_date_range should return True even without range start or end."""
        ret, date_range = validate_date_range(self.good_date_no_start_no_end)

        # Check function returned True
        self.assertTrue(ret)

        # Check data returned matches valid date range
        self.assertEqual(date_range, [self.no_start_date_no_end_date, self.no_end_date])

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


class DateRangeGeneratorTestCase(unittest.TestCase):
    """Test Case for the `date_range_generator` function.

    The `date_range_generator` function will return a generator of date objects
    if given a list containing the start and end dates of the range.

    """
    def setUp(self):
        self.start_date = date(2013, 4, 10)
        self.end_date = date(2013, 4, 12)

        self.start_datetime = datetime(2013, 4, 10, 15, 44, 56)
        self.end_datetime = datetime(2013, 4, 12, 6, 1, 25)

        self.generated_date_range = [
            date(2013, 4, 10), date(2013, 4, 11), date(2013, 4, 12)
        ]

        self.bad_date_wrong_types = ['2013-04-10', 2013]

    def test_date_range_generator(self):
        """date_range_generator should return a generator of dates if given date bounds."""
        date_gen = date_range_generator(self.start_date, self.end_date)

        self.assertEqual(list(date_gen), self.generated_date_range)

    def test_generate_datetime_range(self):
        """date_range_generator should return a generator of dates if given datetime bounds."""
        date_gen = date_range_generator(self.start_datetime, self.end_datetime)

        self.assertEqual(list(date_gen), self.generated_date_range)

    def test_generate_bad_date_wrong_types(self):
        """date_range_generator should raise an Exception if the inputs are not dates."""
        self.assertRaises(Exception, date_range_generator,
            (self.bad_date_wrong_types[0], self.bad_date_wrong_types[1]))


if __name__ == '__main__':
    unittest.main()
