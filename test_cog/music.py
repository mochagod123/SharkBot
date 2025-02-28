from discord.ext import commands
import discord
import traceback
import sys
import logging
import asyncio
from functools import partial
import time
from yt_dlp import YoutubeDL

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

Queues = {}

ytdl = YoutubeDL(YTDL_OPTIONS)

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> MusicCog")

    @commands.group(aliases=["mu"], description="音楽関連です。")
    @commands.guild_only()
    async def music(self, ctx):
        await self.bot.send_subcommand(ctx, "music")

    async def get_music_info(self, url):
        loop = asyncio.get_event_loop()
        try:
            info = await loop.run_in_executor(None, partial(ytdl.extract_info, url, download=False, process=False))
            info["url"] = url
            info["time"] = time.time() + 60 * 60 * 24 * 7
            return info
        except:
            return

    @music.command(name="join", aliases=["j"], description="VCに接続します。")
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def music_join(self, ctx, vc: discord.VoiceChannel = None):
        Queues[ctx.author.voice.channel.id] = []
        if vc != None:
            try:
                await vc.connect()
                return await ctx.reply(embed=discord.Embed(title=f"`{ctx.author.voice.channel.name}`に接続しました。", color=discord.Color.green()))
            except:
                return await ctx.reply(embed=discord.Embed(title=f"`{ctx.author.voice.channel.name}`に接続できませんでした。", color=discord.Color.red()))
        else:
            try:
                await ctx.author.voice.channel.connect()
                return await ctx.reply(embed=discord.Embed(title=f"`{ctx.author.voice.channel.name}`に接続しました。", color=discord.Color.green()))
            except:
                return await ctx.reply(embed=discord.Embed(title=f"`{ctx.author.voice.channel.name}`に接続できませんでした。", color=discord.Color.red()))
            
    @music.command(name="leave", aliases=["l"], description="VCから退出します。")
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def music_leave(self, ctx):
        try:
            Queues[ctx.author.voice.channel.id].clear()
            await ctx.voice_client.disconnect()
            return await ctx.reply(embed=discord.Embed(title=f"`{ctx.author.voice.channel.name}`から切断しました。", color=discord.Color.red()))
        except:
            return await ctx.reply(embed=discord.Embed(title=f"`{ctx.author.voice.channel.name}`から切断できませんでした", color=discord.Color.red()))

    @music.command(name="play", aliases=["p"], description="音楽を再生します。")
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def music_play(self, ctx, youtube: str):
        Queues[ctx.author.voice.channel.id].append(f"{youtube}")
        if not ctx.guild.voice_client.is_playing():
            while True:
                try:
                    if len(Queues[ctx.author.voice.channel.id]) == 0:
                        await ctx.reply(embed=discord.Embed(title="音楽が終了しました。", color=discord.Color.red()))
                        return
                    if not ctx.guild.voice_client.is_playing():
                        info = await self.get_music_info(Queues[ctx.author.voice.channel.id][0])
                        ru = ""
                        t = info["title"]
                        for f in info['formats']:
                                try:
                                    if f["ext"] == "m4a":
                                        ru = f["url"]
                                        break
                                except:
                                    continue
                        ctx.guild.voice_client.play(discord.FFmpegOpusAudio(ru, bitrate=256, stderr=sys.stdout))
                        await ctx.channel.send(embed=discord.Embed(title="再生を開始します。", description=f"{t}", color=discord.Color.green()))
                        Queues[ctx.author.voice.channel.id].remove(Queues[ctx.author.voice.channel.id][0])
                    await asyncio.sleep(10)
                except:
                    return
        else:
            await ctx.reply("キューに追加しました。")

    @music.command(name="stop", aliases=["s"], description="音楽を停止します。")
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def music_stop(self, ctx):
        if ctx.guild.voice_client.is_playing():
            Queues[ctx.author.voice.channel.id].clear()
            ctx.voice_client.stop()
            await ctx.reply(embed=discord.Embed(title="再生を停止しました。", color=discord.Color.green()))
        else:
            await ctx.reply(embed=discord.Embed(title="再生していません。", color=discord.Color.red()))

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        voice_state = member.guild.voice_client
        if voice_state is None:
            return

        if len(voice_state.channel.members) == 1:
            await voice_state.disconnect()

async def setup(bot):
    await bot.add_cog(MusicCog(bot))