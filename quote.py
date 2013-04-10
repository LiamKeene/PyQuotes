import yql

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
