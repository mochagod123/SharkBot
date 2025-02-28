from discord.ext import commands
import discord
import traceback
import sys
import logging
import random
import time
import io
from functools import partial
import asyncio
import aiohttp
import json
from discord import Webhook
from bs4 import BeautifulSoup
from mcstatus import JavaServer
import base64
import aiofiles

class GameCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> GameCog")

    @commands.hybrid_group(name="game", description="モンハンワールドのモンスターを取得するよ", fallback="monster")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def game_monster(self, ctx: commands.Context):
        await ctx.defer()
        await ctx.reply(embed=discord.Embed(title="現在製作中です。", color=discord.Color.green()))

    @game_monster.command(name="minecraft", description="Minecraftのユーザーの情報を取得するよ")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def minecraft(self, ctx: commands.Context, ユーザーネーム: str):
        await ctx.defer()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'https://api.mojang.com/users/profiles/minecraft/{ユーザーネーム}') as response:
                    j = json.loads(await response.text())
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f'https://api.minetools.eu/profile/{j["id"]}') as rs:
                            jj = json.loads(await rs.text())
                            await ctx.reply(embed=discord.Embed(title="Minecraftのユーザー情報", description=f"ID: {j["id"]}\nName: {j["name"]}", color=discord.Color.green()).set_thumbnail(url=f"{jj["decoded"]["textures"]["SKIN"]["url"]}").set_image(url=f"https://mc-heads.net/body/{ユーザーネーム}/200"))
        except:
            return await ctx.reply(embed=discord.Embed(title="ユーザー情報の取得に失敗しました。", color=discord.Color.red()))
        
    @game_monster.command(name="java-server", description="Minecraftサーバー(Java)の情報を見ます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def java_server(self, ctx: commands.Context, アドレス: str):
        await ctx.defer()
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f'https://api.mcsrvstat.us/3/{アドレス}') as response:
                    if response.status == 200:
                        j = json.loads(await response.text())
                        embed = discord.Embed(title=f"「{j['motd']['clean']}」\nの情報", color=discord.Color.green())
                        pl = j.get('players', {}).get('list', [])  # プレイヤーリストが存在しない場合のエラーを回避
                        embed.add_field(name="参加人数", value=f'{j["players"]["online"]}人')
                        embed.add_field(name="最大参加人数", value=f'{j["players"]["max"]}人')
                        if pl:
                            embed.add_field(name="参加者", value=f"{'\n'.join([f'{p['name']}' for p in pl])}", inline=False)
                        else:
                            embed.add_field(name="参加者", value="現在オンラインのプレイヤーはいません", inline=False)

                        # アイコンが存在する場合のみ処理を行う
                        if "icon" in j:
                            try:
                                i = base64.b64decode(j["icon"].split(';base64,')[1]) # base64データを抽出
                                ii = io.BytesIO(i) # BytesIOオブジェクトを直接作成
                                embed.set_thumbnail(url="attachment://f.png") # サムネイルを設定
                                await ctx.reply(embed=embed, file=discord.File(ii, "f.png"))
                            except Exception as e:
                                print(f"アイコン処理エラー: {e}")
                                await ctx.reply(embed=embed, content="サーバーアイコンの読み込みに失敗しました。")
                        else:
                            await ctx.reply(embed=embed) # アイコンがない場合はembedのみ送信

                    else:
                        await ctx.reply(f"サーバー情報を取得できませんでした。ステータスコード: {response.status}")
            except aiohttp.ClientError as e:
                await ctx.reply(f"サーバーへの接続に失敗しました: {e}")
            except json.JSONDecodeError as e:
                await ctx.reply(f"JSONデータの解析に失敗しました: {e}")
            except Exception as e:
                await ctx.reply(f"予期せぬエラーが発生しました: {e}")
                
    @game_monster.command(name="recipe", description="Minecraftのアイテムのレシピを取得します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def recipe(self, ctx: commands.Context, アイテム名: str):
        await ctx.defer()
        try:
            await ctx.reply(file=discord.File(f"data/Minecraft/{アイテム名}のレシピ.png"), content=f"「{アイテム名}」のレシピ")
        except:
            return await ctx.reply(embed=discord.Embed(title="そのようなアイテムはありません。", color=discord.Color.red()))

async def setup(bot):
    await bot.add_cog(GameCog(bot))