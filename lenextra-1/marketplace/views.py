from django.shortcuts import render, redirect
from django.views import View
from .models import Product
from .forms import ProductForm

class ProductListView(View):
    def get(self, request):
        products = Product.objects.all()
        return render(request, 'marketplace/product_list.html', {'products': products})

class ProductDetailView(View):
    def get(self, request, pk):
        product = Product.objects.get(pk=pk)
        return render(request, 'marketplace/product_detail.html', {'product': product})

class ProductSellView(View):
    def get(self, request):
        form = ProductForm()
        return render(request, 'marketplace/product_sell_form.html', {'form': form})

    def post(self, request):
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('product_list')
        return render(request, 'marketplace/product_sell_form.html', {'form': form})