from django.contrib import admin
from .models import ROIResult, Payment, UserCalculationLimit

# Register your models here.

@admin.register(ROIResult)
class ROIResultAdmin(admin.ModelAdmin):
    list_display = ['user', 'mode', 'roi_percent', 'total_annual_gain', 'payment_required', 'payment_completed', 'timestamp']
    list_filter = ['mode', 'payment_required', 'payment_completed', 'timestamp']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']
    
    fieldsets = (
        ('User & Mode', {
            'fields': ('user', 'mode', 'timestamp')
        }),
        ('Business Inputs', {
            'fields': ('annual_revenue', 'gross_margin', 'container_app_fraction', 'annual_cloud_spend', 'compute_spend_fraction', 'cost_sensitive_fraction')
        }),
        ('Productivity Inputs', {
            'fields': ('num_engineers', 'engineer_cost_per_year', 'ops_time_fraction', 'ops_toil_fraction', 'toil_reduction_fraction')
        }),
        ('Performance Inputs', {
            'fields': ('avg_response_time_sec', 'exec_time_influence_fraction', 'lat_red_container', 'lat_red_serverless', 'revenue_lift_per_100ms')
        }),
        ('Availability Inputs', {
            'fields': ('current_fci_fraction', 'fci_reduction_fraction', 'cost_per_1pct_fci')
        }),
        ('Results', {
            'fields': ('cloud_savings', 'productivity_gain', 'performance_gain', 'availability_gain', 'total_annual_gain', 'roi_percent', 'payback_months')
        }),
        ('Payment Status', {
            'fields': ('payment_required', 'payment_completed')
        }),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_id', 'user', 'amount', 'status', 'payment_method', 'created_at', 'paid_at']
    list_filter = ['status', 'payment_method', 'created_at', 'paid_at']
    search_fields = ['payment_id', 'user__username', 'user__email', 'razorpay_payment_id']
    readonly_fields = ['payment_id', 'created_at', 'updated_at', 'paid_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Payment Info', {
            'fields': ('payment_id', 'user', 'amount', 'currency', 'status', 'payment_method')
        }),
        ('Transaction Details', {
            'fields': ('transaction_id', 'razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'paid_at')
        }),
    )
    
    actions = ['mark_as_completed', 'mark_as_failed', 'mark_as_refunded']
    
    def mark_as_completed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='completed', paid_at=timezone.now())
        self.message_user(request, f'{updated} payments marked as completed.')
    mark_as_completed.short_description = "Mark selected payments as completed"
    
    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} payments marked as failed.')
    mark_as_failed.short_description = "Mark selected payments as failed"
    
    def mark_as_refunded(self, request, queryset):
        updated = queryset.update(status='refunded')
        self.message_user(request, f'{updated} payments marked as refunded.')
    mark_as_refunded.short_description = "Mark selected payments as refunded"


@admin.register(UserCalculationLimit)
class UserCalculationLimitAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_calculations_used', 'remaining_calculations', 'last_reset_date']
    list_filter = ['last_reset_date']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['last_reset_date']
    ordering = ['-last_reset_date']
    
    fieldsets = (
        ('User Info', {
            'fields': ('user',)
        }),
        ('Calculation Limits', {
            'fields': ('full_calculations_used', 'last_reset_date')
        }),
    )
    
    actions = ['reset_calculations', 'add_free_calculations']
    
    def remaining_calculations(self, obj):
        remaining = obj.get_remaining_free_calculations()
        if remaining == float('inf'):
            return "Unlimited (Admin)"
        return remaining
    remaining_calculations.short_description = "Remaining Free Calculations"
    
    def reset_calculations(self, request, queryset):
        updated = queryset.update(full_calculations_used=0)
        self.message_user(request, f'{updated} users\' calculation limits reset.')
    reset_calculations.short_description = "Reset calculation limits to 0"
    
    def add_free_calculations(self, request, queryset):
        for obj in queryset:
            obj.full_calculations_used = max(0, obj.full_calculations_used - 5)
            obj.save()
        self.message_user(request, f'Added 5 free calculations to {queryset.count()} users.')
    add_free_calculations.short_description = "Add 5 free calculations"
