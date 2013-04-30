import unittest
import yql

from datetime import date, datetime, time, timedelta
from decimal import Decimal

from functions import *
from quote import *


class YahooQuoteTestCase(unittest.TestCase):
    """Test Case for the YahooQuote model.

    """
    def setUp(self):
        self.test_code = 'ABC'
        self.test_exchange = 'AX'

        self.test_fields = ['Name', 'Code', 'Exchange', ]

        # Expected raw quote
        self.test_raw_quote = {
            'Name': u'ADEL BRTN FPO', 'Symbol': u'ABC.AX', 'StockExchange': u'ASX',
            'ErrorIndicationreturnedforsymbolchangedinvalid': None,
        }

        # Expected parsed quote
        self.test_parsed_quote = {
            'Name': u'ADEL BRTN FPO', 'Code': u'ABC.AX', 'Exchange': u'ASX',
        }

    def test_quote_good_code(self):
        """YahooQuote should create a new quote object, fetch a quote and parse it."""
        quote = YahooQuote(self.test_code, self.test_exchange)

        # Check we got a raw quote
        self.assertTrue(quote.raw_quote is not None)

        # Check we got a parsed quote
        self.assertTrue(quote.quote is not None)

    def test_quote_columns(self):
        """YahooQuote should create a new quote object, fetch and parse given columns."""
        quote = YahooQuote(self.test_code, self.test_exchange, self.test_fields)

        self.assertEqual(quote.raw_quote, self.test_raw_quote)

        self.assertEqual(quote.quote, self.test_parsed_quote)

    def test_quote_deferred(self):
        """YahooQuote should defer fetching and parsing of quote if required."""
        quote = YahooQuote(self.test_code, self.test_exchange, self.test_fields, defer=True)

        # Check quote is unprocessed
        self.assertEqual(quote.quote_fields, {})
        self.assertTrue(quote.raw_quote is None)
        self.assertTrue(quote.quote is None)


class YahooQuoteGetAttributesTestCase(unittest.TestCase):
    """Test Case for the attributes of a YahooQuote.

    """
    def setUp(self):
        self.test_code = 'ABC'
        self.test_exchange = 'AX'
        self.test_quote = YahooQuote(self.test_code, self.test_exchange, defer=True)

        self.test_price = Decimal('3.32')
        self.test_price_date = date(2013, 4, 10)
        self.test_price_time = time(12, 20, 0)

        # Explicitly set the fields and raw quote
        self.test_quote.quote_fields = {
            'Symbol': ('Code', str),
            'LastTradeDate': ('Date', self.test_quote.parse_date),
            'LastTradeTime': ('Time', parse_time),
            'LastTradePriceOnly': ('Close', Decimal),
        }

        self.test_quote.raw_quote = {
            'Symbol': u'ABC.AX',
            'LastTradePriceOnly': str(self.test_price),
            'LastTradeDate': self.test_price_date.strftime('%m/%d/%Y'),
            'LastTradeTime': self.test_price_time.strftime('%I:%M%p'),
        }

    def test_quote_price(self):
        """Test the quote.price is correct after a quote is parsed."""
        # Un-parsed quote (deferred quote?) should raise an Exception
        self.assertRaises(Exception, getattr, self.test_quote, 'price')

        # Parse the quote and update the object
        self.test_quote.quote = self.test_quote.parse_quote()

        # Parsed quote should have correct price
        self.assertEqual(self.test_quote.price, self.test_price)

    def test_quote_date(self):
        """Test the quote.price_date is correct after a quote is parsed."""
        # Un-parsed quote (deferred quote?) should raise an Exception
        self.assertRaises(Exception, getattr, self.test_quote, 'price_date')

        # Parse the quote and update the object
        self.test_quote.quote = self.test_quote.parse_quote()

        # Parsed quote should have correct date
        self.assertEqual(self.test_quote.price_date, self.test_price_date)

    def test_quote_time(self):
        """Test the quote.price_time is correct after a quote is parsed."""
        # Un-parsed quote (deferred quote?) should raise an Exception
        self.assertRaises(Exception, getattr, self.test_quote, 'price_time')

        # Parse the quote and update the object
        self.test_quote.quote = self.test_quote.parse_quote()

        # Parsed quote should have correct price
        self.assertEqual(self.test_quote.price_time, self.test_price_time)

    def test_quote_volume(self):
        """Test the quote.volume does not exist (was not in original quote."""
        # Parse the quote and update the object
        self.test_quote.quote = self.test_quote.parse_quote()

        self.assertRaises(Exception, getattr, self.test_quote, 'volume')


class YahooQuoteGetColumnFromFieldTestCase(unittest.TestCase):
    """Test Case for the `YahooQuote`.`get_column_from_field` function.

    The `get_column_from_field` function should return the column name if given
    the output field name.  Basically works the reverse of `get_field_from_column`.

    """
    def setUp(self):
        self.test_code = 'ABC'
        self.test_exchange = 'AX'
        self.test_fields = ['Name', 'Code', 'Close', 'Volume']
        self.test_columns = ['Name', 'Symbol', 'LastTradePriceOnly', 'Volume']
        self.test_quote = YahooQuote(self.test_code, self.test_exchange, self.test_fields, defer=True)

        self.test_unknown_column = 'RandomField'

    def test_get_field_from_column(self):
        """get_field_from_column should return field name given the quote column."""
        [
            self.assertEqual(
                self.test_quote.get_field_from_column(self.test_columns[i]),
                self.test_fields[i]
            )
            for i in range(len(self.test_fields))
        ]

    def test_get_field_from_column_not_found(self):
        """get_field_from_column should raise Exception if the column is unknown."""
        self.assertRaises(
            Exception,
            self.test_quote.get_field_from_column,
            self.test_unknown_column
        )


class YahooQuoteGetFieldFromColumnTestCase(unittest.TestCase):
    """Test Case for the `YahooQuote`.`get_field_from_column` function.

    The `get_field_from_column` function should return the field name if given
    the query column.  Basically works the reverse of `get_column_from_field`.

    """
    def setUp(self):
        self.test_code = 'ABC'
        self.test_exchange = 'AX'
        self.test_fields = ['Name', 'Code', 'Close', 'Volume']
        self.test_columns = ['Name', 'Symbol', 'LastTradePriceOnly', 'Volume']
        self.test_quote = YahooQuote(self.test_code, self.test_exchange, self.test_fields, defer=True)

        self.test_unknown_column = 'RandomColumn'

    def test_get_column_from_field(self):
        """get_column_from_field should return quote column name given the field output."""
        [
            self.assertEqual(
                self.test_quote.get_field_from_column(self.test_columns[i]),
                self.test_fields[i]
            )
            for i in range(len(self.test_fields))
        ]

    def test_get_column_from_field_not_found(self):
        """get_column_from_field should raise Exception if the field is unknown."""
        self.assertRaises(
            Exception,
            self.test_quote.get_field_from_column,
            self.test_unknown_column
        )


