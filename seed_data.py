import os
import django
from datetime import date, timedelta
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from farmers.models import Department, Farmer, PerformanceLog
from django.contrib.auth.models import User

# Get admin user
admin_user = User.objects.filter(username='admin').first()

# 1. Create Departments
dept_data = [
    {"name": "Poultry", "metric_name": "Egg Yield", "metric_unit": "crates"},
    {"name": "Fishery", "metric_name": "Harvest Weight", "metric_unit": "kg"},
    {"name": "Horticulture", "metric_name": "Harvest Volume", "metric_unit": "crates"},
]

departments = {}
for d in dept_data:
    dept, _ = Department.objects.get_or_create(
        name=d["name"],
        defaults={"metric_name": d["metric_name"], "metric_unit": d["metric_unit"]}
    )
    departments[dept.name] = dept
print("Departments created/verified.")

# 2. Create Farmers
farmers_data = [
    {"name": "Amina Bello", "contact": "+234-803-123-4567", "dept": "Poultry", "status": "active", "days_ago": 60},
    {"name": "Chukwudi Okafor", "contact": "+234-802-987-6543", "dept": "Poultry", "status": "active", "days_ago": 45},
    {"name": "Ibrahim Musa", "contact": "+234-814-555-0199", "dept": "Fishery", "status": "active", "days_ago": 30},
    {"name": "Grace Adeyemi", "contact": "+234-809-777-8822", "dept": "Fishery", "status": "active", "days_ago": 50},
    {"name": "David Mensah", "contact": "+234-818-333-4411", "dept": "Horticulture", "status": "active", "days_ago": 40},
    {"name": "Kofi Asante", "contact": "+234-812-444-9900", "dept": "Poultry", "status": "inactive", "days_ago": 90},
]

created_farmers = []
for f in farmers_data:
    farmer = Farmer.objects.filter(name=f["name"]).first()
    if not farmer:
        farmer = Farmer.objects.create(
            name=f["name"],
            contact=f["contact"],
            department=departments[f["dept"]],
            date_joined=date.today() - timedelta(days=f["days_ago"]),
            status=f["status"]
        )
    created_farmers.append(farmer)

print(f"{len(created_farmers)} Farmers ready.")

# 3. Create Daily Performance Logs for the active farmers over the last 10 days
today = date.today()
for farmer in created_farmers:
    if farmer.status != 'active':
        continue

    base_val = 35.0 if farmer.department.name == "Poultry" else (120.0 if farmer.department.name == "Fishery" else 45.0)

    for i in range(10, -1, -1):
        log_date = today - timedelta(days=i)
        # Random variance
        variance = round(random.uniform(-4.0, 6.0), 2)
        val = max(10.0, base_val + variance)

        PerformanceLog.objects.get_or_create(
            farmer=farmer,
            date=log_date,
            defaults={
                "metric_value": val,
                "notes": f"Routine check for {log_date.strftime('%A')}.",
                "logged_by": admin_user
            }
        )

print("Performance logs seeded successfully!")
