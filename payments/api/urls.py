from django.urls import path
from .views import CheckoutAPIView, PaymentStatusAPIView

app_name = "payments_api"

urlpatterns = [
    path("checkout/", CheckoutAPIView.as_view(), name="checkout"),
    path("<int:pk>/status/", PaymentStatusAPIView.as_view(), name="status"),
]