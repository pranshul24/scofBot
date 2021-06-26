
from twilio.rest import Client
from threading import Thread
from time import sleep
import threading
import datetime
import os
import random
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import requests
import sys
from bs4 import BeautifulSoup
import ssl
from espncricinfo.match import Match

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

liveScoresUrl = "http://static.cricinfo.com/rss/livescores.xml"

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix=';')


account_sid = os.getenv('account_sid')
auth_token = os.getenv('auth_token')
to_contact = os.getenv('to_contact')
twilio_contact = os.getenv('twilio_contact')
to_contact2 = os.getenv('to_contact2')
tem_contact = to_contact
alarms = []
watchMatchOvers = {}
watchMatchWickets = {}
client = Client(account_sid, auth_token)
# cricket_channel_id = os.getenv('cricket_id')


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="with Alarms & Cricket"))


@bot.command(name='toss', help='gives random number in the range (default range = 2)')
async def toss(ctx, *args):
    outp = []
    tot = 0
    if(len(args) == 0):
        tot = 2
    elif(len(args) == 1):
        tot = int(args[0])
    for i in range(tot):
        outp.append(i)
    response = random.choice(outp)
    embedVar = discord.Embed(title="Result", description=response, color=0x00c09a)
    await ctx.channel.send(embed=embedVar)


def alarm_func(arg, cont):
    t = threading.currentThread()
    for i in range(arg):
        if(t.is_running == 1):
            sleep(1)
        else:
            # print("yp")
            return
    call = client.calls.create(
        url='http://demo.twilio.com/docs/voice.xml',
        from_=twilio_contact,
        to=cont
    )
    # print(call.sid)


class Watch(commands.Cog):
    def __init__(self, ctx, matchNum, matchId, milestone, overs):
        self.ctx = ctx
        self.watchMatch.start(ctx, matchNum, matchId, milestone, overs)

    async def cog_unload(self):
        # message_channel = bot.get_channel(int(cricket_channel_id))
        await self.ctx.channel.send("Match has already ended")  # here can send any message to particular channel
        self.watchMatch.cancel()

    @tasks.loop(seconds=30)
    async def watchMatch(self, ctx, matchNum, matchId, milestone, overs):
        # message_channel = bot.get_channel(int(cricket_channel_id))
        curMatch = Match(matchId)
        innings = curMatch.latest_innings
        lastWicket = int(innings["wickets"])
        lastOver = -1
        if matchId in watchMatchOvers:
            lastOver = watchMatchOvers[matchId]
        if matchId in watchMatchWickets:
            lastWicket = watchMatchWickets[matchId]
        # print(lastOver)
        if(milestone == 'w' and ("wickets" in innings) and innings["wickets"] != lastWicket):
            await scorecard(ctx, matchNum, matchId)
            await commentary(ctx, matchNum, 0, matchId)
            lastWicket = int(innings["wickets"])
            watchMatchWickets[matchId] = lastWicket

        elif(milestone == 'o' and ("overs" in innings)):
            # print(milestone == 'o')
            curOver = int(innings["overs"].split(".")[0])
            # print(curOver, " ", overs+lastOver)
            if(curOver < lastOver):  # once 1 inning ends
                curOver = lastOver
            if(curOver == (lastOver+overs)):
                await scorecard(ctx, matchNum, matchId)  # to make sure for index change
                await commentary(ctx, matchNum, 0, matchId)
                watchMatchOvers[matchId] = curOver

        temp = curMatch.innings
        innings = temp[len(temp)-1]
        if(innings["event"] != 0):
            await self.cog_unload()
        # await message_channel.send("Your message") here can send any message to particular channel

    @watchMatch.before_loop
    async def before(self):
        await bot.wait_until_ready()


class AlarmThread(threading.Thread):
    def __init__(self,  *args, **kwargs):
        super(AlarmThread, self).__init__(*args, **kwargs)
        self.is_running = 1


