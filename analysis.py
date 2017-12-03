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
    set_to_string,
    points_to_string,
)

from consts import (
    Branch,
    Chars,
)


class LowAnalyzer(object):

    def __init__(self, function):
        super(LowAnalyzer, self).__init__()

        self.function = function

        # Dominio
        self.domain = get_domain(self.function)

        # Raíces
        self.roots = get_roots(self.function)

        # Signo
        self.positive, self.negative = get_sign(self.function)

        # print "p:", self.positive


class Analyzer(LowAnalyzer):

    def __init__(self, function):
        super(Analyzer, self).__init__(function)

        # Continuidad
        self.continuity = get_continuity(self.function)

        # Ramas infinitas
        self.branches = get_branches(self.function)

        # Crecimiento
        # TODO: Extremos relativos
        self.derived = function.diff(x)
        self.derived_things = LowAnalyzer(self.derived)

        # Concavidad
        # TODO: Puntos de inflexión
        self.derived2 = function.diff(x).diff(x)
        self.derived2_things = LowAnalyzer(self.derived2)

    def get_minimums_and_maximums(self):
        maxs = []
        mins = []

        if self.derived_things.roots:
            symbol = self.derived.free_symbols.copy().pop()
            extrema = self.derived_things.roots.keys()

            for root in extrema:
                y = self.function.subs({symbol: root})

                # FIXME: No debe ser la mejor manera de hacer esto
                y2 = self.function.subs({symbol: root - 0.0001})
                if y < y2:  # Decrece, es un mínimo
                    mins.append((root, y))

                else:
                    maxs.append((root, y))

        return mins, maxs

    def __str__(self):
        # Función
        string = "f(x) = %s\n" % str(self.function)

        # Dominio
        string += "Dominio: " + interval_to_string(self.domain)

        # Raíces
        string += "\nRaíces: "
        string += set_to_string(self.roots.keys(), "No tiene")

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
            string += "Continuidad: f es continua para los x %s %s\n" % (Chars.BELONGS, interval_to_string(self.continuity))

        # Ramas
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
        mins, maxs = self.get_minimums_and_maximums()

        if mins or maxs:
            if maxs:
                string += "    Máximos: "
                string += points_to_string(maxs) + "\n"

            if mins:
                string += "    Mínimos: "
                string += points_to_string(mins) + "\n"

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
    #f = 3*x / (sympy.E**(3*x))
    f = x**2-2*x

    #f = 3*sympy.exp(x)/(2*x)
    a = Analyzer(f)
    print str(a)
