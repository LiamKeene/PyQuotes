import csv
import re
import urllib2
import yql

from datetime import date, datetime, timedelta
from decimal import Decimal

DATE_RE = re.compile(
    r'(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})$'
)
LOOKBACK_DAYS = 60


class QuoteBase(object):
    """Abstract quote model that defines standard attributes and methods for
    different models.

    """
    def get_raw_quote(self):
        """Method to fetch a raw unparsed quote from a provider."""
        raise NotImplementedError('This method must be defined by subclass.')

    def get_quote_fields(self):
        """Method to get the field names and data types for this quote."""
        raise NotImplementedError('This method must be defined by subclass.')

    def parse_quote(self):
        """Method to parse a raw quote from a provider into a standard format."""
        raise NotImplementedError('This method must be defined by subclass.')


class YahooQuote(QuoteBase):
    """Represents a quote that is obtained via the Yahoo Finance community table
    using the YQL library.

    """
    def __init__(self, code, columns='*', defer=False):
        """Initialise a YahooQuote given the stock code.

        Optionally give a list of columns to include in the YQL query (default is
        all columns `*`).

        """
        # Store the stock code and columns of data to fetch
        self.code = code
        self.columns = columns

        # Default value of quote
        self.fields = {}
        self.raw_quote = None
        self.quote = None

        # Process quote or defer it for later
        if not defer:
            self.process_quote()

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

        # Ensure the error column in included and then join as a comma separated string
        if not self.columns == '*' and not error_column in self.columns:
            self.columns.append(error_column)
        columns = ','.join(self.columns)

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

    def get_quote_fields(self):
        """Returns dictionary of field names and types from given Yahoo YQL field names.

        Each field needs it's name and type defined otherwise an Exception is
        raised.

        """
        known_fields = {
            'Name': {'name': 'Name', 'type': str, },
            'LastTradePriceOnly': {'name': 'Close', 'type': Decimal, },
            'StockExchange': {'name': 'Exchange', 'type': str, },
            'Symbol': {'name': 'Code', 'type': str, },
            'Volume': {'name': 'Volume', 'type': Decimal, },
        }

        # If querying all fields, just return the ones we have defined
        if self.columns == '*':
            return known_fields

        output = {}

        for field in self.columns:
            if not known_fields.has_key(field):
                raise NotImplementedError('Field: %s is not known or unhandled' % (field, ))

            # Find field in our known fields
            data = known_fields[field]

            # Add the field name and type to the output
            output[field] = (data['name'], data['type'])

        return output

    def parse_quote(self):
        """Parse the raw data from a Yahoo finance YQL quote into a dictionary of
        useful data.

        Given a dictionary containing the fields to include in the result.

        """
        if self.fields == {} or self.fields is None:
            raise Exception('Quote cannot be parsed without output field dictionary.')

        output = {}

        for key, value in self.raw_quote.items():
            # Ignore fields in data that are not in requested field dict
            if not self.fields.has_key(key):
                continue
            field_name, field_type = self.fields[key]
            output[field_name] = field_type(value)

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


