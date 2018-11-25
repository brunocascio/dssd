# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import viewsets
from app.models import Product, ProductType
from app.serializers import ProductSerializer, ProductTypeSerializer
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


# Create your views here.

class ProductTypeViewSet(viewsets.ModelViewSet):
  """
  API endpoint that allows producttypes to be viewed or edited.
  """
  queryset = ProductType.objects.all()
  serializer_class = ProductTypeSerializer


class ProductViewSet(viewsets.ModelViewSet):
  """
  API endpoint that allows products to be viewed or edited.
  """
  queryset = Product.objects.all()
  serializer_class = ProductSerializer

@require_http_methods(["GET"])
@login_required
def productsList(request):
  products = Product.objects.filter(stock__gt=0)
  return render(request, 'products/index.html', {'products': products})

@require_http_methods(["POST"])
@login_required
@csrf_protect
def productBuy(request):
  product = Product.objects.filter(pk=request.get('id'), stock__gt=0).exists()
  pass
  