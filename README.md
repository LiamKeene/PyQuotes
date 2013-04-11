# PyQuotes
> Get stock quotes from a variety of sources using Python

## About
PyQuotes queries the Yahoo YQL Community tables to get a stock quote.

## Usage
Currently only querying Australian stocks is supported.

To get the latest quote (delayed by 20min)for a company ABC use the following
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
(True, [{u'2013-04-12', u'Close': u'3.33', ...},
{u'Date': u'2013-04-11', u'Close': u'3.34', ...},
{u'Date': u'2013-04-10', u'Close': u'3.40', ...}])
```
The returned quote contains an array with a dictionary of data for each day in
the specified date range.

## Author
**Liam Keene**
[Twitter](https://twitter.com/liam_keene) |
[Github](https://github.com/LiamKeene) | [Website](http://liamkeene.com)

## License
> Copyright (c) 2013 Liam Keene (liam.keene@gmail.com)

Licensed under the MIT License