class YahooQuoteGetQuoteFieldsTestCase(unittest.TestCase):
    """Test Case for the `YahooQuote`.`get_quote_fields` function.

    The `get_quote_fields` function should return a dictionary of two-tuples
    that contain the output field names and data type given the quote field names.

    """
    def setUp(self):
        self.test_code = 'ABC'
        self.test_exchange = 'AX'
        self.test_fields = ['Code', 'Close', 'Volume']
        self.test_quote = YahooQuote(self.test_code, self.test_exchange, self.test_fields, defer=True)
        self.test_quote_fields = {
            'Symbol': ('Code', str),
            'LastTradePriceOnly': ('Close', Decimal),
            'Volume': ('Volume', Decimal),
        }

        self.test_get_all_fields = '*'
        self.test_quote_all_fields = YahooQuote(
            self.test_code, self.test_exchange, self.test_get_all_fields, defer=True
        )

        self.test_unknown_fields = ['RandomField', ]
        self.test_quote_unknown_fields = YahooQuote(
            self.test_code, self.test_exchange, self.test_unknown_fields, defer=True
        )

    def test_get_quote_fields(self):
        """get_quote_fields should return dictionary of tuples of field names."""
        self.assertEqual(self.test_quote.get_quote_fields(), self.test_quote_fields)

    def test_get_all_fields(self):
        """get_quote_fields should return dictionary of tuples of all field names."""
        field_dict = self.test_quote_all_fields.get_quote_fields()

        # Because the number of fields in the YQL quote is high, difficult to check
        # with predefined ones in a test case.
        self.assertTrue(isinstance(field_dict, dict))
        self.assertTrue(len(field_dict.keys()) > 0)

    def test_unknown_fields(self):
        """get_quote_fields should raise Exception if the field is unknown."""
        self.assertRaises(Exception, self.test_quote_unknown_fields.get_quote_fields)


class YahooQuoteGetRawQuoteTestCase(unittest.TestCase):
    """Test Case for `YahooQuote`.`get_raw_quote` function.

    The `get_raw_quote` function should query Yahoo's finance tables using YQL
    and return the latest quote for a particular stock (delayed by 20min).

    """
    def setUp(self):
        self.test_code = 'ABC'
        self.test_exchange = 'AX'

        self.fields = ['Name', 'Code', 'Exchange', ]

        # Expected raw quote
        self.test_raw_quote = {
            'Name': u'ADEL BRTN FPO', 'Symbol': u'ABC.AX', 'StockExchange': u'ASX',
            'ErrorIndicationreturnedforsymbolchangedinvalid': None,
        }

        self.test_quote = YahooQuote(self.test_code, self.test_exchange, defer=True)

        self.test_quote_fields = YahooQuote(self.test_code, self.test_exchange, self.fields, defer=True)

    def test_quote_good_code(self):
        """get_raw_quote should return True given a valid code."""
        raw_quote = self.test_quote.get_raw_quote()

        # Because the number of fields in the YQL quote is high, difficult to check
        # with predefined ones in a test case.
        self.assertTrue(raw_quote is not None)

    def test_quote_get_fields(self):
        """YahooQuote.get_raw_quote should return the requested fields only."""
        self.assertEqual(self.test_quote_fields.get_raw_quote(), self.test_raw_quote)


class YahooQuoteParseDateTestCase(unittest.TestCase):
    """Test Case for the YahooQuote.parse_date function.

    """
    def setUp(self):
        self.test_quote = YahooQuote('ABC', 'AX', defer=True)
        self.test_raw_date = '04/10/2013'
        self.test_parsed_date = date(2013, 4, 10)

    def test_parse_date(self):
        """parse_date should parse a Yahoo YQL date correctly."""
        self.assertEqual(
            self.test_quote.parse_date(self.test_raw_date),
            self.test_parsed_date
        )


class YahooQuoteParseDateTimeTestCase(unittest.TestCase):
    """Test Case for the YahooQuote.parse_date_time function.

    The Yahoo YQL quotes are given in the US/Eastern timezone, which must then
    be converted to the timezone specified in the project settings.

    Uses the django.utils.timezone module, which in turn uses pytz or a custom class.

    """
    def setUp(self):
        # Create a deferred quote
        self.test_quote = YahooQuote('ABC', 'AX', defer=True)

        # The raw date and time from a quote (not called so we can control them)
        self.test_raw_date = '04/10/2013'
        self.test_raw_time = '10:21pm'

        # Get the desired timezone from the quote module
        time_zone = TIME_ZONE

        # Create timezone used in the quote
        self.test_time_zone = pytz.timezone(time_zone)

        # The parsed date/time in the desired timezone
        self.test_parsed_datetime = datetime(
            2013, 4, 11, 12, 21, tzinfo=self.test_time_zone
        )

    def test_parse_date_time(self):
        """parse_date_time should parse a Yahoo YQL date and time correctly."""
        self.assertEqual(
            self.test_quote.parse_datetime(self.test_raw_date, self.test_raw_time),
            self.test_parsed_datetime
        )


class YahooQuoteParseQuoteTestCase(unittest.TestCase):
    """Test Case for the `YahooQuote`.`parse_quote` function.

    The `parse_quote` function should correctly parse the information from
    a Yahoo YQL stock quote.

    """
    def setUp(self):
        # Create three test quote objects
        self.test_code = 'ABC'
        self.test_exchange = 'AX'
        self.test_fields = ['Symbol', 'LastTradePriceOnly', 'Volume']
        self.test_quote = YahooQuote(
            self.test_code, self.test_exchange, self.test_fields, defer=True
        )
        self.test_quote_partial = YahooQuote(
            self.test_code, self.test_exchange, self.test_fields, defer=True
        )
        self.test_quote_no_fields = YahooQuote(
            self.test_code, self.test_exchange, self.test_fields, defer=True
        )

        # Explicitly set the quote fields and raw quote (is this a good idea?)
        self.test_quote.quote_fields = {
            'Symbol': ('Code', str),
            'LastTradePriceOnly': ('Close', Decimal),
            'Volume': ('Volume', Decimal),
        }
        self.test_quote.raw_quote = {
            u'Symbol': u'ABC.AX', u'LastTradePriceOnly': u'3.330', u'Volume': u'1351200',
        }

        # The parsed quote
        self.test_parsed_quote = {
            'Code': 'ABC.AX', 'Close': Decimal('3.330'), 'Volume': Decimal('1351200'),
        }

        # Explicitly set a partial set of the quote fields
        self.test_quote_partial.quote_fields = {
            'Symbol': ('Code', str),
        }
        self.test_quote_partial.raw_quote = self.test_quote.raw_quote

        # The partially parsed_quote
        self.test_parsed_quote_partial = {
            'Code': 'ABC.AX',
        }

        # Explicitly set no fields to parse
        self.test_quote_no_fields.fields = {}
        self.test_quote_no_fields.raw_quote = self.test_quote.raw_quote

    def test_parse_quote(self):
        """parse_quote should be able to parse quote."""
        self.assertEqual(self.test_quote.parse_quote(), self.test_parsed_quote)

    def test_parse_quote_partial(self):
        """parse_quote should be able to parse quote."""
        self.assertEqual(self.test_quote_partial.parse_quote(), self.test_parsed_quote_partial)

    def test_parse_quote_no_fields(self):
        """parse_quote should raise Exception with no specified fields."""
        self.assertRaises(Exception, self.test_quote_no_fields.parse_quote)


