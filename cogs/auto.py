import os
import time
import datetime
from discord.ext import commands, tasks

utc = datetime.timezone.utc

# If no tzinfo is given then UTC is assumed.
repeated_time = datetime.time(hour=0, minute=0, tzinfo=utc)

class Auto(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot
        self.removeInactiveAudio.start()

    def cog_unload(self):
        self.removeInactiveAudio.cancel()
    
    @tasks.loop(time=repeated_time)
    async def removeInactiveAudio(self):
        def list_files(startpath):
            alist = []
            for root, dirs, files in os.walk(startpath):
                for file in files:
                    alist.append(os.path.join(root, file))
            return alist
        for file in list_files('music/'):
            if time.time() - os.path.getatime(file) >= 86400:
                os.remove(file)
    
async def setup(bot):
    await bot.add_cog(Auto(bot))
