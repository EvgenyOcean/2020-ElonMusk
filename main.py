import discord
import os
import logging
from discord.ext import commands
from db.initializer import get_pool

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(r'||||| %(asctime)s: ||||| %(levelname)s:%(message)s')
handler = logging.FileHandler(filename='./logs/general.logs')
handler.setFormatter(formatter)
logger.addHandler(handler)

extensions = (
    'focuser',
    'reporter',
)

# cmon, let's get real here
intents = discord.Intents.all()
elon = commands.Bot(command_prefix="elon.", intents=intents)


@elon.event
async def on_ready():
    logger.info('Elon has been successfully loaded!')


@elon.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CommandNotFound):
        await ctx.send('Command doesn\'t exist!')
    else:
        logger.exception('Global Command Catch Exception')
        await ctx.send('Something went wrong! Try again later!')


for extension in extensions:
    try:
        elon.load_extension('cogs.' + extension)
    except Exception as err:
        logger.exception(f'{extension} failed to load')
    else:
        logger.info(extension + ' has been loaded (success)')


# creating a connection pool
elon.loop.run_until_complete(get_pool(elon))
elon.run(os.environ.get('MIA_TOKEN'))