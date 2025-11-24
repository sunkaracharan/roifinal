
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import ROIResult, Payment, UserCalculationLimit
from .forms import QuickEstimateForm, FullCalculatorForm
from django.contrib.auth import login, authenticate, logout
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.db.models.functions import TruncMonth, TruncDay
from django.db.models import Count
from decimal import Decimal
from datetime import timedelta, datetime
import json
import uuid
import hashlib
import hmac
import base64
import os
import google.generativeai as genai

@login_required
@require_GET
def history_analysis_data(request):
    """Return historical ROIResult data for charts, filtered by time range."""
    import pytz
    user = request.user
    # Get filter from query params
    filter_range = request.GET.get('range', '2m')  # default: last 2 months
    now = timezone.now()
    # Calculate start date based on filter
    if filter_range == '10d':
        start_date = now - timedelta(days=10)
        group_by = TruncDay('timestamp')
        group_type = 'day'
    elif filter_range == '1m':
        start_date = now - timedelta(days=30)
        group_by = TruncDay('timestamp')
        group_type = 'day'
    elif filter_range == '3m':
        start_date = now - timedelta(days=90)
        group_by = TruncMonth('timestamp')
        group_type = 'month'
    elif filter_range == '6m':
        start_date = now - timedelta(days=180)
        group_by = TruncMonth('timestamp')
        group_type = 'month'
    elif filter_range == '1y':
        start_date = now - timedelta(days=365)
        group_by = TruncMonth('timestamp')
        group_type = 'month'
    else:  # default 2 months
        start_date = now - timedelta(days=60)
        group_by = TruncMonth('timestamp')
        group_type = 'month'

    # Query ROIResult for user in range
    results = ROIResult.objects.filter(user=user, timestamp__gte=start_date).order_by('timestamp')

    # Prepare time series data
    data = {
        'dates': [],
        'roi_percent': [],
        'availability_gain': [],
        'performance_gain': [],
        'cloud_savings': [],
        'productivity_gain': [],
    }
    for r in results:
        data['dates'].append(r.timestamp.strftime('%Y-%m-%d'))
        data['roi_percent'].append(float(r.roi_percent))
        data['availability_gain'].append(float(r.availability_gain))
        data['performance_gain'].append(float(r.performance_gain))
        data['cloud_savings'].append(float(r.cloud_savings))
        data['productivity_gain'].append(float(r.productivity_gain))

    # Calculations per period (Python-side grouping for Djongo/MongoDB)
    from collections import Counter
    if group_type == 'day':
        group_format = '%Y-%m-%d'
    else:
        group_format = '%Y-%m'
    period_counts = Counter()
    for r in results:
        period = r.timestamp.strftime(group_format)
        period_counts[period] += 1
    data['calculations_per_period'] = dict(period_counts)

    return JsonResponse(data)

