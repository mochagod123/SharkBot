from discord.ext import commands
import discord
import traceback
import sys
import logging
import yt_dlp
import random
import struct 
import io
import aiohttp
from datetime import datetime, timedelta
import time
import string
import datetime
import asyncio

COOLDOWN_TIME = 5
user_last_message_time = {}

class ModCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> ModCog")

    async def SendLog(self, ctx: commands.Context, title: str, 説明: str):
        db = self.bot.async_db["Main"].LoggingChannel
        try:
            dbfind = await db.find_one({"Guild": ctx.guild.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        try:
            await self.bot.get_channel(dbfind["Channel"]).send(embed=discord.Embed(title=f"{title}", description=f"{説明}", color=discord.Color.green()).set_footer(text=f"実行者: {ctx.author.name}"))
        except:
            return
        
    def random_id(self, n):
        randlst = [random.choice(string.ascii_letters + string.digits) for i in range(n)]
        return ''.join(randlst)

    async def SaveLog(self, ctx: commands.Context, title: str, 説明: str):
        db = self.bot.async_db["Main"].LoggingWeb
        id = self.random_id(10)
        await db.replace_one(
            {"Guild": ctx.guild.id, "ID": id}, 
            {"Guild": ctx.guild.id, "ID": id, "Title": title, "Desc": 説明, "Author": f"{ctx.author.id}/{ctx.author.name}"}, 
            upsert=True
        )

    @commands.hybrid_group(name="moderation", description="ログチャンネルを設定します。", fallback="logging")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def logging_channel(self, ctx: commands.Context, 有効化: bool):
        if 有効化:
            db = self.bot.async_db["Main"].LoggingChannel
            await db.replace_one(
                {"Channel": ctx.channel.id, "Guild": ctx.guild.id}, 
                {"Channel": ctx.channel.id, "Guild": ctx.guild.id}, 
                upsert=True
            )
            await self.SendLog(ctx, "ログが有効化されました。", "特に説明はなし")
            await ctx.reply(embed=discord.Embed(title="モデレーションをログを有効化しました。", color=discord.Color.green()))
        else:
            db = self.bot.async_db["Main"].LoggingChannel
            await db.delete_one({
                "Channel": ctx.channel.id,
            })
            await self.SendLog(ctx, "ログが無効化されました。", "特に説明はなし")
            await ctx.reply(embed=discord.Embed(title="モデレーションをログを無効化しました。", color=discord.Color.green()))

    @logging_channel.command(name="lock", description="チャンネルをLockするよ")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def mod_lock(self, ctx: commands.Context):
        await ctx.defer()
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await self.SendLog(ctx, "チャンネルがロックされました。", f"ロックされたチャンネル: {ctx.channel.name}")
        await self.SaveLog(ctx, "チャンネルがロックされました。", f"ロックされたチャンネル: {ctx.channel.name}")
        await ctx.send(embed=discord.Embed(title=f"チャンネルをロックしました。", color=discord.Color.green()))

    @logging_channel.command(name="unlock", description="チャンネルをUnLockするよ")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def mod_unlock(self, ctx: commands.Context):
        await ctx.defer()
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = True
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await self.SendLog(ctx, "チャンネルが解放されました。", f"解放されたチャンネル: {ctx.channel.name}")
        await self.SaveLog(ctx, "チャンネルが解放されました。", f"解放されたチャンネル: {ctx.channel.name}")
        await ctx.send(embed=discord.Embed(title=f"チャンネルを開放しました。", color=discord.Color.green()))

    @logging_channel.command(name="category-copy", description="カテゴリをコピーします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def category_copy(self, ctx: commands.Context, カテゴリ: discord.CategoryChannel):
        await ctx.defer()
        c = await ctx.guild.create_category(name=カテゴリ.name, overwrites=カテゴリ.overwrites)
        for channel in カテゴリ.channels:
            overwrites = channel.overwrites

            if isinstance(channel, discord.TextChannel):
                new_channel = await ctx.guild.create_text_channel(
                    name=channel.name,
                    category=c,
                    topic=channel.topic,
                    slowmode_delay=channel.slowmode_delay,
                    overwrites=overwrites  # 権限設定を適用
                )
            elif isinstance(channel, discord.VoiceChannel):
                new_channel = await ctx.guild.create_voice_channel(
                    name=channel.name,
                    category=c,
                    bitrate=channel.bitrate,
                    user_limit=channel.user_limit,
                    overwrites=overwrites  # 権限設定を適用
                )
            elif isinstance(channel, discord.StageChannel):
                new_channel = await ctx.guild.create_stage_channel(
                    name=channel.name,
                    category=c,
                    overwrites=overwrites  # 権限設定を適用
                )
            elif isinstance(channel, discord.ForumChannel):  # フォーラムチャンネルの場合
                new_channel = await ctx.guild.create_forum_channel(
                    name=channel.name,
                    category=c,
                    topic=channel.topic,
                    overwrites=overwrites
                )
            await asyncio.sleep(2)
        await self.SendLog(ctx, "カテゴリがコピーされました。", f"{カテゴリ.name}")
        await self.SaveLog(ctx, "カテゴリがコピーされました。", f"{カテゴリ.name}")
        await ctx.send(embed=discord.Embed(title=f"カテゴリをコピーしました。", color=discord.Color.green()), ephemeral=True)

    @logging_channel.command(name="warn", description="メンバーを警告するよ")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(moderate_members=True)
    async def mod_warn(self, ctx: commands.Context, メンバー: discord.Member, 警告文: str):
        await ctx.defer()
        await メンバー.send(embed=discord.Embed(title=f"あなたは`{ctx.guild.name}`警告されました。", description=警告文, color=discord.Color.yellow()))
        await self.SendLog(ctx, "メンバーを警告しました。", f"警告された人: {メンバー.name}")
        await self.SaveLog(ctx, "メンバーを警告しました。", f"警告された人: {メンバー.name}")
        await ctx.send(embed=discord.Embed(title=f"メンバーを警告しました。", color=discord.Color.green()))

    @logging_channel.command(name="clear", description="チャンネルをきれいにするよ")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def mod_clear(self, ctx: commands.Context, 数: int):
        if 数 > 100:
            return await ctx.reply("あまりにもメッセージを削除する量が多すぎます！", ephemeral=True)
        if ctx.interaction:
            await ctx.defer(ephemeral=True)
            await ctx.channel.purge(limit=数)
            await self.SendLog(ctx, "メッセージを削除しました。", f"削除したメッセージの\nあったチャンネル: {ctx.channel.name}\n削除した数: {数}")
            await self.SaveLog(ctx, "メッセージを削除しました。", f"削除したメッセージの\nあったチャンネル: {ctx.channel.name}\n削除した数: {数}")
            await ctx.send(embed=discord.Embed(title=f"メッセージを削除しました。", color=discord.Color.green()), ephemeral=True)
        else:
            await ctx.channel.purge(limit=数 + 1)
            await self.SendLog(ctx, "メッセージを削除しました。", f"削除したメッセージの\nあったチャンネル: {ctx.channel.name}\n削除した数: {数}")
            await self.SaveLog(ctx, "メッセージを削除しました。", f"削除したメッセージの\nあったチャンネル: {ctx.channel.name}\n削除した数: {数}")
            await ctx.channel.send(embed=discord.Embed(title=f"メッセージを削除しました。", color=discord.Color.green()))

    @logging_channel.command(name="remake", description="チャンネルを再生成するよ")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def mod_remake(self, ctx: commands.Context):
        await ctx.defer()
        ch = await ctx.channel.clone()
        await ch.edit(position=ctx.channel.position+1)
        await ctx.channel.delete()
        await asyncio.sleep(1)
        await ch.send("再生成しました。")

    @logging_channel.command(name="mute", description="ユーザーをMuteするよ (はじめは時間がかかるよ)")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(moderate_members=True)
    async def mod_mute(self, ctx: commands.Context, メンバー: discord.Member, 分: int):
        user_id = ctx.author.id
        class CheckButton(discord.ui.View):
            def __init__(self, ctx, bot, member: discord.Member, tid: int):
                super().__init__(timeout=None)
                self.ctx = ctx
                self.member = member
                self.tid = tid
                self.bots = bot
                self.result = None

            @discord.ui.button(label="承認", style=discord.ButtonStyle.green)
            async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer()
                if not user_id == interaction.user.id:
                    return
                try:
                    timeout_duration = datetime.timedelta(minutes=self.tid)
                    await self.member.timeout(timeout_duration)
                    await self.bots.SendLog(ctx, "メンバーがミュートされました。", f"Muteされた人: {メンバー.name}")
                    await self.bots.SaveLog(ctx, "メンバーがミュートされました。", f"Muteされた人: {メンバー.name}")
                    await interaction.message.edit(content=None, embed=discord.Embed(title=f"{メンバー.display_name}をMuteしました。", color=discord.Color.green()), view=None)
                except:
                    await interaction.message.edit(content=None, embed=discord.Embed(title=f"Muteに失敗しました。", color=discord.Color.green()), view=None)

            @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.red)
            async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer()
                if not user_id == interaction.user.id:
                    return
                await interaction.message.edit(content="キャンセルされました。", embed=None, view=None)

        await ctx.reply(embed=discord.Embed(title=f"{メンバー.name}をMuteしていいですか？", color=discord.Color.yellow()), view=CheckButton(ctx, bot=self, member=メンバー, tid=分))

    @logging_channel.command(name="unmute", description="ユーザーをUnMuteするよ")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(moderate_members=True)
    async def mod_unmute(self, ctx: commands.Context, メンバー: discord.Member):
        await ctx.defer()
        await メンバー.edit(timed_out_until=None)
        await self.SendLog(ctx, "ミュートを解除しました。", f"UnMuteされた人: {メンバー.name}")
        await self.SaveLog(ctx, "ミュートを解除しました。", f"UnMuteされた人: {メンバー.name}")
        await ctx.send(embed=discord.Embed(title=f"{メンバー.display_name}をUnMuteしました。", color=discord.Color.green()))
        
    @logging_channel.command(name="echo", description="言葉をしゃべるよ。")
    @commands.cooldown(1, 30, commands.BucketType.guild)
    @commands.has_permissions(administrator=True)
    async def echo_bot(self, ctx: commands.Context, *, テキスト: str):
        await ctx.defer(ephemeral=True)
        print(f"{テキスト.replace("\n", "\\n")} Sayed. by {ctx.author.display_name}({ctx.author.id})")
        await ctx.channel.send(テキスト)
        await self.SendLog(ctx, "テキストが発言されました。", f"内容: {テキスト}")
        await self.SaveLog(ctx, "テキストが発言されました。", f"内容: {テキスト}")
        await ctx.reply("Sended.", ephemeral=True)

    @logging_channel.command(name="ban", description="ユーザーをBANします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(ban_members=True)
    async def ban_member(self, ctx: commands.Context, ユーザー: discord.User, 理由: str):
        user_id = ctx.author.id
        class CheckButton(discord.ui.View):
            def __init__(self, ctx, bot, member: discord.User, 理由: str):
                super().__init__(timeout=None)
                self.ctx = ctx
                self.member = member
                self.reas = 理由
                self.bots = bot
                self.result = None

            @discord.ui.button(label="承認", style=discord.ButtonStyle.green)
            async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer()
                if not user_id == interaction.user.id:
                    return
                await ctx.guild.ban(self.member, reason=self.reas)
                await self.bots.SendLog(ctx, "メンバーがBANされました。", f"BANされた人: {self.member.name}\n理由: {self.reas}")
                await self.bots.SaveLog(ctx, "メンバーがBANされました。", f"BANされた人: {self.member.name}\n理由: {self.reas}")
                await interaction.message.edit(content=None, embed=discord.Embed(title=f"{self.member.display_name}をBANしました。", color=discord.Color.green()), view=None)

            @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.red)
            async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                if not user_id == interaction.user.id:
                    return
                await interaction.response.defer()
                await interaction.message.edit(content="キャンセルされました。", embed=None, view=None)
        await ctx.reply(embed=discord.Embed(title=f"{ユーザー.name}をBANしていいですか？", color=discord.Color.yellow()), view=CheckButton(ctx, self, ユーザー, 理由))

    @logging_channel.command(name="kick", description="ユーザーをKICKします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(kick_members=True)
    async def kick_member(self, ctx: commands.Context, ユーザー: discord.User, 理由: str):
        if ユーザー.id == ctx.author.id:
            return await ctx.reply(embed=discord.Embed(title=f"自分自身はキックできません。", color=discord.Color.red()))
        await ctx.guild.kick(ユーザー, reason=理由)
        await ctx.reply(embed=discord.Embed(title=f"{ユーザー.name}をKickしました。", color=discord.Color.red()))
        await self.SendLog(ctx, "メンバーがKickされました。", f"Kickされた人: {ユーザー.name}\n理由: {理由}")
        await self.SaveLog(ctx, "メンバーがKickされました。", f"Kickされた人: {ユーザー.name}\n理由: {理由}")

    @logging_channel.command(name="color-role", description="ランダムな色付きロールを作ります。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def color_role(self, ctx: commands.Context, ロール名: str):
        r = await ctx.guild.create_role(name=ロール名, color=discord.Colour.random())
        await ctx.reply(embed=discord.Embed(title=f"{ロール名}を作成しました。", description=f"{r.mention}", color=discord.Color.green()))
        await self.SendLog(ctx, "色付きロールが作成されました。", f"ロール名: {r.mention}")
        await self.SaveLog(ctx, "色付きロールが作成されました。", f"ロール名: {r.mention}")

    @logging_channel.command(name="guideline", description="ガイドラインを作成します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(administrator=True)
    async def guideline(self, ctx: commands.Context, ピン止めするか: bool):
        try:
            class send(discord.ui.Modal):
                def __init__(self) -> None:
                    super().__init__(title="ガイドラインの作成", timeout=None)
                    self.etitle = discord.ui.TextInput(label="タイトル",placeholder="タイトルを入力",style=discord.TextStyle.long,required=True)
                    self.desc = discord.ui.TextInput(label="説明",placeholder="説明を入力",style=discord.TextStyle.long,required=True)
                    self.add_item(self.etitle)
                    self.add_item(self.desc)
                async def on_submit(self, interaction: discord.Interaction) -> None:
                    msg = await interaction.channel.send(embed=discord.Embed(title=self.etitle.value, description=self.desc.value, color=discord.Color.random()))
                    if ピン止めするか:
                        await msg.pin()
                    await interaction.response.send_message(embed=discord.Embed(title="ガイドラインを作成しました。", color=discord.Color.green()), ephemeral=True)
            await ctx.interaction.response.send_modal(send())
        except:
            return

    @logging_channel.command(name="report", description="荒らしなどを遠隔で報告します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def report(self, ctx: commands.Context, ユーザー: discord.User, 報告内容: str):
        await ctx.defer(ephemeral=True)
        now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        created_at = ctx.author.created_at.replace(tzinfo=datetime.timezone.utc)
        one_week_ago = now - datetime.timedelta(weeks=1)
        if created_at > one_week_ago:
            return await ctx.reply(ephemeral=True, content="あなたは新しいアカウントなので、まだ申請できません。")
        if "discord.com" in 報告内容:
            return await ctx.reply(ephemeral=True, content="内部エラーが発生しました。")
        if "discord.gg" in 報告内容:
            return await ctx.reply(ephemeral=True, content="内部エラーが発生しました。")
        if "x.gd" in 報告内容:
            return await ctx.reply(ephemeral=True, content="内部エラーが発生しました。")
        await self.bot.get_channel(1330895502857994270).send(embed=discord.Embed(title=f"`{ctx.author.name}`さんの報告", description=f"```{報告内容}```", color=discord.Color.yellow()).add_field(name="ユーザー", value=f"```{ユーザー.display_name}\n{ユーザー.id}```"))
        await self.bot.get_channel(1341607968717799459).send(embed=discord.Embed(title=f"`{ctx.author.name}`さんの報告", description=f"```{報告内容}```", color=discord.Color.yellow()).add_field(name="ユーザー", value=f"```{ユーザー.display_name}\n{ユーザー.id}```"))
        await ctx.reply(embed=discord.Embed(title="報告しました。", description="ご報告ありがとうございます。", color=discord.Color.green()), ephemeral=True)

    @logging_channel.command(name="suggestion", description="Loggingチャンネルに提案を送信します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def suggestion(self, ctx: commands.Context, 提案内容: str):
        await ctx.defer(ephemeral=True)
        await self.SendLog(ctx, title=f"このサーバーに提案されました。", 説明=f"```{提案内容}```")
        await self.SaveLog(ctx, title=f"このサーバーに提案されました。", 説明=f"```{提案内容}```")
        await ctx.reply(embed=discord.Embed(title="提案しました。", description="提案ありがとうございます。", color=discord.Color.green()), ephemeral=True)

async def setup(bot):
    await bot.add_cog(ModCog(bot))