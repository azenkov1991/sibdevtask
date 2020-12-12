from django.db import models


class Customer(models.Model):
    username = models.CharField(
        max_length=255, unique=True
    )

    def __str__(self):
        return self.username


class Item(models.Model):
    name = models.CharField(
        max_length=255, unique=True
    )

    def __str__(self):
        return self.name

class ItemPrice(models.Model):
    item = models.ForeignKey(
        'deals.Item', on_delete=models.CASCADE
    )
    price = models.DecimalField(
        max_digits=15, decimal_places=2
    )
    time_start = models.DateTimeField()
    time_end = models.DateTimeField(
        null=True, blank=True
    )

    def __str__(self):
        return f'{self.item}: {self.time_start.date()} {self.time_start.time()} - \
        {self.time_end.date()} {self.time_end.time()}'

class Deal(models.Model):
    customer = models.ForeignKey(
        'deals.Customer', on_delete=models.CASCADE
    )
    item_price = models.ForeignKey(
        'deals.ItemPrice', on_delete=models.CASCADE
    )
    quantity = models.IntegerField()
    time = models.DateTimeField()

    def __str__(self):
        return f'{self.customer} {self.item_price.item} {self.quantity} {self.item_price.price}'