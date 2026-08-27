from django.urls import path
from . import views

app_name = 'inuwasischedule'

urlpatterns = [
    path('', views.index, name='index'),
    path('view/', views.view_schedule, name='view_schedule'),  # views.view_schedule로 수정
]