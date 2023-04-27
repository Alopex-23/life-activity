import csv
import json
import re
import requests
from bs4 import BeautifulSoup
from django.contrib import messages
from requests import get
from wordcloud import WordCloud
import numpy as np
import jieba
import math
import redis
from django.contrib.auth import authenticate
import datetime
import random
from django.http import JsonResponse
from django.shortcuts import render, redirect
from life.models import UserInfo, Tasktable, ManageTable, Sporttable, Userfoodtable, Foodtable, Tracktable, \
    LifeImformation
from pymysql import Connection
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from mycelery.email.tasks import send_sms
from django.db.models import Q

# Create your views here.

@login_required
def user_index(request):
    if request.method == 'GET':
        login_user=request.user
        obj=UserInfo.objects.get(username=login_user)
        u_id=obj.id
        s='主页'
        img='https://tse4-mm.cn.bing.net/th/id/OIP-C.hx5fNXtqkGF4eIxFvI1eswHaHa?w=209&h=209&c=7&r=0&o=5&dpr=1.3&pid=1.7'
        track=Tracktable(u_id=u_id,locus=s,img=img)
        track.save()
        cnt=0
        lst=list()
        conn = Connection(
            host='localhost',
            port=3306,
            user='root',
            password='Acky16140563.'
        )
        cursor=conn.cursor()
        conn.select_db('digitallife')
        cursor.execute('select `id`,`u_id`,`locus`,`img` from track order by id desc')
        obj1 = cursor.fetchall()
        for i in obj1:
            if i[1]==u_id:
                if cnt==9:
                    break
                a={'locus':i[2],'img':i[3]}
                lst.append(a)
                cnt+=1
        today = datetime.date.today()
        start_of_week = today - datetime.timedelta(days=today.weekday())
        week_dates = [start_of_week + datetime.timedelta(days=i) for i in range(7)]
        day = str(today - week_dates[0])
        day = int(day[:1])
        formatted_dates = [d.strftime('%Y-%m-%d') for d in week_dates]
        max_water = 18000
        max_sleep = 84
        max_exercise = 17.5
        health_score(u_id, formatted_dates, day)
        cd = UserInfo.objects.get(id=u_id)
        score=cd.healthy_score
        sport, sleep, water = cd.sport, cd.sleep, cd.water
        sport_num = round(sport / max_exercise * 100, 1)
        sleep_num = round(sleep / max_sleep * 100, 1)
        water_num = round(water / max_water * 100, 1)
        conn1 = redis.StrictRedis(host="127.0.0.1", port=6379, password="", db=4)
        msg_num=conn1.llen('list'+str(u_id))
        try:
            num = random.randint(0, msg_num - 1)
            msg=conn1.lindex('list'+str(u_id),num).decode('utf-8')
        except:
            msg=''
        if msg:
            tip=request.session.get('tip_date')
            if tip and tip==str(datetime.date.today()):
                msg1=''
            else:
                msg1=msg
                request.session['tip_date'] = str(datetime.date.today())
        return render(request, 'user_index.html',locals())


