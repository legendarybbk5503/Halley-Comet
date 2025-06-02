import discord
from discord.ext import commands
from config import Config
import logging
from cogs.auto import Auto

class MyBot(commands.Bot):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
        self.__cog_list = [
            "basiccommand",
            "music",
            #"errorhandling",
            "auto"
        ]   
        self.__listener_list = [
            "event"
        ]
    
    async def setup_hook(self):
        length = len(self.__cog_list)
        print("cogs:")
        for i, cog in enumerate(self.__cog_list, start = 1):
            await self.load_extension(f"cogs.{cog}")
            print(f"({i}/{length}) loaded {cog}")
        print("listeners:")
        for i, listener in enumerate(self.__listener_list, start = 1):
            await self.load_extension(f"listeners.{listener}")
            print(f"({i}/{length}) loaded {listener}")

        await Auto(self).removeInactiveAudio()
    
    async def on_ready(self):        
        slash = await self.tree.sync()
        print(f"Bot Name: {self.user}")
        print(f"Loaded {len(slash)} slash commands")

def main():
    config = Config("comet")
    prefix = config.prefix
    token = config.token
    
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True

    bot = MyBot(
        command_prefix = prefix,
        intents = intents
    )
    bot.run(token, log_level=logging.INFO, root_logger=True)

if __name__ == "__main__":
    main()