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

def raw_yahoo_quote(code, query_columns='*'):
    """Get a quote from the Yahoo YQL finance tables and return the result.

    Given the code of the stock and an optional list of columns of data to get
    in the quote.

    """
    # Only interested in Australian equities at the moment
    exchange = 'AX'

    # Error column name - save typing
    error_column = 'ErrorIndicationreturnedforsymbolchangedinvalid'

    # Create query object - must set the environment for community tables
    y = yql.Public()
    env = 'http://www.datatables.org/alltables.env'

    # Ensure the error column is included and then join as a comma separated string
    if not query_columns == '*' and not error_column in query_columns:
        query_columns.append(error_column)
    columns = ','.join(query_columns)

    # Execute the query and get the response
    query = 'select %(columns)s from yahoo.finance.quotes where symbol = "%(code)s.%(exchange)s"' \
        % {'code': code, 'exchange': exchange, 'columns': columns, }
    response = y.execute(query, env=env)

    # Get the quote and the error field
    quote = response.results['quote']
    error = quote[error_column]

    # If no error return the quote or raise an exception
    if error is None:
        # Valid code and quote
        return True, quote

    raise Exception(error)

def raw_yahoo_csv_quote(code, symbols='nsxl1'):
    """Get a quote from the Yahoo Finance CSV API and return the result.

    Given the code of the stock and an optional list of symbols that correspond
    to types of data to get in the quote.

    """
    if not len(code) == 3:
        raise Exception('Stock code appears incorrect')

    # Only interested in Australian equities at the moment
    exchange = 'AX'

    quote_url = u'http://finance.yahoo.com/d/quotes.csv' \
        '?s=%(code)s.%(exchange)s&f=%(symbols)s' \
        % {
            'code': code, 'exchange': exchange, 'symbols': symbols,
        }

    response = urllib2.urlopen(quote_url)

    quote = response.read()

    return True, quote

def raw_yahoo_quote_history(code, date_range):
    """Get a list of quotes from the Yahoo YQL finance tables and return the result.

    Given the code of the stock and a list containing the start and end dates of
    the data.

    """
    # Validate dates first
    ret, date_range = validate_date_range(date_range)

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
            'code': code, 'exchange': exchange,
            'start_date': start_date, 'end_date': end_date,
        }
    response = y.execute(query, env=env)

    # If the response results are null there was an error
    if response.results is None:
        raise Exception('Error with results')

    # Get the quote
    quote = response.results['quote']

    return True, quote

def raw_yahoo_csv_quote_history(code, date_range):
    """Get a list of quotes from the Yahoo Finanace CSV API and return the result.

    Given the code of the stock and a list containing the start and end dates of
    the data.

    """
    # Validate dates first
    ret, date_range = validate_date_range(date_range)

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
            'code': code, 'exchange': exchange,
            'start_month': start_date.month - 1, 'start_day': start_date.day,
            'start_year': start_date.year, 'end_month': end_date.month - 1,
            'end_day': end_date.day, 'end_year': end_date.year,
            'period': 'd',
        }

    response = urllib2.urlopen(quote_url)

    quote = response.read()

    return True, quote

def parse_yahoo_csv_quote_symbols(symbols):
    """Parse a string of Yahoo CSV symbols and return them as a tuple.

    This is required as the symbols are either single letters or a letter and
    an integer.

    """
    # Split symbols into a list
    symbol_list = list(symbols)

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

def get_yahoo_csv_quote_fields(symbols):
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

    for symbol in symbols:
        if not known_symbols.has_key(symbol):
            raise NotImplementedError('Symbol: %s is not known or unhandled' % (symbol, ))

        # Find symbol in our known symbols
        data = known_symbols[symbol]

        # Add the field name and type to the output
        output.append((data['name'], data['type']))

    return tuple(output)

def parse_yahoo_csv_quote(raw_quote, fields):
    """Parse the raw data from a Yahoo finance CSV quote into a dictionary of
    useful data.

    """
    # Use the CSV module to parse the quote
    reader = csv.reader(raw_quote.split(','))

    # Read the raw data
    raw_data = [row[0] for row in reader]

    output = {}

    for i in range(len(fields)):
        field_name, field_type = fields[i]
        output[field_name] = field_type(raw_data[i])

    return output

def parse_yahoo_csv_quote_history(raw_quote):
    """Parse the raw data from a Yahoo finance CSV historical quote into a
    dictionary of useful data.

    """
    # Data types for the historical quote fields
    data_types = {
        'Date': parse_date, 'Open': Decimal, 'High': Decimal, 'Low': Decimal,
        'Close': Decimal, 'Volume': Decimal, 'Adj Close': Decimal,
    }

    # Use the CSV module to parse the quote
    reader = csv.reader(raw_quote.split('\n'))

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
             # Lookup data type
            data_type = data_types[headers[j]]

            # Apply the datatype
            dic[headers[j]] = data_type(data[i][j])

        # Add the data dictionary to the output
        output.append(dic)

    return output

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
