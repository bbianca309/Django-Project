from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import RestrictedLoginView

urlpatterns = [
    path('', views.index, name='index'),
    path('book/', views.book, name='book'),
    path('preturi/', views.pret, name='pret'),
    path('success/', views.success, name='success'),
    path('cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('cancel/', views.cancel, name='cancel'),
    path('appointments/', views.appointments_list, name='appointments_list'),
    path('appointments/<int:appointment_id>/status/<str:new_status>/', views.change_appointment_status, name='change_appointment_status'),
    path('notifications/', views.notifications, name='notifications'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('verifica-programari/', views.check_appointments, name='check_appointments'),
    path('login/', RestrictedLoginView.as_view(), name='login'),
    path('servicii/', views.servicii, name='servicii'),


    
]