# Analysis page view
@login_required
def history_analysis(request):
    """Render the analysis page with chart placeholders and filter options."""
    return render(request, 'calculator/history_analysis.html')
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import ROIResult, Payment, UserCalculationLimit
from .forms import QuickEstimateForm, FullCalculatorForm
from django.contrib.auth import login, authenticate, logout
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone
import json
import uuid
import hashlib
import hmac
import base64
import os
import google.generativeai as genai
from decimal import Decimal


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard_home')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                # Auto-login after registration
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password1')
                user = authenticate(username=username, password=password)
                login(request, user)
                messages.success(request, 'Account created successfully! Welcome to ROI Calculator.')
                return redirect('dashboard_home')
            except IntegrityError:
                messages.error(request, 'Username already exists. Please choose a different username.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


def home_page(request):
    """Landing page for non-authenticated users"""
    if request.user.is_authenticated:
        return redirect('dashboard_home')
    return render(request, 'calculator/landing.html')


def contact_page(request):
    """Contact page with form"""
    if request.method == 'POST':
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        message = request.POST.get('message', '')
        messages.success(request, f'Thank you {name}! Your message has been sent successfully. We\'ll get back to you soon.')
        return redirect('contact')
    return render(request, 'calculator/contact.html')


@login_required
def dashboard_home(request):
    """Dashboard home page for authenticated users"""
    recent_results = ROIResult.objects.filter(user=request.user).order_by('-timestamp')[:5]
    total_calculations = ROIResult.objects.filter(user=request.user).count()
    quick_calculations = ROIResult.objects.filter(user=request.user, mode='quick').count()
    full_calculations = ROIResult.objects.filter(user=request.user, mode='full').count()
    best_roi = ROIResult.objects.filter(user=request.user).order_by('-roi_percent').first()
    
    # Get user calculation limits
    user_limit = get_or_create_user_limit(request.user)
    is_admin = request.user.is_staff or request.user.is_superuser

    context = {
        'recent_results': recent_results,
        'total_calculations': total_calculations,
        'quick_calculations': quick_calculations,
        'full_calculations': full_calculations,
        'best_roi': best_roi,
        'user_limit': user_limit,
        'remaining_calculations': user_limit.get_remaining_free_calculations(),
        'is_admin': is_admin,
        'has_unlimited_access': user_limit.unlimited_access,
        'unlimited_access_purchased_at': user_limit.unlimited_access_purchased_at,
    }
    return render(request, 'calculator/dashboard_home.html', context)


@login_required
def quick_estimate(request):
    # Default values
    annual_revenue = int(request.GET.get('annualRevenue', 100000000))
    annual_cloud_spend = int(request.GET.get('annualCloudSpend', 10000000))
    num_engineers = int(request.GET.get('numEngineers', 100))

    # Enhanced calculation logic from TypeScript version
    gross_margin = 80
    container_app_fraction = 90
    compute_spend_fraction = 60
    cost_sensitive_fraction = 50
    engineer_cost_per_year = 150000
    ops_time_fraction = 15
    ops_toil_fraction = 50
    toil_reduction_fraction = 45
    avg_response_time_sec = 2
    exec_time_influence_fraction = 33
    lat_red_container = 28
    lat_red_serverless = 50
    revenue_lift_per_100ms = 1
    current_fci_fraction = 2
    fci_reduction_fraction = 75
    cost_per_1pct_fci = 1

    # Calculate cloud savings
    compute_spend = annual_cloud_spend * (compute_spend_fraction / 100)
    cost_sensitive_spend = compute_spend * (cost_sensitive_fraction / 100)
    cloud_savings = cost_sensitive_spend * ((container_app_fraction / 100) * 0.5 + (1 - container_app_fraction / 100) * 0.2)

    # Calculate productivity gain
    productivity_gain = num_engineers * engineer_cost_per_year * (ops_time_fraction / 100) * (ops_toil_fraction / 100) * (toil_reduction_fraction / 100)

    # Calculate performance gain
    weighted_lat_red = (container_app_fraction / 100) * (lat_red_container / 100) + (1 - container_app_fraction / 100) * (lat_red_serverless / 100)
    time_saved_sec = avg_response_time_sec * weighted_lat_red
    rev_gain_pct = (time_saved_sec / 0.1) * (revenue_lift_per_100ms / 100)
    performance_gain = annual_revenue * rev_gain_pct * (gross_margin / 100) * (exec_time_influence_fraction / 100)

    # Calculate availability gain
    fci_cost_fraction = (cost_per_1pct_fci / 100) * ((current_fci_fraction / 100) / 0.01)
    fci_cost = annual_revenue * fci_cost_fraction * (gross_margin / 100)
    availability_gain = fci_cost * (fci_reduction_fraction / 100)

    # Calculate total results
    total_annual_gain = cloud_savings + productivity_gain + performance_gain + availability_gain
    estimated_cost = total_annual_gain / 10
    roi_percent = (total_annual_gain / estimated_cost) * 100
    payback_months = (12 * estimated_cost) / total_annual_gain

    context = {
        "annual_revenue": annual_revenue,
        "annual_cloud_spend": annual_cloud_spend,
        "num_engineers": num_engineers,
        "total_annual_gain": total_annual_gain,
        "roi_percent": roi_percent,
        "payback_months": payback_months,
        "cloud_savings": cloud_savings,
    }
    return render(request, "calculator/quick_estimate.html", context)


@login_required
def full_calculator(request):
    # Check if user can make calculation
    user_limit = get_or_create_user_limit(request.user)
    
    # Check for payment success messages
    if request.GET.get('payment_success') == 'true':
        if request.GET.get('unlimited_access') == 'true' and user_limit.unlimited_access:
            messages.success(request, '🎉 Payment successful! You now have unlimited access to the Full Calculator!')
        else:
            messages.success(request, '🎉 Payment successful! You can now make additional calculations.')
    
    if not user_limit.can_make_calculation():
        # User has exceeded free limit, redirect to payment page
        messages.warning(request, 'You have used all 5 free calculations. Please make a payment to continue.')
        return redirect('payment_required')
    
    if request.method == 'POST':
        form = FullCalculatorForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            result = calculate_roi(data, mode='full')

            # Check if this calculation requires payment
            payment_required = not user_limit.can_make_calculation()
            
            roi_result = ROIResult.objects.create(
                user=request.user,
                mode='full',
                annual_revenue=data['annual_revenue'],
                gross_margin=data['gross_margin'],
                container_app_fraction=data['container_app_fraction'],
                annual_cloud_spend=data['annual_cloud_spend'],
                compute_spend_fraction=data['compute_spend_fraction'],
                cost_sensitive_fraction=data['cost_sensitive_fraction'],
                num_engineers=data['num_engineers'],
                engineer_cost_per_year=data['engineer_cost_per_year'],
                ops_time_fraction=data['ops_time_fraction'],
                ops_toil_fraction=data['ops_toil_fraction'],
                toil_reduction_fraction=data['toil_reduction_fraction'],
                avg_response_time_sec=data['avg_response_time_sec'],
                exec_time_influence_fraction=data['exec_time_influence_fraction'],
                lat_red_container=data['lat_red_container'],
                lat_red_serverless=data['lat_red_serverless'],
                revenue_lift_per_100ms=data['revenue_lift_per_100ms'],
                current_fci_fraction=data['current_fci_fraction'],
                fci_reduction_fraction=data['fci_reduction_fraction'],
                cost_per_1pct_fci=data['cost_per_1pct_fci'],
                # Results
                cloud_savings=result['cloud_savings'],
                productivity_gain=result['productivity_gain'],
                performance_gain=result['performance_gain'],
                availability_gain=result['availability_gain'],
                total_annual_gain=result['total_annual_gain'],
                roi_percent=result['roi_percent'],
                payback_months=result['payback_months'],
                # Payment tracking
                payment_required=payment_required,
                payment_completed=not payment_required,  # If no payment required, mark as completed
            )
            
            # Increment calculation count
            user_limit.increment_calculation_count()
            
            if payment_required:
                messages.warning(request, 'Calculation completed, but payment is required to view results.')
                return redirect('payment_required')
            else:
                messages.success(request, 'Full calculator calculation saved successfully!')
                return render(request, 'calculator/full_calculator.html', {'form': form, 'result': result})
    else:
        form = FullCalculatorForm()
    
    # Add user limit info to context
    context = {
        'form': form,
        'user_limit': user_limit,
        'remaining_calculations': user_limit.get_remaining_free_calculations(),
        'is_admin': request.user.is_staff or request.user.is_superuser,
        'has_unlimited_access': user_limit.unlimited_access,
        'unlimited_access_purchased_at': user_limit.unlimited_access_purchased_at,
    }
    return render(request, 'calculator/full_calculator.html', context)


@login_required
def results(request):
    results = ROIResult.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'calculator/results.html', {'results': results})


