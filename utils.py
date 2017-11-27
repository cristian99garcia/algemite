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
    REALS
)

EXISTENCIAL_PROBLEMS_OPS = [
    sympy.ln,  # Ln(x) => x > 0
    sympy.Pow  # x ** -a => x != 0 si -a != 0
]


x = sympy.symbols("x", real=True)


def search_for_logs(function, logs=[]):
    """
    Devuelve una lista con todas las funciones
    que se encuentran dentro de un sympy.log
    """

    if function.__class__ == sympy.log:
        logs.append(function.args[0])

    for _func in function.args:
        search_for_logs(_func, logs)

    return logs


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

    logs = search_for_logs(function)
    if logs:
        for _func in logs:
            _logs = search_for_logs(_func, [])
            if not _logs:  # FIXME: Resolver para logaritmos que poseen otro logaritmo.
                domain = inequation_to_interval(sympy.solve(_func > 0))

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
    logs = search_for_logs(function)

    if not logs:
        positive = inequation_to_interval(sympy.solve(function > 0))
        negative = inequation_to_interval(sympy.solve(function < 0))

    else:
        for _func in logs:
            _logs = search_for_logs(_func, [])
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
        positive or EmptySet(),
        negative or EmptySet()
    )


def get_branch(function, sign):
    """
    Devuelve la rama para sign * oo, sign
    debe ser un número positivo o negativo (de
    preferencia, 1 o -1)
    """

    trend = oo * sign
    infinities = [oo, -1 * oo]

    domain = get_domain(function)
    if trend == oo and domain.end < oo:
        return None

    if trend == -oo and domain.start > -oo:
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

        return "%s%s; %s%s" % (s, str(start), str(end), e)

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


if __name__ == "__main__":
    from analisis import Analizer

    # Funciones "simples":
    #f = 3*x**2 - 2*x
    #f = -6 / x**3
    #f = sympy.E**x/x

    # Funciones logarítmicas
    f = sympy.log(x + sympy.log(2*x))
    #f = sympy.log(sympy.log((2*x+1)/(3*x-1) + sympy.log(3*sympy.E**x)))
    #f = sympy.log((2*x+1) / (3*x**2-1))

    a = Analizer(f)
    print a

    #positive, negative = get_sign(f)
    #print negative
    #print "P:", interval_to_string(positive), positive, "\n"
    #print "N:", interval_to_string(negative)
    #logs = search_for_logs(f)
    # print f, get_domain(f)

    #positive, negative = get_sign(f)
    #print positive, "\n", negative
    #print "\nP:", interval_to_string(positive)
    #print "N:", interval_to_string(negative)

    #print a
    #print inequation_to_interval(a), "\n\n", b
    #print inequation_to_interval(b), "\n"
    #print inequation_to_interval(sympy.solve(ineq))

    #inequation = sympy.solve(f > 0)
    #print get_sign(f)[0], get_sign(f)[1]
    #print sympy.solve(f > 0)
    #get_sign(f)

    #print inequation_to_interval(2.2 <= x)

    #inequation = (x > 7) & (x > -3) & (x > -5) & (x < 10)
    #print inequation_to_interval(inequation)

    #print get_sign(f)

    #from sympy import sqrt
    #ine = ((-sqrt(3)/3 < x) & (x < -sqrt(7)/3 + 1/3)) | ((sqrt(3)/3 < x) & (x < 1/3 + sqrt(7)/3))
    #print inequation_to_interval(ine)


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


