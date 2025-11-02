from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'  # or specify the fields you want to include, e.g., ['id', 'name', 'description', 'price', 'seller']