import csv
import pytz
import re
import urllib2
import yql

from datetime import datetime
from decimal import Decimal

from functions import parse_date, parse_time, validate_date_range

TIME_ZONE = 'Australia/Sydney'


class QuoteBase(object):
    """Abstract quote model that defines standard attributes and methods for
    different models.

    """
    def __init__(self, code, exchange, fields='*', defer=False):
        """Initialise the quote model given the stock code.

        Optionally given a list of field names that contain the required data
        in the quote (default is all fields '*'), and a boolean to determine
        whether to process the quote now or at a later time (default is False).

        """
        # Store the stock code and columns of data to fetch
        self.code = code
        self.exchange = exchange
        self.fields = fields

        # Default value of quote
        self.quote_fields = {}
        self.raw_quote = None
        self.quote = None

        # Process quote or defer it for later
        if not defer:
            self.process_quote()

    def get_column_from_field(self, field):
        """Returns the quote query column name from the field name."""
        for column_name, (field_name, field_type) in self._known_fields.items():
            if field == field_name:
                return column_name
        raise Exception('Field - %s is not known or unhandled' % (field, ))

    def get_field_from_column(self, column):
        """Returns the field name from the quote query column name."""
        for column_name, (field_name, field_type) in self._known_fields.items():
            if column == column_name:
                return field_name
        raise Exception('Column: %s is not known or unhandled' % (column, ))

    def get_quote_fields(self):
        """Returns dictionary of field names and types from given quote column names.

        Each field needs it's name and type defined otherwise an Exception is
        raised.

        """
        # If after all fields, just return the ones we have defined
        if self.fields == '*':
            return self._known_fields

        output = {}

        # Determine the query columns
        columns = [self.get_column_from_field(field) for field in self.fields]

        for column in columns:
            if not self._known_fields.has_key(column):
                raise NotImplementedError('Column - %s is not known or unhandled' % (column, ))

            # Find field in our known fields
            data_name, data_type = self._known_fields[column]

            # Add the field name and type to the output
            output[column] = (data_name, data_type)

        return output

    def get_raw_quote(self):
        """Method to fetch a raw unparsed quote from a provider."""
        raise NotImplementedError('This method must be defined by subclass.')

    def parse_quote(self):
        """Method to parse a raw quote from a provider into a standard format."""
        raise NotImplementedError('This method must be defined by subclass.')

    def process_quote(self):
        """Helper method to process a quote.

        Runs the get_quote_fields, get_raw_quote and parse_quote methods.

        """
        # Determine the field names and types
        self.quote_fields = self.get_quote_fields()

        # Fetch the raw quote
        self.raw_quote = self.get_raw_quote()

        # Parse the raw quote with the field names and types
        self.quote = self.parse_quote()


class LatestQuoteBase(QuoteBase):
    """Abstract quote model that expands on the QuoteBase and defines methods
    for quote models that retrieve the latest quote.

    """
    def _get_quote_data(self, field):
        """Returns the desired quote field."""
        if self.quote is None:
            raise Exception('Quote not parsed.')
        if not self.quote.has_key(field):
            raise Exception('%s not included in original quote.' % (field, ))
        return self.quote[field]

    @property
    def price(self):
        """Returns the closing (last) price."""
        return self._get_quote_data('Close')

    @property
    def price_date(self):
        """Returns the last price date."""
        return self._get_quote_data('Date')

    @property
    def price_time(self):
        """Returns the last price time."""
        return self._get_quote_data('Time')

    @property
    def volume(self):
        """Returns the volume traded."""
        return self._get_quote_data('Volume')

    def parse_quote(self):
        """Parse the raw data from a quote into a dictionary of useful data.

        """
        if self.quote_fields == {} or self.quote_fields is None:
            raise Exception('Quote cannot be parsed without output field tuple.')

        output = {}

        for key, value in self.raw_quote.items():
            # Ignore fields in the raw quote that were not requested
            if not self.quote_fields.has_key(key):
                continue
            field_name, field_type = self.quote_fields[key]
            output[field_name] = field_type(value)

        return output


class YahooQuoteDateTimeParseMixin():
    """Mixin Class that provides some methods for parsing date/time values.

    These methods only apply to some quote models, in particular the YahooQuote
    and YahooCSVQuote, whose date/time data are in unusual formats and cannot be
    parsed easily.

    This class is a mixin instead of another abstract class to try and simplify
    inheritance.

    """
    @staticmethod
    def parse_date(value):
        """Parses a string and return a datetime.date.

        """
        return datetime.strptime(value, '%m/%d/%Y').date()

    @staticmethod
    def parse_datetime(date_str, time_str):
        """Parses date/time strings and returns a date/time objects in the local timezone.

        Yahoo latest quote data returns dates in %m/%d/%Y format, and times in
        the US/Eastern timezone.

        """
        # Match the date and time strings to create a single datetime
        date_time_str = '%s %s' % (date_str, time_str)
        date_time_fmt = '%m/%d/%Y %I:%M%p'

        datetime_obj = datetime.strptime(date_time_str, date_time_fmt)

        # Create the timezone used in the quote
        yql_timezone = pytz.timezone('US/Eastern')
        yql_datetime = yql_timezone.localize(datetime_obj)

        # Convert the datetime into the desired timezone
        req_timezone = pytz.timezone(TIME_ZONE)
        req_datetime = req_timezone.normalize(yql_datetime.astimezone(req_timezone))

        return req_datetime

    @staticmethod
    def parse_time(value):
        """Parses a string and return a datetime.time.

        """
        return datetime.strptime(value, '%I:%M%p').time()


