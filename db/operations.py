import logging

logger = logging.getLogger(__name__)
formatter = logging.Formatter(r'%(asctime)s:%(levelname)s:%(message)s')
handler = logging.FileHandler(filename='./logs/operations.logs')
handler.setFormatter(formatter)
logger.addHandler(handler)


async def fetch(pool, command, *args):
    async with pool.acquire() as connection:
        async with connection.transaction():
            records = await connection.fetch(command, *args)
    return records


async def execute(pool, command, **kwargs):
    async with pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(command, *args)
    return