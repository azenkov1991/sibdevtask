from pandas import read_csv
from datetime import datetime
from utils import pairwise, validate_price

from rest_framework import generics, status, serializers
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, ParseError

from .models import *


class DealsAPIException(Exception):
    pass


def formatted_error_response(method):
    def wrap(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except DealsAPIException as e:
            return Response(
                f'Status: Error, Desc: {e}',
                status=status.HTTP_400_BAD_REQUEST
            )
    return wrap


class CustomerUpload(serializers.Serializer):
    deals = serializers.FileField(max_length=255)


class CustomerListEntry(serializers.Serializer):
    customer = serializers.CharField(max_length=255)
    spent_money = serializers.DecimalField(
        max_digits=15, decimal_places=2
    )
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
                    'total': validate_price,
                    'quantity': int,
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

            if int(row.total * 100) % row.quantity !=0:
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

        return Response(status.HTTP_200_OK)


    def get(self, request, *args, **kwargs):
        return Response("Error oc ", status=400 )
