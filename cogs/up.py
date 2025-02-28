from discord.ext import commands
import discord
import traceback
import sys
import logging
import random
import time
import asyncio

class UpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> UpCog")

    @commands.Cog.listener("on_message")
    async def on_message_up_dicoall(self, message: discord.Message):
        if message.author.id == 903541413298450462:
            try:
                if "残りました。" in message.content:
                    db = self.bot.async_db["Main"].Dicoall
                    try:
                        dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
                    except:
                        return
                    if dbfind is None:
                        return
                    await message.channel.send(embed=discord.Embed(title="Upに失敗しました。", description="しばらく待ってから、\n</up:935190259111706754> をお願いします。", color=discord.Color.red()))
            except:
                return
            try:
                if "サーバーは上部に表示されます。" in message.embeds[0].description:
                    db = self.bot.async_db["Main"].Dicoall
                    try:
                        dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
                    except:
                        return
                    if dbfind is None:
                        return
                    await message.reply(embed=discord.Embed(title="Upを検知しました。", description="一時間後に通知します。", color=discord.Color.green()))
                    await asyncio.sleep(3600)
                    await message.channel.send(embed=discord.Embed(title="DicoallをUpしてね！", description="</up:935190259111706754> でアップ。", color=discord.Color.green()))
            except:
                return

    @commands.Cog.listener("on_message")
    async def on_message_bump_distopia(self, message: discord.Message):
        if message.author.id == 1300797373374529557:
            try:
                if "表示順を上げました" in message.embeds[0].description:
                    db = self.bot.async_db["Main"].Distopia
                    try:
                        dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
                    except:
                        return
                    if dbfind is None:
                        return
                    await message.reply(embed=discord.Embed(title="Bumpを検知しました。", description="二時間後に通知します。", color=discord.Color.green()))
                    await asyncio.sleep(7200)
                    await message.channel.send(embed=discord.Embed(title="DisTopiaをBumpしてね！", description="</bump:1309070135360749620> でBump。", color=discord.Color.green()))
                elif "レートリミットです。" in message.embeds[0].description:
                    db = self.bot.async_db["Main"].Distopia
                    try:
                        dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
                    except:
                        return
                    if dbfind is None:
                        return
                    await message.reply(embed=discord.Embed(title="Bumpに失敗しました。", description="しばらく待ってから、\n</bump:1309070135360749620> をお願いします。", color=discord.Color.red()))
            except:
                return

    @commands.Cog.listener("on_message")
    async def on_message_vote_sabachannel(self, message: discord.Message):
        if message.author.id == 1233072112139501608:
            try:
                if "サーバーの表示順位が上位に変更されました！" in message.embeds[0].description:
                    db = self.bot.async_db["Main"].SabaChannel
                    try:
                        dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
                    except:
                        return
                    if dbfind is None:
                        return
                    await message.reply(embed=discord.Embed(title="Voteを検知しました。", description="一時間後に通知します。", color=discord.Color.green()))
                    await asyncio.sleep(3600)
                    await message.channel.send(embed=discord.Embed(title="鯖チャンネルをVoteしてね！", description="</vote:1233072112139501608> でVote。", color=discord.Color.green()))
            except:
                return
            
    @commands.Cog.listener("on_message")
    async def on_message_bump_disboard(self, message: discord.Message):
        if message.author.id == 302050872383242240:
            try:
                if "表示順をアップ" in message.embeds[0].description:
                    db = self.bot.async_db["Main"].DisboardChannel
                    try:
                        dbfind = await db.find_one({"Channel": message.channel.id}, {"_id": False})
                    except:
                        return
                    if dbfind is None:
                        return
                    await message.reply(embed=discord.Embed(title="Bumpを検知しました。", description="二時間後に通知します。", color=discord.Color.green()))
                    await asyncio.sleep(7200)
                    await message.channel.send(embed=discord.Embed(title="DisboardをBumpしてね！", description="</bump:947088344167366698> でBump。", color=discord.Color.green()))
            except:
                return

    @commands.Cog.listener("on_message_edit")
    async def on_message_edit_dissoku(self, before: discord.Message, after: discord.Message):
        if after.author.id == 761562078095867916:
            try:
                if "をアップしたよ!" in after.embeds[0].fields[0].name:
                    db = self.bot.async_db["Main"].DissokuChannel
                    try:
                        dbfind = await db.find_one({"Channel": after.channel.id}, {"_id": False})
                    except:
                        return
                    if dbfind is None:
                        return
                    await after.reply(embed=discord.Embed(title="Upを検知しました。", description="一時間後に通知します。", color=discord.Color.green()))
                    await asyncio.sleep(3600)
                    await after.channel.send(embed=discord.Embed(title="ディス速をUpしてね！", description="</dissoku up:828002256690610256> でアップ。", color=discord.Color.green()))
                elif "失敗しました" in after.embeds[0].fields[0].name:
                    db = self.bot.async_db["Main"].DissokuChannel
                    try:
                        dbfind = await db.find_one({"Channel": after.channel.id}, {"_id": False})
                    except:
                        return
                    if dbfind is None:
                        return
                    await after.reply(embed=discord.Embed(title="Upに失敗しました。", description="しばらく待ってから</dissoku up:828002256690610256>を実行してください。", color=discord.Color.red()))
            except:
                return    

    @commands.hybrid_group(name="bump", description="DicoallのUp通知を有効化します。", fallback="dicoall")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def up_dicoall(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].Dicoall
        msg = await ctx.reply(embed=discord.Embed(title="Dicoallの通知をONにしますか？", description="<:Check:1325247594963927203> .. ON\n<:Cancel:1325247762266193993> .. OFF", color=discord.Color.green()))
        await msg.add_reaction("<:Check:1325247594963927203>")
        await msg.add_reaction("<:Cancel:1325247762266193993>")
        try:
            r, m = await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id and not u.bot and ctx.author.id == u.id, timeout=30)
            if r.emoji.id == 1325247594963927203:
                await db.replace_one(
                    {"Channel": ctx.channel.id},
                    {"Channel": ctx.channel.id},
                    upsert=True
                )
                await ctx.channel.send(embed=discord.Embed(title="Dicoallの通知をONにしました。", color=discord.Color.green()))
            else:
                await db.delete_one(
                    {"Channel": ctx.channel.id}
                )
                await ctx.channel.send(embed=discord.Embed(title="Dicoallの通知をOFFにしました。", color=discord.Color.red()))
        except:
            return
        
    @up_dicoall.command(name="distopia", description="DisTopiaの通知します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def up_distopia(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].Distopia
        msg = await ctx.reply(embed=discord.Embed(title="Distopiaの通知をONにしますか？", description="<:Check:1325247594963927203> .. ON\n<:Cancel:1325247762266193993> .. OFF", color=discord.Color.green()))
        await msg.add_reaction("<:Check:1325247594963927203>")
        await msg.add_reaction("<:Cancel:1325247762266193993>")
        try:
            r, m = await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id and not u.bot and ctx.author.id == u.id, timeout=30)
            if r.emoji.id == 1325247594963927203:
                await db.replace_one(
                    {"Channel": ctx.channel.id},
                    {"Channel": ctx.channel.id},
                    upsert=True
                )
                await ctx.channel.send(embed=discord.Embed(title="Distopiaの通知をONにしました。", color=discord.Color.green()))
            else:
                await db.delete_one(
                    {"Channel": ctx.channel.id}
                )
                await ctx.channel.send(embed=discord.Embed(title="Distopiaの通知をOFFにしました。", color=discord.Color.red()))
        except:
            return
        
    @up_dicoall.command(name="sabachannel", description="鯖チャンネルの通知をします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def sabachannel_vote(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].SabaChannel
        msg = await ctx.reply(embed=discord.Embed(title="鯖チャンネルの通知をONにしますか？", description="<:Check:1325247594963927203> .. ON\n<:Cancel:1325247762266193993> .. OFF", color=discord.Color.green()))
        await msg.add_reaction("<:Check:1325247594963927203>")
        await msg.add_reaction("<:Cancel:1325247762266193993>")
        try:
            r, m = await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id and not u.bot and ctx.author.id == u.id, timeout=30)
            if r.emoji.id == 1325247594963927203:
                await db.replace_one(
                    {"Channel": ctx.channel.id},
                    {"Channel": ctx.channel.id},
                    upsert=True
                )
                await ctx.channel.send(embed=discord.Embed(title="鯖チャンネルの通知をONにしました。", color=discord.Color.green()))
            else:
                await db.delete_one(
                    {"Channel": ctx.channel.id}
                )
                await ctx.channel.send(embed=discord.Embed(title="鯖チャンネルの通知をOFFにしました。", color=discord.Color.red()))
        except:
            await ctx.reply(f"{sys.exc_info()}")
            return
        
    @up_dicoall.command(name="dissoku", description="ディス速の通知をします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def dissoku_up(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].DissokuChannel
        msg = await ctx.reply(embed=discord.Embed(title="ディス速の通知をONにしますか？", description="<:Check:1325247594963927203> .. ON\n<:Cancel:1325247762266193993> .. OFF", color=discord.Color.green()))
        await msg.add_reaction("<:Check:1325247594963927203>")
        await msg.add_reaction("<:Cancel:1325247762266193993>")
        try:
            r, m = await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id and not u.bot and ctx.author.id == u.id, timeout=30)
            if r.emoji.id == 1325247594963927203:
                await db.replace_one(
                    {"Channel": ctx.channel.id},
                    {"Channel": ctx.channel.id},
                    upsert=True
                )
                await ctx.channel.send(embed=discord.Embed(title="ディス速の通知をONにしました。", color=discord.Color.green()))
            else:
                await db.delete_one(
                    {"Channel": ctx.channel.id}
                )
                await ctx.channel.send(embed=discord.Embed(title="ディス速の通知をOFFにしました。", color=discord.Color.red()))
        except:
            await ctx.reply(f"{sys.exc_info()}")
            return
        
    @up_dicoall.command(name="disboard", description="Disboardの通知をします。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def dissoku_up(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].DisboardChannel
        msg = await ctx.reply(embed=discord.Embed(title="Disboard通知をONにしますか？", description="<:Check:1325247594963927203> .. ON\n<:Cancel:1325247762266193993> .. OFF", color=discord.Color.green()))
        await msg.add_reaction("<:Check:1325247594963927203>")
        await msg.add_reaction("<:Cancel:1325247762266193993>")
        try:
            r, m = await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id and not u.bot and ctx.author.id == u.id, timeout=30)
            if r.emoji.id == 1325247594963927203:
                await db.replace_one(
                    {"Channel": ctx.channel.id},
                    {"Channel": ctx.channel.id},
                    upsert=True
                )
                await ctx.channel.send(embed=discord.Embed(title="Disboardの通知をONにしました。", color=discord.Color.green()))
            else:
                await db.delete_one(
                    {"Channel": ctx.channel.id}
                )
                await ctx.channel.send(embed=discord.Embed(title="Disboardの通知をOFFにしました。", color=discord.Color.red()))
        except:
            await ctx.reply(f"{sys.exc_info()}")
            return

async def setup(bot):
    await bot.add_cog(UpCog(bot))