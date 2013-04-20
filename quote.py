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
    def __init__(self):
        """Initialise the quote model with any required parameters."""
        raise NotImplementedError('This method must be defined by subclass.')

    def get_quote_fields(self):
        """Method to get the field names and data types for this quote."""
        raise NotImplementedError('This method must be defined by subclass.')

    def get_raw_quote(self):
        """Method to fetch a raw unparsed quote from a provider."""
        raise NotImplementedError('This method must be defined by subclass.')

    def parse_quote(self):
        """Method to parse a raw quote from a provider into a standard format."""
        raise NotImplementedError('This method must be defined by subclass.')

    def process_quote(self):
        """Method to fetch and parse a raw quote."""
        raise NotImplementedError('This method must be defined by subclass.')


class LatestQuoteBase(QuoteBase):
    """Abstract quote model that expands on the QuoteBase and defines methods
    for quote models that retrieve the latest quote.

    """
    def __init__(self, code, fields='*', defer=False):
        """Initialise the quote model given the stock code.

        Optionally given a list of field names that contain the required data
        in the quote (default is all fields '*'), and a boolean to determine
        whether to process the quote now or at a later time (default is False).

        """
        # Store the stock code and columns of data to fetch
        self.code = code
        self.fields = fields

        # Default value of quote
        self.quote_fields = {}
        self.raw_quote = None
        self.quote = None

        # Process quote or defer it for later
        if not defer:
            self.process_quote()

    @property
    def price(self):
        if self.quote is None:
            raise Exception('Quote not parsed.')
        return self.quote['Close']

    @property
    def price_date(self):
        if self.quote is None:
            raise Exception('Quote not parsed.')
        return self.quote['Date']

    @property
    def price_time(self):
        if self.quote is None:
            raise Exception('Quote not parsed.')
        return self.quote['Time']

    @property
    def volume(self):
        if self.quote is None:
            raise Exception('Quote not parsed.')
        return self.quote['Volume']


