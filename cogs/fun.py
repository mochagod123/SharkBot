from discord.ext import commands
from discord import Webhook
import io
import discord
import io
import traceback
import time
import sys
import base64
from concurrent.futures import ThreadPoolExecutor
import logging
import asyncio
from functools import partial
import textwrap
import aiohttp
import json
import io
from PIL import ImageFont, Image, ImageDraw, ImageSequence
import random
import unicodedata
import ssl
from bs4 import BeautifulSoup
import requests

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE



def text_len_sudden(text):
    count = 0
    for c in text:
        count += 2 if unicodedata.east_asian_width(c) in 'FWA' else 1
    return count

def sudden_generator(msg):
    length = text_len_sudden(msg)
    generating = '＿人'
    for i in range(length//2):
        generating += '人'
    generating += '人＿\n＞  ' + msg + '  ＜\n￣^Y'
    for i in range(length//2):
        generating += '^Y'
    generating += '^Y￣'
    return generating

cooldown_miqmod_time = {}
cooldown_miqrec_time = {}

class FunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("../Token.json") as tk:
            self.tkj = json.loads(tk.read())
            self.imageaikey = self.tkj["ImageAIAPIKey"]
        print(f"init -> FunCog")

    async def keigo_trans(self, kougo_text):
        request_data = {
                "kougo_writing": kougo_text,
                "mode": "direct",
                "platform": 0,
                "translation_id": ""
            }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post("https://y026dvhch0.execute-api.ap-northeast-1.amazonaws.com/translate", json=request_data) as response:
                    if response.status != 200:
                        return "Error"
                    response_data = await response.json()
                    return response_data.get("content", "No content in response")

        except aiohttp.ClientError as e:
            return f"Network error occurred: {e}"
        except Exception as e:
            return f"An error occurred: {e}"

    @commands.hybrid_group(name="fun", description="ランダムな色を生成します。", fallback="random_color")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def random_color(self, ctx: commands.Context):
        await ctx.reply(embed=discord.Embed(title="ランダムな色", color=discord.Color.random()))

    @random_color.command(name="suddendeath", description="突然の死を生成します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def suddendeath(self, ctx: commands.Context, 言葉: str):
        await ctx.defer()
        msg = await ctx.reply(embed=discord.Embed(title="突然の死", description=f"```{sudden_generator(言葉)}```", color=discord.Color.green()))
        await msg.add_reaction("<:Share:1325294641410736208>")
        try:
            r, m = await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id and not u.bot and ctx.author.id == u.id, timeout=30)
            if r.emoji.id == 1325294641410736208:
                await self.bot.share_func(ctx, f"```{sudden_generator(言葉)}```")
        except:
            return
        
    @random_color.command(name="janken", description="じゃんけんをします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def janken(self, ctx: commands.Context):
        await ctx.reply(embed=discord.Embed(title="じゃんけん", description=f"ぼくは「{random.choice(["ぐー", "ちょき", "ぱー"])}」をだしたよ！", color=discord.Color.red()))

    @random_color.command(name="keigo", description="敬語に変換します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def keigp(self, ctx: commands.Context, 口語: str):
        await ctx.defer()
        hen = await self.keigo_trans(口語) 
        await ctx.reply(embed=discord.Embed(title="三秒敬語", description=f"{hen}", color=discord.Color.green()))

    @random_color.command(name="roll", description="さいころをふります。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def roll(self, ctx: commands.Context, 何面か: int):
        await ctx.reply(f"🎲 {ctx.author.mention}: {random.randint(1, 何面か)}")

    @commands.hybrid_group(name="image", description="猫を取得します。", fallback="cat")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def cat_image(self, ctx: commands.Context):
        await ctx.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.thecatapi.com/v1/images/search?size=med&mime_types=jpg&format=json&has_breeds=true&order=RANDOM&page=0&limit=1") as cat:
                msg = await ctx.reply(embed=discord.Embed(title="猫の画像", color=discord.Color.green()).set_image(url=json.loads(await cat.text())[0]["url"]))
        await msg.add_reaction("<:Share:1325294641410736208>")
        try:
            r, m = await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id and not u.bot and ctx.author.id == u.id, timeout=30)
            if r.emoji.id == 1325294641410736208:
                await self.bot.share_func(ctx, f"{msg.jump_url}")
        except:
            return

    @cat_image.command(name="dog", description="犬を取得します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def dog_image(self, ctx: commands.Context):
        await ctx.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get("https://dog.ceo/api/breeds/image/random") as dog_:
                await ctx.reply(embed=discord.Embed(title="犬の画像", color=discord.Color.green()).set_image(url=f"{json.loads(await dog_.text())["message"]}"))

    @cat_image.command(name="5000", description="5000兆円ほしい！")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def choen_5000(self, ctx: commands.Context, 上: str, 下: str, noアルファ: bool = None):
        if noアルファ:
            if noアルファ == False:
                msg = await ctx.reply(embed=discord.Embed(title="5000兆円ほしい！", color=discord.Color.green()).set_image(url=f"https://gsapi.cbrx.io/image?top={上}&bottom={下}"))
            else:
                msg = await ctx.reply(embed=discord.Embed(title="5000兆円ほしい！", color=discord.Color.green()).set_image(url=f"https://gsapi.cbrx.io/image?top={上}&bottom={下}&noalpha=true"))
        else:
            msg = await ctx.reply(embed=discord.Embed(title="5000兆円ほしい！", color=discord.Color.green()).set_image(url=f"https://gsapi.cbrx.io/image?top={上}&bottom={下}"))
        await msg.add_reaction("<:Share:1325294641410736208>")
        try:
            r, m = await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id and not u.bot and ctx.author.id == u.id, timeout=30)
            if r.emoji.id == 1325294641410736208:
                await self.bot.share_func(ctx, f"{msg.jump_url}")
        except:
            return

    @cat_image.command(name="3ds", description="3dsを生成します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def san_ds(self, ctx: commands.Context, 画像: discord.Attachment):
        await ctx.defer()
        image_byte = 画像.url
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_byte) as response:
                    content = await response.read()
                    pdf_data = io.BytesIO(content)
                    sendio = io.BytesIO()
                    def Run():
                        img = Image.open(pdf_data)
                        image1 = Image.open("data/3ds.jpg")
                        img_resize = img.resize((768, 772))
                        image1.paste(img_resize, (7, 23))
                        image1.save(sendio,format="png")
                        sendio.seek(0)
                    loop = asyncio.get_running_loop()
                    with ThreadPoolExecutor() as executor:
                        result = await loop.run_in_executor(executor, Run)
                    msg = await ctx.send(file=discord.File(sendio, filename="result.png"))
                    sendio.close()
        except:
            await ctx.reply(embed=discord.Embed(title="製造失敗。", color=discord.Color.red()))
            return

    @cat_image.command(name="gen_chat", description="Chatを生成します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def get_chat(self, ctx: commands.Context, メンバー: discord.User, テキスト: str, 時間: str):
        await ctx.defer()
        sendio = io.BytesIO()

        def create_font(path, size):
            return ImageFont.truetype(path, size)

        def Run():
            font_path = 'data/DiscordFont.ttf'
            font_large = create_font(font_path, 17)
            font_medium = create_font(font_path, 15)
            font_small = create_font(font_path, 10)
            content = requests.get(メンバー.display_avatar)
            pdf_data = io.BytesIO(content.content)
            img = Image.open(pdf_data)
            image1 = Image.new("RGB", (len(テキスト) * 20 + 200, 65), (49, 51, 56))
            mask = Image.new("L", (40, 40), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, 40, 40), fill=255)
            img_resize = img.resize((40, 40))
            image1.paste(img_resize, (5, 8), mask)
            draw = ImageDraw.Draw(image1)
            draw.text((62, 5), メンバー.display_name, fill=(219, 222, 225), font=font_medium)
            name_bbox = font_medium.getbbox(メンバー.display_name)
            name_width = name_bbox[2]
            draw.text((62 + name_width + 5, 9), 時間, fill=(148, 155, 164), font=font_small)
            draw.text((61, 24), テキスト, fill=(255, 255, 255), font=font_large)
            image1.save(sendio,format="png")
            sendio.seek(0)
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(executor, Run)
        msg = await ctx.send(file=discord.File(sendio, filename="result.png"))
        sendio.close()

    def chunk_string(self, text, chunk_size):
        for i in range(0, len(text), chunk_size):
            yield text[i:i + chunk_size]

    @cat_image.command(name="news", description="ニュースを生成します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def news_gen(self, ctx: commands.Context):
        sendio = io.BytesIO()
        await ctx.defer()
        def create_font(path, size):
            return ImageFont.truetype(path, size)
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://www3.nhk.or.jp/news/', ssl=ssl_context) as response:
                soup = BeautifulSoup(await response.text(), 'html.parser')
                title = soup.find_all('h1', class_="content--header-title")[0]
                urlss = title.find_all('a')[0]
                baseimage = Image.open("data/News.png")
                font_path = 'data/DiscordFont.ttf'
                font_large = create_font(font_path, 17)
                draw = ImageDraw.Draw(baseimage)
                y = 30
                for line in self.chunk_string(urlss.get_text(), 20):
                    draw.text((130, y), line, fill="white", font=font_large)
                    y += 60
                baseimage.save(sendio,format="png")
                sendio.seek(0)
                await ctx.send(file=discord.File(sendio, filename="result.png"))
                sendio.close()

    @commands.command(name="miq")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def miaq_make(self, ctx: commands.Context):
        if ctx.message.reference:
            msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            if type(msg) == discord.Message:
                if not msg.content:
                    return
                loop = asyncio.get_event_loop()
                if msg.author.avatar:
                    res = await loop.run_in_executor(None, partial(requests.post, "https://api.voids.top/fakequote", headers={"Content-Type": "application/json"}, json={
                            "username": f"{msg.author.name}",
                            "display_name": f"{msg.author.display_name}",
                            "text": f"{msg.content}",
                            "avatar": f"{msg.author.avatar.url}",
                            "color": "false"
                        }
                    ))

                    await ctx.reply(embed=discord.Embed(color=discord.Color.green()).set_image(url=res.json()["url"]))
                else:
                    res = await loop.run_in_executor(None, partial(requests.post, "https://api.voids.top/fakequote", headers={"Content-Type": "application/json"}, json={
                            "username": f"{msg.author.name}",
                            "display_name": f"{msg.author.display_name}",
                            "text": f"{msg.content}",
                            "avatar": f"{msg.author.default_avatar.url}",
                            "color": "false"
                        }
                    ))

                    await ctx.reply(embed=discord.Embed(color=discord.Color.green()).set_image(url=res.json()["url"]))

    @cat_image.command(name="profile", description="プロフィールを生成します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def profile(self, ctx: commands.Context, ユーザー: discord.User = None):
        await ctx.defer()
        member = ユーザー
        if member is None:
            member = ctx.author

        async with aiohttp.ClientSession() as session:
            async with session.get(member.avatar.url) as resp:
                avatar_bytes = await resp.read()

        avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
        avatar = avatar.resize((128, 128))  # サイズ変更

        mask = Image.new("L", (128, 128), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, 128, 128), fill=255)
        avatar.putalpha(mask)

        bg = Image.new("RGBA", (500, 200), (30, 30, 30, 255))

        bg.paste(avatar, (20, 36), avatar)

        font = ImageFont.truetype("data/DiscordFont.ttf", 24)

        draw = ImageDraw.Draw(bg)
        draw.text((160, 40), member.name, font=font, fill=(255, 255, 255))
        draw.text((160, 80), f"ID: {member.id}", font=font, fill=(180, 180, 180))
        db = self.bot.async_db["Main"].ProfileTitle
        try:
            dbfind = await db.find_one({"User": member.id}, {"_id": False})
            draw.text((160, 120), f"{dbfind["Title"]}", font=font, fill=(180, 180, 180))
        except:
            pass
        if dbfind is None:
            draw.text((160, 120), f"コメント未設定", font=font, fill=(180, 180, 180))
            pass

        with io.BytesIO() as image_binary:
            bg.save(image_binary, "PNG")
            image_binary.seek(0)
            await ctx.send(file=discord.File(image_binary, "profile.png"))

    @cat_image.command(name="title", description="プロフィールのタイトルを設定します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def profile_title(self, ctx: commands.Context, タイトル: str):
        await ctx.defer()
        db = self.bot.async_db["Main"].ProfileTitle
        await db.replace_one(
            {"User": ctx.author.id}, 
            {"User": ctx.author.id, "Title": タイトル}, 
            upsert=True
        )
        await ctx.reply("タイトルを設定しました。")

async def setup(bot):
    await bot.add_cog(FunCog(bot))