def health_score(u_id,date,day):
    obj = UserInfo.objects.filter(id=u_id)
    obj2=Sporttable.objects.filter(Q(u_id=u_id),Q(sport_date=date[day])|Q(sleep_date=date[day]))
    message=list()
    m_score,sleep_score,time_score,type_score=20,20,20,20
    cnt, sport, ans1, ans2,counter,m,water = 0, 0, 0, 0,0,0,0
    obj1 = Sporttable.objects.filter(u_id=u_id, record=0)
    flag=Sporttable.objects.filter(u_id=u_id)
    obj3=LifeImformation.objects.filter(u_id=u_id)
    flag1 = LifeImformation.objects.filter(u_id=u_id,date=date[0])
    error = ['', '信息未填写完整']
    num,sleep,set = list(),list(),['']
    date1=[date[j] for j in range(day)]
    if (obj1 and flag) or obj3:
        for a in date1:
            if Sporttable.objects.filter(sport_date=a):
                counter += 1
        b = Sporttable.objects.filter(u_id=u_id, record=2)
        if b:
            for i in b:
                if not i.BIM in error:
                    m = float(i.BIM[:4])
            if m < 18.5:
                n = 18.5 - m
            elif m > 24.9:
                n = m - 24.9
            if 1 < n < 2:
                m_score -= 5
                msg = '根据您的BMI值，我们给您提出几点改进的建议：\n' \
                      '1. 饮食上要注意减少高热量、高脂肪和高糖分的食品摄入。\n' \
                      '2. 增加低热量、低脂肪和高纤维的食物摄入比例。\n' \
                      '3. 根据个人情况制定适当的运动计划，进行有氧运动锻炼，帮助消耗体内多余的脂肪，增强代谢效应。'
                message.append(msg)
            elif 2 < n < 3:
                m_score -= 10
                msg = '根据您的BMI值，我们给您提出几点改进的建议：\n' \
                      '1. 应当严格控制饮食，避免过多的高热量、高脂肪和高糖分的食品。\n' \
                      '2. 进一步增加低热量、低脂肪和高纤维的食物，例如新鲜蔬菜和水果，同时适量摄入优质蛋白质。\n' \
                      '3. 加强有氧运动锻炼，可以选择较高强度的运动方式，比如跑步、游泳等，适当增加运动时间和强度。\n'
                message.append(msg)
            elif n >= 3:
                m_score = 5
                msg = '根据您的BMI值，我们给您提出几点改进的建议：\n' \
                      '1. 对饮食进行更为严格的控制和限制，还需要减少食量和避免暴饮暴食。\n' \
                      '2. 适当加入减肥茶、酵素等可以促进代谢的健康品，但要注意剂量。\n' \
                      '3. 加强有氧运动锻炼的同时，还应该参加力量训练，帮助增强肌肉，提高基础代谢率。\n'
                message.append(msg)
        for i in obj1:
            # if i.sport_date or i.sleep_date in date:
            if i.sport_date in date:
                # if i.sleep_time:
                #     # sleep.append(diff(i.sleep_time,i.wake_up))
                #     num.append(float(i.sleep_time))
                if i.sport_time:
                    sport += i.sport_time
        for j in flag:
            if j.sport_date or j.sleep_date in date:
                if j.sleep_time and j.wake_up:
                    sleep.append(diff(j.sleep_time,j.wake_up))
                    num.append(float(j.sleep_time))
                if j.sport_type:
                    if not j.sport_type in set:
                        cnt += 1
                        set.append(j.sport_type)
                if j.sleep_condition == '一夜未眠':
                    ans1 += 1
                elif j.sleep_condition == '有做噩梦':
                    ans2 += 1

        if not num:
            pass
        if counter!=day and counter!=0:
            type_score-=5
            msg='对于无法坚持运动，可以选择尝试坚持每天进行低强度的有氧运动，例如散步、慢跑、骑自行车等，' \
                '希望您可以坚持为自己的运动打卡，我们将会继续追踪您的运动数据，为您提供有效的建议，我们将一直守护您的健康！'
            message.append(msg)
        if 0<cnt < 3:
            type_score -= 5
            msg='如果运动种类单一，会造成身体无法全身性进行运动，无法充分发挥运动对于身体健康的好处，' \
                '可以尝试一些全身性的运动，例如游泳、跳绳、椭圆机等，同时可以通过参加团队运动项目或寻找运动伙伴等方式来增加运动的多样性。'
            msg1='运动种类丰富，可以对身体多个部位充分活动，可以提高全身性的健康程度，' \
                 '平时可以多多接触未体验的运动，说不定您也会爱上它，让您的健康与幸福双收！'
            message.append(msg)
            message.append(msg1)
        elif cnt==0:
            type_score-=5
            msg='运动有利于我们的健康，我们将会追踪您的运动数据，给您提供改进和有用的建议！'
            message.append(msg)
        if ans1 > 0:
            sleep_score -= 10
            msg='最近睡眠质量不好，可以调整睡眠环境，例如保持室内通风、保持安静、控制温度等，同时可以考虑适当的放松及冥想训练，以减少焦虑、压力等负面情绪对睡眠的影响'
            message.append(msg)
        elif ans1 == 0 and ans2 > 0:
            sleep_score -= 5
            msg='最近睡眠质量较低，建议平时生活中清素饮食,蔬菜、水果都对改善睡眠质量有帮助，' \
                '保持健康的作息习惯，早睡早起、避免熬夜，尽量避免白天过多的睡眠、保证睡眠环境安静无噪音。'
            message.append(msg)
        if num:
            variance = np.var(num)
            average = round(sum(num) / len(num), 1)
            rank = [float(str(average)[:2]), float(str(average)[:2])+1]
            if variance >= (rank[1] - rank[0]) / 2:
                sleep_score -= 5
                msg='您的睡眠规律不够稳定，我们建议您制定一个规律的作息计划，' \
                    '尽量在每天相同的时间入睡和起床，保持一个稳定的作息周期，同时也可以采用类似冥想训练等方法来减少睡前的压力和负面情绪的影响。' \
                    '每天按照计划进行记录您的数据，我们也能根据您的数据进行分析，给您进一步的建议。'
                message.append(msg)
        if sport<8/(7-day):
            time_score-=5
            msg='您的每周运动时间不够哦！我们建议您逐步增加运动时间，从而逐渐提高身体的耐力和健康水平。同时也可以考虑采用 HIIT 训练等高强度间歇性训练方式，以达到更好的运动效果。'
            msg1='高强度间歇性训练（HIIT)，是一种让你在短时间内进行全力、快速、爆发式锻炼的一种训练技术。这种技术让你在短期内心率提高并且燃烧更多热量。'
            message.append(msg)
            message.append(msg1)
        if sleep:
            sleep_variance = np.var(sleep)
            average1 = round(sum(sleep) / len(sleep), 1)
            if sleep_variance>0.5:
                sleep_score-=5
                msg='我们追踪您的数据发现，您的睡眠时长不够规律，您可以制定一套作息计划以及利用我们实现睡眠的规律化，' \
                    '您也可以通过自己的工作时间以及起床时间以及我们提供的数据图表，发现自己的睡眠的舒适区间，以此来督促您的睡眠习惯！'
                message.append(msg)
            if average1<7:
                sleep_score-=5
                msg = '我们根据您的数据发现最近您的睡眠不够充足，我们建议您规律作息时间，尽量保证每晚 7-8 小时的睡眠，并避免在睡前过度兴奋活动，例如长时间使用电子设备、饮酒等。'
                message.append(msg)
            elif average1>8:
                sleep_score-=2
                msg='睡眠时间过多可能会导致身体疲劳、头痛、注意力不集中等问题，我们建议您适当减少睡眠时间，以达到身体和精神健康的平衡状态。' \
                    '具体来说，您可以试着规律自己的睡眠时间，保持每天相对固定的睡眠时间和起床时间，并尽可能保证空气流通和环境安静。' \
                    '此外，适当的运动和饮食也能够提高身体素质和睡眠质量，建议用户在日常生活中加强锻炼和均衡膳食，以提高自己的身体素质。'
                message.append(msg)
        obj1.update(record=1)
        obj4=Sporttable.objects.filter(kalcr__contains='Kcal')
        obj4.update(record=2)
        score=round(m_score*1.4+(sleep_score+time_score+type_score)*1.2,1)
        if obj3:
            n = UserInfo.objects.get(id=u_id)
            for j in obj3:
                if (j.date in date) and j.record==0:
                    if j.water:
                        water += int(j.water)
            if (n.water+water) < 10500/(7-day):
                score-=5
                msg='我们根据您的喝水记录数据，给您一些改进的建议:\n' \
                    '1. 喝足够的水是保持身体健康的重要部分。建议每天饮用至少8杯（大约2升）水，以满足人体运作所需的润滑、新陈代谢和水平衡等需要。\n' \
                    '2. 可以逐步增加每天喝水量，例如从现在开始增加每天喝一杯水，逐渐适应并逐步增加到每日8杯。\n' \
                    '3. 为了更好地补充水分，您可以将水瓶或含有水的容器随身携带，并在一天中的不同时间喝水。\n' \
                    '4. 除了水之外，还可以尝试多饮用无糖或低糖的茶、饮料、汤类食品等，来增加水分摄入。\n' \
                    '5. 注意，个体差异存在，在确定自己的每天、每周饮水量时，需要根据自身身体情况和医生的意见作出决策。'
                message.append(msg)

        obj.update(healthy_score=score,sport=n.sport+sport,sleep=sum(sleep),water=n.water+water)
        obj3.update(record=1)
        conn = redis.StrictRedis(host="127.0.0.1", port=6379, password="", db=4)
        if message:
            if conn.llen('list'+str(u_id))!=0:
                conn.delete('list'+str(u_id))
                for j in range(len(message)):
                    conn.rpush('list'+str(u_id),message[j])
                conn.expire('list'+str(u_id),604800)
            else:
                for j in range(len(message)):
                    conn.rpush('list'+str(u_id),message[j])
                conn.expire('list'+str(u_id),604800)
    elif not ( obj2 or flag) and not flag1:
        score=60
        obj.update(healthy_score=score)

