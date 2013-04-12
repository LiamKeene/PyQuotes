import unittest
import yql

from datetime import date, datetime, timedelta
from decimal import Decimal

from quote import raw_yahoo_quote, raw_yahoo_csv_quote
from quote import raw_yahoo_quote_history, raw_yahoo_csv_quote_history
from quote import parse_yahoo_csv_quote_symbols, get_yahoo_csv_quote_fields
from quote import parse_yahoo_csv_quote, parse_yahoo_csv_quote_history
from quote import date_range_generator, validate_date_range, LOOKBACK_DAYS


class RawYahooQuoteTestCase(unittest.TestCase):
    """Test Case for Yahoo quote functions.

    The `raw_yahoo_quote` function should query Yahoo's finance tables using YQL
    and return the latest quote for a particular stock (delayed by 20min).

    The `raw_yahoo_csv_quote` function should query Yahoo's finance CSV API and
    return the latest quote for a particular stock (delayed by 20min).

    The `raw_yahoo_quote_history` function should query Yahoo's finance tables
    using YQL and return the historical quote data for a particular stock over
    a given date range.

    The `raw_yahoo_csv_quote_history` function should query Yahoo's finance CSV
    API and return the historical quote data for a particular stock over a given
    date range.

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

        self.csv_columns = 'nsx'
        self.csv_data = '"ADEL BRTN FPO","ABC.AX","ASX"\r\n'

        self.test_dates = [date(2013, 4, 10), date(2013, 4, 12)]
        self.test_date_range = ['2013-04-12', '2013-04-11', '2013-04-10']

    def test_quote_good_code(self):
        """raw_yahoo_quote should return True given a valid code."""
        ret, quote = raw_yahoo_quote(self.good_code)
        self.assertTrue(ret)

    def test_quote_bad_code(self):
        """raw_yahoo_quote should raise an Exception given an invalid code."""
        self.assertRaises(Exception, raw_yahoo_quote, self.bad_code)

    def test_quote_get_columns(self):
        """raw_yahoo_quote should return the requested column only."""
        ret, quote = raw_yahoo_quote(self.good_code, self.columns)

        for key, value in self.data_dict.items():
            self.assertTrue(key in quote)
            self.assertEqual(quote[key], self.data_dict[key])

    def test_csv_quote_good_code(self):
        """raw_yahoo_csv_quote should return True given a valid code."""
        ret, quote = raw_yahoo_csv_quote(self.good_code)
        self.assertTrue(ret)

    def test_csv_quote_bad_code(self):
        """raw_yahoo_csv_quote should raise an Exception given an invalid code."""
        self.assertRaises(Exception, raw_yahoo_csv_quote, self.bad_code)

    def test_csv_quote_get_columns(self):
        """raw_yahoo_csv_quote should return the requested columns only."""
        ret, quote = raw_yahoo_csv_quote(self.good_code, self.csv_columns)

        self.assertTrue(ret)
        self.assertEqual(quote, self.csv_data)

    def test_history_good_code(self):
        """raw_yahoo_quote_history should return True given a valid code."""
        ret, quotes = raw_yahoo_quote_history(self.good_code, self.test_dates)

        self.assertTrue(ret)
        self.assertEqual(type(quotes), list)
        self.assertEqual(len(quotes), len(self.test_date_range))

        for i in range(len(quotes)):
            self.assertEqual(quotes[i]['Date'], self.test_date_range[i])

    def test_csv_history_good_code(self):
        """raw_yahoo_csv_quote_history should return True given a valid code."""
        ret, quotes = raw_yahoo_csv_quote_history(self.good_code, self.test_dates)
        self.assertTrue(ret)

        # This would ideally be done in another function
        quotes = quotes.split('\n')
        # Remove the headers
        quotes.pop(0)
        # Remove empty elements
        quotes.remove('')

        # Check the length and content of the quotes
        self.assertEqual(len(quotes), len(self.test_date_range))
        for i in range(len(quotes)):
            quote = quotes[i].split(',')
            self.assertEqual(quote[0], self.test_date_range[i])


class ParseYahooCSVQuoteSymbolsTestCase(unittest.TestCase):
    """Test Case for the `parse_yahoo_csv_quote_symbols` function.

    The `parse_yahoo_csv_quote_symbols` function should parse a string of Yahoo CSV tags
    into a tuple of those tags.  Not as simple as it sounds as some tags consist
    of a letter and number.

    """
    def setUp(self):
        self.parsed_symbols_dict = {
            'nsx': ('n', 's', 'x'),
            'ohgl1v': ('o', 'h', 'g', 'l1', 'v', ),
            'nsl1hr5j1ym3m4n4xd1': (
                'n', 's', 'l1', 'h', 'r5', 'j1', 'y', 'm3', 'm4', 'n4', 'x', 'd1'
            ),
        }

    def test_parse_yahoo_csv_quote_symbols(self):
        """parse_yahoo_csv_quote_symbols should return a correctly parsed list of symbols."""
        [self.assertEqual(parse_yahoo_csv_quote_symbols(symbol_str), symbol_list)
            for symbol_str, symbol_list in self.parsed_symbols_dict.items()]


class GetYahooCSVQuoteFieldsTestCase(unittest.TestCase):
    """Test Case for the `get_yahoo_csv_quote_fields` function.

    The `get_yahoo_csv_quote_fields` function should return a tuple of two-tuples
    that contain the single CSV quote field names and data type given field symbols.

    The symbols are found at this url http://www.jarloo.com/yahoo_finance/ and
    are hard-coded here (a db model or fixtures may be useful in the future).

    """
    def setUp(self):
        self.test_data = [
            [
                ('n', 's', 'x', 'l1'),
                (
                    ('Name', str), ('Symbol', str), ('Exchange', str), ('Close', Decimal),
                ),
            ],
            [
                ('s', 'o', 'h', 'g', 'l1', 'v'),
                (
                    ('Symbol', str), ('Open', Decimal), ('High', Decimal),
                    ('Low', Decimal), ('Close', Decimal), ('Volume', Decimal),
                ),
            ]
        ]
        self.test_unknown_symbols = [
            ('f', ),
        ]

    def test_get_yahoo_csv_quote_fields(self):
        """get_yahoo_csv_quote_fields should return dictionary from list of symbols."""
        [self.assertEqual(get_yahoo_csv_quote_fields(symbol_list), field_dict)
            for symbol_list, field_dict in self.test_data]

    def test_unknown_symbols(self):
        """get_yahoo_csv_quote_fields should raise Exception if the symbol is inknown."""
        [self.assertRaises(Exception, get_yahoo_csv_quote_fields, symbol_list)
            for symbol_list in self.test_unknown_symbols]


class ParseYahooQuoteTestCase(unittest.TestCase):
    """Test Case for the `parse_yahoo_csv_quote` and `parse_yahoo_csv_quote_history` functions.

    The `parse_yahoo_csv_quote` function should correctly parse the information
    from a Yahoo CSV stock quote.

    The `parse_yahoo_csv_quote_history` function should correctly parse the information
    from a Yahoo CSV stock history.

    """
    def setUp(self):
        # The single quote will be dependant on the columns that are requested
        self.quote_single = '"ABC.AX",3.330,1351200\r\n'
        # Tuple of two-tuples containing the requested fields and data types
        self.quote_fields = (('Code', str), ('Close', Decimal), ('Volume', Decimal), )

        self.parsed_single = {
            'Code': 'ABC.AX', 'Close': Decimal('3.330'), 'Volume': Decimal('1351200'),
        }

        # The historical quote has defined headers (the first row of CSV data)
        self.quote_history = 'Date,Open,High,Low,Close,Volume,Adj Close\n' \
            '2013-04-12,3.36,3.38,3.31,3.33,1351200,3.33\n' \
            '2013-04-11,3.39,3.41,3.33,3.34,1225300,3.34\n' \
            '2013-04-10,3.39,3.41,3.38,3.40,2076700,3.40\n'

        self.parsed_history = [
            {
                'Date': '2013-04-12', 'Open': '3.36', 'High': '3.38', 'Low': '3.31',
                'Close': '3.33', 'Volume': '1351200', 'Adj Close': '3.33',
            },
            {
                'Date': '2013-04-11', 'Open': '3.39', 'High': '3.41', 'Low': '3.33',
                'Close': '3.34', 'Volume': '1225300', 'Adj Close': '3.34',
            },
            {
                'Date': '2013-04-10', 'Open': '3.39', 'High': '3.41', 'Low': '3.38',
                'Close': '3.40', 'Volume': '2076700', 'Adj Close': '3.40',
            },
        ]

    def test_parse_yahoo_csv_quote_single(self):
        """parse_yahoo_csv_quote should be able to parse good quote."""
        quote = parse_yahoo_csv_quote(self.quote_single, self.quote_fields)

        for key, value in self.parsed_single.items():
            self.assertTrue(key in quote)
            self.assertEqual(quote[key], self.parsed_single[key])

    def test_parse_yahoo_csv_quote_history(self):
        """parse_yahoo_csv_quote_history should be able to parse good historical quotes."""
        self.assertEqual(parse_yahoo_csv_quote_history(self.quote_history), self.parsed_history)


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
