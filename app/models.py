# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class ProductType(models.Model):
  initials = models.CharField(max_length=5)
  description = models.CharField(max_length=100)

  class Meta:
    db_table = "producttype"

  def __unicode__(self):
    return u"%s" % self.initials


class Product(models.Model):
  name = models.CharField(max_length=100)
  costprice = models.IntegerField()
  saleprice = models.IntegerField()
  stock = models.IntegerField(default=0)
  producttype = models.ForeignKey(ProductType, on_delete='CASCADE')

  class Meta:
    db_table = "product"

  def __unicode__(self):
    return u"%s" % self.name


class Sale(models.Model):
  amount = models.CharField(max_length=100)
  product_id = models.ForeignKey(Product, on_delete='RESTRICT')
  email = models.CharField(max_length=100)

  class Meta:
    db_table = "sale"

  def __unicode__(self):
    return u"venta: %d, email: %s" % self.id, self.email

class Cart(models.Model):
  amount = models.CharField(max_length=100)
  product_id = models.ForeignKey(Product, on_delete='RESTRICT')
  user_id = models.ForeignKey(User, on_delete='RESTRICT')
  case_id = models.CharField(max_length=255)

  class Meta:
    db_table = "cart"

  def __unicode__(self):
    return u"cart: %d, user: %s" % self.id, self.user_id
