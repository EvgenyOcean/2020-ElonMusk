import datetime
import os
from functools import cached_property
import pytz


def get_msk_time():
    dt_utcnow = datetime.datetime.now(tz=pytz.UTC)
    msk_time = dt_utcnow.astimezone(pytz.timezone('Europe/Moscow'))
    return msk_time


class ChannelsMixin:
    @cached_property
    def focus_channel(self):
        '''Getting focus channel'''
        return self.elon.get_channel(int(os.environ.get('FOCUS_ID')))

    @cached_property
    def hall_channel(self):
        '''Getting hall of fame channel'''
        return self.elon.get_channel(int(os.environ.get('HALL_ID')))