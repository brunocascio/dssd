# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.

class ProductType(models.Model):
  initials = models.CharField(max_length=5)
  description = models.CharField(max_length=100)

  class Meta:
    db_table = "producttype"

  def __unicode__(self):
    return u"%s" % self.description


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
