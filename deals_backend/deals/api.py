from pandas import read_csv
from datetime import datetime
from utils import pairwise, int_validator, str_validator

from rest_framework import generics, status, serializers
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, ParseError

from django.db.models import F, Sum, Count
from django.core.cache import cache

from .models import *


class DealsAPIException(Exception):
    pass


def formatted_error_response(method):
    def wrap(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except DealsAPIException as e:
            return Response(
                {
                    'Status': 'Error',
                    'Desc': str(e),
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    return wrap


class CustomerUpload(serializers.Serializer):
    deals = serializers.FileField(max_length=255)


class CustomerListEntry(serializers.Serializer):
    username = serializers.CharField(max_length=255)
    spent_money = serializers.IntegerField()
    gems = serializers.ListField(
        child=serializers.CharField(max_length=255),
        allow_empty=True
    )


class CustomerList(generics.GenericAPIView):

    def get_serializer_class(self, *args, **kwargs):
        if self.request.method == 'POST':
            return CustomerUpload
        else:
            return CustomerListEntry


    @formatted_error_response
    def post(self, request, *args, **kwargs):

        try:
            ser = CustomerUpload(data=request.data)
            ser.is_valid(raise_exception=True)
        except (ParseError, ValidationError) as e:
            raise DealsAPIException('Wrong arguments') from e

        file = ser.validated_data['deals']

        # validate header
        # 5 columns expected with names customer', 'item', 'total', 'quantity', 'date'
        header = list(map(lambda x: x.strip(),file.readline().decode().split(',')))
        if header != ['customer', 'item', 'total', 'quantity', 'date']:
            raise DealsAPIException(
                'Wrong file format. CSV file must have following headers:  customer, item, total, quantity,date'
            )

        # read and validate csv
        try:
            df = read_csv(
                file,
                header=None,
                names=header,
                converters={
                    'itme': str_validator(max_len=255),
                    'customer': str_validator(max_len=255),
                    'total': int_validator(min_value=0, max_value=(1<<63)-1),
                    'quantity': int_validator(min_value=0, max_value=(1<<31)-1),
                    'date': lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S.%f")
                },

            )
        except ValueError as e:
            raise DealsAPIException(f'{e}') from e

        if not len(df):
            raise DealsAPIException(
                'No valid entries found'
            )

        df.sort_values(['item', 'date'], inplace=True)

        # clear database
        Customer.objects.all().delete()
        Item.objects.all().delete()

        for row, next_row in pairwise(df.itertuples()):
            customer, created = Customer.objects.get_or_create(username=row.customer)
            item, created = Item.objects.get_or_create(name=row.item)

            # add item_price for item
            price = row.total / row.quantity

            if int(row.total) % row.quantity !=0:
                raise DealsAPIException(f'Total price not divisible by quantinty. Row: {row}')

            item_price = ItemPrice(
                item=item,
                price=price,
                date_start=row.date,
            )

            if next_row:
                if next_row.item == row.item and next_row.date > row.date:
                    item_price.date_end = next_row.date
            item_price.save()

            deal = Deal(
                customer=customer,
                item_price=item_price,
                quantity=row.quantity,
                date=row.date,
            )

            deal.save()

        return Response(
            {
                'Status': 'OK',
            },
            status.HTTP_200_OK
        )


    def get(self, request, *args, **kwargs):

        top_customers = list(Deal.objects.all().values('customer', 'customer__username').annotate(
                spent_money=Sum(F('item_price__price')*F('quantity'))
        ).order_by('-spent_money')[:5])

        top_customers_ids = [ c['customer'] for c in  top_customers ]

        items_two_top_customers_have = Deal.objects.filter(customer_id__in=top_customers_ids)\
            .values('item_price__item')\
            .annotate(customer_count=Count('customer__username', distinct=True))\
            .filter(customer_count__gt=1)

        items_two_top_customers_have_ids = [i['item_price__item'] for i in items_two_top_customers_have]

        for c in top_customers:
            c['username'] = c['customer__username']
            c['gems'] = list(
                Deal.objects.filter(customer_id = c['customer'])\
                    .filter(item_price__item__in=items_two_top_customers_have_ids)\
                    .values_list('item_price__item__name', flat=True)\
                    .distinct('item_price__item__name')
            )

        customer_serializer = CustomerListEntry(
            data = top_customers,
            many=True,

        )

        customer_serializer.is_valid()

        return Response(
            {
                'response': customer_serializer.validated_data,
            },
            status=status.HTTP_200_OK
        )
