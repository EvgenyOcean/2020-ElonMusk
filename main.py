import discord
import os
from discord.ext import commands


# cmon, let's get real here
intents = discord.Intents.all()
mia = commands.Bot(command_prefix="$mia", intents=intents)


@mia.event
async def on_ready(self):
    print('Mia is ready')


mia.run(os.environ.get('MIA_TOKEN'))