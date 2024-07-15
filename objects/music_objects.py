import datetime
import asyncio
import os
import discord
import yt_dlp

from tools.datetime_formatting import DatetimeFormatting as DF
from tools.youtube_url_check import Check
from pytube import Playlist
from youtubesearchpython import VideosSearch


class MusicDatabase():
    
    def __init__(self, url: str, info: dict):
        self.url = url
        
        self.id = info.get("id", None)
        self.title = info.get("title", None)
        self.duration = info.get("duration", None)
        
class GuildPlayer():
    
    def __init__(self, ctx):
        self.__bot = ctx.bot
        self.__guild = ctx.guild
        #self.__channel = ctx.channel
        #self.__owner = ctx.author
        
        self.queue = []
        #[filename, MusicDatabase]
        self._addingToQueue = False
        self.history = []
        
        self.nowplaying_music = None #(str, MusicDatabase)
        self.nowplaying_start_time = None
        
        self.volume = 50
        
        self.__timeout_start_time = None
    
    async def addToQueue(self, music: MusicDatabase, pos = -1):
        video_id = music.id
        video_title = music.title
        
        while True:
            if self._addingToQueue is False:
                self._addingToQueue = True
                self.queue.insert(
                    pos,
                    (
                    rf"music\{self.__guild.id}\{video_id}_{video_title}.mp3",
                    music
                    )
                )
                self._addingToQueue = False
                break
            await asyncio.sleep(0.25)
        return f"`{video_title}` is added to queue"

    async def dlmusic_one(self, url: str) -> MusicDatabase:
        video_opt = {
            "outtmpl": rf"\music\{self.__guild.id}\%(display_id)s_%(title)s.%(ext)s",
            "format": 'bestaudio',
            "extract_audio": True,
            "quiet": True,
            "ignoreerrors": True,
            'noprogress': True,
            'no_warnings': True,
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3'
                }
            ],
        }
        def func():
            with yt_dlp.YoutubeDL(video_opt) as ydl:
                info = ydl.extract_info(url, download = False)
                if os.path.isfile(rf"music\{self.__guild.id}\{info["id"]}_{info["title"]}.mp3") is not True:
                    ydl.download(url)
                music = MusicDatabase(url, info)
                return music
        music = await asyncio.to_thread(func)
        return music
    
    async def dlmusic_many(self, ctx, urls: list[str]) -> list[MusicDatabase]:
        async with ctx.typing():
            message = await ctx.send(f"adding playlist")
            
            async def func(url):
                music = await self.dlmusic_one(url)
                await self.addToQueue(music)
            
            coros = [func(url) for url in urls]
            await asyncio.gather(*coros)
            
            await message.edit(content=f"finished adding")
    
    async def playerLoop(self, ctx):
        await self.__bot.wait_until_ready()
        while True:
            if self.nowplaying_music is not None:
                await asyncio.sleep(1)
                continue
            
            if len(self.queue) == 0:
                if self.__timeout_start_time is None:
                    self.__timeout_start_time = datetime.datetime.now()
                else:
                    delta = (datetime.datetime.now() - self.__timeout_start_time).total_seconds()
                    if delta > 300:
                        if ctx.voice_client is not None:
                            await ctx.voice_client.disconnect()
                            await ctx.send("Timeout (idle over 5 mins)")
                        del self
                        return
                await asyncio.sleep(1)
                continue
            
            #else
            filename, music = self.queue.pop(0)
            if os.path.isfile(filename) is False:
                await self.dlmusic_one(music.url)
            self.nowplaying_music = (filename, music)
            
            volume = self.volume / 100
            source = discord.FFmpegPCMAudio(filename)
            source = discord.PCMVolumeTransformer(source, volume=volume)
            
            def after(error):
                source.cleanup()
                if error is not None:
                    coro = ctx.send(error)
                    asyncio.run_coroutine_threadsafe(coro, self.__bot.loop)
                self.history.insert(0, (filename, music))
                self.nowplaying_music = None
            
            self.nowplaying_start_time = datetime.datetime.now()
            ctx.voice_client.play(source, after=after)
            
            msg = await self.nowplaying()
            await ctx.send(msg)
    
    async def play(self, ctx, messages):
        async with ctx.typing():
            message = "".join(messages)
            if Check().is_watch_url(message):
                url = message
                music = await self.dlmusic_one(url)
                await ctx.send(await self.addToQueue(music))
            elif Check().is_playlist_url(message):
                urls = Playlist(message)
                await self.dlmusic_many(ctx, urls)
                #added all to queue inside dlmusic_many() to prevent getting banned from "spamming msg"
            else: #not url
                url = await self.__search(message)
                music = await self.dlmusic_one(url)
                await ctx.send(await self.addToQueue(music))
        
        if self.nowplaying_music is None:
            await self.playerLoop(ctx)
    
    async def __search(self, message: str) -> str:
        videosSearch = VideosSearch(message, limit = 1)
        url = videosSearch.result()['result'][0]['link']
        return url

    async def nowplaying(self):
        if self.nowplaying_music is None: return None
        
        music = self.nowplaying_music[1]
        start = self.nowplaying_start_time
        delta = datetime.datetime.now() - start
        duration = datetime.timedelta(seconds=music.duration)
        delta = DF().format_time(delta)
        duration = DF().format_time(duration)
        output = f"""
        Nowplaying:
    `{music.title}`
    {delta} / {duration}
        """
        return output
    
    async def repeat(self, ctx):
        _, music = self.nowplaying_music
        await self.addToQueue(music, 0)
        ctx.voice_client.stop()

    async def previous(self, ctx):
        self.queue.insert(0, self.nowplaying_music)
        self.queue.insert(0, self.history.pop(0))
        ctx.voice_client.stop()
        self.history.pop(0)