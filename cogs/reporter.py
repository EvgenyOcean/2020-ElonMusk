import discord
from discord.ext import commands, tasks
from db import operations
from utils import get_msk_time, ChannelsMixin

class Reporter(commands.Cog, ChannelsMixin):
    def __init__(self, elon):
        self.elon = elon
        self.minute_report.start() # add starter function once in production

    @tasks.loop(minutes=5) # change to the daily_report once in production
    async def minute_report(self):
        '''
        Fetches all the users who worked today
        '''
        await self.elon.wait_until_ready()
        today = get_msk_time()
        hall = self.hall_channel
        command = '''
            SELECT username, duration FROM working_session 
            LEFT JOIN users ON working_session.owner = users.id
            WHERE working_session.date_added = $1;
        '''
        records = await operations.fetch(self.elon.pool, command, today)
    
        if not records:
            await hall.send(f'Nobody has wokred just yet. Everybody is chillin :sunglasses:')
        
        else:
            day_workers = {}
            message = ''
            for r in records:
                # idk discord allows same usernames, cuz it uses id also
                # maybe it's better to store username#id in the db to avoid duplicates
                owner = r.get('username')
                duration = r.get('duration')
                if owner in day_workers:
                    day_workers[owner] += duration
                else:
                    day_workers.setdefault(owner, duration)

            for user in day_workers:
                total_seconds = int(day_workers[user])
                hours = total_seconds // 3600
                minutes = (total_seconds // 60) % 60
                message += f':man_technologist: {user} → ** |{hours:02d} : {minutes:02d}| ** \n'

            await hall.send(message)


def setup(elon):
    elon.add_cog(Reporter(elon))