class YahooQuoteParseTimeTestCase(unittest.TestCase):
    """Test Case for the YahooQuote.parse_time function.

    """
    def setUp(self):
        self.test_quote = YahooQuote('ABC', 'AX', defer=True)
        self.test_raw_time = '10:21pm'
        self.test_parsed_time = time(22, 21)

    def test_parse_time(self):
        """parse_time should parse a Yahoo YQL time correctly."""
        self.assertEqual(
            self.test_quote.parse_time(self.test_raw_time),
            self.test_parsed_time
        )


class YahooCSVQuoteTestCase(unittest.TestCase):
    """Test Case for the YahooCSVQuote model.

    """
    def setUp(self):
        self.test_code = 'ABC'
        self.test_exchange = 'AX'

        self.test_fields = ['Name', 'Code', 'Exchange', ]

        # Expected raw quote
        self.test_raw_quote = {
            'n': 'ADEL BRTN FPO', 's': 'ABC.AX', 'x': 'ASX'
        }

        # Expected parsed quote
        self.test_parsed_quote = {
            'Name': u'ADEL BRTN FPO', 'Code': u'ABC.AX', 'Exchange': u'ASX',
        }

    def test_quote_good_code(self):
        """YahooCSVQuote should create a new quote object, fetch a quote and parse it."""
        quote = YahooCSVQuote(self.test_code, self.test_exchange)

        # Check we got a raw quote
        self.assertTrue(quote.raw_quote is not None)

        # Check we got a parsed quote
        self.assertTrue(quote.quote is not None)

    def test_quote_columns(self):
        """YahooCSVQuote should create a new quote object, fetch and parse given columns."""
        quote = YahooCSVQuote(self.test_code, self.test_exchange, self.test_fields)

        self.assertEqual(quote.raw_quote, self.test_raw_quote)

        self.assertEqual(quote.quote, self.test_parsed_quote)

    def test_quote_deferred(self):
        """YahooCSVQuote should defer fetching and parsing of quote if required."""
        quote = YahooCSVQuote(self.test_code, self.test_exchange, self.test_fields, defer=True)

        # Check quote is unprocessed
        self.assertEqual(quote.quote_fields, {})
        self.assertTrue(quote.raw_quote is None)
        self.assertTrue(quote.quote is None)


class YahooCSVQuoteGetAttributesTestCase(unittest.TestCase):
    """Test Case for the attributes of a YahooCSVQuote.

    """
    def setUp(self):
        self.test_code = 'ABC'
        self.test_exchange = 'AX'
        self.test_fields = ['Code', 'Close', 'Date', 'Time', ]
        self.test_quote = YahooCSVQuote(self.test_code, self.test_exchange, self.test_fields, defer=True)

        self.test_price = Decimal('3.32')
        self.test_price_date = date(2013, 4, 10)
        self.test_price_time = time(10, 21, 0)

        # Explicitly set the fields and raw quote
        self.test_quote.quote_fields = {
            's': ('Code', str),
            'l1': ('Close', Decimal),
            'd1': ('Date', self.test_quote.parse_date),
            't1': ('Time', self.test_quote.parse_time),
        }

        self.test_quote.raw_quote = {
            's':  'ABC.AX', 'l1': '3.320', 'd1': '4/10/2013', 't1': '10:21am'
        }

    def test_quote_price(self):
        """Test the quote.price is correct after a quote is parsed."""
        # Un-parsed quote (deferred quote?) should raise an Exception
        self.assertRaises(Exception, getattr, self.test_quote, 'price')

        # Parse the quote and update the object
        self.test_quote.quote = self.test_quote.parse_quote()

        # Parsed quote should have correct price
        self.assertEqual(self.test_quote.price, self.test_price)

    def test_quote_date(self):
        """Test the quote.price_date is correct after a quote is parsed."""
        # Un-parsed quote (deferred quote?) should raise an Exception
        self.assertRaises(Exception, getattr, self.test_quote, 'price_date')

        # Parse the quote and update the object
        self.test_quote.quote = self.test_quote.parse_quote()

        # Parsed quote should have correct date
        self.assertEqual(self.test_quote.price_date, self.test_price_date)

    def test_quote_time(self):
        """Test the quote.price_time is correct after a quote is parsed."""
        # Un-parsed quote (deferred quote?) should raise an Exception
        self.assertRaises(Exception, getattr, self.test_quote, 'price_time')

        # Parse the quote and update the object
        self.test_quote.quote = self.test_quote.parse_quote()

        # Parsed quote should have correct price
        self.assertEqual(self.test_quote.price_time, self.test_price_time)

    def test_quote_volume(self):
        """Test the quote.volume does not exist (was not in original quote."""
        # Parse the quote and update the object
        self.test_quote.quote = self.test_quote.parse_quote()

        self.assertRaises(Exception, getattr, self.test_quote, 'volume')


class YahooCSVQuoteGetColumnFromFieldTestCase(unittest.TestCase):
    """Test Case for the `YahooCSVQuote`.`get_column_from_field` function.

    The `get_column_from_field` function should return the column (symbol) if
    given the output field name.  Basically works the reverse of `get_field_from_column`.

    """
    def setUp(self):
        self.test_code = 'ABC'
        self.test_exchange = 'AX'
        self.test_fields = ['Name', 'Code', 'Close', 'Volume']
        self.test_symbols = ('n', 's', 'l1', 'v')
        self.test_quote = YahooCSVQuote(
            self.test_code, self.test_exchange, self.test_fields, defer=True
        )

        self.test_unknown_field = 'RandomField'

    def test_get_column_from_field(self):
        """get_column_from_field should return quote column/symbol given the field output."""
        [
            self.assertEqual(
                self.test_quote.get_column_from_field(self.test_fields[i]),
                self.test_symbols[i]
            )
            for i in range(len(self.test_symbols))
        ]

    def test_get_column_from_field_not_found(self):
        """get_column_from_field should raise Exception if the column/symbol is unknown."""
        self.assertRaises(
            Exception,
            self.test_quote.get_column_from_field,
            self.test_unknown_field
        )


