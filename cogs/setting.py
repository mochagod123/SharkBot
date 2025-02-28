from discord.ext import commands, oauth2
import discord
import traceback
import sys
from deep_translator import GoogleTranslator
import logging
import urllib
import datetime
import random, string
import asyncio
from collections import defaultdict
from functools import partial
import aiohttp
import re
from discord import Webhook
import time
import json

def randomname(n):
    randlst = [random.choice(string.ascii_letters + string.digits) for i in range(n)]
    return ''.join(randlst)


COOLDOWN_TIME_KEIGO = 5
cooldown_keigo_time = {}
COOLDOWN_TIME_TRANS = 3
cooldown_trans_time = {}
COOLDOWN_TIME_EXPAND = 5
cooldown_expand_time = {}

cooldown_engonly = {}

URL_REGEX = re.compile(r"https://discord.com/channels/(\d+)/(\d+)/(\d+)")

message_counts = defaultdict(int)
spam_threshold = 3  # しきい値 (例: 5回)
time_window = 5    # 秒数 (例: 10秒)

class SettingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("../Token.json") as tk:
            self.tkj = json.loads(tk.read())
            self.token_backup = self.tkj["Token"]
        print(f"init -> SettingCog")

    async def return_setting(self, ctx: commands.Context, name: str):
        db = self.bot.async_db["Main"][name]
        try:
            dbfind = await db.find_one({"Guild": ctx.guild.id}, {"_id": False})
        except:
            return False
        if dbfind is None:
            return False
        return True
    
    async def return_text(self, ctx: commands.Context, name: str):
        db = self.bot.async_db["Main"][name]
        try:
            dbfind = await db.find_one({"Guild": ctx.guild.id}, {"_id": False})
        except:
            return "標準"
        if dbfind is None:
            return "標準"
        return dbfind

    async def return_bool(self, tf: bool):
        if tf:
            return "<:ON:1333716076244238379>"
        return "<:OFF:1333716084364279838>"

    async def keigo_trans(self, kougo_text):
        return "現在封鎖中です。"
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
                    return response_data.get("content", "敬語に変換できませんでした。")

        except aiohttp.ClientError as e:
            return f"Network error occurred: {e}"
        except Exception as e:
            return f"An error occurred: {e}"

    @commands.Cog.listener("on_member_join")
    async def on_member_join_stickrole(self, member: discord.Member):
        g = self.bot.get_guild(member.guild.id)
        db = self.bot.async_db["Main"].StickRole
        try:
            dbfind = await db.find_one({"Guild": g.id, "User": member.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        try:
            r = member.guild.get_role(dbfind["Role"])
            await member.add_roles(r)
        except:
            return
    
    @commands.Cog.listener("on_message")
    async def on_message_englishonly(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.content:
            return
        db = self.bot.async_db["Main"].EnglishOnlyChannel
        try:
            dbfind = await db.find_one({"Guild": message.guild.id, "Channel": message.channel.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        current_time = time.time()
        last_message_time = cooldown_engonly.get(message.guild.id, 0)
        if current_time - last_message_time < 3:
            return
        cooldown_engonly[message.guild.id] = current_time
        try:
            if re.match(r"^[A-Za-z\s.,!?\"'()\-:;]+$", message.content):
                return
            else:
                await message.delete()
        except:
            return

    @commands.Cog.listener("on_message")
    async def on_message_keigo(self, message: discord.Message):
        if message.author.bot:
            return
        db = self.bot.async_db["Main"].KeigoChannel
        try:
            dbfind = await db.find_one({"Guild": message.guild.id, "Channel": message.channel.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        current_time = time.time()
        last_message_time = cooldown_keigo_time.get(message.guild.id, 0)
        if current_time - last_message_time < COOLDOWN_TIME_KEIGO:
            return
        cooldown_keigo_time[message.guild.id] = current_time
        try:
            if "@" in message.content:
                return await message.add_reaction("❌")
            text = await self.keigo_trans(message.content)
            await message.reply(text)
        except:
            return
        
    @commands.Cog.listener("on_message")
    async def on_message_trans(self, message: discord.Message):
        if message.author.bot:
            return
        db = self.bot.async_db["Main"].TranslateChannel
        try:
            dbfind = await db.find_one({"Guild": message.guild.id, "Channel": message.channel.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        current_time = time.time()
        last_message_time = cooldown_trans_time.get(message.guild.id, 0)
        if current_time - last_message_time < COOLDOWN_TIME_TRANS:
            return
        cooldown_trans_time[message.guild.id] = current_time
        try:
            loop = asyncio.get_event_loop()
            translator = GoogleTranslator(source="auto", target="en")
            translated_text = translator.translate(message.content)
            await message.reply(embed=discord.Embed(title=f"自動翻訳", description=f"```{translated_text}```", color=discord.Color.green()))
        except:
            return

    @commands.Cog.listener("on_message")
    async def on_message_robokasu(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.content:
            return
        db = self.bot.async_db["Main"].RobokasuChannel
        try:
            dbfind = await db.find_one({"Guild": message.guild.id, "Channel": message.channel.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        current_time = time.time()
        last_message_time = cooldown_keigo_time.get(message.guild.id, 0)
        if current_time - last_message_time < COOLDOWN_TIME_KEIGO:
            return
        cooldown_keigo_time[message.guild.id] = current_time
        try:
            text = message.content[:24].replace("\n", "").replace(" ", "").replace("　", "")
            await message.reply(embed=discord.Embed(title="ロボかす", color=discord.Color.blue()).set_image(url=f"https://www.sharkbot.xyz/api/robokasu?text={text}"))
        except:
            return

    @commands.Cog.listener("on_voice_state_update")
    async def on_voice_state_update_datetime(self, member, before, after):
        return
        if after.channel is not None:
            voice_channel = after.channel
            db = self.bot.async_db["Main"].VoiceTime
            try:
                dbfind = await db.find_one({"Channel": voice_channel.id}, {"_id": False})
            except:
                return
            if dbfind is None:
                return
            now = datetime.datetime.now()
            try:
                n = voice_channel.name.split("-")[0]
                await voice_channel.edit(name=f"{n}-{now.strftime("%m_%d_%H_%M_%S")}")
            except:
                n = voice_channel.name
                await voice_channel.edit(name=f"{n}-{now.strftime("%m_%d_%H_%M_%S")}")

    async def warn_user(self, message: discord.Message):
        db = self.bot.async_db["Main"].WarnUserScore
        try:
            dbfind = await db.find_one({"Guild": message.guild.id, "User": message.author.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            await db.replace_one(
                {"Guild": message.guild.id, "User": message.author.id}, 
                {"Guild": message.guild.id, "User": message.author.id, "Score": 1}, 
                upsert=True
            )
            try:
                await message.author.timeout(datetime.timedelta(minutes=3))
                return
            except:
                return
        else:
            await db.replace_one(
                {"Guild": message.guild.id, "User": message.author.id}, 
                {"Guild": message.guild.id, "User": message.author.id, "Score": dbfind["Score"] + 1}, 
                upsert=True
            )
            nowscore = dbfind["Score"] + 1
            if nowscore == 10:
                await db.replace_one(
                    {"Guild": message.guild.id, "User": message.author.id}, 
                    {"Guild": message.guild.id, "User": message.author.id, "Score": 0}, 
                    upsert=True
                )
                return await message.author.ban()
            else:
                try:
                    await message.author.timeout(datetime.timedelta(minutes=3))
                    return
                except:
                    return

    async def score_get(self, guild: discord.Guild, user: discord.User):
        db = self.bot.async_db["Main"].WarnUserScore
        try:
            dbfind = await db.find_one({"Guild": guild.id, "User": user.id}, {"_id": False})
        except:
            return 0
        if dbfind is None:
            return 0
        else:
            return dbfind["Score"]

    @commands.Cog.listener("on_message")
    async def on_message_invite_block(self, message: discord.Message):
        if message.author.bot:
            return
        if type(message.channel) == discord.DMChannel:
            return
        if message.author.guild_permissions.administrator:
            return
        INVITE_LINK_REGEX = r"(?:https?://)?(www\.)?(discord\.gg|discordapp\.com/invite)/[a-zA-Z0-9]+"
        if re.search(INVITE_LINK_REGEX, message.content):
            db = self.bot.async_db["Main"].InviteBlock
            try:
                dbfind = await db.find_one({"Guild": message.guild.id}, {"_id": False})
            except:
                return
            if dbfind is None:
                return
            channel_db = self.bot.async_db["Main"].UnBlockChannel
            try:
                channel_db_find = await channel_db.find_one({"Channel": message.channel.id}, {"_id": False})
            except:
                try:
                    await message.delete()
                except:
                    pass
                try:
                    await self.warn_user(message)
                    sc = await self.score_get(message.guild, message.author)
                    await message.channel.send(f"スコアが追加されました。\n現在のスコア: {sc}")
                except:
                    return
            if channel_db_find is None:
                try:
                    await message.delete()
                except:
                    pass
                try:
                    await self.warn_user(message)
                    sc = await self.score_get(message.guild, message.author)
                    await message.channel.send(f"スコアが追加されました。\n現在のスコア: {sc}")
                except:
                    return
                
    @commands.Cog.listener("on_message")
    async def on_message_token_block(self, message: discord.Message):
        if message.author.bot:
            return
        if type(message.channel) == discord.DMChannel:
            return
        if message.author.guild_permissions.administrator:
            return
        TOKEN_REGEX = r"[A-Za-z\d]{24}\.[\w-]{6}\.[\w-]{27}"
        if re.search(TOKEN_REGEX, message.content):
            db = self.bot.async_db["Main"].TokenBlock
            try:
                dbfind = await db.find_one({"Guild": message.guild.id}, {"_id": False})
            except:
                return
            if dbfind is None:
                return
            channel_db = self.bot.async_db["Main"].UnBlockChannel
            try:
                channel_db_find = await channel_db.find_one({"Channel": message.channel.id}, {"_id": False})
            except:
                try:
                    await message.delete()
                except:
                    pass
                try:
                    await self.warn_user(message)
                    sc = await self.score_get(message.guild, message.author)
                    await message.channel.send(f"スコアが追加されました。\n現在のスコア: {sc}")
                except:
                    return
            if channel_db_find is None:
                try:
                    await message.delete()
                except:
                    pass
                try:
                    await self.warn_user(message)
                    sc = await self.score_get(message.guild, message.author)
                    await message.channel.send(f"スコアが追加されました。\n現在のスコア: {sc}")
                except:
                    return

    @commands.Cog.listener("on_message")
    async def on_message_spam_block(self, message: discord.Message):
        if message.author.bot:
            return
        if type(message.channel) == discord.DMChannel:
            return
        if message.author.guild_permissions.administrator:
            return
        try:
            db = self.bot.async_db["Main"].SpamBlock
            try:
                dbfind = await db.find_one({"Guild": message.guild.id}, {"_id": False})
            except:
                return
            if dbfind is None:
                return
            message_counts[message.author.id] += 1

            # 指定した回数を超えたら警告
            if message_counts[message.author.id] >= spam_threshold:
                try:
                    await self.warn_user(message)
                except:
                    return
                print(f"SpamDetected: {message.author.id}/{message.author.display_name}")
                message_counts[message.author.id] = 0  # リセット

            # 指定時間後にカウントを減らす
            await asyncio.sleep(time_window)
            message_counts[message.author.id] -= 1
        except:
            return

    @commands.Cog.listener("on_message")
    async def on_message_expand(self, message: discord.Message):
        if message.author.bot:
            return  # ボットのメッセージは無視
        if not message.content:
            return  # ボットのメッセージは無視
        if type(message.channel) == discord.DMChannel:
            return
        db = self.bot.async_db["Main"].ExpandSettings
        try:
            dbfind = await db.find_one({"Guild": message.guild.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        current_time = time.time()
        last_message_time = cooldown_expand_time.get(message.guild.id, 0)
        if current_time - last_message_time < COOLDOWN_TIME_EXPAND:
            return
        cooldown_expand_time[message.guild.id] = current_time
        urls = URL_REGEX.findall(message.content)
        if not urls:
            return  # Discordメッセージリンクがなければ無視

        for guild_id, channel_id, message_id in urls:
            guild = self.bot.get_guild(int(guild_id))
            if not guild:
                continue  # ボットが参加していないサーバーなら無視

            channel = guild.get_channel(int(channel_id))
            if not channel or not isinstance(channel, discord.TextChannel):
                continue  # 有効なテキストチャンネルでなければ無視

            try:
                msg = await channel.fetch_message(int(message_id))  # メッセージ取得
                embed = discord.Embed(
                    description=msg.content if msg.content else "[メッセージなし]",
                    color=discord.Color.green(),
                    timestamp=msg.created_at
                )
                embed.set_author(name=msg.author.display_name, icon_url=msg.author.avatar.url)
                embed.add_field(name="元のメッセージ", value=f"[リンクを開く]({message.jump_url})", inline=False)
                embed.set_footer(text=f"{msg.guild.name} | {msg.channel.name}", icon_url=msg.guild.icon if msg.guild.icon else None)

                await message.channel.send(embed=embed)
            except:
                return
            return

    @commands.Cog.listener("on_member_update")
    async def on_member_update_timeout_removerole(self, before: discord.Member, after: discord.Member):
        if before.timed_out_until != after.timed_out_until:
            if after.timed_out_until is not None:  # タイムアウトされた
                db = self.bot.async_db["Main"].AutoRoleRemover
                try:
                    g = self.bot.get_guild(after.guild.id)
                    dbfind = await db.find_one({"Guild": g.id}, {"_id": False})
                except:
                    return
                if dbfind is None:
                    return
                role = after.guild.get_role(dbfind["Role"])
                if role in after.roles:
                    try:
                        await after.remove_roles(role)
                    except discord.Forbidden:
                        return
                    except discord.HTTPException as e:
                        return

    @commands.hybrid_group(name="api-setting", description="いろいろなAPIの設定をします。", fallback="x")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def api_setting_x(self, ctx: commands.Context):
        class send(discord.ui.Modal):
            def __init__(self, database) -> None:
                super().__init__(title="XAPIの設定", timeout=None)
                self.db = database
                self.key = discord.ui.TextInput(label="API Key",placeholder="APIKeyを入れる",style=discord.TextStyle.short,required=True)
                self.sec = discord.ui.TextInput(label="API SECRET",placeholder="APISECRETを入れる",style=discord.TextStyle.short,required=True)
                self.act = discord.ui.TextInput(label="Access Token",placeholder="AccessTokenを入れる",style=discord.TextStyle.short,required=True)
                self.acts = discord.ui.TextInput(label="Access Token Secret",placeholder="AccessTokenSecretを入れる",style=discord.TextStyle.short,required=True)
                self.beatoken = discord.ui.TextInput(label="Bearer Token",placeholder="Bearer Tokenを入れる",style=discord.TextStyle.short,required=True)
                self.add_item(self.key)
                self.add_item(self.sec)
                self.add_item(self.act)
                self.add_item(self.acts)
                self.add_item(self.beatoken)
            async def on_submit(self, interaction: discord.Interaction) -> None:
                db = self.db["Main"].XAPISetting
                await db.replace_one(
                    {"User": ctx.author.id}, 
                    {"User": ctx.author.id, "APIKey": self.key.value, "APISECRET": self.sec.value, "APITOKEN": self.act.value, "APITOKENSECRET": self.acts.value, "BearerToken": self.beatoken.value}, 
                    upsert=True
                )
                await interaction.response.send_message(embed=discord.Embed(title="XAPIの設定をしました。", color=discord.Color.green()), ephemeral=True)
        await ctx.interaction.response.send_modal(send(self.bot.async_db))

    def randomname(self, n):
        randlst = [random.choice(string.ascii_letters + string.digits) for i in range(n)]
        return ''.join(randlst)

    @api_setting_x.command(name="sharkbot", description="SharkBotのWebAPIKeyを取得します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(administrator=True)
    async def api_setting_sharkbot(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)
        tk = self.randomname(40)
        db = self.bot.async_db["Main"].AuthToken
        await db.replace_one(
            {"Guild": ctx.guild.id},
            {"Token": tk, "Guild": ctx.guild.id, "GuildName": ctx.guild.name, "Author": ctx.author.id, "AuthorName": ctx.author.name},
            upsert=True
        )
        await ctx.reply(f"発行されたWebAPIKey: `{tk}`", ephemeral=True)

    @commands.hybrid_group(name="settings", description="ようこそメッセージを設定します。", fallback="welcome")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def welcome_setting(self, ctx: commands.Context, 有効にするか: bool):
        if 有効にするか:
            class send(discord.ui.Modal):
                def __init__(self, database) -> None:
                    super().__init__(title="ようこそメッセージの設定", timeout=None)
                    self.db = database
                    self.etitle = discord.ui.TextInput(label="タイトル",placeholder="タイトルを入力",style=discord.TextStyle.long,required=True)
                    self.desc = discord.ui.TextInput(label="説明",placeholder="説明を入力",style=discord.TextStyle.long,required=True)
                    self.add_item(self.etitle)
                    self.add_item(self.desc)
                async def on_submit(self, interaction: discord.Interaction) -> None:
                    db = self.db["Main"].WelcomeMessage
                    await db.replace_one(
                        {"Channel": ctx.channel.id, "Guild": ctx.guild.id}, 
                        {"Channel": ctx.channel.id, "Guild": ctx.guild.id, "Title": self.etitle.value, "Description": self.desc.value}, 
                        upsert=True
                    )
                    await interaction.response.send_message(embed=discord.Embed(title="ウェルカムメッセージを有効化しました。", color=discord.Color.green()))
            await ctx.interaction.response.send_modal(send(self.bot.async_db))
        else:
            db = self.bot.async_db["Main"].WelcomeMessage
            result = await db.delete_one({
                "Channel": ctx.channel.id,
            })
            await ctx.reply(embed=discord.Embed(title="ウェルカムメッセージを無効化しました。", color=discord.Color.green()))

    @welcome_setting.command(name="goodbye", description="さようならメッセージを設定します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def goodbye_message(self, ctx, 有効にするか: bool):
        if 有効にするか:
            class send(discord.ui.Modal):
                def __init__(self, database) -> None:
                    super().__init__(title="さようならメッセージの設定", timeout=None)
                    self.db = database
                    self.etitle = discord.ui.TextInput(label="タイトル",placeholder="タイトルを入力",style=discord.TextStyle.long,required=True)
                    self.desc = discord.ui.TextInput(label="説明",placeholder="説明を入力",style=discord.TextStyle.long,required=True)
                    self.add_item(self.etitle)
                    self.add_item(self.desc)
                async def on_submit(self, interaction: discord.Interaction) -> None:
                    db = self.db["Main"].GoodByeMessage
                    await db.replace_one(
                        {"Channel": ctx.channel.id, "Guild": ctx.guild.id}, 
                        {"Channel": ctx.channel.id, "Guild": ctx.guild.id, "Title": self.etitle.value, "Description": self.desc.value}, 
                        upsert=True
                    )
                    await interaction.response.send_message(embed=discord.Embed(title="さようならメッセージを有効化しました。", color=discord.Color.green()))
            await ctx.interaction.response.send_modal(send(self.bot.async_db))
        else:
            db = self.bot.async_db["Main"].GoodByeMessage
            result = await db.delete_one({
                "Channel": ctx.channel.id,
            })
            await ctx.reply(embed=discord.Embed(title="さようならメッセージを無効化しました。", color=discord.Color.green()))

    @welcome_setting.command(name="stickrole", description="ロールをくっつけます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def stick_role(self, ctx, ユーザー: discord.User, ロール: discord.Role = None):
        db = self.bot.async_db["Main"].StickRole
        if ロール:
            await db.replace_one(
                {"Guild": ctx.guild.id, "User": ユーザー.id}, 
                {"Guild": ctx.guild.id, "User": ユーザー.id, "Role": ロール.id}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title="ユーザーにロールをくっつけました。", description=f"ユーザー: `{ロール.name}`\nロール: `{ロール.name}`", color=discord.Color.green()))
        else:
            result = await db.delete_one({"Guild": ctx.guild.id, "User": ユーザー.id})
            if result.deleted_count == 0:
                return await ctx.reply(embed=discord.Embed(title="その人にロールはくっついていません。", color=discord.Color.red()))
            await ctx.reply(embed=discord.Embed(title="ロールを剝がしました。", color=discord.Color.red()))

    @welcome_setting.command(name="lock-message", description="メッセージを固定します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def lock_message(self, ctx: commands.Context, 有効にするか: bool):
        if 有効にするか:
            class send(discord.ui.Modal):
                def __init__(self, database) -> None:
                    super().__init__(title="メッセージ固定の設定", timeout=None)
                    self.db = database
                    self.etitle = discord.ui.TextInput(label="タイトル",placeholder="タイトルを入力",style=discord.TextStyle.long,required=True)
                    self.desc = discord.ui.TextInput(label="説明",placeholder="説明を入力",style=discord.TextStyle.long,required=True)
                    self.add_item(self.etitle)
                    self.add_item(self.desc)
                async def on_submit(self, interaction: discord.Interaction) -> None:
                    msg = await interaction.channel.send(embed=discord.Embed(title=self.etitle.value, description=self.desc.value, color=discord.Color.random()))
                    db = self.db["Main"].LockMessage
                    await db.replace_one(
                        {"Channel": ctx.channel.id, "Guild": ctx.guild.id}, 
                        {"Channel": ctx.channel.id, "Guild": ctx.guild.id, "Title": self.etitle.value, "Desc": self.desc.value, "MessageID": msg.id}, 
                        upsert=True
                    )
                    await interaction.response.send_message(embed=discord.Embed(title="メッセージ固定を有効化しました。", color=discord.Color.green()), ephemeral=True)
            await ctx.interaction.response.send_modal(send(self.bot.async_db))
        else:
            db = self.bot.async_db["Main"].LockMessage
            result = await db.delete_one({
                "Channel": ctx.channel.id,
            })
            if result.deleted_count == 0:
                return await ctx.reply(embed=discord.Embed(title="メッセージ固定は有効化されていません。", color=discord.Color.red()))    
            await ctx.reply(embed=discord.Embed(title="メッセージ固定を無効化しました。", color=discord.Color.red()))

    @welcome_setting.command(name="keigo-channel", description="発言すると自動的に敬語にするかどうか")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def keigo_channel(self, ctx, 有効にするか: bool):
        db = self.bot.async_db["Main"].KeigoChannel
        if 有効にするか:
            await db.replace_one(
                {"Guild": ctx.guild.id, "Channel": ctx.channel.id}, 
                {"Guild": ctx.guild.id, "Channel": ctx.channel.id}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title="敬語チャンネルを設定しました。", color=discord.Color.green()))
        else:
            result = await db.delete_one({"Guild": ctx.guild.id, "Channel": ctx.channel.id})
            if result.deleted_count == 0:
                return await ctx.reply(embed=discord.Embed(title="ここは敬語チャンネルではありません。", color=discord.Color.red()))
            await ctx.reply(embed=discord.Embed(title="敬語チャンネルを削除しました。", color=discord.Color.red()))

    @welcome_setting.command(name="trans-channel", description="自動的に翻訳します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def trans_channel(self, ctx, 有効にするか: bool):
        db = self.bot.async_db["Main"].TranslateChannel
        if 有効にするか:
            await db.replace_one(
                {"Guild": ctx.guild.id, "Channel": ctx.channel.id}, 
                {"Guild": ctx.guild.id, "Channel": ctx.channel.id}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title="翻訳チャンネルを設定しました。", color=discord.Color.green()))
        else:
            result = await db.delete_one({"Guild": ctx.guild.id, "Channel": ctx.channel.id})
            if result.deleted_count == 0:
                return await ctx.reply(embed=discord.Embed(title="ここは翻訳チャンネルではありません。", color=discord.Color.red()))
            await ctx.reply(embed=discord.Embed(title="翻訳チャンネルを削除しました。", color=discord.Color.red()))

    @welcome_setting.command(name="robokasu-channel", description="ロボかすを自動的に作成します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def robokasu_channel(self, ctx, 有効にするか: bool):
        db = self.bot.async_db["Main"].RobokasuChannel
        if 有効にするか:
            await db.replace_one(
                {"Guild": ctx.guild.id, "Channel": ctx.channel.id}, 
                {"Guild": ctx.guild.id, "Channel": ctx.channel.id}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title="ロボかすチャンネルを設定しました。", color=discord.Color.green()))
        else:
            result = await db.delete_one({"Guild": ctx.guild.id, "Channel": ctx.channel.id})
            if result.deleted_count == 0:
                return await ctx.reply(embed=discord.Embed(title="ここはロボかすチャンネルではありません。", color=discord.Color.red()))
            await ctx.reply(embed=discord.Embed(title="ロボかすチャンネルを削除しました。", color=discord.Color.red()))

    @welcome_setting.command(name="register", description="サーバー掲示板にサーバーを掲載します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def register_server(self, ctx: commands.Context, 説明: str):
        if ctx.guild.icon == None:
            return await ctx.reply("サーバー掲示板に乗せるにはアイコンを設定する必要があります。")
        db = self.bot.async_db["Main"].Register
        inv = await ctx.channel.create_invite()
        await db.replace_one(
            {"Guild": ctx.guild.id}, 
            {"Guild": ctx.guild.id, "Name": ctx.guild.name, "Description": 説明, "Invite": inv.url, "Icon": ctx.guild.icon.url}, 
            upsert=True
        )
        await ctx.reply(embed=discord.Embed(title="サーバーを掲載しました。", color=discord.Color.green()))

    @welcome_setting.command(name="management", description="運営を募集します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def management_server(self, ctx: commands.Context, 仕事内容: str):
        await ctx.defer()
        if ctx.guild.icon == None:
            return await ctx.reply("運営募集掲示板に乗せるにはアイコンを設定する必要があります。")
        db = self.bot.async_db["Main"].ManagementRegister
        inv = await ctx.channel.create_invite()
        await db.replace_one(
            {"Guild": ctx.guild.id}, 
            {"Guild": ctx.guild.id, "Name": ctx.guild.name, "Description": 仕事内容, "Invite": inv.url, "Icon": ctx.guild.icon.url}, 
            upsert=True
        )
        await ctx.reply(embed=discord.Embed(title="サーバーを運営募集掲示板に掲載しました。", color=discord.Color.green()))

    @welcome_setting.command(name="emoji-translate", description="絵文字をつけると翻訳します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def emoji_translate(self, ctx: commands.Context, 有効にするか: bool):
        db = self.bot.async_db["Main"].EmojiTranslate
        if 有効にするか:
            await db.replace_one(
                {"Guild": ctx.guild.id}, 
                {"Guild": ctx.guild.id}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title="絵文字翻訳を有効化しました。", color=discord.Color.green()))
        else:
            result = await db.delete_one({"Guild": ctx.guild.id})
            if result.deleted_count == 0:
                return await ctx.reply(embed=discord.Embed(title="絵文字翻訳は無効です。", color=discord.Color.red()))
            await ctx.reply(embed=discord.Embed(title="絵文字翻訳を無効化しました。", color=discord.Color.red()))

    @welcome_setting.command(name="prefix", description="Prefixを設定します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def setting_prefix(self, ctx: commands.Context, prefix: str):
        await ctx.defer()
        db = self.bot.async_db["Main"].CustomPrefixBot
        await db.replace_one(
            {"Guild": ctx.guild.id}, 
            {"Guild": ctx.guild.id, "Prefix": prefix}, 
            upsert=True
        )
        await ctx.reply(embed=discord.Embed(title="Prefixを設定しました。", description=f"「{prefix}」", color=discord.Color.green()))

    @welcome_setting.command(name="score", description="スコアをチェックします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def setting_score(self, ctx: commands.Context, ユーザー: discord.User):
        class ScoreSettingView(discord.ui.View):
            def __init__(self, db, ユーザーs):
                super().__init__(timeout=None)
                self.db = db
                self.ユーザー = ユーザーs

            @discord.ui.select(
                cls=discord.ui.Select,
                placeholder="スコアに関しての設定",
                options=[
                    discord.SelectOption(label="スコアを9に設定"),
                    discord.SelectOption(label="スコアを8に設定"),
                    discord.SelectOption(label="スコアを5に設定"),
                    discord.SelectOption(label="スコアを3に設定"),
                    discord.SelectOption(label="スコアをクリア"),
                ]
            )
            async def select(self, interaction: discord.Interaction, select: discord.ui.Select):
                if interaction.user.id == ctx.author.id:
                    if "スコアを8に設定" == select.values[0]:
                        db = self.db.WarnUserScore
                        try:
                            dbfind = await db.find_one({"Guild": interaction.guild.id, "User": self.ユーザー.id}, {"_id": False})
                        except:
                            return
                        if dbfind is None:
                            await db.replace_one(
                                {"Guild": interaction.guild.id, "User": self.ユーザー.id}, 
                                {"Guild": interaction.guild.id, "User": self.ユーザー.id, "Score": 8}, 
                                upsert=True
                            )
                        else:
                            await db.replace_one(
                                {"Guild": interaction.guild.id, "User": self.ユーザー.id}, 
                                {"Guild": interaction.guild.id, "User": self.ユーザー.id.id, "Score": 8}, 
                                upsert=True
                            )
                        await interaction.response.send_message("スコアを8に設定しました。", ephemeral=True)
                    elif "スコアを5に設定" == select.values[0]:
                        db = self.db.WarnUserScore
                        try:
                            dbfind = await db.find_one({"Guild": interaction.guild.id, "User": self.ユーザー.id}, {"_id": False})
                        except:
                            return
                        if dbfind is None:
                            await db.replace_one(
                                {"Guild": interaction.guild.id, "User": self.ユーザー.id}, 
                                {"Guild": interaction.guild.id, "User": self.ユーザー.id, "Score": 5}, 
                                upsert=True
                            )
                        else:
                            await db.replace_one(
                                {"Guild": interaction.guild.id, "User": self.ユーザー.id}, 
                                {"Guild": interaction.guild.id, "User": self.ユーザー.id, "Score": 5}, 
                                upsert=True
                            )
                        await interaction.response.send_message("スコアを5に設定しました。", ephemeral=True)
                    elif "スコアを3に設定" == select.values[0]:
                        db = self.db.WarnUserScore
                        try:
                            dbfind = await db.find_one({"Guild": interaction.guild.id, "User": self.ユーザー.id}, {"_id": False})
                        except:
                            return
                        if dbfind is None:
                            await db.replace_one(
                                {"Guild": interaction.guild.id, "User": self.ユーザー.id}, 
                                {"Guild": interaction.guild.id, "User": self.ユーザー.id, "Score": 3}, 
                                upsert=True
                            )
                        else:
                            await db.replace_one(
                                {"Guild": interaction.guild.id, "User": self.ユーザー.id}, 
                                {"Guild": interaction.guild.id, "User": self.ユーザー.id, "Score": 3}, 
                                upsert=True
                            )
                        await interaction.response.send_message("スコアを3に設定しました。", ephemeral=True)
                    elif "スコアを9に設定" == select.values[0]:
                        db = self.db.WarnUserScore
                        try:
                            dbfind = await db.find_one({"Guild": interaction.guild.id, "User": self.ユーザー.id}, {"_id": False})
                        except:
                            return
                        if dbfind is None:
                            await db.replace_one(
                                {"Guild": interaction.guild.id, "User": self.ユーザー.id}, 
                                {"Guild": interaction.guild.id, "User": self.ユーザー.id, "Score": 9}, 
                                upsert=True
                            )
                        else:
                            await db.replace_one(
                                {"Guild": interaction.guild.id, "User": self.ユーザー.id}, 
                                {"Guild": interaction.guild.id, "User": self.ユーザー.id, "Score": 9}, 
                                upsert=True
                            )
                        await interaction.response.send_message("スコアを9に設定しました。", ephemeral=True)
                    elif "スコアをクリア" == select.values[0]:
                        db = self.db.WarnUserScore
                        result = await db.delete_one({"Guild": interaction.guild.id, "User": self.ユーザー.id})
                        await interaction.response.send_message("スコアをクリアしました。", ephemeral=True)
        sc = await self.score_get(ctx.guild, ユーザー)
        await ctx.reply(embed=discord.Embed(title=f"{ユーザー.display_name}さんのスコア", description=f"スコア: {sc}", color=discord.Color.green()), view=ScoreSettingView(self.bot.async_db["Main"], ユーザー))

    @welcome_setting.command(name="automod", description="AutoModを設定します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def setting_automod(self, ctx: commands.Context):
        class AutoModView(discord.ui.View):
            def __init__(self, db):
                super().__init__(timeout=None)
                self.db = db

            @discord.ui.select(
                cls=discord.ui.Select,
                placeholder="設定するAutoModを選択",
                options=[
                    discord.SelectOption(label="招待リンク"),
                    discord.SelectOption(label="Token"),
                    discord.SelectOption(label="スパム"),
                    discord.SelectOption(label="ブロックしないチャンネルの設定"),
                    discord.SelectOption(label="ブロックしないチャンネルの解除"),
                    discord.SelectOption(label="無効化"),
                ]
            )
            async def select(self, interaction: discord.Interaction, select: discord.ui.Select):
                if interaction.user.id == ctx.author.id:
                    if "招待リンク" == select.values[0]:
                        dbs = self.db.InviteBlock
                        await dbs.replace_one(
                            {"Guild": ctx.guild.id}, 
                            {"Guild": ctx.guild.id}, 
                            upsert=True
                        )
                    elif "Token" == select.values[0]:
                        dbs = self.db.TokenBlock
                        await dbs.replace_one(
                            {"Guild": ctx.guild.id}, 
                            {"Guild": ctx.guild.id}, 
                            upsert=True
                        )
                    elif "スパム" == select.values[0]:
                        dbs = self.db.SpamBlock
                        await dbs.replace_one(
                            {"Guild": ctx.guild.id}, 
                            {"Guild": ctx.guild.id}, 
                            upsert=True
                        )
                    elif "ブロックしないチャンネルの設定" == select.values[0]:
                        dbs = self.db.UnBlockChannel
                        await dbs.replace_one(
                            {"Guild": ctx.guild.id, "Channel": ctx.channel.id}, 
                            {"Guild": ctx.guild.id, "Channel": ctx.channel.id}, 
                            upsert=True
                        )
                        return await interaction.response.send_message(f"ブロックしないチャンネルの設定をしました。\n{interaction.channel.mention}", ephemeral=True)
                    elif "ブロックしないチャンネルの解除" == select.values[0]:
                        dbs = self.db.UnBlockChannel
                        await dbs.delete_one({"Channel": ctx.channel.id})
                        return await interaction.response.send_message(f"ブロックしないチャンネルの解除をしました。\n{interaction.channel.mention}", ephemeral=True)
                    elif "無効化" == select.values[0]:
                        dbs = self.db.InviteBlock
                        await dbs.delete_one({"Guild": ctx.guild.id})
                        dbs = self.db.TokenBlock
                        await dbs.delete_one({"Guild": ctx.guild.id})
                        dbs = self.db.SpamBlock
                        await dbs.delete_one({"Guild": ctx.guild.id})
                        return await interaction.response.send_message(f"無効化しました。", ephemeral=True)
                    await interaction.response.send_message(f"AutoModを有効にしました。\n{select.values[0]}", ephemeral=True)
                else:
                    await interaction.response.send_message(f"あなたはコマンドの実行者ではありません。", ephemeral=True)
        await ctx.reply(view=AutoModView(self.bot.async_db["Main"]), embed=discord.Embed(title="AutoModの設定", color=discord.Color.blue()))

    @welcome_setting.command(name="edit-embed", description="Botの投稿したEmbedを書き換えます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def setting_edit_embed(self, ctx: commands.Context, メッセージ: discord.Message, embed: discord.Message):
        if not embed.author.id == 1322100616369147924:
            return await ctx.reply(embed=discord.Embed(title="SharkBotの発言したEmbedではないため、\n編集出来ません。", color=discord.Color.green()))
        if not メッセージ.author.id == 1322100616369147924:
            return await ctx.reply(embed=discord.Embed(title="SharkBotの発言したEmbedではないため、\n編集出来ません。", color=discord.Color.green()))
        if embed.embeds[0].footer.text == f"この埋め込みは、{ctx.author.name}によって作成されました。":
            await メッセージ.edit(embed=embed.embeds[0])
            await ctx.reply(embed=discord.Embed(title="Embedを編集しました。", color=discord.Color.green()), ephemeral=True)
        else:
            await ctx.reply(embed=discord.Embed(title="あなたの作成したEmbedのみ使えます。", color=discord.Color.green()), ephemeral=True)

    @welcome_setting.command(name="make-embed", description="Embedを作成します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def setting_make_embed(self, ctx: commands.Context):
        try:
            class send(discord.ui.Modal):
                def __init__(self) -> None:
                    super().__init__(title="埋め込みの作成", timeout=None)
                    self.etitle = discord.ui.TextInput(label="タイトル",placeholder="タイトルを入力",style=discord.TextStyle.long,required=True)
                    self.desc = discord.ui.TextInput(label="説明",placeholder="説明を入力",style=discord.TextStyle.long,required=True)
                    self.col = discord.ui.TextInput(label="色",placeholder="色を入力。\n255,255,255って感じで書く。",style=discord.TextStyle.short,required=False)
                    self.ilink = discord.ui.TextInput(label="画像",placeholder="画像リンクを入れる",style=discord.TextStyle.short,required=False)
                    self.add_item(self.etitle)
                    self.add_item(self.desc)
                    self.add_item(self.col)
                    self.add_item(self.ilink)
                async def on_submit(self, interaction: discord.Interaction) -> None:
                    await interaction.response.defer(ephemeral=True)
                    if not self.ilink.value:
                        if self.col.value:
                            try:
                                c = self.col.value.split(",")
                                await interaction.channel.send(embed=discord.Embed(title=f"{self.etitle.value}", description=f"{self.desc.value}", color=discord.Color.from_rgb(int(c[0]), int(c[1]), int(c[2]))).set_footer(text=f"この埋め込みは、{ctx.author.name}によって作成されました。"))
                            except:
                                await interaction.channel.send(embed=discord.Embed(title=f"{self.etitle.value}", description=f"{self.desc.value}").set_footer(text=f"この埋め込みは、{ctx.author.name}によって作成されました。"))
                        else:
                            await interaction.channel.send(embed=discord.Embed(title=f"{self.etitle.value}", description=f"{self.desc.value}").set_footer(text=f"この埋め込みは、{ctx.author.name}によって作成されました。"))
                    else:
                        try:
                            if self.col.value:
                                try:
                                    c = self.col.value.split(",")
                                    await interaction.channel.send(embed=discord.Embed(title=f"{self.etitle.value}", description=f"{self.desc.value}", color=discord.Color.from_rgb(int(c[0]), int(c[1]), int(c[2]))).set_footer(text=f"この埋め込みは、{ctx.author.name}によって作成されました。").set_image(url=self.ilink.value))
                                except:
                                    await interaction.channel.send(embed=discord.Embed(title=f"{self.etitle.value}", description=f"{self.desc.value}").set_footer(text=f"この埋め込みは、{ctx.author.name}によって作成されました。").set_image(url=self.ilink.value))
                            else:
                                await interaction.channel.send(embed=discord.Embed(title=f"{self.etitle.value}", description=f"{self.desc.value}").set_footer(text=f"この埋め込みは、{ctx.author.name}によって作成されました。").set_image(url=self.ilink.value))
                        except:
                            if self.col.value:
                                try:
                                    c = self.col.value.split(",")
                                    await interaction.channel.send(embed=discord.Embed(title=f"{self.etitle.value}", description=f"{self.desc.value}", color=discord.Color.from_rgb(int(c[0]), int(c[1]), int(c[2]))).set_footer(text=f"この埋め込みは、{ctx.author.name}によって作成されました。"))
                                except:
                                    await interaction.channel.send(embed=discord.Embed(title=f"{self.etitle.value}", description=f"{self.desc.value}").set_footer(text=f"この埋め込みは、{ctx.author.name}によって作成されました。"))
                            else:
                                await interaction.channel.send(embed=discord.Embed(title=f"{self.etitle.value}", description=f"{self.desc.value}").set_footer(text=f"この埋め込みは、{ctx.author.name}によって作成されました。"))
                    await interaction.followup.send(embed=discord.Embed(title="埋め込みを作成しました。", color=discord.Color.green()), ephemeral=True)
            await ctx.interaction.response.send_modal(send())
        except:
            return

    @welcome_setting.command(name="expand", description="メッセージ展開を有効化します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def setting_message_expand(self, ctx: commands.Context, 有効化するか: bool):
        db = self.bot.async_db["Main"].ExpandSettings
        if 有効化するか:
            await db.replace_one(
                {"Guild": ctx.guild.id}, 
                {"Guild": ctx.guild.id}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title="メッセージ展開を有効化しました。", color=discord.Color.green()))
        else:
            result = await db.delete_one({"Guild": ctx.guild.id})
            if result.deleted_count == 0:
                return await ctx.reply(embed=discord.Embed(title="メッセージ展開は無効です。", color=discord.Color.red()))
            await ctx.reply(embed=discord.Embed(title="メッセージ展開を無効化しました。", color=discord.Color.red()))

    @welcome_setting.command(name="expand-user", description="ユーザー展開を有効化します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def setting_user_expand(self, ctx: commands.Context, 有効化するか: bool):
        db = self.bot.async_db["Main"].ExpandSettingsUser
        if 有効化するか:
            await db.replace_one(
                {"Guild": ctx.guild.id}, 
                {"Guild": ctx.guild.id}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title="ユーザー展開を有効化しました。", color=discord.Color.green()))
        else:
            result = await db.delete_one({"Guild": ctx.guild.id})
            if result.deleted_count == 0:
                return await ctx.reply(embed=discord.Embed(title="ユーザー展開は無効です。", color=discord.Color.red()))
            await ctx.reply(embed=discord.Embed(title="ユーザー展開を無効化しました。", color=discord.Color.red()))

    @welcome_setting.command(name="timeout-roleremove", description="タイムアウトされるとロールを削除します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def setting_timeout_roleremove(self, ctx: commands.Context, ロール: discord.Role = None):
        db = self.bot.async_db["Main"].AutoRoleRemover
        if ロール:
            await db.replace_one(
                {"Guild": ctx.guild.id}, 
                {"Guild": ctx.guild.id, "Role": ロール.id}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title="ロール自動削除を有効化しました。", color=discord.Color.green()))
        else:
            result = await db.delete_one({"Guild": ctx.guild.id})
            if result.deleted_count == 0:
                return await ctx.reply(embed=discord.Embed(title="ロール自動削除は無効です。", color=discord.Color.red()))
            await ctx.reply(embed=discord.Embed(title="ロール自動削除を無効化しました。", color=discord.Color.red()))

    @welcome_setting.command(name="english-only", description="英語専用チャンネルを作ります。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def setting_eng_only(self, ctx: commands.Context, 有効化するか: bool):
        db = self.bot.async_db["Main"].EnglishOnlyChannel
        if 有効化するか:
            await db.replace_one(
                {"Guild": ctx.guild.id}, 
                {"Guild": ctx.guild.id, "Channel": ctx.channel.id}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title="英語専用チャンネルを有効化しました。", color=discord.Color.green()))
        else:
            result = await db.delete_one({"Guild": ctx.guild.id})
            if result.deleted_count == 0:
                return await ctx.reply(embed=discord.Embed(title="英語専用チャンネルは有効ではありません。", color=discord.Color.red()))
            await ctx.reply(embed=discord.Embed(title="英語専用チャンネルを無効化しました。", color=discord.Color.red()))

    @welcome_setting.command(name="hint", description="ヒントを有効化します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_messages=True)
    async def setting_hint(self, ctx: commands.Context, 有効化するか: bool):
        db = self.bot.async_db["Main"].HintSetting
        if 有効化するか:
            await db.replace_one(
                {"Guild": ctx.guild.id}, 
                {"Guild": ctx.guild.id}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title="ヒントを有効化しました。", color=discord.Color.green()))
        else:
            result = await db.delete_one({"Guild": ctx.guild.id})
            if result.deleted_count == 0:
                return await ctx.reply(embed=discord.Embed(title="ヒントは有効ではありません。", color=discord.Color.red()))
            await ctx.reply(embed=discord.Embed(title="ヒントを無効化しました。", color=discord.Color.red()))

"""
    @commands.command(name="voice_date", description="最後にVCを使用した日付を貼り付けます。")
    @commands.has_permissions(manage_channels=True)
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def voice_date(self, ctx, voice: discord.VoiceChannel = None):
        try:
            db = self.bot.async_db["Main"].VoiceTime
            if voice:
                await db.replace_one(
                    {"Channel": voice.id}, 
                    {"Channel": voice.id, "Guild": ctx.guild.id}, 
                    upsert=True
                )
                await ctx.reply(embed=discord.Embed(title="最後にVCに参加した日付を記録するようにしました。", color=discord.Color.green()))
            else:
                await db.delete_one({"Guild": ctx.guild.id})
                await ctx.reply(embed=discord.Embed(title="最後にVCに参加した日付を記録しないようにしました。", color=discord.Color.green()))
        except:
            return
"""
async def setup(bot):
    await bot.add_cog(SettingCog(bot))