from discord.ext import commands
import discord
import traceback
import sys
import logging
import time
import asyncio

COOLDOWN_TIME = 5
user_last_message_time = {}

class LockMessageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> LockMessageCog")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if '!.' in message.content:
            return
        user_id = message.author.id
        db = self.bot.async_db["Main"].LockMessage
        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        current_time = time.time()
        last_message_time = user_last_message_time.get(user_id, 0)
        if current_time - last_message_time < COOLDOWN_TIME:
            return
        user_last_message_time[user_id] = current_time
        try:
            await discord.PartialMessage(channel=message.channel, id=dbfind["MessageID"]).delete()
        except:
            pass
        msg = await message.channel.send(embed=discord.Embed(title=dbfind["Title"], description=dbfind["Desc"], color=discord.Color.random()))
        await db.replace_one(
            {"Channel": message.channel.id, "Guild": message.guild.id}, 
            {"Channel": message.channel.id, "Guild": message.guild.id, "Title": dbfind["Title"], "Desc": dbfind["Desc"], "MessageID": msg.id}, 
            upsert=True
        )

async def setup(bot):
    await bot.add_cog(LockMessageCog(bot))