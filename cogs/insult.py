import requests
import discord
from bs4 import BeautifulSoup
from discord.ext import commands

'''Insult generator.'''


class InsultGenerator:

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def insult(self, ctx):
      await self.bot.delete_message(ctx.message)
      response = requests.get("http://autoinsult.datahamster.com/index.php?style=3").text
      site = BeautifulSoup(response, "lxml")
      await self.bot.send_message(ctx.message.channel, "{}!".format(site.select("div.insult")[0].text))

def setup(bot):
    bot.add_cog(InsultGenerator(bot))