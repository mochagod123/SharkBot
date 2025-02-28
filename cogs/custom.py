from discord.ext import commands
import discord
import io
import traceback
from functools import partial
import sys
from discord import app_commands
import json
import requests
import logging
import urllib
import random
import re
import aiohttp
import time
import asyncio
from PIL import ImageFont, Image, ImageDraw

COOLDOWN_TIME = 10
user_last_message_time = {}

NG_WORDS = [
    # 一般的な下ネタ（日本語）
    "ちんこ", "まんこ", "おっぱい", "アナル", "フェラ", "セックス", "レイプ", "精子", "膣", "陰茎",
    "陰部", "射精", "勃起", "変態", "エロ", "裸", "スカトロ", "童貞", "処女", "肉便器", "中出し", "ハメ撮り",
    
    # 一般的な下ネタ（英語）
    "fuck", "shit", "bitch", "cock", "dick", "pussy", "ass", "boobs", "tits",
    "anal", "blowjob", "cum", "semen", "vagina", "penis", "rape", "orgasm", "masturbation",
    
    # その他、問題になりそうな言葉（ネットスラングなど）
    "きんたま", "ズリネタ", "オナニー", "セフレ", "孕む", "潮吹き", "クリトリス",
    "ガチホモ", "ホモ", "ゲイポルノ", "ロリコン", "ペド", "ペドフィリア", "近親相姦"
]

