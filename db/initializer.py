import asyncpg
import os

async def get_pool(elon):
    # credentials = {"user": "postgres", "password": "postgres", "database": "elon", "host": "192.168.99.101"}
    # this will create initial 10 connections to the database
    pool = await asyncpg.create_pool(dns=os.environ.get('DATABASE_URL'))
    elon.pool = pool