@bot.command(name='del', help='Delete alarm')
async def delete_alarm(ctx, *args):
    if(len(args) == 1 and int(args[0]) <= len(alarms) and int(args[0]) > 0):
        alarms[int(args[0])-1][0].is_running = 0
        del alarms[int(args[0])-1]

    k = len(alarms)
    for i in range(k):
        if(alarms[k-1-i][0].is_alive() == 0):
            del alarms[k-1-i]

    if(len(args) == 0):
        for alarm in alarms:
            alarm[0].is_running = 0
        alarms.clear()

    response = ""
    for i in range(len(alarms)):
        format = '%I:%M %p'
        alTime = alarms[i][1].strftime(format)
        response += "**"+str(i+1)+".** Alarm set for "+str(alTime)+"\n"
    embedVar = discord.Embed(title="Alarms :", description=response, color=0x3498DB)
    await ctx.channel.send(embed=embedVar)


@bot.command(name='disp', help='Show all alarms')
async def display_alarms(ctx):
    k = len(alarms)
    for i in range(k):
        if(alarms[k-1-i][0].is_alive() == 0):
            del alarms[k-1-i]
    response = ""
    for i in range(len(alarms)):
        format = '%I:%M %p'
        alTime = alarms[i][1].strftime(format)
        response += "**"+str(i+1)+".** Alarm set for "+str(alTime)+"\n"
    embedVar = discord.Embed(title="Alarms :", description=response, color=0x00ff00)
    await ctx.channel.send(embed=embedVar)
    # await ctx.send(response)


@bot.command(name='al', help='Set alarm')
async def set_alarm(ctx, *args):
    k = len(alarms)
    for i in range(k):
        if(alarms[k-1-i][0].is_alive() == 0):
            del alarms[k-1-i]
    hour = -1
    minutes = -1
    after = -1
    timeConv = -1  # 0 for am , 1 for pm
    flag = 0
    toPerson = 1
    if(len(args) == 3 or len(args) == 4):
        for i in range(len(args)):
            if(i == 0):
                hour = int(args[i])
            if(i == 1):
                minutes = int(args[i])
            if(i == 2):
                if(args[i] == "a" or args[i] == "am"):
                    timeConv = 0
                elif(args[i] == "p" or args[i] == "pm"):
                    timeConv = 1
            if(i == 3):
                toPerson = int(args[i])
    elif(len(args) == 1):
        after = 1
        minutes = int(args[0])
    elif(len(args) == 2):
        after = 1
        minutes = int(args[0])
        toPerson = int(args[1])
    else:
        flag = 1

    if(toPerson == 1):
        tem_contact = to_contact
    elif(toPerson == 2):
        tem_contact = to_contact2

    if after == 1:
        # set after minutes alarm
        thread = AlarmThread(target=alarm_func, args=(60*minutes, tem_contact, ))
        now = datetime.datetime.now()
        later = now + datetime.timedelta(minutes=minutes)
        thread.start()
        alarms.append((thread, later))
        flag = 1
    elif hour == -1 or minutes == -1 or timeConv == -1:
        flag = 1
    else:
        # set @time alarm
        if(timeConv == 0):
            if hour == 12:
                hour = 0
        else:
            if hour != 12:
                hour += 12
        totMinutes = 1
        now = datetime.datetime.now()
        curhr = now.hour
        curmin = now.minute
        if(curhr < hour or (curhr == hour and curmin < minutes)):
            totMinutes = (hour-curhr)*60+minutes-curmin
        else:
            totMinutes = 24*60-((curhr-hour)*60+curmin-minutes)
        thread = AlarmThread(target=alarm_func, args=(60*totMinutes, tem_contact, ))
        now = datetime.datetime.now()
        later = now + datetime.timedelta(minutes=totMinutes)
        thread.start()
        alarms.append((thread, later))
        flag = 0

    response = "Could not set alarm"
    if flag == 0:
        response = "Alarm set for time "+str(hour)+":"+str(minutes)+" "+args[2][0:1]+"m"
    if flag == 1 and after != -1:
        response = "Timer set for " + str(minutes) + " minutes"
    embedVar = discord.Embed(description=response, color=0xE91E63)
    await ctx.channel.send(embed=embedVar)
    await display_alarms(ctx)


