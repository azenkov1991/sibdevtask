import itertools
import decimal

def pairwise(iterable):
    a, b = itertools.tee(iterable)
    next(b, None)
    return itertools.zip_longest(a, b)


def validate_price(s):
    try:
        d = decimal.Decimal(s, )
        sign, digits, exp = d.as_tuple()
        if not (exp == 0 or exp == 2):
            raise ValueError(f'Ivalid price {s}')
        if sign:
            raise ValueError(f'Ivalid price {s}')
        if len(digits) > 28:
            raise ValueError(f'Ivalid price {s}')
        return d

    except decimal.InvalidOperation:
        raise ValueError(f'Ivalid price {s}')