class YahooQuote(LatestQuoteBase, YahooQuoteDateTimeParseMixin):
    """Represents a quote that is obtained via the Yahoo Finance community table
    using the YQL library.

    """
    @property
    def _known_fields(self):
        """Returns the known fields of this quote model.

        Known fields is a dictionary of YQL query column names as the keys,
        and the output field name and field data type as the values.

        """
        return {
            'Name': ('Name', str),
            'LastTradeDate': ('Date', YahooQuote.parse_date),
            'LastTradeTime': ('Time', YahooQuote.parse_time),
            'LastTradePriceOnly': ('Close', Decimal),
            'StockExchange': ('Exchange', str),
            'Symbol': ('Code', str),
            'Volume': ('Volume', Decimal),
        }

    def get_raw_quote(self):
        """Get a quote from the Yahoo YQL finance tables and return the result.

        """
        # Error column name - save typing
        error_column = 'ErrorIndicationreturnedforsymbolchangedinvalid'

        # Create query object - must set the environment for community tables
        y = yql.Public()
        env = 'http://www.datatables.org/alltables.env'

        # Determine the query columns
        if self.fields == '*':
            columns = '*'
        else:
            columns = [self.get_column_from_field(field) for field in self.fields]

            # Ensure the error column in included
            if not error_column in columns:
                columns.append(error_column)

        # Join as a comma separated string
        columns = ','.join(columns)

        # Execute the query and get the response
        query = 'select %(columns)s from yahoo.finance.quotes where symbol = "%(code)s.%(exchange)s"' \
            % {'code': self.code, 'exchange': self.exchange, 'columns': columns, }
        response = y.execute(query, env=env)

        # Get the quote and the error field
        quote = response.results['quote']
        error = quote[error_column]

        # If no error return the quote or raise an exception
        if error is None:
            # Valid code and quote
            return quote

        raise Exception(error)


class YahooCSVQuote(LatestQuoteBase, YahooQuoteDateTimeParseMixin):
    """Represents a quote that is obtained via the Yahoo CSV API.

    """
    @property
    def _known_fields(self):
        """Returns the known fields of this quote model.

        Known fields is a dictionary of CSV query column symbols as the keys,
        and the output field name and field data type as the values.

        """
        return {
            'd1': ('Date', YahooCSVQuote.parse_date),
            'g': ('Low', Decimal),
            'h': ('High', Decimal),
            'l1': ('Close', Decimal),
            'n': ('Name', str),
            'o': ('Open', Decimal),
            's': ('Code', str),
            't1': ('Time', YahooCSVQuote.parse_time),
            'v': ('Volume', Decimal),
            'x': ('Exchange', str),
        }

    def get_raw_quote(self):
        """Get a quote from the Yahoo Finance CSV API and return the result.

        Given the code of the stock and an optional list of symbols that correspond
        to types of data to get in the quote.

        """
        # Determine the query columns
        if self.fields == '*':
            columns = self._known_fields.keys()
        else:
            columns = [self.get_column_from_field(field) for field in self.fields]

        # Join as a single string
        columns = ''.join(columns)

        quote_url = u'http://finance.yahoo.com/d/quotes.csv' \
            '?s=%(code)s.%(exchange)s&f=%(columns)s' \
            % {
                'code': self.code, 'exchange': self.exchange, 'columns': columns,
            }

        response = urllib2.urlopen(quote_url)

        quote = response.read()

        # Query columns need to be parsed into correct symbols
        columns = self.parse_symbols(columns)

        # Use the CSV module to parse the quote, using the query columns
        reader = csv.DictReader([quote], columns)

        # Read the raw data
        quote = [row for row in reader][0]

        return quote

    def parse_symbols(self, symbol_str):
        """Parse a string of Yahoo CSV symbols and return them as a tuple.

        This is required as the symbols are either single letters or a letter and
        an integer.

        """
        # Split symbols into a list
        symbol_list = list(symbol_str)

        # Symbol output
        output = []
        # Output counter
        count = 0

        # Find integers in the symbols and attach them to the previous character
        for i in range(len(symbol_list)):
            # If the character is a letter append to output
            if not symbol_list[i].isdigit():
                output.append(symbol_list[i])
                count = len(output)
            else:
                # Else append the digit to the previous letter
                output[count-1] = '%s%s' % (symbol_list[i-1], symbol_list[i])

        return tuple(output)


