from discord.ext import commands, ipc, oauth2
import discord
import time
import traceback
import sys
from discord import Webhook
import aiohttp
import json
import io
import logging
import asyncio
import datetime
import aiohttp
import traceback
import textwrap
import random
from functools import partial
import string

COOLDOWN_TIME_BOTJOIN = 60
cooldown_bot_join = {}

join_times = {}

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("../Token.json") as tk:
            self.tkj = json.loads(tk.read())
            self.tko = self.tkj["Token"]
            self.tkob = self.tkj["BetaToken"]
        print(f"init -> AdminCog")

    @commands.command(name="exit", hidden=True)
    @commands.is_owner()
    async def exit_bot_admin(self, ctx):
        await ctx.reply("Botをシャットダウンしています。。")
        await self.bot.close()
        sys.exit()

    @commands.command(name="reload", aliases=["re", "rel"], hidden=True, description="CogをReloadします。(オーナー専用)")
    async def reload_admin(self, ctx: commands.Context, cogname: str):
        if ctx.author.id == 1335428061541437531:
            await self.bot.reload_extension(f"cogs.{cogname}")
            await self.bot.tree.sync()
            await ctx.reply(f"ReloadOK .. `cogs.{cogname}`")
            await ctx.message.add_reaction("<:CheckGreen:1341929972868055123>")

    @commands.command(name="reload_", hidden=True, description="CogをSyncせずにReloadします。(オーナー専用)")
    @commands.is_owner()
    async def reload_admin_two(self, ctx, cogname: str):
        if ctx.author.id == 1335428061541437531:
            await self.bot.reload_extension(f"cogs.{cogname}")
            await ctx.reply(f"ReloadOK .. `cogs.{cogname}`")
            await ctx.message.add_reaction("<:CheckGreen:1341929972868055123>")

    @commands.command(name="load", hidden=True, description="CogをLoadします。(オーナー専用)")
    @commands.is_owner()
    async def load_admin(self, ctx, cogname: str):
        if ctx.author.id == 1335428061541437531:
            await self.bot.load_extension(f"cogs.{cogname}")
            await ctx.reply(f"LoadOK .. `cogs.{cogname}`")
            await ctx.message.add_reaction("<:CheckGreen:1341929972868055123>")

    @commands.command(name="banuser", hidden=True)
    async def banuser_bot(self, ctx, user: discord.User):
        if not ctx.author.id == 1335428061541437531:
            return
        db = self.bot.async_db["Main"].BANUser
        await db.replace_one(
            {"User": user.id}, 
            {"User": user.id}, 
            upsert=True
        )
        await ctx.reply(embed=discord.Embed(title=f"{user.name}をBANしました。", color=discord.Color.red()))

    @commands.command(name="gu_banuser", hidden=True)
    @commands.is_owner()
    async def guild_users_banuser_bot(self, ctx, guild: discord.Guild):
        db = self.bot.async_db["Main"].BANUser
        for m in guild.members:
            if m.bot:
                continue
            await db.replace_one(
                {"User": m.id}, 
                {"User": m.id}, 
                upsert=True
            )
        await guild.leave()
        await ctx.reply(embed=discord.Embed(title=f"{guild.name}のユーザーを全員BotからBANしました。", color=discord.Color.red()))

    @commands.command(name="unbanuser", hidden=True)
    async def unbanuser_bot(self, ctx, user: discord.User):
        if not ctx.author.id == 1335428061541437531:
            return
        db = self.bot.async_db["Main"].BANUser
        await db.delete_one({
            "User": user.id
        })
        await ctx.reply(embed=discord.Embed(title=f"{user.name}のBANを解除しました。", color=discord.Color.red()))

    @commands.command(name="make_error", hidden=True)
    @commands.is_owner()
    async def make_error_admin(self, ctx, errorname: str):
        raise Exception(errorname)
    
    @commands.command(name="guilds_list", hidden=True, description="サーバーのリストを取得します。(管理人専用)")
    async def guilds_list(self, ctx):
        if self.bot.get_guild(1343124570131009579).get_role(1344470846995169310) in self.bot.get_guild(1343124570131009579).get_member(ctx.author.id).roles:
            text = ""
            for g in self.bot.guilds:
                text += f"{g.name} - {g.id}\n"
            slist = text.split("\n")
            b = 0
            n = 30
            msg = await ctx.reply(embed=discord.Embed(title="サーバーリスト", description=f"{"\n".join(slist[b:n])}", color=discord.Color.green()))
            await msg.add_reaction("<:Back:1331888006600331308>")
            await msg.add_reaction("<:Next:1331888013495631962>")
            await msg.add_reaction("<:Cancel:1325247762266193993>")
            try:
                while True:
                    r, m = await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id and not u.bot and ctx.author.id == u.id, timeout=None)
                    await r.remove(ctx.author)
                    if r.emoji.id == 1331888006600331308:
                        b -= 30
                        n -= 30
                        await msg.edit(embed=discord.Embed(title="サーバーリスト", description=f"{"\n".join(slist[b:n])}", color=discord.Color.green()))
                    elif r.emoji.id == 1331888013495631962:
                        b += 30
                        n += 30
                        await msg.edit(embed=discord.Embed(title="サーバーリスト", description=f"{"\n".join(slist[b:n])}", color=discord.Color.green()))
                    else:
                        await msg.edit(embed=None, content="閉じました。")
                        return
            except:
                return
        else:
            await ctx.channel.send(embed=discord.Embed(title="あなたはモデレーターではありません。", color=discord.Color.red()))

    @commands.command(name="guild_info", hidden=True, description="サーバーを検索します。(管理人専用)")
    async def guild_info(self, ctx, guild: discord.Guild):
        if self.bot.get_guild(1343124570131009579).get_role(1344470846995169310) in self.bot.get_guild(1343124570131009579).get_member(ctx.author.id).roles:
            embed = discord.Embed(title=guild.name, description=f"ID: {guild.id}\nCreatedAt: {guild.created_at}\n人数: {guild.member_count}人\nOwnerID: {guild.owner.id}", color=discord.Color.green())
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
            msg = await ctx.reply(embed=embed)
            await msg.add_reaction("<:User:1332339623170543656>")
            r, m = await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id and not u.bot and ctx.author.id == u.id, timeout=None)
            if r.emoji.id == 1332339623170543656:
                um = discord.Embed(title=f"`{guild.owner.display_name}`の情報", description=f"ID: {guild.owner.id}\nUserName: {guild.owner.name}\nCreated at: {guild.owner.created_at}", color=discord.Color.green())
                if guild.owner.avatar:
                    um.set_thumbnail(url=guild.owner.avatar.url)
                await msg.edit(embed=um)
        else:
            await ctx.channel.send(embed=discord.Embed(title="あなたはモデレーターではありません。", color=discord.Color.red()))

    @commands.command(name="guild_channels", hidden=True)
    async def guild_channels_info(self, ctx, guild: discord.Guild):
        if self.bot.get_guild(1343124570131009579).get_role(1344470846995169310) in self.bot.get_guild(1343124570131009579).get_member(ctx.author.id).roles:
            await ctx.reply(embed=discord.Embed(title=f"{guild.name}のチャンネル", description="\n".join([f"{g.name} - {g.id}" for g in guild.channels]), color=discord.Color.green()))
        else:
            return

    @commands.command(name="leave_guild", aliases=["lg"], hidden=True, description="サーバーから退出します。(オーナー専用)")
    async def leave_guild(self, ctx, guild: discord.Guild):
        if ctx.author.id == 1335428061541437531:
            await guild.leave()
            await ctx.reply(f"{guild.name}から退出しました。")

    @commands.command(name="get_invite", hidden=True, description="サーバーの招待リンクを取得します。(管理者専用)")
    async def get_invite(self, ctx, guild: discord.Guild):
        if self.bot.get_guild(1343124570131009579).get_role(1344470846995169310) in self.bot.get_guild(1343124570131009579).get_member(ctx.author.id).roles:
            for i in guild.channels:
                try:
                    inv = await i.create_invite()
                    await ctx.reply(f"{inv.url}")
                    return
                except:
                    continue

    @commands.command(name="check_user", hidden=True)
    @commands.is_owner()
    async def check_user(self, ctx, user: discord.User):
        mem = []
        if user.id == 1322100616369147924:
            return
        for g in self.bot.guilds:
            for m in g.members:
                if m.id == user.id:
                    mem.append(f"{g.name} - {g.id}")
                    break
        await ctx.reply(f"検出されたサーバー\n{"\n".join(mem)}")

    @commands.command(name="add_bot", hidden=True)
    async def add_bot(self, ctx, bot: discord.User):
        if self.bot.get_guild(1343124570131009579).get_role(1344470846995169310) in self.bot.get_guild(1343124570131009579).get_member(ctx.author.id).roles:
            db = self.bot.async_db["Main"].BotRegister
            await db.replace_one(
                {"Bot": bot.id}, 
                {"Bot": bot.id, "Name": bot.display_name, "Invite": f"https://discord.com/oauth2/authorize?client_id={bot.id}&permissions=8&integration_type=0&scope=applications.commands+bot", "Icon": bot.avatar.url}, 
                upsert=True
            )
            await ctx.channel.send(embed=discord.Embed(title="Botを掲示板に乗せました。", color=discord.Color.green()))
        else:
            await ctx.channel.send(embed=discord.Embed(title="あなたはモデレーターではありません。", color=discord.Color.red()))

    @commands.command(name="add_guild", hidden=True, description="承認サーバーに追加します。(管理人専用)")
    async def add_guild(self, ctx, guild: discord.Guild, *, message: str):
        if self.bot.get_guild(1343124570131009579).get_role(1344470846995169310) in self.bot.get_guild(1343124570131009579).get_member(ctx.author.id).roles:
            ch = self.bot.get_channel(1330146277601574912)
            if type(ch) == discord.ForumChannel:
                await ch.create_thread(name=f"{guild.name}", content=f"{message}")
            await ctx.channel.send(embed=discord.Embed(title="連携サーバーに追加しました。", color=discord.Color.green()))
        else:
            await ctx.channel.send(embed=discord.Embed(title="あなたはモデレーターではありません。", color=discord.Color.red()))

    @commands.command(name="eval", hidden=True)
    @commands.is_owner()
    async def eval(self, ctx, *, text: str):
        ev = eval(text)
        await ctx.reply(ev)

    @commands.command(name="mongodb_select", hidden=True)
    @commands.is_owner()
    async def mongodb_select(self, ctx, db: str, filter1: str, intb: bool, *, filter2: str):
        try:
            mdb = self.bot.async_db["Main"][db]
        except:
            return await ctx.reply(embed=discord.Embed(title="MongoDBにクエリを送りました。", description=f"データなし", color=discord.Color.green()))
        try:
            if intb:
                dbfind = await mdb.find_one({filter1: int(filter2)}, {"_id": False})
            else:
                dbfind = await mdb.find_one({filter1: filter2}, {"_id": False})
        except:
            return await ctx.reply(embed=discord.Embed(title="MongoDBにクエリを送りました。", description=f"データなし", color=discord.Color.green()))
        if dbfind is None:
            return await ctx.reply(embed=discord.Embed(title="MongoDBにクエリを送りました。", description=f"データなし", color=discord.Color.green()))
        await ctx.reply(embed=discord.Embed(title="MongoDBにクエリを送りました。", description=f"```{dbfind}```", color=discord.Color.green()))

    @commands.command(name="warn_guild", hidden=True)
    @commands.is_owner()
    async def warn_guild(self, ctx, guild: discord.Guild, *, text: str):
        try:
            await guild.owner.send(embed=discord.Embed(title=f"{guild.name}は警告されました。", description=f"{text}", color=discord.Color.red()))
            await ctx.reply(embed=discord.Embed(title=f"{guild.name}を警告しました。", description=f"{text}", color=discord.Color.green()))
        except:
            await ctx.reply("警告に失敗しました。")

    """
    @commands.command(name="allclear_test", hidden=True)
    @commands.is_owner()
    async def allclear_test(self, ctx: commands.Context):
        ch = await ctx.channel.clone()
        await ch.edit(position=ctx.channel.position+1)
        await ctx.channel.delete()
    """

    # ユーザーの処罰

    @commands.command(name="gmute", hidden=True, description="ユーザーをグローバルチャットでMuteします。(管理人専用)")
    async def gmute(self, ctx: commands.Context, ユーザー: discord.User, *, 理由: str):
        if self.bot.get_guild(1343124570131009579).get_role(1344470846995169310) in self.bot.get_guild(1343124570131009579).get_member(ctx.author.id).roles:
            msg = await ctx.reply(embed=discord.Embed(title=f"{ユーザー.display_name}をGMuteしますか？", description=f"ID: {ユーザー.id}\nUserName: {ユーザー.name}\nDisplayName: {ユーザー.display_name}", color=discord.Color.red()))
            await msg.add_reaction("<:Check:1325247594963927203>")
            await msg.add_reaction("<:Cancel:1325247762266193993>")
            try:
                r, m = await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id and not u.bot and ctx.author.id == u.id, timeout=30)
                if r.emoji.id == 1325247594963927203:
                    db = self.bot.async_db["Main"].GMute
                    await db.replace_one(
                        {"User": ユーザー.id}, 
                        {"User": ユーザー.id, "Reason": 理由}, 
                        upsert=True
                    )
                    await ctx.channel.send(embed=discord.Embed(title="GMuteしました。", color=discord.Color.red()))
                    db = self.bot.async_db["Main"].GlobalChat
                    async for ch in db.find(filter={'Name':f'mute'}):
                        async with aiohttp.ClientSession() as session:
                            try:
                                channel = self.bot.get_channel(ch["Channel"])
                            except:
                                continue
                            if not channel:
                                continue
                            try:
                                ch_webhooks = await channel.webhooks()
                                whname = f"Shark-Global-main"
                                webhooks = discord.utils.get(ch_webhooks, name=whname)
                            except:
                                continue
                            if webhooks is None:
                                webhooks = await channel.create_webhook(name=f"{whname}")
                            try:
                                webhook = Webhook.from_url(webhooks.url, session=session)
                                webhook = Webhook.from_url(webhooks.url, session=session)
                                embed = discord.Embed(title=f"{ユーザー.name}をGMuteしました。", description=f"ユーザーID: {ユーザー.id}\n理由:\n```{理由}```", color=discord.Color.yellow()).set_footer(text=f"実行者: {ctx.author.id}/{ctx.author.name}")
                                if ユーザー.avatar:
                                    embed.set_thumbnail(url=ユーザー.avatar.url)
                                await webhook.send(embed=embed, username="SharkBot-GMute", avatar_url="https://i.imgur.com/obJ17oY.png")
                            except:
                                continue
                else:
                    await ctx.channel.send(embed=discord.Embed(title="キャンセルしました。", color=discord.Color.red()))
            except TimeoutError:
                await ctx.channel.send(embed=discord.Embed(title="タイムアウトしました。", color=discord.Color.red()))
        else:
            await ctx.channel.send(embed=discord.Embed(title="あなたはモデレーターではありません。", color=discord.Color.red()))

    @commands.command(name="ungmute", hidden=True, description="ユーザーをグローバルチャットでUnMuteします。(管理人専用)")
    async def ungmute(self, ctx: commands.Context, ユーザー: discord.User, *, 理由: str):
        if self.bot.get_guild(1343124570131009579).get_role(1344470846995169310) in self.bot.get_guild(1343124570131009579).get_member(ctx.author.id).roles:
            msg = await ctx.reply(embed=discord.Embed(title=f"{ユーザー.display_name}をUnGMuteしますか？", description=f"ID: {ユーザー.id}\nUserName: {ユーザー.name}\nDisplayName: {ユーザー.display_name}", color=discord.Color.red()))
            await msg.add_reaction("<:Check:1325247594963927203>")
            await msg.add_reaction("<:Cancel:1325247762266193993>")
            try:
                r, m = await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id and not u.bot and ctx.author.id == u.id, timeout=30)
                if r.emoji.id == 1325247594963927203:
                    db = self.bot.async_db["Main"].GMute
                    result = await db.delete_one({
                        "User": ユーザー.id,
                    })
                    await ctx.channel.send(embed=discord.Embed(title="UnGMuteしました。", color=discord.Color.red()))
                    db = self.bot.async_db["Main"].GlobalChat
                    async for ch in db.find(filter={'Name':f'mute'}):
                        async with aiohttp.ClientSession() as session:
                            try:
                                channel = self.bot.get_channel(ch["Channel"])
                            except:
                                continue
                            try:
                                ch_webhooks = await channel.webhooks()
                                whname = f"Shark-Global-main"
                                webhooks = discord.utils.get(ch_webhooks, name=whname)
                            except:
                                continue
                            if webhooks is None:
                                webhooks = await channel.create_webhook(name=f"{whname}")
                            try:
                                webhook = Webhook.from_url(webhooks.url, session=session)
                                embed = discord.Embed(title=f"{ユーザー.name}をUnGMuteしました。", description=f"ユーザーID: {ユーザー.id}\n理由:\n```{理由}```", color=discord.Color.yellow()).set_footer(text=f"実行者: {ctx.author.id}/{ctx.author.name}")
                                if ユーザー.avatar:
                                    embed.set_thumbnail(url=ユーザー.avatar.url)
                                await webhook.send(embed=embed, username="SharkBot-UnGMute", avatar_url="https://i.imgur.com/obJ17oY.png")
                            except:
                                continue
                else:
                    await ctx.channel.send(embed=discord.Embed(title="キャンセルしました。", color=discord.Color.red()))
            except TimeoutError:
                await ctx.channel.send(embed=discord.Embed(title="タイムアウトしました。", color=discord.Color.red()))
        else:
            await ctx.channel.send(embed=discord.Embed(title="あなたはモデレーターではありません。", color=discord.Color.red()))

    @commands.command(name="check_autoban", hidden=True)
    @commands.is_owner()
    async def check_autoban(self, ctx):
        gs = []
        db = self.bot.async_db["Main"].AutoBAN
        async for gd in db.find():
            gs.append(f"{self.bot.get_guild(gd["Guild"]).name} {gd["Guild"]}")
        return await ctx.reply(f"```{"\n".join(gs)}```")
    
    @commands.command(name="check_test", hidden=True)
    @commands.is_owner()
    async def check_test(self, ctx: commands.Context):
        class CheckButton(discord.ui.View):
            def __init__(self, ctx):
                super().__init__(timeout=None)
                self.ctx = ctx
                self.result = None

            @discord.ui.button(label="承認", style=discord.ButtonStyle.green)
            async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer()
                await interaction.message.edit(content="承認されました。", embed=None, view=None)

            @discord.ui.button(label="キャンセル", style=discord.ButtonStyle.red)
            async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.defer()
                await interaction.message.edit(content="キャンセルされました。", embed=None, view=None)
        await ctx.reply(embed=discord.Embed(title="チェックしています。", color=discord.Color.yellow()), view=CheckButton(ctx))

    @commands.command(name="get_args", hidden=True)
    @commands.is_owner()
    async def get_args(self, ctx, *, command_name: str):
        command = self.bot.get_command(command_name)
        if not command:
            await ctx.send(f"コマンド `{command_name}` は存在しません。")
            return

        params = command.clean_params
        if not params:
            await ctx.send(f"コマンド `{command_name}` には引数がありません。")
        else:
            args_info = [f"{name}: {param.annotation}" for name, param in params.items()]
            args_text = "\n".join(args_info)
            await ctx.send(f"コマンド `{command_name}` の引数:\n{args_text}")

    @commands.command(name="test_guilds", hidden=True)
    @commands.is_owner()
    async def test_guilds(self, ctx: commands.Context):
        th = self.bot.get_channel(1330146277601574912).threads
        ths = [f"{i.name}" for i in th]
        await ctx.reply(embed=discord.Embed(title="連携サーバー", description="\n".join(ths), color=discord.Color.green()))

    @commands.command("gmutelist", description="サーバー掲示板を見ます。")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def gmutelist(self, ctx):
        await ctx.reply("以下のページをご覧ください。\nhttps://www.sharkbot.xyz/gmute")

    @commands.command("botlist", description="Botリストを見ます。")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def botlist(self, ctx):
        await ctx.reply("以下のページをご覧ください。\nhttps://www.sharkbot.xyz/bot")

    async def join_guild(self, code: str, bot_token: str, user_id: str, guild_id: str):
        url = f'https://discord.com/api/guilds/{guild_id}/members/{user_id}'
        headers = {
            'Authorization': f'Bot {bot_token}',
            'Content-Type': 'application/json'
        }
        data = {"access_token": code}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.put(url, headers=headers, json=data) as resp:
                    if resp.status == 201:
                        return {"success": True, "message": "User added successfully"}
                    else:
                        return {"success": False, "status": resp.status, "error": await resp.text()}
            except Exception as e:
                return {"success": False, "error": str(e)}

    @commands.command("save", description="セーブデータをセーブします。(管理人専用)")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def save(self, ctx):
        if not ctx.author.id == 1335428061541437531:
            return

        def is_owner_check(check):
            return getattr(check, "__qualname__", "").startswith("is_owner")

        commands_data = []

        db = self.bot.async_db["Main"].CommandsList

        for command in self.bot.commands:
            # Botオーナー専用・管理者専用のコマンドは保存しない
            if any(is_owner_check(check) for check in command.checks):
                continue  

            command_data = {
                "name": command.name,
                "description": command.description or "説明なし",
                "type": "command",
                "is_hybrid": isinstance(command, commands.HybridCommand),
                "subcommands": [],
            }

            if isinstance(command, commands.HybridGroup) or isinstance(command, commands.Group):
                command_data["type"] = "group" if isinstance(command, commands.Group) else "hybrid_group"

                # サブコマンドの追加
                for subcommand in command.commands:
                    if any(is_owner_check(check) for check in subcommand.checks):
                        continue  # Botオーナー専用・管理者専用のサブコマンドは除外

                    command_data["subcommands"].append({
                        "name": subcommand.name,
                        "description": subcommand.description or "説明なし",
                        "is_hybrid": isinstance(subcommand, commands.HybridCommand),
                    })

                # HybridGroup の Fallback コマンドを取得
                if isinstance(command, commands.HybridGroup):
                    fallback = getattr(command, "_fallback_command", None)
                    if fallback:
                        command_data["fallback"] = {
                            "name": fallback.name,
                            "description": fallback.description or "説明なし",
                            "is_hybrid": isinstance(fallback, commands.HybridCommand),
                        }

            commands_data.append(command_data)

        # MongoDBへ保存
        db.delete_many({})
        db.insert_many(commands_data)

        await ctx.reply("セーブ完了！")
        await ctx.message.add_reaction("<:CheckGreen:1341929972868055123>")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        join_times[member.id] = datetime.datetime.utcnow()

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        join_time = join_times.pop(member.id, None)  # 参加時間を取得（なければNone）
        if join_time:
            elapsed = (datetime.datetime.utcnow() - join_time).total_seconds()
            if elapsed <= 60:  # 1分以内なら記録
                db = self.bot.async_db["Main"].SokunukeRTA
                await db.insert_one({
                    "username": member.name,
                    "discriminator": member.discriminator,
                    "user_id": member.id,
                    "joined_at": join_time,
                    "left_at": datetime.datetime.utcnow()
                })

    @commands.hybrid_command(name="rta", description="即抜けrtaを見れます。")
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def rta(self, ctx):
        db = self.bot.async_db["Main"].SokunukeRTA
        pipeline = [
            {
                "$addFields": {
                    "elapsed_time": {"$subtract": ["$left_at", "$joined_at"]}
                }
            },
            {
                "$sort": {"elapsed_time": 1}  # 昇順ソート (短い時間順)
            },
            {
                "$limit": 20  # 上位10件取得
            }
        ]

        async with db.aggregate(pipeline) as cursor:
            mons = await cursor.to_list(length=None)
            await ctx.reply(embed=discord.Embed(title="即抜けランキング", description=f"\n".join([f"{m["left_at"]}: {m["username"]}" for m in mons]), color=discord.Color.green()))

    @commands.Cog.listener("on_guild_join")
    async def on_guild_join_message(self, guild: discord.Guild):
        try:
            if guild.system_channel:
                try:
                    await guild.system_channel.send(embed=discord.Embed(title="Bot導入ありがとうございます！", description="このBotには、スーパーグローバルチャットや\n認証機能、ロールパネルなどがあるよ！\nまずは`/bot setup`を見てみよう！", color=discord.Color.blue()))
                except:
                    return
        except:
            return

    @commands.Cog.listener("on_guild_join")
    async def on_guild_join_blockuser(self, guild: discord.Guild):
        # await guild.leave()
        async with aiohttp.ClientSession() as session:
            async with session.post(f'https://discord.com/api/webhooks/1344608170496229376/Xd8xV9cODi98hl48edn5Xy-chgJoowoksNUShgx6e9x1vGRYGNtluTRbk5NpeDUcK7FT', data ={"content": f"{guild.owner.id}/{guild.owner.name}が\n{guild.id}/{guild.name}にBot導入しました。"}) as response:
                db = self.bot.async_db["Main"].BANUser
                try:
                    profile = await db.find_one({"User": guild.owner.id}, {"_id": False})
                    if profile is None:
                        return
                    else:
                        try:
                            await guild.owner.send(embed=discord.Embed(title="あなたはSharkBotから\nBANされています。", color=discord.Color.red()).set_image(url="https://p.turbosquid.com/ts-thumb/Sp/3o4865/I2U5hKZa/minecraftcreeper01/jpg/1458021375/600x600/fit_q87/7acb53fee47d60bec524ca6edca1f4fc56a3d668/minecraftcreeper01.jpg"))
                        except:
                            pass
                        await guild.leave()
                        return
                except:
                    return
                
    @commands.Cog.listener("on_guild_remove")
    async def on_guild_remove_log(self, guild: discord.Guild):
        async with aiohttp.ClientSession() as session:
            async with session.post(f'https://discord.com/api/webhooks/1344608170496229376/Xd8xV9cODi98hl48edn5Xy-chgJoowoksNUShgx6e9x1vGRYGNtluTRbk5NpeDUcK7FT', data ={"content": f"{guild.id}/{guild.name}から退出しました。"}) as response:
                return

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        return
        async with aiohttp.ClientSession() as session:
            async with session.post(f'https://discord.com/api/webhooks/1344584369641095221/TK3RKD2mhp-qj8EC39kkplu3r6yTXAkL1IYlh9ck1eNWwrm0QFXeSmkTlMqRUl4jn2Ri', data ={"content": f"{ctx.author.id}/{ctx.author.name}がコマンドを実行しました。\nサーバー: {ctx.guild.id}/{ctx.guild.name}\nコマンド名: {ctx.command.name}"}) as response:
                return

    @commands.Cog.listener("on_member_join")
    async def on_member_join_hint(self, member: discord.Member):
        g = self.bot.get_guild(member.guild.id)
        db = self.bot.async_db["Main"].HintSetting
        try:
            dbfind = await db.find_one({"Guild": g.id}, {"_id": False})
        except:
            return
        if dbfind is None:
            return
        if member.id == 903541413298450462:
            if member.guild.system_channel:
                try:
                    await member.guild.system_channel.send(embed=discord.Embed(title="SharkBotからのヒントです。", description=f"DicoallのUp通知を使ってみませんか？\n`/bump dicoall`で設定できます。", color=discord.Color.blue()))
                except:
                    return
        elif member.id == 1325891361899151440:
            if member.guild.system_channel:
                try:
                    await member.guild.system_channel.send(embed=discord.Embed(title="SharkBotからのヒントです。", description=f"ベッドロックと合わせてSharkBotの認証も使ってみませんか？\n`/panel auth タイトル: 説明: ロール:`で設定できます。", color=discord.Color.blue()))
                except:
                    return

    PERMISSION_TRANSLATIONS = {
        "administrator": "管理者",
        "manage_channels": "チャンネルの管理",
        "manage_roles": "ロールの管理",
        "manage_messages": "メッセージの管理",
        "ban_members": "メンバーのBAN",
        "kick_members": "メンバーのキック",
        "send_messages": "メッセージの送信",
        "read_message_history": "メッセージ履歴の閲覧",
        "mention_everyone": "@everyone のメンション",
        "manage_guild": "サーバーの管理",
        "manage_emojis": "絵文字の管理",
        "manage_webhooks": "Webhookの管理",
        "manage_nicknames": "ニックネームの管理",
        "mute_members": "メンバーのミュート",
        "deafen_members": "メンバーのスピーカーミュート",
        "move_members": "ボイスチャンネルの移動",
    }

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        error_details = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(embed=discord.Embed(title="コマンドが見つかりません。", color=discord.Color.red()))
        elif isinstance(error, commands.MissingRequiredArgument):
            params = ctx.command.clean_params
            response = []
            for name, param in params.items():
                param_type = param.annotation
                if param_type == str:
                    msg = f"文字列:{name}"
                elif param_type == int:
                    msg = f"数字:{name}"
                elif param_type == bool:
                    msg = f"オンオフ:{name}"
                elif param_type == discord.User:
                    msg = f"ユーザー:{name}"
                elif param_type == discord.Member:
                    msg = f"メンバー:{name}"
                elif param_type == discord.Guild:
                    msg = f"サーバー:{name}"
                elif param_type == discord.Role:
                    msg = f"ロール:{name}"
                elif param_type == discord.TextChannel:
                    msg = f"テキストチャンネル:{name}"
                elif param_type == discord.VoiceChannel:
                    msg = f"VC:{name}"
                elif param_type == discord.CategoryChannel:
                    msg = f"カテゴリチャンネル:{name}"
                elif param_type == discord.Message:
                    msg = f"メッセージ:{name}"
                else:
                    msg = f"不明:{name}"
                response.append(msg)
            args_text = " ".join(response)
            await ctx.send(embed=discord.Embed(title="引数が不足しています。", description=f"```コマンド名 {args_text}```", color=discord.Color.red()))
        elif isinstance(error, commands.NotOwner):
            a = None
            return a
            await ctx.send(embed=discord.Embed(title="管理者専用コマンドです。", description=f"飼い主を裏切れません", color=discord.Color.red()))
        elif isinstance(error, commands.MissingPermissions):
            missing_perms = [self.PERMISSION_TRANSLATIONS.get(perm, perm) for perm in error.missing_permissions]
            missing_perms_str = ", ".join(missing_perms)
            await ctx.reply(embed=discord.Embed(title="権限がありません。", description=f"権限を持っている人が実行してください。\n必要な権限リスト: {missing_perms_str}", color=discord.Color.red()), ephemeral=True)
        elif isinstance(error, commands.CheckFailure):
            await ctx.reply(embed=discord.Embed(title="権限がありません。", description="権限がないため実行できません。", color=discord.Color.red()), ephemeral=True)
        elif isinstance(error, commands.CommandOnCooldown):
            a = None
            return a
        else:
            msg = await ctx.channel.send(embed=discord.Embed(title="予期しないエラーが発生しました。", description=f"```{error}```", color=discord.Color.red()))
            await msg.add_reaction("⬇️")
            await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id and not u.bot)
            if type(msg) == discord.Message:
                await msg.clear_reactions()
                await msg.edit(embed=discord.Embed(title="予期しないエラーが発生しました。", description=f"```{error_details[:1500].replace(self.tko, 'Token').replace(self.tkob, 'Token')}```", color=discord.Color.red()))
                await msg.add_reaction("👁️")
                await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id and not u.bot)
                tb = traceback.extract_tb(error.__traceback__)
                t = []
                for frame in tb:
                    t.append(f"{frame.filename.replace('guangzaijiadao80', 'User')} - {frame.lineno}行目")
                await msg.channel.send(embed=discord.Embed(title="ファイルパスと行数", description="```" + '\n'.join(t) + "```", color=discord.Color.red()))

async def setup(bot):
    await bot.add_cog(AdminCog(bot))