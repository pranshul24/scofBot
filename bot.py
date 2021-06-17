
from twilio.rest import Client
from threading import Thread
from time import sleep
import threading
from datetime import datetime
import os
import random

from discord.ext import commands, tasks
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix=';')


account_sid = os.getenv('account_sid')
auth_token = os.getenv('auth_token')
to_contact = os.getenv('to_contact')
twilio_contact = os.getenv('twilio_contact')
alarms = []
client = Client(account_sid, auth_token)


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
    await ctx.send(response)


def alarm_func(arg):
    for i in range(arg):
        sleep(1)
    call = client.calls.create(
        url='http://demo.twilio.com/docs/voice.xml',
        from_=twilio_contact,
        to=to_contact
    )
    print(call.sid)


@bot.command(name='al', help='Set alarm')
async def create_call(ctx, *args):
    hour = -1
    minutes = -1
    after = -1
    timeConv = -1  # 0 for am , 1 for pm
    flag = 0
    if(len(args) == 3):
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
    elif(len(args) == 1):
        after = 1
        minutes = int(args[0])
    else:
        flag = 1

    if after == 1:
        # set after minutes alarm
        thread = Thread(target=alarm_func, args=(60*minutes, ))
        thread.start()
        print("hi")
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
        now = datetime.now()
        curhr = now.hour
        curmin = now.minute
        if(curhr < hour or (curhr == hour and curmin < minutes)):
            totMinutes = (hour-curhr)*60+minutes-curmin
        else:
            totMinutes = 24*60-((curhr-hour)*60+curmin-minutes)
        thread = Thread(target=alarm_func, args=(60*totMinutes, ))
        thread.start()
        flag = 0

    response = "Could not set alarm"
    if flag == 0:
        response = "Alarm set for time "+str(hour)+":"+str(minutes)+" "+args[2][0:1]+"m"
    if flag == 1 and after != -1:
        response = "Alarm set for " + str(minutes) + " minutes"
    await ctx.send(response)

bot.run(TOKEN)
