# PyQuotes
> Get stock quotes from a variety of sources using Python

## About
PyQuotes queries the Yahoo YQL Community tables to get a stock quote.

## Usage
To get the latest quote (delayed by 20min)for a company ABC use the following
command.  Currently only querying Australian stocks is supported.
```python
>>> get_yahoo_quote('ABC')
(True, {u'YearLow': u'2.730', u'OneyrTargetPrice': u'3.490', ... })
```

## Author
**Liam Keene**
[Twitter](https://twitter.com/liam_keene) |
[Github](https://github.com/LiamKeene) | [Website](http://liamkeene.com)

## License
> Copyright (c) 2013 Liam Keene (liam.keene@gmail.com)

Licensed under the MIT License