def prediction(u_id):
    nowday = datetime.datetime.today()
    year, month, day = nowday.year, nowday.month, nowday.day
    weekday = datetime.date(year, month, day).strftime("%A")
    # today = datetime.date(year, month, day)
    weekd1, weekd2, weekd3, weekd4, weekd5, weekd6, weekd7 = [], [], [], [], [], [], []
    lst = []
    if month != 1:
        lastmonth = month - 1
    else:
        lastmonth = 12
    obj1 = Tasktable.objects.filter(Q(u_id=u_id), Q(date__contains=month) | Q(date__contains=lastmonth))
    for i in obj1:
        f = {'weekd': i.weekd, 'event': i.content}
        lst.append(f)
    for j in lst:
        if j['weekd'] == '1':
            weekd1.append(j)
        elif j['weekd'] == '2':
            weekd2.append(j)
        elif j['weekd'] == '3':
            weekd3.append(j)
        elif j['weekd'] == '4':
            weekd4.append(j)
        elif j['weekd'] == '5':
            weekd5.append(j)
        elif j['weekd'] == '6':
            weekd6.append(j)
        else:
            weekd7.append(j)
    p = change(weekd1, weekd2, weekd3, weekd4, weekd5, weekd6, weekd7, weekday)
    result = []
    for i in range(5):
        a = lottery(p)
        if a in result:
            continue
        else:
            result.append(a)
    if result[0] == None:
        result = result[0]
    return result


@login_required
def plan(request):
    if request.method=='GET':
        login_user = request.user
        obj = UserInfo.objects.get(username=login_user)
        u_id = obj.id
        s = '日程计划'
        img='data:image/jpeg;base64,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'
        track = Tracktable(u_id=u_id, locus=s,img=img)
        track.save()
        result=prediction(u_id)
        return render(request,'plan.html',locals())
    if request.method=='POST':
        login_user=request.user
        obj = UserInfo.objects.get(username=login_user)
        u_id=obj.id
        date=request.POST.get('date')
        weekd=request.POST.get('weekd')
        event=request.POST.get('event')
        duration=request.POST.get('duration')
        task_type=request.POST.get('task_type')
        obj1=Tasktable(u_id=u_id,date=date,weekd=weekd,duration=duration,task_type=task_type,content=event)
        obj1.save()
        result=prediction(u_id)
        return render(request,'plan.html',locals())

def calcu(weekd):
        a = []
        for i in weekd:
            a.append(i['event'])
        return a

def change(weekd1, weekd2, weekd3, weekd4, weekd5, weekd6, weekd7,weekday):
    thingsdic = {}
    if weekday == "Monday":
        things = calcu(weekd1)
        all = len(weekd1)
    elif weekday == "Tuesday":
        things = calcu(weekd2)
        all = len(weekd2)
    elif weekday == "Wednesday":
        things = calcu(weekd3)
        all = len(weekd3)
    elif weekday == "Thursday":
        things = calcu(weekd4)
        all = len(weekd4)
    elif weekday == "Friday":
        things = calcu(weekd5)
        all = len(weekd5)
    elif weekday == "Saturday":
        things = calcu(weekd6)
        all = len(weekd6)
    else:
        things = calcu(weekd7)
        all = len(weekd7)
    for n in things:
        if n in thingsdic:
            thingsdic[n] += 1
        else:
            thingsdic[n] = 1

    thingsgroup = []
    for x, y in thingsdic.items():
        thingsgroup.append((x, y / all))
    return thingsgroup

def lottery(thgroup):
    rand = random.random()
    for th in thgroup:
        if rand < th[1]:
            return th[0]
        else:
            rand -= th[1]
    return None


@login_required
def communcation(request):
    if request.method=='GET':
        login_user = request.user
        obj = UserInfo.objects.get(username=login_user)
        u_id = obj.id
        s = '人际交往'
        img='data:image/jpeg;base64,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'
        track = Tracktable(u_id=u_id, locus=s,img=img)
        track.save()
    return render(request, 'comm.html')


@login_required
def manage(request):
    nowday = datetime.datetime.today()
    year, month, day = nowday.year, nowday.month, nowday.day
    today = datetime.date(year, month, day)
    one_day = datetime.timedelta(days=1)
    two_day = datetime.timedelta(days=2)
    three_day = datetime.timedelta(days=3)
    if request.method == 'GET':
        login_user = request.user
        obj = UserInfo.objects.get(username=login_user)
        u_id = obj.id
        a=manage_echarts(u_id,True,today,one_day,two_day,three_day)
        b=manage_echarts(u_id,False,today,one_day,two_day,three_day)
        gain,pay=a[0],a[1]
        am,pm,din=b[0],b[1],b[2]
        s = '金钱管理'
        img='https://tse4-mm.cn.bing.net/th/id/OIP-C.F-d5ZmH-s_2VGrF-gSizqwAAAA?w=168&h=185&c=7&r=0&o=5&dpr=1.3&pid=1.7'
        track = Tracktable(u_id=u_id, locus=s,img=img)
        track.save()
        date = {'one': (today - three_day - three_day).strftime('%Y-%m-%d'),
                'two': (today - two_day - three_day).strftime('%Y-%m-%d'),
                'three': (today - one_day - three_day).strftime('%Y-%m-%d'),
                'four': (today - three_day).strftime('%Y-%m-%d'), 'five': (today - two_day).strftime('%Y-%m-%d'),
                'six': (today - one_day).strftime('%Y-%m-%d'), 'seven': (today).strftime('%Y-%m-%d')}
        # date=json.dumps(date)
        return render(request, 'money.html',locals())
    if request.method == 'POST':
        login_user = request.user
        obj = UserInfo.objects.get(username=login_user)
        u_id=obj.id
        if 'money' in request.POST:
            optionsRadios = request.POST.get('optionsRadios')
            money = request.POST.get('money')
            source = request.POST.get('source')
            spend = request.POST.get('spend')
            obj1=ManageTable(u_id=u_id,type=optionsRadios,money=money,source=source,pay=spend,date=today)
            obj1.save()
        if 'dinner' in request.POST:
            breakfast = request.POST.get('breakfast')
            lunch = request.POST.get('lunch')
            dinner = request.POST.get('dinner')
            obj2=ManageTable(u_id=u_id,am_money=breakfast,pm_money=lunch,dinner_money=dinner,date=today)
            obj2.save()
        a = manage_echarts(u_id, True, today, one_day, two_day, three_day)
        b = manage_echarts(u_id, False, today, one_day, two_day, three_day)
        gain, pay = a[0], a[1]
        am, pm, din = b[0], b[1], b[2]
        return render(request, 'money.html',locals())


