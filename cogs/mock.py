import discord
import random
from discord.ext import commands
from cogs.utils.checks import *

class mock:

	def __init__(self, bot):
		self.bot = bot

	@commands.command(pass_context=True)
	async def mock(self, ctx, *, msg=""):
		"""Use >mock to randomized capitalization on a message or string.
		Better random comming soon™
		Usage:
		>mock a string
			A sTRiNg
		>mock
			laSt SeNT MeSsaGE
		>mock (message id)
			THaT mEsSAgE
		"""
		result = ""
		if msg:
			if msg.isdigit():
				async for message in self.bot.logs_from(ctx.message.channel, 100):
					if message.id == msg:
						msg = message.content
						break
		else:
			switch = False
			async for message in self.bot.logs_from(ctx.message.channel, 2):
				if switch:
					msg = message.content
				else:
					switch = True
		for char in msg:
			value = random.choice([True, False])
			if value == True:
				result += char.upper()
			if value == False:
				result += char.lower()
		await self.bot.delete_message(ctx.message)
		await self.bot.send_message(ctx.message.channel, result)
		
def setup(bot):
	bot.add_cog(mock(bot))
