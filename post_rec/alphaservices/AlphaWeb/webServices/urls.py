from django.urls import path
from . import views

urlpatterns = [
    path('alpha-ask', views.getAnswer, name='ask question'),
    path('QApage', views.index, name='enter web page')

]
