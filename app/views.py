# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import viewsets
from app.models import Product, ProductType, Sale
from app.serializers import ProductSerializer, ProductTypeSerializer, SaleSerializer
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.db.models import F
from django.db import transaction, IntegrityError
import requests
import json
from pprint import pprint
from app.helpers import parseBonitaProduct


class CaseNotFoundException(Exception):
  pass

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


class SaleTypeViewSet(viewsets.ModelViewSet):
  """
  API endpoint that allows products to be viewed or edited.
  """
  queryset = Sale.objects.all()
  serializer_class = SaleSerializer

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
  try:
    # Validates if product exists and has stock available
    product = get_object_or_404(Product, stock__gt=0, pk=product_id)

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
    error = False
    errorDescription = None
    ready = False
    caseInfo = None

    while not error and not ready:
      caseInfo = session.get(
        'http://localhost:8080/bonita/API/bpm/caseInfo/'+ str(caseId),
      ).json()
      for taskName, taskResultObj in caseInfo['flowNodeStatesCounters'].items():
        if 'failed' in taskResultObj:
          error = True
          errorDescription = taskName + ' has errors'
          break
        if 'ready' in taskResultObj and taskName.lower() == 'confirmar venta':
          ready = True
          break

    pprint(caseInfo)

    if error:
      return render(request, 'products/error.html', {'error': errorDescription })
    else:
      variables = session.get(
        'http://localhost:8080/bonita/API/bpm/caseVariable?f=case_id='+ str(caseId),
      ).json()
      
      pprint(variables)

      productResponse = {
        'case_id': caseId,
        'name': product.name
      }

      parseBonitaProduct(variables, productResponse)

      pprint(productResponse)

      return render(request, 'products/confirm.html', {'product': productResponse})
  except Exception as e:
    return render(request, 'products/error.html', {'error': str(e) })
  

@require_http_methods(["POST"])
@login_required
@csrf_protect
@transaction.atomic
def productBuyConfirm(request):
  caseId = request.POST.get('case_id')
  session = requests.Session()
  try:
    # Login into bonita
    response = session.post(
      'http://localhost:8080/bonita/loginservice', 
      data = {'username':'walter.bates', 'password': 'bpm', 'redirect': False }, 
      headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    )
    # retrieve case variables
    variables = session.get(
      'http://localhost:8080/bonita/API/bpm/caseVariable?f=case_id='+ str(caseId),
    ).json()

    productInstance = {
      'case_id': caseId
    }

    pprint(variables)

    if ('cause' in variables):
      if "not found" in variables['cause']['message'].lower():
        raise CaseNotFoundException('La compra ha expirado.')
      else:
        raise Exception(variables['cause']['message'])

    parseBonitaProduct(variables, productInstance)

    pprint(productInstance)

    # retrieve confirmar venta task id
    confirmarVentaTaskId = session.get(
      'http://localhost:8080/bonita/API/bpm/task?f=caseId=' + str(caseId)
    ).json()[0]['id']

    # retrieve walter.bates identity
    walterBatesUser = session.get(
      'http://localhost:8080/bonita/API/identity/user?f=userName=walter.bates'
    ).json()[0]

    # assign to walter.bates before execute the task
    taskAssigment = session.put(
      'http://localhost:8080/bonita/API/bpm/userTask/' + str(confirmarVentaTaskId),
      data=json.dumps({ 'assigned_id': int(walterBatesUser['id']) }),
      headers = {'Content-Type': 'application/json', 'X-Bonita-API-Token': session.cookies.get_dict().get('X-Bonita-API-Token')}
    )

    # execute human task in order to finish confirmar venta task
    taskExecuted = session.post(
      'http://localhost:8080/bonita/API/bpm/userTask/'+str(confirmarVentaTaskId)+'/execution',
      headers = {'Content-Type': 'application/json', 'X-Bonita-API-Token': session.cookies.get_dict().get('X-Bonita-API-Token')}
    )

    with transaction.atomic():
      product = get_object_or_404(Product, stock__gt=0, pk=int(productInstance['product_id']))
      # decrement stock
      Product.objects.filter(pk=productInstance['product_id']).update(stock=F('stock') - 1)
      sale = Sale.objects.create(
        email=productInstance['email'],
        amount=productInstance['precio_venta'], 
        product_id=product
      )

    return render(request, 'products/sale-ok.html', { 'sale': sale })

  except CaseNotFoundException as e:
    return render(request, 'products/error.html', { 'error': str(e) })
  except Exception as e:
    raise e
    # return render(request, 'products/error.html', { 'error': str(e) })