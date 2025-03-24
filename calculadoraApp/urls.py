from django.urls import path
from .views import home_view, TFG_view, CRC_view

urlpatterns = [
    path('', home_view, name="home"),
    path('calculadora_tfg', TFG_view, name="tfg_calculator"), 
    path('calculadora_crc', CRC_view, name="crc_calculator") 
]
