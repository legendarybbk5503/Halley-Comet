import discord
from discord.ext import commands
import asyncio
import datetime
import os
from objects.music_objects import GuildPlayer, MusicDatabase

class Music(commands.Cog):
    
    def __init__(self, bot):
        self.__bot = bot
        self.__players = {}
            
    async def __userInVoiceChannel(self, ctx, msg = True) -> bool:
        voice = ctx.author.voice
        if voice is None:
            if msg is True:
                await ctx.send("You are not in any voice channel")
            return False
        return True
    
    async def __botInVoiceChannel(self, ctx, msg = True) -> bool:
        voice_client = ctx.voice_client
        if voice_client is None:
            if msg is True:
                await ctx.send("I am not in any voice channel")
            return False
        return True
    
    @commands.command()
    async def join(self, ctx):
        if await self.__userInVoiceChannel(ctx) is False: return
        await ctx.author.voice.channel.connect()
        await ctx.send("Joined your voice channel")

        if self.__players.get(ctx.guild.id, None) is None:
            self.__players[ctx.guild.id] = GuildPlayer(ctx)
    
    @commands.command()
    async def leave(self, ctx):
        if await self.__botInVoiceChannel(ctx) is False: return
        await ctx.voice_client.disconnect()
        await ctx.send("Left your voice channel")
    
    @commands.command()
    async def play(self, ctx, *messages: str): ##enable space in command        
        if await self.__userInVoiceChannel(ctx) is False: return
        if await self.__botInVoiceChannel(ctx, False) is False:
            await self.join(ctx)
        
        player: GuildPlayer = self.__players.get(ctx.guild.id, None)
        await player.play(ctx, messages)

    #REWORK
    @commands.command()
    async def repeat(self, ctx):
        player: GuildPlayer = self.__players.get(ctx.guild.id, None)
        filename, music = player.nowplaying_music
        if os.path.isfile(filename) is False:
            await player.dlmusic_one(ctx, music.url)
        
        volume = player.volume / 100
        source = discord.FFmpegPCMAudio(filename)
        source = discord.PCMVolumeTransformer(source, volume=volume)
        
        def after(error):
            source.cleanup()
            if error is not None:
                coro = ctx.send(error)
                asyncio.run_coroutine_threadsafe(coro, self.__bot.loop)
            coro = player.playNext
            asyncio.run_coroutine_threadsafe(coro, self.__bot.loop)
            
        voice_client = ctx.voice_client
        voice_client.stop()
        player.nowplaying_start_time = datetime.datetime.now()
        voice_client.play(source, after=after)
        return await ctx.send("repeated")

    @commands.command()
    async def previous(self, ctx):
        player: GuildPlayer = self.__players.get(ctx.guild.id, None)
        if player is None:
            return await ctx.send("not playing anything")
        if len(player.history) == 0:
            return await ctx.send("playing history is empty")
        player.queue.insert(0, player.nowplaying_music)
        player.queue.insert(0, player.history.pop(0))
        await self.skip(ctx, False)
        player.history.pop(0)
        return await ctx.send("playing previous")
    
    @commands.command()
    async def pause(self, ctx):
        voice_client = ctx.voice_client
        if voice_client is None:
            return await ctx.send("not playing anything")
        if voice_client.is_playing():
            voice_client.pause()
            await ctx.send("paused")
        elif voice_client.is_paused():
            await ctx.send("it was already paused")
        else:
            await ctx.send("not playing anything")
    
    @commands.command()
    async def resume(self, ctx):
        voice_client = ctx.voice_client
        if voice_client is None:
            return await ctx.send("not playing anything")
        if voice_client.is_playing():
            await ctx.send("it is already playing")
        elif voice_client.is_paused():
            voice_client.resume()
            await ctx.send("resumed")
        else:
            await ctx.send("I ain't playing anything")
    
    @commands.command()
    async def stop(self, ctx):
        voice_client = ctx.voice_client
        if voice_client is None:
            return await ctx.send("not playing anything")
        voice_client.stop()
        player: GuildPlayer = self.__players.get(ctx.guild.id, None)
        player.queue.clear()
        await ctx.send("stopped, cleared queue")
    
    @commands.command()
    async def skip(self, ctx, msg = True):
        player: GuildPlayer = self.__players.get(ctx.guild.id, None)
        if player is None:
            if msg: return await ctx.send("not playing anything")
        if player.nowplaying_music is None:
            if msg: return await ctx.send("not playing anything")
        voice_client = ctx.voice_client
        voice_client.stop()
        if msg: return await ctx.send("skipped")
    
    @commands.command()
    async def queue(self, ctx):
        player: GuildPlayer = self.__players.get(ctx.guild.id, None)
        if player is None:
            return await ctx.send("the queue is empty")
        queue = player.queue
        if len(queue) == 0:
            nowplaying = await player.nowplaying()
            if nowplaying is None:
                return await ctx.send("the queue is empty")
            else:
                return await ctx.send(nowplaying + "\n" + "the queue is empty")
        
        output = "".join([f"    {i}: `{x[1].title}`\n" for i, x in enumerate(queue, start=1)])
        msg = await player.nowplaying() + "\n" + "Queue:" + "\n" + output
        
        await ctx.send(msg)
    
    @commands.command()
    async def remove(self, ctx, num):
        player: GuildPlayer = self.__players.get(ctx.guild.id, None)
        if player is None:
            return await ctx.send("the queue is empty")
        queue = player.queue
        if num == "all":
            queue.clear()
            return await ctx.send("removed all")
        if num.isdigit():
            if int(num) in range(1, len(queue)+1):
                music = queue.pop(int(num)-1)[1]
                return await ctx.send(f"removed {music.title}")
            else:
                return await ctx.send("invalid no.")
        else:
            return await ctx.send("invalid no.")
    
    @commands.command()
    async def history(self, ctx):
        player: GuildPlayer = self.__players.get(ctx.guild.id, None)
        if player is None:
            return await ctx.send("the playlist history is empty")
        history = player.history
        if len(history) == 0:
            nowplaying = await player.nowplaying()
            if nowplaying is None:
                return await ctx.send("the queue history is empty")
            return await ctx.send(nowplaying + "\n" + "the playlist history is empty")
        
        output = "".join([f"    -{i}: `{x[1].title}`\n" for i, x in enumerate(history, start=1)])
        np = await player.nowplaying()
        np = "" if np is None else np
        msg = np + "\n" + "History:" + "\n" + output
        
        await ctx.send(msg)
        
    @commands.command(aliases=["np"])
    async def nowplaying(self, ctx, msg = True) -> str:
        player: GuildPlayer = self.__players.get(ctx.guild.id, None)       
        if player is None:
            if msg: await ctx.send("not playing anything")
            return None

        np = await player.nowplaying()
        if np is None:
            return await ctx.send("not playing anything")
        else:
            return await ctx.send(msg)
        
    @commands.command()
    async def volume(self, ctx, *args):
        player: GuildPlayer = self.__players[ctx.guild.id]
        volume = player.volume
        if args == ():
            return await ctx.send(f"volume: `{volume}%`")
        else:
            new_volume = args[0]
            if new_volume.isdigit():
                if int(new_volume) in range(101):
                    player.volume = int(new_volume)
                    ctx.voice_client.source.volume = int(new_volume) / 100
                    return await ctx.send(f"volume has been changed from `{volume}%` to `{new_volume}%`")
                else:
                    return await ctx.send(f"volume has to be an integer between 0 and 100 inclusively")
            else:
                return await ctx.send(f"volume has to be an integer between 0 and 100 inclusively")
    
async def setup(bot):
    await bot.add_cog(Music(bot))