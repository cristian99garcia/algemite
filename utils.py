#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import ctypes as ct
import cairo
import math
import sympy

from sympy import (
    oo,
    Interval,
    EmptySet,
    Intersection,
    Union,
    And,
    Or,
)

from sympy.logic.boolalg import (
    BooleanTrue,
    BooleanFalse
)

from sympy.core.relational import (
    StrictLessThan,     # a <  b
    LessThan,           # a <= b
    GreaterThan,        # a >  b
    StrictGreaterThan,  # a >= b
)

from consts import (
    Branch,
    REALS,
    Chars,
)


EXISTENCIAL_PROBLEMS_OPS = [
    sympy.ln,  # Ln(x) => x > 0
    sympy.Pow  # x ** -a => x != 0 si -a != 0
]


x = sympy.symbols("x", real=True)


def search_for(function, _class=None, found=[], check=None):
    """
    Devuelve una lista con todas las funciones
    que se encuentran dentro de un sympy.log
    """

    if check is None:
        if function.__class__ == _class:
            found.append(function.args[0])

    else:
        if check(function):
            found.append(function.args[0])

    for _func in function.args:
        if _func.__class__ != sympy.Symbol:
            search_for(_func, _class, found)

    return found


def get_existence_problems(function):
    """
    Devuelve un dict que corresponde a D(f) = R - dict.values
    A cada número fuera del dominio se le asigna un valor
    que corresponde a la cantidad de veces que no existe.

    Esto no funciona muy bien
    Si devuelve 2 valores, puede que la función no exista
    para todos los valores intermedios
    """

    # FIXME: Debería devolver intervalos?, resolvería el
    # problema de los logaritmos: Log(x) tiene problemas
    # de existencia del -oo al 0 (inclusive).
    # Otra posible solución sea devolver una lista compuesta
    # por intervalos y números.

    excluded = {}

    for denom in sympy.solvers.denoms(function):
        for solution in sympy.solve(denom):
            if solution in excluded.keys():
                excluded[solution] += 1

            else:
                excluded[solution] = 1

    #logs = search_for_logs(function)

    #interval = REALS
    #for _log in logs:
    #    pass

    return excluded


def get_domain(function):
    """
    Devuelve un intervalo/unión de intervalos correspondiente
    al dominio de function.
    """

    # FIXME: Dterminar si hay un logaritmo que impida
    # que el domiino empiece en -oo, por ejemplo:
    # log(x), donde el dominio es (0, oo)

    domain = REALS

    logs = search_for(function, sympy.log)
    for _func in logs:
        _logs = search_for(_func, sympy.log, [])
        if not _logs:  # FIXME: Resolver para logaritmos que poseen otro logaritmo.
            interval = inequation_to_interval(sympy.solve(_func >= 0))
            domain = domain.intersect(interval)

    check = lambda a: a.__class__ == sympy.Pow and str(a.args[1]) == "1/2"
    sqrts = search_for(function, check=check)

    for _func in sqrts:
        interval = inequation_to_interval(sympy.solve(_func >= 0))
        domain = domain.intersect(interval)

    problems = get_existence_problems(function)

    problems = problems.keys()
    for value in problems:
        domain -= Interval(value, value)

    return domain


def get_roots(function):
    """
    Devuelve un diccionario compuesto por las raíces
    como keys y el tipo de raíz como value (doble, triple, etc).
    """

    domain = get_domain(function)

    def list_roots_to_dict(values):
        roots = {}
        for value in values:
            if value in domain:
                roots[value] = 1  # FIXME: En realidad no lo sé

        return roots

    try:
        return list_roots_to_dict(sympy.real_roots(function))
    except:
        try:
            return list_roots_to_dict(sympy.solve(function, x))

        except:
            return {}


def _adapt(inequation):
    """
    Transofrma una inecuación de los formatos:
        b < x
        b > x

    a:
        x > b
        x < b

    respectivamente
    """

    a, b = inequation.args

    if inequation.__class__ == StrictLessThan:
        if b == x:
            # Se parte de: a < x
            # Devuelve: x > a
            return b > a

    elif inequation.__class__ == LessThan:
        if b == x:
            # Se parte de: a <= x
            # Devuelve: x >= a
            return b >= a

    elif inequation.__class__ == StrictGreaterThan:
        if b == x:
            # Se parte de: a > x
            # Devuelve: x < a
            return b < a

    elif inequation.__class__ == GreaterThan:
        if b == x:
            # Se parte de a >= x
            # Devuelve: x <= a
            return b <= a

    return inequation


