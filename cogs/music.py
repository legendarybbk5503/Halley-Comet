import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import datetime
import os
from objects.music_objects import GuildPlayer, MusicDatabase
import json


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
    
    @commands.hybrid_command(name = "join", description = "Call the bot to join your voice channel")
    async def join(self, ctx):
        if await self.__userInVoiceChannel(ctx) is False: return
        await ctx.author.voice.channel.connect()
        await ctx.send("Joined your voice channel")

        if self.__players.get(ctx.guild.id, None) is None:
            self.__players[ctx.guild.id] = GuildPlayer(ctx)
    
    @commands.hybrid_command(name = "leave", description = "Call the bot to leave your voice channel")
    async def leave(self, ctx):
        if await self.__botInVoiceChannel(ctx) is False: return
        await ctx.voice_client.disconnect()
        await ctx.send("Left your voice channel")
    
    @commands.hybrid_command(name = "play", description = "Play a song with the given url or search term")
    @app_commands.describe(messages = "The url or search term of the song")
    async def play(self, ctx, messages: str): ##enable space in command        
        if await self.__userInVoiceChannel(ctx) is False: 
            return
        if await self.__botInVoiceChannel(ctx, False) is False:
            await self.join(ctx)
        
        player: GuildPlayer = self.__players.get(ctx.guild.id, None)
        await player.play(ctx, messages)


    @commands.hybrid_command(name = "repeat", description = "Repeat the current song")
    async def repeat(self, ctx):
        player: GuildPlayer = self.__players.get(ctx.guild.id, None)
        if player is None:
            return await ctx.send("not playing anything")
        if player.nowplaying is None:
            return await ctx.send("not playing anything")
        
        await player.repeat(ctx)
        return await ctx.send("repeated")

    ##@commands.hybrid_command(name = "previous", description = "Play the previous song")
    ##async def previous(self, ctx):
    ##    player: GuildPlayer = self.__players.get(ctx.guild.id, None)
    ##    if player is None:
    ##        return await ctx.send("not playing anything")
    ##    if len(player.history) == 0:
    ##        return await ctx.send("playing history is empty")
    ##    player.previous(ctx)
    ##    return await ctx.send("playing previous")
    
    @commands.hybrid_command(name = "pause", description = "pause the playing song")
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
    
    @commands.hybrid_command(name = "resume", description = "resume the paused song")
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
    
    @commands.hybrid_command(name = "stop", description = "Stop the playing song")
    async def stop(self, ctx):
        voice_client = ctx.voice_client
        if voice_client is None:
            return await ctx.send("not playing anything")
        voice_client.stop()
        player: GuildPlayer = self.__players.get(ctx.guild.id, None)
        player.queue.clear()
        await ctx.send("stopped, cleared queue")
    
    @commands.hybrid_command(name = "skip", description = "Skip the playing song")
    async def skip(self, ctx):
        player: GuildPlayer = self.__players.get(ctx.guild.id, None)
        if player is None:
            return await ctx.send("not playing anything")
        if player.nowplaying_music is None:
            return await ctx.send("not playing anything")
        voice_client = ctx.voice_client
        voice_client.stop()
        return await ctx.send("skipped")
    
    @commands.hybrid_command(name = "queue", description = "Show the queue")
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
    
    @commands.hybrid_command(name = "remove", description = "remove the song from the queue by using the queue number")
    @app_commands.describe(num = "The queue number")
    async def remove(self, ctx, num: str):
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
                return await ctx.send(f"removed `{music.title}`")
            else:
                return await ctx.send("invalid no.")
        else:
            return await ctx.send("invalid no.")
    
    @commands.hybrid_command(name = "history", description = "show playlist history")
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
        
    ##@app_commands.command(name = "nowplaying", description = "show the nowplaying song")
    ##async def nowplaying(self, ctx, msg = True) -> str:
    ##    player: GuildPlayer = self.__players.get(ctx.guild.id, None)       
    ##    if player is None:
    ##        if msg: 
    ##            await ctx.send("not playing anything")
    ##        return None
    ##
    ##    np = await player.nowplaying()
    ##    if np is None:
    ##        return await ctx.send("not playing anything")
    ##    else:
    ##        return await ctx.send(np)
        
    @commands.hybrid_command(name = "volume", description = "show the nowplaying song")
    @app_commands.describe(percentage = "percentage volume (0-100)")
    async def volume(self, ctx, percentage: str):
        player: GuildPlayer = self.__players.get(ctx.guild.id, None)
        if player is None:
            return await ctx.send("not playing anything")
        volume = player.volume
        if  percentage == ():
            return await ctx.send(f"volume: `{volume}%`")
        else:
            new_volume =  percentage
            if new_volume.isdigit():
                if int(new_volume) in range(101):
                    player.volume = int(new_volume)
                    ctx.voice_client.source.volume = int(new_volume) / 100
                    return await ctx.send(f"volume has been changed from `{volume}%` to `{new_volume}%`")
                else:
                    return await ctx.send(f"volume has to be an integer between 0 and 100 inclusively")
            else:
                return await ctx.send(f"volume has to be an integer between 0 and 100 inclusively")
    
    ##@commands.hybrid_command(name = "save", description = "save your playlist")
    ##@app_commands.describe(playlistname = "name of the playlist")
    ##async def save(self, ctx, playlistname:str = None):
    ##    name = playlistname
    ##    player: GuildPlayer = self.__players.get(ctx.guild.id, None)
    ##    if player is None:
    ##        return await ctx.send("not playing anything")
    ##    if name is None:
    ##        return await ctx.send("please provide a name for the playlist")
    ##    #get urls from np + queue
    ##    np = player.nowplaying_music[1]
    ##    np = (np.title, np.url)
    ##    if len(player.queue) > 0:
    ##        queue = [(x[1].title, x[1].url) for x in player.queue]
    ##        queue.insert(0, np)
    ##        urls = queue
    ##    else:
    ##        urls = [np]
    ##    
    ##    #read file
    ##    try:
    ##        with open(rf"playlist\{ctx.author.id}.json", 'r') as f:
    ##            d = json.load(f)
    ##    except:
    ##        d = {}
    ##    
    ##    #return if exists
    ##    if name in d.keys():
    ##        return await ctx.send(f"playlist {name} already exists")
    ##    
    ##    #else create playlist
    ##    with open(f"playlist/{ctx.author.id}.json", 'r') as f:
    ##        d[name] = urls
    ##        json.dump(d, f, indent=4)
    ##        return await ctx.send(f"saved playlist as {name}")
        
    ##@commands.hybrid_command(name = "playlist", description = "add the playlist to queue if specified, list all playlists if playlistname is None")
    ##@app_commands.describe(playlistname = "name of the playlist")
    ##async def playlist(self, ctx, playlistname:str = None):
    ##    """
    ##    add the playlist to queue if specified
    ##    list all playlists if playlistname is None
    ##    """
    ##    with open(f"playlist\\{ctx.author.id}.json", 'r') as f:
    ##        d = json.load(f)
    ##    
    ##    name = playlistname
    ##    if name is None:
    ##        output = []
    ##        for name, musics in d.items(): #music = (title, url)
    ##            titles = [f"    {i}: {music[0]}" for i, music in enumerate(musics, start=1)]
    ##            output.append(f"{name}:\n{"\n".join(titles)}")
    ##        return await ctx.send("\n".join(output))
    ##    #else
    ##    if name not in d.keys():
    ##        return await ctx.send(f"cannot find the playlist `{name}`")
    ##    #else
    ##    urls = [x[1] for x in d[name]]
    ##    if await self.__userInVoiceChannel(ctx) is False: return
    ##    if await self.__botInVoiceChannel(ctx, False) is False:
    ##        await self.join(ctx)
    ##    
    ##    player: GuildPlayer = self.__players.get(ctx.guild.id, None)
    ##    await player.dlmusic_many(ctx, urls)
    ##    await ctx.send(f"added playlist `{name}` into queue")
    ##    
    ##    if player.nowplaying_music is None:
    ##        await player.playerLoop(ctx)
        
    
async def setup(bot):
    await bot.add_cog(Music(bot))