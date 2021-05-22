import re
from email.mime import image
from random import randint

from django.contrib.auth import login
from django.db import DatabaseError
from django.db.models.functions import text
from django.shortcuts import render, redirect
import logging

from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from libs.yuntongxun.sms import CCP
from users.models import User

logger = logging.getLogger('django')

# Create your views here.

from django.views import View

# 注册视图
from django_redis import get_redis_connection

from utils.response_code import RETCODE

class RegisterView(View):

    def get(self,request):
        return render(request,'register.html')

    def post(self,request):
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        sms_code = request.POST.get('sms_code')
        if not all([mobile,password,password2,sms_code]):
            return HttpResponseBadRequest('缺少必要的参数')
        if not re.match(r'^1[3-9]\d{9}$',mobile):
            return HttpResponseBadRequest('手机号不符合规则')
        if not re.match(r'^[0-9A-Za-z]{8,20}$',password):
            return HttpResponseBadRequest('密码不符合规则')
        if password != password2 :
            return HttpResponseBadRequest('两次密码不一致')
        redis_coon = get_redis_connection('default')
        sms_code_redis = redis_coon.get('sms:%s'%mobile)
        if sms_code_redis is None:
            return HttpResponseBadRequest('验证码已过期!')
        if sms_code != sms_code_redis.decode():
            return HttpResponseBadRequest('短信验证码不正确')
        try:
            user = User.objects.create_user(username=mobile,mobile=mobile,password=password)
        except DatabaseError as e:
            logger.error(e)
            return HttpResponseBadRequest('注册失败')
        login(request,user)
        # 4.返回响应跳转到指定页面
        # 暂时返回一个注册成功的信息，后期再实现跳转到指定页面

        # redirect 是进行重定向
        # reverse 是可以通过 namespace:name 来获取到视图所对应的路由
        response = redirect(reverse('home:index'))
        # return HttpResponse('注册成功，重定向到首页')

        #设置cookie信息，以方便首页中 用户信息展示的判断和用户信息的展示
        response.set_cookie('is_login',True)
        response.set_cookie('username',user.username,max_age=7*24*3600)
        return response

from libs.captcha.captcha import captcha
from django.http import HttpResponseBadRequest, HttpResponse, JsonResponse


class ImageCodeView(View):

    def get(self,request):
        # 1.接收前端传来的UUID
        uuid = request.GET.get("uuid")
        # 2.判断UUID是否获取到
        if uuid is None:
            return HttpResponseBadRequest("没有UUID")
        # 3.调用captcha来生成图片验证码
        text,image = captcha.generate_captcha()
        # 4.将图片内容保存到redis uuid作为key,图片内容作为value,设置时效
        redis_coon = get_redis_connection('default')
        redis_coon.setex('img:%s'%uuid,300,text)
        # 5.将图片返回前端
        return HttpResponse(image,content_type='image/jpeg')

class SmsCodeView(View):
    def get(self,request):

    # 1.接收参数
        mobile = request.GET.get('mobile')
        image_code = request.GET.get('image_code')
        uuid = request.GET.get('uuid')
    # 2.参数验证
    #     2.1 参数是否齐全
        if not all([mobile,image_code,uuid]):
            return JsonResponse({'code':RETCODE.NECESSARYPARAMERR,'errmsg':'缺少参数'})
    #     2.2 图片验证码验证
    #         连接redis,获取验证码
        redis_conn = get_redis_connection('default')
        redis_image_code = redis_conn.get('img:%s'%uuid)
    #         判断验证码是否存在
        if redis_image_code is None:
            return JsonResponse({'code':RETCODE.IMAGECODEERR,'errmsg':'图片已过期'})
    #         如果验证码未过期,我们获取之后可以删除图片验证码
        try:
            redis_conn.delete('img:%s'%uuid)
        except Exception as e:
            logger.error(e)
    #         比对验证码
        if redis_image_code.decode().lower() != image_code.lower():
            return JsonResponse({'code':RETCODE.IMAGECODEERR,'errmsg':'验证码错误'})
    # 3.生成短信验证码
        sms_code = '%06d'%randint(0,999999)
        logger.info(sms_code)
    # 4.将短信验证码保存在redis
        redis_conn.setex('sms:%s'%mobile,300,sms_code)
    # 5.发送短信
        CCP().send_template_sms(mobile,[sms_code,5],1)
    # 6.返回响应
        return JsonResponse({'code':RETCODE.OK,'errmsg':'短信发送成功!'})