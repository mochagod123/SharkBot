from discord.ext import commands
from urllib.parse import quote
import discord
import traceback
import sys
import tweepy
import logging
import time
import datetime
import asyncio
import aiohttp
import json
from functools import partial
import re
import urllib
from urllib.parse import urlparse, parse_qs
import whois
import requests
from bs4 import BeautifulSoup
import urllib.parse
import io
import base64
import mimetypes

def UploadFile(io, filename: str):
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Referer': 'https://firestorage.jp/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    params = {
        'act': 'flashupjs',
        'type': 'flash10b',
        'photo': '1',
        'talk': '1',
        'json': '1',
        'eid': '',
    }

    uploadfolder = requests.get('https://firestorage.jp/flashup.cgi', params=params, headers=headers)

    uploadid = uploadfolder.json()

    headers = {
        'Accept': '*/*',
        'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Origin': 'https://firestorage.jp',
        'Referer': 'https://firestorage.jp/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    mime_type, _ = mimetypes.guess_type(filename)

    files = [
            ('folder_id', (None, f'{uploadid["folder_id"]}')),
            ('ppass', (None, '')),
            ('dpass', (None, '')),
            ('thumbnail', (None, 'nomal')),
            ('top', (None, '1')),
            ('jqueryupload', (None, '1')),
            ('max_size', (None, '2147483648')),
            ('max_sized', (None, '2')),
            ('max_size_photo', (None, '15728640')),
            ('max_size_photod', (None, '15')),
            ('max_size_photo', (None, '150')),
            ('max_count', (None, '20')),
            ('max_count_photo', (None, '150')),
            ('jqueryupload', (None, '1')),
            ('eid', (None, '')),
            ('processid', (None, f'{uploadid["folder_id"]}')),
            ('qst', (None, 'n1=Mozilla&n2=Netscape&n3=Win32&n4=Mozilla/5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit/537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome/131.0.0.0%20Safari/537.36')),
            ('comments', (None, '')),
            ('comment', (None, '')),
            ('arc', (None, '')),
            ('zips', (None, '')),
            ('file_queue', (None, '1')),
            ('pc', (None, '1')),
            ('exp', (None, '7')),
            ('Filename', (f"{filename}", io, mime_type)),
    ]

    response = requests.post('https://server73.firestorage.jp/upload.cgi', headers=headers, files=files)

    decoded_str = urllib.parse.unquote(response.text)

    soup = BeautifulSoup(decoded_str, 'html.parser')

    download_url = soup.find('a', {'id': 'downloadlink'})['href']

    return download_url

COOLDOWN_TIME = 5
user_last_message_time = {}

class ToolCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> ToolCog")

    async def get_bothyoka(self, bot: discord.User):
        db = self.bot.async_db["Main"].BotHyokaBun
        try:
            dbfind = await db.find_one({"Bot": f"{bot.id}"}, {"_id": False})
        except:
            return None
        if dbfind is None:
            return None
        return dbfind["Content"] + "\n" + "著者: " + self.bot.get_user(dbfind["User"]).display_name

    def is_valid_url(self, url):
        url_regex = re.compile(
            r'^(https?|ftp)://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'
            r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        return re.match(url_regex, url) is not None


    @commands.Cog.listener("on_message")
    async def on_message_afk(self, message):
        if message.author.bot:
            return
        db = self.bot.async_db["Main"].AFK
        try:
            dbfind = await db.find_one({"User": message.author.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        await message.reply(embed=discord.Embed(title="AFKを解除しました。", description=f"{dbfind["Reason"]}", color=discord.Color.green()))
        await db.delete_one({
            "User": message.author.id,
        })

    @commands.Cog.listener("on_message")
    async def on_message_afk_post(self, message):
        if message.channel.id == 1329969245362327582:
            try:
                content = message.content.split(",")
                author = content[0]
                reason = content[1]
                db = self.bot.async_db["Main"].AFK
                await db.replace_one(
                    {"User": int(author)}, 
                    {"User": int(author), "Reason": reason}, 
                    upsert=True
                )
            except:
                return

    @commands.Cog.listener("on_message")
    async def on_message_afk_mention(self, message):
        if message.author.bot:
            return
        if message.mentions:
            mentioned_users = [user.id for user in message.mentions]
            for m in mentioned_users:
                db = self.bot.async_db["Main"].AFK
                try:
                    dbfind = await db.find_one({"User": m}, {"_id": False})
                except:
                    return
                if dbfind is None:
                    return
                await message.reply(embed=discord.Embed(title=f"その人はAFKです。", description=f"理由: {dbfind["Reason"]}", color=discord.Color.red()))
                return

    @commands.hybrid_group(name="tools", description="AFKを設定します。", fallback="afk")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def afk_set(self, ctx: commands.Context, 理由: str, xに出すか: bool):
        await ctx.defer()
        if xに出すか:
            xdb = self.bot.async_db["Main"].XAPISetting
            try:
                xdbfind = await xdb.find_one({"User": ctx.author.id}, {"_id": False})
            except:
                return await ctx.reply(ephemeral=True, content="XAPIKeyが設定されていません。\n設定してください。")
            if xdbfind is None:
                return await ctx.reply(ephemeral=True, content="XAPIKeyが設定されていません。\n設定してください。")
            client = tweepy.Client(bearer_token=xdbfind["BearerToken"],
                                consumer_key=xdbfind["APIKey"],
                                consumer_secret=xdbfind["APISECRET"],
                                access_token=xdbfind["APITOKEN"],
                                access_token_secret=xdbfind["APITOKENSECRET"])
            response = client.create_tweet(text=f"「{ctx.author.name}」さんが放置状態になりました。\n理由: 「{理由}」\n\nBy SharkBot\nhttps://discord.com/application-directory/1322100616369147924")
        database = self.bot.async_db["Main"].AFK
        await database.replace_one(
            {"User": ctx.author.id}, 
            {"User": ctx.author.id, "Reason": 理由}, 
            upsert=True
        )
        await ctx.reply(embed=discord.Embed(title="AFKを設定しました。", description=f"{理由}", color=discord.Color.green()))

    @afk_set.command(name="webshot", description="スクリーンショットを取るよ")
    @commands.cooldown(1, 20, commands.BucketType.guild)
    async def webshot(self, ctx: commands.Context, url: str):
        await ctx.defer()
        if self.is_valid_url(url):
            headers = {
            "Content-Type": "application/x-www-form-urlencoded"
            }
            body = f"url={url}&waitTime=1&browserWidth=1000&browserHeight=1000"
            async with aiohttp.ClientSession() as session:
                async with session.post("https://securl.nu/jx/get_page_jx.php", headers=headers, data=body) as response:
                    text = await response.text()
                    js = json.loads(text)
                    await ctx.reply(embed=discord.Embed(title="スクリーンショット", color=discord.Color.green()).set_image(url=f"https://securl.nu{js["img"]}"))
        else:
            await ctx.reply(embed=discord.Embed(title="それはURLではありません。", color=discord.Color.red()))

    @afk_set.command(name="botinvite", description="Botの招待リンクから解析します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def _bot_invite(self, ctx: commands.Context, url: str):
        await ctx.defer()
        try:
            if re.match(r'https://discord.com/oauth2/authorize?', url):
                q = urlparse(url).query
                p = parse_qs(q)
                if "bot" in p["scope"][0]:
                    try:
                        u = self.bot.get_user(int(p["client_id"][0]))
                        if type(u) == discord.User:
                            bot = await self.get_bothyoka(u)
                            embed = discord.Embed(title="Botの情報", description=f"名前: {u.name}\nID: {u.id}\n{u.created_at}", color=discord.Color.green())
                            if bot:
                                embed.add_field(name="Botの評価", value=f"{bot}")
                            if u.avatar:
                                embed.set_thumbnail(url=u.avatar.url)
                        else:
                            return await ctx.reply(embed=discord.Embed(title="解析に失敗しました。", color=discord.Color.red()))
                    except:
                        pass
                    msg = await ctx.reply(embeds=[discord.Embed(title="解析結果", description=f"ClientID: {p["client_id"][0]}\nScope: {p["scope"][0]}", color=discord.Color.green()), embed])
                    if not bot:
                        await msg.add_reaction("🖊")
                        try:
                            r, m = await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id and not u.bot and ctx.author.id == u.id, timeout=30)
                            await ctx.channel.send("このBotの評価を書いて")
                            ms = await self.bot.wait_for("message", check=lambda ms: not ms.author.bot and ctx.author.id == ms.author.id, timeout=30)
                            db = self.bot.async_db["Main"].BotHyokaBun
                            await db.replace_one(
                                {"Bot": p["client_id"][0]}, 
                                {"User": ctx.author.id, "Content": ms.content, "Bot": p["client_id"][0]}, 
                                upsert=True
                            )
                            await ms.add_reaction("✅")
                        except:
                            return
                    else:
                        await msg.add_reaction("👆")
                        await msg.add_reaction("👇")
                        try:
                            r, m = await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id and not u.bot and ctx.author.id == u.id, timeout=30)
                            await ctx.channel.send("そう思う理由を書いて")
                            ms = await self.bot.wait_for("message", check=lambda ms: not ms.author.bot and ctx.author.id == ms.author.id, timeout=30)
                            db = self.bot.async_db["Main"].BotHyokaBun
                            await db.replace_one(
                                {"Bot": p["client_id"][0]}, 
                                {"User": ctx.author.id, "Content": ms.content, "Bot": p["client_id"][0]}, 
                                upsert=True
                            )
                            await ms.add_reaction("✅")
                        except:
                            return
                else:
                    await ctx.reply(embed=discord.Embed(title="解析に失敗しました。", description="それはBotの招待リンクではありません。", color=discord.Color.red()))
            else:
                await ctx.reply(embed=discord.Embed(title="解析に失敗しました。", color=discord.Color.red()))
        except:
            await ctx.reply(embed=discord.Embed(title="解析に失敗しました。", color=discord.Color.red()))

    @afk_set.command(name="tempchannel", description="一時的なテキストチャンネルを作ります")
    @commands.cooldown(1, 20, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def tempchannel(self, ctx: commands.Context, チャンネル名: str, 何分か: int):
        if 何分か > 10:
            return await ctx.reply("10分以上は不可です。")
        await ctx.defer()
        db = self.bot.async_db["Main"].TempChannelCheck
        try:
            dbfind = await db.find_one({"Guild": ctx.guild.id}, {"_id": False})
        except:
            return await ctx.reply("二つ以上作成できません。")
        if not dbfind is None:
            return await ctx.reply("二つ以上作成できません。")
        await db.replace_one(
            {"Guild": ctx.guild.id}, 
            {"Guild": ctx.guild.id}, 
            upsert=True
        )
        ch = await ctx.guild.create_text_channel(name=チャンネル名)
        await ctx.reply(embed=discord.Embed(title="一時的なチャンネルを作成しました。", color=discord.Color.green(), description=f"{ch.jump_url}"))
        await asyncio.sleep(何分か*60)
        if ch and ch in ctx.guild.text_channels:
            await ch.delete()
        await db.delete_one({
            "Guild": ctx.guild.id,
        })

    @afk_set.command(name="whois", description="ドメインの情報を見ます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def whois(self, ctx: commands.Context, urlかドメイン: str):
        await ctx.defer()
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, partial(whois.whois, urlかドメイン))
        await ctx.reply(embed=discord.Embed(title="Whois検索", color=discord.Color.green()).add_field(name="ドメイン名", value=response["domain_name"], inline=False).add_field(name="ドメインの作成日", value=response["creation_date"], inline=False))

    @commands.command(name="upload", description="ファイルをアップロードして、URL化します。")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def upload_file_firestorage(self, ctx: commands.Context):
        if not ctx.message.attachments:
            return await ctx.reply("ファイルがありません。")
        
        loop = asyncio.get_event_loop()
        ios = io.BytesIO(await ctx.message.attachments[0].read())
        response = await loop.run_in_executor(None, partial(UploadFile, ios, f"{ctx.message.attachments[0].filename}"))
        await ctx.reply(f"🔗アップロードしました。\n{response}")

    @commands.command(name="hello", description="今日が始まってから何時間立ったかを計測します。")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def hello_time(self, ctx: commands.Context):
        now = datetime.datetime.now()
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        diff = now - midnight
        
        await ctx.reply(f'今日が始まってからの誤差は {diff} です。')

    @commands.command(name="custom_invite", description="カスタム招待リンクを作成します。")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def custom_invite(self, ctx: commands.Context, code: str):
        db = self.bot.async_db["Main"].CustomInvite
        try:
            dbfind = await db.find_one({"Code": code.replace(" ", "-")}, {"_id": False})
        except:
            return await ctx.reply("すでにそのコードは使用されています。")
        if not dbfind is None:
            return await ctx.reply("すでにそのコードは使用されています。")
        inv = await ctx.channel.create_invite()
        await db.replace_one(
            {"Code": code.replace(" ", "-")}, 
            {"Code": code.replace(" ", "-"), "URL": inv.url}, 
            upsert=True
        )
        await ctx.reply(f"カスタム招待リンクを作成しました。\nhttps://www.sharkbot.xyz/invite/{code.replace(" ", "-")}")

    @commands.command(name="category_ch_count", description="カテゴリの量をカウントします。")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def category_ch_count(self, ctx: commands.Context, カテゴリ: discord.CategoryChannel):
        await ctx.reply(f"{カテゴリ.name}のチャンネル数: {len(カテゴリ.channels)}個")

async def setup(bot):
    await bot.add_cog(ToolCog(bot))