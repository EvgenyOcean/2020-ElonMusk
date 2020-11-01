import datetime
import pytz


def get_msk_time():
    dt_utcnow = datetime.datetime.now(tz=pytz.UTC)
    msk_time = dt_utcnow.astimezone(pytz.timezone('Europe/Moscow'))
    return msk_time
