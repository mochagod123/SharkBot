from discord.ext import commands
import discord
import traceback
import sys
import logging
import random
import time
import asyncio
import aiohttp
from discord import Webhook

class WelcomeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> WelcomeCog")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        g = self.bot.get_guild(member.guild.id)
        db = self.bot.async_db["Main"].WelcomeMessage
        try:
            dbfind = await db.find_one({"Guild": g.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        async def rep_name(msg: str, member: discord.Member):
            return msg.replace("<name>", member.name).replace("<count>", f"{member.guild.member_count}").replace("<guild>", member.guild.name).replace("<createdat>", f"{member.created_at}")
        try:
            wb = await self.bot.get_channel(dbfind["Channel"]).webhooks()
            webhooks = discord.utils.get(wb, name="SharkBot")
            if webhooks is None:
                webhooks = await self.bot.get_channel(dbfind["Channel"]).create_webhook(name=f"SharkBot")
            async with aiohttp.ClientSession() as session:
                webhook = Webhook.from_url(webhooks.url, session=session)
                try:
                    await webhook.send(embed=discord.Embed(title=f"{await rep_name(dbfind["Title"], member=member)}", description=f"{await rep_name(dbfind["Description"], member=member)}", color=discord.Color.green()))
                except:
                    return
        except:
            return

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        g = self.bot.get_guild(member.guild.id)
        db = self.bot.async_db["Main"].GoodByeMessage
        try:
            dbfind = await db.find_one({"Guild": g.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        async def rep_name(msg: str, member: discord.Member):
            return msg.replace("<name>", member.name).replace("<count>", f"{member.guild.member_count}").replace("<guild>", member.guild.name).replace("<createdat>", f"{member.created_at}")
        try:
            wb = await self.bot.get_channel(dbfind["Channel"]).webhooks()
            webhooks = discord.utils.get(wb, name="SharkBot")
            if webhooks is None:
                webhooks = await self.bot.get_channel(dbfind["Channel"]).create_webhook(name=f"SharkBot")
            async with aiohttp.ClientSession() as session:
                webhook = Webhook.from_url(webhooks.url, session=session)
                try:
                    await webhook.send(embed=discord.Embed(title=f"{await rep_name(dbfind["Title"], member=member)}", description=f"{await rep_name(dbfind["Description"], member=member)}", color=discord.Color.green()))
                except:
                    return
        except:
            return

async def setup(bot):
    await bot.add_cog(WelcomeCog(bot))