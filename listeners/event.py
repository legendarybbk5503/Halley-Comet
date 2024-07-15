import discord
from discord.ext import commands
from discord import Forbidden

class Event(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot
        self.hack_dict = {}
        self.hack_message = []

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.__bot.user:
            return
        if message.content.startswith("hello"):
            await message.channel.send("world")
    
    async def deletemessage(self,author):
        for msg in self.hack_message:
            if msg.author == author:
                print(msg)
                try:
                    await msg.delete()
                except Forbidden:
                    print("Could not delete message due to insufficient permissions.")
        self.hack_dict.pop(author)
        self.hack_message = [msg for msg in self.hack_message if msg.author != author]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.__bot.user:
            return
        if (message.mention_everyone and "http" in message.content):
            print("WARNING:", message.author, "might be hacked")
            self.hack_message.append(message)
            if message.author in self.hack_dict:
                self.hack_dict[message.author] += 1
            else:
                self.hack_dict[message.author] = 1
            if self.hack_dict[message.author] > 3:
                await self.deletemessage(message.author)
            
async def setup(bot):
    await bot.add_cog(Event(bot))