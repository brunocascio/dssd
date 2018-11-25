from app.models import Product, ProductType
from rest_framework import serializers

class ProductTypeSerializer(serializers.ModelSerializer):
  class Meta:
    model = ProductType
    fields = ('id', 'initials', 'description')

class ProductSerializer(serializers.ModelSerializer):
  
  class Meta:
    model = Product
    fields = ('id', 'name', 'costprice', 'saleprice', 'producttype', 'stock')