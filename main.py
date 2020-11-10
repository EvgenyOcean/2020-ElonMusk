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
    # 'reporter',
    # 'greeter',
    # 'moderator',
)


# cmon, let's get real here
intents = discord.Intents.all()
elon = commands.Bot(command_prefix="elon.", intents=intents)
elon.debug = os.environ.get('DEBUG_VALUE') == 'True'

@elon.event
async def on_ready():
    logger.info('Elon has been successfully loaded!')


@elon.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CommandNotFound):
        await ctx.send('Command doesn\'t exist!')
    elif isinstance(error, commands.errors.MemberNotFound):
        logger.warning('One of the commands returned Member Not Found')
    else:
        logger.warning(error, exc_info=True)


for extension in extensions:
    try:
        elon.load_extension('cogs.' + extension)
    except Exception as err:
        logger.exception(f'{extension} failed to load')
    else:
        logger.info(extension + ' has been loaded (success)')


# creating a connection pool
elon.loop.run_until_complete(get_pool(elon))
if elon.debug:
    print('ELON TEST IS RUNNING!')
    elon.run(os.environ.get('ELON_TEST_TOKEN'))
else:
    elon.run(os.environ.get('MIA_TOKEN'))