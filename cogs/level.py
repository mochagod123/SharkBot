from discord.ext import commands
import discord
import traceback
import sys
import logging
import asyncio
from PIL import Image, ImageDraw, ImageFont
import asyncio
import aiohttp
import io
import random

class LevelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> LevelCog")

    async def check_level_enabled(self, guild: discord.Guild):
        db = self.bot.async_db["Main"].LevelingSetting
        try:
            dbfind = await db.find_one({"Guild": guild.id}, {"_id": False})
        except:
            return False
        if dbfind is None:
            return False
        else:
            return True

    async def new_user_write(self, guild: discord.Guild, user: discord.User):
        try:
            db = self.bot.async_db["Main"].Leveling
            await db.replace_one(
                {"Guild": guild.id, "User": user.id}, 
                {"Guild": guild.id, "User": user.id, "Level": 0, "XP": 1}, 
                upsert=True
            )
        except:
            return
        
    async def user_write(self, guild: discord.Guild, user: discord.User, level: int, xp: int):
        try:
            db = self.bot.async_db["Main"].Leveling
            await db.replace_one(
                {"Guild": guild.id, "User": user.id}, 
                {"Guild": guild.id, "User": user.id, "Level": level, "XP": xp}, 
                upsert=True
            )
        except:
            return
        
    async def get_level(self, guild: discord.Guild, user: discord.User):
        try:
            db = self.bot.async_db["Main"].Leveling
            try:
                dbfind = await db.find_one({"Guild": guild.id, "User": user.id}, {"_id": False})
            except:
                return None
            if dbfind is None:
                return None
            else:
                return dbfind["Level"]
        except:
            return
        
    async def get_xp(self, guild: discord.Guild, user: discord.User):
        try:
            db = self.bot.async_db["Main"].Leveling
            try:
                dbfind = await db.find_one({"Guild": guild.id, "User": user.id}, {"_id": False})
            except:
                return None
            if dbfind is None:
                return None
            else:
                return dbfind["XP"]
        except:
            return
        
    async def set_user_image(self, user: discord.User, url: str):
        try:
            db = self.bot.async_db["Main"].LevelingBackImage
            await db.replace_one(
                {"User": user.id}, 
                {"User": user.id, "Image": url}, 
                upsert=True
            )
        except:
            return
        
    async def get_user_image(self, user: discord.User):
        try:
            db = self.bot.async_db["Main"].LevelingBackImage
            try:
                dbfind = await db.find_one({"User": user.id}, {"_id": False})
            except:
                return None
            if dbfind is None:
                return None
            else:
                return dbfind["Image"]
        except:
            return
        
    async def set_channel(self, guild: discord.Guild, channel: discord.TextChannel = None):
        try:
            if channel == None:
                db = self.bot.async_db["Main"].LevelingUpAlertChannel
                await db.delete_one(
                    {"Guild": guild.id}
                )
                return
            db = self.bot.async_db["Main"].LevelingUpAlertChannel
            await db.replace_one(
                {"Guild": guild.id, "Channel": channel.id}, 
                {"Guild": guild.id, "Channel": channel.id}, 
                upsert=True
            )
        except:
            return

    async def get_channel(self, guild: discord.Guild):
        try:
            db = self.bot.async_db["Main"].LevelingUpAlertChannel
            try:
                dbfind = await db.find_one({"Guild": guild.id}, {"_id": False})
            except:
                return None
            if dbfind is None:
                return None
            else:
                return dbfind["Channel"]
        except:
            return
        
    async def set_role(self, guild: discord.Guild, level: int, role: discord.Role = None, ):
        db = self.bot.async_db["Main"].LevelingUpRole
        try:
            if role is None:
                await db.delete_one({"Guild": guild.id})
                return
            
            await db.replace_one(
                {"Guild": guild.id}, 
                {"Guild": guild.id, "Role": role.id, "Level": level}, 
                upsert=True
            )
        except Exception as e:
            print(f"Error in set_role: {e}")

    async def get_role(self, guild: discord.Guild, level: int):
        db = self.bot.async_db["Main"].LevelingUpRole
        try:
            dbfind = await db.find_one({"Guild": guild.id, "Level": level}, {"_id": False})
            return dbfind["Role"] if dbfind else None
        except Exception as e:
            return None

    @commands.Cog.listener("on_message")
    async def on_message_level(self, message: discord.Message):
        if message.author.bot:
            return
        try:
            enabled = await self.check_level_enabled(message.guild)
        except:
            return
        if enabled:
            db = self.bot.async_db["Main"].Leveling
            try:
                dbfind = await db.find_one({"Guild": message.guild.id, "User": message.author.id}, {"_id": False})
            except:
                return
            if dbfind is None:
                return await self.new_user_write(message.guild, message.author)
            else:
                await self.user_write(message.guild, message.author, dbfind["Level"], dbfind["XP"] + random.randint(0, 2))
                xp = await self.get_xp(message.guild, message.author)
                if xp > 100:
                    lv = await self.get_level(message.guild, message.author)
                    await self.user_write(message.guild, message.author, lv + 1, 0)
                    lvg = await self.get_level(message.guild, message.author)
                    cha = await self.get_channel(message.guild)
                    role = await self.get_role(message.guild, lvg)
                    if role:
                        grole = message.guild.get_role(role)
                        if grole:
                            await message.author.add_roles(grole)
                    if cha:
                        await self.bot.get_channel(cha).send(embed=discord.Embed(title=f"`{message.author.name}`さんの\nレベルが{lvg}になったよ！", color=discord.Color.gold()))
                    else:
                        return await message.reply(f"レベルが「{lvg}レベル」になったよ！")
        else:
            return

    @commands.hybrid_group(name="level", description="レベルを有効化&無効化します。", fallback="setting")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def level_setting(self, ctx):
        await ctx.defer()
        db = self.bot.async_db["Main"].LevelingSetting
        msg = await ctx.reply(embed=discord.Embed(title="レベリングをONにしますか？", description=f"<:Check:1325247594963927203> .. ON\n<:Cancel:1325247762266193993> .. OFF", color=discord.Color.green()))
        await msg.add_reaction("<:Check:1325247594963927203>")
        await msg.add_reaction("<:Cancel:1325247762266193993>")
        try:
            r, m = await self.bot.wait_for("reaction_add", check=lambda r, u: r.message.id == msg.id and not u.bot and ctx.author.id == u.id, timeout=30)
            if r.emoji.id == 1325247594963927203:
                await db.replace_one(
                    {"Guild": ctx.guild.id},
                    {"Guild": ctx.guild.id},
                    upsert=True
                )
                await ctx.channel.send(embed=discord.Embed(title="レベリングをONにしました。", color=discord.Color.green()))
            else:
                await db.delete_one(
                    {"Guild": ctx.guild.id}
                )
                await ctx.channel.send(embed=discord.Embed(title="レベリングをOFFにしました。", color=discord.Color.red()))
        except:
            return await ctx.reply(f"{sys.exc_info()}")
        
    @level_setting.command(name="show", description="レベルを見ます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def level_show(self, ctx: commands.Context):
        await ctx.defer()
        try:
            enabled = await self.check_level_enabled(ctx.guild)
        except:
            return
        if ctx.author.avatar:
            avatar = ctx.author.avatar.url
        else:
            avatar = ctx.author.default_avatar.url
        if enabled:
            lv = await self.get_level(ctx.guild, ctx.author)
            if lv == None:
                return await ctx.reply(embed=discord.Embed(title=f"`{ctx.author.name}`のレベル", description=f"レベル: 「0レベル」\nXP: 「0XP」", color=discord.Color.blue()).set_thumbnail(url=avatar))
            xp = await self.get_xp(ctx.guild, ctx.author)
            if xp == None:
                return await ctx.reply(embed=discord.Embed(title=f"`{ctx.author.name}`のレベル", description=f"レベル: 「0レベル」\nXP: 「0XP」", color=discord.Color.blue()).set_thumbnail(url=avatar))
            await ctx.reply(embed=discord.Embed(title=f"`{ctx.author.name}`のレベル", description=f"レベル: 「{lv}レベル」\nXP: 「{xp}XP」", color=discord.Color.blue()).set_thumbnail(url=avatar))
        else:
            return await ctx.reply(embed=discord.Embed(title="レベルは無効です。", color=discord.Color.red()))
        
    @level_setting.command(name="channel", description="レベルアップの通知のチャンネルを設定します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_channels=True)
    async def level_channel(self, ctx, チャンネル: discord.TextChannel = None):
        await ctx.defer()
        try:
            enabled = await self.check_level_enabled(ctx.guild)
        except:
            return
        if enabled:
            if チャンネル:
                await self.set_channel(ctx.guild, チャンネル)
                await ctx.reply(embed=discord.Embed(title="レベルアップの通知チャンネルを設定しました。", color=discord.Color.green()))
            else:
                await self.set_channel(ctx.guild)
                await ctx.reply(embed=discord.Embed(title="レベルアップの通知チャンネルを削除しました。", color=discord.Color.green()))
        else:
            return await ctx.reply(embed=discord.Embed(title="レベルは無効です。", color=discord.Color.red()))

    @level_setting.command(name="role", description="特定のレベルになるとロールを付けます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def level_role(self, ctx, レベル: int, ロール: discord.Role = None):
        await ctx.defer()
        try:
            enabled = await self.check_level_enabled(ctx.guild)
        except:
            return await ctx.reply(embed=discord.Embed(title="レベルは無効です。", color=discord.Color.red()))
        if enabled:
            if not ロール:
                await self.set_role(ctx.guild, レベル)
                return await ctx.reply(embed=discord.Embed(title=f"{レベル}レベルになってもロールをもらえなくしました。", color=discord.Color.green()))
            await self.set_role(ctx.guild, レベル, ロール)
            return await ctx.reply(embed=discord.Embed(title=f"{レベル}レベルになるとロールを付与するようにしました。", color=discord.Color.green()))
        else:
            return await ctx.reply(embed=discord.Embed(title="レベルは無効です。", color=discord.Color.red()))

    @level_setting.command(name="set-image", description="背景画像を見ます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def level_image_url(self, ctx, 画像url: str):
        await ctx.defer()
        await self.set_user_image(ctx.author, 画像url)
        await ctx.reply(embed=discord.Embed(title="画像を設定しました。", color=discord.Color.green()).set_image(url=画像url))

    @level_setting.command(name="image", description="レベルカードを作ります。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def level_image(self, ctx: commands.Context):
        await ctx.defer()
        try:
            enabled = await self.check_level_enabled(ctx.guild)
        except:
            return
        if enabled:
            lv = await self.get_level(ctx.guild, ctx.author)
            xp = await self.get_xp(ctx.guild, ctx.author)

            # ユーザーのアバター画像を取得
            async with aiohttp.ClientSession() as session:
                async with session.get(ctx.author.avatar.url) as response:
                    avatar_content = await response.read()

            burl = await self.get_user_image(ctx.author)
            if not burl == None:
                async with aiohttp.ClientSession() as session:
                    async with session.get(burl) as response:
                        backimage = await response.read()
            else:
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://aipict.com/wp-content/uploads/2022/09/beach01.png") as response:
                        backimage = await response.read()

            # ベース画像とアバターの準備
            imagecard = io.BytesIO(avatar_content)
            background = Image.open(io.BytesIO(backimage)).convert("RGBA").resize((671, 291))
            avatar = Image.open(imagecard).convert("RGBA")
            avatar = avatar.resize((200, 200))

            # アバターを丸くトリミング
            mask = Image.new("L", avatar.size, 0)
            draw = ImageDraw.Draw(mask)
            radius = min(avatar.size) // 2
            center = (avatar.size[0] // 2, avatar.size[1] // 2)
            draw.ellipse((center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius), fill=255)

            # 背景にアバターを描画
            background.paste(avatar, (50, 50), mask=mask)

            # テキスト描画用の透明レイヤーを作成
            overlay = Image.new("RGBA", background.size, (255, 255, 255, 0))
            overlay_draw = ImageDraw.Draw(overlay)

            # フォント設定
            font_path = 'C:/Windows/Fonts/meiryob.ttc'  # フォントのパスを適宜変更
            font_large = ImageFont.truetype(font_path, 50)
            font_small = ImageFont.truetype(font_path, 30)

            level_text = f"{lv}レベル"
            level_position = (300, 40)
            level_bbox = overlay_draw.textbbox(level_position, level_text, font=font_large)
            level_background = (
                level_bbox[0] - 10,
                level_bbox[1] - 5,
                level_bbox[2] + 10,
                level_bbox[3] + 5,
            )

            # レベル背景を描画
            overlay_draw.rectangle(level_background, fill=(200, 200, 200, 128))

            # XPテキストの設定
            xp_text = f"{xp}XP"
            xp_position = (300, 100)
            xp_bbox = overlay_draw.textbbox(xp_position, xp_text, font=font_small)
            xp_background = (
                xp_bbox[0] - 10,
                xp_bbox[1] - 5,
                xp_bbox[2] + 10,
                xp_bbox[3] + 5,
            )

            # XP背景を描画
            overlay_draw.rectangle(xp_background, fill=(200, 200, 200, 128))

            # テキストを描画
            base_image = Image.alpha_composite(background, overlay)
            draw = ImageDraw.Draw(base_image)
            draw.text(level_position, level_text, fill=(0, 0, 0), font=font_large)
            draw.text(xp_position, xp_text, fill=(0, 0, 0), font=font_small)

            # 画像を保存して送信
            ios = io.BytesIO()
            base_image.save(ios, format="PNG")
            ios.seek(0)
            await ctx.reply(file=discord.File(ios, "level.png"))
            ios.close()
        else:
            return await ctx.reply(embed=discord.Embed(title="レベルは無効です。", color=discord.Color.red()))

async def setup(bot):
    await bot.add_cog(LevelCog(bot))