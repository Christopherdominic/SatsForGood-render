from django.urls import path
from . import views

urlpatterns = [
    path('create-invoice/', views.create_invoice),
    path('invoice-status/<str:payment_hash>/', views.invoice_status),
    path('recent-donations/', views.recent_donations),
    path('donation-stats/', views.donation_stats),  # ✅ ADD THIS LINE
]