class YahooQuote(QuoteBase):
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

    def get_column_from_field(self, field):
        """Returns the YQL query column name from the field name."""
        for column_name, (field_name, field_type) in self._known_fields.items():
            if field == field_name:
                return column_name
        raise Exception('Field - %s is not known or unhandled' % (field, ))

    def get_field_from_column(self, column):
        """Returns the field name from the YQL query column name."""
        for column_name, (field_name, field_type) in self._known_fields.items():
            if column == column_name:
                return field_name
        raise Exception('Column: %s is not known or unhandled' % (column, ))

    def get_quote_fields(self):
        """Returns dictionary of field names and types from given YQL column names.

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
        """Get a quote from the Yahoo YQL finance tables and return the result.

        """
        # Only interested in Australian equities at the moment
        exchange = 'AX'

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
            % {'code': self.code, 'exchange': exchange, 'columns': columns, }
        response = y.execute(query, env=env)

        # Get the quote and the error field
        quote = response.results['quote']
        error = quote[error_column]

        # If no error return the quote or raise an exception
        if error is None:
            # Valid code and quote
            return quote

        raise Exception(error)

    @staticmethod
    def parse_date(value):
        """Parses a string and return a datetime.date.

        This is a staticmethod as it only applies to the format of YQL date strings.

        """
        return datetime.strptime(value, '%m/%d/%Y').date()

    @staticmethod
    def parse_datetime(date_str, time_str):
        """Parses date/time strings and returns a date/time objects in the local timezone.

        Yahoo YQL data returns dates in %m/%d/%Y format, and times in the
        US/Eastern timezone.

        This is a staticmethod as it only applies to the format of date and time
        strings that appear in a Yahoo YQL Quote.

        """
        # Match the date and time strings to create a single datetime
        date_time_str = '%s %s' % (date_str, time_str)
        date_time_fmt = '%m/%d/%Y %I:%M%p'

        datetime_obj = datetime.strptime(date_time_str, date_time_fmt)

        date_obj = datetime_obj.date()

        # Create the timezone used in the quote
        yql_timezone = pytz.timezone('US/Eastern')
        yql_datetime = yql_timezone.localize(datetime_obj, is_dst=True)

        # Convert the datetime into the desired timezone
        req_timezone = pytz.timezone(TIME_ZONE)
        req_datetime = req_timezone.normalize(yql_datetime.astimezone(req_timezone))

        return req_datetime

    @staticmethod
    def parse_time(value):
        """Parses a string and return a datetime.time.

        This is a staticmethod as it only applies to the format of YQL time strings.

        """
        return datetime.strptime(value, '%I:%M%p').time()

    def parse_quote(self):
        """Parse the raw data from a Yahoo finance YQL quote into a dictionary of
        useful data.

        Given a dictionary containing the fields to include in the result.

        """
        if self.quote_fields == {} or self.quote_fields is None:
            raise Exception('Quote cannot be parsed without output field dictionary.')

        output = {}

        for key, value in self.raw_quote.items():
            # Ignore fields in data that are not in requested field dict
            if not self.quote_fields.has_key(key):
                continue
            field_name, field_type = self.quote_fields[key]
            output[field_name] = field_type(value)

        return output

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


class YahooCSVQuote(QuoteBase):
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

    def get_column_from_field(self, field):
        """Returns the CSV query column name from the field name."""
        for column_name, (field_name, field_type) in self._known_fields.items():
            if field == field_name:
                return column_name
        raise Exception('Field - %s is not known or unhandled' % (field, ))

    def get_field_from_column(self, column):
        """Returns the field name from the CSV query column name."""
        for column_name, (field_name, field_type) in self._known_fields.items():
            if column == column_name:
                return field_name
        raise Exception('Column: %s is not known or unhandled' % (column, ))

    def get_quote_fields(self):
        """Returns field names and types from given Yahoo CSV symbols.

        Each symbol needs it's name and type defined otherwise an Exception is
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
        """Get a quote from the Yahoo Finance CSV API and return the result.

        Given the code of the stock and an optional list of symbols that correspond
        to types of data to get in the quote.

        """
        if not len(self.code) == 3:
            raise Exception('Stock code appears incorrect')

        # Only interested in Australian equities at the moment
        exchange = 'AX'

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
                'code': self.code, 'exchange': exchange, 'columns': columns,
            }

        response = urllib2.urlopen(quote_url)

        quote = response.read()

        return quote

    @staticmethod
    def parse_date(value):
        """Parses a string and return a datetime.date.

        This is a staticmethod as it only applies to the format of YQL date strings.

        """
        return datetime.strptime(value, '%m/%d/%Y').date()

    @staticmethod
    def parse_datetime(date_str, time_str):
        """Parses date/time strings and returns a date/time objects in the local timezone.

        Yahoo YQL data returns dates in %m/%d/%Y format, and times in the
        US/Eastern timezone.

        This is a staticmethod as it only applies to the format of date and time
        strings that appear in a Yahoo YQL Quote.

        """
        # Match the date and time strings to create a single datetime
        date_time_str = '%s %s' % (date_str, time_str)
        date_time_fmt = '%m/%d/%Y %I:%M%p'

        datetime_obj = datetime.strptime(date_time_str, date_time_fmt)

        date_obj = datetime_obj.date()

        # Create the timezone used in the quote
        yql_timezone = pytz.timezone('US/Eastern')
        yql_datetime = yql_timezone.localize(datetime_obj, is_dst=True)

        # Convert the datetime into the desired timezone
        req_timezone = pytz.timezone(TIME_ZONE)
        req_datetime = req_timezone.normalize(yql_datetime.astimezone(req_timezone))

        return req_datetime

    @staticmethod
    def parse_time(value):
        """Parses a string and return a datetime.time.

        This is a staticmethod as it only applies to the format of YQL time strings.

        """
        return datetime.strptime(value, '%I:%M%p').time()

    def parse_quote(self):
        """Parse the raw data from a Yahoo finance CSV quote into a dictionary of
        useful data.

        Given a dictionary containing the fields to include in the result.

        """
        if self.quote_fields == {} or self.quote_fields is None:
            raise Exception('Quote cannot be parsed without output field tuple.')

        # Get the list of fieldname
        if self.fields == '*':
            columns = self._known_fields.keys()
        else:
            columns = [self.get_column_from_field(field) for field in self.fields]

        # Use the CSV module to parse the quote
        reader = csv.DictReader([self.raw_quote], columns)

        # Read the raw data
        raw_data = [row for row in reader][0]

        output = {}

        for key, value in raw_data.items():
            # Ignore fields in data that are not in requested field dict
            if not self.quote_fields.has_key(key):
                continue
            field_name, field_type = self.quote_fields[key]
            output[field_name] = field_type(value)

        return output

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


