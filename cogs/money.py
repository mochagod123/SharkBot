from discord.ext import commands, tasks
import discord
import traceback
import sys
from unbelievaboat import Client
import logging
import time
import aiofiles
import asyncio
import aiohttp
import aiosqlite
import json
import re
import random
import string
from itertools import islice

from collections import Counter

def compress_list(lst):
    count = Counter(lst)
    return [f"{item} ×{count[item]}" if count[item] > 1 else item for item in count]


def randomname(n):
    randlst = [random.choice(string.ascii_letters + string.digits) for i in range(n)]
    return ''.join(randlst)

def chunk_list_iter(lst, size):
    it = iter(lst)
    return iter(lambda: list(islice(it, size)), [])

class Paginator(discord.ui.View):
    def __init__(self, embeds):
        super().__init__()
        self.embeds = embeds
        self.index = 0

    async def update_message(self, interaction):
        await interaction.response.edit_message(embed=self.embeds[self.index], view=self)

    @discord.ui.button(label="◀", style=discord.ButtonStyle.gray, disabled=True)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index -= 1
        self.next_page.disabled = False
        if self.index == 0:
            self.previous_page.disabled = True
        await self.update_message(interaction)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.gray)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index += 1
        self.previous_page.disabled = False
        if self.index == len(self.embeds) - 1:
            self.next_page.disabled = True
        await self.update_message(interaction)

    @discord.ui.button(label="❌", style=discord.ButtonStyle.gray)
    async def close_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="ページを閉じました。", embed=None, view=None)

STOCKS = {"AAPL": 150, "TSLA": 700, "GOOGL": 2800}

COOLDOWN_TIME_WORK = 5
cooldown_work_time = {}

class MoneyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("../Token.json") as tk:
            self.tkj = json.loads(tk.read())
            self.mt = self.tkj["MoneyBotToken"]
        print(f"init -> MoneyCog")

    @commands.hybrid_group(name="money", description="サーバー内通貨を作成します。", fallback="make")
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 300, type=commands.BucketType.guild)
    async def money_make(self, ctx: commands.Context, 通貨名: str):
        await ctx.defer()
        db = self.bot.async_db["Main"].ServerMoney
        try:
            profile = await db.find_one({
                "Guild": ctx.guild.id
            })
            if profile is None:
                await db.replace_one(
                    {"Guild": ctx.guild.id, "User": ctx.author.id}, 
                    {"Guild": ctx.guild.id, "User": ctx.author.id, "Money": 0, "CoinName": 通貨名}, 
                    upsert=True
                )
                await ctx.reply(embed=discord.Embed(title="通貨を作成しました。", description=f"名前: {通貨名}", color=discord.Color.green()))
            else:
                await ctx.reply(embed=discord.Embed(title="すでに経済が存在します。", color=discord.Color.red()))
        except:
            await db.replace_one(
                {"Guild": ctx.guild.id, "User": ctx.author.id}, 
                {"Guild": ctx.guild.id, "User": ctx.author.id, "Money": 0, "CoinName": 通貨名}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title="通貨を作成しました。", description=f"名前: {通貨名}", color=discord.Color.green()))

    @money_make.command(name="work", description="働いて、サーバー内通貨を取得します。")
    @commands.cooldown(2, 20, type=commands.BucketType.user)
    async def money_work(self, ctx: commands.Context):
        await ctx.defer()

        current_time = time.time()
        last_message_time = cooldown_work_time.get(ctx.author.id, 0)
        if current_time - last_message_time < 1800:
            return await ctx.reply("今はまだ稼げません。\nしばらく待ってください。")
        cooldown_work_time[ctx.author.id] = current_time
        
        db = self.bot.async_db["Main"].ServerMoney
        wm = random.randint(700, 1100)
        try:
            profile = await db.find_one({
                "Guild": ctx.guild.id, "User": ctx.author.id
            }, {
                "_id": False  # 内部IDを取得しないように
            })
            if profile is None:
                tname = await db.find_one({
                    "Guild": ctx.guild.id
                })
                if tname is None:
                    return await ctx.reply(embed=discord.Embed(title=f"このサーバーの通貨はありません。", color=discord.Color.red()))
                await db.replace_one(
                    {"Guild": ctx.guild.id, "User": ctx.author.id}, 
                    {"Guild": ctx.guild.id, "User": ctx.author.id, "Money": wm, "CoinName": tname["CoinName"]}, 
                    upsert=True
                )
                return await ctx.reply(embed=discord.Embed(title="お金を稼ぎました。", description=f"稼いだ額: {wm}{tname["CoinName"]}\n現在何{tname["CoinName"]}か: {wm}", color=discord.Color.green()))
            else:
                await db.replace_one(
                    {"Guild": ctx.guild.id, "User": ctx.author.id}, 
                    {"Guild": ctx.guild.id, "User": ctx.author.id, "Money": wm + profile.get("Money", 0), "CoinName": profile["CoinName"]}, 
                    upsert=True
                )
                return await ctx.reply(embed=discord.Embed(title="お金を稼ぎました。", description=f"稼いだ額: {wm}{profile["CoinName"]}\n現在何{profile["CoinName"]}か: {wm + profile.get("Money", 0)}{profile["CoinName"]}", color=discord.Color.green()))
        except Exception as e:
            return await ctx.reply(embed=discord.Embed(title=f"このサーバーの通貨はありません。", description=f"{e}", color=discord.Color.red()))

    @money_make.command(name="money", description="お金を見ます。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def money_money(self, ctx: commands.Context):
        await ctx.defer()
        db = self.bot.async_db["Main"].ServerMoney
        try:
            money = await db.find_one({
                "Guild": ctx.guild.id, "User": ctx.author.id
            }, {
                "_id": False  # 内部IDを取得しないように
            })
            if money is None:
                return await ctx.reply(embed=discord.Embed(title=f"あなたはお金を持っていません。", color=discord.Color.red()))
            await ctx.reply(embed=discord.Embed(title="現在のお金", description=f"{money["Money"]}{money["CoinName"]}", color=discord.Color.green()))
        except:
            return await ctx.reply(embed=discord.Embed(title=f"このサーバーの通貨はありません。", color=discord.Color.red()))
        
    @money_make.command(name="coin", description="お金の名前を見ます。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def money_coin(self, ctx: commands.Context):
        await ctx.defer()
        db = self.bot.async_db["Main"].ServerMoney
        try:
            money = await db.find_one({
                "Guild": ctx.guild.id,
            }, {
                "_id": False  # 内部IDを取得しないように
            })
            await ctx.reply(embed=discord.Embed(title="お金の名前", description=f"{money["CoinName"]}", color=discord.Color.green()))
        except:
            return await ctx.reply(embed=discord.Embed(title=f"このサーバーの通貨はありません。", color=discord.Color.red()))

    @money_make.command(name="convert", description="unbelievaboatにお金を変換します。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def money_convert(self, ctx: commands.Context, お金: int):
        await ctx.defer()
        db = self.bot.async_db["Main"].ServerMoney
        try:
            money = await db.find_one({
                "Guild": ctx.guild.id, "User": ctx.author.id
            }, {
                "_id": False
            })
            if money is None:
                return await ctx.reply(embed=discord.Embed(title=f"あなたはお金を持っていません。", color=discord.Color.red()))
            if money["Money"] < お金:
                return await ctx.reply(embed=discord.Embed(title=f"お金が足りません。", color=discord.Color.red()))
            client = Client(self.mt)
            try:
                guild = await client.get_guild(ctx.guild.id)
                user = await guild.get_user_balance(ctx.author.id)
                await user.set(bank=お金 + user.bank)
            except:
                return await ctx.reply(embed=discord.Embed(title="まずこれを認証してください。", description="https://unbelievaboat.com/applications/authorize?app_id=1326818885663592015", color=discord.Color.red()))
            await db.replace_one(
                {"Guild": ctx.guild.id, "User": ctx.author.id}, 
                {"Guild": ctx.guild.id, "User": ctx.author.id, "Money": money["Money"] - お金, "CoinName": money["CoinName"]}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title="お金を変換しました。", description=f"{お金}{money["CoinName"]}\n-> {お金}コイン", color=discord.Color.green()))
        except:
            return await ctx.reply(embed=discord.Embed(title=f"このサーバーの通貨はありません。", color=discord.Color.red()))

    @money_make.command(name="item", description="購入したアイテムを表示します。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def money_shop_item(self, ctx: commands.Context, ユーザー: discord.User):
        await ctx.defer()
        try:
            mdb = self.bot.async_db["Main"].ServerMoneyItems
            money = await mdb.find_one({
                "User": ユーザー.id
            }, {
                "_id": False  # 内部IDを取得しないように
            })
            if money is None:
                return await ctx.reply(embed=discord.Embed(title=f"あなたはアイテムを持っていません。", color=discord.Color.red()))
            txt = ""
            async for s in mdb.find(filter={'User': ユーザー.id}):
                txt += f"{s["ItemName"]}\n"
            ls = compress_list(txt.split("\n"))
            chunks = chunk_list_iter(ls, 10)
            embeds = []
            for i, chunk in enumerate(chunks, 1):
                embeds.append(discord.Embed(title=f"ページ{i}", description=f"\n".join(chunk), color=discord.Color.blue()))
        except:
            return
        view = Paginator(embeds)
        await ctx.reply(embed=embeds[0], view=view)

    async def add_item(self, ctx: commands.Context, アイテム名: str, 値段: int):
        idb = self.bot.async_db["Main"].ServerMoneyItems
        await idb.replace_one(
            {"User": ctx.author.id, "ItemName": アイテム名, "ID": randomname(5)}, 
            {"User": ctx.author.id, "Money": 値段, "ItemName": アイテム名, "ID": randomname(5)}, 
            upsert=True
        )

    @money_make.command(name="buy", description="ショップからかいます。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def money_shop_buy(self, ctx: commands.Context, アイテム名: str):
        await ctx.defer()
        db = self.bot.async_db["Main"].ServerMoneyShop
        try:
            mdb = self.bot.async_db["Main"].ServerMoney
            money = await mdb.find_one({
                "Guild": ctx.guild.id
            }, {
                "_id": False  # 内部IDを取得しないように
            })
            if money is None:
                return await ctx.reply(embed=discord.Embed(title=f"このサーバーにショップはありません。", color=discord.Color.red()))
            usermoney = await mdb.find_one({
                "Guild": ctx.guild.id, "User": ctx.author.id
            }, {
                "_id": False  # 内部IDを取得しないように
            })
            if usermoney is None:
                return await ctx.reply(embed=discord.Embed(title=f"あなたはお金がありません。", color=discord.Color.red()))
            tname = await db.find_one({
                "Guild": ctx.guild.id, "Name": アイテム名
            })
            if tname is None:
                return await ctx.reply(embed=discord.Embed(title=f"このにショップにそのアイテムがありません。", color=discord.Color.red()))
            if usermoney.get("Money", 0) > tname["Coin"]:
                await mdb.replace_one(
                    {"Guild": ctx.guild.id, "User": ctx.author.id}, 
                    {"Guild": ctx.guild.id, "User": ctx.author.id, "Money": usermoney["Money"] - tname["Coin"], "CoinName": usermoney["CoinName"]}, 
                    upsert=True
                )
                idb = self.bot.async_db["Main"].ServerMoneyItems
                await idb.replace_one(
                    {"User": ctx.author.id, "ItemName": tname["Name"], "ID": randomname(5)}, 
                    {"User": ctx.author.id, "Money": tname["Coin"], "ItemName": tname["Name"], "ID": randomname(5)}, 
                    upsert=True
                )
                shopdb = self.bot.async_db["Main"].ServerMoneyShop
                await shopdb.delete_one(
                    {"Guild": ctx.guild.id, "Name": アイテム名}
                )
                await ctx.reply(embed=discord.Embed(title=f"{tname["Name"]}を購入しました。", description=f"アイテム名: {tname["Name"]}", color=discord.Color.green()))
            else:
                await ctx.reply(embed=discord.Embed(title=f"お金がありません。", color=discord.Color.red()))
        except:
            return await ctx.reply(embed=discord.Embed(title=f"このサーバーにショップがないか、\nそのアイテムがありません。", description=f"{sys.exc_info()}", color=discord.Color.red()))

    @money_make.command(name="shop", description="ショップを見ます。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def money_shop(self, ctx: commands.Context):
        await ctx.defer()
        db = self.bot.async_db["Main"].ServerMoneyShop
        try:
            mdb = self.bot.async_db["Main"].ServerMoney
            money = await mdb.find_one({
                "Guild": ctx.guild.id
            }, {
                "_id": False  # 内部IDを取得しないように
            })
            if money is None:
                return await ctx.reply(embed=discord.Embed(title=f"このサーバーにショップはありません。", color=discord.Color.red()))
            txt = ""
            async for s in db.find(filter={'Guild': ctx.guild.id}):
                txt += f"{s["Name"]} - {s["Coin"]}{money["CoinName"]}\n"
            await ctx.reply(embed=discord.Embed(title=f"{ctx.guild.name}のショップ", description=txt, color=discord.Color.green()))
        except:
            return await ctx.reply(embed=discord.Embed(title=f"このサーバーにショップはありません。", color=discord.Color.red()))
        
    @money_make.command(name="shop_add", description="ショップに追加します。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True)
    async def money_shop_add(self, ctx: commands.Context, アイテムの名前: str, 値段: int):
        await ctx.defer()
        db = self.bot.async_db["Main"].ServerMoneyShop
        try:
            await db.replace_one(
                {"Guild": ctx.guild.id, "Name": アイテムの名前}, 
                {"Guild": ctx.guild.id, "Name": アイテムの名前, "Coin": 値段}, 
                upsert=True
            )
            await ctx.reply(embed=discord.Embed(title=f"{ctx.guild.name}のショップに\nアイテムを追加しました。", description=f"アイテム名: {アイテムの名前}\n値段: {値段}", color=discord.Color.green()))
        except:
            return await ctx.reply(embed=discord.Embed(title=f"このサーバーにショップはありません。", color=discord.Color.red()))

    @money_make.command(name="shop_remove", description="ショップから削除します。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True)
    async def money_shop_remove(self, ctx: commands.Context, アイテムの名前: str):
        await ctx.defer()
        db = self.bot.async_db["Main"].ServerMoneyShop
        try:
            mdb = self.bot.async_db["Main"].ServerMoney
            money = await mdb.find_one({
                "Guild": ctx.guild.id
            }, {
                "_id": False  # 内部IDを取得しないように
            })
            if money is None:
                return await ctx.reply(embed=discord.Embed(title=f"このサーバーにショップはありません。", color=discord.Color.red()))
            await db.delete_one(
                {"Guild": ctx.guild.id, "Name": アイテムの名前}
            )
            await ctx.reply(embed=discord.Embed(title=f"{ctx.guild.name}のショップから\nアイテムを削除しました。", description=f"アイテム名: {アイテムの名前}", color=discord.Color.green()))
        except:
            return await ctx.reply(embed=discord.Embed(title=f"このサーバーにショップはありません。", color=discord.Color.red()))

    @money_make.command(name="netshop", description="ブラウザ上でアイテムを購入します。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def money_netshop(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].ServerMoney
        try:
            tname = await db.find_one({
                "Guild": ctx.guild.id
            })
            if tname is None:
                return await ctx.reply(embed=discord.Embed(title=f"このサーバーの通貨はありません。", color=discord.Color.red()))
        except:
            return await ctx.reply(embed=discord.Embed(title=f"このサーバーの通貨はありません。", color=discord.Color.red()))
        await ctx.reply(f"以下のページをご覧ください。\nhttps://www.sharkbot.xyz/shop?id={ctx.guild.id}")

    @money_make.command(name="gift", description="アイテムをプレゼントします。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def money_gift(self, ctx: commands.Context, ユーザー: discord.User, アイテム名: str):
        db = self.bot.async_db["Main"].ServerMoney
        idb = self.bot.async_db["Main"].ServerMoneyItems
        profile = await idb.find_one({"User": ctx.author.id, "ItemName": アイテム名}, {
            "_id": False  # 内部IDを取得しないように
        })
        if profile is None:
            return await ctx.reply(f"そのアイテムはありません。")
        await idb.replace_one(
            {"User": ユーザー.id, "ItemName": アイテム名, "ID": randomname(5)}, 
            {"User": ユーザー.id, "Money": profile["Money"], "ItemName": アイテム名, "ID": randomname(5)}, 
            upsert=True
        )
        await idb.delete_one(
            {"User": ctx.author.id, "ItemName": アイテム名}
        )
        await ctx.reply(embed=discord.Embed(title="アイテムをプレゼントしました。", description=f"{アイテム名}", color=discord.Color.green()))

    async def remove_money_fund(self, ctx: commands.Context, お金: int):
        mdb = self.bot.async_db["Main"].ServerMoney
        usermoney = await mdb.find_one({
            "Guild": ctx.guild.id, "User": ctx.author.id
        }, {
            "_id": False  # 内部IDを取得しないように
        })
        if usermoney is None:
            return False
        if usermoney.get("Money", 0) > お金:
            await mdb.replace_one(
                {"Guild": ctx.guild.id, "User": ctx.author.id}, 
                {"Guild": ctx.guild.id, "User": ctx.author.id, "Money": usermoney["Money"] - お金, "CoinName": usermoney["CoinName"]}, 
                upsert=True
            )
            return True
        else:
            return False

    async def add_money_fund(self, ctx: commands.Context, お金: int):
        mdb = self.bot.async_db["Main"].ServerMoney
        usermoney = await mdb.find_one({
            "Guild": ctx.guild.id, "User": ctx.author.id
        }, {
            "_id": False  # 内部IDを取得しないように
        })
        if usermoney is None:
            tname = await mdb.find_one({
                "Guild": ctx.guild.id
            })
            if tname is None:
                await mdb.replace_one(
                    {"Guild": ctx.guild.id, "User": ctx.author.id}, 
                    {"Guild": ctx.guild.id, "User": ctx.author.id, "Money": お金, "CoinName": tname["CoinName"]}, 
                    upsert=True
                )
                return True
            else:
                return False
        await mdb.replace_one(
            {"Guild": ctx.guild.id, "User": ctx.author.id}, 
            {"Guild": ctx.guild.id, "User": ctx.author.id, "Money": usermoney["Money"] + お金, "CoinName": usermoney["CoinName"]}, 
            upsert=True
        )
        return True
    
    async def add_money_func_pay(self, ctx: commands.Context, user: discord.User, お金: int):
        mdb = self.bot.async_db["Main"].ServerMoney
        usermoney = await mdb.find_one({
            "Guild": ctx.guild.id, "User": user.id
        }, {
            "_id": False  # 内部IDを取得しないように
        })
        if usermoney is None:
            tname = await mdb.find_one({
                "Guild": ctx.guild.id
            })
            if tname is None:
                await mdb.replace_one(
                    {"Guild": ctx.guild.id, "User": user.id}, 
                    {"Guild": ctx.guild.id, "User": user.id, "Money": お金, "CoinName": tname["CoinName"]}, 
                    upsert=True
                )
                return True
            else:
                return False
        await mdb.replace_one(
            {"Guild": ctx.guild.id, "User": user.id}, 
            {"Guild": ctx.guild.id, "User": user.id, "Money": usermoney["Money"] + お金, "CoinName": usermoney["CoinName"]}, 
            upsert=True
        )
        return True

    @money_make.command(name="pay", description="お金を送信します。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def money_pay(self, ctx: commands.Context, ユーザー: discord.User, お金: int):
        await ctx.defer(ephemeral=True)
        await self.remove_money_fund(ctx, お金)
        await self.add_money_func_pay(ctx, ユーザー, お金)
        await ctx.reply(f"{ユーザー.display_name}さんへ送金しました。", ephemeral=True)

    @money_make.command(name="use", description="アイテムを使います。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def money_use(self, ctx: commands.Context, アイテム名: str):
        idb = self.bot.async_db["Main"].ServerMoneyItems
        profile = await idb.find_one({"User": ctx.author.id, "ItemName": アイテム名}, {
            "_id": False  # 内部IDを取得しないように
        })
        if profile is None:
            return await ctx.reply(f"そのアイテムはありません。")
        await idb.delete_one(
            {"User": ctx.author.id, "ItemName": アイテム名}
        )
        msg = random.choice(["とけた！", "おいしかった！", "捨てた！", "吐いた！", "転売した！", "飲み込んだ！", "飲んだ！"])
        await ctx.reply(embed=discord.Embed(title=f"{アイテム名}を使用しました。", description=f"{msg}", color=discord.Color.green()))

    @money_make.command(name="fish", description="魚を釣ります。")
    @commands.cooldown(1, 60, type=commands.BucketType.user)
    async def money_fish(self, ctx: commands.Context):
        fishname = random.choice(["サメ", "Mee6", "ビン", "カン", "サケ", "マグロ", "死骸"])
        値段 = random.randint(100, 2000)
        await self.add_item(ctx, fishname, 値段)
        await ctx.reply(embed=discord.Embed(title=f"魚を釣りました。", description=f"{fishname}が釣れた！\n値段: {値段}コイン", color=discord.Color.green()))

    @money_make.command(name="sell", description="アイテムを売ります。")
    @commands.cooldown(2, 20, type=commands.BucketType.guild)
    async def money_sell(self, ctx: commands.Context, アイテム名: str):
        idb = self.bot.async_db["Main"].ServerMoneyItems
        profile = await idb.find_one({"User": ctx.author.id, "ItemName": アイテム名}, {
            "_id": False  # 内部IDを取得しないように
        })
        if profile is None:
            return await ctx.reply(f"そのアイテムはありません。")
        db = self.bot.async_db["Main"].ServerMoney
        moneyadd = await db.find_one({
            "Guild": ctx.guild.id, "User": ctx.author.id
        }, {
            "_id": False  # 内部IDを取得しないように
        })
        if moneyadd is None:
            tname = await db.find_one({
                "Guild": ctx.guild.id
            })
            if tname is None:
                return await ctx.reply(embed=discord.Embed(title=f"このサーバーの通貨はありません。", color=discord.Color.red()))
            await db.replace_one(
                {"Guild": ctx.guild.id, "User": ctx.author.id}, 
                {"Guild": ctx.guild.id, "User": ctx.author.id, "Money": profile["Money"], "CoinName": tname["CoinName"]}, 
                upsert=True
            )
        else:
            await db.replace_one(
                {"Guild": ctx.guild.id, "User": ctx.author.id}, 
                {"Guild": ctx.guild.id, "User": ctx.author.id, "Money": profile["Money"] + moneyadd.get("Money", 0), "CoinName": moneyadd["CoinName"]}, 
                upsert=True
            )
        await idb.delete_one(
            {"User": ctx.author.id, "ItemName": アイテム名}
        )
        shopdb = self.bot.async_db["Main"].ServerMoneyShop
        await shopdb.replace_one(
            {"Guild": ctx.guild.id, "Name": アイテム名}, 
            {"Guild": ctx.guild.id, "Name": アイテム名, "Coin": profile["Money"]}, 
            upsert=True
        )
        tname = await db.find_one({
            "Guild": ctx.guild.id
        })
        await ctx.reply(embed=discord.Embed(title=f"アイテムを売りました。", description=f"{アイテム名}\n{profile["Money"]}{tname["CoinName"]}", color=discord.Color.green()))

    @commands.hybrid_group(name="money-game", description="料理をします。", fallback="cooking")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def money_cooking(self, ctx: commands.Context, 材料: str, 材料2: str):
        idb = self.bot.async_db["Main"].ServerMoneyItems
        profile = await idb.find_one({"User": ctx.author.id, "ItemName": 材料}, {
            "_id": False  # 内部IDを取得しないように
        })
        if profile is None:
            return await ctx.reply(f"そのアイテムはありません。")
        profile = await idb.find_one({"User": ctx.author.id, "ItemName": 材料2}, {
            "_id": False  # 内部IDを取得しないように
        })
        if profile is None:
            return await ctx.reply(f"そのアイテムはありません。")
        await idb.delete_one(
            {"User": ctx.author.id, "ItemName": 材料}
        )
        await idb.delete_one(
            {"User": ctx.author.id, "ItemName": 材料2}
        )
        itemname = random.choice(["パンケーキ", "クッキー", "餅", "チョコレート", "マシュマロ", "失敗作", "不思議な料理", "パン", "食パン", "タコス🌮", "コインチョコ", "日本陸軍", "日本海軍", "馬刺し", "チョコクッキー", "おにぎり", "ハンバーグ", "ハンバーガー", "溶岩ステーキ"])
        値段 = random.randint(100, 3000)
        await self.add_item(ctx, itemname, 値段)
        await ctx.reply(embed=discord.Embed(title="料理をしました。", description=f"料理名: {itemname}\n値段: {値段}コイン\n材料: {材料} と {材料2}", color=discord.Color.green()))
    
    async def get_coinname_fund(self, ctx: commands.Context):
        mdb = self.bot.async_db["Main"].ServerMoney
        tname = await mdb.find_one({
            "Guild": ctx.guild.id
        })
        if tname is None:
            return None
        return tname["CoinName"]

    @money_cooking.command(name="guess", description="0~5の間で、数字あてゲームをします。")
    @commands.cooldown(2, 20, type=commands.BucketType.user)
    async def money_guess(self, ctx: commands.Context, お金: int, 数字: int):
        await ctx.defer()
        mdb = self.bot.async_db["Main"].ServerMoney
        usermoney = await mdb.find_one({
            "Guild": ctx.guild.id, "User": ctx.author.id
        }, {
            "_id": False  # 内部IDを取得しないように
        })
        if usermoney is None:
            return await ctx.reply(embed=discord.Embed(title=f"あなたはお金がありません。", color=discord.Color.red()))
        if usermoney.get("Money", 0) > お金:
            数字s = random.randint(0, 5)
            await mdb.replace_one(
                {"Guild": ctx.guild.id, "User": ctx.author.id}, 
                {"Guild": ctx.guild.id, "User": ctx.author.id, "Money": usermoney["Money"] - お金, "CoinName": usermoney["CoinName"]}, 
                upsert=True
            )
            if 数字s == 数字:
                await mdb.replace_one(
                    {"Guild": ctx.guild.id, "User": ctx.author.id}, 
                    {"Guild": ctx.guild.id, "User": ctx.author.id, "Money": usermoney["Money"] + お金 * 3 , "CoinName": usermoney["CoinName"]}, 
                    upsert=True
                )
                await ctx.reply(embed=discord.Embed(title="正解しました。", description=f"{お金}{usermoney["CoinName"]}使用しました。\n{お金*3}{usermoney["CoinName"]}返ってきました。", color=discord.Color.green()))
            else:
                await ctx.reply(embed=discord.Embed(title="不正解です。", description=f"{お金}{usermoney["CoinName"]}使用しました。", color=discord.Color.red()))
        else:
            await ctx.reply(embed=discord.Embed(title=f"お金がありません。", color=discord.Color.red()))

    @money_cooking.command(name="roulette", description="ルーレットで遊びます。")
    @commands.cooldown(2, 20, type=commands.BucketType.user)
    @discord.app_commands.choices(
        赤か黒=[
            discord.app_commands.Choice(name="赤", value="red"),
            discord.app_commands.Choice(name="黒", value="black"),
        ]
    )
    async def money_roulette(self, ctx: commands.Context, お金: int, 赤か黒: discord.app_commands.Choice[str]):
        m = await self.remove_money_fund(ctx, お金)
        cn = await self.get_coinname_fund(ctx)
        rb = random.choice(["r", "b"])
        if m:
            if 赤か黒.name == "赤":
                if rb == "r":
                    await self.add_money_fund(ctx, お金*3)
                    await ctx.reply(embed=discord.Embed(title="当たりました。", color=discord.Color.green(), description=f"{お金}{cn}を使用して、\n{お金*3}{cn}が返ってきました。"))
                else:
                    return await ctx.reply(embed=discord.Embed(title="外れました。", color=discord.Color.red(), description=f"{お金}{cn}を使用しました。"))
            else:
                if rb == "b":
                    await self.add_money_fund(ctx, お金*3)
                    await ctx.reply(embed=discord.Embed(title="当たりました。", color=discord.Color.green(), description=f"{お金}{cn}を使用して、\n{お金*3}{cn}が返ってきました。"))
                    return
                else:
                    return await ctx.reply(embed=discord.Embed(title="外れました。", color=discord.Color.red(), description=f"{お金}{cn}を使用しました。"))
        else:
            return await ctx.reply(embed=discord.Embed(title=f"お金がありません。", color=discord.Color.red()))

    @money_cooking.command(name="amazon", description="ほかの鯖から10倍の価格で取り寄せます")
    @commands.cooldown(1, 60, type=commands.BucketType.user)
    async def money_amazon(self, ctx: commands.Context, アイテム名: str):
        await ctx.defer()
        db = self.bot.async_db["Main"].ServerMoneyShop
        try:
            mdb = self.bot.async_db["Main"].ServerMoney
            money = await mdb.find_one({
                "Guild": ctx.guild.id
            }, {
                "_id": False  # 内部IDを取得しないように
            })
            if money is None:
                return await ctx.reply(embed=discord.Embed(title=f"このサーバーにショップはありません。", color=discord.Color.red()))
            usermoney = await mdb.find_one({
                "Guild": ctx.guild.id, "User": ctx.author.id
            }, {
                "_id": False  # 内部IDを取得しないように
            })
            if usermoney is None:
                return await ctx.reply(embed=discord.Embed(title=f"あなたはお金がありません。", color=discord.Color.red()))
            tname = await db.find_one({
                "Name": アイテム名
            })
            if tname is None:
                return await ctx.reply(embed=discord.Embed(title=f"どこのショップにもそのアイテムがありません。", color=discord.Color.red()))
            if usermoney.get("Money", 0) > tname["Coin"] * 10:
                await mdb.replace_one(
                    {"Guild": ctx.guild.id, "User": ctx.author.id}, 
                    {"Guild": ctx.guild.id, "User": ctx.author.id, "Money": usermoney["Money"] - tname["Coin"] * 10, "CoinName": usermoney["CoinName"]}, 
                    upsert=True
                )
                await self.add_item(ctx, アイテム名, tname["Coin"] * 10)
                await ctx.reply(embed=discord.Embed(title=f"{tname["Name"]}を購入しました。", description=f"アイテム名: {tname["Name"]}", color=discord.Color.green()))
            else:
                await ctx.reply(embed=discord.Embed(title=f"お金がありません。", description=f"{tname["Coin"] * 10}{usermoney["CoinName"]}かかります。", color=discord.Color.red()))
        except:
            return await ctx.reply(embed=discord.Embed(title=f"このサーバーにショップがないか、\nそのアイテムがありません。", description=f"{sys.exc_info()}", color=discord.Color.red()))

    async def vending_make_(self, ctx: commands.Context, 自販機名: str, 自販機説明: str):
        db = self.bot.async_db["Main"].ServerMoneyVending
        await db.replace_one(
            {"Guild": ctx.guild.id, "Name": 自販機名}, 
            {"Guild": ctx.guild.id, "Name": 自販機名, "Desc": 自販機説明}, 
           upsert=True
        )
        return
    
    async def vending_make_role(self, ctx: commands.Context, 自販機名: str, 自販機説明: str):
        db = self.bot.async_db["Main"].ServerMoneyVendingRole
        await db.replace_one(
            {"Guild": ctx.guild.id, "Name": 自販機名}, 
            {"Guild": ctx.guild.id, "Name": 自販機名, "Desc": 自販機説明}, 
           upsert=True
        )
        return
    
    async def vending_add_(self, ctx: commands.Context, 自販機名: str, アイテム名: str, 値段: int):
        db = self.bot.async_db["Main"].ServerMoneyVendingItem
        await db.replace_one(
            {"Guild": ctx.guild.id, "Name": 自販機名, "ItemName": アイテム名}, 
            {"Guild": ctx.guild.id, "Name": 自販機名, "ItemName": アイテム名, "Money": 値段}, 
           upsert=True
        )
        return
    
    async def vending_get_(self, ctx: commands.Context, コイン名: str, 自販機名: str):
        db = self.bot.async_db["Main"].ServerMoneyVending
        dt = await db.find_one({
            "Guild": ctx.guild.id, "Name": 自販機名
        }, {
            "_id": False  # 内部IDを取得しないように
        })
        if dt is None:
            return None
        db2 = self.bot.async_db["Main"].ServerMoneyVendingItem
        async with db2.find(filter={"Guild": ctx.guild.id, "Name": 自販機名}) as cursor:
            servers = await cursor.to_list(length=None)
            embed = discord.Embed(title=dt["Name"], description=dt["Desc"], color=discord.Color.blue())
            for s in servers:
                embed.add_field(name=s["ItemName"], value=f"{s["Money"]}{コイン名}", inline=False)
            return embed
        
    async def vending_get_item(self, ints: discord.Integration, 自販機名: str, アイテム名: str):
        try:
            db2 = self.bot.async_db["Main"].ServerMoneyVendingItem
            profile = await db2.find_one({
                "Guild": ints.guild.id, "Name": 自販機名, "ItemName": アイテム名
            }, {
                "_id": False  # 内部IDを取得しないように
            })
            return profile["Money"]
        except:
            return None
        
    async def vending_get_view(self, ctx: commands.Context, 自販機名: str):
        db = self.bot.async_db["Main"].ServerMoneyVending
        dt = await db.find_one({
            "Guild": ctx.guild.id, "Name": 自販機名
        }, {
            "_id": False  # 内部IDを取得しないように
        })
        if dt is None:
            return None
        db2 = self.bot.async_db["Main"].ServerMoneyVendingItem
        async with db2.find(filter={"Guild": ctx.guild.id, "Name": 自販機名}) as cursor:
            servers = await cursor.to_list(length=None)
            view = discord.ui.View()
            for s in servers:
                view.add_item(discord.ui.Button(label=f"{s["ItemName"]}", custom_id=f"vending_buy_v2+{s["Name"]}+{s["ItemName"]}"))
            return view
        
    async def vending_get_all(self, ctx: commands.Context):
        db2 = self.bot.async_db["Main"].ServerMoneyVending
        async with db2.find(filter={"Guild": ctx.guild.id}) as cursor:
            servers = await cursor.to_list(length=None)
            return [dt["Name"] for dt in servers]

    @commands.hybrid_group(name="vending", description="自販機を作ります。", fallback="make")
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(1, 300, type=commands.BucketType.guild)
    @discord.app_commands.choices(
        種類選択=[
            discord.app_commands.Choice(name="アイテム", value="item"),
            discord.app_commands.Choice(name="ロール", value="role"),
        ]
    )
    async def vending_make(self, ctx: commands.Context, 自販機名: str, 自販機説明: str, 種類選択: discord.app_commands.Choice[str], ロール: discord.Role = None, 値段: int = None):
        await ctx.defer(ephemeral=True)
        if 種類選択.name == "アイテム":
            db = self.bot.async_db["Main"].ServerMoney
            try:
                tname = await db.find_one({
                    "Guild": ctx.guild.id
                })
                if tname is None:
                    return await ctx.reply(embed=discord.Embed(title=f"このサーバーの通貨はありません。", color=discord.Color.red()), ephemeral=True)
            except:
                return await ctx.reply(embed=discord.Embed(title=f"このサーバーの通貨はありません。", color=discord.Color.red()), ephemeral=True)
            await self.vending_make_(ctx, 自販機名, 自販機説明)
            await ctx.reply(embed=discord.Embed(title="自販機を作成しました。", color=discord.Color.green()), ephemeral=True)
        else:
            db = self.bot.async_db["Main"].ServerMoney
            try:
                tname = await db.find_one({
                    "Guild": ctx.guild.id
                })
                if tname is None:
                    return await ctx.reply(embed=discord.Embed(title=f"このサーバーの通貨はありません。", color=discord.Color.red()), ephemeral=True)
            except:
                return await ctx.reply(embed=discord.Embed(title=f"このサーバーの通貨はありません。", color=discord.Color.red()), ephemeral=True)
            if not ロール:
                return await ctx.reply(embed=discord.Embed(title="ロールがありません。\nロールを選択してください。", color=discord.Color.red()), ephemeral=True)
            if not 値段:
                return await ctx.reply(embed=discord.Embed(title="値段がありません。\n値段を選択してください。", color=discord.Color.red()), ephemeral=True)
            await ctx.channel.send(embed=discord.Embed(title=f"{自販機名}", description=f"{自販機説明}\n\n{値段}{tname["CoinName"]}", color=discord.Color.blue()), view=discord.ui.View().add_item(discord.ui.Button(label=f"{ロール.name}", custom_id=f"vending_role_buy_v2+{ロール.id}+{値段}")))
            await ctx.reply(embed=discord.Embed(title="自販機を送信しました。", color=discord.Color.green()), ephemeral=True)

    @vending_make.command(name="add", description="自販機にアイテムを追加します。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def vending_add(self, ctx: commands.Context, 自販機名: str, アイテム名: str, 値段: int):
        await ctx.defer(ephemeral=True)
        db = self.bot.async_db["Main"].ServerMoney
        try:
            tname = await db.find_one({
                "Guild": ctx.guild.id
            })
            if tname is None:
                return await ctx.reply(embed=discord.Embed(title=f"このサーバーの通貨はありません。", color=discord.Color.red()), ephemeral=True)
        except:
            return await ctx.reply(embed=discord.Embed(title=f"このサーバーの通貨はありません。", color=discord.Color.red()), ephemeral=True)
        await self.vending_add_(ctx, 自販機名, アイテム名, 値段)
        await ctx.reply(embed=discord.Embed(title="自販機にアイテムを追加しました。", color=discord.Color.green()), ephemeral=True)

    @vending_make.command(name="send", description="自販機を送信します。")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def vending_send(self, ctx: commands.Context, 自販機名: str):
        db = self.bot.async_db["Main"].ServerMoney
        try:
            tname = await db.find_one({
                "Guild": ctx.guild.id
            })
            if tname is None:
                return await ctx.reply(embed=discord.Embed(title=f"このサーバーの通貨はありません。", color=discord.Color.red()), ephemeral=True)
        except:
            return await ctx.reply(embed=discord.Embed(title=f"このサーバーの通貨はありません。", color=discord.Color.red()), ephemeral=True)
        embed = await self.vending_get_(ctx, tname["CoinName"], 自販機名)
        view = await self.vending_get_view(ctx, 自販機名)
        if not embed:
            return await ctx.reply(embed=discord.Embed(title="自販機が見つかりません。", color=discord.Color.red()), ephemeral=True)
        await ctx.channel.send(embed=embed, view=view)
        await ctx.reply(embed=discord.Embed(title="自販機を送信しました。", color=discord.Color.green()), ephemeral=True)

    @vending_make.command(name="list", description="すべての自販機を")
    @commands.cooldown(2, 10, type=commands.BucketType.guild)
    async def vending_all(self, ctx: commands.Context):
        db = self.bot.async_db["Main"].ServerMoney
        try:
            tname = await db.find_one({
                "Guild": ctx.guild.id
            })
            if tname is None:
                return await ctx.reply(embed=discord.Embed(title=f"このサーバーの通貨はありません。", color=discord.Color.red()), ephemeral=True)
        except:
            return await ctx.reply(embed=discord.Embed(title=f"このサーバーの通貨はありません。", color=discord.Color.red()), ephemeral=True)
        vens = await self.vending_get_all(ctx)
        if not vens:
            return await ctx.reply(embed=discord.Embed(title="自販機がありません。", color=discord.Color.red()), ephemeral=True)
        await ctx.reply(embed=discord.Embed(title="自販機リスト", color=discord.Color.green(), description="\n".join(vens)), ephemeral=True)

    @commands.Cog.listener(name="on_interaction")
    async def on_interaction_vending(self, interaction: discord.Interaction):
        try:
            if interaction.data['component_type'] == 2:
                try:
                    custom_id = interaction.data["custom_id"]
                except:
                    return
                if "vending_buy_v2+" in custom_id:
                    await interaction.response.defer(ephemeral=True)
                    vendingname = custom_id.split("+")[1]
                    itemname = custom_id.split("+")[2]
                    db = self.bot.async_db["Main"].ServerMoney
                    money = await db.find_one({
                        "Guild": interaction.guild.id
                    }, {
                        "_id": False  # 内部IDを取得しないように
                    })
                    if money is None:
                        return await interaction.followup.send(embed=discord.Embed(title=f"このサーバーにショップはありません。", color=discord.Color.red()), ephemeral=True)
                    usermoney = await db.find_one({
                        "Guild": interaction.guild.id, "User": interaction.user.id
                    }, {
                        "_id": False  # 内部IDを取得しないように
                    })
                    if usermoney is None:
                        return await interaction.followup.send(embed=discord.Embed(title=f"あなたはお金がありません。", color=discord.Color.red()), ephemeral=True)
                    coin = await self.vending_get_item(interaction, vendingname, itemname)
                    if usermoney.get("Money", 0) > coin:
                        await db.replace_one(
                            {"Guild": interaction.guild.id, "User": interaction.user.id}, 
                            {"Guild": interaction.guild.id, "User": interaction.user.id, "Money": usermoney["Money"] - coin, "CoinName": usermoney["CoinName"]}, 
                            upsert=True
                        )
                        idb = self.bot.async_db["Main"].ServerMoneyItems
                        await idb.replace_one(
                            {"User": interaction.user.id, "ItemName": itemname, "ID": randomname(5)}, 
                            {"User": interaction.user.id, "Money": coin, "ItemName": itemname, "ID": randomname(5)}, 
                            upsert=True
                        )
                        return await interaction.followup.send(f"{itemname}を購入しました。", ephemeral=True)
                    else:
                        return await interaction.followup.send(f"お金がありません。", ephemeral=True)
                elif "vending_role_buy_v2+" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        roleid = int(custom_id.split("+")[1])
                        coincount = int(custom_id.split("+")[2])
                        db = self.bot.async_db["Main"].ServerMoney
                        money = await db.find_one({
                            "Guild": interaction.guild.id
                        }, {
                            "_id": False  # 内部IDを取得しないように
                        })
                        if money is None:
                            return await interaction.followup.send(embed=discord.Embed(title=f"このサーバーにショップはありません。", color=discord.Color.red()), ephemeral=True)
                        usermoney = await db.find_one({
                            "Guild": interaction.guild.id, "User": interaction.user.id
                        }, {
                            "_id": False  # 内部IDを取得しないように
                        })
                        if usermoney is None:
                            return await interaction.followup.send(embed=discord.Embed(title=f"あなたはお金がありません。", color=discord.Color.red()), ephemeral=True)
                        if usermoney.get("Money", 0) > coincount:
                            await db.replace_one(
                                {"Guild": interaction.guild.id, "User": interaction.user.id}, 
                                {"Guild": interaction.guild.id, "User": interaction.user.id, "Money": usermoney["Money"] - coincount, "CoinName": usermoney["CoinName"]}, 
                                upsert=True
                            )
                            await interaction.user.add_roles(interaction.guild.get_role(roleid))
                            return await interaction.followup.send(f"{interaction.guild.get_role(roleid).name}を購入しました。", ephemeral=True)
                        else:
                            return await interaction.followup.send(f"お金がありません。", ephemeral=True)
                    except:
                        return await interaction.followup.send(f"{sys.exc_info()}")
        except:
            return

async def setup(bot):
    await bot.add_cog(MoneyCog(bot))