class YahooCSVQuoteGetFieldFromColumnTestCase(unittest.TestCase):
    """Test Case for the `YahooCSVQuote`.`get_field_from_column` function.

    The `get_field_from_column` function should return the output field name if
    given the column name.  Basically works the reverse of `get_column_from_field`.

    """
    def setUp(self):
        self.test_code = 'ABC'
        self.test_exchange = 'AX'
        self.test_fields = ['Name', 'Code', 'Close', 'Volume']
        self.test_columns = ('n', 's', 'l1', 'v')
        self.test_quote = YahooCSVQuote(
            self.test_code, self.test_exchange, self.test_fields, defer=True
        )

        self.test_unknown_field = 'RandomField'

    def test_get_field_from_column(self):
        """get_field_from_column should return quote field given the column/symbol."""
        [
            self.assertEqual(
                self.test_quote.get_field_from_column(self.test_columns[i]),
                self.test_fields[i]
            )
            for i in range(len(self.test_fields))
        ]

    def test_get_field_from_column_not_found(self):
        """get_field_from_column should raise Exception if the field is unknown."""
        self.assertRaises(
            Exception,
            self.test_quote.get_field_from_column,
            self.test_unknown_field
        )


class YahooCSVQuoteGetQuoteFieldsTestCase(unittest.TestCase):
    """Test Case for the `YahooCSVQuote`.`get_quote_fields` function.

    The `get_quote_fields` function should return a tuple of two-tuples
    that contain the single CSV quote field names and data type given field symbols.

    The symbols are found at this url http://www.jarloo.com/yahoo_finance/ and
    are hard-coded here (a db model or fixtures may be useful in the future).

    """
    def setUp(self):
        self.test_code = 'ABC'
        self.test_exchange = 'AX'
        self.test_fields = ['Code', 'Close', 'Volume']
        self.test_quote = YahooCSVQuote(
            self.test_code, self.test_exchange, self.test_fields, defer=True
        )
        self.test_quote_fields = {
            's': ('Code', str),
            'l1': ('Close', Decimal),
            'v': ('Volume', Decimal),
        }

        self.test_get_all_fields = '*'
        self.test_quote_all_fields = YahooCSVQuote(
            self.test_code, self.test_exchange, self.test_get_all_fields, defer=True
        )

        self.test_unknown_fields = ['RandomField', ]
        self.test_quote_unknown_fields = YahooCSVQuote(
            self.test_code, self.test_exchange, self.test_unknown_fields, defer=True
        )

    def test_get_quote_fields(self):
        """get_quote_fields should return dictionary of tuples of field names."""
        self.assertEqual(self.test_quote.get_quote_fields(), self.test_quote_fields)

    def test_get_all_fields(self):
        """get_quote_fields should return dictionary of tuples of all field names."""
        field_dict = self.test_quote_all_fields.get_quote_fields()

        # Because the number of fields in the CSV quote is high, difficult to check
        # with predefined ones in a test case.
        self.assertTrue(isinstance(field_dict, dict))
        self.assertTrue(len(field_dict.keys()) > 0)

    def test_unknown_fields(self):
        """get_quote_fields should raise Exception if the field is unknown."""
        self.assertRaises(Exception, self.test_quote_unknown_fields.get_quote_fields)


class YahooCSVQuoteGetRawQuoteTestCase(unittest.TestCase):
    """The `YahooCSVQuote`.`get_raw_quote` function should query Yahoo's finance CSV API and
    return the latest quote for a particular stock (delayed by 20min).

    """
    def setUp(self):
        self.test_code = 'ABC'
        self.test_exchange = 'AX'

        self.fields = ['Name', 'Code', 'Exchange', ]

        # Expected raw quote
        self.test_raw_quote = {
            'n': 'ADEL BRTN FPO', 's': 'ABC.AX', 'x': 'ASX'
        }

        self.test_quote = YahooCSVQuote(self.test_code, self.test_exchange, defer=True)

        self.test_quote_fields = YahooCSVQuote(self.test_code, self.test_exchange, self.fields, defer=True)

    def test_quote_good_code(self):
        """YahooCSVQuote.get_raw_quote should return True given a valid code."""
        raw_quote = self.test_quote.get_raw_quote()

        # Because the number of fields in the CSVquote is high, difficult to check
        # with predefined ones in a test case.
        self.assertTrue(raw_quote is not None)

    def test_quote_get_fields(self):
        """YahooCSVQuote.get_raw_quote should return the requested fields only."""
        self.assertEqual(self.test_quote_fields.get_raw_quote(), self.test_raw_quote)


class YahooCSVQuoteParseDateTestCase(unittest.TestCase):
    """Test Case for the YahooCSVQuote.parse_date function.

    """
    def setUp(self):
        self.test_quote = YahooCSVQuote('ABC', 'AX', defer=True)
        self.test_raw_date = '04/10/2013'
        self.test_parsed_date = date(2013, 4, 10)

    def test_parse_date(self):
        """parse_date should parse a Yahoo CSV date correctly."""
        self.assertEqual(
            self.test_quote.parse_date(self.test_raw_date),
            self.test_parsed_date
        )


class YahooCSVQuoteParseDateTimeTestCase(unittest.TestCase):
    """Test Case for the YahooCSVQuote.parse_date_time function.

    The Yahoo CSV quotes are given in the US/Eastern timezone, which must then
    be converted to the timezone specified in the project settings.

    Uses the django.utils.timezone module, which in turn uses pytz or a custom class.

    """
    def setUp(self):
        # Create a deferred quote
        self.test_quote = YahooQuote('ABC', 'AX', defer=True)

        # The raw date and time from a quote (not called so we can control them)
        self.test_raw_date = '04/10/2013'
        self.test_raw_time = '10:21pm'

        # Get the desired timezone from the quote module
        time_zone = TIME_ZONE

        # Create timezone used in the quote
        self.test_time_zone = pytz.timezone(time_zone)

        # The parsed date/time in the desired timezone
        self.test_parsed_datetime = datetime(
            2013, 4, 11, 12, 21, tzinfo=self.test_time_zone
        )

    def test_parse_date_time(self):
        """parse_date_time should parse a Yahoo CSV date and time correctly."""
        self.assertEqual(
            self.test_quote.parse_datetime(self.test_raw_date, self.test_raw_time),
            self.test_parsed_datetime
        )