def inequation_to_interval(inequation):
    """
    Devuelve un intervalo a partir de una inequación
    Parte del supuesto de que de un lado de la inecuación
    se encuentra "x", sin operaciones.
    """

    args = inequation.args

    less = [LessThan, StrictLessThan]
    greater = [GreaterThan, StrictGreaterThan]

    if inequation.__class__ in greater + less:  # [StrictGreaterThan, GreaterThan, StrictLessThan, LessThan]
        inequation = _adapt(inequation)

        args = inequation.args
        a = args[0]
        b = args[1]

        if inequation.__class__ in greater:
            if inequation.__class__ == StrictGreaterThan:
                # Ejemplo: x > b
                # Intervalo: (b, +oo)
                return Interval.open(b, oo)

            elif inequation.__class__ == GreaterThan:
                # Ejemplo: x >= b
                # Intervalo: [b, +oo)
                return Interval(b, oo)  # Cerrado por izquierda

        elif inequation.__class__ in less:
            if inequation.__class__ == StrictLessThan:
                # Ejemplo: x < b
                # Intervalo: (-oo, b)
                return Interval.open(-oo, b)

            elif inequation.__class__ == LessThan:
                # Ejemplo: x <= b
                # Intervalo: (-oo, b]
                return Interval(-oo, b)  # Cerrado por derecha

    elif inequation.__class__ == And:
        # El primer valor en args siempre es una inequación

        _args = []
        for arg in args:
            _args.append(_adapt(arg))

        args = _args

        d = {
            1: [],
            2: []
        }

        for arg in args:
            # FIXME: Y si hay otro And o un Or ?
            if arg.__class__ in less:
                d[1].append(inequation_to_interval(arg))

            elif arg.__class__ in greater:
                d[2].append(inequation_to_interval(arg))

        if d[1]:
            __less = True
            _less = d[1][0]
            for _i in d[1][1:]:
                _less = Interval.union(_less, _i)

        else:
            __less = False
            _less = EmptySet()

        if d[2]:
            __greater = True
            _greater = d[2][0]
            for _i in d[2][1:]:
                _greater = Interval.union(_greater, _i)

        else:
            __greater = False
            _greater = EmptySet()

        if __greater and __less:
            return _less.intersect(_greater)

        elif __less and not __greater:
            return _less

        elif __greater and not __less:
            return _greater

    elif inequation.__class__ == Or:
        interval = inequation_to_interval(args[0])

        for arg in args[1:]:
            interval = Union(interval, inequation_to_interval(arg))

        return interval

    elif inequation.__class__ == BooleanTrue:
        # Por ejemplo: 4 > 2, todos los x pertenecientes
        # a los reales cumplen esta inecuación
        return REALS

    elif inequation.__class__ == BooleanFalse:
        # Por ejemplo: 2 > 4, ningún x perteneciente a los
        # reales cumple con esta inecuación
        return EmptySet()

    else:
        print inequation, inequation.__class__


def get_sign(function):
    logs = search_for(function, _class=sympy.log, found=[])

    if not logs:
        in1 = sympy.solve(function < 0)
        in2 = sympy.solve(function > 0)
        return (
            inequation_to_interval(in1),
            inequation_to_interval(in2)
        )

    else:
        for _func in logs:
            _logs = search_for(_func, sympy.log, [])
            if not _logs:
                negative = inequation_to_interval(sympy.solve(_func > 0))
                negative = negative.intersect(inequation_to_interval(sympy.solve(_func < 1)))

                # print sympy.solve(_func > 1)
                positive = inequation_to_interval(sympy.solve(_func > 1))
                break  # FIXME: Y si hay más logaritmos?

    """
    if positive.__class__ != EmptySet:
        positive -= Interval(positive.start, positive.start)
        positive -= Interval(positive.end, positive.end)

    if negative.__class__ != EmptySet:
        negative -= Interval(negative.start, negative.start)
        negative -= Interval(negative.end, negative.end)

    for root in get_roots(function):
        positive -= Interval(root, root)
        negative -= Interval(root, root)
    """

    return (
        negative or EmptySet(),
        positive or EmptySet(),
    )


