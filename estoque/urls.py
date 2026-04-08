from django.urls import path

from . import views

app_name = 'estoque'

urlpatterns = [
    path(
        'transferencia-interempresa/',
        views.transferencia_interempresa,
        name='transferencia_interempresa',
    ),
]
