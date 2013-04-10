import yql

def get_yahoo_quote(code):
    """Get a quote from the Yahoo YQL finance tables and return the result.

    """
    # Only interested in Australian equities at the moment
    exchange = 'AX'

    # Create query and execute
    y = yql.Public()
    env = 'http://www.datatables.org/alltables.env'
    query = 'select * from yahoo.finance.quotes where symbol = "%s.%s"' % (code, exchange)
    response = y.execute(query, env=env)

    # Get the quote and the error field
    quote = response.results['quote']
    error = quote['ErrorIndicationreturnedforsymbolchangedinvalid']

    if error is None:
        # Valid code and quote
        return True, quote

    raise Exception(error)