def manage_echarts(u_id,flag,today,one_day,two_day,three_day):
    obj = ManageTable.objects.filter(u_id=u_id)
    if flag==True:
        lst=list()
        gain={'a':0,'b':0,'c':0,'d':0,'e':0,'f':0,'g':0}
        pay={'a':0,'b':0,'c':0,'d':0,'e':0,'f':0,'g':0}
        for i in obj:
            if i.type=='收入':
                if i.date == (today - three_day-three_day).strftime('%Y-%m-%d'):
                    gain['a'] += int(i.money)
                elif i.date == (today - two_day-three_day).strftime('%Y-%m-%d'):
                    gain['b'] += int(i.money)
                elif i.date == (today - one_day-three_day).strftime('%Y-%m-%d'):
                    gain['c'] += int(i.money)
                elif i.date == (today-three_day).strftime('%Y-%m-%d'):
                    gain['d'] += int(i.money)
                elif i.date == (today - two_day).strftime('%Y-%m-%d'):
                    gain['e'] += int(i.money)
                elif i.date == (today - one_day).strftime('%Y-%m-%d'):
                    gain['f'] += int(i.money)
                elif i.date == (today).strftime('%Y-%m-%d'):
                    gain['g'] += int(i.money)
            elif i.type=='支出':
                if i.date == (today - three_day-three_day).strftime('%Y-%m-%d'):
                    pay['a'] += int(i.money)
                elif i.date == (today - two_day-three_day).strftime('%Y-%m-%d'):
                    pay['b'] += int(i.money)
                elif i.date == (today - one_day-three_day).strftime('%Y-%m-%d'):
                    pay['c'] += int(i.money)
                elif i.date == (today-three_day).strftime('%Y-%m-%d'):
                    pay['d'] += int(i.money)
                elif i.date == (today - two_day).strftime('%Y-%m-%d'):
                    pay['e'] += int(i.money)
                elif i.date == (today - one_day).strftime('%Y-%m-%d'):
                    pay['f'] += int(i.money)
                elif i.date == (today).strftime('%Y-%m-%d'):
                    pay['g'] += int(i.money)
        lst.append(gain),lst.append(pay)
        return lst
    if flag==False:
        lst=list()
        am = {'a': 0, 'b': 0, 'c': 0, 'd': 0, 'e': 0, 'f': 0, 'g': 0}
        pm = {'a': 0, 'b': 0, 'c': 0, 'd': 0, 'e': 0, 'f': 0, 'g': 0}
        din = {'a': 0, 'b': 0, 'c': 0, 'd': 0, 'e': 0, 'f': 0, 'g': 0}
        for i in obj:
            if i.am_money:
                if i.date == (today - three_day-three_day).strftime('%Y-%m-%d'):
                    am['a'] += float(i.am_money)
                elif i.date == (today - two_day-three_day).strftime('%Y-%m-%d'):
                    am['b'] += float(i.am_money)
                elif i.date == (today - three_day-one_day).strftime('%Y-%m-%d'):
                    am['c'] += float(i.am_money)
                elif i.date == (today-three_day).strftime('%Y-%m-%d'):
                    am['d'] += float(i.am_money)
                elif i.date == (today - two_day).strftime('%Y-%m-%d'):
                    am['e'] += float(i.am_money)
                elif i.date == (today - one_day).strftime('%Y-%m-%d'):
                    am['f'] += float(i.am_money)
                elif i.date == (today).strftime('%Y-%m-%d'):
                    am['g'] += float(i.am_money)
            if i.pm_money:
                if i.date == (today - three_day-three_day).strftime('%Y-%m-%d'):
                    pm['a'] += float(i.pm_money)
                elif i.date == (today - two_day-three_day).strftime('%Y-%m-%d'):
                    pm['b'] += float(i.pm_money)
                elif i.date == (today - one_day-three_day).strftime('%Y-%m-%d'):
                    pm['c'] += float(i.pm_money)
                elif i.date == (today-three_day).strftime('%Y-%m-%d'):
                    pm['d'] += float(i.pm_money)
                elif i.date == (today - two_day).strftime('%Y-%m-%d'):
                    pm['e'] += float(i.pm_money)
                elif i.date == (today - one_day).strftime('%Y-%m-%d'):
                    pm['f'] += float(i.pm_money)
                elif i.date == (today).strftime('%Y-%m-%d'):
                    pm['g'] += float(i.pm_money)
            if i.dinner_money:
                if i.date == (today - three_day-three_day).strftime('%Y-%m-%d'):
                    din['a'] += float(i.dinner_money)
                elif i.date == (today - two_day-three_day).strftime('%Y-%m-%d'):
                    din['b'] += float(i.dinner_money)
                elif i.date == (today - one_day-three_day).strftime('%Y-%m-%d'):
                    din['c'] += float(i.dinner_money)
                elif i.date == (today-three_day).strftime('%Y-%m-%d'):
                    din['d'] += float(i.dinner_money)
                elif i.date == (today - two_day).strftime('%Y-%m-%d'):
                    din['e'] += float(i.dinner_money)
                elif i.date == (today - one_day).strftime('%Y-%m-%d'):
                    din['f'] += float(i.dinner_money)
                elif i.date == (today).strftime('%Y-%m-%d'):
                    din['g'] += float(i.dinner_money)
        lst.append(am),lst.append(pm),lst.append(din)
        return lst