@bot.command(name='live', help='Shows all live matches')
async def live_matches(ctx):
    response = ""
    url = liveScoresUrl
    html = urlopen(url, context=ctx).read()
    soup = BeautifulSoup(html, "html.parser")
    response = ""
    tags = soup('item')
    i = 1
    for tag in tags:
        response += "**"+str(i)+".** "+tag.contents[1].contents[0]+"\n"
        i += 1
    embedVar = discord.Embed(title="Live Matches :", description=response, color=0x00ff00)
    await ctx.channel.send(embed=embedVar)


@bot.command(name='score', help='Shows score for the match ')
async def scorecard(ctx, *args):
    idx = 0
    if(len(args) == 1):
        idx = int(args[0])
    response = ""
    url = liveScoresUrl
    html = urlopen(url, context=ctx).read()
    soup = BeautifulSoup(html, "html.parser")
    response = "No such match"
    tags = soup('item')
    i = 1
    matchId = -1
    for tag in tags:
        if(i == idx):
            lnk = tag.contents[7].contents[0]
            lnk = lnk.split("/")
            matchId = lnk[-1].split(".")[0]
            break
        i += 1
    desc = ""
    curMatch = ""
    if(len(args) == 2):
        matchId = args[1]
    if(matchId != -1):
        curMatch = Match(matchId)
        response = curMatch.description
    colors = [0xf8c300, 0xfd0061, 0xa652bb, 0x00ff00]
    embedVar = discord.Embed(title=response, color=random.choice(colors))
    embedVar.add_field(name='Result', value=curMatch.result, inline=False)
    embedVar.add_field(name='Summary', value=curMatch.current_summary, inline=False)
    teams = []
    team1 = curMatch.team_1
    team2 = curMatch.team_2
    teams.append((team1["team_id"], team1["team_abbreviation"]))
    teams.append((team2["team_id"], team2["team_abbreviation"]))
    innings = curMatch.innings
    for inning in innings:
        for team in teams:
            if(int(team[0]) == inning["batting_team_id"]):
                title = team[1]+" ("+str(inning["innings_numth"])+" innings)"
                if(inning["live_current"] == 1):
                    title += " : current"
                val = "> Runs: "+str(inning["runs"])+"\n> Wickets: "+str(inning["wickets"])+"\n> Overs: "+str(inning["overs"])
                embedVar.add_field(name=title, value=val, inline=True)
                break

    batScoreCard = curMatch.latest_batting
    batSc = ""
    for batsmen in batScoreCard:
        batSc += "> " + batsmen["known_as"]
        if(batsmen["notout"] == 1):
            batSc += "*"
        batSc += " : "
        batSc += str(batsmen["runs"])+"("+str(batsmen["balls_faced"])+")\n"
    embedVar.add_field(name='Batting Scorecard [N R(B)]', value=batSc, inline=False)
    bowlScoreCard = curMatch.latest_bowling
    bowlSc = ""
    for bowler in bowlScoreCard:
        bowlSc += "> " + bowler["known_as"]
        bowlSc += " : "
        bowlSc += str(bowler["conceded"])+" runs, "+str(bowler["overs"])+" overs, "+str(bowler["wickets"])+" wickets\n"
    embedVar.add_field(name='Bowling Scorecard [N R O W]', value=bowlSc, inline=False)
    await ctx.channel.send(embed=embedVar)


