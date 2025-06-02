import discord
from discord.ext import commands, tasks
from discord import Forbidden
from datetime import datetime

class Event(commands.Cog):
    def __init__(self, bot):
        self.__bot = bot
        self.hack_dict = {}
        self.hack_message = []
    
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
        if (("everyone" in message.content or "here" in message.content )and "http" in message.content):
            print("WARNING:", message.author, "might be hacked")
            self.hack_message.append(message)
            if message.author in self.hack_dict:
                self.hack_dict[message.author] += 1
            else:
                self.hack_dict[message.author] = 1
            if self.hack_dict[message.author] > 3:
                await self.deletemessage(message.author)
                return
        for message in self.hack_message:
            if  1 < datetime.now().minute - message.created_at.minute > -2:
                self.hack_message.remove(message)
        for author in self.hack_dict:
            exist = True
            for message in self.hack_message:
                if message.author == author:
                    exist = True
                    break
            if not exist:
                self.hack_dict.pop(author)
            
async def setup(bot):
    await bot.add_cog(Event(bot))