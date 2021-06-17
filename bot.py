
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
client = Client(account_sid, auth_token)


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="with Alarms"))


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
    embedVar = discord.Embed(title="Result", description=response, color=0x00ff00)
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
    response = "Alarms :\n"
    for i in range(len(alarms)):
        format = '%I:%M %p'
        alTime = alarms[i][1].strftime(format)
        response += str(i+1)+". Alarm set for "+str(alTime)+"\n"
    await ctx.send(response)


@bot.command(name='disp', help='Show all alarms')
async def display_alarms(ctx):
    k = len(alarms)
    for i in range(k):
        if(alarms[k-1-i][0].is_alive() == 0):
            del alarms[k-1-i]
    response = "Alarms :\n"
    for i in range(len(alarms)):
        format = '%I:%M %p'
        alTime = alarms[i][1].strftime(format)
        response += str(i+1)+". Alarm set for "+str(alTime)+"\n"
    await ctx.send(response)


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
    await ctx.send(response)
    await display_alarms(ctx)

bot.run(TOKEN)