@bot.command(name='com', help='Shows commentary (last over) for the match ')
async def commentary(ctx, *args):
    idx = 0
    overNum = 0
    if(len(args) >= 1):
        idx = int(args[0])
    if(len(args) == 2):
        overNum = int(args[1])
    response = ""
    url = liveScoresUrl
    html = urlopen(url, context=ctx).read()
    soup = BeautifulSoup(html, "html.parser")
    response = "No such match"
    tags = soup('item')
    i = 1
    matchId = -1
    for tag in tags:
        if(i == idx):
            lnk = tag.contents[7].contents[0]
            lnk = lnk.split("/")
            matchId = lnk[-1].split(".")[0]
            break
        i += 1
    desc = ""
    curMatch = ""
    if(len(args) == 2):
        matchId = args[1]
    if(matchId != -1):
        curMatch = Match(matchId)
        response = curMatch.description
    colors = [0xf8c300, 0xfd0061, 0xa652bb, 0x00ff00]
    if(overNum >= len(curMatch.json['comms'])):
        overNum = 0
        desc = "**Commentary not available for specified over ! Instead showing latest over ...**"
    lastOver = curMatch.json['comms'][overNum]["ball"]
    embedVar = discord.Embed(title=response, description=desc, color=random.choice(colors))
    for ball in lastOver:
        if("overs_actual" in ball):
            title = ball["overs_actual"]+" ( "+ball["players"]+" )"
            val = "> **"+ball["event"]+"**\n"
            if(ball["dismissal"] != ""):
                val += "> Dismissal: "+ball["dismissal"]+"\n"
            if(("pre_text" in ball) and ball["pre_text"] != ""):
                actualText = BeautifulSoup(ball["pre_text"], "lxml").text
                val += "> **"+actualText.replace('\n', ' ')+"**\n"
            if(ball["text"] != ""):
                actualText = BeautifulSoup(ball["text"], "lxml").text
                val += "> "+actualText.replace('\n', ' ')+"\n"
            if(("post_text" in ball) and ball["post_text"] != ""):
                actualText = BeautifulSoup(ball["post_text"], "lxml").text
                val += "> **"+actualText.replace('\n', ' ')+"**\n"
            if(len(val) > 1018):
                val = val[:1018]+"...**"
            embedVar.add_field(name=title, value=val, inline=False)
    await ctx.channel.send(embed=embedVar)


@bot.command(name='wm', help='Watch a match')
async def watch(ctx, *args):
    idx = 0
    overNum = -1
    milestone = 'w'  # default
    if(len(args) >= 1):  # wickets  (wm matchnum w)
        idx = int(args[0])
    if(len(args) == 3):  # overs
        if(args[1] == 'o'):
            overNum = int(args[2])
            milestone = 'o'
    response = ""
    url = liveScoresUrl
    html = urlopen(url, context=ctx).read()
    soup = BeautifulSoup(html, "html.parser")
    response = "No such match"
    tags = soup('item')
    i = 1
    matchId = -1
    for tag in tags:
        if(i == idx):
            lnk = tag.contents[7].contents[0]
            lnk = lnk.split("/")
            matchId = lnk[-1].split(".")[0]
            break
        i += 1
    desc = ""
    curMatch = ""
    if(matchId != -1):
        curMatch = Match(matchId)
        response = curMatch.description
        desc = "Watching this match with milestone : **"+str(milestone)+"**"
        if(overNum < 1):
            milestone = 'w'
        curMatch = Match(matchId)
        innings = curMatch.latest_innings
        lastWicket = int(innings["wickets"])
        lastOver = int(innings["overs"].split(".")[0])
        if(milestone == 'o'):
            desc += " for every **"+str(overNum)+" overs**"
            watchMatchOvers[matchId] = lastOver
        else:
            watchMatchWickets[matchId] = lastWicket
        kk = Watch(ctx, idx, matchId, milestone, overNum)

    colors = [0xf8c300, 0xfd0061, 0xa652bb, 0x00ff00]
    embedVar = discord.Embed(title=response, description=desc, color=random.choice(colors))
    await ctx.channel.send(embed=embedVar)

bot.run(TOKEN)
