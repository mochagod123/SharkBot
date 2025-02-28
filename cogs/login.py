from discord.ext import commands
import discord
import traceback
import sys
import logging
import random
import time
import asyncio
import re
from functools import partial
import time

class LoginCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> LoginCog")

    @commands.hybrid_group(name="login", description="ログインデータを取得します。", fallback="date")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def login_date(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)
        vi = discord.ui.View()
        vi.add_item(discord.ui.Button(label="ログイン", url="https://discord.com/oauth2/authorize?client_id=1322100616369147924&response_type=code&redirect_uri=https%3A%2F%2Fwww.sharkbot.xyz%2Fcookie&scope=identify+guilds+guilds.join"))
        db = self.bot.async_db["Main"].SharkAC
        try:
            dbfind = await db.find_one({"UserID": str(ctx.author.id)}, {"_id": False})
        except:
            return await ctx.reply("まだアカウントはありません。", ephemeral=True, view=vi)
        if dbfind is None:
            return await ctx.reply("まだアカウントはありません。", ephemeral=True, view=vi)
        await ctx.reply(embed=discord.Embed(title="あなたのアカウント", color=discord.Color.green()).add_field(name="ユーザーネーム", value=f"```{dbfind["UserName"]}```", inline=False).add_field(name="ユーザーID", value=f"```{dbfind["UserID"]}```", inline=False), ephemeral=True, view=vi)

    @login_date.command(name="logout", description="ログインデータを削除します。")
    @commands.cooldown(1, 20, commands.BucketType.guild)
    async def logout_data(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)
        mdb = self.bot.async_db["Main"].SharkAC
        mdb.delete_one(
                {"UserID": str(ctx.author.id)}
            )
        await ctx.reply(ephemeral=True, embed=discord.Embed(title="ログアウトしました。", color=discord.Color.green()))

async def setup(bot):
    await bot.add_cog(LoginCog(bot))