class HistoryQuoteBase(QuoteBase):
    """Abstract quote model that expands on the QuoteBase and defines methods
    for quote models that retrieve historical quotes.

    """
    def __init__(self, code, exchange, date_range, fields='*', defer=False):
        """Initialise the quote model given the stock code and date range.

        Optionally given a list of field names that contain the required data
        in the quote (default is all fields '*'), and a boolean to determine
        whether to process the quote now or at a later time (default is False).

        """
        # Store the date range
        self.date_range = date_range

        # Initialise the superclass
        super(HistoryQuoteBase, self).__init__(code, exchange, fields=fields, defer=defer)

    def parse_quote(self):
        """Parse the raw data from a historical quote into a dictionary of useful data.

        """
        if self.quote_fields == {} or self.quote_fields is None:
            raise Exception('Quote cannot be parsed without output field dictionary.')

        output = []

        # Populate the output list with data dictionaries
        for data in self.raw_quote:

            # Create dictionary for this data
            dic = {}

            for key, value in data.items():
                # Ignore fields in data that are not in requested field dict
                if not self.quote_fields.has_key(key):
                    continue
                # Lookup data name and data type
                data_name, data_type = self.quote_fields[key]

                # Apply the datatype
                dic[data_name] = data_type(value)

            # Add the data dictionary to the output
            output.append(dic)

        return output


class YahooQuoteHistory(HistoryQuoteBase):
    """Represents a set of historical quotes that are obtained via the Yahoo
    Finance community table using the YQL library.

    """
    @property
    def _known_fields(self):
        """Returns the known fields of this quote model.

        Known fields is a dictionary of YQL query column symbols as the keys,
        and the output field name and field data type as the values.

        """
        return {
            'Date': ('Date', parse_date),
            'Open': ('Open', Decimal),
            'High': ('High', Decimal),
            'Low': ('Low', Decimal),
            'Close': ('Close', Decimal),
            'Volume': ('Volume', Decimal),
            'Adj_Close': ('Adj Close', Decimal),
        }

    def get_raw_quote(self):
        """Get a list of quotes from the Yahoo YQL finance tables and return the result.

        Given the code of the stock and a list containing the start and end dates of
        the data.

        """
        # Validate dates first
        ret, date_range = validate_date_range(self.date_range)

        if not ret:
            # raise exception or just quit - validate_date_range will raise an exceptions
            raise Exception('Date range is no valid')

        start_date = date_range[0]
        end_date = date_range[1]

        # Create query object - must set the environment for community tables
        y = yql.Public()
        env = 'http://www.datatables.org/alltables.env'

        # Determine the query columns
        if self.fields == '*':
            columns = '*'
        else:
            columns = [self.get_column_from_field(field) for field in self.fields]

        # Join as a comma separated string
        columns = ','.join(columns)

        # Execute the query and get the response
        query = 'select %(columns)s from yahoo.finance.historicaldata ' \
            'where symbol = "%(code)s.%(exchange)s" ' \
            'and startDate = "%(start_date)s" and endDate = "%(end_date)s"' \
            % {
                'code': self.code, 'exchange': self.exchange, 'columns': columns,
                'start_date': start_date, 'end_date': end_date,
            }
        response = y.execute(query, env=env)

        # If the response results are null there was an error
        if response.results is None:
            raise Exception('Error with results')

        # Get the quote
        quote = response.results['quote']

        return quote


class YahooCSVQuoteHistory(HistoryQuoteBase):
    """Represents a set of historical quotes that are obtained via the Yahoo
    CSV API.

    """
    @property
    def _known_fields(self):
        """Returns the known fields of this quote model.

        Known fields is a dictionary of CSV headers as the keys,
        and the output field name and field data type as the values.

        """
        return {
            'Date': ('Date', parse_date),
            'Open': ('Open', Decimal),
            'High': ('High', Decimal),
            'Low': ('Low', Decimal),
            'Close': ('Close', Decimal),
            'Volume': ('Volume', Decimal),
            'Adj Close': ('Adj Close', Decimal),
        }

    def get_raw_quote(self):
        """Get a list of quotes from the Yahoo Finanace CSV API and return the result.

        Given the code of the stock and a list containing the start and end dates of
        the data.

        """
        # Validate dates first
        ret, date_range = validate_date_range(self.date_range)

        if not ret:
            # raise exception or just quit - validate_date_range will raise an exceptions
            raise Exception('Date range is no valid')

        start_date = date_range[0]
        end_date = date_range[1]

        quote_url = 'http://ichart.yahoo.com/table.csv' \
            '?s=%(code)s.%(exchange)s' \
            '&a=%(start_month)s&b=%(start_day)s&c=%(start_year)s' \
            '&d=%(end_month)s&e=%(end_day)s&f=%(end_year)s' \
            '&g=%(period)s' \
            '&ignore=.csv' \
            % {
                'code': self.code, 'exchange': self.exchange,
                'start_month': start_date.month - 1, 'start_day': start_date.day,
                'start_year': start_date.year, 'end_month': end_date.month - 1,
                'end_day': end_date.day, 'end_year': end_date.year,
                'period': 'd',
            }

        response = urllib2.urlopen(quote_url)

        quote = response.read()

        # Use the CSV module to parse the quote (we need to split on new lines)
        # Don't specify any columns (they will be taken as the first row of data)
        reader = csv.DictReader(quote.split('\n'))

        # Read the raw data
        quote = [row for row in reader]

        return quote
