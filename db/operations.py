import logging
# from asyncpg.exceptions import PostgresSyntaxError # if you wanna go safe

# logger = logging.getLogger(__name__)
# formatter = logging.Formatter(r'%(asctime)s:%(levelname)s:%(message)s')
# handler = logging.FileHandler(filename='./logs/operations.logs')
# handler.setFormatter(formatter)
# logger.addHandler(handler)


async def execute_focus(pool, member=None, members=None):
    '''
    User enters the focus channel, make sure that:
    1. Check if related tables exist for the user
    2. Create new working_session for that dude
    3. I mean, it kinda watches usernames, not ideally, but it'll do for now
    '''
    query = 'SELECT create_tables($1, $2);'
    async with pool.acquire() as connection:
        async with connection.transaction():
            if members:
                for member in members:
                    # for loop is fine, cuz not that many members can jump into focus channel
                    # during 5 seconds cycling...
                    await connection.execute(query, member.id, str(member))
            else:
                await connection.execute(query, member.id, str(member))


async def fetch_unfocus(pool, member):
    '''
    Return number of seconds a user worked for this session
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


async def less_than_minute(pool, member):
    '''
    Sessions less than a minute shouldn't be a thing
    To avoid spamming, I'll leave it here for now
    '''
    query = '''
        DELETE FROM working_session 
        WHERE EXTRACT(epoch FROM(date_finished - date_started)) < 60
            AND owner=$1
    '''
    async with pool.acquire() as connection:
        async with connection.transaction():
            result = await connection.fetch(query, member.id)


async def fetch_week_workers(pool, week_num):
    '''
    Fetches users who worked this week
    Removes last week entries due to heroku 10000 rows limit
    Sorry bruh
    '''
    query1 = '''
        SELECT owner, username, SUM(ROUND(EXTRACT(epoch FROM(date_finished - date_started)))) as duration FROM users
        LEFT JOIN working_session ON working_session.owner = users.discord_id
        WHERE DATE_PART('week', working_session.date_started)=$1 AND 
                    date_finished IS NOT NULL
        GROUP BY (users.username, working_session.owner)
        ORDER BY duration DESC;
    '''
    
    query2 = '''
        WITH week_sessions AS (
        DELETE FROM working_session
        WHERE DATE_PART('week', working_session.date_started) = $1 AND 
                date_finished IS NOT NULL
        returning *
        )
        UPDATE timings SET total=total + ROUND(EXTRACT(epoch FROM(date_finished - date_started)))
        FROM week_sessions
        WHERE week_sessions.owner=timings.discord_id;
    '''
    async with pool.acquire() as connection:
        async with connection.transaction():
            records = await connection.fetch(query1, week_num)
            await connection.execute(query2, week_num)
    return records


async def fetch_daily_workers(pool):
    query = '''
        SELECT username, owner, SUM(ROUND(EXTRACT(epoch FROM (date_finished - date_started)))) as duration FROM working_session 
        LEFT JOIN users ON working_session.owner=users.discord_id
        WHERE date_started::date=timezone('europe/moscow', now())::date AND date_finished IS NOT NULL
        GROUP BY (username, owner)
        ORDER BY duration DESC;
    '''

    async with pool.acquire() as connection:
        async with connection.transaction():
            records = await connection.fetch(query)
    return records


async def fetch_unfinished_sessions(pool):
    query = '''
        SELECT * FROM working_session
        WHERE date_finished IS NULL;
    '''
    async with pool.acquire() as connection:
        async with connection.transaction():
            records = await connection.fetch(query)
    return records


async def finish_sessions(pool, in_db_not_in_focus):
    records = []
    query = '''
        WITH update_sessions AS (
        UPDATE working_session SET date_finished=timezone('europe/moscow', now())
        WHERE owner=$1 AND date_finished IS NULL
        returning *
        )
        SELECT owner, username, ROUND(EXTRACT(epoch FROM (date_finished - date_started))) as duration
        FROM update_sessions
        LEFT JOIN users ON update_sessions.owner=users.discord_id;
    '''
    async with pool.acquire() as connection:
        async with connection.transaction():
            for member_id in in_db_not_in_focus:
                # for loop is fine, cuz not that many people can potentially
                # quit during 5 seconds cycling process
                record = await connection.fetchrow(query, member_id)
                records.append(record)
    return records


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