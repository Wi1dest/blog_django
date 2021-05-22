# 进行users子应用的视图路由
from django.urls import path
from users.views import RegisterView, ImageCodeView

urlpatterns = [
    # path的第一个参数:路由 第二个参数:视图函数
    path('register/',RegisterView.as_view(),name='register'),

    # 图片验证码
    path('imagecode/',ImageCodeView.as_view(),name='imagecode')
]