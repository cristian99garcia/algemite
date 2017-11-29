#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sympy
from sympy.core import numbers

import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk
from gi.repository import Pango
from gi.repository import GObject

import utils as U


BLOCK_SIGNALS = {
    "size-changed": (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, [GObject.TYPE_INT, GObject.TYPE_INT]),
}


NUMBERS = [int, float, sympy.Integer, sympy.Float, numbers.E, numbers.Exp1, numbers.Pi, numbers.Rational]


SPECIAL_SYMBOLS = {
    numbers.Pi: "π",
}


class Block(GObject.GObject):

    __gsignals__ = BLOCK_SIGNALS

    def __init__(self):
        GObject.GObject.__init__(self)

    def set_font_size(self, size):
        pass

    def get_font_size(self):
        return 0


class TextBlock(Gtk.Label, Block):

    __gsignals__ = BLOCK_SIGNALS
    # Tengo que establecer nuevamente la variable __gsignals__
    # debido a la herencia múltiple, de lo contrario, __gsignals__
    # será remplazada por la versión de de Gtk.Label  y nunca
    # contendrá la señal "size-changed" (debido a que Gtk.Label
    # se encuentra primero en el órden de herencia).

    def __init__(self, text=""):
        Gtk.Label.__init__(self)
        Block.__init__(self)

        self.fontd = None

        self.set_vexpand(False)
        self.set_text(text)
        self.set_font_size(30)  # FIXME: Depende del bloque padre

        self.connect("size-allocate", self.__size_allocate_cb)

    def set_font_size(self, size):
        self.set_font(str(size))

    def get_font_size(self):
        if self.fontd is not None:
            return self.fontd.get_size() / Pango.SCALE

        return 0

    def set_font(self, font):
        self.fontd = Pango.FontDescription(font)
        self.override_font(self.fontd)

    def __size_allocate_cb(self, textblock, allocation):
        self.emit("size-changed", allocation.width, allocation.height)

    def __str__(self):
        return self.get_text()


class ContainerBlock(Gtk.Box, Block):

    __gsignals__ = BLOCK_SIGNALS

    def __init__(self, *args, **kargs):
        Gtk.Box.__init__(self, *args, **kargs)
        Block.__init__(self)

        self.children = []

        self.label = TextBlock()
        self.set_center_widget(self.label)

    def set_label(self, text):
        self.label.set_text(text)

    def set_label_widget(self, label):
        if self.label in self.get_children():
            self.remove(self.label)

        self.label = label
        self.set_center_widget(self.label)

    def set_font_size(self, size):
        self.label.set_font_size(size)

    def get_font_size(self):
        return self.label.get_font_size()

    def replace_child_at(self, idx, new_child, start=True, a=False, b=False, s=0):
        if len(self.get_children()) - 2 >= idx:
            # 2 Porque len() da un número mayor al requerido
            # y porque hay que ignorar el label 

            current_child = self.children[idx]
            self.remove(current_child)
            self.children.remove(current_child)

        if not issubclass(new_child.__class__, Block):
            if new_child.__class__ in SPECIAL_SYMBOLS.keys():
                new_child = TextBlock(SPECIAL_SYMBOLS[new_child.__class__])
            else:
                new_child = TextBlock(str(new_child))

        if start:
            self.pack_start(new_child, a, b, s)

        else:
            self.pack_end(new_child, a, b, s)

        self.children.insert(idx, new_child)
        self.show_children()

    def show_children(self, ignore_label=False):
        for child in self.get_children():
            if child == self.label and ignore_label:
                continue

            if getattr(child, "show_all", None) is None:
                child.show()

            else:
                child.show_all()


class VContainerBlock(ContainerBlock):

    def __init__(self):
        ContainerBlock.__init__(self, orientation=Gtk.Orientation.VERTICAL)

        #self.children = []
        # Estructura de cada valor en children:
        # {
        #    "x": int,
        #    "y": int,
        #    "widget": GtkWidget,
        # }

class HContainerBlock(ContainerBlock):

    def __init__(self):
        ContainerBlock.__init__(self, orientation=Gtk.Orientation.HORIZONTAL)