class LocalCairoFontLoader(object):
    """
    Basado en: https://www.cairographics.org/cookbook/freetypepython/
    No se puede hacer directamente desde python, así
    que se utiliza C.
    """

    _instance = None

    def __new__(_class, *args, **kwargs):
        """
        Singleton.
        """

        if not isinstance(_class._instance, _class):
            _class._instance = object.__new__(_class, *args, **kwargs)

        return _class._instance

    def __init__(self):
        super(LocalCairoFontLoader, self).__init__()

        self.__initialized = False
        self.__freetype_so = None
        self.__cairo_so = None
        self.__ft_lib = None
        self.__ft_destroy_key = None
        self.__surface = None

    def load(self, filename, faceindex=0, loadoptions=0):
        CAIRO_STATUS_SUCCESS = 0
        FT_Err_Ok = 0

        if not self.__initialized:
            # find shared objects
            self.__freetype_so = ct.CDLL("libfreetype.so.6")
            self.__cairo_so = ct.CDLL("libcairo.so.2")
            self.__cairo_so.cairo_ft_font_face_create_for_ft_face.restype = ct.c_void_p
            self.__cairo_so.cairo_ft_font_face_create_for_ft_face.argtypes = [ct.c_void_p, ct.c_int]
            self.__cairo_so.cairo_font_face_get_user_data.restype = ct.c_void_p
            self.__cairo_so.cairo_font_face_get_user_data.argtypes = (ct.c_void_p, ct.c_void_p)
            self.__cairo_so.cairo_font_face_set_user_data.argtypes = (ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p)
            self.__cairo_so.cairo_set_font_face.argtypes = [ct.c_void_p, ct.c_void_p]
            self.__cairo_so.cairo_font_face_status.argtypes = [ct.c_void_p]
            self.__cairo_so.cairo_font_face_destroy.argtypes = (ct.c_void_p,)
            self.__cairo_so.cairo_status.argtypes = [ct.c_void_p]

            # initialize freetype
            self.__ft_lib = ct.c_void_p()
            status = self.__freetype_so.FT_Init_FreeType(ct.byref(self.__ft_lib))
            if status != FT_Err_Ok:
                raise RuntimeError("Error %d initializing FreeType library." % status)

            class PycairoContext(ct.Structure):
                _fields_ = [
                    ("PyObject_HEAD", ct.c_byte * object.__basicsize__),
                    ("ctx", ct.c_void_p),
                    ("base", ct.c_void_p),
                ]

            self.__surface = cairo.ImageSurface(cairo.FORMAT_A8, 0, 0)
            self.__ft_destroy_key = ct.c_int() # dummy address
            self.__initialized = True

        ft_face = ct.c_void_p()
        cr_face = None
        try:
            # load FreeType face
            status = self.__freetype_so.FT_New_Face(self.__ft_lib, filename.encode("utf-8"), faceindex, ct.byref(ft_face))
            if status != FT_Err_Ok:
                raise RuntimeError("Error %d creating FreeType font face for %s" % (status, filename))
            #end if

            # create Cairo font face for freetype face
            cr_face = self.__cairo_so.cairo_ft_font_face_create_for_ft_face(ft_face, loadoptions)
            status = self.__cairo_so.cairo_font_face_status(cr_face)
            if status != CAIRO_STATUS_SUCCESS:
                raise RuntimeError("Error %d creating cairo font face for %s" % (status, filename))

            # Problem: Cairo doesn't know to call FT_Done_Face when its font_face object is
            # destroyed, so we have to do that for it, by attaching a cleanup callback to
            # the font_face. This only needs to be done once for each font face, while
            # cairo_ft_font_face_create_for_ft_face will return the same font_face if called
            # twice with the same FT Face.
            # The following check for whether the cleanup has been attached or not is
            # actually unnecessary in our situation, because each call to FT_New_Face
            # will return a new FT Face, but we include it here to show how to handle the
            # general case.
            if self.__cairo_so.cairo_font_face_get_user_data(cr_face, ct.byref(self.__ft_destroy_key)) is None:
                status = self.__cairo_so.cairo_font_face_set_user_data(
                    cr_face,
                    ct.byref(self.__ft_destroy_key),
                    ft_face,
                    self.__freetype_so.FT_Done_Face
                )

                if status != CAIRO_STATUS_SUCCESS:
                    raise RuntimeError("Error %d doing user_data dance for %s" % (status, filename))

                ft_face = None # Cairo has stolen my reference

            # set Cairo font face into Cairo context
            cairo_ctx = cairo.Context(self.__surface)
            cairo_t = PycairoContext.from_address(id(cairo_ctx)).ctx
            self.__cairo_so.cairo_set_font_face(cairo_t, cr_face)
            status = self.__cairo_so.cairo_font_face_status(cairo_t)
            if status != CAIRO_STATUS_SUCCESS:
                raise RuntimeError("Error %d creating cairo font face for %s" % (status, filename))

        finally:
            self.__cairo_so.cairo_font_face_destroy(cr_face)
            self.__freetype_so.FT_Done_Face(ft_face)

        # get back Cairo font face as a Python object
        face = cairo_ctx.get_font_face()
        return face


def get_local_dir():
    return os.path.abspath(os.path.dirname(__file__))


def get_math_font_file():
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), "font.ttf")


def get_category_icon(category):
    return os.path.join(get_local_dir(), "images", "categories", category + ".svg")


def get_button_icon(name):
    return os.path.join(get_local_dir(), "images", name + ".svg")
