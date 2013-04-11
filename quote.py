import yql

from datetime import date, datetime

def get_yahoo_quote(code, query_columns='*'):
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

    # date_range elements must be sane (start < end, start <= today)
    if not start_date < end_date or not start_date <= date.today():
        raise ValueError('Start date must be before end date, and not in the future')

    return False, date_range
