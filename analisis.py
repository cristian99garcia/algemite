#!/usr/bin/env python
# -*- coding: utf-8 -*-

import math

import sympy
from sympy import (
    Poly,
    oo
)

from sympy.sets.sets import EmptySet

from utils import (
    x,
    get_roots,
    get_domain,
    get_existence_problems,
    get_sign,
    get_branches,
    get_continuity,
    inequation_to_interval,
    interval_to_string,
)

from consts import (
    Branch,
    Chars,
)


class LowAnalizer(object):

    def __init__(self, function):
        super(LowAnalizer, self).__init__()

        self.function = function

        # Dominio
        self.domain = get_domain(self.function)

        # Raíces
        self.roots = get_roots(self.function)

        # Signo
        self.positive, self.negative = get_sign(self.function)

        # print "p:", self.positive


class Analizer(LowAnalizer):

    def __init__(self, function):
        super(Analizer, self).__init__(function)

        # Continuidad
        self.continuity = get_continuity(self.function)

        # Ramas infinitas
        self.branches = get_branches(self.function)

        # Crecimiento
        # TODO: Extremos relativos
        self.derived = function.diff(x)
        self.derived_things = LowAnalizer(self.derived)

        # Concavidad
        # TODO: Puntos de inflexión
        self.derived2 = function.diff(x).diff(x)
        self.derived2_things = LowAnalizer(self.derived2)

    def __str__(self):
        # Función
        string = "f(x) = %s\n" % str(self.function)

        # Dominio
        string += "Dominio: " + interval_to_string(self.domain)

        # Raíces
        string += "\nRaíces: "
        if self.roots:
            string += "{" + "; ".join([str(x) for x in self.roots]) + "}"
        else:
            string += "No tiene"

        # Signo
        string += "\nSigno:\n"
        if self.positive.__class__ != EmptySet:
            string += "    + %s \n" % interval_to_string(self.positive)

        if self.negative.__class__ != EmptySet:
            string += "    - %s \n" % interval_to_string(self.negative)

        # Continuidad
        if self.continuity == self.domain:
            string += "Continuidad: f es continua en todo su dominio\n"

        else:
            string += "Continuidad: f es continua para los x %s %s\n" % (Chars.PERTENECIENTE, interval_to_string(self.continuity))

        # Ramas
        # FIXME: Puede que no exista una rama
        string += "Ramas:\n"

        if self.branches[oo] is not None:
            string += "    f posee %s cuando x %s +%s\n" % (Branch.get_name(*self.branches[oo]), Chars.TREND, Chars.INFINITY)

        if self.branches[-oo] is not None:
            string += "    f posee %s cuando x %s -%s\n" % (Branch.get_name(*self.branches[-oo]), Chars.TREND, Chars.INFINITY)

        # Crecimiento
        string += "Crecimiento: f'(x) = %s\n" % str(self.derived)
        if self.derived_things.positive.__class__ != EmptySet:
            string += "    f crece en: %s\n" % interval_to_string(self.derived_things.positive)

        if self.derived_things.negative.__class__ != EmptySet:
            string += "    f decrece en: %s\n" % interval_to_string(self.derived_things.negative)

        # Extremos relativos/absolutos
        if self.derived_things.roots:
            symbol = self.derived.free_symbols.copy().pop()
            extrema = self.derived_things.roots.keys()
            maxs = []
            mins = []

            for root in extrema:
                y = self.function.subs({symbol: root})

                # FIXME: No debe ser la mejor manera de hacer esto
                y2 = self.function.subs({symbol: root - 0.0001})
                if y < y2:  # Decrece, es un mínimo
                    mins.append((root, y))

                else:
                    maxs.append((root, y))

            if maxs:
                string += "    Máximos: "
                for p in maxs:
                    string += "(%s; %s) " % (str(p[0]), str(p[1])) 

                string = string[:-1] + "\n"

            if mins:
                string += "    Mínimos: "
                for p in mins:
                    string += "(%s; %s) " % (str(p[0]), str(p[1])) 

                string = string[:-1] + "\n"

        # Concavidad
        string += "Concavidad: f''(x) = %s\n" % self.derived2

        if self.derived2_things.positive.__class__ != EmptySet:
            string += "    f tiene concavidad positiva en: %s\n" % interval_to_string(self.derived2_things.positive)

        if self.derived2_things.negative.__class__ != EmptySet:
            string += "    f tiene concavidad negativa en: %s" % interval_to_string(self.derived2_things.negative)

        # Puntos de inflexión
        if self.derived2_things.roots:
            _string = ""
            symbol = self.derived2.free_symbols.copy().pop()

            for root in self.derived2_things.roots.keys():
                y = self.derived2.subs({symbol: root})
                _string += "(%d; %s), " % (root, str(y))

            if _string != "":
                string += "\n    Puntos de inflexción: " + _string[:-2]

        return string


if __name__ == "__main__":
    #f = 3*x**2 - 2*x
    #f = -6 / x**3
    #f = -2*x**3 + 4*x
    f = 3*x / (sympy.E**(3*x))

    #f = 3*sympy.exp(x)/(2*x)
    a = Analizer(f)
    print str(a)
