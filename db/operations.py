import logging
# from asyncpg.exceptions import PostgresSyntaxError # if you wanna go safe

# logger = logging.getLogger(__name__)
# formatter = logging.Formatter(r'%(asctime)s:%(levelname)s:%(message)s')
# handler = logging.FileHandler(filename='./logs/operations.logs')
# handler.setFormatter(formatter)
# logger.addHandler(handler)



async def execute_focus(pool, member):
    '''
    User enters the focus channel, make sure that:
    1. Check if related tables exist for the user
    2. Create new working_session for that dude
    3. I mean, it kinda watches usernames, not ideally, but it'll do for now
    '''
    query = 'SELECT create_tables($1, $2);'
    async with pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(query, member.id, member.display_name)


async def fetch_unfocus(pool, member):
    '''
    Return number of seconds user worked for this session
    '''
    query = '''
        WITH user_entry AS (
            UPDATE working_session SET date_finished=timezone('europe/moscow', now())
            WHERE owner=$1 AND date_finished IS NULL
            returning *
        )
        SELECT EXTRACT(epoch FROM(date_finished - date_started)) as duration, owner FROM user_entry;
    '''
    async with pool.acquire() as connection:
        async with connection.transaction():
            result = await connection.fetch(query, member.id)
    return result


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