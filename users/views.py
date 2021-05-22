from email.mime import image

from django.db.models.functions import text
from django.shortcuts import render

# Create your views here.

from django.views import View

# 注册视图
from django_redis import get_redis_connection


class RegisterView(View):

    def get(self,request):
        return render(request,'register.html')


from libs.captcha.captcha import captcha
from django.http import HttpResponseBadRequest, HttpResponse


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