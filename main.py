import discord
import os
from discord.ext import commands


# cmon, let's get real here
intents = discord.Intents.all()
mia = commands.Bot(command_prefix="$mia ", intents=intents)


@mia.event
async def on_ready():
    print('Mia is ready')


@mia.command(name="who")
async def daddy(ctx, *, command=None):
    if command == 'is your daddy':
        await ctx.send('You know that ^^')
    else:
        await ctx.send('Figure it out!')


mia.run(os.environ.get('MIA_TOKEN'))