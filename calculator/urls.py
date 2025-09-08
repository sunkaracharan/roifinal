from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    # Dashboard home (protected)
    path('', login_required(views.dashboard_home), name='dashboard_home'),
    
    # Calculator routes (all protected)
    path('quick/', login_required(views.quick_estimate), name='quick_estimate'),
    path('full/', login_required(views.full_calculator), name='full_calculator'),
    path('results/', login_required(views.results), name='results'),
    
    # Save quick results (protected)
    path('save-quick-results/', login_required(views.save_quick_results), name='save_quick_results'),
    
    # Save full results (protected)
    path('save-full-results/', login_required(views.save_full_results), name='save_full_results'),
    
    # Delete result (protected)
    path('results/delete/<int:result_id>/', login_required(views.delete_result), name='delete_result'),
    path('results/delete-all/', login_required(views.delete_all_results), name='delete_all_results'),
    
    # Export PDF (protected)
    path('results/export/<int:result_id>/', login_required(views.export_pdf), name='export_pdf'),
    
    # Payment routes (protected)
    path('payment-required/', login_required(views.payment_required), name='payment_required'),
    path('payment/create/', login_required(views.create_payment), name='create_payment'),
    path('payment/verify/', login_required(views.verify_payment), name='verify_payment'),
    path('payment/success/', login_required(views.payment_success), name='payment_success'),
    path('payment/failure/', login_required(views.payment_failure), name='payment_failure'),
    path('payment/history/', login_required(views.payment_history), name='payment_history'),
    
    # Razorpay webhook (not protected - external service)
    path('payment/webhook/', views.razorpay_webhook, name='razorpay_webhook'),
    
    # Chatbot routes (protected)
    path('chatbot/', login_required(views.chatbot_view), name='chatbot'),
    path('chatbot/api/', login_required(views.chatbot_api), name='chatbot_api'),
] 