import csv
import json
import re
from datetime import date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db.models import Count, Avg, Max, Min, Sum, Q
from django.db.models.functions import TruncWeek, TruncMonth
from .models import Farmer, Department, PerformanceLog
from .forms import FarmerForm, PerformanceLogForm, DepartmentForm

def dashboard(request):
    """
    Overview Dashboard: High-level metrics, department breakdown, and recent logs.
    """
    active_farmers_count = Farmer.objects.filter(status='active').count()
    inactive_farmers_count = Farmer.objects.filter(status='inactive').count()
    total_logs_count = PerformanceLog.objects.count()

    # Departments with active farmer count and average metric
    departments = Department.objects.annotate(
        active_farmer_count=Count('farmers', filter=Q(farmers__status='active'))
    )

    # Recent 8 performance logs
    recent_logs = PerformanceLog.objects.select_related('farmer', 'farmer__department').order_by('-date', '-created_at')[:8]

    context = {
        'active_farmers_count': active_farmers_count,
        'inactive_farmers_count': inactive_farmers_count,
        'departments': departments,
        'total_logs_count': total_logs_count,
        'recent_logs': recent_logs,
    }
    return render(request, 'farmers/dashboard.html', context)


def farmer_list(request):
    """
    Searchable and filterable table of farmers with status badges.
    """
    query = request.GET.get('q', '').strip()
    dept_id = request.GET.get('department', '')
    status = request.GET.get('status', 'active')

    farmers = Farmer.objects.select_related('department')

    if status and status != 'all':
        farmers = farmers.filter(status=status)

    if dept_id:
        farmers = farmers.filter(department_id=dept_id)

    if query:
        farmers = farmers.filter(
            Q(name__icontains=query) |
            Q(farmer_id__icontains=query) |
            Q(contact__icontains=query)
        )

    departments = Department.objects.all()

    context = {
        'farmers': farmers,
        'departments': departments,
        'selected_dept': dept_id,
        'selected_status': status,
        'query': query,
    }
    return render(request, 'farmers/farmer_list.html', context)


def farmer_create(request):
    """
    Enroll a new farmer with validation.
    """
    if request.method == 'POST':
        form = FarmerForm(request.POST)
        if form.is_valid():
            farmer = form.save()
            messages.success(request, f"Farmer {farmer.name} ({farmer.farmer_id}) successfully enrolled!")
            return redirect('farmer_list')
    else:
        form = FarmerForm()

    return render(request, 'farmers/farmer_form.html', {'form': form, 'title': 'Enroll New Farmer'})


def farmer_edit(request, pk):
    """
    Edit existing farmer details.
    """
    farmer = get_object_or_404(Farmer, pk=pk)
    if request.method == 'POST':
        form = FarmerForm(request.POST, instance=farmer)
        if form.is_valid():
            form.save()
            messages.success(request, f"Farmer {farmer.name} updated successfully!")
            return redirect('farmer_detail', pk=farmer.pk)
    else:
        form = FarmerForm(instance=farmer)

    return render(request, 'farmers/farmer_form.html', {'form': form, 'farmer': farmer, 'title': f'Edit {farmer.name}'})


def farmer_toggle_status(request, pk):
    """
    Soft-delete (archive) or reactivate a farmer record.
    """
    farmer = get_object_or_404(Farmer, pk=pk)
    if farmer.status == 'active':
        farmer.status = 'inactive'
        action_name = "archived (soft-deleted)"
    else:
        farmer.status = 'active'
        action_name = "reactivated"
    
    farmer.save()
    messages.success(request, f"Farmer {farmer.name} has been {action_name} successfully.")
    return redirect('farmer_list')


