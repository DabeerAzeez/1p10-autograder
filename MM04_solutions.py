

def f_to_k(t):
    return (t-32) * 5 / 9 + 273.15


def impl2loz(w):
    l = int(w)
    o = (w-l)*16
    return l, o


def pale(n):
    first = n // 1000 % 10
    second = n // 100 % 10
    third = n // 10 % 10
    last = n % 10

    consecutive_threes = first == 3 and second == 3 or \
        second == 3 and third == 3 or \
        third == 3 and last == 3

    last_four = last % 4 == 0

    return not (consecutive_threes or last_four)


def bibformat(author, title, city, publisher, year):
    return f"{author} ({year}). {title}. {city}: {publisher}"


def compound(x, y, z):
    return x % 2 == 0 and y % 2 == 1 and z % 2 == 1 and max(x+y, y+z, z+x) > 100  # noqa: E501


def funct(p):
    import math
    print(f"The solution is {math.sqrt(math.log(p-10, 5))}")


def gol(n):
    import math
    return math.ceil(math.log2(n))


def cad_cashier(price, payment):
    result = price - payment
    result = round(result * 5, 2) / 5
    return result
