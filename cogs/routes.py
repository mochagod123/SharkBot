from typing import Dict
from discord.ext import commands, ipc
from discord.ext.ipc.server import Server
from discord.ext.ipc.objects import ClientPayload
import json

class Routes(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        if not hasattr(bot, "ipc"):
            bot.ipc = ipc.Server(self.bot, secret_key="🐼")
    
    async def cog_unload(self) -> None:
        await self.bot.ipc.stop()
        self.bot.ipc = None

    @Server.route()
    async def get_user_data(self, data: ClientPayload) -> Dict:
        user = self.bot.get_user(data.user_id)
        return user._to_minimal_user_json()

    @Server.route()
    async def get_guild_count(self, data):
        return len(self.bot.guilds) # returns the len of the guilds to the client

    @Server.route()
    async def get_guild_ids(self, data):
        final = []
        for guild in self.bot.guilds:
            final.append(guild.id)
        return final # returns the guild ids to the client

    @Server.route()
    async def get_guild(self, data):
        guild = self.bot.get_guild(data.guild_id)
        if guild is None: return None

        guild_data = {
            "name": guild.name,
            "id": guild.id,
            "prefix" : "?"
        }

        return json.dumps(guild_data)

async def setup(bot):
    await bot.add_cog(Routes(bot))