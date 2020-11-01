import discord 
import asyncio
import datetime
import pytz
import logging
from functools import cached_property
from discord.ext import commands, tasks
from db import operations

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
        self.elon.loop.create_task(self.fetch_something()) # just for testing remove in the future


    async def fetch_something(self):
        await self.elon.wait_until_ready() # just for testing remove in the future
        command = '''
            SELECT * FROM working_session;
        '''
        results = await operations.fetch(self.elon.pool, command)


def setup(elon):
    elon.add_cog(Focuser(elon))