class TwoValuesBlock(HContainerBlock):

    def __init__(self, a=None, b=None):
        HContainerBlock.__init__(self)

        self.children = []
        self.set_children(a, b)

    def set_children(self, a=None, b=None):
        if a is not None:
            self.replace_child_at(0, a)

        if b is not None:
            self.replace_child_at(1, b, False)

        self.show_all()

    def get_a(self):
        return self.children[0]

    def get_b(self):
        return self.children[1]


class AddBlock(TwoValuesBlock):

    def __init__(self, a=None, b=None):
        TwoValuesBlock.__init__(self, a, b)

        self.set_label("+")


class SubtractBlock(TwoValuesBlock):

    def __init__(self, a=None, b=None):
        TwoValuesBlock.__init__(self, a, b)

        self.set_label("-")


class MultiplicationBlock(TwoValuesBlock):

    def __init__(self, a=None, b=None):
        TwoValuesBlock.__init__(self)

        #print "Mul", a, b
        self.set_children(a, b)

    def set_children(self, a=None, b=None):
        TwoValuesBlock.set_children(self, a, b)

        if a.__class__ in NUMBERS and b.__class__ == sympy.Symbol or \
           b.__class__ == NUMBERS and a.__class__ == sympy.Symbol:

            self.set_label("")

        else:
            self.set_label("×")

class DivisionBlock(TwoValuesBlock):

    def __init__(self, a=None, b=None):
        TwoValuesBlock.__init__(self, a, b)

        self.set_orientation(Gtk.Orientation.VERTICAL)

        label = TextBlock("───")  # FIXME: Depende de los hijos
        label.set_font_size(20)   # FIXME: Depende del padre
        self.set_label_widget(label)


class EqualBlock(TwoValuesBlock):

    def __init__(self, a=None, b=None):
        TwoValuesBlock.__init__(self, a, b)

        self.set_label("=")


class LogBlock(ContainerBlock):

    def __init__(self, base=None, result=None):
        ContainerBlock.__init__(self)

        self.set_label("log")
        self.label.set_font_size(48)
        self.remove(self.label)
        self.pack_start(self.label, False, False, 0)

        if base is not None:
            self.base_block = base
        else:
            self.base_block = TextBlock("0")

        self.base_block.set_font_size(self.label.get_font_size() / 2)

        self.__vbox = Gtk.VBox()
        self.pack_start(self.__vbox, False, False, 0)
        self.__vbox.pack_end(self.base_block, False, False, 0)

        self._plabel1 = TextBlock("(")
        self._plabel1.set_font_size(self.label.get_font_size())
        self.pack_start(self._plabel1, False, False, 0)

        if result is not None:
            self.result_block = result
        else:
            self.result_block = TextBlock("1")

        self.pack_start(self.result_block, False, False, 5)

        self._plabel2 = TextBlock(")")
        self._plabel2.set_font_size(self.label.get_font_size())
        self.pack_start(self._plabel2, False, False, 0)

        self.show_all()

    def set_children(self, result=None, base=None, a=None, b=None):
        if result is None and a is not None:
            result = a

        if base is None and b is not None:
            base = b

        if result is not None:
            if self.result_block is not None:
                self.remove(self.result_block)

            self.result_block = result
            self.pack_start(self.result_block, False, False, 5)

            self.reorder_child(self._plabel2, len(self.get_children()))

        if base is not None:
            if self.base_block is not None:
                self.__vbox.remove(self.base_block)

            self.base_block = base
            self.__vbox.pack_end(self.base_block, False, False, 0)

    def show_base(self, show=True):
        if show and self.__vbox not in self.get_children():
            self.pack_end(self.__vbox, False, False, 0)

        elif not show and self.__vbox in self.get_children():
            self.remove(self.__vbox)


class Log10Block(LogBlock):

    def __init__(self, result=None):
        LogBlock.__init__(self, result=result)

        self.set_children(base=TextBlock("10"))
        self.show_base(False)
        self.set_label("log")


class LnBlock(LogBlock):

    """
    Logaritmo neperiano (de base e).
    """

    def __init__(self, result=None):
        LogBlock.__init__(self, result=result)

        self.set_children(base=TextBlock("e"))
        self.show_base(False)
        self.set_label("ln")


