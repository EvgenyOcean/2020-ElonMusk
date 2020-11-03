import discord
import os
import datetime
import asyncio
from discord.ext import commands,tasks
from utils import ChannelsMixin, get_msk_time


class Greeter(commands.Cog, ChannelsMixin):
    def __init__(self, elon):
        self.elon = elon
        self.elon.loop.create_task(self.schedule_hello_ping())

    @tasks.loop(hours=24)
    async def hello_ping(self):
        # get anonymous role
        if self.elon.debug:
            print('Debug is on, otherwise message would be sent!')
            return
        guild = self.elon.get_guild(int(os.environ.get('GUILD_ID')))
        anon_role = guild.get_role(int(os.environ.get('ANONYMOUS_ROLE_ID')))

        message = f':bell: {anon_role.mention}, как оно? Может быть сегодня походящий день, чтобы рассказать о себе? Давайте я покажу как это делается:'
        message += '```Всем привет, крутая группа :D Меня зовут Elon Musk, я изучаю JS по learn.javascript.ru. Хорошо знаю Python (если ты тоже его знаешь, го вместе запилим что-нибудь). Увлекаюсь вязанием и ракетостроением. Если ты тоже... впрочем вряд ли. ```'
        message += ':money_with_wings: Таким образом мне будет понятно, что вы не AI. И ребята смогут дать Вам новую роль "Verified Member" и будет понятно какими технологиями вы увлекаетесь. А это уже трамплин на Марс, ну или как минимум - возможность для дальнейшего общения :wink:'
        await self.hello_channel.send(message)

    async def schedule_hello_ping(self):
        '''
        Start hello_ping at 10AM
        '''
        await self.elon.wait_until_ready()
        dt_msk = get_msk_time()

        if self.elon.debug:
            # start ASAP *almost
            td = datetime.timedelta(seconds=3)
            dt_run_time = dt_msk + td
        else:
            # it may leave 1 day off, but it's okay
            td = datetime.timedelta(days=1)
            dt_run_time = dt_msk + td
            dt_run_time = dt_msk.replace(hour=10, minute=0, second=0)

        # getting the amount of seconds between them
        td = dt_run_time - dt_msk
        ts = td.total_seconds()
        print(f'Waiting for hello_ping, {ts} seconds left')

        if ts < 0:
            # need to reschedule or whatever
            print('We can\'t run the task in the past!')
            return
        
        # wait some amount of seconds until it's 10AM
        await asyncio.sleep(ts)
        self.hello_ping.start()


def setup(elon):
    elon.add_cog(Greeter(elon))