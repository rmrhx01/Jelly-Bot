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
                #Check if the queue exists
                if self.ctx.guild.id in queues.keys():
                    #Checks if the queue is not empty
                    if queues[self.ctx.guild.id]:
                        asyncio.run_coroutine_threadsafe(queues[self.ctx.guild.id].pop(0).play(),client.loop)
                        #Delete the file for the last song

                    else:
                        #If empty we delete it from the dictionary and disconnect
                        del queues[self.ctx.guild.id]
                        asyncio.run_coroutine_threadsafe(self.ctx.guild.voice_client.disconnect(),client.loop)
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

client = commands.Bot()

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

async def author_is_connected(ctx):
    if ctx.author.voice and ctx.author.voice.channel:
        return True
    else:
        await ctx.response.send_message("You gotta be in a voice channel pal")
        return False

async def bot_is_connected(ctx):
    if ctx.guild.voice_client:
        return True
    else:
        await ctx.response.send_message("Im not connected pal")
        return False

async def connect_bot(ctx):
    #Checks if the bot is connected to a voicechannel in the server
    if ctx.guild.voice_client == None:
        await ctx.author.voice.channel.connect()
    return True
    

async def connected_same_channel(ctx):
    #Checks if the author and the bot are in the same channel
    if ctx.guild.voice_client.channel != ctx.author.voice.channel:
        await ctx.response.send_message("You gotta be in the same voice channel pal")
        return False
    else:
        return True
    

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client)) 


@client.slash_command(guild_ids=[658165266206818315])
@commands.guild_only()
@commands.check(author_is_connected)
@commands.check(connect_bot)
@commands.check(connected_same_channel)
async def play_url(ctx, url):
    
    voice = ctx.guild.voice_client

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
        await ctx.response.send_message('Added: {}'.format(video_title))


@client.slash_command(guild_ids=[658165266206818315])
async def bye(ctx):
    await ctx.response.send_message("Good night")
    for server in client.guilds:
        if server.voice_client:
            await server.voice_client.disconnect()
    await client.close()   

# Pause command
@client.slash_command(guild_ids=[658165266206818315])
@commands.check(author_is_connected)
@commands.check(bot_is_connected)
@commands.check(connected_same_channel)
async def pause(ctx):
    # Song is playing
    if not ctx.guild.voice_client.is_paused():
        ctx.guild.voice_client.pause()
        await ctx.response.send_message("Pausing song pal")
    
    # Song is paused
    else:
        await ctx.response.send_message("I'm already paused pal")

# Unpause command
@client.slash_command(guild_ids=[658165266206818315])
@commands.check(author_is_connected)
@commands.check(bot_is_connected)
@commands.check(connected_same_channel)
async def unpause(ctx):
    # Song is paused
    if ctx.guild.voice_client.is_paused():
        ctx.guild.voice_client.resume()
        await ctx.response.send_message("Unpausing song pal")

    # No songs are paused
    else:
        await ctx.response.send_message("I'm not paused pal")

# Skip command
@client.slash_command(guild_ids=[658165266206818315])
@commands.check(author_is_connected)
@commands.check(bot_is_connected)
@commands.check(connected_same_channel)
async def skip(ctx):
    if ctx.guild.voice_client.is_playing() or ctx.guild.voice_client.is_paused():
        ctx.guild.voice_client.stop()
        await ctx.response.send_message("Skipping song pal")
    else:
        await ctx.response.send_message("Nothing is playing pal")

# Stop command
@client.slash_command(guild_ids=[658165266206818315])
@commands.check(author_is_connected)
@commands.check(bot_is_connected)
@commands.check(connected_same_channel)
async def stop(ctx):
    if ctx.guild.voice_client.is_playing():
        del queues[ctx.guild.id]
        ctx.guild.voice_client.stop()
        await ctx.response.send_message("Stopped queue pal")
    else:
        await ctx.response.send_message("Nothing is playing pal")

client.run(config.token)