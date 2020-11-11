import discord 
import datetime
import asyncio
import logging
from functools import cached_property
from discord.ext import commands
from db import operations
from utils import get_msk_time, ChannelsMixin, get_final_string


### setting up a logger ###
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# i don't like hardcoded path tho
handler = logging.FileHandler('./logs/focuser.logs')
formatter = logging.Formatter(r'%(asctime)s:%(levelname)s:%(message)s:%(stack_info)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class Focuser(commands.Cog, ChannelsMixin):
    def __init__(self, elon):
        self.elon = elon
        self.in_focus = {}

    @commands.Cog.listener()
    async def on_voice_state_update(self, member:discord.Member, before, after):
        '''
        Event fires once user enters or leave a voice channel
        Also fires once you mute/unmute mic or sound
        '''
        try:
            # users changed sound/voice settings, 
            # but didn't change the channel
            if after.channel == before.channel:
                return
            # user joined focus channel
            elif after.channel == self.focus_channel:
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

        await operations.execute_focus(self.elon.pool, member)
        await self.briefing_channel.send(f'Guys, **{member.display_name}** has just entered the working mode! Try to catch up!')

    async def handle_user_unfocused(self, member):
        '''
        User left deep_focus, time to calculate how much time he spent there.
        Returns the string with time info.
        '''
        result = await operations.fetch_unfocus(self.elon.pool, member)
        try:
            ts = int(result[0].get('duration'))
            if ts < 60:
                # send the seconds
                await self.briefing_channel.send(f'Dude, **{member.display_name}** worked for {ts} seconds! That is sick!')
                # TODO: implement banning user if he abuses quiting/entering the focus channel
                # delete the entries which are less than a minute
                await operations.less_than_minute(self.elon.pool, member)
            else:   
                final_str = get_final_string(ts)
                await self.briefing_channel.send(f'Hey, **{member.display_name}** you was productive for __{final_str}__! Hope to see ya soon again!')

        except Exception as err:
            logger.exception(err)
            await self.briefing_channel.send(f'Houston, we have a bit of a problem!')


def setup(elon):
    elon.add_cog(Focuser(elon))