@login_required
def healthy(request):
    global weight, height, age, BMR, type1,heat, BMI,cnt
    cnt=0
    nowday = datetime.datetime.today()
    year, month, day = nowday.year, nowday.month, nowday.day
    today = datetime.date(year, month, day)
    one_day = datetime.timedelta(days=1)
    two_day = datetime.timedelta(days=2)
    three_day = datetime.timedelta(days=3)
    if request.method == 'GET':
        login_user = request.user
        obj = UserInfo.objects.get(username=login_user)
        u_id = obj.id
        sport=healthy_echarts(u_id,True,today,one_day,two_day,three_day)
        sleep=healthy_echarts(u_id,False,today,one_day,two_day,three_day)
        s = '健康生活'
        img='https://tse3-mm.cn.bing.net/th/id/OIP-C.CJfWsz6JVlmBsPPcs4nU1QHaF9?w=253&h=203&c=7&r=0&o=5&dpr=1.3&pid=1.7'
        track = Tracktable(u_id=u_id, locus=s,img=img)
        track.save()
        obj1=Sporttable.objects.filter(u_id=u_id)
        error=['','信息未填写完整(Kcal)','信息未填写完整(千卡/天)','信息未填写完整']
        for i in obj1:
            if not (i.kalcr and i.BMR and i.BIM) in error:
                h=i.kalcr
                r=i.BMR
                m=i.BIM
        return render(request, 'healthy.html',locals())
    if request.method == 'POST':
        sex,heat='',''
        flag=0
        login_user = request.user
        obj = UserInfo.objects.get(username=login_user)
        u_id=obj.id
        if 'sport_type' in request.POST:
            try:
                sport_type = request.POST.get('sport_type')
                sport_time = request.POST.get('sport_time')
                sport_time=float(sport_time)
                sport_date = request.POST.get('sport_date')
            except:
                msg = '未填写数据'
                return render(request,'healthy.html',locals())
            try:
                datetime.datetime.strptime(sport_date, '%Y-%m-%d')
                flag=1
            except:
                flag=0
            if sport_type and sport_time and sport_date and flag == 1:
                obj1 = Sporttable(u_id=u_id, sport_type=sport_type, sport_time=sport_time, sport_date=sport_date)
                obj1.save()
                cnt += 1
            elif flag == 0:
                msg = '填写格式错误，请正确填写数据格式！！！'
        elif 'sleep_time' in request.POST:
            flag=0
            try:
                sleep_conditions = request.POST.get('sleep_conditions')
                sleep_time = request.POST.get('sleep_time')
                wakeup = request.POST.get('wakeup')
                a,b=int(sleep_time[:2]),int(sleep_time[3:])
                sleep_time=a+b/60.0
                a1,b1=int(wakeup[:2]),int(wakeup[3:])
                wakeup=a1+b1/60.0
                sleep_date = request.POST.get('sleep_date')
            except:
                msg1 = '未填写数据'
                return render(request,'healthy.html',locals())
            try:
                datetime.datetime.strptime(sleep_date, '%Y-%m-%d')
                flag=1
            except:
                flag=0
            if sleep_conditions and sleep_time and wakeup and sleep_date and flag==1:
                obj2 = Sporttable(u_id=u_id, sleep_condition=sleep_conditions, sleep_time=sleep_time, wake_up=wakeup,
                                  sleep_date=sleep_date)
                obj2.save()
                cnt += 1
            elif flag==0:
                msg1 = '填写数据格式错误，请正确填写数据格式！！！'
        elif 'type' in request.POST:
            sex = request.POST.get('sex')
            age = request.POST.get('age')
            height = request.POST.get('height')
            weight = request.POST.get('weight')
            type1 = request.POST.get('type')
        elif 'age1' in request.POST:
            sex = request.POST.get('sex')
            age = request.POST.get('age1')
            height = request.POST.get('height')
            weight = request.POST.get('weight')
        elif 'age2' in request.POST:
            sex = request.POST.get('sex')
            age = request.POST.get('age2')
            height = request.POST.get('height')
            weight = request.POST.get('weight')
        if sex and age and height and weight:
            BMI = round(int(weight) / (int(height)*int(height)/10000),1)
            if sex == '女':
                BMR = 655 + (9.6 * int(weight)) + (1.8 * int(height)) - (4.7 * int(age))
            if sex == '男':
                BMR = 66 + (13.7 * int(weight)) + (5 * int(height)) - (6.8 * int(age))
            if type1:
                if type1 == '久坐':
                    heat = round(BMR * 1.2,2)
                elif type1 == '稍微运动(每周1-3次运动)':
                    heat = round(BMR * 1.375,2)
                elif type1 == '中度运动(每周3-5次运动)':
                    heat = round(BMR * 1.55,2)
                elif type1 == '积极运动(每周6-7次运动)':
                    heat = round(BMR * 1.725,2)
                elif type1 == '专业运动(2倍运动量)':
                    heat = round(BMR * 1.9,2)
        elif heat == '' or BMR == '' or BMI == '':
            heat = '信息未填写完整'
            BMR = '信息未填写完整'
            BMI = '信息未填写完整'
        else:
            heat = ''
            BMR = ''
            BMI = ''
        if BMI!='' and BMI!='信息未填写完整':
            BMI=float(BMI)
            if BMI<18.5:
                m=str(BMI)+'(体重过轻)'
            elif 18.5 <= BMI <= 23.9:
                m=str(BMI)+'(体重健康)'
            elif 24 <= BMI <= 27.9:
                m=str(BMI)+'(体重超重)'
            elif 28 <= BMI <= 32:
                m=str(BMI)+'(体重肥胖)'
            elif BMI>32:
                m=str(BMI)+'(非常肥胖)'
        else:
            m=BMI
        r=str(BMR)+'(千卡/天)'
        h=str(heat)+'(Kcal)'
        if cnt==0:
            obj3=Sporttable(u_id=u_id,kalcr=h,BMR=r,BIM=m)
            obj3.save()
        sport = healthy_echarts(u_id, True, today, one_day, two_day, three_day)
        sleep = healthy_echarts(u_id, False, today, one_day, two_day, three_day)
        obj0 = Sporttable.objects.filter(u_id=u_id)
        error = ['', '信息未填写完整(Kcal)', '信息未填写完整(千卡/天)', '信息未填写完整']
        for i in obj0:
            if not (i.kalcr and i.BMR and i.BIM) in error:
                h = i.kalcr
                r = i.BMR
                m = i.BIM
        return render(request,'healthy.html',locals())


def diff(sleep_time,now_time):
    if float(sleep_time)%1!=0:
        decimal_part1, integer_part1 = math.modf(float(sleep_time))
        decimal_part1 = round(decimal_part1, 2)
    else:
        integer_part1 = float(sleep_time)
        decimal_part1 = 0
    if float(now_time)%1!=0:
        decimal_part2, integer_part2 = math.modf(float(now_time))
        decimal_part2 = round(decimal_part2, 2)
    else:
        integer_part2 = float(now_time)
        decimal_part2 = 0
    if integer_part1>integer_part2:
        a = datetime.datetime.now() - datetime.timedelta(days=1)
        a = a.replace(hour=int(integer_part1), minute=int(decimal_part1*60), second=0, microsecond=0)
        b = datetime.datetime.now().replace(hour=int(integer_part2), minute=int(decimal_part2*60), second=0, microsecond=0)
        duration_sec = (a - b).total_seconds()
        duration_hour = abs(duration_sec / 3600)
        duration_hour=round(duration_hour,2)
        return duration_hour
    elif integer_part1<integer_part2:
        a=datetime.datetime.now()
        a = a.replace(hour=int(integer_part1), minute=int(decimal_part1 * 60), second=0, microsecond=0)
        b = datetime.datetime.now().replace(hour=int(integer_part2), minute=int(decimal_part2 * 60), second=0,
                                            microsecond=0)
        duration_sec = (a - b).total_seconds()
        duration_hour = abs(duration_sec / 3600)
        duration_hour = round(duration_hour, 2)
        return duration_hour


