from discord.ext import commands
import aiosqlite
import discord
import traceback
import random
import sys
import logging
import asyncio
import aiofiles
from bs4 import BeautifulSoup
import time

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> HelpCog")

    @commands.hybrid_group(name="bot", description="Pingを見ます。", fallback="ping")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def ping_bot(self, ctx: commands.Context):
        await ctx.reply(embed=discord.Embed(title="Pingを測定しました。", description=f"{round(self.bot.latency * 1000)}ms", color=discord.Color.green()))

    @ping_bot.command(name="about", description="Botの情報を見ます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def about_bot(self, ctx: commands.Context):
        await ctx.defer()
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="招待リンク", url="https://discord.com/oauth2/authorize?client_id=1322100616369147924&permissions=1759218604441591&integration_type=0&scope=bot+applications.commands"))
        view.add_item(discord.ui.Button(label="サポートサーバー", url="https://discord.gg/PNKyebmqMy"))
        mem = self.bot.get_guild(1323780339285360660).get_role(1325246452829650944).members
        em = discord.Embed(title="`SharkBot`の情報", color=discord.Color.green())
        em.add_field(name="サーバー数", value=f"{len(self.bot.guilds)}サーバー").add_field(name="ユーザー数", value=f"{len(self.bot.users)}人")
        cl = [c.name for c in self.bot.get_all_channels()]
        em.add_field(name="チャンネル数", value=f"{len(cl)}個")
        em.add_field(name="絵文字数", value=f"{len(self.bot.emojis)}個")
        em.add_field(name="オーナー", value=self.bot.get_user(1335428061541437531).display_name)
        em.add_field(name="モデレーター", value="\n".join([user.display_name for user in mem if not user.id == 1335428061541437531]), inline=False)
        em.add_field(name="現在のバグ", value="```SGCに送信されていないメッセージに返信したときにSharkBotにメッセージが表示されなくなる```", inline=False)
        await ctx.reply(embed=em, view=view)

    @ping_bot.command(name="invite", description="Botを招待します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def invite_bot(self, ctx: commands.Context, botのid: discord.User = None):
        if botのid:
            if not botのid.bot:
                return await ctx.reply(f"あれれ？{botのid.display_name}はBotじゃないよ？")
            return await ctx.reply(embed=discord.Embed(title=f"{botのid}を招待する。", description=f"# [☢️管理者権限で招待](https://discord.com/oauth2/authorize?client_id={botのid.id}&permissions=8&integration_type=0&scope=bot+applications.commands)\n\n# [😆権限なしで招待](https://discord.com/oauth2/authorize?client_id={botのid.id}&permissions=0&integration_type=0&scope=bot+applications.commands)", color=discord.Color.green()))
        await ctx.reply("""
# SharkBotの招待リンクです。
https://discord.gg/dkss9hqzyf
https://discord.com/application-directory/1322100616369147924
        """)

    @ping_bot.command(name="shark", description="SharkNetworkについて見ます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def shark_network(self, ctx: commands.Context):
        await ctx.reply(embed=discord.Embed(title="`SharkNetwork`の情報", description=f"""SharkNetworkについて。
SharkNetworkは、
以下のサービスを運営しております。
・`SharkBot` .. だれにでも使いやすいDiscordBot
・`SharkAds` .. お客様に合う広告を簡単に配信
ぜひご利用ください。
        """, color=discord.Color.green()))

    @ping_bot.command(name="setup", description="セットアップ用のヘルプを見ます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def setup_help(self, ctx: commands.Context):
        await ctx.reply(embed=discord.Embed(title="セットアップ用ヘルプです", description=f"""
グローバル宣伝を追加:
`/ads activate`
スーパーグローバルチャットを追加:
`/globalchat activate`
サーバー掲示板に乗せてみる():
`/settings register 説明:`
もっと知りたい？ `/help`を見よう！
        """, color=discord.Color.green()))

async def setup(bot):
    await bot.add_cog(HelpCog(bot))