class HelpView(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self.pages = self.generate_pages()
        self.current_page = 0
        self.set_page_footer()

    def generate_pages(self):
        visible_commands = [cmd for cmd in self.bot.commands if not cmd.hidden]

        categories = {}
        for command in visible_commands:
            if isinstance(command, commands.HybridGroup):
                # グループコマンド（サブコマンドを含む）
                subcommands = [
                    f"`/{command.name} {sub.name}`: {sub.description or '説明なし'}"
                    for sub in command.commands if not sub.hidden
                ]
                if command.invoke_without_command:
                    subcommands.insert(0, f"`/{command.name} {command.fallback}`: {command.description or '説明なし'}")
                categories[command.name] = subcommands
            elif isinstance(command, commands.HybridCommand):
                # 一般コマンド
                cog_name = "一般"
                if cog_name not in categories:
                    categories[cog_name] = []
                categories[cog_name].append(f"`/{command.name}`: {command.description or '説明なし'}")

        field_count = 0
        pages = []
        current_embed = None
        for category, commands_list in categories.items():
            if current_embed is None:
                current_embed = discord.Embed(
                    title=f"ヘルプ",
                    description="以下は利用可能なコマンド一覧です。",
                    color=discord.Color.blue()
                )

            for command in commands_list:
                if field_count >= 10:  # フィールド数が20を超えたら新しいEmbedを作成
                    pages.append(current_embed)
                    current_embed = discord.Embed(
                        title=f"ヘルプ",
                        description="以下は利用可能なコマンド一覧です。",
                        color=discord.Color.blue()
                    )
                    field_count = 0

                current_embed.add_field(name=command.split(":")[0], value=command.split(":")[1], inline=False)
                field_count += 1

        if not pages:
            pages.append(discord.Embed(
                title="ヘルプ",
                description="現在利用可能なコマンドはありません。",
                color=discord.Color.red()
            ))
        return pages

    def set_page_footer(self):
        total_pages = len(self.pages)
        embed = self.pages[self.current_page]
        embed.set_footer(text=f"ページ {self.current_page + 1} / {total_pages}")

    @discord.ui.button(label="戻る", style=discord.ButtonStyle.secondary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = (self.current_page - 1) % len(self.pages)
        self.set_page_footer()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(label="次へ", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = (self.current_page + 1) % len(self.pages)
        self.set_page_footer()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(label="閉じる", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="ヘルプメニューを閉じました。", embed=None, view=None)


class CustomCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> CustomCog")

    async def get_prefix(self, guild: discord.Guild):
        cp = self.bot.async_db["Main"].CustomPrefix
        try:
            pf = await cp.find_one({"Guild": guild.id}, {"_id": False})
        except:
            return "?"
        if pf is None:
            return "?"
        return pf["Prefix"]
    
    async def get_commands(self, guild: discord.Guild):
        try:
            p = await self.get_prefix(guild)
            cp = self.bot.async_db["Main"].CustomCommand
            async with cp.find({"Guild": guild.id}) as cursor:
                commands = await cursor.to_list(length=None)

            return [p + command["Name"] for command in commands]
        except:
            return ["登録なし"]
        
    async def get_command(self, guild: discord.Guild, cmdname: str):
        try:
            p = await self.get_prefix(guild)
            cp = self.bot.async_db["Main"].CustomCommand
            try:
                dbfind = await cp.find_one({"Guild": guild.id, "Name": cmdname.split(" ")[0].replace(p, "")}, {"_id": False})
            except:
                return None
            if dbfind is None:
                return None
            return dbfind["Program"]
        except:
            return None
        
    async def check_level_enabled_cm(self, guild: discord.Guild):
        db = self.bot.async_db["Main"].LevelingSetting
        try:
            dbfind = await db.find_one({"Guild": guild.id}, {"_id": False})
        except:
            return False
        if dbfind is None:
            return False
        else:
            return True

    async def get_level_cm(self, guild: discord.Guild, user: discord.User):
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

    def replace_random_choice(text):
        matches = re.findall(r'\((.*?)\)', text)  # すべての () 内の文字列を取得
        for match in matches:
            replacement = random.choice(match.split(","))  # `,` で分割しランダム選択
            text = re.sub(r'\(' + re.escape(match) + r'\)', replacement, text, 1)  # 1回のみ置換

        return text  # 変更後の文字列を返す

    def censor_text(self, text, ng_words, replacement="***"):
        pattern = re.compile("|".join(map(re.escape, ng_words)), re.IGNORECASE)
        return pattern.sub(replacement, text)

    async def run_program(self, message: discord.Message, program: str, arsgs: list):
        try:
            cmd = program.split("\n")
            arg1 = "None"
            arg2 = "None"
            arg3 = "None"
            memory = {}
            lv = await self.check_level_enabled_cm(message.guild)
            async def _replace(st: str):
                r1 = st.replace("[Name]", message.author.name).replace("[Avatar]", message.author.avatar.url).replace("[arg1]", arg1).replace("[arg2]", arg2).replace("[arg3]", arg3).replace("\\n", "\n").replace("[channel]", f"{message.channel.name}")
                r1 = r1.replace("[Memory]", f"{memory}")
                memcheck = re.findall(r"\[.*?\]", r1)
                if memcheck:
                    for m in memcheck:
                        key = m.strip("[]")  # [] を削除
                        if key in memory:
                            r1 = re.sub(r"\[.*?\]", memory[key], r1, 1)
                if lv:
                    l = await self.get_level_cm(message.guild, message.author)
                    if l:
                        r1 = r1.replace("[level]", f"{l}")
                return self.censor_text(r1, NG_WORDS)
            for p in cmd:
                pp = p.split(">")[0]
                args = p.split(">")[1:]
                if pp == "echo":
                    await message.channel.send(await _replace(args[0]))
                    await asyncio.sleep(2)
                elif pp == "embed":
                    await message.channel.send(embed=discord.Embed(title=await _replace(args[0]), description=await _replace(args[1])))
                    await asyncio.sleep(2)
                elif pp == "getargs1":
                    try:
                        arg1 = arsgs[1]
                    except:
                        arg1 = "None"
                elif pp == "getargs2":
                    try:
                        arg2 = arsgs[2]
                    except:
                        arg2 = "None"
                elif pp == "getargs3":
                    try:
                        arg3 = arsgs[3]
                    except:
                        arg3 = "None"
                elif pp == "printargs":
                    await message.reply(f"{arsgs}")
                    await asyncio.sleep(2)
                elif pp == "addrole":
                    role = message.guild.get_role(int(args[0]))
                    await message.author.add_roles(role)
                    await asyncio.sleep(2)
                elif pp == "removerole":
                    role = message.guild.get_role(int(args[0]))
                    await message.author.remove_roles(role)
                    await asyncio.sleep(2)
                elif pp == "requests":
                    try:
                        # https://kenji123.pythonanywhere.com/req?url=URL
                        async with aiohttp.ClientSession() as session:
                            async with session.get("https://sh.yuushi.online/req?url=" + await _replace(args[0])) as response:
                                memory[await _replace(args[1])] = await response.text()
                    except:
                        memory[await _replace(args[1])] = f"{sys.exc_info()}"
                elif pp == "json": #json>テキスト>JSONの保存先の値名
                    try:
                        memory[await _replace(args[1])] = json.loads(await _replace(args[0]))
                    except:
                        continue
                elif pp == "json_load": #json_load>JSONのデータ名>出す値のKey>保存先の値名
                    try:
                        memory[await _replace(args[2])] = memory[await _replace(args[0])][await _replace(args[1])]
                    except:
                        continue
                elif pp == "addreact":
                    try:
                        await message.add_reaction(await _replace(args[0]))
                    except:
                        continue
                elif pp == "echo_id":
                    try:
                        id = self.bot.get_channel(int(await _replace(args[0])))
                        await id.send(await _replace(args[1]))
                    except:
                        continue
                elif pp == "memory_add":
                    try:
                        memory[await _replace(args[0])] = await _replace(args[1])
                    except:
                        continue
                elif pp == "memory_remove":
                    try:
                        del memory[await _replace(args[0])]
                    except:
                        continue
                elif pp == "save":
                    try:
                        db = self.bot.async_db["Main"].CustomCommandSaveData
                        await db.replace_one(
                            {"User": message.author.id, "SaveName": await _replace(args[0])}, 
                            {"User": message.author.id, "SaveName": await _replace(args[0]), "SaveData": await _replace(args[1])}, 
                            upsert=True
                        )
                    except:
                        continue
                elif pp == "load":
                    try:
                        db = self.bot.async_db["Main"].CustomCommandSaveData
                        try:
                            dbfind = await db.find_one({"User": message.author.id, "SaveName": await _replace(args[0])}, {"_id": False})
                        except:
                            memory[await _replace(args[1])] = "None"
                        if dbfind is None:
                            memory[await _replace(args[1])] = "None"
                        memory[await _replace(args[1])] = dbfind["SaveData"]
                    except:
                        continue
                elif pp == "//":
                    continue
                else:
                    continue
            return None
        except:
            return f"{sys.exc_info()}"

    @commands.Cog.listener("on_message")
    async def on_message_custom(self, message: discord.Message):
        if message.author.bot:
            return
        c = await self.get_command(message.guild, message.content)
        if not c:
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
        cu = await self.run_program(message, c, message.content.split(" "))

    async def dynamic_choices(self, interaction: discord.Interaction, current: str):
        options = []
        for command in self.bot.tree.get_commands():
            if isinstance(command, app_commands.Group):
                options.append(command.name)
        filtered = [
            app_commands.Choice(name=option, value=option)
            for option in options if current.lower() in option.lower()
        ]
        return filtered[:25]

    @commands.hybrid_command(name = "help", with_app_command = True, description = "ヘルプを見ます。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @app_commands.autocomplete(カテゴリ=dynamic_choices)
    async def help_slash(self, ctx: commands.Context, カテゴリ: str = None):
        await ctx.defer()
        if カテゴリ:
            return await ctx.reply(f"以下のページをご覧ください。\nhttps://www.sharkbot.xyz/commands#:~:text={カテゴリ}")
        return await ctx.reply(f"以下のページをご覧ください。\nhttps://www.sharkbot.xyz/commands")
        if not カテゴリ:
            view = HelpView(self.bot)
            return await ctx.reply(embed=view.pages[0], view=view)
        if カテゴリ == "commands":
            prefix = await self.get_prefix(ctx.guild)
            cmds = await self.get_commands(ctx.guild)
            await ctx.reply(embed=discord.Embed(title="`commands`プラグイン", description=f"{"\n".join(cmds)}", color=discord.Color.blue()).set_footer(text=f"Prefix: {prefix}"))
        elif カテゴリ == "help":
            await ctx.reply(embed=discord.Embed(title="`help`プラグイン", color=discord.Color.blue()).add_field(name="`help`", value="ヘルプを見ます。"))
        else:
            embed = discord.Embed(title=f"`{カテゴリ}`プラグイン", color=discord.Color.blue())
            for command in self.bot.tree.get_commands():
                if isinstance(command, app_commands.Group):
                    if command.name == f"{カテゴリ}":
                        for subcommand in command.commands:
                            embed.add_field(name=f"`{subcommand.name}`", value=f"{subcommand.description}")
                        break
            return await ctx.reply(embed=embed)

    @commands.hybrid_group(name="custom", description="カスタムコマンドのPrefixを設定します。", fallback="prefix")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True)
    async def custom_prefix(self, ctx: commands.Context, prefix: str):
        db = self.bot.async_db["Main"].CustomPrefix
        await db.replace_one(
            {"Guild": ctx.guild.id, "Prefix": prefix}, 
            {"Guild": ctx.guild.id, "Prefix": prefix}, 
            upsert=True
        )
        await ctx.reply(embed=discord.Embed(title="Prefixを設定しました。", description=f"`{prefix}`", color=discord.Color.green()))

    @custom_prefix.command(name="create", description="カスタムコマンドを作成します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True)
    async def custom_create(self, ctx):
        try:
            class send(discord.ui.Modal):
                def __init__(self, database) -> None:
                    super().__init__(title="カスタムコマンドの作成", timeout=None)
                    self.db = database
                    self.etitle = discord.ui.TextInput(label="コマンド名",placeholder="animal",style=discord.TextStyle.long,required=True)
                    self.desc = discord.ui.TextInput(label="プログラム",placeholder="echo>I am Shark.",style=discord.TextStyle.long,required=True)
                    self.add_item(self.etitle)
                    self.add_item(self.desc)
                async def on_submit(self, interaction: discord.Interaction) -> None:
                    db = self.db["Main"].CustomCommand
                    await db.replace_one(
                        {"Guild": ctx.guild.id, "Name": self.etitle.value}, 
                        {"Guild": ctx.guild.id, "Name": self.etitle.value, "Program": self.desc.value}, 
                        upsert=True
                    )
                    await interaction.response.send_message(embed=discord.Embed(title="カスタムコマンドを作成しました。", color=discord.Color.green()))
            await ctx.interaction.response.send_modal(send(self.bot.async_db))
        except:
            return
        
    @custom_prefix.command(name="remove", description="カスタムコマンドを削除します。")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True)
    async def custom_remove(self, ctx, コマンド名: str):
        try:
            db = self.bot.async_db["Main"].CustomCommand
            result = await db.delete_one({
                "Guild": ctx.guild.id, "Name": コマンド名,
            })
            await ctx.reply(embed=discord.Embed(title="カスタムコマンドを削除しました。", color=discord.Color.red()))
        except:
            await ctx.reply(f"{sys.exc_info()}")
            return

async def setup(bot):
    await bot.add_cog(CustomCog(bot))