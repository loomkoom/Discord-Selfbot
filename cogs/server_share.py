import requests
from urllib import parse
from bs4 import BeautifulSoup
from appuselfbot import bot_prefix
from discord.ext import commands
from cogs.utils.checks import *
from PythonGists import PythonGists

'''Server share cog for creating a gist of members with x number of shared servers'''


class ServerShare:

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def servershare(self, ctx, *, num_servers):
        """Creates a GitHub gist of all members (does not have to be from the server in which the message is posted) as long as they have a specified number of mutual servers
        It can also include a certain server if specified by the exact server name.
        
        Usage:

        a) >servershare <number_of_servers> 
        b) >servershare <number_of_servers> | server=<server_to_include>
        
        Example: `>servershare 3 | server=Appu's Selfbot` will include all members of all servers who have atleast 3 servers in common, and one of them must be Appu's Selfbot
        """
        ser = False
        if " | server=" in num_servers:
            try:
                print(num_servers.split(" | server=")[0])
                num = int(num_servers.split(" | server=")[0])
                ser = num_servers.split(" | server=")[1]
                #print(server)
                
            except:
                await self.bot.send_message(ctx.message.channel, bot_prefix + "Wrong format")
                return
                
        else:
            try:
                num = int(num_servers)
                print(num)
            except:
                await self.bot.send_message(ctx.message.channel, bot_prefix + "The argument isnt an integer")
                await self.bot.delete_message(ctx.message)
                return
        await self.bot.delete_message(ctx.message)
        data = {}
        for server in self.bot.servers:
            for user in server.members:
                for guild in self.bot.servers:
                    if guild.get_member(user.id) and guild.id != server.id and not user.bot:
                        if user not in data: 
                            data[user] = set([])
                        data[user].add(guild.name)

        remUsers = []
        del data[ctx.message.author]
        for a in data:
            if len(data[a]) < num:
                remUsers.append(a)
            elif ser:
                if ser not in data[a]:
                    remUsers.append(a)
        for b in remUsers:
            del data[b]
        result = ""
        result = result + 'Users I share a server with:\nUser - Servers\n'
        for user in data:
            servers = ', '.join(data[user])
            result = result + user.name + ' - ' + servers + '\n'
        url = PythonGists.Gist(description='People who share '+ str(num) + ' servers with '+ ctx.message.author.name , content=str(result), name='output.txt')
        embed = discord.Embed(title="Shared Servers", color=discord.Color.blue())
        embed.set_author(name="GitHub Gist", url=url)
        embed.url = url
        if ser is False:
            embed.description = "People who share " + str(num) + " servers with " + ctx.message.author.name + "."
        else:
            embed.description = "People who share " + str(num) + " servers with " + ctx.message.author.name + " and have " + str(ser) + " server in common."
        await self.bot.send_message(ctx.message.channel, embed=embed)


def setup(bot):
    bot.add_cog(ServerShare(bot))