import re

from datetime import date, datetime, time, timedelta

LOOKBACK_DAYS = 60

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

    From django.utils.dateparse.

    """
    date_re = re.compile(
        r'(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})$'
    )
    match = date_re.match(value)
    if match:
        return date(**dict((k, int(v)) for k, v in match.groupdict().items()))

def parse_time(value):
    """Parses a string and return a datetime.time.

    This function doesn't support time zone offsets.

    From django.utils.dateparse.

    """
    time_re = re.compile(
        r'(?P<hour>\d{1,2}):(?P<minute>\d{1,2})'
        r'(?::(?P<second>\d{1,2})(?:\.(?P<microsecond>\d{1,6})\d{0,6})?)?'
    )
    match = time_re.match(value)
    if match:
        kw = match.groupdict()
        if kw['microsecond']:
            kw['microsecond'] = kw['microsecond'].ljust(6, '0')
        kw = dict((k, int(v)) for k, v in match.groupdict().items() if v is not None)
        return time(**kw)

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