def get_interval_start(interval):
    if interval.__class__ == Union:
        return get_interval_start(interval.args[0])

    elif interval.__class__ == Interval:
        return interval.start

    return None


def get_interval_end(interval):
    if interval.__class__ == Union:
        return get_interval_end(interval.args[-1])

    elif interval.__class__ == Interval:
        return interval.end

    return None


def get_branch(function, sign):
    """
    Devuelve la rama para sign * oo, sign
    debe ser un número positivo o negativo (de
    preferencia, 1 o -1)
    """

    trend = oo * sign
    infinities = [oo, -1 * oo]

    domain = get_domain(function)
    if trend == oo and get_interval_end(domain) < oo:
        return None

    if trend == -oo and get_interval_start(domain) > -oo:
        return None

    limit1 = sympy.limit(function, x, trend)
    if limit1 not in infinities:
        # Asíntota Horizontal = limit1
        return (Branch.AH, limit1)

    limit2 = sympy.limit(function / x, x, trend)
    if limit2 == 0:  # FIXME: diferenciar entre 0+ y 0- ?
        # Dirección Asintótica Paralela a Ox
        return (Branch.DAPX,)

    elif limit2 in infinities:
        # Dirección Asintótica Paralela a Oy
        return (Branch.DAPY,)

    limit3 = sympy.limit(function - limit2 * x, x, trend)
    if limit2 not in infinities:
        # Asíntota oblicua y = limit2 * x + limit3
        return (Branch.AO, limit2, limit3)

    # Dirección Asintótica Paralela a y = limit2 * x
    return (Branch.DAP, limit2)


def get_branches(function):
    return {
        +oo: get_branch(function, 1),
        -oo: get_branch(function, -1)
    }


def interval_to_string(interval):
    if interval.__class__ == Interval:
        start, end = interval.start, interval.end
        s, e = "(", ")"
        if start in interval:
            s = "["

        if end in interval:
            e = "]"

        text = "%s%s; %s%s" % (s, str(start), str(end), e)
        return text.replace("oo", Chars.INFINITY)

    elif interval.__class__ == sympy.sets.Union:
        string = ""
        for arg in interval.args:
            string += interval_to_string(arg) + " U "

        return string[:-3]

    elif interval.__class__ == Intersection:
        _interval = interval.args[0]
        for arg in interval.args[1:]:
            _interval = _interval.intersect(arg)

        return interval_to_string(_interval)

    return "()"


def get_continuity(function):
    """
    Devuelve el intervalo de las x para los que f es continua.
    """

    problems = get_existence_problems(function)
    domain = get_domain(function)

    for value in problems:
        right_hand_limit = sympy.limit(function, x, value, "+")
        left_hand_limit = sympy.limit(function, x, value, "-")

        if right_hand_limit != left_hand_limit:
            domain -= Interval(value, value)

    return domain


def set_to_string(_set, alt=None):
    if type(_set) == set:
        _set = list(_set)

    if not _set:
        return alt or Chars.EMPTY_SET

    string = "{ "

    idx = 0
    _len = len(_set)

    while idx < _len - 1:
        string += str(_set[idx]) + "; "
        idx += 1

    string += str(_set[-1]) + " }"
    return string


def points_to_string(points):
    string = ""
    for point in points:
        string += "(%s; %s) " % (str(point[0]), str(point[1])) 

    if len(string) > 0:
        return string[:-1]

    return string


def get_local_dir():
    return os.path.abspath(os.path.dirname(__file__))


def get_math_font_file():
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), "font.ttf")


def get_category_icon(category):
    return os.path.join(get_local_dir(), "images", "categories", category + ".svg")


def get_button_icon(name):
    return os.path.join(get_local_dir(), "images", name + ".svg")


def subclass_in(_class, classes):
    """
    Busca si _class es una sub clase de entre todas en classes.
    El equivalente a hacer issubclass(a, b1) or issubclass(a, b2).
    """

    for __class in classes:
        if issubclass(_class, __class):
            return True

    return False


if __name__ == "__main__":
    f = sympy.sqrt(x)
    negative = inequation_to_interval(sympy.solve(f < 0))
    #print get_domain(f)
    #print get_sign(f)
    print negative, interval_to_string(negative)
