# PyQuotes
> Get stock quotes from a variety of sources using Python

## About
PyQuotes queries the Yahoo YQL Community tables to get a stock quote.

## Usage
Currently only querying Australian stocks is supported.

Quotes can be obtained from Yahoo's YQL and CSV APIs.

To get a single quote for a company 'ABC' (delayed by 20min) you can use the quote objects
```YahooQuote``` and ```YahooCSVQuote```.
```python
>>> quote = YahooQuote('ABC')           # Quote from YQL API
>>> csv_quote = YahooCSVQuote('ABC')    # Quote from CSV API
```

To get a set of historical quotes given a date range you can use the quote objects
```YahooQuoteHistory``` and ```YahooCSVQuoteHistory```.
```python
>>> history = YahooQuoteHistory('ABC', ['2013-04-10', '2013-04-12'])        # Historical quotes from YQL API
>>> csv_history = YahooCSVQuoteHistory('ABC', ['2013-04-10', '2013-04-12']) # Historical quotes from CSV API
```

The quote objects fetch and parse the quote data.  An optional list of columns
to be used in the query can be added to the quote constructors.

The ```raw_quote``` attribute contains the quote as it is returned from the API,
and the ```quote``` attribute contains the parsed quote.
```python
>>> quote.raw_quote
{u'YearLow': u'2.730', u'OneyrTargetPrice': u'3.490', u'DividendShare': u'0.165', ...}
>>> quote.quote
{'Volume': Decimal('2064145'), 'Close': Decimal('3.310'), 'Code': 'ABC.AX', 'Name': 'ADEL BRTN FPO', 'Exchange': 'ASX'}
```

The quote is only parsed according to fields that have had their quote field name and field type
defined.  This information is in the `known_fields` class attribute in each quote class.

From the ```YahooQuote``` class.
```python
known_fields = {
    'Name': ('Name', str),
    'LastTradePriceOnly': ('Close', Decimal),
    'StockExchange': ('Exchange', str),
    'Symbol': ('Code', str),
    'Volume': ('Volume', Decimal),
}
```
This dictionary specifies that the ```LastTradePriceOnly``` column in the raw
quote should be mapped to the ```Close``` field in the output and converted to
a ```Decimal```.  Other quote classes contain similar dictionaries.

## Author
**Liam Keene**
[Twitter](https://twitter.com/liam_keene) |
[Github](https://github.com/LiamKeene) | [Website](http://liamkeene.com)

## License
> Copyright (c) 2013 Liam Keene (liam.keene@gmail.com)

Licensed under the MIT License