@login_required
@require_POST
def delete_result(request, result_id):
    result = get_object_or_404(ROIResult, id=result_id, user=request.user)
    result.delete()
    messages.success(request, 'Calculation deleted successfully!')
    return redirect('results')


@login_required
@require_POST
def delete_all_results(request):
    count = ROIResult.objects.filter(user=request.user).count()
    ROIResult.objects.filter(user=request.user).delete()
    messages.success(request, f'{count} calculation(s) deleted successfully!')
    return redirect('results')


@require_POST
@login_required
def save_quick_results(request):
    """Save quick calculator results"""
    try:
        data = json.loads(request.body)
        inputs = data.get('inputs', {})
        results = data.get('results', {})
        
        # Create ROIResult object
        roi_result = ROIResult.objects.create(
            user=request.user,
            mode='quick',
            annual_revenue=inputs.get('annualRevenue', 0),
            annual_cloud_spend=inputs.get('annualCloudSpend', 0),
            num_engineers=inputs.get('numEngineers', 0),
            total_annual_gain=results.get('totalAnnualGain', 0),
            roi_percent=results.get('roiPercent', 0),
            payback_months=results.get('paybackMonths', 0),
            cloud_savings=results.get('cloudSavings', 0),
            productivity_gain=results.get('productivityGain', 0),
            performance_gain=results.get('performanceGain', 0),
            availability_gain=results.get('availabilityGain', 0),
            # Set default values for required fields
            gross_margin=80,
            container_app_fraction=90,
            compute_spend_fraction=60,
            cost_sensitive_fraction=50,
            engineer_cost_per_year=150000,
            ops_time_fraction=15,
            ops_toil_fraction=50
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Results saved successfully!',
            'result_id': roi_result.id
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error saving results: {str(e)}'
        }, status=400)


@require_POST
@login_required
def save_full_results(request):
    """Save full calculator results"""
    try:
        data = json.loads(request.body)
        inputs = data.get('inputs', {})
        # Extract all the values from the full calculator
        annual_revenue = inputs.get('annualRevenue', 0)
        gross_margin = inputs.get('grossMargin', 80)
        container_app_fraction = inputs.get('containerAppFraction', 90)
        annual_cloud_spend = inputs.get('annualCloudSpend', 0)
        compute_spend_fraction = inputs.get('computeSpendFraction', 60)
        cost_sensitive_fraction = inputs.get('costSensitiveFraction', 50)
        num_engineers = inputs.get('numEngineers', 0)
        engineer_cost_per_year = inputs.get('engineerCostPerYear', 150000)
        ops_time_fraction = inputs.get('opsTimeFraction', 15)
        ops_toil_fraction = inputs.get('opsToilFraction', 50)
        avg_response_time_sec = inputs.get('avgResponseTimeSec', 2)
        revenue_lift_per_100ms = inputs.get('revenueLiftPer100ms', 1)
        current_fci_fraction = inputs.get('currentFCIFraction', 2)
        cost_per_1pct_fci = inputs.get('costPer1PctFCI', 1)
        toil_reduction_fraction = inputs.get('toilReductionFraction', 45)
        exec_time_influence_fraction = inputs.get('execTimeInfluenceFraction', 33)
        lat_red_container = inputs.get('latRedContainer', 28)
        lat_red_serverless = inputs.get('latRedServerless', 50)
        fci_reduction_fraction = inputs.get('fciReductionFraction', 75)
        
        # Get calculated results
        results = data.get('results', {})
        
        # Get user limit and check if they can make calculation
        user_limit = get_or_create_user_limit(request.user)
        
        # Create ROIResult object
        roi_result = ROIResult.objects.create(
            user=request.user,
            mode='full',
            annual_revenue=annual_revenue,
            gross_margin=gross_margin,
            container_app_fraction=container_app_fraction,
            annual_cloud_spend=annual_cloud_spend,
            compute_spend_fraction=compute_spend_fraction,
            cost_sensitive_fraction=cost_sensitive_fraction,
            num_engineers=num_engineers,
            engineer_cost_per_year=engineer_cost_per_year,
            ops_time_fraction=ops_time_fraction,
            ops_toil_fraction=ops_toil_fraction,
            toil_reduction_fraction=toil_reduction_fraction,
            avg_response_time_sec=avg_response_time_sec,
            exec_time_influence_fraction=exec_time_influence_fraction,
            lat_red_container=lat_red_container,
            lat_red_serverless=lat_red_serverless,
            revenue_lift_per_100ms=revenue_lift_per_100ms,
            current_fci_fraction=current_fci_fraction,
            fci_reduction_fraction=fci_reduction_fraction,
            cost_per_1pct_fci=cost_per_1pct_fci,
            # Results
            cloud_savings=results.get('cloudSavings', 0),
            productivity_gain=results.get('productivityGain', 0),
            performance_gain=results.get('performanceGain', 0),
            availability_gain=results.get('availabilityGain', 0),
            total_annual_gain=results.get('totalAnnualGain', 0),
            roi_percent=results.get('roiPercent', 0),
            payback_months=results.get('paybackMonths', 0),
        )
        
        # Increment calculation count (this was missing!)
        user_limit.increment_calculation_count()
        
        # Prepare response message based on user type
        is_admin = request.user.is_staff or request.user.is_superuser
        remaining = user_limit.get_remaining_free_calculations()
        # Convert Infinity to a JSON-safe value
        if remaining == float('inf'):
            remaining_calculations = "unlimited"
        else:
            remaining_calculations = remaining

        if is_admin:
            message = 'Full calculator results saved successfully! (Admin: Unlimited calculations)'
        else:
            message = f'Full calculator results saved successfully! ({remaining_calculations} free calculations remaining)'

        return JsonResponse({
            'success': True,
            'message': message,
            'result_id': roi_result.id,
            'remaining_calculations': remaining_calculations,
            'is_admin': is_admin
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error saving results: {str(e)}'
        }, status=400)


