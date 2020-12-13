from pandas import read_csv
import decimal
from datetime import datetime

from rest_framework import generics, status, serializers
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, ParseError


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

        # read and validate csv
        try:
            df = read_csv(
                file,
                converters={
                    'total': decimal.Decimal,
                    'quantity': int,
                    'date': lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S.%f")
                },

            )
        except (ValueError, ValidationError) as e:
            raise DealsAPIException(f'{e}') from e
        except decimal.InvalidOperation as e:
            raise DealsAPIException('Invalid price format') from e


        # 5 columns expected with names customer', 'item', 'total', 'quantity', 'date'
        if not (len(df.columns) == 5 and \
                all(
                    map(
                        lambda x: x in df.columns,
                        ['customer', 'item', 'total', 'quantity', 'date'],
                    )
                )):
            raise DealsAPIException(
                'Wrong file format. CSV file must have following headers:  customer, item, total, quantity,date'
            )


        customers = df['customer'].drop_duplicates()

        items = df['item'].drop_duplicates()


        return Response(status.HTTP_200_OK)


    def get(self, request, *args, **kwargs):
        return Response("Error oc ", status=400 )