class YahooQuoteHistory(QuoteBase):
    """Represents a set of historical quotes that are obtained via the Yahoo
    Finance community table using the YQL library.

    """
    def __init__(self, code, date_range, columns='*', defer=False):
        """Initialise a YahooQuoteHistory given the stock code and date range.

        Optionally give a list of columns to include in the YQL query (default is
        all columns `*`).

        """
        # Store the stock code and columns of data to fetch
        self.code = code
        self.date_range = date_range
        self.columns = columns

        # Default value of quote
        self.fields = {}
        self.raw_quote = None
        self.quote = None

        # Process quote or defer it for later
        if not defer:
            self.process_quote()

    @property
    def _known_fields(self):
        return {
            'Date': ('Date', parse_date),
            'Open': ('Open', Decimal),
            'High': ('High', Decimal),
            'Low': ('Low', Decimal),
            'Close': ('Close', Decimal),
            'Volume': ('Volume', Decimal),
            'Adj_Close': ('Adj Close', Decimal),
        }

    def get_column_from_field(self, field_name):
        for field, (col_name, col_type) in self._known_fields.items():
            if col_name == field_name:
                return field
        raise Exception('Field: %s is not known or unhandled' % (field_name, ))

    def get_quote_fields(self):
        """Returns field names and types from given Yahoo YQL field names.

        Each field needs it's name and type defined otherwise an Exception is
        raised.

        """
        # If after all fields, just return the ones we have defined
        if self.columns == '*':
            return self._known_fields

        output = {}

        for field in self.columns:
            if not self._known_fields.has_key(field):
                raise NotImplementedError('Field: %s is not known or unhandled' % (field, ))

            # Find field in our known fields
            data_name, data_type = self._known_fields[field]

            # Add the field name and type to the output
            output[field] = (data_name, data_type)

        return output

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

        # Only interested in Australian equities at the moment
        exchange = 'AX'

        # Create query object - must set the environment for community tables
        y = yql.Public()
        env = 'http://www.datatables.org/alltables.env'

        # Execute the query and get the response
        query = 'select * from yahoo.finance.historicaldata ' \
            'where symbol = "%(code)s.%(exchange)s" ' \
            'and startDate = "%(start_date)s" and endDate = "%(end_date)s"' \
            % {
                'code': self.code, 'exchange': exchange,
                'start_date': start_date, 'end_date': end_date,
            }
        response = y.execute(query, env=env)

        # If the response results are null there was an error
        if response.results is None:
            raise Exception('Error with results')

        # Get the quote
        quote = response.results['quote']

        return quote

    def parse_quote(self):
        """Parse the raw data from a Yahoo finance YQL historical quote into a
        dictionary of useful data.

        Given a dictionary containing the fields to include in the result.

        """
        if self.fields == {} or self.fields is None:
            raise Exception('Quote cannot be parsed without output field dictionary.')

        output = []

        # Populate the output list with data dictionaries
        for data in self.raw_quote:

            # Create dictionary for this data
            dic = {}

            for key, value in data.items():
                # Ignore fields in data that are not in requested field dict
                if not self.fields.has_key(key):
                    continue
                # YQL historical quotes have superfluous 'date' field
                if key == 'date':
                   continue
                # Lookup data name and data type
                data_name, data_type = self.fields[key]

                # Apply the datatype
                dic[data_name] = data_type(value)

            # Add the data dictionary to the output
            output.append(dic)

        return output

    def process_quote(self):
        """Helper method to process a quote.

        Runs the get_quote_fields, get_raw_quote and parse_quote methods.

        """
        # Determine the field names and types
        self.fields = self.get_quote_fields()

        # Fetch the raw quote
        self.raw_quote = self.get_raw_quote()

        # Parse the raw quote with the field names and types
        self.quote = self.parse_quote()


