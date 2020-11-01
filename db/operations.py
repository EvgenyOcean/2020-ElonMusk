import logging
# from asyncpg.exceptions import PostgresSyntaxError # if you wanna go safe

# logger = logging.getLogger(__name__)
# formatter = logging.Formatter(r'%(asctime)s:%(levelname)s:%(message)s')
# handler = logging.FileHandler(filename='./logs/operations.logs')
# handler.setFormatter(formatter)
# logger.addHandler(handler)


async def fetch(pool, command, *args):
    async with pool.acquire() as connection:
        async with connection.transaction():
            records = await connection.fetch(command, *args)
    return records


async def executemany(pool, payload):
    async with pool.acquire() as connection:
        async with connection.transaction():
            for query in payload:
                await connection.execute(query[0], *query[1])
    return