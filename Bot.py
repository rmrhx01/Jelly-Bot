#Improved bot
#By: Robbie

import discord
import youtube_dl
import asyncio
import os
import random
import config
from discord.ext import commands
from youtubesearchpython import VideosSearch #results = VideosSearch("video",limit = 1).result()

#Dictionary where the key is the id to every guild where the bot is currently playing
#Every key is gonna be associated with a list of songs which are on the queue
voiceChannels = {}

class Song:
    def __init__(self, ctx, idvideo: str, video_title: str, duration: int, voice):
        self.ctx = ctx
        self.idvideo = idvideo
        self.video_title = video_title
        self.duration = duration
        self.voice = voice
        
    async def play(self, afterFunc = None):
        self.voice.stop()
        def afterFunc(error):
            if(error):
                print(error)
            else:
                self._get_or_create_eventloop()
                if voiceChannels[self.ctx.guild.id]:
                    asyncio.run_coroutine_threadsafe(voiceChannels[self.ctx.guild.id][0].play(),client.loop)
                    voiceChannels[self.ctx.guild.id].pop(0)
                else:
                    asyncio.run_coroutine_threadsafe(self.ctx.guild.voice_client.disconnect(),client.loop)
            
        self.voice.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(self.idvideo)),after = afterFunc)
        await self.ctx.send(self)
    
    def is_playing(self):
        return self.voice.is_playing()
    
    def is_paused(self):
        return self.voice.is_paused()

    @staticmethod
    def _get_or_create_eventloop():
        try:
            return asyncio.get_event_loop()
        except RuntimeError as ex:
            if "There is no current event loop in thread" in str(ex):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                return asyncio.get_event_loop()

    def __str__(self):
        return ('Now playing: {}'.format(self.video_title))

client = commands.Bot(command_prefix = "&")

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(id)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'nooverwrites': True,
    'cachedir' : False,
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    #I feel so smart for the code below
    for guild in client.guilds:
        for c in guild.channels:
            if c.name == 'general':
                channel = c
    #await channel.send("We in bois, my current prefix is " + prefix)   


@client.command(pass_context=True)
@commands.guild_only()
#@commands.check(whatever condition)
async def playURL(ctx, url, *args):

    if ctx.author.voice and ctx.author.voice.channel:
        if ctx.guild.voice_client == None :
            voice = await ctx.author.voice.channel.connect()
        else:
            voice = ctx.guild.voice_client 
    else:
        await ctx.send("You gotta be in a voice channel pal")
        return
                   
    info_dict = ytdl.extract_info(url, download=True)
    video_title = info_dict.get('title', None)
    duration = info_dict.get('duration',None)
    idvideo = str(info_dict.get('id', None) + '.' + info_dict.get('ext', None))

    s = Song(ctx, idvideo, video_title, duration, voice)
    if not(ctx.guild.id in voiceChannels.keys()):
        voiceChannels[ctx.guild.id] = []
        await s.play()

    else:
        voiceChannels[ctx.guild.id].append(s)
        await ctx.send('Added: {}'.format(video_title))


@client.command(pass_context=True)
async def bye(ctx):
    await ctx.message.channel.send("Good night")
    await client.logout()   


client.run(config.token)