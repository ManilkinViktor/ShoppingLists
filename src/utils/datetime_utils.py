import datetime


def utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


def validate_utc_timezone(v: datetime.datetime) -> datetime.datetime:
    if v.tzinfo is None:
        raise ValueError('datetime must have timezone')
    if v.tzinfo != datetime.UTC:
        v = v.astimezone(datetime.UTC)

    return v


def validate_not_future_time(v: datetime.datetime) -> datetime.datetime:
    if v > utc_now():
        raise ValueError('datetime cannot be future')
    return v