class YahooCSVQuoteParseQuoteTestCase(unittest.TestCase):
    """The `YahooCSVQuote`.`parse_quote` function should correctly parse the information
    from a Yahoo CSV stock quote.

    """
    def setUp(self):
        # Create three test quote objects
        self.test_code = 'ABC'
        self.test_exchange = 'AX'
        self.test_fields = ['Code', 'Close', 'Volume', ]
        self.test_quote_fields = {
            's': ('Code', str),
            'l1': ('Close', Decimal),
            'v': ('Volume', Decimal),
        }
        self.test_quote = YahooCSVQuote(
            self.test_code, self.test_exchange, self.test_fields, defer=True
        )
        self.test_quote_partial = YahooCSVQuote(
            self.test_code, self.test_exchange, self.test_fields, defer=True
        )
        self.test_quote_no_fields = YahooCSVQuote(
            self.test_code, self.test_exchange, self.test_fields, defer=True
        )
        # Explicitly set the quote fields and raw quote
        self.test_quote.quote_fields = self.test_quote_fields
        self.test_quote.raw_quote = {
            's': 'ABC.AX', 'l1': '3.330', 'v': '1351200'
        }

        # The parsed quote
        self.test_parsed_quote = {
            'Code': 'ABC.AX', 'Close': Decimal('3.330'), 'Volume': Decimal('1351200'),
        }

        # Explicitly set a partial set of the quote fields
        self.test_quote_partial.quote_fields = {'s': ('Code', str), }
        self.test_quote_partial.raw_quote = self.test_quote.raw_quote

        # The partially parsed quote
        self.test_parsed_quote_partial = {
            'Code': 'ABC.AX',
        }

        # Explicitly set no fields to parse
        self.test_quote_no_fields.fields = {}
        self.test_quote_no_fields.raw_quote = self.test_quote.raw_quote

    def test_parse_quote(self):
        """parse_quote should be able to parse quote."""
        self.assertEqual(self.test_quote.parse_quote(), self.test_parsed_quote)

    def test_parse_quote_partial(self):
        """parse_quote should be able to parse quote."""
        self.assertEqual(self.test_quote_partial.parse_quote(), self.test_parsed_quote_partial)

    def test_parse_quote_no_fields(self):
        """parse_quote should raise Exception with no specified fields."""
        self.assertRaises(Exception, self.test_quote_no_fields.parse_quote)


class YahooCSVQuoteParseSymbolsTestCase(unittest.TestCase):
    """Test Case for the `YahooCSVQuote`.`parse_symbols` function.

    The `parse_symbols` function should parse a string of Yahoo CSV tags
    into a tuple of those tags.  Not as simple as it sounds as some tags consist
    of a letter and number.

    """
    def setUp(self):
        self.test_code = 'ABC'
        self.test_exchange = 'AX'
        self.test_symbols_dict = {
            'nsx': ('n', 's', 'x'),
            'ohgl1v': ('o', 'h', 'g', 'l1', 'v', ),
            'nsl1hr5j1ym3m4n4xd1': (
                'n', 's', 'l1', 'h', 'r5', 'j1', 'y', 'm3', 'm4', 'n4', 'x', 'd1'
            ),
        }

        self.test_quote = YahooCSVQuote(self.test_code, self.test_exchange, defer=True)

    def test_parse_symbols(self):
        """parse_symbols should return a correctly parsed list of symbols."""
        [
            self.assertEqual(
                self.test_quote.parse_symbols(symbol_str),
                symbol_list
            )
            for symbol_str, symbol_list in self.test_symbols_dict.items()
        ]


class YahooCSVQuoteParseTimeTestCase(unittest.TestCase):
    """Test Case for the YahooCSVQuote.parse_time function.

    """
    def setUp(self):
        self.test_quote = YahooCSVQuote('ABC', 'AX', defer=True)
        self.test_raw_time = '10:21pm'
        self.test_parsed_time = time(22, 21)

    def test_parse_time(self):
        """parse_time should parse a Yahoo CSV time correctly."""
        self.assertEqual(
            self.test_quote.parse_time(self.test_raw_time),
            self.test_parsed_time
        )


