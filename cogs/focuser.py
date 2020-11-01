import os
import discord 
import asyncio
import logging
from functools import cached_property
from discord.ext import commands, tasks
from db import operations
from utils import get_msk_time


### setting up a logger ###
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# i don't like hardcoded path tho
handler = logging.FileHandler('./logs/focuser.logs')
formatter = logging.Formatter(r'%(asctime)s:%(levelname)s:%(message)s:%(stack_info)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class Focuser(commands.Cog):
    def __init__(self, elon):
        self.elon = elon
        self.in_focus = {}

    @cached_property
    def focus_channel(self):
        '''Getting focus channel'''
        return self.elon.get_channel(int(os.environ.get('FOCUS_ID')))

    @cached_property
    def hall_channel(self):
        '''Getting hall of fame channel'''
        return self.elon.get_channel(int(os.environ.get('HALL_ID')))

    @commands.Cog.listener()
    async def on_voice_state_update(self, member:discord.Member, before, after):
        '''Event fires once user enters or leave a voice channel'''
        try:
            # user joined focus channel
            if after.channel == self.focus_channel:
                await self.handle_user_focused(member)

            # user left focus channel
            elif before.channel == self.focus_channel:
                    await self.handle_user_unfocused(member)                
        except Exception as err:
            logger.exception('User quit/join focus channel error!')

    async def handle_user_focused(self, member):
        '''
        Adds member and the time he joined deep_focus to the self.in_focus
        And sends the message to the hall channel to notify other users
        '''
        start_time = get_msk_time()
        self.in_focus.update({member: start_time})
        await self.hall_channel.send(f'Guys, **{member.display_name}** has just entered the working mode! Try to catch up!')

    async def handle_user_unfocused(self, member):
        '''
        User left deep_focus, time to calculate how much time he spent there.
        Returns the string with time info.
        '''
        started_working = self.in_focus.pop(member)
        end_working = get_msk_time()
        td = end_working - started_working
        ts = td.total_seconds()

        if ts < 60:
            await self.hall_channel.send(f'Nevermind, **{member.display_name}** quit already! Duh!')
            return
        
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
        await self.hall_channel.send(f'Hey, **{member.display_name}** you was productive for __{final_str}__! Hope to see ya soon again!')


def setup(elon):
    elon.add_cog(Focuser(elon))