def farmer_detail(request, pk):
    """
    Individual Farmer Portfolio & Performance History with Chart.js trend.
    """
    farmer = get_object_or_404(Farmer.objects.select_related('department'), pk=pk)
    logs = farmer.performance_logs.order_by('date')

    # Aggregates
    total_logs = logs.count()
    avg_performance = logs.aggregate(Avg('metric_value'))['metric_value__avg'] or 0
    max_performance = logs.aggregate(Max('metric_value'))['metric_value__max'] or 0

    # Chart data (chronological)
    chart_dates = [log.date.strftime('%b %d, %Y') for log in logs]
    chart_values = [float(log.metric_value) for log in logs]

    context = {
        'farmer': farmer,
        'logs': logs.reverse(), # Show most recent first in table
        'total_logs': total_logs,
        'avg_performance': round(avg_performance, 2),
        'max_performance': round(max_performance, 2),
        'chart_dates_json': json.dumps(chart_dates),
        'chart_values_json': json.dumps(chart_values),
    }
    return render(request, 'farmers/farmer_detail.html', context)


def log_entry(request):
    """
    Supervisor daily performance log entry.
    """
    if request.method == 'POST':
        form = PerformanceLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            if request.user.is_authenticated:
                log.logged_by = request.user
            log.save()
            messages.success(request, f"Performance logged successfully for {log.farmer.name} on {log.date}!")
            return redirect('farmer_detail', pk=log.farmer.pk)
    else:
        farmer_id = request.GET.get('farmer_id')
        initial = {'farmer': farmer_id} if farmer_id else {}
        form = PerformanceLogForm(initial=initial)

    farmer_meta = {
        f.id: {
            'unit': f.department.metric_unit,
            'metric': f.department.metric_name,
            'department': f.department.name
        }
        for f in Farmer.objects.filter(status='active').select_related('department')
    }

    context = {
        'form': form,
        'farmer_meta_json': json.dumps(farmer_meta),
    }
    return render(request, 'farmers/log_entry.html', context)


def department_list(request):
    """
    Department overview and tracked performance metrics.
    """
    departments = Department.objects.annotate(
        active_farmer_count=Count('farmers', filter=Q(farmers__status='active')),
        total_farmer_count=Count('farmers')
    )
    return render(request, 'farmers/department_list.html', {'departments': departments})


def department_create(request):
    """
    Create a new operational department directly on the frontend.
    """
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            dept = form.save()
            messages.success(request, f"Department '{dept.name}' created successfully with metric: {dept.metric_name} ({dept.metric_unit})!")
            return redirect('department_list')
    else:
        form = DepartmentForm()

    return render(request, 'farmers/department_form.html', {'form': form})


