import discord
from cogs.utils.checks import *

config = load_config()
command_prefix = config['cmd_prefix']

class autoquote:

	def __init__(self, bot):
		self.bot = bot
		
	async def on_message(self, message):
		if message.content == "^" and message.author == self.bot.user:
			await self.bot.delete_message(message)
			channel = message.channel
			search = self.bot.all_log[message.channel.id + ' ' + message.server.id][-2]
			result = search[0]
			await self.bot.send_message(message.channel, "{}quote {}".format(command_prefix, result.id))
	
def setup(bot):
    bot.add_cog(autoquote(bot))