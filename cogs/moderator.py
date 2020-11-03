import discord
from discord.ext import commands
from utils import ChannelsMixin, get_msk_time

# TODO: group the checks into a mixin or whatever
def is_it_mif(ctx):
    for role in ctx.author.roles:
        if role.name == 'MIF':
            return True


class Moderator(commands.Cog, ChannelsMixin):
    def __init__(self, elon):
        self.elon = elon

    @commands.command(name="clean_up")
    @commands.check(is_it_mif)
    async def clean_up(self, ctx, num=None):
        if not num:
            await ctx.send('Instructions are not clear!')
        else:
            await ctx.channel.purge(limit=int(num)+1)


def setup(elon):
    elon.add_cog(Moderator(elon))