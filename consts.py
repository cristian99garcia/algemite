#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sympy
from sympy import (
    oo,
    Interval,
)

from sympy.core import numbers


REALS = Interval(-oo, +oo)  # El signo de + no es necesario


GI_REQUIREMENTS = {
    "Gtk": "3.0",
}


MATH_CHARS = {
    # Caracteres de la fuente con símbolos matemáticos
    # SIMBOLO: CARACTER_UNICODE
    "karp-reduction": "A",
    "karp-reduction-inverse": "B",
    "left-arrow": "C",
    "right-arrow": "D",
    "up-arrow": "E",
    "down-arrow": "F",
    "left-right-arrow": "G",
    "right-up-arrow": "H",
    "right-down-arrow": "I",
    "congruence": "J",
    "material-implication-inverse": "K",
    "material-implication": "L",
    "material-implication-up": "M",
    "material-implication-down": "N",
    "material-equivalence": "O",
    "left-up-arrow": "P",
    "left-down-arrow": "Q",
    "proportional": "R",
    "derivate-of": "S",
    "infinity": "T",
    "in": "U",
    "in": "V",
    "delta": "W",
    "nabla": "X",
    "such-that": "Y",
    "": "Z",
    "top": "a",
    "bottom": "b",
    "naturals": "c",
    "A": "d",
    "B": "e",
    "C": "f",
    "D": "g",
    "E": "h",
    "F": "i",
    "G": "j",
    "H": "k",
    "I": "l",
    "J": "m",
    "K": "n",
    "L": "o",
    "M": "p",
    "N": "q",
    "O": "r",
    "P": "s",
    "Q": "t",
    "R": "u",
    "S": "v",
    "T": "w",
    "U": "x",
    "V": "y",
    "W": "z",
    "for-all": "[",
    "": "]",
    "X": "{",
    "Z": "}",
    "add": "*",
    "reals": "_",
    "+": "!",
    "summation": chr(170),
}


class Chars:
    # Caracteres ASCII
    BELONGS = "∈"
    TREND = "→"
    INFINITY = "∞"
    PI = "π"
    CAPITAL_SIGMA = "Σ"
    E = "ℯ"
    HORIZONTAL_BAR = "─"

    @classmethod
    def get_char(self, text, other):
        if text.lower() == "pi":
            return Chars.PI

        elif text.lower() == "e":
            return Chars.E

        return other


class Branch:
    AH = 0    # Asíntota horizontal
    DAPX = 1  # Dirección asintótica paralela a Ox
    DAPY = 2  # Dirección asintótica paralela a 0y
    AO = 3    # Asíntota oblicua y = m*x + n
    DAP = 4   # Dirección asintótica paralela a y = m*x
    NULL = 5  # Cuando x, por el dominio, no puede tender a -oo

    @classmethod
    def get_name(self, branch, m=0, n=0):
        names = [
            "Asíntota horizontal",
            "Dirección asintótica paralela a Ox",
            "Dirección asintótica paralela a 0y",
            "Asíntota oblicua y = %s*x + %s" % (str(m), str(n)),
            "Dirección asintótica paralela a y = %s*x" % str(m),
            None,
        ]

        return names[branch]



EDITOR_BUTTONS = {
    "basics": [
        [
            "fraction",
            "sqrt",
        #    "root",
        ],
        [
            "power",
        ],
        [
            "plus",
            "minus",
            "multiplication",
        ],
        [
        #    "pi",
        #    "infinity",
        #    "factorial",
            "equal"
        ]
    ],
    "functions": [
        [
        #    "ln"
        #    "log",
        #    "exp"
        ],
        [
        #    "sin",
        #    "tan",
        #    "sec",
        #    "cos",
        #    "cot",
        #    "csc",
        ],
        #[
        #    "limit",
        #    "summation",
        #]
    ]
}

EDITOR_BUTTONS_CATEGORIES = [
    "basics",
    "functions"
]


NUMBERS = [int, float, sympy.Integer, sympy.Float, numbers.E, numbers.Exp1, numbers.Pi, numbers.Rational]


SPECIAL_SYMBOLS = {
    numbers.Pi: Chars.PI,
}