def performance_analysis(request):
    """
    Weekly & Monthly Performance Analysis with unit separation,
    normalized fairness ranking (% vs department avg), and honest day-counted chart labels.
    """
    period_type = request.GET.get('period', 'weekly')  # 'weekly' or 'monthly'
    dept_id = request.GET.get('department', '')

    departments = Department.objects.all()
    selected_dept = None
    if dept_id:
        selected_dept = get_object_or_404(Department, pk=dept_id)

    # Base logs queryset
    logs = PerformanceLog.objects.select_related('farmer', 'farmer__department')
    if selected_dept:
        logs = logs.filter(farmer__department=selected_dept)

    # 1. Department Breakdown (Calculated per-department so units are NEVER improperly blended)
    dept_summaries = []
    dept_daily_averages = {}

    target_departments = [selected_dept] if selected_dept else departments
    for d in target_departments:
        d_logs = PerformanceLog.objects.filter(farmer__department=d)
        d_total = d_logs.aggregate(Sum('metric_value'))['metric_value__sum'] or 0
        d_avg = d_logs.aggregate(Avg('metric_value'))['metric_value__avg'] or 0
        d_farmers_count = d_logs.values('farmer').distinct().count()
        d_top = d_logs.values('farmer__id', 'farmer__name', 'farmer__farmer_id') \
            .annotate(total=Sum('metric_value')).order_by('-total').first()

        dept_daily_averages[d.id] = float(d_avg)

        dept_summaries.append({
            'department': d,
            'total_output': round(d_total, 2),
            'avg_daily': round(d_avg, 2),
            'active_farmers': d_farmers_count,
            'top_farmer': d_top,
        })

    # 2. Honest Chart Data with Day Counts (Avoids partial week distortion)
    trunc_func = TruncWeek if period_type == 'weekly' else TruncMonth
    aggregated_periods = logs.annotate(period=trunc_func('date')) \
        .values('period') \
        .annotate(
            total_output=Sum('metric_value'),
            avg_daily=Avg('metric_value'),
            days_count=Count('date', distinct=True),
            min_date=Min('date'),
            max_date=Max('date')
        ) \
        .order_by('period')

    chart_labels = []
    chart_averages = []
    chart_totals = []

    for item in aggregated_periods:
        p_date = item['period']
        if not p_date:
            continue
        days = item['days_count']
        min_d = item['min_date']
        max_d = item['max_date']

        if period_type == 'weekly':
            if min_d == max_d:
                date_str = min_d.strftime('%b %d')
            else:
                date_str = f"{min_d.strftime('%b %d')}–{max_d.strftime('%d')}"
            label = f"{date_str} ({days}d)"
        else:
            label = f"{p_date.strftime('%B %Y')} ({days}d logged)"

        chart_labels.append(label)
        chart_averages.append(float(round(item['avg_daily'], 2)))
        chart_totals.append(float(round(item['total_output'], 2)))

    # 3. Normalized League Table (% vs Department Average)
    # Fairly compares farmers across departments by benchmarking against their own peers!
    farmer_stats = logs.values(
        'farmer__id', 'farmer__name', 'farmer__farmer_id', 
        'farmer__department__id', 'farmer__department__name', 'farmer__department__metric_unit'
    ).annotate(
        total_output=Sum('metric_value'),
        avg_output=Avg('metric_value'),
        entry_count=Count('id')
    )

    ranked_farmers = []
    for f in farmer_stats:
        f_dept_id = f['farmer__department__id']
        dept_avg = dept_daily_averages.get(f_dept_id, 0)
        f_avg = float(f['avg_output'])

        if dept_avg > 0:
            rel_perf = round(((f_avg - dept_avg) / dept_avg) * 100, 1)
        else:
            rel_perf = 0.0

        ranked_farmers.append({
            'farmer_id': f['farmer__id'],
            'farmer_code': f['farmer__farmer_id'],
            'name': f['farmer__name'],
            'dept_name': f['farmer__department__name'],
            'unit': f['farmer__department__metric_unit'],
            'total_output': round(f['total_output'], 2),
            'avg_output': round(f['avg_output'], 2),
            'entry_count': f['entry_count'],
            'rel_perf': rel_perf,  # Percentage relative to department benchmark!
        })

    # Sort by relative performance (highest outperformer first!)
    ranked_farmers.sort(key=lambda x: x['rel_perf'], reverse=True)

    # Top overall relative performer
    top_performer = ranked_farmers[0] if ranked_farmers else None

    context = {
        'period_type': period_type,
        'departments': departments,
        'selected_dept': selected_dept,
        'dept_summaries': dept_summaries,
        'ranked_farmers': ranked_farmers,
        'top_performer': top_performer,
        'chart_labels_json': json.dumps(chart_labels),
        'chart_averages_json': json.dumps(chart_averages),
        'chart_totals_json': json.dumps(chart_totals),
        'is_all_departments': selected_dept is None,
    }
    return render(request, 'farmers/performance_analysis.html', context)