class YahooQuoteHistoryTestCase(unittest.TestCase):
    """Test Case for the YahooQuoteHistory model.

    """
    def setUp(self):
        self.test_code = 'ABC'
        self.test_exchange = 'AX'

        self.test_dates = [date(2013, 4, 10), date(2013, 4, 12)]
        self.test_fields = ['Date', 'Close', 'Volume']
        self.test_raw_quote = [
            {'Date': '2013-04-12', 'Close': '3.33', 'Volume': '1351200', },
            {'Date': '2013-04-11', 'Close': '3.34', 'Volume': '1225300', },
            {'Date': '2013-04-10', 'Close': '3.40', 'Volume': '2076700', },
        ]

        self.test_parsed_quote = [
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

    def test_quote_good_code(self):
        """YahooQuoteHistory should create a new quote object, fetch a quote and parse it."""
        quote = YahooQuoteHistory(self.test_code, self.test_exchange, self.test_dates)

        # Check we got a raw quote
        self.assertTrue(quote.raw_quote is not None)

        # Check we got a parsed quote
        self.assertTrue(quote.quote is not None)

    def test_quote_columns(self):
        """YahooQuoteHistory should create a new quote object, fetch and parse given columns."""
        quote = YahooQuoteHistory(self.test_code, self.test_exchange, self.test_dates, self.test_fields)

        self.assertEqual(quote.raw_quote, self.test_raw_quote)

        self.assertEqual(quote.quote, self.test_parsed_quote)

    def test_quote_deferred(self):
        """YahooQuoteHistory should defer fetching and parsing of quote if required."""
        quote = YahooQuoteHistory(self.test_code, self.test_exchange, self.test_dates, self.test_fields, defer=True)

        # Check quote is unprocessed
        self.assertEqual(quote.quote_fields, {})
        self.assertTrue(quote.raw_quote is None)
        self.assertTrue(quote.quote is None)


class YahooQuoteHistoryGetColumnFromFieldTestCase(unittest.TestCase):
    """Test Case for the `YahooQuoteHistory`.`get_column_from_field` function.

    The `get_column_from_field` function should return the column name if given
    the output field name.  Basically works the reverse of `get_field_from_column`.

    """
    def setUp(self):
        self.test_code = 'ABC'
        self.test_exchange = 'AX'
        self.test_dates = [date(2013, 4, 10), date(2013, 4, 12)]
        self.test_fields = ['Date', 'Close', 'Adj Close']
        self.test_columns = ['Date', 'Close', 'Adj_Close']
        self.test_quote = YahooQuoteHistory(
            self.test_code, self.test_exchange, self.test_dates, self.test_fields, defer=True
        )

        self.test_unknown_field = 'RandomField'

    def test_get_column_from_field(self):
        """get_column_from_field should return quote column name given the field output."""
        [
            self.assertEqual(
                self.test_quote.get_column_from_field(self.test_fields[i]),
                self.test_columns[i]
            )
            for i in range(len(self.test_columns))
        ]

    def test_get_column_from_field_not_found(self):
        """get_column_from_field should raise Exception if the field is unknown."""
        self.assertRaises(
            Exception,
            self.test_quote.get_column_from_field,
            self.test_unknown_field
        )


class YahooQuoteHistoryGetFieldFromColumnTestCase(unittest.TestCase):
    """Test Case for the `YahooQuoteHistory`.`get_field_from_column` function.

    The `get_field_from_column` function should return the column name if given
    the output field name.  Basically works the reverse of `get_column_from_field`.

    """
    def setUp(self):
        self.test_code = 'ABC'
        self.test_exchange = 'AX'
        self.test_dates = [date(2013, 4, 10), date(2013, 4, 12)]
        self.test_fields = ['Date', 'Close', 'Adj Close']
        self.test_columns = ['Date', 'Close', 'Adj_Close']
        self.test_quote = YahooQuoteHistory(
            self.test_code, self.test_exchange, self.test_dates, self.test_fields, defer=True
        )

        self.test_unknown_column = 'RandomColumn'

    def test_get_field_from_column(self):
        """get_field_from_column should return quote column name given the field output."""
        [
            self.assertEqual(
                self.test_quote.get_field_from_column(self.test_columns[i]),
                self.test_fields[i]
            )
            for i in range(len(self.test_columns))
        ]

    def test_get_field_from_column_not_found(self):
        """get_field_from_column should raise Exception if the field is unknown."""
        self.assertRaises(
            Exception,
            self.test_quote.get_field_from_column,
            self.test_unknown_column
        )


class YahooQuoteHistoryGetQuoteFieldsTestCase(unittest.TestCase):
    """Test Case for the `YahooQuoteHistory`.`get_quote_fields` function.

    The `get_quote_fields` function should return a dictionary of
    two-tuples that contain the output field names and data type given the quote
    field names.

    """
    def setUp(self):
        self.test_code = 'ABC'
        self.test_exchange = 'AX'
        self.test_dates = [date(2013, 4, 10), date(2013, 4, 12)]
        self.test_fields = ['Date', 'High', 'Low', 'Close', 'Volume']
        self.test_quote = YahooQuoteHistory(
            self.test_code, self.test_exchange, self.test_dates, self.test_fields, defer=True
        )
        self.test_quote_fields = {
            'Date': ('Date', parse_date), 'High': ('High', Decimal),
            'Low': ('Low', Decimal), 'Close': ('Close', Decimal),
            'Volume': ('Volume', Decimal),
        }

        self.test_get_all_fields = '*'
        self.test_quote_all_fields = YahooQuoteHistory(
            self.test_code, self.test_exchange, self.test_dates, self.test_get_all_fields, defer=True
        )

        self.test_unknown_fields = ['RandomField', ]
        self.test_quote_unknown_fields = YahooQuoteHistory(
            self.test_code, self.test_exchange, self.test_dates, self.test_unknown_fields, defer=True
        )

    def test_get_quote_fields(self):
        """get_quote_fields should return dictionary of tuples of field names."""
        self.assertEqual(self.test_quote.get_quote_fields(), self.test_quote_fields)

    def test_get_all_fields(self):
        """get_quote_fields should return dictionary of tuples of all field names."""
        self.assertEqual(self.test_quote_all_fields.get_quote_fields(), self.test_quote._known_fields)

    def test_unknown_fields(self):
        """get_quote_fields should raise Exception if the field is unknown."""
        self.assertRaises(Exception, self.test_quote_unknown_fields.get_quote_fields)


class YahooQuoteHistoryGetRawQuoteTestCase(unittest.TestCase):
    """The `YahooQuoteHistory`.`get_raw_quote` function should query Yahoo's finance tables
    using YQL and return the historical quote data for a particular stock over
    a given date range.

    The date range must be a list containing the start and end dates.  The dates
    may be date objects (fully specified), strings or empty.  If the start date
    is empty a reasonable default is used.  If the end date is empty the latest
    date is used.

    """
    def setUp(self):
        self.test_code = 'ABC'
        self.test_exchange = 'AX'

        self.test_dates = [date(2013, 4, 10), date(2013, 4, 12)]
        self.test_fields = ['Date', 'Close', 'Volume', ]

        self.test_date_range = ['2013-04-12', '2013-04-11', '2013-04-10']

        self.test_raw_quote = [
            {
                'Date': '2013-04-12', 'Open': '3.36', 'High': '3.38',
                'Low': '3.31', 'Close': '3.33', 'Volume': '1351200',
                'Adj_Close': '3.33', 'date': '2013-04-12',
            },
            {
                'Date': '2013-04-11', 'Open': '3.39', 'High': '3.41',
                'Low': '3.33', 'Close': '3.34', 'Volume': '1225300',
                'Adj_Close': '3.34', 'date': '2013-04-11',
            },
            {
                'Date': '2013-04-10', 'Open': '3.39', 'High': '3.41',
                'Low': '3.38', 'Close': '3.40', 'Volume': '2076700',
                'Adj_Close': '3.40', 'date': '2013-04-10',
            }
        ]

        self.test_raw_quote_fields = [
            {'Date': '2013-04-12', 'Close': '3.33', 'Volume': '1351200', },
            {'Date': '2013-04-11', 'Close': '3.34', 'Volume': '1225300', },
            {'Date': '2013-04-10', 'Close': '3.40', 'Volume': '2076700', },
        ]

        self.test_quote = YahooQuoteHistory(
            self.test_code, self.test_exchange, self.test_dates, defer=True
        )

        self.test_quote_fields = YahooQuoteHistory(
            self.test_code, self.test_exchange, self.test_dates, self.test_fields, defer=True
        )

    def test_quote_good_code(self):
        """YahooQuoteHistory.get_raw_quote should return True given a valid code."""
        self.assertEqual(self.test_quote.get_raw_quote(), self.test_raw_quote)

    def test_quote_get_fields(self):
        """YahooQuoteHistory.get_raw_quote should return the requested fields only."""
        self.assertEqual(self.test_quote_fields.get_raw_quote(), self.test_raw_quote_fields)


class YahooQuoteHistoryParseQuoteTestCase(unittest.TestCase):
    """The `YahooQuoteHistory`.`parse_quote` function should correctly parse the
    information from a Yahoo YQL stock history.

    """
    def setUp(self):
        self.test_code = 'ABC'
        self.test_exchange = 'AX'
        self.test_dates = [date(2013, 4, 10), date(2013, 4, 12)]
        self.test_date_range = ['2013-04-12', '2013-04-11', '2013-04-10', ]
        self.test_fields = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume',]

        self.test_quote = YahooQuoteHistory(
            self.test_code, self.test_exchange, self.test_date_range, self.test_fields, defer=True
        )
        self.test_quote_partial = YahooQuoteHistory(
            self.test_code, self.test_exchange, self.test_date_range, self.test_fields, defer=True
        )
        self.test_quote_no_fields = YahooQuoteHistory(
            self.test_code, self.test_exchange, self.test_date_range, self.test_fields, defer=True
        )

        # Explicitly set the quote fields and raw quote (is this a good idea?)
        self.test_quote.quote_fields = {
            'Date': ('Date', parse_date), 'Open': ('Open', Decimal),
            'High': ('High', Decimal), 'Low': ('Low', Decimal),
            'Close': ('Close', Decimal), 'Volume': ('Volume', Decimal),
        }
        self.test_quote.raw_quote = [
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

        # The parsed quote
        self.test_parsed_quote = [
            {
                'Date': date(2013, 4, 12), 'Open': Decimal('3.36'),
                'High': Decimal('3.38'), 'Low': Decimal('3.31'),
                'Close': Decimal('3.33'), 'Volume': Decimal('1351200'),
            },
            {
                'Date': date(2013, 4, 11), 'Open': Decimal('3.39'),
                'High': Decimal('3.41'), 'Low': Decimal('3.33'),
                'Close': Decimal('3.34'), 'Volume': Decimal('1225300'),
            },
            {
                'Date': date(2013, 4, 10), 'Open': Decimal('3.39'),
                'High': Decimal('3.41'), 'Low': Decimal('3.38'),
                'Close': Decimal('3.40'), 'Volume': Decimal('2076700'),
            },
        ]

        # Only parse parts of the quote
        self.test_quote_partial.quote_fields = {
            'Date': ('Date', parse_date), 'Close': ('Close', Decimal),
            'Volume': ('Volume', Decimal),
        }
        self.test_quote_partial.raw_quote = self.test_quote.raw_quote

        # The partially parsed quote
        self.test_parsed_quote_partial = [
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
        # Don't ask to parse anything - raises Exception
        self.test_quote_no_fields.quote_fields = {}
        self.test_quote_no_fields.raw_quote = self.test_quote.raw_quote

    def test_parse_quote(self):
        """parse_quote should be able to parse quote."""
        self.assertEqual(self.test_quote.parse_quote(), self.test_parsed_quote)

    def test_parse_quote_partial(self):
        """parse_quote should be able to parse quote."""
        self.assertEqual(self.test_quote_partial.parse_quote(), self.test_parsed_quote_partial)

    def test_parse_quote_no_fields(self):
        """parse_quote should raise Exception with no specified fields."""
        self.assertRaises(Exception, self.test_quote_no_fields.parse_quote)


class YahooCSVQuoteHistoryTestCase(unittest.TestCase):
    """Test Case for the YahooCSVQuoteHistory model.

    """
    def setUp(self):
        self.test_code = 'ABC'
        self.test_exchange = 'AX'

        self.test_dates = [date(2013, 4, 10), date(2013, 4, 12)]
        self.test_fields = ['Date', 'Close', 'Volume']
        self.test_raw_quote = [
            {
                'Date': '2013-04-12', 'Open': '3.36', 'High': '3.38', 'Low': '3.31',
                'Close': '3.33', 'Volume': '1351200', 'Adj Close': '3.33'
            },
            {
                'Date': '2013-04-11', 'Open': '3.39', 'High': '3.41', 'Low': '3.33',
                'Close': '3.34', 'Volume': '1225300', 'Adj Close': '3.34'
            },
            {
                'Date': '2013-04-10', 'Open': '3.39', 'High': '3.41', 'Low': '3.38',
                'Close': '3.40', 'Volume': '2076700', 'Adj Close': '3.40'
            }
        ]

        self.test_parsed_quote = [
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

    def test_quote_good_code(self):
        """YahooCSVQuoteHistory should create a new quote object, fetch a quote and parse it."""
        quote = YahooCSVQuoteHistory(self.test_code, self.test_exchange, self.test_dates)

        # Check we got a raw quote
        self.assertTrue(quote.raw_quote is not None)

        # Check we got a parsed quote
        self.assertTrue(quote.quote is not None)

    def test_quote_columns(self):
        """YahooCSVQuoteHistory should create a new quote object, fetch and parse given columns."""
        quote = YahooCSVQuoteHistory(self.test_code, self.test_exchange, self.test_dates, self.test_fields)

        self.assertEqual(quote.raw_quote, self.test_raw_quote)

        self.assertEqual(quote.quote, self.test_parsed_quote)

    def test_quote_deferred(self):
        """YahooCSVQuoteHistory should defer fetching and parsing of quote if required."""
        quote = YahooCSVQuoteHistory(self.test_code, self.test_exchange, self.test_dates, self.test_fields, defer=True)

        # Check quote is unprocessed
        self.assertEqual(quote.quote_fields, {})
        self.assertTrue(quote.raw_quote is None)
        self.assertTrue(quote.quote is None)


class YahooCSVQuoteHistoryGetColumnFromFieldTestCase(unittest.TestCase):
    """Test Case for the `YahooCSVQuoteHistory`.`get_column_from_field` function.

    The `get_column_from_field` function should return the column name if given
    the output field name.  Basically works the reverse of `get_quote_fields`.

    """
    def setUp(self):
        self.test_code = 'ABC'
        self.test_exchange = 'AX'
        self.test_dates = [date(2013, 4, 10), date(2013, 4, 12)]
        self.test_columns = ['Date', 'Close', 'Adj Close']
        self.test_fields = ['Date', 'Close', 'Adj Close']
        self.test_quote = YahooCSVQuoteHistory(
            self.test_code, self.test_exchange, self.test_dates, self.test_fields, defer=True
        )

        self.test_unknown_field = 'RandomField'

    def test_get_column_from_field(self):
        """get_column_from_field should return quote column name given the field output."""
        [
            self.assertEqual(
                self.test_quote.get_column_from_field(self.test_fields[i]),
                self.test_columns[i]
            )
            for i in range(len(self.test_columns))
        ]

    def test_get_column_from_field_not_found(self):
        """get_column_from_field should raise Exception if the field is unknown."""
        self.assertRaises(
            Exception,
            self.test_quote.get_column_from_field,
            self.test_unknown_field
        )


class YahooCSVQuoteHistoryGetFieldFromColumnTestCase(unittest.TestCase):
    """Test Case for the `YahooQuoteHistory`.`get_field_from_column` function.

    The `get_field_from_column` function should return the column name if given
    the output field name.  Basically works the reverse of `get_column_from_field`.

    """
    def setUp(self):
        self.test_code = 'ABC'
        self.test_exchange = 'AX'
        self.test_dates = [date(2013, 4, 10), date(2013, 4, 12)]
        self.test_columns = ['Date', 'Close', 'Adj_Close']
        self.test_fields = ['Date', 'Close', 'Adj Close']
        self.test_quote = YahooQuoteHistory(
            self.test_code, self.test_exchange, self.test_dates, self.test_fields, defer=True
        )

        self.test_unknown_column = 'RandomColumn'

    def test_get_field_from_column(self):
        """get_field_from_column should return quote column name given the field output."""
        [
            self.assertEqual(
                self.test_quote.get_field_from_column(self.test_columns[i]),
                self.test_fields[i]
            )
            for i in range(len(self.test_columns))
        ]

    def test_get_field_from_column_not_found(self):
        """get_get_field_from_column should raise Exception if the field is unknown."""
        self.assertRaises(
            Exception,
            self.test_quote.get_field_from_column,
            self.test_unknown_column
        )


class YahooCSVQuoteHistoryGetQuoteFieldsTestCase(unittest.TestCase):
    """Test Case for the `get_quote_fields` function.

    The `get_quote_fields` function should return a dictionary of
    two-tuples that contain the output field names and data type given the quote
    field names.

    """
    def setUp(self):
        self.test_code = 'ABC'
        self.test_exchange = 'AX'
        self.test_dates = [date(2013, 4, 10), date(2013, 4, 12)]
        self.test_fields = ['Date', 'High', 'Low', 'Close', 'Volume']
        self.test_quote = YahooCSVQuoteHistory(
            self.test_code, self.test_exchange, self.test_dates, self.test_fields, defer=True
        )
        self.test_quote_fields = {
            'Date': ('Date', parse_date), 'High': ('High', Decimal),
            'Low': ('Low', Decimal), 'Close': ('Close', Decimal),
            'Volume': ('Volume', Decimal),
        }

        self.test_get_all_fields = '*'
        self.test_quote_all_fields = YahooCSVQuoteHistory(
            self.test_code, self.test_exchange, self.test_dates, self.test_get_all_fields, defer=True
        )

        self.test_unknown_fields = ['RandomField', ]
        self.test_quote_unknown_fields = YahooCSVQuoteHistory(
            self.test_code, self.test_exchange, self.test_dates, self.test_unknown_fields, defer=True
        )

    def test_get_quote_fields(self):
        """get_quote_fields should return dictionary of tuples of field names."""
        self.assertEqual(self.test_quote.get_quote_fields(), self.test_quote_fields)

    def test_get_all_fields(self):
        """get_quote_fields should return dictionary of tuples of all field names."""
        self.assertEqual(self.test_quote_all_fields.get_quote_fields(), self.test_quote._known_fields)

    def test_unknown_fields(self):
        """get_quote_fields should raise Exception if the field is unknown."""
        self.assertRaises(Exception, self.test_quote_unknown_fields.get_quote_fields)


class YahooCSVQuoteHistoryGetRawQuoteTestCase(unittest.TestCase):
    """The `YahooCSVQuoteHistory`.`get_raw_quote` function should query Yahoo's finance CSV
    API and return the historical quote data for a particular stock over a given
    date range.

    The date range must be a list containing the start and end dates.  The dates
    may be date objects (fully specified), strings or empty.  If the start date
    is empty a reasonable default is used.  If the end date is empty the latest
    date is used.

    """
    def setUp(self):
        self.test_code = 'ABC'
        self.test_exchange = 'AX'

        self.test_dates = [date(2013, 4, 10), date(2013, 4, 12)]

        self.test_date_range = ['2013-04-12', '2013-04-11', '2013-04-10']

        self.test_raw_quote = [
            {
                'Date': '2013-04-12', 'Open': '3.36', 'High': '3.38', 'Low': '3.31',
                'Close': '3.33', 'Volume': '1351200', 'Adj Close': '3.33'
            },
            {
                'Date': '2013-04-11', 'Open': '3.39', 'High': '3.41', 'Low': '3.33',
                'Close': '3.34', 'Volume': '1225300', 'Adj Close': '3.34'
            },
            {
                'Date': '2013-04-10', 'Open': '3.39', 'High': '3.41', 'Low': '3.38',
                'Close': '3.40', 'Volume': '2076700', 'Adj Close': '3.40'
            }
        ]

        self.test_quote = YahooCSVQuoteHistory(
            self.test_code, self.test_exchange, self.test_dates, defer=True
        )

    def test_quote_good_code(self):
        """YahooCSVQuoteHistory.get_raw_quote should return True given a valid code."""
        self.assertEqual(self.test_quote.get_raw_quote(), self.test_raw_quote)


class YahooCSVQuoteHistoryParseQuoteTestCase(unittest.TestCase):
    """The `YahooCSVQuoteHistory`.`parse_quote` function should correctly parse the
    information from a Yahoo CSV stock history.

    """
    def setUp(self):
        # The CSV historical quote has defined headers (the first row of CSV data)
        self.test_code = 'ABC'
        self.test_exchange = 'AX'
        self.test_dates = [date(2013, 4, 10), date(2013, 4, 12)]
        self.test_date_range = ['2013-04-12', '2013-04-11', '2013-04-10', ]
        self.test_fields = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume',]

        self.test_quote = YahooCSVQuoteHistory(
            self.test_code, self.test_exchange, self.test_date_range, self.test_fields, defer=True
        )
        self.test_quote_partial = YahooCSVQuoteHistory(
            self.test_code, self.test_exchange, self.test_date_range, self.test_fields, defer=True
        )
        self.test_quote_no_fields = YahooCSVQuoteHistory(
            self.test_code, self.test_exchange, self.test_date_range, self.test_fields, defer=True
        )

        # Explicitly set the quote fields and raw quote (is this a good idea?)
        self.test_quote.quote_fields = {
            'Date': ('Date', parse_date), 'Open': ('Open', Decimal),
            'High': ('High', Decimal), 'Low': ('Low', Decimal),
            'Close': ('Close', Decimal), 'Volume': ('Volume', Decimal),
        }
        self.test_quote.raw_quote = [
            {
                'Date': '2013-04-12', 'Open': '3.36', 'High': '3.38', 'Low': '3.31',
                'Close': '3.33', 'Volume': '1351200', 'Adj Close': '3.33'
            },
            {
                'Date': '2013-04-11', 'Open': '3.39', 'High': '3.41', 'Low': '3.33',
                'Close': '3.34', 'Volume': '1225300', 'Adj Close': '3.34'
            },
            {
                'Date': '2013-04-10', 'Open': '3.39', 'High': '3.41', 'Low': '3.38',
                'Close': '3.40', 'Volume': '2076700', 'Adj Close': '3.40'
            }
        ]

        # The parsed quote
        self.test_parsed_quote = [
            {
                'Date': date(2013, 4, 12), 'Open': Decimal('3.36'),
                'High': Decimal('3.38'), 'Low': Decimal('3.31'),
                'Close': Decimal('3.33'), 'Volume': Decimal('1351200'),
            },
            {
                'Date': date(2013, 4, 11), 'Open': Decimal('3.39'),
                'High': Decimal('3.41'), 'Low': Decimal('3.33'),
                'Close': Decimal('3.34'), 'Volume': Decimal('1225300'),
            },
            {
                'Date': date(2013, 4, 10), 'Open': Decimal('3.39'),
                'High': Decimal('3.41'), 'Low': Decimal('3.38'),
                'Close': Decimal('3.40'), 'Volume': Decimal('2076700'),
            },
        ]

        # Only parse parts of the quote
        self.test_quote_partial.quote_fields = {
            'Date': ('Date', parse_date), 'Close': ('Close', Decimal),
            'Volume': ('Volume', Decimal),
        }
        self.test_quote_partial.raw_quote = self.test_quote.raw_quote

        # The partially parsed quote
        self.test_parsed_quote_partial = [
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

        # Don't ask to parse anything - raises Exception
        self.test_quote_no_fields.quote_fields = {}
        self.test_quote_no_fields.raw_quote = self.test_quote.raw_quote

    def test_parse_quote(self):
        """parse_quote should be able to parse quote."""
        self.assertEqual(self.test_quote.parse_quote(), self.test_parsed_quote)

    def test_parse_quote_partial(self):
        """parse_quote should be able to parse quote."""
        self.assertEqual(self.test_quote_partial.parse_quote(), self.test_parsed_quote_partial)

    def test_parse_quote_no_fields(self):
        """parse_quote should raise Exception with no specified fields."""
        self.assertRaises(Exception, self.test_quote_no_fields.parse_quote)


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
