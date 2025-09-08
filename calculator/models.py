from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

# Create your models here.

class ROIResult(models.Model):
    MODE_CHOICES = [
        ('quick', 'Quick Estimate'),
        ('full', 'Full Calculator'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    mode = models.CharField(max_length=32, choices=MODE_CHOICES)
    
    # Business inputs
    annual_revenue = models.BigIntegerField()
    gross_margin = models.FloatField()
    container_app_fraction = models.FloatField()
    annual_cloud_spend = models.BigIntegerField()
    compute_spend_fraction = models.FloatField()
    cost_sensitive_fraction = models.FloatField()
    
    # Productivity inputs
    num_engineers = models.IntegerField()
    engineer_cost_per_year = models.BigIntegerField()
    ops_time_fraction = models.FloatField()
    ops_toil_fraction = models.FloatField()
    toil_reduction_fraction = models.FloatField(null=True, blank=True)
    
    # Performance inputs
    avg_response_time_sec = models.FloatField(null=True, blank=True)
    exec_time_influence_fraction = models.FloatField(null=True, blank=True)
    lat_red_container = models.FloatField(null=True, blank=True)
    lat_red_serverless = models.FloatField(null=True, blank=True)
    revenue_lift_per_100ms = models.FloatField(null=True, blank=True)
    
    # Availability inputs
    current_fci_fraction = models.FloatField(null=True, blank=True)
    fci_reduction_fraction = models.FloatField(null=True, blank=True)
    cost_per_1pct_fci = models.FloatField(null=True, blank=True)
    
    # Results
    cloud_savings = models.FloatField()
    productivity_gain = models.FloatField()
    performance_gain = models.FloatField()
    availability_gain = models.FloatField()
    total_annual_gain = models.FloatField()
    roi_percent = models.FloatField()
    payback_months = models.FloatField()
    
    # Payment tracking
    payment_required = models.BooleanField(default=False)
    payment_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.get_mode_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        ordering = ['-timestamp']


class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('razorpay', 'Razorpay'),
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('manual', 'Manual'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    roi_result = models.ForeignKey(ROIResult, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    currency = models.CharField(max_length=3, default='INR')
    payment_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='razorpay')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Razorpay specific fields
    razorpay_order_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=200, null=True, blank=True)
    
    def __str__(self):
        return f"Payment {self.payment_id} - {self.user.username} - ₹{self.amount}"
    
    class Meta:
        ordering = ['-created_at']


class UserCalculationLimit(models.Model):
    """Track user's calculation limits and free trials"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_calculations_used = models.IntegerField(default=0)
    unlimited_access = models.BooleanField(default=False)  # Track if user has unlimited access
    unlimited_access_purchased_at = models.DateTimeField(null=True, blank=True)  # When unlimited access was purchased
    last_reset_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.full_calculations_used} calculations used"
    
    def get_remaining_free_calculations(self):
        """Get remaining free calculations (5 free for non-admin users)"""
        if self.user.is_staff or self.user.is_superuser:
            return float('inf')  # Unlimited for admin
        if self.unlimited_access:
            return float('inf')  # Unlimited for paid users
        return max(0, 5 - self.full_calculations_used)
    
    def can_make_calculation(self):
        """Check if user can make a calculation without payment"""
        if self.user.is_staff or self.user.is_superuser:
            return True
        if self.unlimited_access:
            return True  # Unlimited access users can always make calculations
        return self.full_calculations_used < 5
    
    def increment_calculation_count(self):
        """Increment the calculation count (skip for admin users and unlimited access users)"""
        if not (self.user.is_staff or self.user.is_superuser) and not self.unlimited_access:
            self.full_calculations_used += 1
            self.save()
    
    def grant_unlimited_access(self):
        """Grant unlimited access to the user"""
        self.unlimited_access = True
        self.unlimited_access_purchased_at = timezone.now()
        self.save()
    
    class Meta:
        ordering = ['-last_reset_date']
