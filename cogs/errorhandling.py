import discord
from discord.ext import commands

class ErrorHandling(commands.Cog):
    
    def __init__(self, bot):
        self.__bot = bot
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if hasattr(ctx.command, "on_error"): return
        
        ignored = (
            commands.CommandNotFound,
        )
        if isinstance(error, ignored): return
        
        cog = ctx.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return
            
        await ctx.send(error)
        print(error)
    
async def setup(bot):
    await bot.add_cog(ErrorHandling(bot))