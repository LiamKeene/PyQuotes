import unittest
import yql

from datetime import date, datetime, timedelta
from decimal import Decimal

from quote import *


class YahooQuoteTestCase(unittest.TestCase):
    """Test Case for the YahooQuote model.

    """
    def setUp(self):
        self.good_code = 'ABC'
        self.bad_code = 'A'

        self.columns = ['Name', 'Symbol', 'StockExchange', ]
        self.data = [u'ADEL BRTN FPO', u'ABC.AX', u'ASX', ]
        self.data_dict = dict(zip(self.columns, self.data))

    def test_quote_good_code(self):
        """YahooQuote should create a new quote object, fetch a quote and parse it."""
        quote = YahooQuote(self.good_code, self.columns)

        # Check we got a raw quote
        self.assertTrue(quote.raw_quote is not None)

        # Check the quote has been parsed
        for key, value in quote.quote.items():
            self.assertTrue(key in quote.quote)
            self.assertEqual(quote.quote[key], value)


class RawYahooQuoteTestCase(unittest.TestCase):
    """Test Case for `YahooQuote`.`get_raw_quote` function.

    The `get_raw_quote` function should query Yahoo's finance tables using YQL
    and return the latest quote for a particular stock (delayed by 20min).

    """
    def setUp(self):
        self.good_code = 'ABC'
        self.bad_code = 'A'

        self.columns = ['Name', 'Symbol', 'StockExchange', ]
        self.data = [u'ADEL BRTN FPO', u'ABC.AX', u'ASX', ]
        self.data_dict = dict(zip(self.columns, self.data))

    def test_quote_good_code(self):
        """get_raw_quote should return True given a valid code."""
        ret, quote = YahooQuote().get_raw_quote(self.good_code)
        self.assertTrue(ret)

    def test_quote_bad_code(self):
        """get_raw_quote should raise an Exception given an invalid code."""
        self.assertRaises(Exception, YahooQuote().get_raw_quote, self.bad_code)

    def test_quote_get_columns(self):
        """get_raw_quote should return the requested column only."""
        ret, quote = YahooQuote().get_raw_quote(self.good_code, self.columns)

        for key, value in self.data_dict.items():
            self.assertTrue(key in quote)
            self.assertEqual(quote[key], self.data_dict[key])


class RawYahooCSVQuoteTestCase(unittest.TestCase):
    """The `YahooCSVQuote`.`get_raw_quote` function should query Yahoo's finance CSV API and
    return the latest quote for a particular stock (delayed by 20min).

    """
    def setUp(self):
        self.good_code = 'ABC'
        self.bad_code = 'A'

        self.csv_columns = 'nsx'
        self.csv_data = '"ADEL BRTN FPO","ABC.AX","ASX"\r\n'

    def test_csv_quote_good_code(self):
        """get_raw_quote should return True given a valid code."""
        ret, quote = YahooCSVQuote().get_raw_quote(self.good_code)
        self.assertTrue(ret)

    def test_csv_quote_bad_code(self):
        """get_raw_quote should raise an Exception given an invalid code."""
        self.assertRaises(Exception, YahooCSVQuote().get_raw_quote, self.bad_code)

    def test_csv_quote_get_columns(self):
        """get_raw_quote should return the requested columns only."""
        ret, quote = YahooCSVQuote().get_raw_quote(self.good_code, self.csv_columns)

        self.assertTrue(ret)
        self.assertEqual(quote, self.csv_data)


class RawYahooQuoteHistoryTestCase(unittest.TestCase):
    """The `YahooQuoteHistory`.`get_raw_quote` function should query Yahoo's finance tables
    using YQL and return the historical quote data for a particular stock over
    a given date range.

    The date range must be a list containing the start and end dates.  The dates
    may be date objects (fully specified), strings or empty.  If the start date
    is empty a reasonable default is used.  If the end date is empty the latest
    date is used.

    """
    def setUp(self):
        self.good_code = 'ABC'

        self.test_dates = [date(2013, 4, 10), date(2013, 4, 12)]
        self.test_date_range = ['2013-04-12', '2013-04-11', '2013-04-10']

    def test_history_good_code(self):
        """get_raw_quote should return True given a valid code."""
        ret, quotes = YahooQuoteHistory().get_raw_quote(self.good_code, self.test_dates)

        self.assertTrue(ret)
        self.assertEqual(type(quotes), list)
        self.assertEqual(len(quotes), len(self.test_date_range))

        for i in range(len(quotes)):
            self.assertEqual(quotes[i]['Date'], self.test_date_range[i])


