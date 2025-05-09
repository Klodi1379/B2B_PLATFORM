# Generated by Django 5.2 on 2025-05-06 00:28

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('orders', '0002_initial'),
        ('products', '0001_initial'),
        ('suppliers', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='supplier',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='orders', to='suppliers.supplier', verbose_name='Supplier'),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='orders.order', verbose_name='Order'),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='products.product', verbose_name='Product'),
        ),
    ]