class PowerBlock(ContainerBlock):

    def __init__(self, base=None, exponent=None):
        ContainerBlock.__init__(self)

        self.remove(self.label)

        #print "Power", base, exponent

        if base is not None:
            self.base_block = base
        else:
            self.base_block = TextBlock("0")

        self.pack_start(self.base_block, False, False, 0)

        if exponent is not None:
            self.exponent_block = exponent
        else:
            self.exponent_block = TextBlock("0")

        self.__vbox = Gtk.VBox()
        self.pack_end(self.__vbox, False, False, 5)

        self.exponent_block.set_font_size(self.base_block.get_font_size() / 2)
        self.__vbox.pack_start(self.exponent_block, False, False, 0)


EQUIVALENCES = {
    sympy.Add: AddBlock,
    sympy.Mul: MultiplicationBlock,
    sympy.Pow: PowerBlock,
    sympy.log: Log10Block,
    sympy.ln: LnBlock,
    sympy.Symbol: TextBlock,
    sympy.Integer: TextBlock,
}


def _startswith(obj, stw):
    if type(obj) in [str] + NUMBERS:
        return str(obj).startswith(stw)

    elif issubclass(obj.__class__, TwoValuesBlock):
        return _startswith(obj.get_a(), stw) or _startswith(obj.get_b(), stw)

    elif issubclass(obj.__class__, TextBlock):
        return _startswith(str(obj), stw)

    return False


def _two_values_class(_class, value1, value2):
    """
    Sympy toma:
        como suma              x - 1 (x, -1)
        como potencia          1 / x (x, -1)
        como multiplicación    x / 2 (1/2, x)
    """

    if _class == AddBlock:
        if _startswith(value1, "-"):
            return SubtractBlock(value2, value1 * -1)

        elif _startswith(value2, "-"):
            return SubtractBlock(value1, value2 * -1)

    elif _class == PowerBlock and str(value2).startswith("-"):
        return DivisionBlock(value2 * -1, value1)

    elif _class == MultiplicationBlock:
        if issubclass(value1.__class__, numbers.Rational):
            arg1, arg2 = str(value1).split("/")
            arg1 = sympy.sympify(arg1)
            arg2 = sympy.sympify(arg2)
            return DivisionBlock(MultiplicationBlock(arg1, value2), arg2)

    return _class(value1, value2)


def convert_exp_to_blocks(expression):
    if expression.__class__ in EQUIVALENCES:
        args = ()
        for arg in expression.args:
            args += (convert_exp_to_blocks(arg),)

        _class = EQUIVALENCES[expression.__class__]
        if issubclass(_class, TwoValuesBlock) and len(args) > 2:
            block = _two_values_class(_class, args[0], args[1])

            for arg in args[2:]:
                block = _two_values_class(_class, block, arg)

        elif issubclass(_class, TwoValuesBlock) and len(args) <= 2:
            block = _two_values_class(_class, *args)

        elif issubclass(_class, TextBlock):
            block = TextBlock(str(expression))
            # print expression

        else:
            #print expression, _class, args
            block = _class(*args)

        # print str(block)
        return block

    else:
        print "NOT IN", expression.__class__
        return None


class MathView(Gtk.Fixed):

    def __init__(self):
        Gtk.Fixed.__init__(self)

        self.block = None

        self.set_border_width(10)

        lb = LogBlock()
        lb.set_children(base=TextBlock("e"))

        lnb = LnBlock()
        lnb.set_children(TextBlock("1313"))
        lb.set_children(result=lnb)
        self.set_block(lb)

    def set_block(self, block):
        if self.block is not None:
            self.remove(self.block)

        self.block = block
        if self.block is not None:
            self.put(self.block, 0, 0)

    def set_from_expression(self, expression):
        expr = str(expression)
        block = rpn.expr_to_blocks(expr)
        self.set_block(block)


if __name__ == "__main__":
    w = Gtk.Window()
    #w.set_default_size(600, 480)
    w.connect("destroy", Gtk.main_quit)

    v = Gtk.VBox()
    w.add(v)

    x = sympy.Symbol("x")
    f = sympy.log(-3*sympy.E+15)*((x**2)-1)/(x+2)

    import rpn

    view = MathView()
    view.set_from_expression(f)
    v.pack_start(view, True, True, 0)

    w.show_all()
    Gtk.main()
