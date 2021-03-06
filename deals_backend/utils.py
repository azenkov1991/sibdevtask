import itertools
import decimal

def pairwise(iterable):
    a, b = itertools.tee(iterable)
    next(b, None)
    return itertools.zip_longest(a, b)

def int_validator(min_value=None, max_value=None):
    def validator(s):
        max_digits=None
        if max_value:
            max_digits = len(str(max_value))
        if min_value:
            max_digits = max(len(str(min_value)), max_digits)


        if max_digits and len(s)>max_digits:
            raise ValueError(f'Too big number {s}')

        n = int(s)

        if not min_value is None and n < min_value:
            raise ValueError(f'Minimum value is {min_value}. Number:{s}')
        if not max_value is None and n > max_value:
            raise ValueError(f'Maximum value is {max_value} Number: {s}')

        return n

    return validator

def str_validator(max_len=None, not_empty=None):
    def validator(s):
        if not_empty and not len(s):
            raise ValueError(f'Empty string')
        if max_len and len(s)>max_len:
            raise ValueError(f'String too big {s}')
        return s

    return validator