def user_login(request):
    """
    3-Door Login Portal: Admin, Supervisor, Farmer.
    """
    active_tab = request.GET.get('role', 'admin')  # 'admin', 'supervisor', 'farmer'

    if request.method == 'POST':
        role = request.POST.get('role', 'admin')
        active_tab = role

        if role == 'farmer':
            farmer_code_input = request.POST.get('farmer_id', '').strip()
            contact_input = request.POST.get('contact', '').strip()

            if not farmer_code_input or not contact_input:
                messages.error(request, "Please enter your Farmer ID and contact phone number.")
            else:
                # 1. Flexible Farmer ID Normalization (handles 1, 0001, fmr1, FMR-0001, etc.)
                farmer = Farmer.objects.filter(farmer_id__iexact=farmer_code_input, status='active').first()
                if not farmer:
                    clean_id = re.sub(r'[^a-zA-Z0-9]', '', farmer_code_input).upper()
                    digits_match = re.search(r'\d+', clean_id)
                    if digits_match:
                        num = int(digits_match.group())
                        formatted_id = f"FMR-{num:04d}"
                        farmer = Farmer.objects.filter(farmer_id__iexact=formatted_id, status='active').first()

                if farmer:
                    # 2. Flexible Phone/Contact Normalization (digits only comparison)
                    farmer_phone_digits = re.sub(r'\D', '', farmer.contact)
                    input_phone_digits = re.sub(r'\D', '', contact_input)

                    match = False
                    if input_phone_digits and farmer_phone_digits:
                        if input_phone_digits in farmer_phone_digits or farmer_phone_digits in input_phone_digits:
                            match = True
                        elif len(input_phone_digits) >= 7 and len(farmer_phone_digits) >= 7:
                            if input_phone_digits[-7:] == farmer_phone_digits[-7:]:
                                match = True
                    # Fallback email match
                    if not match and '@' in contact_input and contact_input.lower() in farmer.contact.lower():
                        match = True

                    if match:
                        request.session['farmer_id'] = farmer.id
                        request.session['farmer_name'] = farmer.name
                        request.session['farmer_code'] = farmer.farmer_id
                        request.session['user_role'] = 'farmer'
                        messages.success(request, f"Welcome back, {farmer.name}! Here is your personal portfolio.")
                        return redirect('farmer_detail', pk=farmer.id)
                    else:
                        messages.error(request, f"Phone/contact number does not match records for {farmer.farmer_id}.")
                else:
                    messages.error(request, f"No active farmer found matching ID '{farmer_code_input}'.")

        elif role in ['admin', 'supervisor']:
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '').strip()

            user = authenticate(request, username=username, password=password)
            if user is not None:
                user_role = getattr(getattr(user, 'profile', None), 'role', None)
                if user.is_superuser or user.is_staff:
                    user_role = 'admin' if not user_role else user_role

                if role == 'admin' and (user.is_superuser or user_role == 'admin'):
                    login(request, user)
                    request.session['user_role'] = 'admin'
                    messages.success(request, f"Welcome back, Admin {user.username}!")
                    next_url = request.GET.get('next') or 'dashboard'
                    return redirect(next_url)
                elif role == 'supervisor' and (user_role == 'supervisor' or user.is_staff):
                    login(request, user)
                    request.session['user_role'] = 'supervisor'
                    messages.success(request, f"Welcome, Supervisor {user.username}!")
                    return redirect('log_entry')
                else:
                    messages.error(request, f"Account '{username}' does not have '{role.capitalize()}' privileges. Please choose the correct portal.")
            else:
                messages.error(request, f"Invalid username or password for {role.capitalize()} portal.")

    context = {
        'active_tab': active_tab,
        'next': request.GET.get('next', ''),
    }
    return render(request, 'login.html', context)


def user_logout(request):
    """
    Sign out user or farmer session.
    """
    logout(request)
    request.session.flush()
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')


