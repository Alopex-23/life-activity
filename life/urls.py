from django.urls import path
from life import views

urlpatterns=[
    path('user_index/',views.user_index),
    path('plan/',views.plan),
    path('comm/',views.communcation),
    path('manage/',views.manage),
    path('healthy/',views.healthy),
    path('clothes/',views.clothes),
    path('eat/',views.eat),
    path('talk/',views.talk),
    path('login/',views.login_view),
    path('register/',views.register),
    path('ajax_reg/',views.ajax_reg),
    path('index/',views.index),
    path('login_out/',views.logout_view),
    path('user_index/profile1/',views.profile1),
    path('user_index/profile2/',views.profile2),
]