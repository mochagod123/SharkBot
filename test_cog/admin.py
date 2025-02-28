from discord.ext import commands
import discord
import traceback
import sys
from discord import Webhook
import aiohttp
import json
import logging
import asyncio
import traceback

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

    @commands.command(name="reload", aliases=["re", "rel"], hidden=True)
    @commands.is_owner()
    async def reload_admin(self, ctx, cogname: str):
        await self.bot.reload_extension(f"test_cog.{cogname}")
        await ctx.reply(f"ReloadOK .. `test_cog.{cogname}`")

    @commands.command(name="load", hidden=True)
    @commands.is_owner()
    async def load_admin(self, ctx, cogname: str):
        await self.bot.load_extension(f"test_cog.{cogname}")
        await ctx.reply(f"LoadOK .. `test_cog.{cogname}`")

    @commands.command(name="banuser", hidden=True)
    @commands.is_owner()
    async def banuser_bot(self, ctx, user: discord.User):
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
    @commands.is_owner()
    async def unbanuser_bot(self, ctx, user: discord.User):
        db = self.bot.async_db["Main"].BANUser
        await db.delete_one({
            "User": user.id
        })
        await ctx.reply(embed=discord.Embed(title=f"{user.name}のBANを解除しました。", color=discord.Color.red()))

    @commands.command(name="make_error", hidden=True)
    @commands.is_owner()
    async def make_error_admin(self, ctx, errorname: str):
        raise Exception(errorname)
    
    @commands.command(name="set_ad", hidden=True)
    @commands.is_owner()
    async def set_ad(self, ctx, adurl: str):
        db = self.bot.async_db["Main"].SharkAds
        await db.replace_one(
            {"ID": 0}, 
            {"ID": 0, "ImageURL": adurl}, 
            upsert=True
        )
        await ctx.reply("広告を設定しました。")
    
    @commands.command(name="guilds_list", hidden=True)
    @commands.is_owner()
    async def guilds_list(self, ctx):
        text = ""
        for g in self.bot.guilds:
            text += f"{g.name} - {g.id}\n"
        await ctx.reply(embed=discord.Embed(title="サーバーリスト", description=f"{text}", color=discord.Color.green()))

    @commands.command(name="leave_guild", hidden=True)
    @commands.is_owner()
    async def leave_guild(self, ctx, guild: discord.Guild):
        await guild.leave()
        await ctx.reply(f"{guild.name}から退出しました。")

    @commands.command(name="get_invite", hidden=True)
    @commands.is_owner()
    async def get_invite(self, ctx, guild: discord.Guild):
        for i in guild.channels:
            try:
                inv = await i.create_invite()
                await ctx.reply(f"{inv.url}")
                return
            except:
                continue

    @commands.command(name="eval", hidden=True)
    @commands.is_owner()
    async def eval(self, ctx, *, text: str):
        await ctx.reply(f"Eval\n{eval(text)}")

    @commands.Cog.listener("on_guild_join")
    async def on_guild_join_blockuser(self, guild: discord.Guild):
        # await guild.leave()
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

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        error_details = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(embed=discord.Embed(title="コマンドが見つかりません。", color=discord.Color.red()))
        elif isinstance(error, commands.MissingRequiredArgument):
            missing_arg = error.param.name
            await ctx.send(embed=discord.Embed(title="引数が不足しています。", description=f"あと`{missing_arg}`が足りません。", color=discord.Color.red()))
        elif isinstance(error, commands.NotOwner):
            await ctx.send(embed=discord.Embed(title="管理者専用コマンドです。", color=discord.Color.red()))
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(embed=discord.Embed(title="権限がありません。", description="権限を持っている人が実行してください。", color=discord.Color.red()))
        elif isinstance(error, commands.CommandOnCooldown):
            a = None
            return a
        else:
            msg = await ctx.channel.send(embed=discord.Embed(title="予期しないエラーが発生しました。", description=f"```{sys.exc_info()}```", color=discord.Color.red()))
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