def calculate_roi(data, mode='quick'):
    """
    ROI calculation for both Quick and Full modes
    - Quick mode uses default values
    - Full mode uses form-provided values
    """

    # Common inputs
    annual_revenue = data['annual_revenue']
    annual_cloud_spend = data['annual_cloud_spend']
    num_engineers = data['num_engineers']

    if mode == 'quick':
        # Defaults for Quick Estimate Mode
        gross_margin = 80
        container_app_fraction = 90
        compute_spend_fraction = 60
        cost_sensitive_fraction = 50
        engineer_cost_per_year = 150_000
        ops_time_fraction = 15
        ops_toil_fraction = 50
        toil_reduction_fraction = 45
        avg_response_time_sec = 2
        exec_time_influence_fraction = 33
        lat_red_container = 28
        lat_red_serverless = 50
        revenue_lift_per_100ms = 1
        current_fci_fraction = 2
        fci_reduction_fraction = 75
        cost_per_1pct_fci = 1

    else:  # Full Calculator Mode
        gross_margin = data['gross_margin']
        container_app_fraction = data['container_app_fraction']
        compute_spend_fraction = data['compute_spend_fraction']
        cost_sensitive_fraction = data['cost_sensitive_fraction']
        engineer_cost_per_year = data['engineer_cost_per_year']
        ops_time_fraction = data['ops_time_fraction']
        ops_toil_fraction = data['ops_toil_fraction']
        toil_reduction_fraction = data['toil_reduction_fraction']
        avg_response_time_sec = data['avg_response_time_sec']
        exec_time_influence_fraction = data['exec_time_influence_fraction']
        lat_red_container = data['lat_red_container']
        lat_red_serverless = data['lat_red_serverless']
        revenue_lift_per_100ms = data['revenue_lift_per_100ms']
        current_fci_fraction = data['current_fci_fraction']
        fci_reduction_fraction = data['fci_reduction_fraction']
        cost_per_1pct_fci = data['cost_per_1pct_fci']

    # === ROI BUSINESS LOGIC (from calculate_quick_roi) ===
    compute_spend = annual_cloud_spend * (compute_spend_fraction / 100)
    cost_sensitive_spend = compute_spend * (cost_sensitive_fraction / 100)
    cloud_savings = cost_sensitive_spend * (
        (container_app_fraction / 100) * 0.5 +
        (1 - container_app_fraction / 100) * 0.2
    )

    productivity_gain = (
        num_engineers * engineer_cost_per_year *
        (ops_time_fraction / 100) *
        (ops_toil_fraction / 100) *
        (toil_reduction_fraction / 100)
    )

    weighted_lat_red = (
        (container_app_fraction / 100) * (lat_red_container / 100) +
        (1 - container_app_fraction / 100) * (lat_red_serverless / 100)
    )
    time_saved_sec = avg_response_time_sec * weighted_lat_red
    rev_gain_pct = (time_saved_sec / 0.1) * (revenue_lift_per_100ms / 100)

    performance_gain = (
        annual_revenue * rev_gain_pct *
        (gross_margin / 100) *
        (exec_time_influence_fraction / 100)
    )

    fci_cost_fraction = (cost_per_1pct_fci / 100) * ((current_fci_fraction / 100) / 0.01)
    fci_cost = annual_revenue * fci_cost_fraction * (gross_margin / 100)
    availability_gain = fci_cost * (fci_reduction_fraction / 100)

    total_annual_gain = cloud_savings + productivity_gain + performance_gain + availability_gain
    estimated_cost = annual_cloud_spend / 10   # React version
    roi_percent = (total_annual_gain / (estimated_cost + (num_engineers * engineer_cost_per_year))) * 100
    payback_months = (12 * estimated_cost) / total_annual_gain if total_annual_gain > 0 else 0

    return {
        'cloud_savings': round(cloud_savings, 2),
        'productivity_gain': round(productivity_gain, 2),
        'performance_gain': round(performance_gain, 2),
        'availability_gain': round(availability_gain, 2),
        'total_annual_gain': round(total_annual_gain, 2),
        'roi_percent': round(roi_percent, 2),
        'payback_months': round(payback_months, 1),
    }


