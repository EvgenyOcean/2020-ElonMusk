import discord
import os
from discord.ext import commands
from db.initializer import get_pool


extensions = (
    'focuser',
)

# cmon, let's get real here
intents = discord.Intents.all()
elon = commands.Bot(command_prefix="elon.", intents=intents)


@elon.event
async def on_ready():
    print('Elon is ready')


for extension in extensions:
    try:
        elon.load_extension('cogs.' + extension)
    except Exception as err:
        print(err)
    else:
        print(extension + ' has been loaded (success)')


# creating a connection pool
elon.loop.run_until_complete(get_pool(elon))
elon.run(os.environ.get('MIA_TOKEN'))