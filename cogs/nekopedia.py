from discord.ext import commands
import discord
import traceback
import sys
import logging
import random
import time
import asyncio

COOLDOWN_TIME = 5
user_last_message_time = {}

class NekoPediaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> NekoPediaCog")

    @commands.hybrid_group(name="nekipedia", description="Nekipediaを見るよ", fallback="show")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def nekipedia_show(self, ctx: commands.Context, 言葉: str):
        db = self.bot.async_db["Main"].NekiPedia
        try:
            dbfind = await db.find_one({"Word": 言葉}, {"_id": False})
        except:
            return await ctx.reply(embed=discord.Embed(title=f"情報がありません。", color=discord.Color.red()))
        if dbfind is None:
            return await ctx.reply(embed=discord.Embed(title=f"情報がありません。", color=discord.Color.red()))
        await ctx.reply(embed=discord.Embed(title=f"`{言葉}`を参照しました。", description=f"{dbfind["Desc"]}", color=discord.Color.green()).set_footer(text="著者: " + dbfind["Author"]))

    @nekipedia_show.command(name="write", description="Nekipediaに書くよ")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def nekipedia_write(self, ctx: commands.Context, 言葉: str, *, 意味: str):
        db = self.bot.async_db["Main"].NekiPedia
        try:
            await db.replace_one(
                {"Word": 言葉}, 
                {"Word": 言葉, "Desc": 意味, "Author": ctx.author.display_name}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title=f"{言葉}を書き込みました。", description=f"`!.nekipedia show {言葉}`で参照。", color=discord.Color.green()))
        except:
            return await ctx.reply(embed=discord.Embed(title=f"書き込めませんでした。", color=discord.Color.red()))
        
    @nekipedia_show.command(name="remove", description="Nekipediaから消すよ")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def nekipedia_remove(self, ctx: commands.Context, 言葉: str):
        db = self.bot.async_db["Main"].NekiPedia
        try:
            await db.replace_one(
                {"Word": 言葉}, 
                {"Word": 言葉, "Desc": f"これは、`{ctx.author.display_name}`によって、\n削除されました。", "Author": "なし"}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title=f"{言葉}を削除しました。", color=discord.Color.green()))
        except:
            return await ctx.reply(embed=discord.Embed(title=f"削除に失敗しました。", color=discord.Color.red()))
        
    @nekipedia_show.command(name="random", description="Nekipediaの内容をランダムに出すよ。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def nekipedia_random(self, ctx: commands.Context):
        await ctx.defer()
        db = self.bot.async_db["Main"].NekiPedia
        lt = []
        async for d in db.find():
            if "削除されました。" not in d["Desc"]:
                lt.append(f"{d['Word']},{d['Desc']},{d['Author']}")
            else:
                continue
        se = random.choice(lt)
        ls = se.split(",")
        await ctx.reply(embed=discord.Embed(title=f"{ls[0]}", description=f"{ls[1]}", color=discord.Color.green()).set_footer(text="著者: " + ls[2]))

async def setup(bot):
    await bot.add_cog(NekoPediaCog(bot))