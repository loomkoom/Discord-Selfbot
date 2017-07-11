import discord
import datetime
import random
import requests
import json
from PythonGists import PythonGists
from discord.ext import commands
from cogs.utils.checks import *

'''Quoting, without a name or channel'''

class AnonQuote:
    def __init__(self, bot):
        self.bot = bot
        config = load_config()
        self.bot_prefix = config["bot_identifier"]
    
    @commands.command(pass_context=True)
    async def noquote(self, ctx, *, msg: str = None):
        """Quote a message. >help noquote for more info.
        >noquote - quotes the last message sent in the channel.
        >noquote <words> - tries to search for a message in the server that contains the given words and quotes it.
        >noquote <message_id> - quotes the message with the given message id. Ex: >noquote 302355374524644290(Enable developer mode to copy message ids)."""
        result = channel = None
        await self.bot.delete_message(ctx.message)
        quote_cmd = ctx.message.content.split(' ', 1)[0]
        if msg:
            try:
                length = len(self.bot.all_log[ctx.message.channel.id + ' ' + ctx.message.server.id])
                if length < 201:
                    size = length
                else:
                    size = 200
                for channel in ctx.message.server.channels:
                    if str(channel.type) == 'text':
                        if channel.id + ' ' + ctx.message.server.id in self.bot.all_log:
                            for i in range(length - 2, length - size, -1):
                                try:
                                    search = self.bot.all_log[channel.id + ' ' + ctx.message.server.id][i]
                                except:
                                    continue
                                if (msg.lower().strip() in search[0].content.lower() and (search[0].author != ctx.message.author or not search[0].content.startswith(quote_cmd))) or ctx.message.content[6:].strip() == search[0].id:
                                    result = search[0]
                                    break
                            if result:
                                break
            except:
                pass
            if not result:
                for channel in ctx.message.server.channels:
                    try:
                        async for sent_message in self.bot.logs_from(channel, limit=500):
                            if (msg.lower().strip() in sent_message.content.lower() and (sent_message.author != ctx.message.author or not sent_message.content.startswith(quote_cmd))) or msg.strip() == sent_message.id:
                                result = sent_message
                                break
                    except:
                        pass
                    if result:
                        break
        else:
            channel = ctx.message.channel
            search = self.bot.all_log[ctx.message.channel.id + ' ' + ctx.message.server.id][-2]
            result = search[0]
        if result:
            if embed_perms(ctx.message) and result.content:
                em = discord.Embed(description=result.content, timestamp=result.timestamp, color=0xbc0b0b)
                em.set_author(name="Anonymous")
                await self.bot.send_message(ctx.message.channel, embed=em)
            else:
                await self.bot.send_message(ctx.message.channel, '%s - %s```%s```' % (result.author.name, result.timestamp, result.content))
        else:
            await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + 'No quote found.')
            
def setup(bot):
    bot.add_cog(AnonQuote(bot))
