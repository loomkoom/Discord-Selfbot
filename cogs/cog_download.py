﻿import discord
import os
import requests
from github import Github
import json
from discord.ext import commands
from bs4 import BeautifulSoup
from cogs.utils.checks import parse_prefix

"""Cog for cog downloading."""


class CogDownloading:
    
    def __init__(self, bot):
        self.bot = bot

    async def githubUpload(self, username, password, repo_name, link, file_name):
        g = Github(username, password)
        repo = g.get_user().get_repo(repo_name)
        req = requests.get(link)
        if req.encoding != "utf-8":
            filecontent = req.text.encode("utf-8")
        else:
            filecontent = req.text
        await self.bot.say("Uploading to GitHub. Heroku users, wait for the bot to restart")
        repo.create_file('/cogs/' + file_name, 'Commiting file: ' + file_name + ' to GitHub', filecontent)
        
    @commands.group(pass_context=True)
    async def cog(self, ctx):
        """Manage custom cogs from ASCII. >help cog for more information.
        The Appu Selfbot Cog Importable Index (aka ASCII) is a server that hosts custom cogs for the bot.
        >cog install <cog> - Install a custom cog from ASCII.
        >cog uninstall <cog> - Uninstall one of your ASCII cogs.
        >cog list - List all cogs on ASCII.
        >cog view <cog> - View information about a cog on ASCII.
        >cog update - Update all of your ASCII cogs.
        If you would like to add a custom cog to ASCII, see http://appucogs.tk
        """
        if ctx.invoked_subcommand is None:
            await self.bot.delete_message(ctx.message)
            await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + "Invalid usage. Valid subcommands: `install`, `uninstall`, `view`, `update`\nDo `help cog` for more information.")
        
                
    @cog.command(pass_context=True)
    async def install(self, ctx, cog):
        """Install a custom cog from ASCII."""
        def check(msg):
            if msg:
                return msg.content.lower().strip() == 'y' or msg.content.lower().strip() == 'n'
            else:
                return False
                
        await self.bot.delete_message(ctx.message)
        response = requests.get("http://appucogs.tk/cogs/{}.json".format(cog))
        if response.status_code == 404:
            await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + "That cog couldn't be found on the network. Check your spelling and try again.")
        else:
            cog = response.json()
            embed = discord.Embed(title=cog["title"], description=cog["description"])
            embed.set_author(name=cog["author"])
            await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + "Are you sure you want to download this cog? (y/n)", embed=embed)
            reply = await self.bot.wait_for_message(author=ctx.message.author, check=check)
            if reply.content.lower() == "y":
                coglink = cog["link"]
                download = requests.get(cog["link"]).text
                filename = cog["link"].rsplit("/", 1)[1]
                with open("settings/github.json", "r+") as fp:
                    opt = json.load(fp)
                    if opt['username'] != "":
                        #try:
                            await self.githubUpload(opt['username'], os.environ['password'], os.environ['reponame'], coglink, filename)
                        #except:
                         #   await self.bot.send_message(ctx.message.channel, "Wrong GitHub account credentials")
                with open("cogs/" + filename, "wb+") as f:
                    f.write(download.encode("utf-8"))
                try:
                    self.bot.load_extension("cogs." + filename.rsplit(".", 1)[0])
                    await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + "Successfully downloaded the `{}` cog.".format(cog["title"]))
                except Exception as e:
                    os.remove("cogs/" + filename)
                    await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + "There was an error loading your cog: `{}: {}` You may want to report this error to the author of the cog.".format(type(e).__name__, str(e)))
            else:
                await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + "Didn't download `{}`: user cancelled.".format(cog["title"]))
    
    @cog.command(pass_context=True)
    async def uninstall(self, ctx, cog):
        """Uninstall one of your custom ASCII cogs."""
        def check(msg):
            if msg:
                return msg.content.lower().strip() == 'y' or msg.content.lower().strip() == 'n'
            else:
                return False
                
        await self.bot.delete_message(ctx.message)
        response = requests.get("http://appucogs.tk/cogs/{}.json".format(cog))
        if response.status_code == 404:
            await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + "That's not a real cog!")
        else:
            found_cog = response.json()
            if os.path.isfile("cogs/" + cog + ".py"):
                embed = discord.Embed(title=found_cog["title"], description=found_cog["description"])
                embed.set_author(name=found_cog["author"])
                await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + "Are you sure you want to delete this cog? (y/n)", embed=embed)
                reply = await self.bot.wait_for_message(author=ctx.message.author, check=check)
                if reply.content.lower() == "y":
                    os.remove("cogs/" + cog + ".py")
                    self.bot.unload_extension("cogs." + cog)
                    await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + "Successfully deleted the `{}` cog.".format(found_cog["title"]))
                else:
                    await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + "Didn't delete `{}`: user cancelled.".format(found_cog["title"]))
            else:
                await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + "You don't have `{}` installed!".format(found_cog["title"]))
    
    @cog.command(pass_context=True)
    async def list(self, ctx):
        """List all cogs on ASCII."""
        await self.bot.delete_message(ctx.message)
        site = requests.get('https://github.com/LyricLy/ASCII/tree/master/cogs').text
        soup = BeautifulSoup(site, "lxml")
        data = soup.find_all(attrs={"class": "js-navigation-open"})
        list = []
        for a in data:
            list.append(a.get("title"))
        embed = discord.Embed(title="Available Cogs", description="")
        for entry in list[2:]:
            entry = entry.rsplit(".")[0]
            if os.path.isfile("cogs/" + entry + ".py"):
                embed.description += "\✅ `{}`\n".format(entry)
            else:
                embed.description += "\🆕 `{}`\n".format(entry)
        embed.set_footer(text="To view information about a specific cog, do >cog view <cog>")
        await self.bot.send_message(ctx.message.channel, content=parse_prefix(self.bot, "[b]Use `[c]install/uninstall <cog_name>` to manage your cogs."), embed=embed)
        
    @cog.command(pass_context=True)
    async def view(self, ctx, cog):
        """View information about a cog on ASCII."""
        await self.bot.delete_message(ctx.message)
        response = requests.get("http://appucogs.tk/cogs/{}.json".format(cog))
        if response.status_code == 404:
            await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + "That cog couldn't be found on the network. Check your spelling and try again.")
        else:
            cog = response.json()
            embed = discord.Embed(title=cog["title"], description=cog["description"])
            embed.set_author(name=cog["author"])
            await self.bot.send_message(ctx.message.channel, embed=embed)
            
    @cog.command(pass_context=True)
    async def update(self, ctx):
        """Update all of your installed ASCII cogs."""
        await self.bot.delete_message(ctx.message)
        msg = await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + "Updating...")
        site = requests.get('https://github.com/LyricLy/ASCII/tree/master/cogs').text
        soup = BeautifulSoup(site, "lxml")
        data = soup.find_all(attrs={"class": "js-navigation-open"})
        list = []
        for a in data:
            list.append(a.get("title"))
        embed = discord.Embed(title="Cog list", description="")
        successful = 0
        failures = 0
        for entry in list[2:]:
            entry = entry.rsplit(".")[0]
            if os.path.isfile("cogs/" + entry + ".py"):
                cog = requests.get("http://appucogs.tk/cogs/{}.json".format(entry)).json()
                link = cog["link"]
                download = requests.get(link).text
                filename = link.rsplit("/", 1)[1]
                with open("cogs/" + filename, "wb+") as f:
                    f.write(download.encode("utf-8"))
                try:
                    self.bot.load_extension("cogs." + filename.rsplit(".", 1)[0])
                    successful += 1
                except Exception as e:
                    failures += 1
                    os.remove("cogs/" + filename)
                    await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + "There was an error updating the `{}` cog: `{}: {}` You may want to report this error to the author of the cog.".format(cog["title"], type(e).__name__, str(e)))
        if failures == 0:
            await self.bot.edit_message(msg, self.bot.bot_prefix + "Updated all cogs successfully.")
        else:
            await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + "Updated {}/{} cogs successfully.".format(successful, successful + failures))


def setup(bot):
    bot.add_cog(CogDownloading(bot))
