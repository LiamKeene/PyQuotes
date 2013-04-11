# PyQuotes
> Get stock quotes from a variety of sources using Python

## About
PyQuotes queries the Yahoo YQL Community tables to get a stock quote.

## Usage
Currently only querying Australian stocks is supported.

### Obtaining Quotes

To get the latest quote (delayed by 20min) for a company ABC use the following
command.
```python
>>> get_yahoo_quote('ABC')
(True, {u'YearLow': u'2.730', u'OneyrTargetPrice': u'3.490', ... })
```
This returns all the information in the table.

To get a subset of columns of the latest quote (delayed by 20min) for a company
ABC use the following command.
```python
>>> quote.get_yahoo_quote('ABC', ['Symbol', 'LastTradePriceOnly', ])
(True, {u'ErrorIndicationreturnedforsymbolchangedinvalid': None,
u'Symbol': u'ABC.AX', u'LastTradePriceOnly': u'3.310'})
```
The very long key in the dictionary is returned in all queries to check that the
given symbol (stock code) was valid.

You can also request historical prices for a stock using the command.
```python
>>> quote.get_yahoo_quote_history('ABC', ['2013-04-10', '2013-04-12'])
(True, [{u'Date': u'2013-04-12', u'Close': u'3.33', ...},
{u'Date': u'2013-04-11', u'Close': u'3.34', ...},
{u'Date': u'2013-04-10', u'Close': u'3.40', ...}])
```
The returned quote contains an array with a dictionary of data for each day in
the specified date range.

Quotes may also be obtained using Yahoo's CSV API, which can be more reliable
than the YQL API.  The functions are ```get_yahoo_csv_quote``` and
```get_yahoo_csv_history```.  The ```get_yahoo_csv_quote``` function takes a
string of symbols that correspond to the data to return.  These symbols can be
found at http://www.jarloo.com/yahoo_finance/.

### Parsing Quotes
The Yahoo CSV Quotes output raw strings of data, which can be parsed into more
manageable formats using the ```parse_yahoo_quote``` and ```parse_yahoo_history```
functions.

```python
>>> quote = get_yahoo_csv_quote_history('ABC', ['2013-04-10', '2013-04-12'])
>>> parse_yahoo_history(quote[1]) # The first element is a boolean for quote success
(['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close'],
[['2013-04-12', '3.36', '3.38', '3.31', '3.33', '1351200', '3.33'],
['2013-04-11', '3.39', '3.41', '3.33', '3.34', '1225300', '3.34'],
['2013-04-10', '3.39', '3.41', '3.38', '3.40', '2076700', '3.40']])
```

## Author
**Liam Keene**
[Twitter](https://twitter.com/liam_keene) |
[Github](https://github.com/LiamKeene) | [Website](http://liamkeene.com)

## License
> Copyright (c) 2013 Liam Keene (liam.keene@gmail.com)

Licensed under the MIT License
