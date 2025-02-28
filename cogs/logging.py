from discord.ext import commands
import discord
import traceback
import sys
import logging
import random
import time
import asyncio
from discord import Webhook
import aiohttp

class LoggingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> LoggingCog")

"""
    @commands.Cog.listener("on_message_delete")
    async def on_message_delete_logging(self, message: discord.Message):
        channel = discord.utils.get(message.guild.channels, name='shark-logging')
        ch_webhooks = await channel.webhooks()
        whname = f"SharkBot"
        webhooks = discord.utils.get(ch_webhooks, name=whname)
        if webhooks is None:
            webhooks = await channel.create_webhook(name=f"{whname}")
        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(webhooks.url, session=session)    
            avatar = None
            if message.author.avatar:
                avatar = message.author.avatar.url
            await webhook.send(embed=discord.Embed(title="メッセージが削除されました。", description=f"{message.content}", color=discord.Color.blue()).set_author(name=message.author.name, icon_url=avatar), username="SharkBot", avatar_url="https://images-ext-1.discordapp.net/external/A8TIhdt6s2yZizSw9utIM5o-NzB54XUstE26HLQ3dmE/%3Fsize%3D1024/https/cdn.discordapp.com/avatars/1322100616369147924/ea2f4e3e91a7ed3e096567b34c070600.png?format=webp&quality=lossless&width=614&height=614")  
"""

async def setup(bot):
    await bot.add_cog(LoggingCog(bot))