def custom_logout(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out!')
    return redirect('landing')


def get_or_create_user_limit(user):
    """Get or create UserCalculationLimit for a user"""
    limit, created = UserCalculationLimit.objects.get_or_create(user=user)
    return limit


@login_required
def payment_required(request):
    """Show payment required page"""
    user_limit = get_or_create_user_limit(request.user)
    remaining = user_limit.get_remaining_free_calculations()
    
    context = {
        'remaining_calculations': remaining,
        'total_used': user_limit.full_calculations_used,
        'is_admin': request.user.is_staff or request.user.is_superuser,
    }
    return render(request, 'calculator/payment_required.html', context)


@login_required
def create_payment(request):
    """Create a payment order for Razorpay"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
    try:
        # Check if user can make calculation
        user_limit = get_or_create_user_limit(request.user)
        if user_limit.can_make_calculation():
            return JsonResponse({'error': 'You still have free calculations remaining'}, status=400)
        
        # Create payment record
        payment = Payment.objects.create(
            user=request.user,
            amount=Decimal('1.00'),
            currency='INR',
            payment_id=str(uuid.uuid4()),
            status='pending'
        )
        
        # Get Razorpay configuration
        razorpay_key_id = getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_demo_key')
        razorpay_payment_button_id = getattr(settings, 'RAZORPAY_PAYMENT_BUTTON_ID', 'pl_RDhRAQjOTNv1Jm')
        
        # Create success URL for redirect after payment
        success_url = request.build_absolute_uri(f'/dashboard/payment/success/?payment_id={payment.payment_id}')
        
        # Return payment details for frontend with your payment button
        return JsonResponse({
            'success': True,
            'payment_id': payment.payment_id,
            'amount': float(payment.amount),
            'currency': payment.currency,
            'key': razorpay_key_id,
            'payment_button_id': razorpay_payment_button_id,
            'success_url': success_url,
            'user_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
            'user_email': request.user.email or '',
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def verify_payment(request):
    """Verify payment completion"""
    import sys
    import traceback
    try:
        print("[verify_payment] Raw request body:", request.body)
        data = json.loads(request.body)
        print("[verify_payment] Parsed data:", data)
        payment_id = data.get('payment_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')

        print(f"[verify_payment] payment_id: {payment_id}, razorpay_payment_id: {razorpay_payment_id}, razorpay_signature: {razorpay_signature}")

        if not all([payment_id, razorpay_payment_id, razorpay_signature]):
            print("[verify_payment] Missing payment data")
            return JsonResponse({'error': 'Missing payment data'}, status=400)

        # Get payment record
        try:
            payment = Payment.objects.get(
                payment_id=payment_id,
                user=request.user,
                status='pending'
            )
        except Payment.DoesNotExist:
            print(f"[verify_payment] Payment not found for payment_id={payment_id}, user={request.user}")
            return JsonResponse({'error': 'Payment not found'}, status=404)

        print(f"[verify_payment] Found payment: {payment}")

        # For demo purposes, we'll simulate successful verification
        # In production, you would verify with Razorpay
        payment.status = 'completed'
        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.paid_at = timezone.now()

        # Fix for Djongo/MongoDB Decimal128 issue
        from decimal import Decimal
        try:
            # If amount is Decimal128, convert to string then Decimal
            if hasattr(payment.amount, 'to_decimal'):
                print(f"[verify_payment] Converting Decimal128 to Decimal: {payment.amount}")
                payment.amount = Decimal(str(payment.amount.to_decimal()))
            elif not isinstance(payment.amount, Decimal):
                print(f"[verify_payment] Converting amount to Decimal: {payment.amount}")
                payment.amount = Decimal(str(payment.amount))
        except Exception as conv_exc:
            print(f"[verify_payment] Error converting amount: {conv_exc}")
            traceback.print_exc()
            payment.amount = Decimal('1.00')  # fallback

        try:
            payment.save()
            print("[verify_payment] Payment saved successfully.")
        except Exception as save_exc:
            print(f"[verify_payment] Error saving payment: {save_exc}")
            traceback.print_exc()
            return JsonResponse({'error': f'Error saving payment: {str(save_exc)}'}, status=500)

        # Grant unlimited access to the user
        try:
            user_limit = get_or_create_user_limit(request.user)
            user_limit.grant_unlimited_access()
            print("[verify_payment] Unlimited access granted.")
        except Exception as grant_exc:
            print(f"[verify_payment] Error granting unlimited access: {grant_exc}")
            traceback.print_exc()
            return JsonResponse({'error': f'Error granting unlimited access: {str(grant_exc)}'}, status=500)

        return JsonResponse({
            'success': True,
            'message': 'Payment verified successfully! You now have unlimited access to the Full Calculator.',
            'payment_id': payment.payment_id,
            'unlimited_access': True
        })

    except Exception as e:
        print(f"[verify_payment] Exception: {e}")
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def payment_success(request):
    """Payment success page - redirects to full calculator after successful payment"""
    payment_id = request.GET.get('payment_id')
    razorpay_payment_id = request.GET.get('razorpay_payment_id')
    razorpay_signature = request.GET.get('razorpay_signature')
    
    if payment_id:
        try:
            payment = Payment.objects.get(payment_id=payment_id, user=request.user)
            
            # If payment is still pending and we have Razorpay data, verify it
            if payment.status == 'pending' and razorpay_payment_id and razorpay_signature:
                # Update payment status to completed
                payment.status = 'completed'
                payment.razorpay_payment_id = razorpay_payment_id
                payment.razorpay_signature = razorpay_signature
                payment.paid_at = timezone.now()
                payment.save()
                
                # Grant unlimited access to the user
                user_limit = get_or_create_user_limit(request.user)
                user_limit.grant_unlimited_access()
                
                # Redirect to full calculator with success message
                messages.success(request, '🎉 Payment successful! You now have unlimited access to the Full Calculator.')
                return redirect('full_calculator')
            
            # If payment is already completed, just redirect
            elif payment.status == 'completed':
                user_limit = get_or_create_user_limit(request.user)
                if user_limit.unlimited_access:
                    messages.success(request, '🎉 Payment successful! You now have unlimited access to the Full Calculator.')
                else:
                    messages.warning(request, 'Payment completed but unlimited access not yet activated. Please try again.')
                return redirect('full_calculator')
            
            # If payment is still pending without Razorpay data, show success page
            else:
                messages.warning(request, 'Payment is being processed. Please wait a moment.')
                return redirect('full_calculator')
                
        except Payment.DoesNotExist:
            messages.error(request, 'Payment not found.')
            return redirect('full_calculator')
    else:
        messages.error(request, 'No payment ID provided.')
        return redirect('full_calculator')


@login_required
def payment_failure(request):
    """Payment failure page"""
    return render(request, 'calculator/payment_failure.html')


@csrf_exempt
def razorpay_webhook(request):
    """Handle Razorpay webhook for payment verification"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Get webhook data
        webhook_data = json.loads(request.body)
        event_type = webhook_data.get('event')
        
        if event_type == 'payment.captured':
            # Payment was successful
            payment_data = webhook_data.get('payload', {}).get('payment', {})
            razorpay_payment_id = payment_data.get('entity', {}).get('id')
            amount = payment_data.get('entity', {}).get('amount')
            # Ensure amount is a Decimal for model compatibility
            from decimal import Decimal, InvalidOperation
            try:
                if amount is not None:
                    # Razorpay may send amount in paise (int/str), convert to rupees if needed
                    if isinstance(amount, str):
                        amount = Decimal(amount)
                    elif isinstance(amount, (int, float)):
                        amount = Decimal(str(amount))
            except InvalidOperation:
                amount = Decimal('0.00')
            
            # Find the payment record by Razorpay payment ID
            try:
                payment = Payment.objects.get(
                    razorpay_payment_id=razorpay_payment_id,
                    status='pending'
                )
                
                # Update payment status
                payment.status = 'completed'
                payment.amount = amount
                payment.paid_at = timezone.now()
                payment.save()
                
                # Grant unlimited access
                user_limit = get_or_create_user_limit(payment.user)
                user_limit.grant_unlimited_access()
                
                return JsonResponse({'status': 'success'})
                
            except Payment.DoesNotExist:
                return JsonResponse({'error': 'Payment not found'}, status=404)
        
        return JsonResponse({'status': 'ignored'})
        
    except Exception as e:
        
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def payment_history(request):
    """Show user's payment history"""
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')
    user_limit = get_or_create_user_limit(request.user)
    
    context = {
        'payments': payments,
        'user_limit': user_limit,
        'remaining_calculations': user_limit.get_remaining_free_calculations(),
    }
    return render(request, 'calculator/payment_history.html', context)


@login_required
@require_POST
@csrf_exempt
def chatbot_api(request):
    """Handle chatbot API requests with OpenAI integration"""
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({
                'success': False,
                'error': 'Message cannot be empty'
            }, status=400)
        
        # Initialize Google Gemini
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            return JsonResponse({
                'success': False,
                'error': 'Gemini API key not configured'
            }, status=500)
        
        # Configure Gemini
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Failed to initialize Gemini: {str(e)}'
            }, status=500)
        
        # Create a context-aware prompt for ROI calculator assistance
        system_prompt = """ROI Calculator Input Categories and Default Values:

BUSINESS INPUTS:
- annualRevenue: $100,000,000 (Annual company revenue)
- grossMargin: 80% (Company's gross profit margin)
- containerAppFraction: 90% (Percentage of applications that are containerized)
- annualCloudSpend: $10,000,000 (Total annual cloud infrastructure spending)
- computeSpendFraction: 60% (Percentage of cloud spend on compute resources)
- costSensitiveFraction: 50% (Percentage of compute spend that is cost-sensitive)

PRODUCTIVITY INPUTS:
- numEngineers: 100 (Number of engineers in the team)
- engineerCostPerYear: $150,000 (Annual cost per engineer including salary and benefits)
- opsTimeFraction: 15% (Percentage of engineering time spent on operations)
- opsToilFraction: 50% (Percentage of ops time spent on repetitive tasks/toil)
- toilReductionFraction: 45% (Expected reduction in toil through automation - fixed)

PERFORMANCE INPUTS:
- avgResponseTimeSec: 2 seconds (Current average application response time)
- execTimeInfluenceFraction: 33% (Percentage of revenue influenced by execution time - fixed)
- latRedContainer: 28% (Latency reduction for containerized apps - fixed)
- latRedServerless: 50% (Latency reduction for serverless apps - fixed)
- revenueLiftPer100ms: 1% (Revenue increase per 100ms response time improvement)

AVAILABILITY INPUTS:
- currentFCIFraction: 2% (Current Failure Cost Index as percentage of revenue)
- fciReductionFraction: 75% (Expected reduction in failure costs - fixed)
- costPer1PctFCI: 1% (Cost per 1% of FCI)

CALCULATION FORMULAS:

1. Cloud Savings:
   computeSpend = annualCloudSpend * (computeSpendFraction / 100)
   costSensitiveSpend = computeSpend * (costSensitiveFraction / 100)
   cloudSavings = costSensitiveSpend * ((containerAppFraction / 100) * 0.5 + (1 - containerAppFraction / 100) * 0.2)

2. Productivity Gain:
   productivityGain = numEngineers * engineerCostPerYear * (opsTimeFraction / 100) * (opsToilFraction / 100) * (toilReductionFraction / 100)

3. Performance Gain:
   weightedLatRed = (containerAppFraction / 100) * (latRedContainer / 100) + (1 - containerAppFraction / 100) * (latRedServerless / 100)
   timeSavedSec = avgResponseTimeSec * weightedLatRed
   revGainPct = (timeSavedSec / 0.1) * (revenueLiftPer100ms / 100)
   performanceGain = annualRevenue * revGainPct * (grossMargin / 100) * (execTimeInfluenceFraction / 100)

4. Availability Gain:
   fciCostFraction = (costPer1PctFCI / 100) * (currentFCIFraction / 100 / 0.01)
   fciCost = annualRevenue * fciCostFraction * (grossMargin / 100)
   availabilityGain = fciCost * (fciReductionFraction / 100)

5. Total Calculations:

   totalAnnualGain = cloudSavings + productivityGain + performanceGain + availabilityGain
   estimatedCost = Math.max(annualCloudSpend * 0.1, numEngineers * engineerCostPerYear * 0.05, annualRevenue * 0.005)
   roiPercent = (totalAnnualGain / (totalAnnualGain/10 + engineerCostPerYear))*100;
   paybackMonths = (12 * estimatedCost) / totalAnnualGain

The calculator estimates the ROI by calculating potential savings and gains across four key areas: cloud infrastructure optimization, engineering productivity improvements, application performance enhancements, and system availability improvements."""
        
        # Create the full prompt
        full_prompt = f"{system_prompt}\n\nUser question: {user_message}"
        
        # Make API call to Gemini
        try:
            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=500,
                    temperature=0.7,
                )
            )
            bot_response = response.text
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Failed to generate response: {str(e)}'
            }, status=500)
        
        return JsonResponse({
            'success': True,
            'response': bot_response,
            'timestamp': timezone.now().isoformat()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@login_required
def chatbot_view(request):
    """Render the chatbot interface"""
    return render(request, 'calculator/chatbot.html')


@login_required
def export_pdf(request, result_id):
    """Export ROI result as PDF report"""
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from io import BytesIO
    from django.http import HttpResponse
    import datetime
    
    # Get the result
    result = get_object_or_404(ROIResult, id=result_id, user=request.user)
    
    # Create response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="ROI_Report_{result.user.username}_{result.timestamp.strftime("%Y%m%d_%H%M")}.pdf"'
    
    # Create PDF buffer
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#2E86AB')
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#A23B72')
    )
    
    section_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.HexColor('#2E86AB')
    )
    
    # Build the story (content)
    story = []
    
    # Page 1: Card-style layout matching the results page
    # Header
    current_time = datetime.datetime.now().strftime("%m/%d/%y, %I:%M %p")
    story.append(Paragraph(f"{current_time}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Main title
    story.append(Paragraph("My ROI Results", title_style))
    story.append(Paragraph("View and compare your saved calculations", subtitle_style))
    story.append(Spacer(1, 30))
    
    # Card-style container for the result
    # Card header with calculation type and timestamp
    card_header_data = [
        [f"{'Quick Estimate' if result.mode == 'quick' else 'Full Calculator'}", f"${result.total_annual_gain:,.0f}M"],
        [f"{result.timestamp.strftime('%b %d, %Y %H:%M')}", "Total Gain"]
    ]
    
    card_header_table = Table(card_header_data, colWidths=[4*inch, 2*inch])
    card_header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F8F9FA')),
        ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#E3F2FD')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (0, 0), 14),
        ('FONTSIZE', (1, 0), (1, 0), 16),
        ('FONTSIZE', (0, 1), (-1, 1), 10),
        ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
        ('TEXTCOLOR', (1, 0), (1, 0), colors.HexColor('#1976D2')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E0E0E0'))
    ]))
    
    story.append(card_header_table)
    story.append(Spacer(1, 20))
    
    # Key Metrics section (ROI and Payback)
    story.append(Paragraph("Key Metrics", section_style))
    metrics_data = [
        [f"{result.roi_percent:.0f}%", f"{result.payback_months:.1f} mo"],
        ["ROI", "Payback"]
    ]
    
    metrics_table = Table(metrics_data, colWidths=[3*inch, 3*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#E3F2FD')),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#E8F5E8')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (1, 0), 16),
        ('FONTSIZE', (0, 1), (1, 1), 10),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#1976D2')),
        ('TEXTCOLOR', (1, 0), (1, 0), colors.HexColor('#2E7D32')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E0E0E0'))
    ]))
    
    story.append(metrics_table)
    story.append(Spacer(1, 20))
    
    # Breakdown section (matching the card layout)
    story.append(Paragraph("Breakdown", section_style))
    breakdown_data = [
        [f"${result.cloud_savings:,.0f}M", f"${result.productivity_gain:,.0f}M"],
        ["Cloud", "Productivity"],
        [f"${result.performance_gain:,.0f}M", f"${result.availability_gain:,.0f}M"],
        ["Performance", "Availability"]
    ]
    
    breakdown_table = Table(breakdown_data, colWidths=[3*inch, 3*inch])
    breakdown_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#E3F2FD')),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#E8F5E8')),
        ('BACKGROUND', (0, 2), (0, 2), colors.HexColor('#FFF3E0')),
        ('BACKGROUND', (1, 2), (1, 2), colors.HexColor('#E1F5FE')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (1, 2), 14),
        ('FONTSIZE', (0, 1), (1, 3), 10),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#1976D2')),
        ('TEXTCOLOR', (1, 0), (1, 0), colors.HexColor('#2E7D32')),
        ('TEXTCOLOR', (0, 2), (0, 2), colors.HexColor('#F57C00')),
        ('TEXTCOLOR', (1, 2), (1, 2), colors.HexColor('#0277BD')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E0E0E0'))
    ]))
    
    story.append(breakdown_table)
    story.append(Spacer(1, 20))
    
    # Key Inputs section (matching the card layout)
    story.append(Paragraph("Key Inputs", section_style))
    inputs_data = [
        [f"${result.annual_revenue:,.0f}M", str(result.num_engineers), f"${result.annual_cloud_spend:,.0f}M"],
        ["Revenue", "Engineers", "Cloud Spend"]
    ]
    
    inputs_table = Table(inputs_data, colWidths=[2*inch, 2*inch, 2*inch])
    inputs_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F5F5F5')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('FONTSIZE', (0, 1), (-1, 1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E0E0E0'))
    ]))
    
    story.append(inputs_table)
    story.append(PageBreak())
    
    # Page 2: Additional Details and Summary
    story.append(Paragraph("Additional Details", section_style))
    
    # Additional input details
    additional_data = [
        ['Engineer Cost/Year:', f'${result.engineer_cost_per_year:,}'],
        ['Gross Margin:', f'{result.gross_margin:.0f}%'],
        ['Container App Fraction:', f'{result.container_app_fraction:.0f}%'],
        ['Compute Spend Fraction:', f'{result.compute_spend_fraction:.0f}%'],
        ['Cost Sensitive Fraction:', f'{result.cost_sensitive_fraction:.0f}%'],
        ['Ops Time Fraction:', f'{result.ops_time_fraction * 100:.0f}%'],
        ['Ops Toil Fraction:', f'{result.ops_toil_fraction * 100:.0f}%'],
        ['Response Time:', f'{result.avg_response_time_sec * 1000:.0f}ms' if result.avg_response_time_sec else 'N/A'],
        ['Current FCI Fraction:', f'{result.current_fci_fraction * 100:.0f}%' if result.current_fci_fraction else '5%']
    ]
    
    # Create additional details table
    additional_table_data = []
    for i in range(0, len(additional_data), 2):
        row = []
        if i < len(additional_data):
            row.extend(additional_data[i])
        else:
            row.extend(['', ''])
        if i + 1 < len(additional_data):
            row.extend(additional_data[i + 1])
        else:
            row.extend(['', ''])
        additional_table_data.append(row)
    
    additional_table = Table(additional_table_data, colWidths=[2.5*inch, 1.5*inch, 2.5*inch, 1.5*inch])
    additional_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8F9FA')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, 0), (1, -1), colors.HexColor('#E9ECEF')),
        ('BACKGROUND', (2, 0), (3, -1), colors.HexColor('#E9ECEF')),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#F8F9FA'), colors.white])
    ]))
    
    story.append(additional_table)
    story.append(Spacer(1, 30))
    
    # Summary section
    story.append(Paragraph("Summary", section_style))
    summary_text = f"""
    This ROI analysis shows that {result.user.username} can achieve significant financial benefits through cloud optimization. 
    The analysis indicates a total annual gain of <b>${result.total_annual_gain:,.0f}</b> with a return on investment of <b>{result.roi_percent:.1f}%</b>. 
    The payback period is estimated at <b>{result.payback_months:.1f} months</b>.
    
    The breakdown shows:
    • Cloud Savings: ${result.cloud_savings:,.0f}M
    • Productivity Gains: ${result.productivity_gain:,.0f}M  
    • Performance Gains: ${result.performance_gain:,.0f}M
    • Availability Gains: ${result.availability_gain:,.0f}M
    """
    story.append(Paragraph(summary_text, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Footer
    footer_text = f"Cloud ROI Calculator | Generated: {datetime.datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')} | Report ID: ROI-{int(datetime.datetime.now().timestamp() * 1000)}"
    story.append(Paragraph(footer_text, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    
    # Get PDF content
    pdf_content = buffer.getvalue()
    buffer.close()
    
    # Return PDF response
    response.write(pdf_content)
    return response




