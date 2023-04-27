from importlib.resources import _

from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.

class LifeImformation(models.Model):
    class Meta:
        db_table = "life"

    u_id = models.IntegerField(blank=False, verbose_name='用户id', db_column='u_id')
    breakfast = models.CharField(max_length=255, blank=True, verbose_name='早餐餐品', db_column='breakfast')
    am_tea = models.CharField(max_length=255, blank=True, verbose_name='上午茶', db_column='am_tea')
    lunch = models.CharField(max_length=255, blank=True, verbose_name='午餐餐品', db_column='lunch')
    pm_tea = models.CharField(max_length=255, blank=True, verbose_name='下午茶', db_column='pm_tea')
    dinner = models.CharField(max_length=255, blank=True, verbose_name='晚餐餐品', db_column='dinner')
    supper = models.CharField(max_length=255, blank=True, verbose_name='夜宵', db_column='supper')
    water = models.CharField(max_length=255, blank=False, verbose_name='饮水记录', db_column='water')
    drink=models.CharField(max_length=255,blank=True,verbose_name='今日份饮品')
    num=models.CharField(max_length=255,blank=True,verbose_name='杯数',db_column='num')
    size=models.CharField(max_length=100,blank=True,verbose_name='大小',db_column='size')
    date=models.CharField(max_length=255,blank=False,verbose_name='日期',db_column='date',default='')
    record = models.IntegerField(default=0, verbose_name='记录判断', db_column='record')

class ManageTable(models.Model):
    class Meta:
        db_table='Managetable'

    u_id = models.IntegerField(blank=False, verbose_name='用户id', db_column='u_id')
    type=models.CharField(max_length=255,blank=True,verbose_name='流通方式',db_column='type')
    money=models.FloatField(blank=True,verbose_name='金额',db_column='money',default=0)
    source=models.CharField(max_length=255,blank=True,verbose_name='收入来源',db_column='source')
    pay=models.CharField(max_length=255,blank=True,verbose_name='指出去向',db_column='pay')
    am_money=models.CharField(blank=True,max_length=100,verbose_name='早餐金额',db_column='am_money',default='')
    pm_money=models.CharField(blank=True,max_length=100,verbose_name='午餐金额',db_column='pm_money',default='')
    dinner_money=models.CharField(blank=True,max_length=100,verbose_name='晚餐金额',db_column='dinner_money',default='')
    date=models.CharField(max_length=255,blank=False,verbose_name='日期',db_column='date',default='')


class Tasktable(models.Model):
    class Meta:
        db_table = 'task'
    u_id = models.IntegerField(blank=False, verbose_name='用户id', db_column='u_id')
    content = models.TextField(blank=False, verbose_name='活动事件', db_column='content',default='')
    date=models.CharField(blank=False,max_length=255,verbose_name='日期',db_column='date',default='')
    weekd=models.CharField(blank=False,max_length=100,verbose_name='星期',db_column='weekd',default='')
    duration=models.FloatField(blank=False,verbose_name='时长',db_column='duration')
    task_type=models.CharField(max_length=255,blank=False,verbose_name='活动类型',db_column='task_type',default='')


class Eventtable(models.Model):
    class Meta:
        db_table = 'event'
    u_id = models.IntegerField(blank=False, verbose_name='用户id', db_column='u_id')
    clothes = models.CharField(blank=False, max_length=255, verbose_name='衣服穿搭', db_column='clothes',default='')
    clothe_type=models.CharField(max_length=100,blank=True,verbose_name='衣物类型',db_column='clothe_type')
    degree=models.CharField(max_length=100,blank=True,verbose_name='薄厚程度',db_column='degree')
    min_c=models.CharField(max_length=100,blank=False,verbose_name='最低温',db_column='min_c',default='')
    max_c=models.CharField(max_length=100,blank=False,verbose_name='最高温',db_column='max_c',default='')


class Userfoodtable(models.Model):
    class Meta:
        db_table = 'user_food'
    u_id = models.IntegerField(blank=False, verbose_name='用户id', db_column='u_id')
    score = models.IntegerField(blank=False, verbose_name='美食评分', db_column='score')
    food = models.CharField(max_length=255, blank=False, verbose_name='美食名称', db_column='usr_food')


class Foodtable(models.Model):
    class Meta:
        db_table = 'foodtable'

    food = models.CharField(max_length=255, blank=False, verbose_name='美食名称', db_column='food')
    img=models.ImageField(upload_to='images',max_length=255,default='')

class Sporttable(models.Model):
    class Meta:
        db_table='sporttable'

    u_id = models.IntegerField(blank=False, verbose_name='用户id', db_column='u_id')
    sport_type=models.CharField(max_length=255,blank=True,verbose_name='运动方式',db_column='sport_type',default='')
    sport_time=models.FloatField(blank=True,verbose_name='运动时间',db_column='sport_time',default=0)
    sport_date=models.CharField(max_length=255,blank=True,verbose_name='运动日期',db_column='sport_date',default='')
    sleep_date=models.CharField(max_length=255,blank=True,verbose_name='睡眠日期',db_column='sleep_date',default='')
    sleep_condition=models.CharField(max_length=255,blank=True,verbose_name='睡眠状况',db_column='sleep_condition',default='')
    sleep_time=models.CharField(max_length=255,blank=True,verbose_name='入睡时间',db_column='sleep_time',default='')
    wake_up=models.CharField(max_length=255,blank=True,verbose_name='起床时间',db_column='wake_up',default='')
    kalcr = models.CharField(max_length=255, blank=True, verbose_name='热量', db_column='kalcr',default='')
    BMR = models.CharField(max_length=255, blank=True, verbose_name='基础代谢率', db_column='BMR',default='')
    BIM = models.CharField(max_length=255, blank=True, verbose_name='身体质量指数', db_column='BIM',default='')
    record=models.IntegerField(default=0,verbose_name='记录判断',db_column='record')


class Tracktable(models.Model):
    class Meta:
        db_table='track'

    u_id = models.IntegerField(blank=False, verbose_name='用户id', db_column='u_id')
    locus=models.CharField(max_length=255,blank=True,verbose_name='轨迹',db_column='locus')
    daily=models.TextField(blank=True,verbose_name='日记',db_column='daily')
    img=models.TextField(blank=True,verbose_name='图片地址',db_column='img')

class UserInfo(AbstractUser):
    class Meta:
        db_table='UserInfo'

    healthy_score=models.IntegerField(default=60,verbose_name='健康分数',db_column='healthy_score')
    email_active=models.BooleanField(default=False,verbose_name='邮箱激活',db_column='email_active')
    sport=models.FloatField(default=0,verbose_name='周运动时长',db_column='sport')
    sleep=models.FloatField(default=0,verbose_name='周睡眠时长',db_column='sleep')
    water=models.FloatField(default=0,verbose_name='周喝水记录',db_column='water')