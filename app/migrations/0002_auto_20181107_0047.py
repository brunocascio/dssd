# Generated by Django 2.1.2 on 2018-11-07 00:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='producttype',
            field=models.ForeignKey(on_delete='CASCADE', to='app.ProductType'),
        ),
    ]
