from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('farmers/', views.farmer_list, name='farmer_list'),
    path('farmers/add/', views.farmer_create, name='farmer_create'),
    path('farmers/<int:pk>/', views.farmer_detail, name='farmer_detail'),
    path('farmers/<int:pk>/edit/', views.farmer_edit, name='farmer_edit'),
    path('farmers/<int:pk>/toggle-status/', views.farmer_toggle_status, name='farmer_toggle_status'),
    path('logs/add/', views.log_entry, name='log_entry'),
    path('logs/batch/', views.batch_log_entry, name='batch_log_entry'),
    path('export/logs/', views.export_performance_csv, name='export_performance_csv'),
    path('export/farmers/', views.export_farmers_csv, name='export_farmers_csv'),
    path('analysis/', views.performance_analysis, name='analysis'),
    path('departments/', views.department_list, name='department_list'),
    path('departments/add/', views.department_create, name='department_create'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
]
