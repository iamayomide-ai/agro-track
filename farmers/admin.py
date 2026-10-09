from django.contrib import admin
from .models import Department, SupervisorProfile, Farmer, PerformanceLog

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'metric_name', 'metric_unit', 'created_at')
    search_fields = ('name',)

@admin.register(SupervisorProfile)
class SupervisorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'department', 'phone')
    list_filter = ('role', 'department')

@admin.register(Farmer)
class FarmerAdmin(admin.ModelAdmin):
    list_display = ('farmer_id', 'name', 'department', 'contact', 'status', 'date_joined')
    list_filter = ('status', 'department')
    search_fields = ('farmer_id', 'name', 'contact')

@admin.register(PerformanceLog)
class PerformanceLogAdmin(admin.ModelAdmin):
    list_display = ('farmer', 'date', 'metric_value', 'logged_by')
    list_filter = ('farmer__department', 'date')
    search_fields = ('farmer__name', 'farmer__farmer_id')
