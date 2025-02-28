from discord.ext import commands, tasks
import discord
import traceback
import ssl
import datetime
from bs4 import BeautifulSoup
import aiohttp
import requests
import sys
import logging
import time
from functools import partial
import json
import asyncio
from urllib.parse import urlparse
import ast
import operator
from deep_translator import GoogleTranslator

# サポートする演算子を定義
ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

COOLDOWN_TIME_TRANSEMOJI = 3
cooldown_transemoji_time = {}

class SafeCalculator(ast.NodeVisitor):
    def visit_BinOp(self, node):
        # 左右のノードを再帰的に評価
        left = self.visit(node.left)
        right = self.visit(node.right)
        # 演算子を取得して評価
        operator_type = type(node.op)
        if operator_type in ALLOWED_OPERATORS:
            return ALLOWED_OPERATORS[operator_type](left, right)
        return "エラー。"

    def visit_Num(self, node):
        return node.n

    def visit_Expr(self, node):
        return self.visit(node.value)

    def visit(self, node):
        if isinstance(node, ast.Expression):
            return self.visit_Expr(node)
        elif isinstance(node, ast.BinOp):
            return self.visit_BinOp(node)
        elif isinstance(node, ast.Constant):  # Python 3.8以降
            return node.value
        elif isinstance(node, ast.Num):  # Python 3.7以前
            return self.visit_Num(node)
        else:
            return "エラー。"

def safe_eval(expr):
    try:
        tree = ast.parse(expr, mode='eval')
        calculator = SafeCalculator()
        return calculator.visit(tree.body)
    except Exception as e:
        return f"Error: {e}"

class InfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("../Token.json") as tk:
            self.tkj = json.loads(tk.read())
            self.imgurclientid = self.tkj["ImgurClientID"]
        print(f"init -> SearchCog")

    @commands.hybrid_group(name="search", description="ユーザー情報を見ます。", fallback="user")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def user_search(self, ctx: commands.Context, user: discord.User):
        try:
            JST = datetime.timezone(datetime.timedelta(hours=9))
            isguild = None
            isbot = None
            if ctx.guild.get_member(user.id):
                isguild = "います。"
            else:
                isguild = "いません。"
            if user.bot:
                isbot = "はい"
            else:
                isbot = "いいえ"
            permissions = "<:User:1332339623170543656> ユーザー"
            try:
                if self.bot.get_guild(1323780339285360660).get_role(1325246452829650944) in self.bot.get_guild(1323780339285360660).get_member(user.id).roles:
                    permissions = "<:Mod:1332721179563131031> モデレーター"
                if user.id == 1206048010740432906:
                    permissions = "<:Owner:1332721431552856245> 管理者"
                if user.id == 1322100616369147924:
                    permissions = "<:same:1324943040871399456> SharkBot"
                if user.id == 462522669036732416:
                    permissions = "<:Rowen:1332721834495578182> RowenBot"
            except:
                pass
            if user.avatar:
                await ctx.reply(embed=discord.Embed(title=f"{user.display_name}の情報", color=discord.Color.green()).set_thumbnail(url=user.avatar.url).add_field(name="基本情報", value=f"ID: **{user.id}**\nユーザーネーム: **{user.name}#{user.discriminator}**\n作成日: **{user.created_at.astimezone(JST)}**\nこの鯖に？: **{isguild}**\nBot？: **{isbot}**").add_field(name="サービス情報", value=f"権限: **{permissions}**"))
            else:
                await ctx.reply(embed=discord.Embed(title=f"{user.display_name}の情報", color=discord.Color.green()).add_field(name="基本情報", value=f"ID: **{user.id}**\nユーザーネーム: **{user.name}#{user.discriminator}**\n作成日: **{user.created_at.astimezone(JST)}**\nこの鯖に？: **{isguild}**\nBot？: **{isbot}**").add_field(name="サービス情報", value=f"権限: **{permissions}**"))
        except:
            return
        
    @user_search.command(name="guild", description="サーバーの情報を見ます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def guild_info(self, ctx: commands.Context):
        embed = discord.Embed(title=f"{ctx.guild.name}の情報", color=discord.Color.green())
        embed.add_field(name="サーバー名", value=ctx.guild.name)
        embed.add_field(name="サーバーID", value=str(ctx.guild.id))
        embed.add_field(name="オーナー名", value=ctx.guild.owner.name)
        embed.add_field(name="オーナーID", value=str(ctx.guild.owner.id))
        JST = datetime.timezone(datetime.timedelta(hours=9))
        embed.add_field(name="作成日", value=ctx.guild.created_at.astimezone(JST))
        if ctx.guild.icon:
            await ctx.reply(embed=embed.set_thumbnail(url=ctx.guild.icon.url))
        else:
            await ctx.reply(embed=embed)

    @user_search.command(name="avatar", description="アバターを取得します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def avatar_info(self, ctx: commands.Context, avatar: discord.User):
        if avatar.avatar == None:
            return await ctx.reply(embed=discord.Embed(title=f"{avatar.name}さんのアバター", color=discord.Color.green()))
        await ctx.reply(embed=discord.Embed(title=f"{avatar.name}さんのアバター", color=discord.Color.green()).set_image(url=avatar.avatar.url))

    @user_search.command(name="asset", description="アバターの装飾を取得します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def avatar_asset(self, ctx: commands.Context, avatar: discord.User):
        if avatar.avatar_decoration == None:
            return await ctx.reply(embed=discord.Embed(title=f"{avatar.name}さんの装飾", color=discord.Color.green()))
        await ctx.reply(embed=discord.Embed(title=f"{avatar.name}さんのアバター", color=discord.Color.green()).set_image(url=avatar.avatar_decoration.url))

    @user_search.command(name="embed", description="Embedの情報を見るよ")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def embed_info(self, ctx: commands.Context, メッセージid: str):
        await ctx.defer()
        message = await ctx.channel.fetch_message(int(メッセージid))
        if not message.embeds:
            return await ctx.reply(embed=discord.Embed(title="Embedが見つかりません。", color=discord.Color.red()))
        embed = message.embeds[0]
        await ctx.reply(embed=discord.Embed(title="Embedの情報", description=f"Title: {embed.title}\nDescription: \n{embed.description}", color=discord.Color.green()))

    @user_search.command(name="emoji", description="絵文字の情報を見ます。")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def emoji_info(self, ctx: commands.Context, 絵文字: discord.Emoji):
        await ctx.defer()
        await ctx.reply(embed=discord.Embed(title="絵文字情報", color=discord.Color.green()).set_image(url=絵文字.url).add_field(name="基本情報", value=f"名前: {絵文字.name}\n作成日時: {絵文字.created_at}", inline=False).add_field(name="サーバー情報", value=f"{絵文字.guild.name} ({絵文字.guild.id})", inline=False))

    @user_search.command(name="snapshot", description="転送の情報を見ます。")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def snapshot_info(self, ctx: commands.Context, メッセージ: discord.Message):
        await ctx.defer()
        if メッセージ.message_snapshots:
            snap = メッセージ.message_snapshots[0]
            await ctx.reply(embed=discord.Embed(title="転送の情報", description=f"内容:\n{snap.content}\n作成日: **{snap.created_at}**", color=discord.Color.green()))
        else:
            await ctx.reply(embed=discord.Embed(title="転送の情報", description=f"転送が見つかりませんでした。", color=discord.Color.red()))

    @user_search.command(name="translate", description="翻訳をします。")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def translate(self, ctx: commands.Context, 翻訳先: str, *, テキスト: str):
        await ctx.defer()

        try:
            translator = GoogleTranslator(source="auto", target=翻訳先)
            translated_text = translator.translate(テキスト)

            embed = discord.Embed(
                title=f"翻訳 ({翻訳先} へ)",
                description=f"```{translated_text}```",
                color=discord.Color.green()
            )
            await ctx.reply(embed=embed)
        
        except Exception as e:
            embed = discord.Embed(
                title="翻訳に失敗しました",
                description="指定された言語コードが正しいか確認してください。",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed)

    @user_search.command(name="news", description="ニュースを表示します。")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def news(self, ctx: commands.Context):
        await ctx.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://www3.nhk.or.jp/news/', ssl=ssl_context) as response:
                soup = BeautifulSoup(await response.text(), 'html.parser')
                title = soup.find_all('h1', class_="content--header-title")[0]
                url = title.find_all('a')[0]
                await ctx.reply(embed=discord.Embed(title=f"{url.get_text()}", description=f"https://www3.nhk.or.jp{url["href"]}", color=discord.Color.green()).set_footer(text="NHK News", icon_url="https://gg-supply.com/wp-content/uploads/2022/01/nhk_gray-logo.png"))

    @user_search.command(name="eew", description="地震速報を表示します。")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def news(self, ctx: commands.Context):
        await ctx.defer()
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://api.p2pquake.net/v2/history?codes=551&limit=1', ssl=ssl_context) as response:
                js = json.loads(await response.text())
                await ctx.reply(embed=discord.Embed(title=f"{js[0]["earthquake"]["hypocenter"]["name"]}の地震", description=f"発生場所: ```{"\n".join([ff["addr"] for ff in js[0]["points"]][:20])}\n...```", color=discord.Color.blue()).set_footer(text="地震速報").add_field(name="危険度", value=f"{js[0]["earthquake"]["domesticTsunami"]}").add_field(name="発生時間", value=f"{js[0]["earthquake"]["time"]}"))

    @user_search.command(name="safeweb", description="Webサイトが安全かどうかをチェックします。")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def safeweb(self, ctx: commands.Context, url: str):
        await ctx.defer()
        async with aiohttp.ClientSession() as session:
            q = urlparse(url).netloc
            async with session.get(f'https://safeweb.norton.com/safeweb/sites/v1/details?url={q}&insert=0', ssl=ssl_context) as response:
                js = json.loads(await response.text())
                if js["rating"] == "b":
                    await ctx.reply(embed=discord.Embed(title="このサイトは危険です。", description=f"URLの評価: {js["communityRating"]}", color=discord.Color.red()))
                elif js["rating"] == "w":
                    await ctx.reply(embed=discord.Embed(title="このサイトは注意が必要です。", description=f"URLの評価: {js["communityRating"]}", color=discord.Color.yellow()))
                elif js["rating"] == "g":
                    await ctx.reply(embed=discord.Embed(title="このサイトは評価されていません。", description=f"URLの評価: {js["communityRating"]}", color=discord.Color.blue()))
                else:
                    await ctx.reply(embed=discord.Embed(title="このサイトは多分安全です。", description=f"URLの評価: {js["communityRating"]}", color=discord.Color.green()))

    @user_search.command(name="wikipedia", description="WikiPediaを検索します。")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def weikipedia_search(self, ctx: commands.Context, 検索ワード: str):
        await ctx.defer()
        loop = asyncio.get_event_loop()
        try:
            
            wikipedia_api_url = "https://ja.wikipedia.org/w/api.php"
            
            # APIパラメータ
            params = {
                "action": "query",
                "format": "json",
                "titles": 検索ワード,
                "prop": "info",
                "inprop": "url"
            }
            
            response = await loop.run_in_executor(None, partial(requests.get, wikipedia_api_url, params=params))
            await loop.run_in_executor(None, partial(response.raise_for_status))
            data = await loop.run_in_executor(None, partial(response.json))
            
            pages = data.get("query", {}).get("pages", {})
            if not pages:
                await ctx.send(f"'{検索ワード}' に該当するWikipedia記事が見つかりませんでした。")
                return
            
            page_id, page_info = next(iter(pages.items()))
            if page_id == "-1":
                await ctx.send(f"'{検索ワード}' に該当するWikipedia記事が見つかりませんでした。")
                return
            
            short_url = f"https://ja.wikipedia.org/w/index.php?curid={page_id}"
            await ctx.send(f"🔗 **{検索ワード}** のWikipedia短縮リンク: {short_url}")
        
        except Exception as e:
            await ctx.send(f"エラーが発生しました: {str(e)}")

    @user_search.command(name="suggestion", description="提案サーチを使います。")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def suggestion_search(self, ctx: commands.Context, 検索ワード: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://sug.search.nicovideo.jp/suggestion/expand/{検索ワード}', ssl=ssl_context) as response:
                try:
                    js = json.loads(await response.text())
                    await ctx.reply(embed=discord.Embed(title="提案検索", description=f"{"\n".join(js["candidates"])}", color=discord.Color.green()))
                except:
                    return await ctx.reply(ephemeral=True, content="検索に失敗しました。")

    @user_search.command(name="imgur", description="画像を検索します。")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def imgur(self, ctx: commands.Context, 検索ワード: str):
        await ctx.defer()
        try:
            params = {
                'client_id': f'{self.imgurclientid}',
                'inflate': 'tags',
                'q': f'{検索ワード}',
                'types': 'users,tags,posts',
            }

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, partial(requests.get, 'https://api.imgur.com/3/suggest', params=params))
            data = await loop.run_in_executor(None, partial(response.json))
            return await ctx.reply(f"https://imgur.com/gallery/{data["data"]["posts"][0]["hash"]}")
        except:
            return await ctx.reply(f"検索に失敗しました。")

    @commands.Cog.listener("on_reaction_add")
    async def on_reaction_add_translate(self, reaction: discord.Reaction, user: discord.Member):
        if user.bot:  # Botのリアクションは無視
            return

        db = self.bot.async_db["Main"].EmojiTranslate
        try:
            dbfind = await db.find_one({"Guild": reaction.message.guild.id}, {"_id": False})
        except Exception as e:
            print(f"DBエラー: {e}")
            return

        if dbfind is None:
            return

        current_time = time.time()
        last_message_time = cooldown_transemoji_time.get(reaction.message.guild.id, 0)
        if current_time - last_message_time < COOLDOWN_TIME_TRANSEMOJI:
            return
        cooldown_transemoji_time[reaction.message.guild.id] = current_time

        content = reaction.message.content
        if not content and reaction.message.embeds:
            content = reaction.message.embeds[0].description

        if not content:
            return  # 翻訳対象がない場合は何もしない

        lang_map = {
            "🇯🇵": "ja",
            "🇺🇸": "en",
        }

        if reaction.emoji in lang_map:
            target_lang = lang_map[reaction.emoji]
            msg = await reaction.message.channel.send(
                embed=discord.Embed(title="🔄 翻訳中...", color=discord.Color.blue())
            )

            try:
                translator = GoogleTranslator(source="auto", target=target_lang)
                translated_text = translator.translate(content)
                await msg.edit(
                    embed=discord.Embed(
                        title=f"翻訳結果 ({target_lang})",
                        description=f"```{translated_text}```",
                        color=discord.Color.green()
                    )
                )
            except Exception as e:
                print(f"翻訳エラー: {e}")
                await msg.edit(
                    embed=discord.Embed(
                        title="翻訳に失敗しました",
                        color=discord.Color.red()
                    )
                )

async def setup(bot):
    await bot.add_cog(InfoCog(bot))