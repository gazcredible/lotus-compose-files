import datetime
import time


def round_time(dt=None, date_delta=datetime.timedelta(minutes=1), to='average'):
    """
    Round a datetime object to a multiple of a timedelta
    dt : datetime.datetime object, default now.
    dateDelta : timedelta object, we round to a multiple of this, default 1 minute.
    from:  http://stackoverflow.com/questions/3463930/how-to-round-the-minute-of-a-datetime-object-python
    """
    round_to = date_delta.total_seconds()
    if dt is None:
        dt = datetime.now()
    seconds = (dt - dt.min).seconds

    if seconds % round_to == 0 and dt.microsecond == 0:
        rounding = (seconds + round_to / 2) // round_to * round_to
    else:
        if to == 'up':
            # // is a floor division, not a comment on following line (like in javascript):
            rounding = (seconds + dt.microsecond / 1000000 + round_to) // round_to * round_to
        elif to == 'down':
            rounding = seconds // round_to * round_to
        else:
            rounding = (seconds + round_to / 2) // round_to * round_to

    return dt + datetime.timedelta(0, rounding - seconds, - dt.microsecond)


def is_fiware_valid_ms(fiware_time):
    try:
        dt = datetime.datetime.strptime(fiware_time, '%Y-%m-%dT%H:%M:%S.%fZ')
        return True
    except Exception as e:
        pass

    return False


def is_fiware_valid_no_ms(fiware_time):
    try:
        dt = datetime.datetime.strptime(fiware_time, '%Y-%m-%dT%H:%M:%SZ')
        return True
    except Exception as e:
        pass

    return False


def is_fiware_valid(fiware_time):
    return is_fiware_valid_ms(fiware_time) or is_fiware_valid_no_ms(fiware_time)


def fiware_to_datetime(fiware_time):
    try:
        if '.' in fiware_time:
            return datetime.datetime.strptime(fiware_time, '%Y-%m-%dT%H:%M:%S.%fZ')

        return datetime.datetime.strptime(fiware_time, '%Y-%m-%dT%H:%M:%SZ')
    except Exception as e:
        # no seconds?
        return datetime.datetime.strptime(fiware_time, '%Y-%m-%dT%H:%MZ')


def fiware_to_time(fiware_time):
    return fiware_to_datetime(fiware_time).timestamp()


def time_to_fiware(time_in_sec):
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.localtime(time_in_sec))


def datetime_to_fiware(time_as_datetime):
    try:
        dt = time_as_datetime
        return str(dt.year) + '-' + str(dt.month).zfill(2) + '-' + str(dt.day).zfill(2) + 'T' + str(dt.hour).zfill(2) + ':' + str(dt.minute).zfill(2) + ':' + str(dt.second).zfill(2) + 'Z'
        return time_to_fiware(time_as_datetime.timestamp())
    except Exception as e:
        print('datetime_to_fiware()-' + str(e))


def time_to_datetime(time_in_sec):
    return datetime.datetime.fromtimestamp(time_in_sec)


def time_to_timestamp(time_as_sec):
    return datetime.datetime.timestamp(time_to_datetime(time_as_sec))


def date_to_fiware(date_string):
    try:
        return datetime_to_fiware(datetime.datetime.strptime(date_string, "%Y-%m-%d"))
    except Exception as e:
        print('date_to_fiware()-' + str(e))


def fiware_to_date(fiware_datetime):
    fiware_datetime = fiware_datetime.replace('.000', '')

    rawtime = ''

    try:
        rawtime = datetime.datetime.timestamp(datetime.datetime.strptime(fiware_datetime, '%Y-%m-%dT%H:%M:%SZ'))
    except Exception as e:
        rawtime = datetime.datetime.timestamp(datetime.datetime.strptime(fiware_datetime, '%Y-%m-%dT%H:%MZ'))

    return time.strftime('%Y-%m-%d', time.localtime(rawtime))


def datetime_to_date(time_as_datetime):
    return time_as_datetime.strftime('%Y-%m-%d')


def datetime_to_timestamp(time_as_datetime):
    try:
        return datetime.datetime.timestamp(time_as_datetime)
    except Exception as e:
        print('datetime_to_timestamp()-' + str(e))


def date_to_timestamp(date_string):
    return datetime_to_timestamp(datetime.datetime.strptime(date_string, "%Y-%m-%d"))


def date_to_datetime(date_string):
    try:
        return datetime.datetime.strptime(date_string, "%Y-%m-%d")
    except Exception as e:
        print('date_to_datetime()-' + str(e))


def prettyprint_fiware(fiware_datetime: str) -> str:
    try:
        result = datetime_to_fiware(fiware_to_datetime(fiware_datetime))
        result = result.replace('Z', '')
        result = result.replace('T', ' ')

        return result

    except Exception as e:
        print('prettyprint_fiware()-' + str(e))

    return fiware_datetime