class RawYahooCSVQuoteHistoryTestCase(unittest.TestCase):
    """The `YahooCSVQuoteHistory`.`get_raw_quote` function should query Yahoo's finance CSV
    API and return the historical quote data for a particular stock over a given
    date range.

    The date range must be a list containing the start and end dates.  The dates
    may be date objects (fully specified), strings or empty.  If the start date
    is empty a reasonable default is used.  If the end date is empty the latest
    date is used.

    """
    def setUp(self):
        self.good_code = 'ABC'

        self.test_dates = [date(2013, 4, 10), date(2013, 4, 12)]
        self.test_date_range = ['2013-04-12', '2013-04-11', '2013-04-10']

    def test_csv_history_good_code(self):
        """get_raw_quote should return True given a valid code."""
        ret, quotes = YahooCSVQuoteHistory().get_raw_quote(self.good_code, self.test_dates)
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
    """Test Case for the `YahooCSVQuote`.`parse_symbols` function.

    The `parse_symbols` function should parse a string of Yahoo CSV tags
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
        """parse_symbols should return a correctly parsed list of symbols."""
        [self.assertEqual(YahooCSVQuote().parse_symbols(symbol_str), symbol_list)
            for symbol_str, symbol_list in self.parsed_symbols_dict.items()]


class GetYahooQuoteFieldsTestCase(unittest.TestCase):
    """Test Case for the `YahooQuote`.`get_quote_fields` function.

    The `get_quote_fields` function should return a dictionary of two-tuples
    that contain the output field names and data type given the quote field names.

    """
    def setUp(self):
        self.test_data = [
            [
                ('Symbol', 'LastTradePriceOnly', 'Volume'),
                {
                    'Symbol': ('Code', str),
                    'LastTradePriceOnly': ('Close', Decimal),
                    'Volume': ('Volume', Decimal),
                },
            ],
        ]
        self.test_get_all_fields = '*'

        self.test_unknown_fields = [
            ('RandomField'),
        ]

    def test_get_yahoo_quote_fields(self):
        """get_quote_fields should return dictionary of tuples of field names"""
        [self.assertEqual(YahooQuote().get_quote_fields(field_tuple), field_dict)
            for field_tuple, field_dict in self.test_data]

    def test_get_all_fields(self):
        """get_quote_fields should return dictionary of tuples of all field names."""
        field_dict = YahooQuote().get_quote_fields(self.test_get_all_fields)

        self.assertTrue(isinstance(field_dict, dict))
        self.assertTrue(len(field_dict.keys()) > 0)

    def test_unknown_fields(self):
        """get_quote_fields should raise Exception if the field is unknown."""
        [self.assertRaises(Exception, YahooQuote().get_quote_fields, field_tuple)
            for field_tuple in self.test_unknown_fields]


class GetYahooCSVQuoteFieldsTestCase(unittest.TestCase):
    """Test Case for the `YahooCSVQuote`.`get_quote_fields` function.

    The `get_quote_fields` function should return a tuple of two-tuples
    that contain the single CSV quote field names and data type given field symbols.

    The symbols are found at this url http://www.jarloo.com/yahoo_finance/ and
    are hard-coded here (a db model or fixtures may be useful in the future).

    """
    def setUp(self):
        self.test_data = [
            [
                ('n', 's', 'x', 'l1'),
                (
                    ('Name', str), ('Code', str), ('Exchange', str), ('Close', Decimal),
                ),
            ],
            [
                ('s', 'o', 'h', 'g', 'l1', 'v'),
                (
                    ('Code', str), ('Open', Decimal), ('High', Decimal),
                    ('Low', Decimal), ('Close', Decimal), ('Volume', Decimal),
                ),
            ]
        ]
        self.test_unknown_symbols = [
            ('f', ),
        ]

    def test_get_yahoo_csv_quote_fields(self):
        """get_quote_fields should return dictionary from list of symbols."""
        [self.assertEqual(YahooCSVQuote().get_quote_fields(symbol_list), field_dict)
            for symbol_list, field_dict in self.test_data]

    def test_unknown_symbols(self):
        """get_quote_fields should raise Exception if the symbol is inknown."""
        [self.assertRaises(Exception, YahooCSVQuote().get_quote_fields, symbol_list)
            for symbol_list in self.test_unknown_symbols]


class GetYahooQuoteHistoryFieldsTestCase(unittest.TestCase):
    """Test Case for the `YahooQuoteHistory`.`get_quote_fields` function.

    The `get_quote_fields` function should return a dictionary of
    two-tuples that contain the output field names and data type given the quote
    field names.

    """
    def setUp(self):
        self.test_data = [
            [
                ('Date', 'Open', 'High', 'Low', 'Close', 'Volume'),
                {
                    'Date': ('Date', parse_date), 'Open': ('Open', Decimal),
                    'High': ('High', Decimal), 'Low': ('Low', Decimal),
                    'Close': ('Close', Decimal), 'Volume': ('Volume', Decimal),
                },
            ],
        ]

        self.test_unknown_fields = [
            ('RandomField'),
        ]

    def test_get_yahoo_quote_history_fields(self):
        """get_quote_fields should return dictionary of tuples of field names"""
        [self.assertEqual(YahooQuoteHistory().get_quote_fields(field_tuple), field_dict)
            for field_tuple, field_dict in self.test_data]

    def test_unknown_fields(self):
        """get_quote_fields should raise Exception if the field is unknown."""
        [self.assertRaises(Exception, YahooQuoteHistory().get_quote_fields, field_tuple)
            for field_tuple in self.test_unknown_fields]


class ParseYahooQuoteTestCase(unittest.TestCase):
    """Test Case for the `YahooQuote`.`parse_quote` function.

    The `parse_quote` function should correctly parse the information from
    a Yahoo YQL stock quote.

    """
    def setUp(self):
        # The YQL quote will be dependant on the columns that are requested
        self.quote = {
            u'Symbol': u'ABC.AX', u'LastTradePriceOnly': u'3.330', u'Volume': u'1351200',
        }

        # List of columns used in the YQL quote
        self.quote_fields = {
            'Symbol': ('Code', str),
            'LastTradePriceOnly': ('Close', Decimal),
            'Volume': ('Volume', Decimal),
        }
        self.quote_partial_fields = {
            'Symbol': ('Code', str),
        }
        self.quote_no_fields = {}

        self.quote_parsed = {
            'Code': 'ABC.AX', 'Close': Decimal('3.330'), 'Volume': Decimal('1351200'),
        }
        self.quote_partial_parsed = {
            'Code': 'ABC.AX',
        }

    def test_parse_quote(self):
        """parse_quote should be able to parse quote."""
        quote = YahooQuote().parse_quote(self.quote, self.quote_fields)

        for key, value in self.quote_parsed.items():
            self.assertTrue(key in quote)
            self.assertEqual(quote[key], value)

    def test_parse_quote_partial(self):
        """parse_quote should be able to parse quote."""
        self.assertEqual(
            YahooQuote().parse_quote(self.quote, self.quote_partial_fields),
            self.quote_partial_parsed
        )

    def test_parse_quote_no_fields(self):
        """parse_quote should raise Exception with no specified fields."""
        self.assertRaises(
            Exception,
            YahooQuote().parse_quote,
            self.quote, self.quote_no_fields
        )


class ParseYahooCSVQuoteTestCase(unittest.TestCase):
    """The `YahooCSVQuote`.`parse_quote` function should correctly parse the information
    from a Yahoo CSV stock quote.

    """
    def setUp(self):
        # The CSV quote will be dependant on the columns that are requested
        self.csv_quote = '"ABC.AX",3.330,1351200\r\n'

        # Tuple of two-tuples containing the requested fields and data types
        self.csv_quote_fields = (('Code', str), ('Close', Decimal), ('Volume', Decimal), )
        self.csv_quote_partial_fields = (('Code', str), )
        self.csv_quote_no_fields = ()

        self.csv_quote_parsed = {
            'Code': 'ABC.AX', 'Close': Decimal('3.330'), 'Volume': Decimal('1351200'),
        }
        self.csv_quote_partial_parsed = {
            'Code': 'ABC.AX',
        }

    def test_parse_yahoo_csv_quote(self):
        """parse_quote should be able to parse CSV quote."""
        quote = YahooCSVQuote().parse_quote(self.csv_quote, self.csv_quote_fields)

        for key, value in self.csv_quote_parsed.items():
            self.assertTrue(key in quote)
            self.assertEqual(quote[key], value)

    def test_parse_yahoo_csv_quote_partial(self):
        """parse_quote should be able to parse quote."""
        self.assertEqual(
            YahooCSVQuote().parse_quote(self.csv_quote, self.csv_quote_partial_fields),
            self.csv_quote_partial_parsed
        )

    def test_parse_yahoo_csv_quote_no_fields(self):
        """parse_quote should raise Exception with no specified fields."""
        self.assertRaises(
            Exception,
            YahooCSVQuote().parse_quote,
            self.csv_quote, self.csv_quote_no_fields
        )


class ParseYahooQuoteHistoryTestCase(unittest.TestCase):
    """The `YahooQuoteHistory`.`parse_quote` function should correctly parse the
    information from a Yahoo YQL stock history.

    """
    def setUp(self):
        # The YQL historical quote has defined headers (at the moment anyway)
        self.quote_history = [
            {
                u'Volume': u'1351200', u'Adj_Close': u'3.33', u'High': u'3.38',
                u'Date': u'2013-04-12', u'Low': u'3.31', u'date': u'2013-04-12',
                u'Close': u'3.33', u'Open': u'3.36'
            },
            {
                u'Volume': u'1225300', u'Adj_Close': u'3.34', u'High': u'3.41',
                u'Date': u'2013-04-11', u'Low': u'3.33', u'date': u'2013-04-11',
                u'Close': u'3.34', u'Open': u'3.39'
            },
            {
                u'Volume': u'2076700', u'Adj_Close': u'3.40', u'High': u'3.41',
                u'Date': u'2013-04-10', u'Low': u'3.38', u'date': u'2013-04-10',
                u'Close': u'3.40', u'Open': u'3.39'
            }
        ]

        # The YQL historical fields are a dictionary of the field name as the key
        # and the desired output name and type as the value
        self.quote_history_fields = {
            'Date': ('Date', parse_date), 'Open': ('Open', Decimal),
            'High': ('High', Decimal), 'Low': ('Low', Decimal),
            'Close': ('Close', Decimal), 'Adj_Close': ('Adj Close', Decimal),
            'Volume': ('Volume', Decimal),
        }

        # Only parse parts of the quote
        self.quote_history_partial_fields = {
            'Date': ('Date', parse_date), 'Close': ('Close', Decimal),
            'Volume': ('Volume', Decimal),
        }
        # Don't ask to parse anything - raises Exception
        self.quote_history_no_fields = {}

        # The parsed YQL historical field
        self.quote_history_parsed = [
            {
                'Date': date(2013, 4, 12),
                'Open': Decimal('3.36'), 'High': Decimal('3.38'),
                'Low': Decimal('3.31'), 'Close': Decimal('3.33'),
                'Volume': Decimal('1351200'), 'Adj Close': Decimal('3.33'),
            },
            {
                'Date': date(2013, 4, 11),
                'Open': Decimal('3.39'), 'High': Decimal('3.41'),
                'Low': Decimal('3.33'), 'Close': Decimal('3.34'),
                'Volume': Decimal('1225300'), 'Adj Close': Decimal('3.34'),
            },
            {
                'Date': date(2013, 4, 10),
                'Open': Decimal('3.39'), 'High': Decimal('3.41'),
                'Low': Decimal('3.38'), 'Close': Decimal('3.40'),
                'Volume': Decimal('2076700'), 'Adj Close': Decimal('3.40'),
            },
        ]
        self.quote_history_partial_parsed = [
            {
                'Date': date(2013, 4, 12), 'Close': Decimal('3.33'),
                'Volume': Decimal('1351200'),
            },
            {
                'Date': date(2013, 4, 11), 'Close': Decimal('3.34'),
                'Volume': Decimal('1225300'),
            },
            {
                'Date': date(2013, 4, 10), 'Close': Decimal('3.40'),
                'Volume': Decimal('2076700'),
            },
        ]

    def test_parse_yahoo_quote_history(self):
        """parse_quote should be able to parse historical quotes."""
        self.assertEqual(
            YahooQuoteHistory().parse_quote(self.quote_history, self.quote_history_fields),
            self.quote_history_parsed
        )

    def test_parse_yahoo_quote_history_partial(self):
        """parse_quote should be able to parse historical quotes."""
        self.assertEqual(
            YahooQuoteHistory().parse_quote(self.quote_history, self.quote_history_partial_fields),
            self.quote_history_partial_parsed
        )

    def test_parse_yahoo_quote_history_no_fields(self):
        """parse_quote should raise Exception with no specified fields."""
        self.assertRaises(
            Exception,
            YahooQuoteHistory().parse_quote,
            self.quote_history, self.quote_history_no_fields
        )


class ParseYahooCSVQuoteHistoryTestCase(unittest.TestCase):
    """The `YahooCSVQuoteHistory`.`parse_quote` function should correctly parse the
    information from a Yahoo CSV stock history.

    """
    def setUp(self):
        # The CSV historical quote has defined headers (the first row of CSV data)
        self.csv_quote_history = 'Date,Open,High,Low,Close,Volume,Adj Close\n' \
            '2013-04-12,3.36,3.38,3.31,3.33,1351200,3.33\n' \
            '2013-04-11,3.39,3.41,3.33,3.34,1225300,3.34\n' \
            '2013-04-10,3.39,3.41,3.38,3.40,2076700,3.40\n'

        # The CSV quote fields
        self.csv_quote_history_fields = {
            'Date': ('Date', parse_date), 'Open': ('Open', Decimal),
            'High': ('High', Decimal), 'Low': ('Low', Decimal),
            'Close': ('Close', Decimal), 'Adj Close': ('Adj Close', Decimal),
            'Volume': ('Volume', Decimal),
        }
        # A partial set of fields to return
        self.csv_quote_history_partial_fields = {
            'Date': ('Date', parse_date), 'Close': ('Close', Decimal),
            'Volume': ('Volume', Decimal),
        }
        # Don't ask to parse anything - raises Exception
        self.csv_quote_history_no_fields = {}

        self.csv_quote_history_parsed = [
            {
                'Date': date(2013, 4, 12), 'Open': Decimal('3.36'),
                'High': Decimal('3.38'), 'Low': Decimal('3.31'),
                'Close': Decimal('3.33'), 'Adj Close': Decimal('3.33'),
                'Volume': Decimal('1351200'),
            },
            {
                'Date': date(2013, 4, 11), 'Open': Decimal('3.39'),
                'High': Decimal('3.41'), 'Low': Decimal('3.33'),
                'Close': Decimal('3.34'), 'Adj Close': Decimal('3.34'),
                'Volume': Decimal('1225300'),
            },
            {
                'Date': date(2013, 4, 10), 'Open': Decimal('3.39'),
                'High': Decimal('3.41'), 'Low': Decimal('3.38'),
                'Close': Decimal('3.40'), 'Adj Close': Decimal('3.40'),
                'Volume': Decimal('2076700'),
            },
        ]

        self.csv_quote_history_partial_parsed = [
            {
                'Date': date(2013, 4, 12), 'Close': Decimal('3.33'),
                'Volume': Decimal('1351200'),
            },
            {
                'Date': date(2013, 4, 11), 'Close': Decimal('3.34'),
                'Volume': Decimal('1225300'),
            },
            {
                'Date': date(2013, 4, 10), 'Close': Decimal('3.40'),
                'Volume': Decimal('2076700'),
            },
        ]


    def test_parse_yahoo_csv_quote_history(self):
        """parse_yahoo_csv_quote_history should be able to parse CSV historical quotes."""
        self.assertEqual(
            YahooCSVQuoteHistory().parse_quote(self.csv_quote_history, self.csv_quote_history_fields),
            self.csv_quote_history_parsed
        )

    def test_parse_yahoo_csv_quote_history_partial(self):
        """parse_yahoo_csv_quote_history should be able to parse CSV historical quotes."""
        self.assertEqual(
            YahooCSVQuoteHistory().parse_quote(self.csv_quote_history, self.csv_quote_history_partial_fields),
            self.csv_quote_history_partial_parsed
        )

    def test_parse_yahoo_csv_quote_history_no_fields(self):
        """parse_yahoo_csv_quote_history should raise Exception with no specified fields."""
        self.assertRaises(
            Exception,
            YahooCSVQuoteHistory().parse_quote,
            self.csv_quote_history, self.csv_quote_history_no_fields
        )


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


class ParseDateTestCase(unittest.TestCase):
    """Test Case for the `parse_date` function.

    The `parse_date` function will take a date string and return a date object.

    """
    def setUp(self):
        self.valid_date = date(2013, 4, 10)
        self.good_date = '2013-04-10'
        self.bad_date = '2013-13-10'
        self.bad_date_format = '10-04-2013'

    def test_parse_good_date(self):
        """parse_date should return date object given a proper date string."""
        self.assertEqual(parse_date(self.good_date), self.valid_date)

    def test_parse_bad_date(self):
        """parse_date should raise ValueError if given a proper but impossible date."""
        self.assertRaises(ValueError, parse_date, self.bad_date)

    def test_parse_bad_date_format(self):
        """Parse_date should return None if given an improper date string."""
        self.assertEqual(parse_date(self.bad_date_format), None)


if __name__ == '__main__':
    unittest.main()