def healthy_echarts(u_id,flag,today,one_day,two_day,three_day):
    global sleep
    obj=Sporttable.objects.filter(u_id=u_id)
    if flag==True:
        spo_type={'a':0,'b':0,'c':0,'d':0,'e':0,'f':0,'g':0,'h':0,'i':0,'j':0,'k':0,'l':0,'m':0,'n':0,'o':0}
        for i in obj:
            if i.sport_type=='步行':
                spo_type['a']+=float(i.sport_time)
            elif i.sport_type=='户外跑步':
                spo_type['b']+=float(i.sport_time)
            elif i.sport_type=='室内跑步':
                spo_type['c']+=float(i.sport_time)
            elif i.sport_type=='瑜伽':
                spo_type['d']+=float(i.sport_time)
            elif i.sport_type=='健身':
                spo_type['e']+=float(i.sport_time)
            elif i.sport_type=='骑行':
                spo_type['f']+=float(i.sport_time)
            elif i.sport_type=='高尔夫':
                spo_type['g']+=float(i.sport_time)
            elif i.sport_type=='跳绳':
                spo_type['h']+=float(i.sport_time)
            elif i.sport_type=='篮球':
                spo_type['i']+=float(i.sport_time)
            elif i.sport_type=='羽毛球':
                spo_type['j']+=float(i.sport_time)
            elif i.sport_type=='乒乓球':
                spo_type['k']+=float(i.sport_time)
            elif i.sport_type=='健美操':
                spo_type['l']+=float(i.sport_time)
            elif i.sport_type=='网球':
                spo_type['m']+=float(i.sport_time)
            elif i.sport_type=='足球':
                spo_type['n']+=float(i.sport_time)
            elif i.sport_type=='其他':
                spo_type['o']+=float(i.sport_time)
        return spo_type
    if flag==False:
        sl_time={'a':0,'b':0,'c':0,'d':0,'e':0,'f':0,'g':0}
        for i in obj:
            if i.sleep_time and i.wake_up:
                sleep = diff(i.sleep_time, i.wake_up)
            elif i.sleep_time=='' or i.wake_up=='':
                sleep=0
            if i.sleep_date==(today-three_day-three_day-one_day).strftime('%Y-%m-%d'):
                sl_time['a']=sleep
            elif i.sleep_date==(today-three_day-three_day).strftime('%Y-%m-%d'):
                sl_time['b']=sleep
            elif i.sleep_date==(today-two_day-three_day).strftime('%Y-%m-%d'):
                sl_time['c']=sleep
            elif i.sleep_date==(today-three_day-one_day).strftime('%Y-%m-%d'):
                sl_time['d']=sleep
            elif i.sleep_date==(today-three_day).strftime('%Y-%m-%d'):
                sl_time['e']=sleep
            elif i.sleep_date==(today-two_day).strftime('%Y-%m-%d'):
                sl_time['f']=sleep
            elif i.sleep_date==(today-one_day).strftime('%Y-%m-%d'):
                sl_time['g']=sleep
        return sl_time



@login_required
def clothes(request):
    # x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    # if x_forwarded_for:
    #     ip = x_forwarded_for.split(',')[-1].strip()
    # else:
    #     ip = request.META.get('REMOTE_ADDR')
    # print(ip)
    url = 'http://txt.go.sohu.com/ip/soip'
    response = requests.get(url)
    text = response.text
    ip = re.findall(r'\d+.\d+.\d+.\d+', text)[0]
    print("默认访客ip：%s" % ip)
    r=requests.get('http://whois.pconline.com.cn/ipJson.jsp?ip=%s&json=true'%ip).text
    json1=json.loads(r)
    city = json1["city"][:2]
    if request.method=='GET':
        login_user = request.user
        obj = UserInfo.objects.get(username=login_user)
        u_id = obj.id
        s = '穿衣推荐'
        img='https://tse1-mm.cn.bing.net/th/id/OIP-C.hHts10Q9vuZHnq3Nu7cfUwHaHa?w=194&h=194&c=7&r=0&o=5&dpr=1.3&pid=1.7'
        track = Tracktable(u_id=u_id, locus=s,img=img)
        track.save()
        locationid = getID(city, "08c6e2b97a774cb587a7caa11cc5da17")
        url1 = f'http://www.weather.com.cn/weather/{locationid}.shtml'
        try:
            r1=requests.get(url1,timeout=30)
            r1.raise_for_status()
            r1.encoding=r1.apparent_encoding
            data1, data1_7 = get_content(r1.text)
            s='/home/dreamcreator/djdemo/user_csv/weather'+str(u_id)+'.csv'
            write_to_csv(s, data1)
        except:
            r1=''
    return render(request, 'clothes.html')

def getID(address,key):
    """获取locationid"""
    url = f'https://geoapi.qweather.com/v2/city/lookup?location={address}&key={key}'
    datas = requests.get(url).json()
    # print(data)
    # print(type(datas))
    for data in datas['location']:
       if data['name'] == address:
           ID = data['id']
           return ID


def get_content(html):
    final = []  # 初始化一个列表保存数据
    bs = BeautifulSoup(html, "html.parser")  # 创建BeautifulSoup对象
    body = bs.body
    data = body.find('div', {'id': '7d'})  # 找到div标签且id = 7d
    # 下面爬取当天的数据
    data2 = body.find_all('div', {'class': 'left-div'})
    text = data2[2].find('script').string
    text = text[text.index('=') + 1:-2]  # 移除改var data=将其变为json数据
    jd = json.loads(text)
    dayone = jd['od']['od2']  # 找到当天的数据
    final_day = []  # 存放当天的数据
    count = 0
    for i in dayone:
        temp = []
        if count <= 23:
            temp.append(i['od21'])  # 添加时间
            temp.append(i['od22'])  # 添加当前时刻温度
            temp.append(i['od24'])  # 添加当前时刻风力方向
            temp.append(i['od25'])  # 添加当前时刻风级
            temp.append(i['od26'])  # 添加当前时刻降水量
            temp.append(i['od27'])  # 添加当前时刻相对湿度
            temp.append(i['od28'])  # 添加当前时刻控制质量
            # print(temp)
            final_day.append(temp)
        count = count + 1
        # 下面爬取7天的数据
    ul = data.find('ul')  # 找到所有的ul标签
    li = ul.find_all('li')  # 找到左右的li标签
    i = 0  # 控制爬取的天数
    for day in li:  # 遍历找到的每一个li
        if i < 7 and i > 0:
            temp = []  # 临时存放每天的数据
            date = day.find('h1').string  # 得到日期
            date = date[0:date.index('日')]  # 取出日期号
            temp.append(date)
            inf = day.find_all('p')  # 找出li下面的p标签,提取第一个p标签的值，即天气
            temp.append(inf[0].string)

            tem_low = inf[1].find('i').string  # 找到最低气温

            if inf[1].find('span') is None:  # 天气预报可能没有最高气温
                tem_high = None
            else:
                tem_high = inf[1].find('span').string  # 找到最高气温
            temp.append(tem_low[:-1])
            if tem_high[-1] == '℃':
                temp.append(tem_high[:-1])
            else:
                temp.append(tem_high)

            wind = inf[2].find_all('span')  # 找到风向
            for j in wind:
                temp.append(j['title'])

            wind_scale = inf[2].find('i').string  # 找到风级
            index1 = wind_scale.index('级')
            temp.append(int(wind_scale[index1 - 1:index1]))
            final.append(temp)
        i = i + 1
    return final_day, final

