from discord.ext import commands
import discord
import traceback
import sys
import logging
import asyncio

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print(f"init -> HelpCog")

    @commands.command(name="about")
    async def shark_bot_about(self, ctx: commands.Context):
        await ctx.reply(embed=discord.Embed(title="このBotは、最小環境のSharkBotです。", description="テストなどに使います。", color=discord.Color.green()))

async def setup(bot):
    await bot.add_cog(HelpCog(bot))