from discord.ext import commands
import discord
import traceback
import urllib
import sys
import time
import random
import aiosqlite
import logging
import asyncio
import re
from discord import Webhook
import io
import aiohttp
from motor import motor_asyncio as motor
import json

COOLDOWN_TIME = 10
user_last_message_time = {}

COOLDOWN_TIME2 = 3
user_last_message_time2 = {}

COOLDOWN_TIMEGC = 3
user_last_message_timegc = {}

user_last_message_sharknetwork = {}

class GlobalCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> GlobalCog")

    @commands.hybrid_group(name="globalchat", description="グローバルチャットを有効化します。", fallback="activate")
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def globalchat_activate(self, ctx: commands.Context, gcname: str = "sgc", password: str = "None", sgcの名前: str = "main"):
        if ctx.channel is None:
            await ctx.reply("このコマンドはチャンネル内でのみ使用できます。")
            return
        if gcname == "sgc":
            sdb = self.bot.async_db["Main"].SuperGlobalChat
            newdata = {
                "Channel": ctx.channel.id,
                "Guild": ctx.guild.id,
            }
            await sdb.replace_one(
                {"Channel": ctx.channel.id, "Guild": ctx.guild.id}, 
                newdata, 
                upsert=True
            )
            return await ctx.reply("sgcに参加しました。")
        elif gcname == "dsgc":
            sdb = self.bot.async_db["Main"].DebugSuperGlobalChat
            newdata = {
                "Channel": ctx.channel.id,
                "Guild": ctx.guild.id,
            }
            await sdb.replace_one(
                {"Channel": ctx.channel.id, "Guild": ctx.guild.id}, 
                newdata, 
                upsert=True
            )
            return await ctx.reply("dsgcに参加しました。")
        elif gcname == "csgc":
            await ctx.defer()
            sdb = self.bot.async_db["Main"].CustomSuperGlobalChatRooms
            newdata = {
                "Name": sgcの名前
            }
            await sdb.replace_one(
                {"Name": sgcの名前}, 
                newdata, 
                upsert=True
            )
            sdb = self.bot.async_db["Main"].CustomSuperGlobalChat
            newdata = {
                "Channel": ctx.channel.id,
                "Guild": ctx.guild.id,
                "Name": sgcの名前
            }
            await sdb.replace_one(
                {"Channel": ctx.channel.id, "Guild": ctx.guild.id}, 
                newdata, 
                upsert=True
            )
            ch = self.bot.get_channel(707158257818664991)
            dic = {}
            dic.update({"type": "shark-create"})
            dic.update({"name": f"{sgcの名前}"})
            jsondata = json.dumps(dic, ensure_ascii=False)
            await ch.send(jsondata)
            return await ctx.reply("カスタムsgcに参加しました。")
            
        async def handle_global_chat(ctx, password, gcname=None):
            db = self.bot.async_db["Main"].GlobalChat
            name = "main" if gcname is None else gcname
            new_data = {
                "Channel": ctx.channel.id,
                "Guild": ctx.guild.id,
                "Owner": ctx.author.id,
                "Name": name,
                "Password": password
            }

            try:
                profile = await db.find_one({"Name": name}, {"_id": False})
            except Exception as e:
                profile = None

            if profile is None:
                message = "メイングローバルチャットを作成しました。" if name == "main" else "個人グローバルチャットを作成しました。"
            else:
                if profile["Password"] != "None":
                    await ctx.author.send(embed=discord.Embed(title="パスワードを入力してください", color=discord.Color.red()))
                    def check(c):
                        return c.channel.id == ctx.author.dm_channel.id and not c.author.bot
                    try:
                        msg = await self.bot.wait_for("message", check=check, timeout=30)
                        if msg.content != profile["Password"]:
                            await ctx.author.send(embed=discord.Embed(title="認証に失敗しました。", color=discord.Color.red()))
                            return
                        else:
                            await ctx.author.send(embed=discord.Embed(title="認証に成功しました。", color=discord.Color.green()))
                    except:
                        return
                message = "メイングローバルチャットを有効化しました。" if name == "main" else "個人グローバルチャットを有効化しました。"

            await db.replace_one(
                {"Channel": ctx.channel.id, "Guild": ctx.guild.id}, 
                new_data, 
                upsert=True
            )
            await ctx.send(message)
        if gcname == None:
            await handle_global_chat(ctx, password)
        else:
            await handle_global_chat(ctx, password, gcname)

    @globalchat_activate.command(name="deactivate", description="グローバルチャットを無効化します。")
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def globalchat_deactivate(self, ctx):
        db = self.bot.async_db["Main"].GlobalChat
        await db.delete_one({
            "Channel": ctx.channel.id,
            "Guild": ctx.guild.id
        })
        sdb = self.bot.async_db["Main"].SuperGlobalChat
        await sdb.delete_one({
            "Channel": ctx.channel.id,
        })
        sdb = self.bot.async_db["Main"].DebugSuperGlobalChat
        await sdb.delete_one({
            "Channel": ctx.channel.id,
        })
        sdb = self.bot.async_db["Main"].CustomSuperGlobalChat
        await sdb.delete_one({
            "Channel": ctx.channel.id,
        })
        return await ctx.reply("グローバルチャットを削除しました。")
    
    @globalchat_activate.command(name="sgc", description="スーパーグローバルチャットについてみます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def globalchat_sgc(self, ctx: commands.Context):
        await ctx.defer()
        await ctx.reply(embed=discord.Embed(title="スーパーグローバルチャットの参加方法", description=f"`/globalchat activate gcname:sgc`で参加。", color=discord.Color.green()))

    @commands.Cog.listener("on_message")
    async def on_message_custom_sgc_getjson_makeroom(self, message):
        if message.channel.id == 707158257818664991:
            if message.author.id == 1322100616369147924:
                return
            try:
                dic = json.loads(message.content)
            except json.decoder.JSONDecodeError as e:
                return
            
            if "type" in dic and dic["type"] != "shark-create":
                return
            
            sdb = self.bot.async_db["Main"].CustomSuperGlobalChatRooms
            newdata = {
                "Name": dic["name"]
            }
            await sdb.replace_one(
                {"Name": dic["name"]}, 
                newdata, 
                upsert=True
            )

            await message.add_reaction("✅")

    @commands.Cog.listener("on_message")
    async def on_message_custom_sgc_getjson_getroom(self, message):
        if message.channel.id == 707158257818664991:
            if message.author.id == 1322100616369147924:
                return
            try:
                dic = json.loads(message.content)
            except json.decoder.JSONDecodeError as e:
                return
            
            if "type" in dic and dic["type"] != "shark-room_message":
                return
            
            sdb = self.bot.async_db["Main"].CustomSuperGlobalChat
            async for ch in sdb.find(filter={"Name": dic["Name"]}):
                async with aiohttp.ClientSession() as session:
                    try:
                        channel = self.bot.get_channel(ch["Channel"])
                    except:
                        continue
                    try:
                        if channel.id == message.channel.id:
                            continue
                    except:
                        continue
                    try:
                        ch_webhooks = await channel.webhooks()
                        whname = f"Shark-Global-main"
                        webhooks = discord.utils.get(ch_webhooks, name=whname)
                        if webhooks is None:
                            webhooks = await channel.create_webhook(name=f"{whname}")
                        webhook = Webhook.from_url(webhooks.url, session=session)
                    except:
                        continue
                    if "attachmentsUrl" in dic:
                        msg = discord.Embed(color=discord.Color.green()).set_image(url=urllib.parse.unquote(dic["attachmentsUrl"][0]))
                        try:
                            await webhook.send(f"{dic["content"].replace('@', '＠')}", avatar_url="https://media.discordapp.net/avatars/{}/{}.png?size=1024".format(dic["userId"], dic["userAvatar"]), username=f"({dic["userName"]}/{dic["userId"]})({dic["guildName"].lower().replace("discord", "*")}/{dic["channelName"].lower().replace("discord", "*")})", embed=msg)
                        except:
                            continue
                    else:
                        try:
                            await webhook.send(f"{dic["content"].replace('@', '＠')}", avatar_url="https://media.discordapp.net/avatars/{}/{}.png?size=1024".format(dic["userId"], dic["userAvatar"]), username=f"({dic["userName"]}/{dic["userId"]})({dic["guildName"].lower().replace("discord", "*")}/{dic["channelName"].lower().replace("discord", "*")})")
                        except:
                            continue
            await message.add_reaction("✅")

    @commands.Cog.listener("on_message")
    async def on_message_custom_sgc_sendroom(self, message: discord.Message):
        if message.author.bot:
            return
        if "!." in message.content:
            return
        if "discord.com" in message.content:
            return
        if "discord.gg" in message.content:
            return
        if "discord.gg" in message.content:
            return
        if "x.gd" in message.content:
            return
        if "<sound:" in message.content:
            return
        if type(message.channel) == discord.DMChannel:
            return
        db = self.bot.async_db["Main"].CustomSuperGlobalChat
        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        db_gmute = self.bot.async_db["Main"].GMute
        try:
            dbfind_gmute = await db_gmute.find_one({"User": message.author.id}, {"_id": False})
        except:
            pass
        if not dbfind_gmute is None:
            return
        sdb = self.bot.async_db["Main"].CustomSuperGlobalChat
        async for ch in sdb.find(filter={"Name": dbfind["Name"]}):
            async with aiohttp.ClientSession() as session:
                    try:
                        channel = self.bot.get_channel(ch["Channel"])
                    except:
                        continue
                    try:
                        if channel.id == message.channel.id:
                            continue
                    except:
                        continue
                    try:
                        ch_webhooks = await channel.webhooks()
                        whname = f"Shark-Global-main"
                        webhooks = discord.utils.get(ch_webhooks, name=whname)
                        if webhooks is None:
                            webhooks = await channel.create_webhook(name=f"{whname}")
                        webhook = Webhook.from_url(webhooks.url, session=session)
                    except:
                        continue
                    if not message.attachments == []:
                        if message.author.avatar:
                            msg = discord.Embed(color=discord.Color.green()).set_image(url=message.attachments[0].url)
                            try:
                                await webhook.send(f"{message.content.replace('@', '＠')}", avatar_url=message.author.avatar.url, username=f"({message.author.name}/{message.author.id})({message.guild.name.lower().replace("discord", "*")})", embed=msg)
                            except:
                                continue
                        else:
                            msg = discord.Embed(color=discord.Color.green()).set_image(url=message.attachments[0].url)
                            try:
                                await webhook.send(f"{message.content.replace('@', '＠')}", username=f"({message.author.name}/{message.author.id})({message.guild.name.lower().replace("discord", "*")})", embed=msg)
                            except:
                                continue
                    else:
                        if message.author.avatar:
                            try:
                                await webhook.send(f"{message.content.replace('@', '＠')}", avatar_url=message.author.avatar.url, username=f"({message.author.name}/{message.author.id})({message.guild.name.lower().replace("discord", "*")})")
                            except:
                                continue
                        else:
                            try:
                                await webhook.send(f"{message.content.replace('@', '＠')}", username=f"({message.author.name}/{message.author.id})({message.guild.name.lower().replace("discord", "*")})")
                            except:
                                continue
        dic = {}
        dic.update({"type": "shark-room_message"})
        dic.update({"Name": f"{dbfind["Name"]}"})
        dic.update({"userId": str(message.author.id)})
        dic.update({"userName": message.author.name})
        dic.update({"x-userGlobal_name": message.author.display_name})
        dic.update({"userDiscriminator": message.author.discriminator})
        if hasattr(message.author.avatar, 'key'):
            dic.update({"userAvatar": message.author.avatar.key})
        else:
            dic.update({"userAvatar": None})
        dic.update({"isBot": message.author.bot})
        dic.update({"guildId": str(message.guild.id)})
        dic.update({"guildName": message.guild.name})
        if hasattr(message.guild.icon, 'key'):
            dic.update({"guildIcon": message.guild.icon.key})
        else:
            dic.update({"guildIcon": None})
        dic.update({"channelId": str(message.channel.id)})
        dic.update({"channelName": message.channel.name})
        dic.update({"messageId": str(message.id)})
        dic.update({"content": message.content.replace('@', '＠')})

        if message.attachments != []: #添付ファイルが存在するとき
            arr = [] #リストを初期化
            for attachment in message.attachments: #添付ファイルをループ
                arr.append(attachment.url) #添付ファイルのURLを追加
            dic.update({"attachmentsUrl": arr})

        jsondata = json.dumps(dic, ensure_ascii=False)

        dic = {}

        await self.bot.get_channel(707158257818664991).send(jsondata)


    @commands.Cog.listener("on_message")
    async def on_message_sgc_getjson(self, message):
        if type(message.channel) == discord.DMChannel:
            return
        if message.channel.id == 707158257818664991:
            if message.author.id == 1322100616369147924:
                return
            try:
                dic = json.loads(message.content)
            except json.decoder.JSONDecodeError as e:
                return
            
            if "type" in dic and dic["type"] != "message":
                return

            await message.add_reaction("✅")
            db = self.bot.async_db["Main"].SuperGlobalChat
            async for ch in db.find():
                async with aiohttp.ClientSession() as session:
                    try:
                        channel = self.bot.get_channel(ch["Channel"])
                    except:
                        continue
                    try:
                        if channel.id == message.channel.id:
                            continue
                    except:
                        continue
                    try:
                        ch_webhooks = await channel.webhooks()
                        whname = f"Shark-Global-main"
                        webhooks = discord.utils.get(ch_webhooks, name=whname)
                        if webhooks is None:
                            webhooks = await channel.create_webhook(name=f"{whname}")
                        webhook = Webhook.from_url(webhooks.url, session=session)
                    except:
                        continue
                    if message.reference:
                        try:
                            rmsg = await message.channel.fetch_message(message.reference.message_id)
                            msg = discord.Embed(description=rmsg.content, color=discord.Color.green()).set_author(name=f"{rmsg.author.name} - {rmsg.author.id}")
                        except:
                            msg = None
                    else:
                        try:
                            reference_mid = dic["reference"] #返信元メッセージID

                            reference_message_content = "" #返信元メッセージ用変数を初期化
                            reference_message_author = "" #返信元ユーザータグ用変数を初期化
                            past_dic = None #返信元メッセージの辞書型リスト用変数を初期化
                            async for past_message in message.channel.history(limit=1000): #JSONチャンネルの過去ログ1000件をループ
                                try: #JSONのエラーを監視
                                    past_dic = json.loads(past_message.content) #過去ログのJSONを辞書型リストに変換
                                except json.decoder.JSONDecodeError as e: #JSON読み込みエラー→そもそもJSONでは無い可能性があるのでスルー
                                    continue
                                if "type" in past_dic and past_dic["type"] != "message": #メッセージでは無い時はスルー
                                    continue

                                if not "messageId" in past_dic: #キーにメッセージIDが存在しない時はスルー
                                    continue
                                
                                if str(past_dic["messageId"]) == str(reference_mid): #過去ログのメッセージIDが返信元メッセージIDと一致したとき
                                    reference_message_author = "{}#{}".format(past_dic["userName"],past_dic["userDiscriminator"]) #ユーザータグを取得
                                    reference_message_content = past_dic["content"] #メッセージ内容を取得
                                    if not "attachmentsUrl" in dic:
                                        msg = discord.Embed(description=reference_message_content, color=discord.Color.green()).set_author(name=reference_message_author).set_footer(text=f"mID:{dic["messageId"]}")
                                    else:
                                        msg = discord.Embed(description=reference_message_content, color=discord.Color.green()).set_author(name=reference_message_author).set_footer(text=f"mID:{dic["messageId"]}").set_image(url=urllib.parse.unquote(dic["attachmentsUrl"][0]))
                                    break
                        except:
                            if not "attachmentsUrl" in dic:
                                msg = discord.Embed(color=discord.Color.green()).set_footer(text=f"mID:{dic["messageId"]}")
                            else:
                                msg = discord.Embed(color=discord.Color.green()).set_footer(text=f"mID:{dic["messageId"]}").set_image(url=urllib.parse.unquote(dic["attachmentsUrl"][0]))
                    if not "attachmentsUrl" in dic:
                        try:
                            await webhook.send(f"{dic["content"].replace('@', '＠')}", avatar_url="https://media.discordapp.net/avatars/{}/{}.png?size=1024".format(dic["userId"], dic["userAvatar"]), username=f"({dic["userName"]}/{dic["userId"]})({dic["guildName"].lower().replace("discord", "*")}/{dic["channelName"].lower().replace("discord", "*")})", embed=msg)
                        except:
                            continue
                    else:
                        try:
                            await webhook.send(f"{dic["content"].replace('@', '＠')}", avatar_url="https://media.discordapp.net/avatars/{}/{}.png?size=1024".format(dic["userId"], dic["userAvatar"]), username=f"({dic["userName"]}/{dic["userId"]})({dic["guildName"].lower().replace("discord", "*")}/{dic["channelName"].lower().replace("discord", "*")})", embed=msg)
                        except:
                            continue

    @commands.Cog.listener("on_message")
    async def on_message_dsgc_getjson(self, message):
        if type(message.channel) == discord.DMChannel:
            return
        if message.channel.id == 707158343952629780:
            if message.author.id == 1322100616369147924:
                return
            try:
                dic = json.loads(message.content)
            except json.decoder.JSONDecodeError as e:
                return
            
            if "type" in dic and dic["type"] != "message":
                return

            db = self.bot.async_db["Main"].DebugSuperGlobalChat
            async for ch in db.find():
                async with aiohttp.ClientSession() as session:
                    try:
                        channel = self.bot.get_channel(ch["Channel"])
                    except:
                        continue
                    try:
                        if channel.id == message.channel.id:
                            continue
                    except:
                        continue
                    try:
                        ch_webhooks = await channel.webhooks()
                        whname = f"Shark-Global-main"
                        webhooks = discord.utils.get(ch_webhooks, name=whname)
                        if webhooks is None:
                            webhooks = await channel.create_webhook(name=f"{whname}")
                        webhook = Webhook.from_url(webhooks.url, session=session)
                    except:
                        continue
                    if message.reference:
                        try:
                            rmsg = await message.channel.fetch_message(message.reference.message_id)
                            msg = discord.Embed(description=rmsg.content, color=discord.Color.green()).set_author(name=f"{rmsg.author.name} - {rmsg.author.id}")
                        except:
                            msg = None
                    else:
                        try:
                            reference_mid = dic["reference"] #返信元メッセージID

                            reference_message_content = "" #返信元メッセージ用変数を初期化
                            reference_message_author = "" #返信元ユーザータグ用変数を初期化
                            past_dic = None #返信元メッセージの辞書型リスト用変数を初期化
                            async for past_message in message.channel.history(limit=1000): #JSONチャンネルの過去ログ1000件をループ
                                try: #JSONのエラーを監視
                                    past_dic = json.loads(past_message.content) #過去ログのJSONを辞書型リストに変換
                                except json.decoder.JSONDecodeError as e: #JSON読み込みエラー→そもそもJSONでは無い可能性があるのでスルー
                                    continue
                                if "type" in past_dic and past_dic["type"] != "message": #メッセージでは無い時はスルー
                                    continue

                                if not "messageId" in past_dic: #キーにメッセージIDが存在しない時はスルー
                                    continue
                                
                                if str(past_dic["messageId"]) == str(reference_mid): #過去ログのメッセージIDが返信元メッセージIDと一致したとき
                                    reference_message_author = "{}#{}".format(past_dic["userName"],past_dic["userDiscriminator"]) #ユーザータグを取得
                                    reference_message_content = past_dic["content"] #メッセージ内容を取得
                                    if not "attachmentsUrl" in dic:
                                        msg = discord.Embed(description=reference_message_content, color=discord.Color.green()).set_author(name=reference_message_author).set_footer(text=f"mID:{dic["messageId"]}")
                                    else:
                                        msg = discord.Embed(description=reference_message_content, color=discord.Color.green()).set_author(name=reference_message_author).set_footer(text=f"mID:{dic["messageId"]}").set_image(url=urllib.parse.unquote(dic["attachmentsUrl"][0]))
                                    break
                        except:
                            if not "attachmentsUrl" in dic:
                                msg = discord.Embed(color=discord.Color.green()).set_footer(text=f"mID:{dic["messageId"]}")
                            else:
                                msg = discord.Embed(color=discord.Color.green()).set_footer(text=f"mID:{dic["messageId"]}").set_image(url=urllib.parse.unquote(dic["attachmentsUrl"][0]))
                    if not "attachmentsUrl" in dic:
                        try:
                            await webhook.send(f"{dic["content"].replace('@', '＠')}", avatar_url="https://media.discordapp.net/avatars/{}/{}.png?size=1024".format(dic["userId"], dic["userAvatar"]), username=f"({dic["userName"]}/{dic["userId"]})({dic["guildName"].lower().replace("discord", "*")})", embed=msg)
                        except:
                            continue
                    else:
                        try:
                            await webhook.send(f"{dic["content"].replace('@', '＠')}", avatar_url="https://media.discordapp.net/avatars/{}/{}.png?size=1024".format(dic["userId"], dic["userAvatar"]), username=f"({dic["userName"]}/{dic["userId"]})({dic["guildName"].lower().replace("discord", "*")})", embed=msg)
                        except:
                            continue
            await message.add_reaction("<:CheckGreen:1341929972868055123>")

    async def get_reference_message(self, channel, reference_mid):
        """過去の返信元メッセージを取得"""
        async for past_message in channel.history(limit=1000):
            try:
                past_dic = json.loads(past_message.content)
                if past_dic.get("type") == "message" and past_dic.get("messageId") == reference_mid:
                    return {
                        "content": past_dic["content"],
                        "author": f"{past_dic['userName']}#{past_dic['userDiscriminator']}"
                    }
            except json.decoder.JSONDecodeError:
                continue
        return None

    @commands.Cog.listener("on_message")
    async def on_message_sgc(self, message):
        if message.author.bot:
            return
        if type(message.channel) == discord.DMChannel:
            return
        if "!." in message.content:
            return
        if "discord.com" in message.content:
            return
        if "discord.gg" in message.content:
            return
        if "discord.gg" in message.content:
            return
        if "x.gd" in message.content:
            return
        if "<sound:" in message.content:
            return
        if "niga" in message.content:
            return
        db = self.bot.async_db["Main"].SuperGlobalChat
        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        db_gmute = self.bot.async_db["Main"].GMute
        try:
            dbfind_gmute = await db_gmute.find_one({"User": message.author.id}, {"_id": False})
        except:
            pass
        if not dbfind_gmute is None:
            return
        current_time = time.time()
        last_message_time = user_last_message_time2.get(message.guild.id, 0)
        if current_time - last_message_time < COOLDOWN_TIME2:
            return
        user_last_message_time2[message.guild.id] = current_time
        async with aiohttp.ClientSession() as session:
            async for ch in db.find():
                try:
                    channel = self.bot.get_channel(ch["Channel"])
                except:
                    continue
                try:
                    if channel.id == message.channel.id:
                        continue
                except:
                    continue
                try:
                    ch_webhooks = await channel.webhooks()
                    whname = f"Shark-Global-main"
                    webhooks = discord.utils.get(ch_webhooks, name=whname)
                    if webhooks is None:
                        webhooks = await channel.create_webhook(name=f"{whname}")
                    webhook = Webhook.from_url(webhooks.url, session=session)
                    if message.reference:
                        if message.attachments == []:
                            try:
                                rmsg = await message.channel.fetch_message(message.reference.message_id)
                                msg = discord.Embed(description=rmsg.content, color=discord.Color.green()).set_author(name=f"{rmsg.author.name} - {rmsg.author.id}").set_footer(text=f"mID:{message.id}")
                            except:
                                msg = discord.Embed(color=discord.Color.green()).set_footer(text=f"mID:{message.id}")
                        else:
                            try:
                                rmsg = await message.channel.fetch_message(message.reference.message_id)
                                msg = discord.Embed(description=rmsg.content, color=discord.Color.green()).set_author(name=f"{rmsg.author.name} - {rmsg.author.id}").set_footer(text=f"mID:{message.id}").set_image(url=message.attachments[0].url)
                            except:
                                msg = discord.Embed(color=discord.Color.green()).set_footer(text=f"mID:{message.id}").set_image(url=message.attachments[0].url)
                    else:
                        if message.attachments == []:
                            msg = discord.Embed(color=discord.Color.green()).set_footer(text=f"mID:{message.id}")
                        else:
                            msg = discord.Embed(color=discord.Color.green()).set_footer(text=f"mID:{message.id}").set_image(url=message.attachments[0].url)
                except:
                    continue
                if message.attachments == []:
                    try:
                        if message.author.avatar == None:
                            await webhook.send(f"{message.content.replace('@', '＠').replace('.com/application-directory/', '')}", username=f"({message.author.name}/{message.author.id})({message.guild.name.lower().replace("discord", "*")})", embed=msg)
                        else:
                            await webhook.send(f"{message.content.replace('@', '＠').replace('.com/application-directory/', '')}", avatar_url=message.author.avatar.url, username=f"({message.author.name}/{message.author.id})({message.guild.name.lower().replace("discord", "*")})", embed=msg)
                    except:
                        continue
                else:
                    try:
                        if message.author.avatar == None:
                            await webhook.send(f"{message.content.replace('@', '＠').replace('.com/application-directory/', '')}", username=f"({message.author.name}/{message.author.id})({message.guild.name.lower().replace("discord", "*")})", embed=msg)
                        else:
                            await webhook.send(f"{message.content.replace('@', '＠').replace('.com/application-directory/', '')}", avatar_url=message.author.avatar.url, username=f"({message.author.name}/{message.author.id})({message.guild.name.lower().replace("discord", "*")})", embed=msg)
                    except:
                        continue
                await asyncio.sleep(2)
        try:
            dic = {}

            if message.reference:
                reference_msg = await message.channel.fetch_message(message.reference.message_id)#WebHookでも行けるの？いけるよ。ありがとう
                reference_mid = 0
                if reference_msg.application_id == self.bot.user.id:#bot自身宛の返信だった場合、
                    arr = reference_msg.embeds[0].footer.text

                    if "mID:" in arr: #「mID:」が含まれるとき
                        reference_mid = arr.replace("mID:","",1) #「mID:」を取り除いたものをメッセージIDとして取得
                elif reference_msg.application_id != self.bot.user.id:#自分自身以外の返信の場合
                    reference_mid = reference_msg.id
                dic.update({"reference": str(reference_mid)})

            dic.update({"type": "message"})
            dic.update({"userId": str(message.author.id)})
            dic.update({"userName": message.author.name})
            dic.update({"x-userGlobal_name": message.author.display_name})
            dic.update({"userDiscriminator": message.author.discriminator})
            if hasattr(message.author.avatar, 'key'):
                dic.update({"userAvatar": message.author.avatar.key})
            else:
                dic.update({"userAvatar": None})
            dic.update({"isBot": message.author.bot})
            dic.update({"guildId": str(message.guild.id)})
            dic.update({"guildName": message.guild.name})
            if hasattr(message.guild.icon, 'key'):
                dic.update({"guildIcon": message.guild.icon.key})
            else:
                dic.update({"guildIcon": None})
            dic.update({"channelId": str(message.channel.id)})
            dic.update({"channelName": message.channel.name})
            dic.update({"messageId": str(message.id)})
            dic.update({"content": message.content.replace('@', '＠')})

            if message.attachments != []: #添付ファイルが存在するとき
                arr = [] #リストを初期化
                for attachment in message.attachments: #添付ファイルをループ
                    arr.append(attachment.url) #添付ファイルのURLを追加
                dic.update({"attachmentsUrl": arr})

            jsondata = json.dumps(dic, ensure_ascii=False)

            dic = {}

            await self.bot.get_channel(707158257818664991).send(jsondata)

            await message.add_reaction("✅")
        except:
            return
        
    @commands.Cog.listener("on_message")
    async def on_message_dsgc(self, message):
        if message.author.bot:
            return
        if type(message.channel) == discord.DMChannel:
            return
        if "!." in message.content:
            return
        if "discord.com" in message.content:
            return
        if "discord.gg" in message.content:
            return
        if "discord.gg" in message.content:
            return
        if "x.gd" in message.content:
            return
        if "<sound:" in message.content:
            return
        if "niga" in message.content:
            return
        db = self.bot.async_db["Main"].DebugSuperGlobalChat
        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        db_gmute = self.bot.async_db["Main"].GMute
        try:
            dbfind_gmute = await db_gmute.find_one({"User": message.author.id}, {"_id": False})
        except:
            pass
        if not dbfind_gmute is None:
            return
        async for ch in db.find():
            async with aiohttp.ClientSession() as session:
                try:
                    channel = self.bot.get_channel(ch["Channel"])
                except:
                    continue
                try:
                    if channel.id == message.channel.id:
                        continue
                except:
                    continue
                ch_webhooks = await channel.webhooks()
                whname = f"Shark-Global-main"
                webhooks = discord.utils.get(ch_webhooks, name=whname)
                if webhooks is None:
                    webhooks = await channel.create_webhook(name=f"{whname}")
                webhook = Webhook.from_url(webhooks.url, session=session)
                try:
                    if message.reference:
                        if message.attachments == []:
                            try:
                                rmsg = await message.channel.fetch_message(message.reference.message_id)
                                msg = discord.Embed(description=rmsg.content, color=discord.Color.green()).set_author(name=f"{rmsg.author.name} - {rmsg.author.id}").set_footer(text=f"mID:{message.id}")
                            except:
                                msg = discord.Embed(color=discord.Color.green()).set_footer(text=f"mID:{message.id}")
                        else:
                            try:
                                rmsg = await message.channel.fetch_message(message.reference.message_id)
                                msg = discord.Embed(description=rmsg.content, color=discord.Color.green()).set_author(name=f"{rmsg.author.name} - {rmsg.author.id}").set_footer(text=f"mID:{message.id}").set_image(url=message.attachments[0].url)
                            except:
                                msg = discord.Embed(color=discord.Color.green()).set_footer(text=f"mID:{message.id}").set_image(url=message.attachments[0].url)
                    else:
                        if message.attachments == []:
                            msg = discord.Embed(color=discord.Color.green()).set_footer(text=f"mID:{message.id}")
                        else:
                            msg = discord.Embed(color=discord.Color.green()).set_footer(text=f"mID:{message.id}").set_image(url=message.attachments[0].url)
                except:
                    continue
                if message.attachments == []:
                    try:
                        if message.author.avatar == None:
                            await webhook.send(f"{message.content.replace('@', '＠')}", username=f"({message.author.name}/{message.author.id})({message.guild.name.lower().replace("discord", "*")})", embed=msg)
                        else:
                            await webhook.send(f"{message.content.replace('@', '＠')}", avatar_url=message.author.avatar.url, username=f"({message.author.name}/{message.author.id})({message.guild.name.lower().replace("discord", "*")})", embed=msg)
                    except:
                        continue
                else:
                    try:
                        if message.author.avatar == None:
                            await webhook.send(f"{message.content.replace('@', '＠')}\n{message.attachments[0].url}", username=f"({message.author.name}/{message.author.id})({message.guild.name.lower().replace("discord", "*")})", embed=msg)
                        else:
                            await webhook.send(f"{message.content.replace('@', '＠')}\n{message.attachments[0].url}", avatar_url=message.author.avatar.url, username=f"({message.author.name}/{message.author.id})({message.guild.name.lower().replace("discord", "*")})", embed=msg)
                    except:
                        continue
        try:
            dic = {}

            if message.reference:
                reference_msg = await message.channel.fetch_message(message.reference.message_id)#WebHookでも行けるの？いけるよ。ありがとう
                reference_mid = 0
                if reference_msg.application_id == self.bot.user.id:#bot自身宛の返信だった場合、
                    arr = reference_msg.embeds[0].footer.text

                    if "mID:" in arr: #「mID:」が含まれるとき
                        reference_mid = arr.replace("mID:","",1) #「mID:」を取り除いたものをメッセージIDとして取得
                elif reference_msg.application_id != self.bot.user.id:#自分自身以外の返信の場合
                    reference_mid = reference_msg.id
                dic.update({"reference": str(reference_mid)})

            dic.update({"type": "message"})
            dic.update({"userId": str(message.author.id)})
            dic.update({"userName": message.author.name})
            dic.update({"x-userGlobal_name": message.author.display_name})
            dic.update({"userDiscriminator": message.author.discriminator})
            if hasattr(message.author.avatar, 'key'):
                dic.update({"userAvatar": message.author.avatar.key})
            else:
                dic.update({"userAvatar": None})
            dic.update({"isBot": message.author.bot})
            dic.update({"guildId": str(message.guild.id)})
            dic.update({"guildName": message.guild.name})
            if hasattr(message.guild.icon, 'key'):
                dic.update({"guildIcon": message.guild.icon.key})
            else:
                dic.update({"guildIcon": None})
            dic.update({"channelId": str(message.channel.id)})
            dic.update({"channelName": message.channel.name})
            dic.update({"messageId": str(message.id)})
            dic.update({"content": message.content.replace('@', '＠')})

            if message.attachments != []: #添付ファイルが存在するとき
                arr = [] #リストを初期化
                for attachment in message.attachments: #添付ファイルをループ
                    arr.append(attachment.url) #添付ファイルのURLを追加
                dic.update({"attachmentsUrl": arr})

            jsondata = json.dumps(dic, ensure_ascii=False)

            dic = {}

            await self.bot.get_channel(707158343952629780).send(jsondata)

            await message.add_reaction("✅")
        except:
            return

    @commands.Cog.listener("on_message")
    async def on_message_gc(self, message: discord.Message):
        if message.author.bot:
            return
        if type(message.channel) == discord.DMChannel:
            return
        if "!." in message.content:
            return
        if "discord.com" in message.content:
            return
        if "discord.gg" in message.content:
            return
        if "discord.gg" in message.content:
            return
        if "x.gd" in message.content:
            return
        if "<sound:" in message.content:
            return
        current_time = time.time()
        last_message_time = user_last_message_timegc.get(message.guild.id, 0)
        if current_time - last_message_time < COOLDOWN_TIMEGC:
            return
        user_last_message_timegc[message.guild.id] = current_time
        db = self.bot.async_db["Main"].GlobalChat
        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        db_gmute = self.bot.async_db["Main"].GMute
        try:
            dbfind_gmute = await db_gmute.find_one({"User": message.author.id}, {"_id": False})
        except:
            pass
        if not dbfind_gmute is None:
            return
        async for ch in db.find(filter={'Name':f'{dbfind["Name"]}'}):
            async with aiohttp.ClientSession() as session:
                try:
                    channel = self.bot.get_channel(ch["Channel"])
                except:
                    continue
                try:
                    if channel.id == message.channel.id:
                        continue
                except:
                    continue
                try:
                    ch_webhooks = await channel.webhooks()
                    whname = f"Shark-Global-main"
                    webhooks = discord.utils.get(ch_webhooks, name=whname)
                    if webhooks is None:
                        webhooks = await channel.create_webhook(name=f"{whname}")
                    webhook = Webhook.from_url(webhooks.url, session=session)
                    if message.reference:
                        try:
                            rmsg = await message.channel.fetch_message(message.reference.message_id)
                            msg = discord.Embed(description=rmsg.content, color=discord.Color.green()).set_author(name=f"{rmsg.author.name} - {rmsg.author.id}")
                        except:
                            msg = None
                except:
                    continue
                else:
                    msg = None
                if message.attachments == []:
                    try:
                        if message.author.avatar == None:
                            await webhook.send(f"{message.content.replace('@', '＠')}", username=f"({message.guild.name})({message.author.name}/{message.author.id})", embed=msg)
                        else:
                            await webhook.send(f"{message.content.replace('@', '＠')}", avatar_url=message.author.avatar.url, username=f"({message.guild.name})({message.author.name}/{message.author.id})", embed=msg)
                    except:
                        continue
                else:
                    try:
                        if message.author.avatar == None:
                            await webhook.send(f"{message.content.replace('@', '＠')}\n{message.attachments[0].url}", username=f"({message.guild.name})({message.author.name}/{message.author.id})", embed=msg)
                        else:
                            await webhook.send(f"{message.content.replace('@', '＠')}\n{message.attachments[0].url}", avatar_url=message.author.avatar.url, username=f"({message.guild.name})({message.author.name}/{message.author.id})", embed=msg)
                    except:
                        continue

    @commands.hybrid_group(name="ads", description="宣伝グローバルチャットを有効化します。", fallback="activate")
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def ads_activate(self, ctx: commands.Context):
        await ctx.defer()
        db = self.bot.async_db["Main"].GlobalAds
        async for ch in db.find():
            async with aiohttp.ClientSession() as session:
                try:
                    channel = self.bot.get_channel(ch["Channel"])
                except:
                    continue
                try:
                    ch_webhooks = await channel.webhooks()
                    whname = f"Shark-Global-main"
                    webhooks = discord.utils.get(ch_webhooks, name=whname)
                    if webhooks is None:
                        webhooks = await channel.create_webhook(name=f"{whname}")
                    webhook = Webhook.from_url(webhooks.url, session=session)
                    await webhook.send(embed=discord.Embed(title=f"{ctx.guild.name}が参加したよ！よろしく！", color=discord.Color.green()), username="GlobalAds - Join")
                except:
                    continue
        await db.replace_one(
            {"Channel": ctx.channel.id}, 
            {"Channel": ctx.channel.id, "Guild": ctx.guild.id, "GuildName": ctx.guild.name}, 
            upsert=True
        )
        msg = await ctx.reply(embed=discord.Embed(title="広告を有効化しました。", description=f"ルール\n・エロ鯖を貼らない。\n・ショップ鯖を貼らない。\n・荒らし関連の鯖を貼らない。\n・連続で貼らない。\n・スパムをしない。\n以上です。", color=discord.Color.green()))

    @ads_activate.command(name="deactivate", description="宣伝グローバルチャットを無効化します。")
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def ads_deactivate(self, ctx):
        db = self.bot.async_db["Main"].GlobalAds
        await db.delete_one({
            "Channel": ctx.channel.id,
        })
        return await ctx.reply(embed=discord.Embed(title="広告を無効化しました。", color=discord.Color.green()))

    @commands.Cog.listener("on_message")
    async def on_message_ads(self, message: discord.Message):
        if message.author.bot:
            return
        if message.content == "!.ads on":
            return
        if message.content == "!.ads off":
            return
        if "niga" in message.content:
            return
        if type(message.channel) == discord.DMChannel:
            return
        db = self.bot.async_db["Main"].GlobalAds
        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        db_gmute = self.bot.async_db["Main"].GMute
        try:
            dbfind_gmute = await db_gmute.find_one({"User": message.author.id}, {"_id": False})
        except:
            pass
        if not dbfind_gmute is None:
            return
        current_time = time.time()
        last_message_time = user_last_message_time.get(message.guild.id, 0)
        if current_time - last_message_time < COOLDOWN_TIME:
            return
        user_last_message_time[message.guild.id] = current_time
        async for ch in db.find():
            async with aiohttp.ClientSession() as session:
                try:
                    channel = self.bot.get_channel(ch["Channel"])
                except:
                    continue
                try:
                    if channel.id == message.channel.id:
                        continue
                except:
                    continue
                try:
                    ch_webhooks = await channel.webhooks()
                    whname = f"Shark-Global-main"
                    webhooks = discord.utils.get(ch_webhooks, name=whname)
                    if webhooks is None:
                        webhooks = await channel.create_webhook(name=f"{whname}")
                    webhook = Webhook.from_url(webhooks.url, session=session)
                except:
                    continue
                if message.reference:
                    try:
                        rmsg = await message.channel.fetch_message(message.reference.message_id)
                        msg = discord.Embed(description=rmsg.content, color=discord.Color.green()).set_author(name=f"{rmsg.author.name} - {rmsg.author.id}")
                    except:
                        msg = None
                else:
                    msg = None
                if message.attachments == []:
                    try:
                        if message.author.avatar == None:
                            await webhook.send(f"{message.content.replace('@', '＠')}", username=f"({message.author.name}/{message.author.id})({message.guild.name.lower().replace("discord", "*")})", embed=msg)
                        else:
                            await webhook.send(f"{message.content.replace('@', '＠')}", username=f"({message.author.name}/{message.author.id})({message.guild.name.lower().replace("discord", "*")})", avatar_url=f"{message.author.avatar.url}", embed=msg)
                    except:
                        continue
                else:
                    try:
                        if message.author.avatar == None:
                            await webhook.send(f"{message.content.replace('@', '＠')}", username=f"({message.author.name}/{message.author.id})({message.guild.name.lower().replace("discord", "*")})", embed=msg)
                        else:
                            await webhook.send(f"{message.content.replace('@', '＠')}", username=f"({message.author.name}/{message.author.id})({message.guild.name.lower().replace("discord", "*")})", avatar_url=f"{message.author.avatar.url}", embed=msg)
                    except:
                        continue
                await asyncio.sleep(0.8)
        await message.add_reaction("✅")

    @commands.command(name="sgc_lookup", hidden=True)
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def sgc_lookup(self, ctx, message: str):
        m = await ctx.reply(embed=discord.Embed(title="<a:Loading:1333337181074493481> 参照中。。", color=discord.Color.yellow()))
        ch = self.bot.get_channel(707158257818664991)
        if re.match(r'https://discord.com/channels/[0-9]+/[0-9]+/[0-9]+', message):
            try:
                chi = self.bot.get_channel(int(message.split("/")[5]))
                msg = await chi.fetch_message(int(message.split("/")[6]))
                if type(ch) == discord.TextChannel:
                    async for past_message in ch.history(limit=1000): #JSONチャンネルの過去ログ1000件をループ
                        try: #JSONのエラーを監視
                            past_dic = json.loads(past_message.content) #過去ログのJSONを辞書型リストに変換
                        except json.decoder.JSONDecodeError as e: #JSON読み込みエラー→そもそもJSONでは無い可能性があるのでスルー
                            continue
                        if "type" in past_dic and past_dic["type"] != "message": #メッセージでは無い時はスルー
                            continue
                        if past_dic["content"] == msg.content:
                            return await m.edit(embed=discord.Embed(title="sgcメッセージの参照", description=f"{past_dic["content"]}", color=discord.Color.green()).set_author(name=f"{past_dic["userName"]}", icon_url="https://media.discordapp.net/avatars/{}/{}.png?size=1024".format(past_dic["userId"], past_dic["userAvatar"])))
                    return await m.edit(embed=discord.Embed(title="参照に失敗しました。", description="見つかりませんでした。", color=discord.Color.red()))
            except:
                return await m.edit(embed=discord.Embed(title="参照に失敗しました。", description="message.contentが空な可能性があります。", color=discord.Color.red()))
        else:
            return await m.edit(embed=discord.Embed(title="参照に失敗しました。", description="メッセージリンクを指定してください。", color=discord.Color.red()))

    def get_first_number_from_list(self, text_list):
        match = re.search(r"\d+", text_list, re.DOTALL)
        if match:
            return match.group(0)
        return None

    @commands.Cog.listener("on_message")
    async def on_message_sharknet(self, message: discord.Message):
        if message.author.bot:
            return
        if message.content == None:
            return
        if "discord.com" in message.content:
            return
        if "discord.gg" in message.content:
            return
        if "discord.gg" in message.content:
            return
        if "x.gd" in message.content:
            return
        if "<sound:" in message.content:
            return
        if type(message.channel) == discord.DMChannel:
            return
        db = self.bot.async_db["Main"].SharkNetwork
        try:
            dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        db_gmute = self.bot.async_db["Main"].GMute
        try:
            dbfind_gmute = await db_gmute.find_one({"User": message.author.id}, {"_id": False})
        except:
            pass
        if not dbfind_gmute is None:
            return
        current_time = time.time()
        last_message_time = user_last_message_sharknetwork.get(message.guild.id, 0)
        if current_time - last_message_time < 10:
            return
        user_last_message_sharknetwork[message.guild.id] = current_time
        embed = discord.Embed(title=f"匿名ユーザー", description=f"{message.content}", color=discord.Color.blue())
        if message.content.startswith(">>"):
            try:
                st = self.get_first_number_from_list(message.content.split(">>")[1].replace("\n", ""))
                suji = int(st[0])
                m = [msg async for msg in message.channel.history(limit=suji+1)]
                embed.add_field(name=f">>{suji}", value=f"{m[suji - 1].embeds[0].description}")
            except:
                pass
        if not message.attachments == []:
            file = await message.attachments[0].to_file()
            url = await self.bot.get_channel(1336216025837867182).send(file=file)
            embed.set_image(url=url.attachments[0].url)
        await message.delete()
        async for ch in db.find():
            try:
                channel = self.bot.get_channel(ch["Channel"])
            except:
                continue
            try:
                await channel.send(embed=embed)
                await asyncio.sleep(3)
            except:
                continue
        await self.bot.get_channel(1344481788000731198).send(f"名前: {message.author.display_name}\nID: {message.author.id}\nサーバー名: {message.guild.name}\nサーバーid: {message.guild.id}\n内容\n```{message.content}```")

    @commands.hybrid_group(name="sharknet", description="Twitterみたいなグローバルチャットを作成します。", fallback="activate")
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def sharknet_activate(self, ctx: commands.Context):
        await ctx.defer()
        db = self.bot.async_db["Main"].SharkNetwork
        await db.replace_one(
            {"Channel": ctx.channel.id}, 
            {"Channel": ctx.channel.id, "Guild": ctx.guild.id, "GuildName": ctx.guild.name}, 
            upsert=True
        )
        msg = await ctx.reply(embed=discord.Embed(title="SharkNetworkを有効化しました。", color=discord.Color.green()))

    @sharknet_activate.command(name="deactivate", description="Twitterみたいなグローバルチャットを削除します。")
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def sharknet_deactivate(self, ctx):
        db = self.bot.async_db["Main"].SharkNetwork
        await db.delete_one({
            "Channel": ctx.channel.id,
        })
        return await ctx.reply(embed=discord.Embed(title="SharkNetworkを無効化しました。", color=discord.Color.green()))

async def setup(bot):
    await bot.add_cog(GlobalCog(bot))