def write_to_csv(file_name, data):
    with open(file_name, 'a', errors='ignore', newline='') as f:
        header = ['小时', '温度', '风力方向', '风级', '降水量', '相对湿度', '空气质量']
        f_csv = csv.writer(f)
        f_csv.writerow(header)
        f_csv.writerows(data)

@login_required
def eat(request):
    nowday = datetime.datetime.today()
    year, month, day = nowday.year, nowday.month, nowday.day
    today = datetime.date(year, month, day)
    one_day = datetime.timedelta(days=1)
    two_day = datetime.timedelta(days=2)
    three_day = datetime.timedelta(days=3)
    if request.method=='GET':
        login_user = request.user
        obj = UserInfo.objects.get(username=login_user)
        u_id = obj.id
        value=eat_charts(u_id,False,today,one_day,two_day,three_day)
        result=eat_charts(u_id,True,today,one_day,two_day,three_day)
        s = '饮食推荐'
        img='https://tse3-mm.cn.bing.net/th/id/OIP-C.BOFw2FzpbDVXHrFvXlBVmAHaHa?w=218&h=219&c=7&r=0&o=5&dpr=1.3&pid=1.7'
        track = Tracktable(u_id=u_id, locus=s,img=img)
        track.save()
        lst=list()
        find(lst)
        Item = ItemBasedCF(lst)
        Item.ItemSimilarity()
        u_id = str(u_id)
        recommedDic1 = Item.Recommend(u_id) # 计算给用户A的推荐列表
        recommedDic=list()
        if recommedDic1:
            for k in recommedDic1:
                obj1=Foodtable.objects.filter(food__exact=k)
                for i in obj1:
                    a={'food':i.food,'img':i.img}
                    recommedDic.append(a)
        if not recommedDic1:
            obj1 = Foodtable.objects.filter(id__lte=6)
            for i in obj1:
                a = {'food': i.food, 'img': i.img}
                recommedDic.append(a)
        return render(request,'eat.html', locals())
    if request.method=='POST':
        nowday = datetime.datetime.today()
        year, month, day = nowday.year, nowday.month, nowday.day
        today = datetime.date(year, month, day)
        login_user = request.user
        obj = UserInfo.objects.get(username=login_user)
        u_id = obj.id
        if 'am' in request.POST:
            breakfast=request.POST.get('breakfast')
            am=request.POST.get('am')
            lunch=request.POST.get('lunch')
            pm=request.POST.get('pm')
            dinner=request.POST.get('dinner')
            supper=request.POST.get('supper')
            op1=int(request.POST.get('op1'))
            op2=int(request.POST.get('op2'))
            op3=int(request.POST.get('op3'))
            op4 = int(request.POST.get('op4'))
            op5 = int(request.POST.get('op5'))
            op6 = int(request.POST.get('op6'))
            obj1=LifeImformation(u_id=u_id,breakfast=breakfast,am_tea=am,pm_tea=pm,lunch=lunch,dinner=dinner,supper=supper,date=today)

            obj1.save()
        if 'type' in request.POST:
            optionsRadios=request.POST.get('optionsRadios')
            type=request.POST.get('type')
            num=request.POST.get('num')
            size=request.POST.get('size')
            if optionsRadios=='600~800ml':
                optionsRadios='700'
            elif optionsRadios=='800~1000ml':
                optionsRadios='900'
            elif optionsRadios=='1000~1200ml':
                optionsRadios='1100'
            elif optionsRadios=='1200~1400ml':
                optionsRadios='1300'
            elif optionsRadios=='1400~1600ml':
                optionsRadios='1500'
            elif optionsRadios=='1600~1800ml':
                optionsRadios='1700'
            elif optionsRadios=='1800~2000ml':
                optionsRadios='1900'
            obj1=LifeImformation(u_id=u_id,water=optionsRadios,drink=type,num=num,size=size,date=today)
            obj1.save()
            value = eat_charts(u_id, False, today, one_day, two_day, three_day)
            result = eat_charts(u_id, True, today, one_day, two_day, three_day)
        return render(request,'eat.html',locals())


def eat_charts(u_id,flag,today,one_day,two_day,three_day):
    obj = LifeImformation.objects.filter(u_id=u_id)
    if flag==False:
        value = {'breakfast':0,'lunch':0,'dinner':0,'am':0,'pm':0,'supper':0}
        if obj:
            for i in obj:
                if i.breakfast:
                    value['breakfast']+=1
                if i.lunch:
                    value['lunch']+=1
                if i.dinner:
                    value['dinner']+=1
                if i.am_tea:
                    value['am']+=1
                if i.pm_tea:
                    value['pm']+=1
                if i.supper:
                    value['supper']+=1
        return value
    else:
        data={'one':0,'two':0,'three':0,'four':0,'five':0,'six':0,'seven':0}
        for i in obj:
            if i.water:
                if i.date==(today-three_day-three_day).strftime('%Y-%m-%d'):
                    data['one']+=int(i.water)
                elif i.date==(today-two_day-three_day).strftime('%Y-%m-%d'):
                    data['two']+=int(i.water)
                elif i.date==(today-one_day-three_day).strftime('%Y-%m-%d'):
                    data['three']+=int(i.water)
                elif i.date==(today-three_day).strftime('%Y-%m-%d'):
                    data['four']+=int(i.water)
                elif i.date==(today-two_day).strftime('%Y-%m-%d'):
                    data['five']+=int(i.water)
                elif i.date==(today-one_day).strftime('%Y-%m-%d'):
                    data['six']+=int(i.water)
                elif i.date==(today).strftime('%Y-%m-%d'):
                    data['seven']+=int(i.water)
        return data


