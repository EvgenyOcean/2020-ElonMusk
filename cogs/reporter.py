import os
import discord
import logging
import datetime
import pytz
import asyncio
from discord.ext import commands, tasks
from db import operations
from utils import get_msk_time, ChannelsMixin, get_final_string


logger = logging.getLogger(__name__)
formatter = logging.Formatter(r'%(asctime)s:%(levelname)s:%(message)s')
handler = logging.FileHandler(filename='./logs/reporter.logs')
handler.setFormatter(formatter)
logger.addHandler(handler)


class Reporter(commands.Cog, ChannelsMixin):
    def __init__(self, elon):
        self.elon = elon
        self.elon.loop.create_task(self.fixes_cycling())
        self.elon.loop.create_task(self.schedule_daily_report())
        self.elon.loop.create_task(self.schedule_weekly_report())

    @tasks.loop(hours=24)
    async def daily_report(self):
        hall = self.hall_channel
        records = await operations.fetch_daily_workers(self.elon.pool)

        if not records:
            await hall.send(f'Nobody worked today, are u guys still alive? :sunglasses:') 

        today = get_msk_time()
        message = f":sunglasses: ** Another productive day is passing by [{today.strftime('%d-%m-%Y')}] ** :sunglasses: \n\n"
        place = 0
        for record in records:
            place += 1
            total_seconds = int(record.get('duration'))
            username = record.get('username')
            hours = total_seconds // 3600
            minutes = (total_seconds // 60) % 60
            if place == 1:
                message += f':trophy: {username} → ** |{hours:02d} : {minutes:02d}| ** \n'
            elif place == 2:
                message += f':second_place: {username} → ** |{hours:02d} : {minutes:02d}| ** \n'
            elif place == 3:
                message += f':third_place: {username} → ** |{hours:02d} : {minutes:02d}| ** \n'
            else:
                message += f'{username} → ** |{hours:02d} : {minutes:02d}| ** \n'

        message += f'``` ```'
        await hall.send(message)
            
    @tasks.loop(hours=168)
    async def weekly_report(self):
        today = get_msk_time()
        hall = self.hall_channel
        week_num = today.isocalendar()[1]
        records = await operations.fetch_week_workers(self.elon.pool, week_num)
        message = f'''            
        :sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles:\
        \r\n:sparkles:** Heroes Of The Week ** :sparkles:\
        \r\n:sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles:\r
        '''

        if not records:
            await hall.send(f'Nobody worked this week. Are u ahuel tam? :sunglasses:')

        if not self.elon.debug:
            try:
                await self.manage_hero_role(records[:3])
            except Exception as err:
                logger.exception(err)
            
        # nicely printing leaders
        place = 0
        for record in records:
            place += 1
            username = record.get('username')
            total_seconds = int(record.get('duration'))
            hours = total_seconds // 3600
            minutes = (total_seconds // 60) % 60
            if place < 3:
                message += f'\r\n:man_superhero: {username} → ** |{hours:02d} : {minutes:02d}| **'
            elif place == 3:
                message += f'\r\n:man_superhero: {username} → ** |{hours:02d} : {minutes:02d}| **'
                message += f'''            
                \r\n:sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles:\
                \r\n:sparkles:** Heroes Of The Week ** :sparkles:\
                \r\n:sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles::sparkles:
                '''
            else:
                message += f'\r\n {username} → ** |{hours:02d} : {minutes:02d}| **'

        await hall.send(message)

    @commands.command()
    async def file(self, ctx, *, member : discord.Member):
        '''
        Return number of hours a member worked this week.
        '''
        record = await operations.user_week(self.elon.pool, member)
        # meaning the member never worked this week
        if not record:
            await ctx.send(f'{member.display_name} is chillin :sunglasses:')
        else:
            total_seconds = int(record.get('duration'))
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
        Only at 11:59PM
        '''
        await self.elon.wait_until_ready()
        # I need to start running daily_report everyday at 11:59PM
        # But first time it should aslo run at 11:59PM
        # This method only runs once! But we can reconfigure to check if 
        # something went wrong and if we need to rerun daily_report
        dt_msk = get_msk_time()

        if self.elon.debug:
            # start ASAP *almost
            td = datetime.timedelta(seconds=3)
            dt_run_time = dt_msk + td
        else:
            # start at 11:59PM
            dt_run_time = dt_msk.replace(hour=23, minute=59, second=50)

        # getting the amount of seconds between them
        td = dt_run_time - dt_msk
        ts = td.total_seconds()
        print(f'Waiting for daily report, {ts} seconds left')

        if ts < 0:
            # need to reschedule or whatever
            print('We can\'t run the task in the past!')
            return
        
        # wait some amount of seconds until it's 11:59PM
        await asyncio.sleep(ts)
        # once it's 11:59PM start loop task
        self.daily_report.start()

    async def schedule_weekly_report(self):
        '''
        To properly start the loop with weekly reports 
        Only sundays 11:59PM
        '''
        await self.elon.wait_until_ready()
        # I need to start running weekly_reports on sundays at 11:59PM
        # But first time it should aslo run on sunday at 11:59PM
        # This method only runs once! But we can reconfigure to check if 
        # something went wrong and if we need to rerun weekly_report
        dt_msk = get_msk_time()

        if self.elon.debug:
            # start ASAP *almost
            td = datetime.timedelta(seconds=5)
            dt_run_time = dt_msk + td
        else:
            # start at 11:59PM
            dt_run_time = dt_msk.replace(hour=23, minute=59, second=55)
            # how many days until sunday
            days_to_wait = 7 - dt_run_time.isoweekday()
            if days_to_wait:
                td = datetime.timedelta(days=days_to_wait)
                dt_run_time += td

        # getting the amount of seconds between them
        td = dt_run_time - dt_msk
        ts = td.total_seconds()
        print(f'Waiting for weekly report: {ts} seconds left')

        if ts < 0:
            # need to reschedule or whatever
            print('We can\'t run the task in the past!')
            return
        
        # wait some amount of seconds until it's 11:59PM
        await asyncio.sleep(ts)
        # once it's 11:59PM start loop task
        self.weekly_report.start()

    async def manage_hero_role(self, records):
        '''
        Deletes previous heros and adds new ones
        '''
        guild = self.main_guild
        hero_role = guild.get_role(int(os.environ.get('HERO_ROLE_ID')))

        # deleting previous ones
        for member in hero_role.members:
            try: # fixed, can be deleted later on
                await member.remove_roles(hero_role)
            except Exception as err:
                logger.exception('Error while removing a hero role')

        # adding new ones
        for record in records:
            user = guild.get_member(int(record.get('owner')))
            # user may leave the guild
            if (user):
                await user.add_roles(hero_role)

    async def fixes_cycling(self):
        # 1. get everyone's id who's currently in working_session
        await self.elon.wait_until_ready()
        current_members = self.focus_channel.members
        cm_ids = set([member.id for member in current_members])
        # 2. get every working_session where date_finished IS NULL
        records = await operations.fetch_unfinished_sessions(self.elon.pool)
        records_ids = set([int(record.get('owner')) for record in records])
        # 3. find the differences 
        in_db_not_in_focus = records_ids - cm_ids
        in_focus_not_in_db = cm_ids - records_ids

        # if in db => update date_finished and send message to the briefing channel
        if in_db_not_in_focus:
            records = await operations.finish_sessions(self.elon.pool, in_db_not_in_focus)
            for record in records:
                username = record.get('username')
                duration = int(record.get('duration'))
                if duration < 60:
                    await self.briefing_channel.send(f'Dude, **{username}** worked for {duration} seconds! That is sick!')
                else:
                    final_str = get_final_string(duration)
                    await self.briefing_channel.send(f'Hey, **{username}** you was productive for __{final_str}__! Hope to see ya soon again!')
            
        # if in focus => add new entry to working_session and send message to the briefing channel
        if in_focus_not_in_db:
            guild = self.main_guild
            members = [guild.get_member(id) for id in in_focus_not_in_db]
            await operations.execute_focus(self.elon.pool, members=members)
            for member in members:
                await self.briefing_channel.send(f'Guys, **{member.display_name}** has just entered the working mode! Try to catch up!')


def setup(elon):
    elon.add_cog(Reporter(elon))