class YahooCSVQuote(QuoteBase):
    """Represents a quote that is obtained via the Yahoo CSV API.

    """
    def __init__(self, code, symbols='nsxl1', defer=False):
        """Initialise a YahooCSVQuote given the stock code.

        Optionally give a list of symbols to include in the CSV Url (default is
        `nsxl1`).

        """
        # Store the stock code and columns of data to fetch
        self.code = code
        self.symbols = symbols

        # Default value of quote
        self.parsed_symbols = ()
        self.fields = ()
        self.raw_quote = None
        self.quote = None

        # Process quote or defer it for later
        if not defer:
            self.process_quote()

    def get_raw_quote(self):
        """Get a quote from the Yahoo Finance CSV API and return the result.

        Given the code of the stock and an optional list of symbols that correspond
        to types of data to get in the quote.

        """
        if not len(self.code) == 3:
            raise Exception('Stock code appears incorrect')

        # Only interested in Australian equities at the moment
        exchange = 'AX'

        quote_url = u'http://finance.yahoo.com/d/quotes.csv' \
            '?s=%(code)s.%(exchange)s&f=%(symbols)s' \
            % {
                'code': self.code, 'exchange': exchange, 'symbols': self.symbols,
            }

        response = urllib2.urlopen(quote_url)

        quote = response.read()

        return quote

    def get_quote_fields(self):
        """Returns field names and types from given Yahoo CSV symbols.

        Each symbol needs it's name and type defined otherwise an Exception is
        raised.

        """
        known_symbols = {
            'g': {'name': 'Low', 'type': Decimal, },
            'h': {'name': 'High', 'type': Decimal, },
            'l1': {'name': 'Close', 'type': Decimal, },
            'n': {'name': 'Name', 'type': str, },
            'o': {'name': 'Open', 'type': Decimal, },
            's': {'name': 'Code', 'type': str, },
            'v': {'name': 'Volume', 'type': Decimal, },
            'x': {'name': 'Exchange', 'type': str, },
        }

        output = []

        for symbol in self.parsed_symbols:
            if not known_symbols.has_key(symbol):
                raise NotImplementedError('Symbol: %s is not known or unhandled' % (symbol, ))

            # Find symbol in our known symbols
            data = known_symbols[symbol]

            # Add the field name and type to the output
            output.append((data['name'], data['type']))

        return tuple(output)

    def parse_symbols(self):
        """Parse a string of Yahoo CSV symbols and return them as a tuple.

        This is required as the symbols are either single letters or a letter and
        an integer.

        """
        # Split symbols into a list
        symbol_list = list(self.symbols)

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

    def parse_quote(self):
        """Parse the raw data from a Yahoo finance CSV quote into a dictionary of
        useful data.

        Given a dictionary containing the fields to include in the result.

        """
        if self.fields == () or self.fields is None:
            raise Exception('Quote cannot be parsed without output field tuple.')

        # Use the CSV module to parse the quote
        reader = csv.reader(self.raw_quote.split(','))

        # Read the raw data
        raw_data = [row[0] for row in reader]

        output = {}

        for i in range(len(self.fields)):
            field_name, field_type = self.fields[i]
            output[field_name] = field_type(raw_data[i])

        return output

    def process_quote(self):
        """Helper method to process a quote.

        Runs the parse_symbols, get_quote_fields, get_raw_quote and parse_quote methods.

        """
        # Parse the CSV symbols
        self.parsed_symbols = self.parse_symbols()

        # Determine the field names and types
        self.fields = self.get_quote_fields()

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

    def get_quote_fields(self):
        """Returns field names and types from given Yahoo YQL field names.

        Each field needs it's name and type defined otherwise an Exception is
        raised.

        """
        known_fields = {
            'Date': {'name': 'Date', 'type': parse_date, },
            'Open': {'name': 'Open', 'type': Decimal, },
            'High': {'name': 'High', 'type': Decimal, },
            'Low': {'name': 'Low', 'type': Decimal, },
            'Close': {'name': 'Close', 'type': Decimal, },
            'Volume': {'name': 'Volume', 'type': Decimal, },
        }

        # If after all fields, just return the ones we have defined
        if self.columns == '*':
            return known_fields

        output = {}

        for field in self.columns:
            if not known_fields.has_key(field):
                raise NotImplementedError('Field: %s is not known or unhandled' % (field, ))

            # Find field in our known fields
            data = known_fields[field]

            # Add the field name and type to the output
            output[field] = (data['name'], data['type'])

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

    def get_quote_fields(self):
        """Returns field names and types from given Yahoo YQL field names.

        Each field needs it's name and type defined otherwise an Exception is
        raised.

        """
        known_fields = {
            'Date': {'name': 'Date', 'type': parse_date, },
            'Open': {'name': 'Open', 'type': Decimal, },
            'High': {'name': 'High', 'type': Decimal, },
            'Low': {'name': 'Low', 'type': Decimal, },
            'Close': {'name': 'Close', 'type': Decimal, },
            'Volume': {'name': 'Volume', 'type': Decimal, },
        }

        # If after all fields, just return the ones we have defined
        if self.columns== '*':
            return known_fields

        output = {}

        for field in self.columns:
            if not known_fields.has_key(field):
                raise NotImplementedError('Field: %s is not known or unhandled' % (field, ))

            # Find field in our known fields
            data = known_fields[field]

            # Add the field name and type to the output
            output[field] = (data['name'], data['type'])

        return output

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

def validate_date_range(date_range):
    """Validate a date range.

    A date range must be a list of two elements; the first representing a start
    date and the second an end date.  The elements may be date objects or string
    representations of a date (yyyy-mm-dd format).

    Returns the date_range list using string representations.

    """
    DATE_FORMAT = '%Y-%m-%d'

    # date_range must be a list
    if not isinstance(date_range, list):
        raise TypeError('Date range must be a list')

    # date_range must have two elements only
    if not len(date_range) == 2:
        raise ValueError('Date range must be a list of two elements.')

    # test start and end dates for the correct type
    start_date = date_range[0]
    end_date = date_range[1]

    # If the end_date is None or empty string, the default is today
    if end_date is None or end_date is '':
        end_date = date.today()

    # if the start_date is None or empty string, the default is end_date minus a defined amount
    if start_date is None or start_date is '':
        start_date = end_date - timedelta(days=LOOKBACK_DAYS)

    if not isinstance(start_date, (str, date)) or not isinstance(end_date, (str, date)):
        raise TypeError('Range elements must be strings or date objects')

    # try to convert start and end dates to date object
    if isinstance(start_date, str):
        try:
            start_date = datetime.strptime(start_date, DATE_FORMAT).date()
        except ValueError:
            raise ValueError('Start date must be in %s format' %(DATE_FORMAT, ))
    if isinstance(end_date, str):
        try:
            end_date = datetime.strptime(end_date, DATE_FORMAT).date()
        except ValueError:
            raise ValueError('End date must be in %s format' %(DATE_FORMAT, ))

    # date_range elements must be sane (start <= end, start <= today)
    if not start_date <= end_date or not start_date <= date.today():
        raise ValueError('Start date must be before end date, and not in the future')

    # Finally (!) we have an acceptable date range list
    return True, [start_date, end_date]

def date_range_generator(start_date, end_date):
    """Returns a generator of the dates bound by the given start and end date.

    The start and end dates must be date (or datetime) objects

    """
    # Only allow date or datetime objects
    if not isinstance(start_date, (date, datetime)) or \
            not isinstance(end_date, (date, datetime)):
        raise Exception('Start and end dates must be date or datetime objects.')

    # If range bounds are datetime, extract the date component
    if isinstance(start_date, datetime):
        start_date = start_date.date()
    if isinstance(end_date, datetime):
        end_date = end_date.date()

    # Create a generator of date objects between the start and end dates
    while True:
        yield start_date
        start_date = start_date + timedelta(days=1)
        if start_date > end_date:
            break

def parse_date(value):
    """Parses a string and returns a datetime.date object.

    From django.utils.parse_date.

    """
    match = DATE_RE.match(value)
    if match:
        return date(**dict((k, int(v)) for k, v in match.groupdict().items()))
