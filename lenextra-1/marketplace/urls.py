from django.urls import path
from .views import ProductListView, ProductDetailView, ProductSellView

urlpatterns = [
    path('', ProductListView.as_view(), name='product_list'),
    path('product/<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('sell/', ProductSellView.as_view(), name='product_sell'),
]