from rest_framework import serializers
from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    course_title = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = (
            "id", "course", "course_title", "amount", "currency",
            "status", "provider", "provider_status", "provider_reference",
            "created_at",
        )
        read_only_fields = fields

    def get_course_title(self, obj):
        return getattr(obj.course, "title", None) or getattr(obj.course, "name", None)

class CheckoutRequestSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    provider = serializers.ChoiceField(choices=[("paynow", "paynow"), ("stripe", "stripe")], default="paynow")
    phone = serializers.CharField(required=False, allow_blank=True)
    method = serializers.ChoiceField(required=False, choices=[("ecocash", "ecocash"), ("onemoney", "onemoney")], default="ecocash")