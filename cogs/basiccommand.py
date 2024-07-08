import discord
from discord.ext import commands

class BasicCommand(commands.Cog):
    
    def __init__(self, bot):
        self.__bot = bot

    @commands.command()
    async def ping(self, ctx):
        await ctx.send(f"{round(self.__bot.latency*1000)}ms")
    
async def setup(bot):
    await bot.add_cog(BasicCommand(bot))