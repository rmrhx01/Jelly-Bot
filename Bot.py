#Improved bot
#By: Robbie and DoctorSneus

import discord
import youtube_dl
import asyncio
import config
from discord.ext import commands
from discord.commands import Option
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
        self.send_message = True
        
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
                    else:
                        #If empty we delete it from the dictionary and disconnect
                        del queues[self.ctx.guild.id]
                        asyncio.run_coroutine_threadsafe(self.ctx.guild.voice_client.disconnect(),client.loop)
                else:
                    asyncio.run_coroutine_threadsafe(self.ctx.guild.voice_client.disconnect(),client.loop)
        self.voice.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(self.idvideo)),after = afterFunc)
        if self.send_message:
            await self.ctx.send(self)   
    
    def set_send_message(self, send_message: bool = True ):
        self.send_message = send_message

    def get_videoTitle(self):
        return self.video_title

    def __str__(self):
        return ('Now playing: {}'.format(self.video_title))

client = commands.Bot()

guilds = [715759799668834324, 658165266206818315]
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(id)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'nooverwrites': True,
    'cachedir' : False,
    'source_address' : '0.0.0.0'
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

async def genericPlay(ctx, url):
    #Stream music
    info_dict = await client.loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=False)
        )
    video_title = info_dict.get('title', None)
    idvideo = info_dict.get('url',None)

    #Create song object
    voice = ctx.guild.voice_client
    s = Song(ctx, idvideo, video_title, voice)

    #Check if a queue exists for the server
    if not(ctx.guild.id in queues.keys()):
        queues[ctx.guild.id] = []
        m = await ctx.interaction.original_message()
        await m.edit(content = s)
        s.set_send_message(send_message = False)
        await s.play()

    else:
        queues[ctx.guild.id].append(s)
        m = await ctx.interaction.original_message()
        await m.edit(content = 'Added: {}'.format(video_title))

@client.slash_command(guild_ids=guilds, description = "Play a song from a youtube search pal")
@commands.guild_only()
@commands.check(author_is_connected)
@commands.check(connect_bot)
@commands.check(connected_same_channel)
async def play( ctx, 
                query: Option(str, "What do you want to search for, pal?")):
    await ctx.interaction.response.defer()

    # Finding the URL
    url = VideosSearch(query = query,limit = 1).result()["result"][0]["link"]
    await genericPlay(ctx, url)

@client.slash_command(guild_ids=guilds, description = "Play a song from a URL pal")
@commands.guild_only()
@commands.check(author_is_connected)
@commands.check(connect_bot)
@commands.check(connected_same_channel)
async def play_url(ctx, url):
    await ctx.interaction.response.defer()
    
    await genericPlay(ctx, url)


@client.slash_command(guild_ids=guilds, description = "Kill the bot pal")
async def bye(ctx):
    await ctx.response.send_message("Good night")
    for server in client.guilds:
        if server.voice_client:
            await server.voice_client.disconnect()
    await client.close()   

# Pause command
@client.slash_command(guild_ids=guilds, description = "Pause the current song pal")
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
@client.slash_command(guild_ids=guilds, description = "Unpause the current song pal")
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
@client.slash_command(guild_ids=guilds, description = "Skip the current song pal")
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
@client.slash_command(guild_ids=guilds, description = "No more music pal")
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
'''
@client.slash_command(guild_ids=guilds, description = "Show the songs on queue pal")
@commands.guild_only()
@commands.check(bot_is_connected)
async def show_queue(ctx):
    """Shows the queue of songs

    Args:
        ctx (abc.Messagable): Context of the command when summoned
    """
    if ctx.guild.id in queues.keys() and queues[ctx.guild.id]: 
        await ctx.defer()
        string = ""
        for i in queues[ctx.guild.id]:
            string += i.get_videoTitle()
        m = await ctx.interaction.original_message()
        await m.edit(content = string)

    else:
        await ctx.response.send_message("Queue is empty pal")
    
'''

client.run(config.token)