class YahooCSVQuoteHistory(QuoteBase):
    """Represents a set of historical quotes that are obtained via the Yahoo
    CSV API.

    """
    def __init__(self, code, date_range, columns='*', defer=False):
        """Initialise a YahooQuoteHistory given the stock code and date range.

        Optionally give a list of columns to include in the YQL query (default is
        all columns `*`).

        """
        # Store the stock code and columns of data to fetch
        self.code = code
        self.date_range = date_range
        self.columns = columns

        # Default value of quote
        self.fields = {}
        self.raw_quote = None
        self.quote = None

        # Process quote or defer it for later
        if not defer:
            self.process_quote()

    @property
    def _known_fields(self):
        return {
            'Date': ('Date', parse_date),
            'Open': ('Open', Decimal),
            'High': ('High', Decimal),
            'Low': ('Low', Decimal),
            'Close': ('Close', Decimal),
            'Volume': ('Volume', Decimal),
            'Adj Close': ('Adj Close', Decimal),
        }

    def get_column_from_field(self, field_name):
        for field, (col_name, col_type) in self._known_fields.items():
            if col_name == field_name:
                return field
        raise Exception('Field: %s is not known or unhandled' % (field_name, ))

    def get_quote_fields(self):
        """Returns field names and types from given Yahoo YQL field names.

        Each field needs it's name and type defined otherwise an Exception is
        raised.

        """
        # If after all fields, just return the ones we have defined
        if self.columns== '*':
            return self._known_fields

        output = {}

        for field in self.columns:
            if not self._known_fields.has_key(field):
                raise NotImplementedError('Field: %s is not known or unhandled' % (field, ))

            # Find field in our known fields
            data_name, data_type = self._known_fields[field]

            # Add the field name and type to the output
            output[field] = (data_name, data_type)

        return output

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

        # Only interested in Australian equities at the moment
        exchange = 'AX'

        quote_url = 'http://ichart.yahoo.com/table.csv' \
            '?s=%(code)s.%(exchange)s' \
            '&a=%(start_month)s&b=%(start_day)s&c=%(start_year)s' \
            '&d=%(end_month)s&e=%(end_day)s&f=%(end_year)s' \
            '&g=%(period)s' \
            '&ignore=.csv' \
            % {
                'code': self.code, 'exchange': exchange,
                'start_month': start_date.month - 1, 'start_day': start_date.day,
                'start_year': start_date.year, 'end_month': end_date.month - 1,
                'end_day': end_date.day, 'end_year': end_date.year,
                'period': 'd',
            }

        response = urllib2.urlopen(quote_url)

        quote = response.read()

        return quote

    def parse_quote(self):
        """Parse the raw data from a Yahoo finance CSV historical quote into a
        dictionary of useful data.

        Given a dictionary containing the fields to include in the result.

        """
        if self.fields == {} or self.fields is None:
            raise Exception('Quote cannot be parsed without output field dictionary.')

        # Use the CSV module to parse the quote
        reader = csv.reader(self.raw_quote.split('\n'))

        # Read the raw data
        raw_data = [row for row in reader]

        # Remove any empty rows
        raw_data.remove([])

        # Remove the headers
        headers = raw_data.pop(0)

        # Trade data is the remaining CSV data
        data = raw_data

        output = []

        # Populate the output list with data dictionaries
        for i in range(len(data)):
            # Create dictionary for this data
            dic = {}

            for j in range(len(headers)):
                # Ignore fields in data that are not in requested field dict
                if not self.fields.has_key(headers[j]):
                    continue

                # Lookup data name and data type
                data_name, data_type = self.fields[headers[j]]

                # Apply the datatype
                dic[data_name] = data_type(data[i][j])

            # Add the data dictionary to the output
            output.append(dic)

        return output

    def process_quote(self):
        """Helper method to process a quote.

        Runs the get_quote_fields, get_raw_quote and parse_quote methods.

        """

        # Determine the field names and types
        self.fields = self.get_quote_fields()

        # Fetch the raw quote
        self.raw_quote = self.get_raw_quote()

        # Parse the raw quote with the field names and types
        self.quote = self.parse_quote()
