from django.db import models
from django.contrib.auth.models import User

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    metric_name = models.CharField(max_length=100, help_text="e.g. Egg Yield, Fish Weight, Harvest Volume")
    metric_unit = models.CharField(max_length=30, help_text="e.g. crates, kg, liters")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.metric_name} in {self.metric_unit})"


class SupervisorProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('supervisor', 'Supervisor'),
    ]

    # OneToOneField: each User gets exactly one SupervisorProfile
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='supervisor')
    department = models.ForeignKey(
        Department, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='supervisors',
        help_text="The department this supervisor manages"
    )
    phone = models.CharField(max_length=30, blank=True)
    bio = models.TextField(blank=True, help_text="Short bio of the supervisor")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


class Farmer(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    # Unique auto-generated ID (e.g. FMR-0001)
    farmer_id = models.CharField(max_length=20, unique=True, blank=True, editable=False)
    name = models.CharField(max_length=150)
    contact = models.CharField(max_length=50)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name='farmers')
    date_joined = models.DateField()
    location = models.CharField(max_length=200, blank=True, help_text="Farm location, village, or address")
    notes = models.TextField(blank=True, help_text="Farmer bio, farm size, background records")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Generate FMR-0001 format automatically on initial save
        if not self.farmer_id:
            last_farmer = Farmer.objects.order_by('-id').first()
            next_number = (last_farmer.id + 1) if last_farmer else 1
            self.farmer_id = f"FMR-{next_number:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.farmer_id} - {self.name} ({self.department.name})"


class PerformanceLog(models.Model):
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name='performance_logs')
    date = models.DateField()
    metric_value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Recorded metric value")
    notes = models.TextField(blank=True)
    logged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Enforce one daily entry per farmer
        unique_together = ('farmer', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.farmer.name} - {self.date}: {self.metric_value}"
