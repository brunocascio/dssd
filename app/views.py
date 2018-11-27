# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import viewsets
from app.models import Product, ProductType
from app.serializers import ProductSerializer, ProductTypeSerializer
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
import requests
from pprint import pprint
import json

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
  product_id = int(request.POST.get('product_id'))
  session = requests.Session()
  # Validates if product exists and has stock available 
  product = Product.objects.filter(pk=product_id, stock__gt=0).exists()
  # Login into bonita
  response = session.post(
    'http://localhost:8080/bonita/loginservice', 
    data = {'username':'walter.bates', 'password': 'bpm', 'redirect': False }, 
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
  )
  # Search process by name
  processId = session.get(
    'http://localhost:8080/bonita/API/bpm/process?f=name=Proceso+de+compra',
  ).json()[0].get('id')

  # Instantiate sale process (returns caseId)
  caseId = session.post(
    'http://localhost:8080/bonita/API/bpm/process/'+processId+'/instantiation',
    data = json.dumps({
      "var_product_id": product_id,
      "var_cupon": request.POST.get('coupon'),
      "var_email": request.user.get_username()
    }),
    headers = {'Content-Type': 'application/json', 'X-Bonita-API-Token': session.cookies.get_dict().get('X-Bonita-API-Token')}
  ).json().get('caseId')

  # polling requesting result variable
  case = { 'state': 'initializing' }

  while case.get('state') in ('initializing', 'started', 'completing', 'aborting'):
    case = session.get(
      'http://localhost:8080/bonita/API/bpm/case/'+ str(caseId),
    ).json()
    pprint(case.get('state'))

  if case.get('stage') == 'completed':
    return render(request, 'products/confirm.html', {'case': case})
  else:
    # 'suspended', 'cancelled', 'aborted', 'error'
    return render(request, 'products/error.html', {'case': case })

  # redirect user to confirm page or error if something happens

  