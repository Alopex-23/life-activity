import random
from django.core.mail import send_mail
# from djdemo import settings
from mycelery.main import app
import redis
import time
from celery.result import AsyncResult

@app.task  #celery装饰器，以下的函数就是任务函数
def send_sms(email):
    sms_code = '%06d' % random.randint(0, 999999)
    # to_email = email  # 邮箱来自
    EMAIL_HOST_USER='3052573970@qq.com'
    email_title = '邮箱验证'
    email_body = "您的邮箱注册验证码为：{0}, 该验证码有效时间为两分钟，请及时进行验证。".format(sms_code)
    send_status = send_mail(email_title, email_body,EMAIL_HOST_USER , [email])
    conn = redis.StrictRedis(host="127.0.0.1", port=6379, password="", db=3)
    conn.set(email,sms_code,ex=120)
    return send_status