from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("checkout/course/<int:course_id>/", views.create_checkout_session, name="checkout_course"),
    path("paynow/return/", views.paynow_return, name="paynow_return"),
    path("paynow/result/", views.paynow_result, name="paynow_result"),
    path("success/", views.success, name="success"),
    path("cancel/", views.cancel, name="cancel"),
]