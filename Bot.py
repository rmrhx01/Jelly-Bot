#Improved bot
#By: Robbie and DoctorSneus

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
queues = {}

class Song:
    def __init__(self, ctx, idvideo: str, video_title: str, voice):
        self.ctx = ctx
        self.idvideo = idvideo
        self.video_title = video_title
        self.voice = voice
        
    async def play(self):

        #Function to play after the song is done
        def afterFunc(error = None):
            if(error):
                print(error)
            else:
                #Check if the queue is not empty
                if queues[self.ctx.guild.id]:
                    asyncio.run_coroutine_threadsafe(queues[self.ctx.guild.id].pop(0).play(),client.loop)
                    #Delete the file for the last song

                else:
                    asyncio.run_coroutine_threadsafe(self.ctx.guild.voice_client.disconnect(),client.loop)
            
        self.voice.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(self.idvideo)),after = afterFunc)
        await self.ctx.send(self)
    
    def is_playing(self):
        return self.voice.is_playing()
    
    def is_paused(self):
        return self.voice.is_paused()

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


ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client)) 


@client.command(pass_context=True)
@commands.guild_only()
#@commands.check(whatever condition)
async def playURL(ctx, url, *args):

    #Checks if the author is connected to a voice channel
    if ctx.author.voice and ctx.author.voice.channel:
        #Checks if the bot is connected to a voicechannel in the server
        if ctx.guild.voice_client == None:
            #If it isnt it connects to the where the author is
            voice = await ctx.author.voice.channel.connect()
        #Checks if the author and the bot are in the same channel
        elif ctx.guild.voice_client.channel != ctx.author.voice.channel:
            await ctx.send("You gotta be in the same voice channel pal")
            return
        else:
            voice = ctx.guild.voice_client 
    else:
        await ctx.send("You gotta be in a voice channel pal")
        return
                   
    #Download music
    info_dict = ytdl.extract_info(url, download=True)
    video_title = info_dict.get('title', None)
    idvideo = str(info_dict.get('id', None) + '.' + info_dict.get('ext', None))

    #Create song object
    s = Song(ctx, idvideo, video_title, voice)

    #Check if a queue exists for the server
    if not(ctx.guild.id in queues.keys()):
        queues[ctx.guild.id] = []
        await s.play()

    else:
        queues[ctx.guild.id].append(s)
        await ctx.send('Added: {}'.format(video_title))


@client.command(pass_context=True)
async def bye(ctx):
    await ctx.message.channel.send("Good night")
    await client.logout()   


client.run(config.token)