#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Basico(object):

    es_numero = False
    es_simbolo = False
    es_funcion = False
    es_suma = False
    es_multi = False
    es_potencia = False
    es_decimal = False
    es_relacion = False
    es_entero = False
    es_SimboloNumero = False
    es_derivable = False
    es_polinomio = False
    es_igualidad = False

    def __new__(clase, *args):
        objeto = object.__new__(clase)
        objeto._args = args

        return objeto


class Expr(Bascio):

    def __init__(self, name):
        super(Expr, self).__init__()

    def __int__(self):
        return 0

    def __mul__(self, arg):
        return 0

    def __add__(self, arg):
        return 0


class Suma(Basico):

    def __init__(self, *args):
        pass