def batch_log_entry(request):
    """
    Bulk daily entry grid: enables supervisors/admins to record daily yields
    for all active farmers in a department at once.
    """
    departments = Department.objects.all().order_by('name')
    selected_dept_id = request.GET.get('department') or request.POST.get('department')
    
    # Default to supervisor's department if available, or first department
    selected_dept = None
    if selected_dept_id:
        selected_dept = Department.objects.filter(id=selected_dept_id).first()
    elif hasattr(request.user, 'profile') and request.user.profile.department:
        selected_dept = request.user.profile.department
    elif departments.exists():
        selected_dept = departments.first()

    today_str = date.today().isoformat()
    selected_date_str = request.GET.get('date') or request.POST.get('date') or today_str

    try:
        selected_date = date.fromisoformat(selected_date_str)
        if selected_date > date.today():
            messages.error(request, "Future dates are prohibited. Resetting to today.")
            selected_date = date.today()
            selected_date_str = today_str
    except ValueError:
        selected_date = date.today()
        selected_date_str = today_str

    active_farmers = []
    farmer_rows = []

    if selected_dept:
        active_farmers = Farmer.objects.filter(department=selected_dept, status='active').order_by('name')
        existing_logs = {
            log.farmer_id: log
            for log in PerformanceLog.objects.filter(farmer__in=active_farmers, date=selected_date)
        }

        if request.method == 'POST':
            saved_count = 0
            for farmer in active_farmers:
                val_key = f"yield_{farmer.id}"
                notes_key = f"notes_{farmer.id}"
                raw_val = request.POST.get(val_key, '').strip()
                raw_notes = request.POST.get(notes_key, '').strip()

                if raw_val:
                    try:
                        metric_val = float(raw_val)
                        if metric_val < 0:
                            continue
                        PerformanceLog.objects.update_or_create(
                            farmer=farmer,
                            date=selected_date,
                            defaults={
                                'metric_value': metric_val,
                                'notes': raw_notes,
                                'logged_by': request.user if request.user.is_authenticated else None
                            }
                        )
                        saved_count += 1
                    except ValueError:
                        pass

            messages.success(request, f"Successfully recorded daily yields for {saved_count} farmer(s) in {selected_dept.name} on {selected_date}.")
            return redirect(f"{request.path}?department={selected_dept.id}&date={selected_date_str}")

        for farmer in active_farmers:
            log = existing_logs.get(farmer.id)
            farmer_rows.append({
                'farmer': farmer,
                'existing_log': log,
                'value': log.metric_value if log else '',
                'notes': log.notes if log else '',
            })

    context = {
        'departments': departments,
        'selected_dept': selected_dept,
        'selected_date_str': selected_date_str,
        'today_str': today_str,
        'farmer_rows': farmer_rows,
        'total_active': len(farmer_rows),
    }
    return render(request, 'farmers/batch_log_entry.html', context)


def export_performance_csv(request):
    """
    Exports filtered or all performance logs to a downloadable CSV spreadsheet.
    """
    logs = PerformanceLog.objects.select_related('farmer', 'farmer__department', 'logged_by').order_by('-date', 'farmer__name')
    
    dept_id = request.GET.get('department')
    if dept_id:
        logs = logs.filter(farmer__department_id=dept_id)

    farmer_id = request.GET.get('farmer_id')
    if farmer_id:
        logs = logs.filter(farmer_id=farmer_id)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    today_str = date.today().strftime('%Y-%m-%d')
    response['Content-Disposition'] = f'attachment; filename="AgroTrack_Performance_Logs_{today_str}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Log ID', 'Date', 'Farmer ID', 'Farmer Name', 'Department',
        'Metric Name', 'Recorded Yield', 'Unit', 'Logged By', 'Notes'
    ])

    for log in logs:
        writer.writerow([
            log.id,
            log.date.strftime('%Y-%m-%d'),
            log.farmer.farmer_id,
            log.farmer.name,
            log.farmer.department.name,
            log.farmer.department.metric_name,
            log.metric_value,
            log.farmer.department.metric_unit,
            log.logged_by.username if log.logged_by else 'Field Log',
            log.notes or ''
        ])

    return response


def export_farmers_csv(request):
    """
    Exports the complete farmer directory with department stats to CSV.
    """
    farmers = Farmer.objects.select_related('department').annotate(
        total_logs=Count('performance_logs'),
        avg_yield=Avg('performance_logs__metric_value')
    ).order_by('department__name', 'name')

    dept_id = request.GET.get('department')
    if dept_id:
        farmers = farmers.filter(department_id=dept_id)

    status = request.GET.get('status')
    if status and status != 'all':
        farmers = farmers.filter(status=status)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    today_str = date.today().strftime('%Y-%m-%d')
    response['Content-Disposition'] = f'attachment; filename="AgroTrack_Farmers_Directory_{today_str}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Farmer ID', 'Farmer Name', 'Department', 'Contact', 'Location',
        'Date Joined', 'Status', 'Total Logs Recorded', 'Lifetime Avg Yield', 'Unit', 'Notes'
    ])

    for f in farmers:
        writer.writerow([
            f.farmer_id,
            f.name,
            f.department.name,
            f.contact,
            f.location or 'N/A',
            f.date_joined.strftime('%Y-%m-%d') if f.date_joined else '',
            f.status.capitalize(),
            f.total_logs,
            round(f.avg_yield, 2) if f.avg_yield is not None else 0.0,
            f.department.metric_unit,
            f.notes or ''
        ])

    return response



