from discord.ext import commands
import discord
import traceback
import re
import sys
import logging
import random
import asyncio
import datetime
import string

tku = []
freech = []

class AuthModal_keisan(discord.ui.Modal, title="認証をする"):
    def __init__(self, role: discord.Role):
        super().__init__()

        a = random.randint(1, 999)
        b = random.randint(1, 999)
        self.kekka = str(a + b)
        self.r = role

        self.name = discord.ui.TextInput(label=f"{a} + {b}は? 結果を数字だけで入力")
        self.add_item(self.name)
    async def on_submit(self, interaction: discord.Interaction) -> None:
        if self.kekka == self.name.value:
            await interaction.response.defer(ephemeral=True)
            try:
                await interaction.user.add_roles(self.r)
                await interaction.followup.send("認証に成功しました。", ephemeral=True)
            except:
                await interaction.followup.send("認証に失敗しました。", ephemeral=True)
        else:
            await interaction.response.send_message("認証に失敗しました。", ephemeral=True)

class AuthModal_kanji(discord.ui.Modal, title="認証をする (間違っていたらもう一度やり直してください。)"):
    def __init__(self, role: discord.Role):
        super().__init__()

        self.kj = random.choice(["漢字,かんじ", "狩猟民族,しゅりょうみんぞく"])
        self.r = role

        self.name = discord.ui.TextInput(label=f"{self.kj.split(',')[0]}の読みは？ひらがなで入力")
        self.add_item(self.name)
    async def on_submit(self, interaction: discord.Interaction) -> None:
        if self.kj.split(",")[1] == self.name.value:
            await interaction.response.defer(ephemeral=True)
            try:
                await interaction.user.add_roles(self.r)
                await interaction.followup.send("認証に成功しました。", ephemeral=True)
            except:
                await interaction.followup.send("認証に失敗しました。", ephemeral=True)
        else:
            await interaction.response.send_message("認証に失敗しました。", ephemeral=True)

class PlusAuthModal_keisan(discord.ui.Modal, title="認証をする"):
    def __init__(self, role: discord.Role, drole: discord.Role):
        super().__init__()

        a = random.randint(1, 999)
        b = random.randint(1, 999)
        self.kekka = str(a + b)
        self.r = role
        self.dr = drole

        self.name = discord.ui.TextInput(label=f"{a} + {b}は? 結果を数字だけで入力")
        self.add_item(self.name)
    async def on_submit(self, interaction: discord.Interaction) -> None:
        if self.kekka == self.name.value:
            await interaction.response.defer(ephemeral=True)
            try:
                await interaction.user.remove_roles(self.dr)
                await interaction.user.add_roles(self.r)
                await interaction.followup.send("認証に成功しました。", ephemeral=True)
            except:
                await interaction.followup.send("認証に失敗しました。", ephemeral=True)
        else:
            await interaction.response.send_message("認証に失敗しました。", ephemeral=True)

class PanelCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> PanelCog")

    @commands.hybrid_group(name="panel", description="ロールパネルを作ります。", fallback="role")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def role_panel(self, ctx: commands.Context, タイトル: str, 説明: str, メンションを表示するか: bool, ロール1: discord.Role, ロール2: discord.Role = None, ロール3: discord.Role = None, ロール4: discord.Role = None, ロール5: discord.Role = None, ロール6: discord.Role = None, ロール7: discord.Role = None, ロール8: discord.Role = None, ロール9: discord.Role = None, ロール10: discord.Role = None):
        view = discord.ui.View()
        ls = []
        view.add_item(discord.ui.Button(label=f"{ロール1.name}", custom_id=f"rolepanel_v1+{ロール1.id}"))
        ls.append(f"{ロール1.mention}")
        try:
            view.add_item(discord.ui.Button(label=f"{ロール2.name}", custom_id=f"rolepanel_v1+{ロール2.id}"))
            ls.append(f"{ロール2.mention}")
        except:
            pass
        try:
            view.add_item(discord.ui.Button(label=f"{ロール3.name}", custom_id=f"rolepanel_v1+{ロール3.id}"))
            ls.append(f"{ロール3.mention}")
        except:
            pass
        try:
            view.add_item(discord.ui.Button(label=f"{ロール4.name}", custom_id=f"rolepanel_v1+{ロール4.id}"))
            ls.append(f"{ロール4.mention}")
        except:
            pass
        try:
            view.add_item(discord.ui.Button(label=f"{ロール5.name}", custom_id=f"rolepanel_v1+{ロール5.id}"))
            ls.append(f"{ロール5.mention}")
        except:
            pass
        try:
            view.add_item(discord.ui.Button(label=f"{ロール6.name}", custom_id=f"rolepanel_v1+{ロール6.id}"))
            ls.append(f"{ロール6.mention}")
        except:
            pass
        try:
            view.add_item(discord.ui.Button(label=f"{ロール7.name}", custom_id=f"rolepanel_v1+{ロール7.id}"))
            ls.append(f"{ロール7.mention}")
        except:
            pass
        try:
            view.add_item(discord.ui.Button(label=f"{ロール8.name}", custom_id=f"rolepanel_v1+{ロール8.id}"))
            ls.append(f"{ロール8.mention}")
        except:
            pass
        try:
            view.add_item(discord.ui.Button(label=f"{ロール9.name}", custom_id=f"rolepanel_v1+{ロール9.id}"))
            ls.append(f"{ロール9.mention}")
        except:
            pass
        try:
            view.add_item(discord.ui.Button(label=f"{ロール10.name}", custom_id=f"rolepanel_v1+{ロール10.id}"))
            ls.append(f"{ロール10.mention}")
        except:
            pass
        embed = discord.Embed(title=f"{タイトル}", description=f"{説明}", color=discord.Color.green())
        if メンションを表示するか:
            embed.add_field(name="ロール一覧", value=f"\n".join(ls))
        await ctx.channel.send(embed=embed, view=view)
        await ctx.reply(embed=discord.Embed(title="作成しました。", color=discord.Color.green()), ephemeral=True)

    @role_panel.command(description="ロールパネルを編集します。", name="role-edit")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    @discord.app_commands.choices(
        削除か追加か=[
            discord.app_commands.Choice(name="追加", value="add"),
            discord.app_commands.Choice(name="削除", value="remove"),
        ]
    )
    async def panel_rolepanel_edit(self, ctx: commands.Context, ロールパネルのid: discord.Message, ロール: discord.Role, 削除か追加か: discord.app_commands.Choice[str]):
        await ctx.defer(ephemeral=True)
        view = discord.ui.View()
        for action_row in ロールパネルのid.components:
            for v in action_row.children:  # ActionRow の子要素（ボタン）
                if isinstance(v, discord.Button):
                    view.add_item(discord.ui.Button(label=v.label, custom_id=v.custom_id))

        if 削除か追加か.name == "追加":
            view.add_item(discord.ui.Button(label=ロール.name, custom_id=f"rolepanel_v1+{ロール.id}"))

        else:
            view = discord.ui.View()
            for action_row in ロールパネルのid.components:
                for v in action_row.children:  # ActionRow の子要素（ボタン）
                    if isinstance(v, discord.Button):
                        if not v.label == ロール.name:
                            view.add_item(discord.ui.Button(label=v.label, custom_id=v.custom_id))
        await ロールパネルのid.edit(view=view)
        await ctx.reply(embed=discord.Embed(title="編集しました。", color=discord.Color.green()), ephemeral=True)

    @role_panel.command(description="認証パネルを作ります。", name="auth")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def panel_authbutton(self, ctx, タイトル: str, 説明: str, ロール: discord.Role):
        await ctx.channel.send(embed=discord.Embed(title=f"{タイトル}", description=f"{説明}", color=discord.Color.green()), view=discord.ui.View().add_item(discord.ui.Button(label="認証", custom_id=f"authpanel_v1+{ロール.id}")))
        await ctx.reply(embed=discord.Embed(title="作成しました。", color=discord.Color.green()), ephemeral=True)

    @role_panel.command(description="認証したらロールが外れた後にロールが付くパネルを作ります。", name="auth-plus")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def panel_authbutton_plus(self, ctx, タイトル: str, 説明: str, ロール: discord.Role, 外すロール: discord.Role):
        await ctx.channel.send(embed=discord.Embed(title=f"{タイトル}", description=f"{説明}", color=discord.Color.green()), view=discord.ui.View().add_item(discord.ui.Button(label="認証", custom_id=f"authpanel_plus_v1+{ロール.id}+{外すロール.id}")))
        await ctx.reply(embed=discord.Embed(title="作成しました。", color=discord.Color.green()), ephemeral=True)

    @role_panel.command(description="Web認証パネルを作ります。", name="webauth")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def panel_authboost(self, ctx, タイトル: str, 説明: str, ロール: discord.Role):
        await ctx.channel.send(embed=discord.Embed(title=f"{タイトル}", description=f"{説明}", color=discord.Color.green()), view=discord.ui.View().add_item(discord.ui.Button(label="認証", custom_id=f"boostauth+{ロール.id}")))
        await ctx.reply(embed=discord.Embed(title="作成しました。", color=discord.Color.green()), ephemeral=True)

    @role_panel.command(description="投票パネルを作ります。", name="poll")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    async def panel_poll(self, ctx: commands.Context, タイトル: str, 選択肢1: str, 選択肢2: str = None, 選択肢3: str = None, 選択肢4: str = None, 選択肢5: str = None):
        text = ""
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label=f"{選択肢1}", custom_id=f"poll+{選択肢1}"))
        text += f"{選択肢1}: 0\n"
        try:
            if 選択肢2 != None:
                view.add_item(discord.ui.Button(label=f"{選択肢2}", custom_id=f"poll+{選択肢2}"))
                text += f"{選択肢2}: 0\n"
        except:
            pass
        try:
            if 選択肢3 != None:
                view.add_item(discord.ui.Button(label=f"{選択肢3}", custom_id=f"poll+{選択肢3}"))
                text += f"{選択肢3}: 0\n"
        except:
            pass
        try:
            if 選択肢4 != None:
                view.add_item(discord.ui.Button(label=f"{選択肢4}", custom_id=f"poll+{選択肢4}"))
                text += f"{選択肢4}: 0\n"
        except:
            pass
        try:
            if 選択肢5 != None:
                view.add_item(discord.ui.Button(label=f"{選択肢5}", custom_id=f"poll+{選択肢5}"))
                text += f"{選択肢5}: 0"
        except:
            pass
        view.add_item(discord.ui.Button(label=f"集計", custom_id=f"poll_done+{ctx.author.id}"))
        await ctx.channel.send(embed=discord.Embed(title=f"{タイトル}", description=f"{text}", color=discord.Color.green()), view=view)
        await ctx.reply(embed=discord.Embed(title="作成しました。", color=discord.Color.green()), ephemeral=True)


    def randstring(self, n):
        randlst = [random.choice(string.ascii_letters + string.digits) for i in range(n)]
        return ''.join(randlst)

    @role_panel.command(description="チケットパネルを作ります。", name="ticket")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def panel_ticket(self, ctx, タイトル: str, 説明: str):
        await ctx.channel.send(embed=discord.Embed(title=f"{タイトル}", description=f"{説明}", color=discord.Color.green()), view=discord.ui.View().add_item(discord.ui.Button(label="チケットを作成", custom_id=f"ticket_v1")))
        await ctx.reply(embed=discord.Embed(title="作成しました。", color=discord.Color.green()), ephemeral=True)

    @role_panel.command(description="一時テキストチャンネルパネルを作成します。", name="freechannel")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def panel_freechannel(self, ctx, タイトル: str, 説明: str):
        await ctx.channel.send(embed=discord.Embed(title=f"{タイトル}", description=f"{説明}", color=discord.Color.green()), view=discord.ui.View().add_item(discord.ui.Button(label="チャンネルを作成", custom_id=f"freech_v1")))
        await ctx.reply(embed=discord.Embed(title="作成しました。", color=discord.Color.green()), ephemeral=True)

    def extract_user_id(self,mention: str) -> int | None:
        match = re.match(r"<@&!?(\d+)>", mention)
        return int(match.group(1)) if match else None

    @role_panel.command(description="ほかのBotからコピーします。", name="copy")
    @commands.cooldown(2, 10, commands.BucketType.guild)
    @commands.has_permissions(manage_roles=True)
    async def panel_copy(self, ctx: commands.Context, パネル: discord.Message):
        await ctx.defer(ephemeral=True)
        if パネル.author.id == 1316023730484281394:
            if not パネル.embeds:
                return await ctx.reply(ephemeral=True, content="移行できないパネルです。")
            else:
                if パネル.embeds[0].fields[0].name == "利用可能なロール":
                    li = []
                    for p in パネル.embeds[0].fields[0].value.split("\n"):
                        li.append(self.extract_user_id(p))
                    view = discord.ui.View()
                    for l in li:
                        view.add_item(discord.ui.Button(label=f"{ctx.guild.get_role(l).name}", custom_id=f"rolepanel_v1+{l}"))
                    await ctx.channel.send(embed=discord.Embed(title=f"{パネル.embeds[0].title}", description=パネル.embeds[0].fields[0].value, color=discord.Color.blue()), view=view)
                    await ctx.reply(f"移行しました。")
                else:
                    await ctx.reply(ephemeral=True, content="移行に失敗しました。")
        else:
            await ctx.reply("パネルの移行に対応していません。", ephemeral=True)

    @commands.Cog.listener(name="on_interaction")
    async def on_interaction_panel(self, interaction: discord.Interaction):
        try:
            if interaction.data['component_type'] == 2:
                try:
                    custom_id = interaction.data["custom_id"]
                except:
                    return
                if "rolepanel_v1+" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        if not interaction.guild.get_role(int(custom_id.split("+")[1])) in interaction.user.roles:
                            await interaction.user.add_roles(interaction.guild.get_role(int(custom_id.split("+")[1])))
                            await interaction.followup.send("ロールを追加しました。", ephemeral=True)
                        else:
                            await interaction.user.remove_roles(interaction.guild.get_role(int(custom_id.split("+")[1])))
                            await interaction.followup.send("ロールを剥奪しました。", ephemeral=True)
                    except discord.Forbidden as f:
                        await interaction.followup.send("付与したいロールの位置がSharkBotのロールよりも\n上にあるため付与できませんでした。\nhttps://i.imgur.com/fGcWslT.gif", ephemeral=True)
                    except:
                        await interaction.followup.send("追加に失敗しました。", ephemeral=True)
                elif "authpanel_v1+" in custom_id:
                    try:
                        if interaction.guild.get_role(int(custom_id.split("+")[1])) in interaction.user.roles:
                            return await interaction.response.send_message("あなたはすでに認証しています。", ephemeral=True)
                        ch = random.choice(["k", "kanji"])
                        if ch == "k":
                            await interaction.response.send_modal(AuthModal_keisan(interaction.guild.get_role(int(custom_id.split("+")[1]))))
                        else:
                            await interaction.response.send_modal(AuthModal_kanji(interaction.guild.get_role(int(custom_id.split("+")[1]))))
                    except discord.Forbidden as f:
                        await interaction.response.send_message("付与したいロールの位置がSharkBotのロールよりも\n上にあるため付与できませんでした。\nhttps://i.imgur.com/fGcWslT.gif", ephemeral=True)
                    except:
                        await interaction.response.send_message("認証に失敗しました。", ephemeral=True)
                elif "authpanel_plus_v1+" in custom_id:
                    try:
                        if interaction.guild.get_role(int(custom_id.split("+")[1])) in interaction.user.roles:
                            return await interaction.response.send_message("あなたはすでに認証しています。", ephemeral=True)
                        await interaction.response.send_modal(PlusAuthModal_keisan(interaction.guild.get_role(int(custom_id.split("+")[1])), interaction.guild.get_role(int(custom_id.split("+")[2]))))
                    except discord.Forbidden as f:
                        await interaction.response.send_message("付与したいロールの位置がSharkBotのロールよりも\n上にあるため付与できませんでした。\nhttps://i.imgur.com/fGcWslT.gif", ephemeral=True)
                    except:
                        await interaction.response.send_message(f"認証に失敗しました。\n{sys.exc_info()}", ephemeral=True)
                elif "poll+" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        des = interaction.message.embeds[0].description.split("\n")
                        text = ""
                        for d in des:
                            if d.split(": ")[0] == custom_id.split("+")[1]:
                                ct = int(d.split(": ")[1]) + 1
                                text += f"{d.split(": ")[0]}: {ct}\n"
                                continue
                            text += f"{d}\n"
                        await interaction.message.edit(embed=discord.Embed(title=f"{interaction.message.embeds[0].title}", description=f"{text}", color=discord.Color.green()))
                        await interaction.followup.send(content="投票しました。", ephemeral=True)
                    except:
                        await interaction.followup.send(f"投票に失敗しました。\n{sys.exc_info()}", ephemeral=True)
                elif "poll_done" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        if custom_id.split("+")[1] == f"{interaction.user.id}":
                            await interaction.message.edit(view=None)
                            await interaction.followup.send(content="集計しました。", ephemeral=True)
                        else:
                            await interaction.followup.send(content="権限がありません。", ephemeral=True)
                    except:
                        await interaction.followup.send(f"集計に失敗しました。\n{sys.exc_info()}", ephemeral=True)
                elif "ticket_v1" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        if f"{interaction.user.id}" in tku:
                            return await interaction.followup.send(f"複数チケットは作成できません。", ephemeral=True)
                        overwrites = {
                            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                            interaction.guild.me: discord.PermissionOverwrite(read_messages=True),
                            interaction.user: discord.PermissionOverwrite(read_messages=True)
                        }
                        tkc = await interaction.guild.create_text_channel(name=f"{interaction.user.name}-ticket", overwrites=overwrites)
                        view = discord.ui.View()
                        view.add_item(discord.ui.Button(label="閉じる", custom_id="delete_ticket", style=discord.ButtonStyle.red))
                        await tkc.send(embed=discord.Embed(title=f"`{interaction.user.name}`のチケット", color=discord.Color.green()), view=view)
                        tku.append(f"{interaction.user.id}")
                        await interaction.followup.send(f"チケットを作成しました。\n{tkc.jump_url}", ephemeral=True)
                    except:
                        await interaction.followup.send(f"チケット作成に失敗しました。\n{sys.exc_info()}", ephemeral=True)
                elif "delete_ticket" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        try:
                            tku.remove(f"{interaction.user.id}")
                        except:
                            pass
                        await interaction.channel.delete()
                    except:
                        await interaction.followup.send(f"チケット削除に失敗しました。\n{sys.exc_info()}", ephemeral=True)
                elif "freech_v1" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        if f"{interaction.user.id}" in freech:
                            return await interaction.followup.send(f"複数部屋は作成できません。", ephemeral=True)
                        if interaction.channel.category:
                            tkc = await interaction.channel.category.create_text_channel(name=f"{interaction.user.name}の部屋", overwrites=interaction.channel.category.overwrites)
                        else:
                            tkc = await interaction.guild.create_text_channel(name=f"{interaction.user.name}の部屋")
                        view = discord.ui.View()
                        view.add_item(discord.ui.Button(label="削除", custom_id="freech_ticket", style=discord.ButtonStyle.red))
                        await tkc.send(embed=discord.Embed(title=f"`{interaction.user.name}`の部屋", color=discord.Color.green()), view=view)
                        freech.append(f"{interaction.user.id}")
                        await interaction.followup.send(f"部屋を作成しました。\n{tkc.jump_url}", ephemeral=True)
                    except:
                        await interaction.followup.send(f"部屋作成に失敗しました。\n{sys.exc_info()}", ephemeral=True)
                elif "freech_ticket" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        try:
                            freech.remove(f"{interaction.user.id}")
                        except:
                            pass
                        await interaction.channel.delete()
                    except:
                        await interaction.followup.send(f"チケット削除に失敗しました。\n{sys.exc_info()}", ephemeral=True)
                elif "boostauth+" in custom_id:
                    try:
                        await interaction.response.defer(ephemeral=True)
                        role = custom_id.split("+")[1]
                        code = self.randstring(30)
                        db = self.bot.async_db["Main"].MemberAddAuthRole
                        await db.replace_one(
                            {"Guild": str(interaction.guild.id), "Code": code}, 
                            {"Guild": str(interaction.guild.id), "Code": code, "Role": role}, 
                            upsert=True
                        )
                        await interaction.followup.send("この認証パネルは、Webにアクセスする必要があります。\nまた、サーバーに追加される場合もあります。\n同意する場合のみ、認証してください。", ephemeral=True, view=discord.ui.View().add_item(discord.ui.Button(label="認証する", url=f"https://discord.com/oauth2/authorize?client_id=1322100616369147924&response_type=code&redirect_uri=https%3A%2F%2Fwww.sharkbot.xyz%2Finvite_auth&scope=identify+guilds.join&state={code}")))
                    except:
                        await interaction.followup.send(f"チケット削除に失敗しました。\n{sys.exc_info()}", ephemeral=True)
        except:
            return

async def setup(bot):
    await bot.add_cog(PanelCog(bot))