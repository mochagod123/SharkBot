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

class CharacterCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> CharacterCog")

    @commands.Cog.listener("on_message")
    async def on_message_character(self, message: discord.Message):
        db = self.bot.async_db["Main"].Character
        try:
            name = message.content.split("?")[0]
            try:
                dbfind = await db.find_one({"Guild": message.guild.id, "Name": name}, {"_id": False})
            except:
                return
            if dbfind is None:
                return
            ch_webhooks = await message.channel.webhooks()
            whname = f"SharkBot"
            webhooks = discord.utils.get(ch_webhooks, name=whname)
            if webhooks is None:
                webhooks = await message.channel.create_webhook(name=f"{whname}")
            async with aiohttp.ClientSession() as session:
                webhook = Webhook.from_url(webhooks.url, session=session)
                wordc = self.bot.async_db["Main"].CharacterWord
                try:
                    wordcfind = await wordc.find_one({"Guild": message.guild.id, "Name": name, "Word": message.content.split("?")[1]}, {"_id": False})
                except:
                    return
                if wordcfind is None:
                    return
                await webhook.send(content=f"{wordcfind["Reply"]}", avatar_url=f"{dbfind["Icon"]}", username=f"{dbfind["Name"]}")
        except:
            return

    @commands.hybrid_group(name="character", description="キャラクターを作成します。", fallback="make")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def character_make(self, ctx: commands.Context, キャラクター名: str, アイコン: str):
        await ctx.defer()
        db = self.bot.async_db["Main"].Character
        await db.replace_one(
            {"Guild": ctx.guild.id, "Name": キャラクター名}, 
            {"Guild": ctx.guild.id, "Name": キャラクター名, "Icon": アイコン}, 
            upsert=True
        )
        await ctx.reply(embed=discord.Embed(title="キャラクターを作成したよ！", description=f"やあ、僕は「{キャラクター名}」。\nよろしく！", color=discord.Color.yellow()).set_thumbnail(url=アイコン))

    @character_make.command(name="list", description="キャラクター一覧を表示します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def character_list(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].Character
        async with db.find(filter={"Guild": ctx.guild.id}) as cursor:
            servers = await cursor.to_list(length=None)
            cl = [f"{s["Name"]}" for s in servers]
            if len(cl) == 0:
                return await ctx.reply(embed=discord.Embed(title="キャラクター 一覧", description=f"まだありません。", color=discord.Color.green()))
            await ctx.reply(embed=discord.Embed(title="キャラクター 一覧", description=f"```{"\n".join(cl)}```", color=discord.Color.green()))

    @character_make.command(name="word", description="キャラクターの返す言葉を追加します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def character_word(self, ctx: commands.Context, キャラクターの名前: str, 質問: str, 返答: str):
        db = self.bot.async_db["Main"].CharacterWord
        await db.replace_one(
            {"Guild": ctx.guild.id, "Name": キャラクターの名前, "Word": 質問}, 
            {"Guild": ctx.guild.id, "Name": キャラクターの名前, "Word": 質問, "Reply": 返答}, 
            upsert=True
        )
        await ctx.reply(embed=discord.Embed(title="キャラクターに質問を覚えさせたよ！", color=discord.Color.yellow()))

    @character_make.command(name="forget", description="質問を忘れさせるよ")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def character_forget(self, ctx: commands.Context, キャラクターの名前: str, 質問: str):
        db = self.bot.async_db["Main"].CharacterWord
        await db.delete_one(
            {"Guild": ctx.guild.id, "Name": キャラクターの名前, "Word": 質問}
        )
        await ctx.reply(embed=discord.Embed(title="キャラクターが質問を忘れたよ！", color=discord.Color.yellow()))

async def setup(bot):
    await bot.add_cog(CharacterCog(bot))