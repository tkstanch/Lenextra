from decimal import Decimal
from typing import Optional

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from paynow import Paynow

from courses.models import Course
from payments.models import Payment
from payments.serializers import CheckoutRequestSerializer, PaymentSerializer
import stripe  # add
from django.views.decorators.csrf import csrf_exempt

stripe.api_key = getattr(settings, "STRIPE_SECRET_KEY", "")

def _paynow_client():
    result_url = f"{settings.SITE_URL}{reverse('payments:paynow_result')}"
    return_url = f"{settings.SITE_URL}{reverse('payments:paynow_return')}"
    return Paynow(settings.PAYNOW_INTEGRATION_ID, settings.PAYNOW_INTEGRATION_KEY, result_url, return_url)

def _enroll_and_mark_paid(payment: Payment, provider_status: Optional[str] = None):
    payment.status = "paid"
    if provider_status:
        payment.provider_status = provider_status
    payment.save(update_fields=["status", "provider_status", "updated_at"])
    # Unlock course
    try:
        if hasattr(payment.course, "students"):
            payment.course.students.add(payment.user)
    except Exception:
        pass

def _poll_and_update(payment: Payment) -> str:
    if not payment.poll_url:
        payment.status = "failed"
        payment.provider_status = "no_poll_url"
        payment.save(update_fields=["status", "provider_status"])
        return "failed"

    pn = _paynow_client()
    status_obj = pn.check_transaction_status(payment.poll_url)
    current = getattr(status_obj, "status", None) or str(status_obj)  # e.g., "Paid", "Sent", "Cancelled"
    payment.provider_status = current
    lc = (current or "").lower()
    if lc == "paid":
        _enroll_and_mark_paid(payment, provider_status=current)
        return "paid"
    elif lc in ("cancelled", "canceled", "failed"):
        payment.status = "failed"
        payment.save(update_fields=["status", "provider_status"])
        return "failed"
    else:
        payment.save(update_fields=["provider_status"])
        return "pending"

class CheckoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not getattr(settings, "PAYNOW_INTEGRATION_ID", "") or not getattr(settings, "PAYNOW_INTEGRATION_KEY", ""):
            return Response({"detail": "Paynow not configured"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        ser = CheckoutRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        course = get_object_or_404(Course, pk=ser.validated_data["course_id"])

        amount = getattr(course, "price", None) or Decimal("10.00")
        currency = getattr(course, "currency", "usd")

        payment = Payment.objects.create(
            user=request.user,
            course=course,
            amount=amount,
            currency=currency,
            status="pending",
            provider="paynow",
        )

        pn = _paynow_client()
        label = f"Course {getattr(course, 'title', None) or getattr(course, 'name', course.id)}"
        pn_payment = pn.create_payment(label, request.user.email or "noemail@example.com")
        pn_payment.add(label, float(amount))

        phone = ser.validated_data.get("phone") or ""
        method = ser.validated_data.get("method") or "ecocash"

        if phone:
            # Mobile money (STK push)
            response = pn.send_mobile(pn_payment, phone, method)
        else:
            # Web checkout
            response = pn.send(pn_payment)

        if not response.success:
            payment.status = "failed"
            payment.provider_status = "init_failed"
            payment.save(update_fields=["status", "provider_status"])
            return Response({"detail": "Failed to initiate payment"}, status=status.HTTP_400_BAD_REQUEST)

        payment.poll_url = response.poll_url
        payment.provider_reference = getattr(response, "reference", None)
        payment.save(update_fields=["poll_url", "provider_reference"])

        data = {
            "payment": PaymentSerializer(payment).data,
            "next_action": {
                "type": "redirect" if not phone else "await_stk",
                "redirect_url": getattr(response, "redirect_url", None),
                "instructions": getattr(response, "instructions", None),  # for mobile, if provided
            },
        }
        return Response(data, status=status.HTTP_201_CREATED)

class PaymentStatusAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk: int):
        payment = get_object_or_404(Payment, pk=pk, user=request.user)
        state = _poll_and_update(payment) if payment.status != "paid" else "paid"
        enrolled = False
        try:
            enrolled = hasattr(payment.course, "students") and payment.course.students.filter(id=request.user.id).exists()
        except Exception:
            enrolled = False
        return Response({
            "payment": PaymentSerializer(payment).data,
            "state": state,
            "enrolled": enrolled,
        })

@login_required
def create_checkout_session(request, course_id: int):
    course = get_object_or_404(Course, pk=course_id)
    amount = getattr(course, "price", None) or Decimal("10.00")
    currency = getattr(course, "currency", "usd")
    provider = request.GET.get("provider") or ("stripe" if getattr(settings, "STRIPE_SECRET_KEY", "") else "paynow")

    payment = Payment.objects.create(
        user=request.user,
        course=course,
        amount=amount,
        currency=currency,
        status="pending",
        provider=provider,
    )

    if provider == "stripe":
        if not getattr(settings, "STRIPE_SECRET_KEY", ""):
            payment.status = "failed"
            payment.provider_status = "stripe_not_configured"
            payment.save(update_fields=["status", "provider_status"])
            return HttpResponseBadRequest("Stripe not configured")
        redirect_url = _create_stripe_checkout(payment, course, request.user.email or None)
        return HttpResponseRedirect(redirect_url)

    # Paynow web checkout
    if not getattr(settings, "PAYNOW_INTEGRATION_ID", "") or not getattr(settings, "PAYNOW_INTEGRATION_KEY", ""):
        payment.status = "failed"
        payment.provider_status = "paynow_not_configured"
        payment.save(update_fields=["status", "provider_status"])
        return HttpResponseBadRequest("Paynow not configured")

    pn = _paynow_client()
    label = f"Course {getattr(course, 'title', None) or getattr(course, 'name', course.id)}"
    pn_payment = pn.create_payment(label, request.user.email or "noemail@example.com")
    pn_payment.add(label, float(amount))
    response = pn.send(pn_payment)

    if not response.success:
        payment.status = "failed"
        payment.provider_status = "init_failed"
        payment.save(update_fields=["status", "provider_status"])
        return HttpResponseBadRequest("Failed to initiate Paynow payment")

    payment.poll_url = response.poll_url
    payment.provider_reference = getattr(response, "reference", None)
    payment.save(update_fields=["poll_url", "provider_reference"])
    return HttpResponseRedirect(response.redirect_url)

def _create_stripe_checkout(payment: Payment, course: Course, email: Optional[str]) -> str:
    label = f"Course {getattr(course, 'title', None) or getattr(course, 'name', course.id)}"
    success_url = f"{settings.SITE_URL}{reverse('payments:success')}?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{settings.SITE_URL}{reverse('payments:cancel')}"
    session = stripe.checkout.Session.create(
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
        customer_email=email or None,
        line_items=[{
            "price_data": {
                "currency": payment.currency,
                "unit_amount": int(Decimal(payment.amount) * 100),
                "product_data": {"name": label},
            },
            "quantity": 1,
        }],
        metadata={"payment_id": str(payment.id), "course_id": str(course.id), "user_id": str(payment.user.id)},
    )
    payment.stripe_session_id = session.id
    payment.save(update_fields=["stripe_session_id"])
    return session.url

# Optional success/cancel pages
def success(request):
    return HttpResponse("Payment successful. You can close this window.")

def cancel(request):
    return HttpResponse("Payment canceled. You can close this window.")

# Paynow browser return
def paynow_return(request):
    ref = request.GET.get("reference") or request.POST.get("reference")
    qs = Payment.objects.filter(provider="paynow")
    payment = qs.filter(provider_reference=ref).first() if ref else qs.order_by("-id").first()
    if not payment:
        return HttpResponseBadRequest("Payment not found.")
    state = _poll_and_update(payment)
    if state == "paid":
        return success(request)
    elif state == "failed":
        return cancel(request)
    return HttpResponse("Payment pending. Please wait a moment and refresh.")

# Paynow server-to-server callback
@csrf_exempt
def paynow_result(request):
    ref = request.POST.get("reference") or request.GET.get("reference")
    if not ref:
        return HttpResponseBadRequest("Missing reference")
    try:
        payment = Payment.objects.get(provider="paynow", provider_reference=ref)
    except Payment.DoesNotExist:
        return HttpResponseBadRequest("Payment not found")
    _poll_and_update(payment)
    return HttpResponse(status=200)

# Stripe webhook
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig = request.META.get("HTTP_STRIPE_SIGNATURE")
    secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "")
    if not sig or not secret:
        return HttpResponseBadRequest("Missing signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig, secret)
    except stripe.error.SignatureVerificationError:
        return HttpResponseBadRequest("Invalid signature")
    except Exception:
        return HttpResponseBadRequest("Invalid payload")

    if event.get("type") == "checkout.session.completed":
        session = event["data"]["object"]
        payment_id = session.get("metadata", {}).get("payment_id")
        intent_id = session.get("payment_intent")
        if payment_id:
            try:
                p = Payment.objects.select_related("user", "course").get(id=payment_id, provider="stripe")
                p.status = "paid"
                p.stripe_payment_intent_id = intent_id
                p.save(update_fields=["status", "stripe_payment_intent_id"])
                _enroll_and_mark_paid(p)
            except Payment.DoesNotExist:
                pass
    return HttpResponse(status=200)