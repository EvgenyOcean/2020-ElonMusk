import discord
import logging
import datetime
import pytz
import asyncio
from discord.ext import commands, tasks
from db import operations
from utils import get_msk_time, ChannelsMixin


logger = logging.getLogger(__name__)
formatter = logging.Formatter(r'%(asctime)s:%(levelname)s:%(message)s')
handler = logging.FileHandler(filename='./logs/reporter.logs')
handler.setFormatter(formatter)
logger.addHandler(handler)


class Reporter(commands.Cog, ChannelsMixin):
    def __init__(self, elon):
        self.elon = elon
        self.elon.loop.create_task(self.schedule_daily_report())
        self.elon.loop.create_task(self.schedule_weekly_report())

    @tasks.loop(hours=24)
    async def daily_report(self):
        '''
        Fetches all the users who worked today
        '''
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
            message = f":sunglasses: ** Another productive day is passing by ** :sunglasses: \n\n"
            for r in records:
                owner = r.get('username')
                duration = r.get('duration')
                if owner in day_workers:
                    day_workers[owner] += duration
                else:
                    day_workers.setdefault(owner, duration)
            
            # sorting by number of worked seconds
            day_workers = {k: v for k, v in sorted(day_workers.items(), key=lambda item: item[1], reverse=True)}
            place = 0
            # nicely printing leaders
            for user in day_workers:
                place += 1
                total_seconds = int(day_workers[user])
                hours = total_seconds // 3600
                minutes = (total_seconds // 60) % 60
                if place == 1:
                    message += f':trophy: {user} → ** |{hours:02d} : {minutes:02d}| ** \n'
                elif place == 2:
                    message += f':second_place: {user} → ** |{hours:02d} : {minutes:02d}| ** \n'
                elif place == 3:
                    message += f':third_place: {user} → ** |{hours:02d} : {minutes:02d}| ** \n'
                else:
                    message += f'{user} → ** |{hours:02d} : {minutes:02d}| ** \n'

            await hall.send(message)

    @tasks.loop(hours=168)
    async def weekly_report(self):
        '''
        Fetches all the users who worked this week
        '''
        # getting ordinal week number of the year
        today = get_msk_time()
        week_num = today.isocalendar()[1]
        hall = self.hall_channel
        command = '''
            SELECT username, duration FROM working_session 
            LEFT JOIN users ON working_session.owner = users.id
            WHERE DATE_PART('week', working_session.date_added) = $1;
        '''
        records = await operations.fetch(self.elon.pool, command, week_num)
    
        if not records:
            await hall.send(f'Nobody worked this week. Are u ahuel tam? :sunglasses:')
        
        else:
            day_workers = {}
            message = f'''            
            :sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles:\
            \r\n:sparkles:** Heroes Of The Week ** :sparkles:\
            \r\n:sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles:\r
            '''
            for r in records:
                owner = r.get('username')
                duration = r.get('duration')
                if owner in day_workers:
                    day_workers[owner] += duration
                else:
                    day_workers.setdefault(owner, duration)
            
            # sorting by number of worked seconds
            day_workers = {k: v for k, v in sorted(day_workers.items(), key=lambda item: item[1], reverse=True)}
            # nicely printing leaders
            for user in day_workers:
                total_seconds = int(day_workers[user])
                hours = total_seconds // 3600
                minutes = (total_seconds // 60) % 60
                message += f'\r\n:man_superhero: {user} → ** |{hours:02d} : {minutes:02d}| **'

            message += f'''            
            \r\n:sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles:\
            \r\n:sparkles:** Heroes Of The Week ** :sparkles:\
            \r\n:sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles:\r\n
            '''
            await hall.send(message)

    @commands.command()
    async def file(self, ctx, member : discord.Member):
        '''
        Return number of hours a member worked this week.
        '''
        msk_time = get_msk_time()
        current_week = msk_time.isocalendar()[1]
        command = '''
            SELECT duration
            FROM working_session
            WHERE owner = $1 AND DATE_PART('week', date_added) = $2
        '''
        records = await operations.fetch(self.elon.pool, command, member.id, current_week)

        total_seconds = 0
        for record in records:
            total_seconds += int(record.get('duration'))
        
        # meaning the member never worked this week
        if not total_seconds:
            await ctx.send(f'{member.display_name} is chillin :sunglasses:')

        # counting number of hours and minutes the member worked this week
        else:
            hours = total_seconds // 3600
            minutes = (total_seconds // 60) % 60
            await ctx.send(f'{member.display_name} worked for ** |{hours:02d} : {minutes:02d}|** this week.')

    @file.error
    async def file_error(self, ctx, error):
        if isinstance(error, commands.errors.MemberNotFound):
            await ctx.send('Sorry pal, couldn\'t find that person :(')
        elif isinstance(error, commands.errors.MissingRequiredArgument): 
            await ctx.send('You need to specify username')
        else:
            logger.exception('Something wrong with file command:', error)

    async def schedule_daily_report(self):
        '''
        To properly start the loop with daily reports 
        Only at 23:59PM
        '''
        await self.elon.wait_until_ready()
        # I need to start running daily_report everyday at 23:59PM
        # But first time it should aslo run at 23:59PM
        # This method only runs once! But we can reconfigure to check if 
        # something went wrong and if we need to rerun daily_report
        dt_msk = get_msk_time()

        if self.elon.debug:
            # start ASAP *almost
            td = datetime.timedelta(seconds=3)
            dt_run_time = dt_msk + td
        else:
            # start at 23:59PM
            dt_run_time = dt_msk.replace(hour=23, minute=59, second=50)

        # getting the amount of seconds between them
        td = dt_run_time - dt_msk
        ts = td.total_seconds()
        print(f'Waiting for daily report, {ts} seconds') # Waiting for 4.317719 seconds

        if ts < 0:
            # need to reschedule or whatever
            print('We can\'t run the task in the past!')
            return
        
        # wait some amount of seconds until it's 23:59PM
        await asyncio.sleep(ts)
        # once it's 23:59PM start loop task
        self.daily_report.start()

    async def schedule_weekly_report(self):
        '''
        To properly start the loop with weekly reports 
        Only sundays 23:59PM
        '''
        await self.elon.wait_until_ready()
        # I need to start running weekly_reports on sundays at 23:59PM
        # But first time it should aslo run on sunday at 23:59PM
        # This method only runs once! But we can reconfigure to check if 
        # something went wrong and if we need to rerun weekly_report
        dt_msk = get_msk_time()

        if self.elon.debug:
            # start ASAP *almost
            td = datetime.timedelta(seconds=5)
            dt_run_time = dt_msk + td
        else:
            # start at 23:59PM
            dt_run_time = dt_msk.replace(hour=23, minute=59, second=55)
            # how many days until saturday
            days_to_wait = 7 - dt_run_time.isoweekday()
            if days_to_wait:
                td = datetime.timedelta(days=days_to_wait)
                dt_run_time += td

        # getting the amount of seconds between them
        td = dt_run_time - dt_msk
        ts = td.total_seconds()
        print(f'Waiting for weekly report: {ts} seconds left') # Waiting for 4.317719 seconds

        if ts < 0:
            # need to reschedule or whatever
            print('We can\'t run the task in the past!')
            return
        
        # wait some amount of seconds until it's 23:59PM
        await asyncio.sleep(ts)
        # once it's 23:59PM start loop task
        self.weekly_report.start()


def setup(elon):
    elon.add_cog(Reporter(elon))