@login_required
def talk(request):
    login_user = request.user
    obj = UserInfo.objects.get(username=login_user)
    u_id = obj.id
    if request.method=='GET':
        s = '自我对话'
        img='https://tse3-mm.cn.bing.net/th/id/OIP-C.g0F4g62Ib8W1l2HXnx3xGgHaHa?w=203&h=203&c=7&r=0&o=5&dpr=1.3&pid=1.7'
        track = Tracktable(u_id=u_id, locus=s,img=img)
        track.save()
        f=Tracktable.objects.filter(u_id=u_id)
        file=''
        for i in f:
            if i.daily:
                file+=i.daily
        # with open('/home/dreamcreator/djdemo/life/dayact.txt', 'r', encoding="UTF-8") as f:
        #     # 将文本读取为整个字符串，readlines可以按行读取
        #     file = f.read()
        if file:
            data_cut = jieba.cut(file, cut_all=False)
            img1=cloud(data_cut,u_id)
        else:
            msg='请您将你的生活记录下来吧，生成你专有的词云图！！！'
        return render(request, 'talk.html', locals())
    if request.method=='POST':
        daily=request.POST.get('daily')
        obj=Tracktable(u_id=u_id,daily=daily)
        obj.save()
        return render(request, 'talk.html',locals())


def login_view(request):
    if request.method=='GET':
        return render(request,'login.html')
    if request.method=='POST':
        username=request.POST.get('username')
        password=request.POST.get('password')
        user= authenticate(request,username=username, password=password,is_active=1,email_active=1)
        if user:
            login(request,user)
            return redirect('/life/user_index')
        else:
            error='该用户不存在或者帐号密码错误'
            return render(request,'login.html',locals())


def register(request):
    if request.method=='GET':
        return render(request,'register.html')
    if request.method=='POST':
        username = request.POST.get('username')
        password = request.POST.get('password1')
        repassword=request.POST.get('password2')
        email = request.POST.get('email')
        verify=request.POST.get('verify')
        conn = redis.StrictRedis(host="127.0.0.1", port=6379, password="", db=3)
        if verify:
            try:
                obj=conn.get(email).decode('utf-8')
            except:
                errmg='请先获取验证码'
                return render(request,'register.html',locals())
        else:
            errmg='未填写验证码'
            return render(request,'register.html',locals())
        if password==repassword:
            if verify==obj:
                user = UserInfo.objects.create_user(username=username, password=password, email=email,is_staff=False,is_superuser=False,email_active=1)
                user.save()
                message='注册成功'
                return render(request,'login.html',locals())
            else:
                errmg='验证码不正确，请重新输入'
                return render(request,'register.html',{'errmg':errmg})
        else:
            errmg='密码不一致，请更改好再提交'
            return render(request,'register.html',{'errmg':errmg})

def logout_view(request):
    logout(request)
    return redirect('/life/index/')

def ajax_reg(request):
    global response
    if request.method=='POST':
        email = request.POST.get('email', '').strip()
        if not email:
            return JsonResponse({'success':False,'message':'邮箱不能为空'})
        conn = Connection(
            host='localhost',
            port=3306,
            user='root',
            password='Acky16140563.'
        )
        cursor = conn.cursor()
        conn.select_db('digitallife')
        sql="select `email`,`email_active` from UserInfo where email='%s';"%(email)
        cursor.execute(sql)
        obj=cursor.fetchall()
        if obj:
            for i in obj:
                if i[1]==1:
                    message='该邮箱已经注册了！！！'
                    return JsonResponse({'success':False,'message':message})
                else:
                    try:
                        result=send_sms.delay(email)
                        if result==1:
                            return JsonResponse({'code':200,'msg':'验证码发送成功，请您注意接收'})
                        else:
                            message='验证码发送失败，检查一下自己的网络或者业务繁忙请稍后再试！'
                            return JsonResponse({'code':400,'msg':message})
                    except:
                        message='验证码发送失败,请检查邮箱地址'
                        return JsonResponse({'code':400,'msg':message})
        else:
            result = send_sms.delay(email)
            status=result.state
            suc=['PENDING','STARTED','SUCCESS']
            if status in suc:
                return JsonResponse({'code':200,'msg':'，验证码发送成功，请您注意接收'})
            elif status=='RETRY':
                message='正在重新发送，如还未收到，可进行重新发送'
                return JsonResponse({'success':400,'message':message})
            elif status=='FAILURE':
                message = '验证码发送失败，检查一下自己的网络或者业务繁忙请稍后再试！'
                return JsonResponse({'code': 400, 'msg': message})


class ItemBasedCF:
    def __init__(self,train_file):
        self.train_file = train_file
        self.readData()
    def readData(self):
        self.train = dict()
        for line in self.train_file:
            user,score,item = line.strip().split(",")
            self.train.setdefault(user,{})
            self.train[user][item] = int(float(score))

    def ItemSimilarity(self):
        C = dict()
        N = dict()
        for user, items in self.train.items():
            for i in items.keys():
                N.setdefault(i, 0)
                N[i] += 1
                C.setdefault(i, {})
                for j in items.keys():
                    if i == j: continue
                    C[i].setdefault(j, 0)
                    C[i][j] += 1 / math.log(1 + len(items) * 1.0)
        self.W = dict()
        self.W_max = dict()
        for i, related_items in C.items():
            self.W.setdefault(i, {})

            for j, cij in related_items.items():
                self.W_max.setdefault(j, 0.0)
                self.W[i][j] = cij / (math.sqrt(N[i] * N[j]))
                if self.W[i][j] > self.W_max[j]:
                    self.W_max[j] = self.W[i][j]
        for i, related_items in C.items():
            for j, cij in related_items.items():
                self.W[i][j] = self.W[i][j] / self.W_max[j]

        return self.W



    def Recommend(self, user, K=3, N=10):
        rank = dict()
        try:
            action_item = self.train[user]
            for item, score in action_item.items():
                for j, wj in sorted(self.W[item].items(), key=lambda x: x[1], reverse=True)[0:K]:
                    if j in action_item.keys():
                        continue
                    rank.setdefault(j, 0)
                    rank[j] += score * wj
            return dict(sorted(rank.items(), key=lambda x: x[1], reverse=True)[0:N])
        except:
            return


def find(lst):
    data=Userfoodtable.objects.values_list('u_id','score','food')
    for i in data:
        i=list(i)
        a=str(i[0])
        b=str(i[1])
        s=a+','+b+','+i[2]
        lst.append(s)


def index(request):
    return render(request,'index.html')


def cloud(data_cut,u_id):
    stop_words = []
    with open("/home/dreamcreator/djdemo/life/stopwords.txt", 'r', encoding='utf-8') as f:
        for line in f:
            if len(line) > 0:
                stop_words.append(line.strip())
    data_result = [i for i in data_cut if i not in stop_words]
    text = " ".join(data_result).replace("\n", "")
    wc = WordCloud(font_path="/home/dreamcreator/djdemo/life/STXIHEI.TTF", background_color="white", max_words=500)
    wc.generate(text)
    m='/home/dreamcreator/djdemo'
    s = '/static/images/IMJG' + str(u_id) + '.jpg'
    wc.to_file(m+s)
    return s


def profile1(request):
    return render(request,'profile1.html')

def profile2(request):
    return render(request,'profile2.html')