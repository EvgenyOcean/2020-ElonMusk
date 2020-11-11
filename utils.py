import datetime
import os
from functools import cached_property
import pytz


def get_msk_time():
    dt_utcnow = datetime.datetime.now(tz=pytz.UTC)
    msk_time = dt_utcnow.astimezone(pytz.timezone('Europe/Moscow'))
    return msk_time


def get_final_string(duration):
    td = datetime.timedelta(seconds=duration)
    time_obj = {
        'days': td.days,
        'hours': td.seconds//3600,
        'minute(s)': (td.seconds//60)%60
    }

    final_str = ''
    for time_prop in time_obj:
        value = time_obj[time_prop]
        if value != 0:
            final_str += f' {value} {time_prop}'
    final_str = final_str.strip()

    return final_str


class ChannelsMixin:
    @cached_property
    def focus_channel(self):
        '''Getting focus channel'''
        return self.elon.get_channel(int(os.environ.get('FOCUS_CHANNEL_ID')))

    @cached_property
    def hall_channel(self):
        '''Getting hall of fame channel'''
        return self.elon.get_channel(int(os.environ.get('HALL_CHANNEL_ID')))

    @cached_property
    def briefing_channel(self):
        '''Getting briefing channel'''
        return self.elon.get_channel(int(os.environ.get('BRIEFING_CHANNEL_ID')))

    @cached_property
    def hello_channel(self):
        '''Getting hello channel'''
        return self.elon.get_channel(int(os.environ.get('HELLO_CHANNEL_ID')))

    @cached_property
    def main_guild(self):
        '''Getting the server(guild)'''
        return self.elon.get_guild(int(os.environ.get('GUILD_ID')))
