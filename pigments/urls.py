from django.urls import path

from pigments import views

app_name = 'pigments'
urlpatterns = [
    path('', views.pigment_list, name='list'),
]
