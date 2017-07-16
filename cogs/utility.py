import datetime
import asyncio
import strawpy
import pytz
import re
import requests
import json
import discord
import os
from PythonGists import PythonGists
from discord.ext import commands
from cogs.utils.checks import embed_perms, cmd_prefix_len, attach_perms, find_channel
from bs4 import BeautifulSoup
from urllib import parse
from urllib.request import Request, urlopen

'''Module for fun/meme commands commands'''


class Utility:
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def get_datetime():
        a = None
        tzerror = False
        with open('settings/optional_config.json', 'r') as fp:
            opt = json.load(fp)
            try:
                if opt['timezone']:
                    tz = opt['timezone']
                    a = pytz.timezone(tz)
            except IndexError:
                # Timezone entry missing in configuration file
                pass
            except pytz.exceptions.UnknownTimeZoneError:
                tzerror = True
        return datetime.datetime.now(a), tzerror

    @commands.command(pass_context=True)
    async def now(self, ctx):
        """Date time module."""
        dandt, tzerror = self.get_datetime()
        if embed_perms(ctx.message):
            em = discord.Embed(color=discord.Color.blue())
            em.add_field(name=u'\u23F0 Time', value="{:%H:%M:%S}".format(dandt), inline=False)
            em.add_field(name=u'\U0001F4C5 Date', value="{:%d %B %Y}".format(dandt), inline=False)
            if tzerror:
                em.add_field(name=u'\u26A0 Warning', value="Invalid timezone specified, system timezone was used instead.", inline=False)

            await self.bot.send_message(ctx.message.channel, content=None, embed=em)
        else:
            msg = '**Local Date and Time:** ```{:Time: %H:%M:%S\nDate: %Y-%m-%d```}'.format(dandt)
            await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + msg)
        await self.bot.delete_message(ctx.message)

    @commands.command(pass_context=True)
    async def time(self, ctx):
        """Show current time"""
        await self.bot.delete_message(ctx.message)
        dandt, tzerror = self.get_datetime()
        msg = '{:Time: `%H:%M:%S`}'.format(dandt)
        await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + msg)

    @commands.command(pass_context=True)
    async def date(self, ctx):
        """Show current date"""
        await self.bot.delete_message(ctx.message)
        dandt, tzerror = self.get_datetime()
        msg = '{:Date: `%d %B %Y`}'.format(dandt)
        await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + msg)

    @commands.command(pass_context=True, aliases=['emote'])
    async def emoji(self, ctx, *, msg):
        """
        Embed or copy a custom emoji (from any server).
        Usage:
        1) >emoji :smug: [Will display the smug emoji as an image]
        2) >emoji copy :smug: [Will add the emoji as a custom emote for the server]
        """
        copy_emote_bool = False
        if "copy " in msg:
            msg = msg.split("copy ")[1]
            copy_emote_bool = True
        if msg.startswith('s '):
            msg = msg[2:]
            get_server = True
        else:
            get_server = False
        msg = msg.strip(':')
        if msg.startswith('<'):
            msg = msg[2:].split(':', 1)[0].strip()
        url = emoji = server = None
        exact_match = False
        for server in self.bot.servers:
            for emoji in server.emojis:
                if msg.strip().lower() in str(emoji):
                    url = emoji.url
                    emote_name = emoji.name
                if msg.strip() == str(emoji).split(':')[1]:
                    url = emoji.url
                    emote_name = emoji.name
                    exact_match = True
                    break
            if exact_match:
                break
        response = requests.get(emoji.url, stream=True)
        name = emoji.url.split('/')[-1]
        with open(name, 'wb') as img:

            for block in response.iter_content(1024):
                if not block:
                    break

                img.write(block)

        if attach_perms(ctx.message) and url:
            if get_server:
                await self.bot.send_message(ctx.message.channel,
                                            '**ID:** {}\n**Server:** {}'.format(emoji.id, server.name))
            with open(name, 'rb') as fp:
                if copy_emote_bool:
                    e = fp.read()
                else:
                    await self.bot.send_file(ctx.message.channel, fp)
            if copy_emote_bool:
                try:
                    await self.bot.create_custom_emoji(ctx.message.server, name=emote_name, image=e)
                    embed = discord.Embed(title="Added new emote", color=discord.Color.blue())
                    embed.description = "New emote added: " + emote_name
                    await self.bot.say("", embed=embed)
                except:
                    await self.bot.say("Not enough permissions to do this")
            os.remove(name)
        elif not embed_perms(ctx.message) and url:
            await self.bot.send_message(ctx.message.channel, url)
        else:
            await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + 'Could not find emoji.')

        return await self.bot.delete_message(ctx.message)

    @commands.command(pass_context=True)
    async def code(self, ctx, *, msg):
        """Write text in code format"""
        await self.bot.delete_message(ctx.message)
        await self.bot.send_message(ctx.message.channel, "```" + msg + "```")

    @commands.command(pass_context=True)
    async def timezone(self, ctx, *, msg):
        """Set preferred timezone. Use `>timezonelist` for full list of timezones"""
        if msg:
            with open('settings/optional_config.json', 'r+') as fp:
                opt = json.load(fp)
                opt['timezone'] = msg
                fp.seek(0)
                fp.truncate()
                json.dump(opt, fp, indent=4)
            await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + 'Preferred timezone has been set')
        else:
            await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + 'You can find the list of timezones at `https://gist.github.com/anonymous/67129932414d0b82f58758a699a5a0ef`')

    @commands.command(pass_context=True)
    async def timezonelist(self, ctx):
        """List of all available timezones"""
        await self.bot.delete_message(ctx.message)
        embed = discord.Embed()
        embed.description = "[List of valid timezones](https://gist.github.com/anonymous/67129932414d0b82f58758a699a5a0ef)"
        await self.bot.send_message(ctx.message.channel, "", embed=embed)

    @commands.command(pass_context=True)
    async def cmdprefix(self, ctx, *, msg: str = None):
        """Set command prefix, needs a reboot to activate"""
        if msg:
            with open('settings/config.json', 'r+') as fp:
                opt = json.load(fp)
                opt['cmd_prefix'] = msg
                fp.seek(0)
                fp.truncate()
                json.dump(opt, fp, indent=4)
            await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + 'Prefix changed. use `restart` to reboot the bot for the updated prefix')
        else:
            await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + 'Type a prefix as an argument for the `prefix` command')

    @commands.command(pass_context=True)
    async def customcmdprefix(self, ctx, *, msg: str = None):
        """Set command prefix, needs a reboot to activate"""
        if msg:
            with open('settings/config.json', 'r+') as fp:
                opt = json.load(fp)
                opt['customcmd_prefix'] = msg
                fp.seek(0)
                fp.truncate()
                json.dump(opt, fp, indent=4)
            self.bot.customcmd_prefix = msg
            await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + 'Prefix changed.')
        else:
            await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + 'Type a prefix as an argument for the `prefix` command')

    @commands.command(pass_context=True)
    async def botprefix(self, ctx, *, msg: str = None):
        """Set bot prefix"""
        if msg:
            with open('settings/config.json', 'r+') as fp:
                opt = json.load(fp)
                opt['bot_identifier'] = msg
                fp.seek(0)
                fp.truncate()
                json.dump(opt, fp, indent=4)
            self.bot.bot_prefix = msg + ' '
            await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + 'Prefix changed.')
        else:
            await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + 'Type a prefix as an argument for the `prefix` command')

    @commands.command(pass_context=True)
    async def calc(self, ctx, *, msg):
        """Simple calculator. Ex: >calc 2+2"""
        equation = msg.strip().replace('^', '**')
        if '=' in equation:
            left = eval(equation.split('=')[0])
            right = eval(equation.split('=')[1])
            answer = str(left == right)
        else:
            answer = str(eval(equation))
        if embed_perms(ctx.message):
            em = discord.Embed(color=0xD3D3D3, title='Calculator')
            em.add_field(name='Input:', value=msg.replace('**', '^'), inline=False)
            em.add_field(name='Output:', value=answer, inline=False)
            await self.bot.send_message(ctx.message.channel, content=None, embed=em)
            await self.bot.delete_message(ctx.message)
        else:
            await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + answer)


    @commands.command(aliases=['sd'],pass_context=True)
    async def selfdestruct(self, ctx, *, amount: str = None):
        """Builds a self-destructing message. Ex: >sd 5"""
        killmsg = self.bot.self_log[ctx.message.channel.id][len(self.bot.self_log[ctx.message.channel.id]) - 2]
        timer = int(amount.strip())
        # Animated countdown because screw rate limit amirite
        destroy = await self.bot.edit_message(ctx.message,
                                              self.bot.bot_prefix + 'The above message will self-destruct in:')
        msg = await self.bot.send_message(ctx.message.channel, '``%s  |``' % timer)
        for i in range(0, timer, 4):
            if timer - 1 - i == 0:
                await self.bot.delete_message(destroy)
                msg = await self.bot.edit_message(msg, '``0``')
                break
            else:
                msg = await self.bot.edit_message(msg, '``%s  |``' % int(timer - 1 - i))
                await asyncio.sleep(1)
            if timer - 1 - i != 0:
                if timer - 2 - i == 0:
                    await self.bot.delete_message(destroy)
                    msg = await self.bot.edit_message(msg, '``0``')
                    break
                else:
                    msg = await self.bot.edit_message(msg, '``%s  /``' % int(timer - 2 - i))
                    await asyncio.sleep(1)
            if timer - 2 - i != 0:
                if timer - 3 - i == 0:
                    await self.bot.delete_message(destroy)
                    msg = await self.bot.edit_message(msg, '``0``')
                    break
                else:
                    msg = await self.bot.edit_message(msg, '``%s  -``' % int(timer - 3 - i))
                    await asyncio.sleep(1)
            if timer - 3 - i != 0:
                if timer - 4 - i == 0:
                    await self.bot.delete_message(destroy)
                    msg = await self.bot.edit_message(msg, '``0``')
                    break
                else:
                    msg = await self.bot.edit_message(msg, '``%s  \ ``' % int(timer - 4 - i))
                    await asyncio.sleep(1)
        await self.bot.edit_message(msg, ':bomb:')
        await asyncio.sleep(.5)
        await self.bot.edit_message(msg, ':fire:')
        await self.bot.edit_message(killmsg, ':fire:')
        await asyncio.sleep(.5)
        await self.bot.delete_message(msg)
        await self.bot.delete_message(killmsg)

    @commands.command(aliases=['d'], pass_context=True)
    async def delete(self, ctx, txt: str=None, channel: str=None):
        """Deletes the last message sent or n messages sent. Ex: >d 5"""
        if txt: # If number of seconds/messages are specified
            await self.bot.delete_message(ctx.message)
            deleted = 0
            if txt == "all":limit = 1000
            else:
                txt = int(txt)
                limit = 200
                if txt > 200: txt = 200
            if channel:
                channel = find_channel(ctx.message.server.channels, channel)
                if not channel: channel = find_channel(self.bot.get_all_channels(), channel)
            else: channel = ctx.message.channel
            async for sent_message in self.bot.logs_from(channel, limit=limit):
                if sent_message.author == ctx.message.author:
                    try:
                        await self.bot.delete_message(sent_message)
                        deleted += 1
                    except: pass
                    if deleted == txt: break
        else: # If no number specified, delete last message immediately
            await self.bot.delete_message(self.bot.self_log[ctx.message.channel.id].pop())
            await self.bot.delete_message(self.bot.self_log[ctx.message.channel.id].pop())

    @commands.command(pass_context=True)
    async def spoiler(self, ctx, *, msg: str):
        """Spoiler tag. Ex: >spoiler Some book | They get married."""
        try:
            if " | " in msg:
                spoiled_work, spoiler = msg.split(" | ", 1)
            else:
                spoiled_work = msg
                spoiler = msg
            await self.bot.edit_message(ctx.message, self.bot.bot_prefix + 'Spoiler for `' + spoiled_work + '`: \n`'
                                        + ''.join(
                map(lambda c: chr(ord('a') + (((ord(c) - ord('a')) + 13) % 26)) if c >= 'a' and c <= 'z' else c,
                    spoiler))
                                        + '`\n' + self.bot.bot_prefix + 'Use http://rot13.com to decode')
        except:
            await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + 'Could not encrypt spoiler.')

    @commands.group(pass_context=True)
    async def gist(self, ctx):
        """Posts to gist"""
        if ctx.invoked_subcommand is None:
            pre = cmd_prefix_len()
            url = PythonGists.Gist(
                description='Created in channel: {} in server: {}'.format(ctx.message.channel, ctx.message.server),
                content=ctx.message.content[4 + pre:].strip(), name='Output')
            await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + 'Gist output: ' + url)
            await self.bot.delete_message(ctx.message)

    @gist.command(pass_context=True)
    async def file(self, ctx, *, msg):
        """Create gist of file"""
        try:
            with open(msg) as fp:
                output = fp.read()
                url = PythonGists.Gist(
                    description='Created in channel: {} in server: {}'.format(ctx.message.channel, ctx.message.server),
                    content=output, name=msg.replace('/', '.'))
                await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + 'Gist output: ' + url)
        except:
            await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + 'File not found.')
        finally:
            await self.bot.delete_message(ctx.message)

    @commands.command(pass_context=True)
    async def uni(self, ctx, *, msg: str):
        """Convert to unicode emoji if possilbe. Ex: >uni :eyes:"""
        await self.bot.send_message(ctx.message.channel, "`" + msg.replace("`", "") + "`")

    @commands.command(pass_context=True)
    async def poll(self, ctx, *, msg):
        """Create a strawpoll. Ex: >poll Favorite color = Blue | Red | Green"""
        loop = asyncio.get_event_loop()
        try:
            options = [op.strip() for op in msg.split('|')]
            if '=' in options[0]:
                title, options[0] = options[0].split('=')
                options[0] = options[0].strip()
            else:
                title = 'Poll by %s' % ctx.message.author.name
        except:
            return await self.bot.send_message(ctx.message.channel,
                                               self.bot.bot_prefix + 'Invalid Syntax. Example use: ``>poll Favorite color = Blue | Red | Green | Purple``')

        poll = await loop.run_in_executor(None, strawpy.create_poll, title.strip(), options)
        await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + poll.url)

    @commands.command(pass_context=True, aliases=['source'])
    async def sauce(self, ctx, *, txt: str = None):
        """Find source of image. Ex: >sauce http://i.imgur.com/NIq2U67.png"""
        if not txt:
            return await self.bot.send_message(ctx.message.channel,
                                               self.bot.bot_prefix + 'Input a link to check the source. Ex: ``>sauce http://i.imgur.com/NIq2U67.png``')
        await self.bot.delete_message(ctx.message)
        sauce_nao = 'http://saucenao.com/search.php?db=999&url='
        request_headers = {
            "Accept-Language": "en-US,en;q=0.5",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "http://thewebsite.com",
            "Connection": "keep-alive"
        }
        loop = asyncio.get_event_loop()
        try:
            req = Request(sauce_nao + txt, headers=request_headers)
            webpage = await loop.run_in_executor(None, urlopen, req)
        except:
            return await self.bot.send_message(ctx.message.channel,
                                               self.bot.bot_prefix + 'Exceeded daily request limit. Try again tomorrow, sorry!')
        soup = BeautifulSoup(webpage, 'html.parser')
        pretty_soup = soup.prettify()
        em = discord.Embed(color=0xaa550f, description='**Input:**\n{}\n\n**Results:**'.format(txt))
        try:
            em.set_thumbnail(url=txt)
        except:
            pass
        match = re.findall(r'(?s)linkify" href="(.*?)"', str(soup.find('div', id='middle')))
        title = re.findall(r'(?s)<div class="resulttitle">(.*?)</td', str(soup.find('div', id='middle')))
        similarity_percent = re.findall(r'(?s)<div class="resultsimilarityinfo">(.*?)<',
                                        str(soup.find('div', id='middle')))
        ti = ''
        if title and float(similarity_percent[0][:-1]) > 60.0:
            title = title[0].strip().replace('<br/>', '\n').replace('<strong>', '').replace('</strong>', '').replace(
                '<div class="resultcontentcolumn">', '').replace('<span class="subtext">', '\n').replace('<small>',
                                                                                                         '').replace(
                '</span>', ' ').replace('</small>', '').replace('</tr>', '').replace('</td>', '').replace('</table>',
                                                                                                          '').replace(
                '</div>', '').split('\n')
            ti = '\n'.join([i.strip() for i in title if i.strip() != ''])
            if '</a>' not in ti:
                em.add_field(name='Source', value=ti)

            try:
                pretty_soup = pretty_soup.split('id="result-hidden-notification"', 1)[0]
            except:
                pass
            episode = re.findall(r'(?s)<span class="subtext">\n EP(.*?)<div', pretty_soup)
            ep = ''
            if episode:
                episode = episode[0].strip().replace('<br/>', '').replace('<strong>', '**').replace('</strong>',
                                                                                                    '**').replace(
                    '<span class="subtext">', '').replace('</span>', '').replace('</tr>', '').replace('</td>',
                                                                                                      '').replace(
                    '</table>', '').replace('</div>', '').split('\n')

                ep = ' '.join([j.strip() for j in episode if j.strip() != ''])
                ep = ep.replace('Est Time:', '\nEst Time:')
                em.add_field(name='More Info', value='**Episode** ' + ep, inline=False)
            est_time = re.findall(r'(?s)Est Time:(.*?)<div', pretty_soup)
            if est_time and 'Est Time:' not in ep:
                est_time = est_time[0].strip().replace('<br/>', '').replace('<strong>', '').replace('</strong>',
                                                                                                    '').replace(
                    '<span class="subtext">', '').replace('</span>', '').replace('</tr>', '').replace('</td>',
                                                                                                      '').replace(
                    '</table>', '').replace('</div>', '').split('\n')

                est = ' '.join([j.strip() for j in est_time if j.strip() != ''])
                est = est.replace('Est Time:', '\nEst Time:')
                em.add_field(name='More Info', value='**Est Time:** ' + est, inline=False)

        sources = ''
        count = 0
        source_sites = {'www.pixiv.net': 'pixiv', 'danbooru': 'danbooru', 'seiga.nicovideo': 'nico nico seiga',
                        'yande.re': 'yande.re', 'openings.moe': 'openings.moe', 'fakku.net': 'fakku',
                        'gelbooru': 'gelbooru',
                        'deviantart': 'deviantart', 'bcy.net': 'bcy.net', 'konachan.com': 'konachan',
                        'anime-pictures.net': 'anime-pictures.net', 'drawr.net': 'drawr'}
        for i in match:
            if not i.startswith('http://saucenao.com'):
                if float(similarity_percent[count][:-1]) > 60.0:
                    link_to_site = '{} - {}, '.format(i, similarity_percent[count])
                    for site in source_sites:
                        if site in i:
                            link_to_site = '[{}]({}) - {}, '.format(source_sites[site], i, similarity_percent[count])
                            break
                    sources += link_to_site
                    count += 1

            if count == 4:
                break
        sources = sources.rstrip(', ')

        material = re.search(r'(?s)Material:(.*?)</div', str(soup.find('div', id='middle')))
        if material and ('Materials:' not in ti and 'Material:' not in ti):
            material_list = material.group(1).strip().replace('<br/>', '\n').replace('<strong>', '').replace(
                '</strong>', '').split('\n')
            mat = ', '.join([i.strip() for i in material_list if i.strip() != ''])
            em.add_field(name='Material(s)', value=mat)

        characters = re.search(r'(?s)Characters:(.*?)</div', str(soup.find('div', id='middle')))
        if characters and ('Characters:' not in ti and 'Character:' not in ti):
            characters_list = characters.group(1).strip().replace('<br/>', '\n').replace('<strong>', '').replace(
                '</strong>', '').split('\n')
            chars = ', '.join([i.strip() for i in characters_list if i.strip() != ''])
            em.add_field(name='Character(s)', value=chars)

        creator = re.search(r'(?s)Creator:(.*?)</div', str(soup.find('div', id='middle')))
        if creator and ('Creators:' not in ti and 'Creator:' not in ti):
            creator_list = creator.group(1).strip().replace('<br/>', '\n').replace('<strong>', '').replace('</strong>',
                                                                                                           '').split(
                '\n')
            creat = ', '.join([i.strip() for i in creator_list if i.strip() != ''])
            em.add_field(name='Creator(s)', value=creat)

        if sources != '' and sources:
            em.add_field(name='Source sites - percent similarity', value=sources, inline=False)

        if not sources and not creator and not characters and not material and not title or float(
                similarity_percent[0][:-1]) < 60.0:
            em = discord.Embed(color=0xaa550f, description='**Input:**\n{}\n\n**No results found.**'.format(txt))

        await self.bot.send_message(ctx.message.channel, content=None, embed=em)

    @commands.command(aliases=['nick'], pass_context=True, no_pm=True)
    async def nickname(self, ctx, *, txt: str = None):
        """Change your nickname on a server. Leave empty to remove nick."""
        await self.bot.delete_message(ctx.message)
        try:
            await self.bot.change_nickname(ctx.message.author, txt)
            await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + 'Changed nickname to: `%s`' % txt)
        except:
            await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + 'Unable to change nickname.')

    @commands.command(pass_context=True)
    async def ud(self, ctx, *, msg):
        """Pull data from Urban Dictionary. Use >help ud for more information.
        Usage: >ud <term> - Search for a term on Urban Dictionary.
        You can pick a specific result to use with >ud <term> | <result>.
        If no result is specified, the first result will be used.
        """
        await self.bot.delete_message(ctx.message)
        number = 1
        if " | " in msg:
            msg, number = msg.rsplit(" | ", 1)
        search = parse.quote(msg)
        response = requests.get("http://api.urbandictionary.com/v0/define?term={}".format(search)).text
        result = json.loads(response)
        if result["result_type"] == "no_results":
            await self.bot.send_message(ctx.message.channel,
                                        self.bot.bot_prefix + "{} couldn't be found on Urban Dictionary.".format(msg))
        else:
            try:
                top_result = result["list"][int(number) - 1]
                embed = discord.Embed(title=top_result["word"], description=top_result["definition"],
                                      url=top_result["permalink"])
                try:
                    if result["example"]:
                        embed.add_field(name="Example:", value=top_result["example"])
                except KeyError:
                    pass
                if result["tags"]:
                    embed.add_field(name="Tags:", value=" ".join(result["tags"]))
                embed.set_author(name=top_result["author"],
                                 icon_url="https://lh5.ggpht.com/oJ67p2f1o35dzQQ9fVMdGRtA7jKQdxUFSQ7vYstyqTp-Xh-H5BAN4T5_abmev3kz55GH=w300")
                number = str(int(number) + 1)
                embed.set_footer(text="{} results were found. To see a different result, use >ud {} | {}.".format(
                    len(result["list"]), msg, number))
                await self.bot.send_message(ctx.message.channel, "", embed=embed)
            except IndexError:
                await self.bot.send_message(ctx.message.channel,
                                            self.bot.bot_prefix + "That result doesn't exist! Try >ud {}.".format(msg))

    @commands.command(pass_context=True, aliases=['yt', 'vid', 'video'])
    async def youtube(self, ctx, *, msg):
        """Search for videos on YouTube."""
        search = parse.quote(msg)
        response = requests.get("https://www.youtube.com/results?search_query={}".format(search)).text
        result = BeautifulSoup(response, "lxml")
        await self.bot.delete_message(ctx.message)
        await self.bot.send_message(ctx.message.channel, "https://www.youtube.com{}".format(result.find_all(attrs={'class': 'yt-uix-tile-link'})[0].get('href')))

    @commands.command(pass_context=True)
    async def xkcd(self, ctx, *, comic=""):
        """Pull comics from xkcd."""
        if comic == "random":
            randcomic = requests.get("https://c.xkcd.com/random/comic/".format(comic))
            comic = randcomic.url.split("/")[-2]
        site = requests.get("https://xkcd.com/{}/info.0.json".format(comic))
        if site.status_code == 404:
            site = None
            found = None
            search = parse.quote(comic)
            result = requests.get("https://www.google.co.nz/search?&q={}+site:xkcd.com".format(search)).text
            soup = BeautifulSoup(result, "lxml")
            links = soup.find_all("cite")
            for link in links:
                if link.text.startswith("https://xkcd.com/"):
                    found = link.text.split("/")[3]
                    break
            if not found:
                await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + "That comic doesn't exist!")
            else:
                site = requests.get("https://xkcd.com/{}/info.0.json".format(found))
                comic = found
        if site:
            json = site.json()
            embed = discord.Embed(title="xkcd {}: {}".format(json["num"], json["title"]), url="https://xkcd.com/{}".format(comic))
            embed.set_image(url=json["img"])
            embed.set_footer(text="{}".format(json["alt"]))
            await self.bot.send_message(ctx.message.channel, "", embed=embed)

    @commands.command(pass_context=True)
    async def hastebin(self, ctx, *, data):
        """Post to Hastebin."""
        await self.bot.delete_message(ctx.message)
        post = requests.post("https://hastebin.com/documents", data=data)
        try:
            await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + "Succesfully posted to Hastebin:\nhttps://hastebin.com/{}.txt".format(post.json()["key"]))
        except json.JSONDecodeError:
            await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + "Failed to post to Hastebin. The API may be down right now.")

    @commands.command(pass_context=True)
    async def whoisplaying(self, ctx, *, game):
        """Check how many people are playing a certain game."""
        msg = ""
        for server in self.bot.servers:
            for user in server.members:
                if user.game is not None:
                    if user.game.name is not None:
                        if user.game.name.lower() == game.lower():
                            msg += "{}#{}\n".format(user.name, user.discriminator)
        msg = "\n".join(set(msg.split("\n")))  # remove dupes
        if len(msg) > 1500:
            gist = PythonGists.Gist(description="Number of people playing {}".format(game), content=msg, name="Output")
            await self.bot.send_message(ctx.message.channel, "{}Large output posted to Gist: {}".format(self.bot.bot_prefix, gist))
        elif len(msg) == 0:
            await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + "Nobody is playing that game!")
        else:
            embed = discord.Embed(title="Number of people playing {}".format(game), description=msg)
            await self.bot.send_message(ctx.message.channel, "", embed=embed)
            
    @commands.command(pass_context=True)
    async def animate(self, ctx, animation):
        """Play an animation from a text file. >help animate for more details.
        >animate <animation> - Animate a text file.
        Animation text files are stored in the anims folder. Each frame of animation is put on a new line.
        
        An example text file looks like this:
        family
        fam ily
        fam i ly
        fam i love y
        fam i love you
        
        You can additionally add a number to the top of the file to denote the delay between each frame. The default is 0.2 seconds.
        1
        fam
        fam i
        fam i love
        fam i love you
        """
        try:
            with open("anims/{}.txt".format(animation)) as f:
                anim = f.read().split("\n")
        except IOError:
            return await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + "You don't have that animation in your anims folder!")
        if anim:
            try:
                delay = float(anim[0])
                for frame in anim[1:]:
                    await asyncio.sleep(delay)
                    await self.bot.edit_message(ctx.message, frame)
            except ValueError:
                for frame in anim:
                    await asyncio.sleep(0.2)
                    await self.bot.edit_message(ctx.message, frame)
                    
    @commands.command(pass_context=True)
    async def roles(self, ctx, *, user):
        """Check the roles of a user."""
        await self.bot.delete_message(ctx.message)
        member = ctx.message.server.get_member_named(user)
        if not member:
            member = ctx.message.server.get_member(user)
        if not member:
            try:
                member = ctx.message.mentions[0]
            except IndexError:
                pass
        if not member:
            await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + "That user couldn't be found. Please check your spelling and try again.")
        elif len(member.roles[1:]) >= 1:
            embed = discord.Embed(title="{}'s roles".format(member.name), description="\n".join([x.name for x in member.roles[::-1][:-1]]), colour=member.colour)
            await self.bot.send_message(ctx.message.channel, "", embed=embed)
        else:
            await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + "That user has no roles!")
            
    @commands.command(pass_context=True)
    async def messagedump(self, ctx, limit, filename, details="yes", reverse="no"):
        """Dump messages."""
        await self.bot.delete_message(ctx.message)
        await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + "Downloading messages...")
        if not os.path.isdir('message_dump'):
            os.mkdir('message_dump')
        with open("message_dump/" + filename.rsplit('.', 1)[0] + ".txt", "wb+") as f:
            if reverse == "yes":
                if details == "yes":
                    async for message in self.bot.logs_from(ctx.message.channel, int(limit)):
                        f.write("<{} at {}> {}\n".format(message.author.name, message.timestamp.strftime('%d %b %Y'), message.content).encode())

                else:
                    async for message in self.bot.logs_from(ctx.message.channel, int(limit)):
                        f.write(message.content.encode() + "\n".encode())
            else:
                if details == "yes":
                    async for message in self.bot.logs_from(ctx.message.channel, int(limit), reverse=True):
                        f.write("<{} at {}> {}\n".format(message.author.name, message.timestamp.strftime('%d %b %Y'), message.content).encode())

                else:
                    async for message in self.bot.logs_from(ctx.message.channel, int(limit), reverse=True):
                        f.write(message.content.encode() + "\n".encode())
        await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + "Finished downloading!")
        
    @commands.group(pass_context=True)
    async def link(self, ctx):
        await self.bot.delete_message(ctx.message)
        if ctx.invoked_subcommand is None:
            await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + "Usage: `link <shorten/lengthen> <url>`")
            
    @link.command(pass_context=True)
    async def shorten(self, ctx, url):
        try:
            r = requests.get(url).status_code
        except requests.exceptions.RequestException:
            r = 404
        if r == 200:
            params = {
                "access_token": "757c24db53fac6a6a994439da41bdbbe325dfb99",
                "longUrl": url
            }
            response = requests.get("https://api-ssl.bitly.com/v3/shorten", params=params)
            if response.status_code == 200:
                await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + "<{}>".format(response.json()["data"]["url"]))
            else:
                await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + "There was an error shortening your URL.")
        else:
            await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + "You did not enter a valid URL.")
                
    
    @link.command(pass_context=True)
    async def lengthen(self, ctx, url):
        try:
            r = requests.get(url).status_code
        except requests.exceptions.RequestException:
            r = 404
        if r == 200:
            await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + "<{}>".format(requests.get(url).url))
        else:
            await self.bot.send_message(ctx.message.channel, self.bot.bot_prefix + "You did not enter a valid URL.")

def setup(bot):
    bot.add_cog(Utility(bot))
