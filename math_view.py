#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sympy

import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Pango
from gi.repository import GObject

from utils import subclass_in

from consts import (
    Chars,
    NUMBERS,
    MATH_CHARS,
    SPECIAL_SYMBOLS
)


BLOCK_SIGNALS = {
    "size-changed": (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, [GObject.TYPE_INT, GObject.TYPE_INT]),
}


class Block(GObject.GObject):

    __gsignals__ = BLOCK_SIGNALS

    def __init__(self):
        GObject.GObject.__init__(self)

        self._connected_signals = {}

    def get_size(self):
        return Gdk.Rectangle()

    def set_font_size(self, size):
        pass

    def get_font_size(self):
        return 0

    def connect(self, signal, callback, *args):
        sid = GObject.GObject.connect(self, signal, callback, *args)

        if signal not in self._connected_signals.keys():
            self._connected_signals[signal] = []

        self._connected_signals[signal].append(sid)

    def disconnect_signal(self, signal, idx=0):
        if signal in self._connected_signals.keys():
            if len(self._connected_signals) >= idx + 1:
                sid = self._connected_signals[signal][idx]
                GObject.GObject.disconnect(self, sid)

                self._connected_signals[signal].remove(sid)


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
        self.set_valign(Gtk.Align.CENTER)
        self.set_halign(Gtk.Align.CENTER)

        self.connect("size-allocate", self.__size_allocate_cb)

    def get_size(self):
        return self.get_allocation()

    def get_hypothetical_size(self, text=""):
        """
        Devuelve el tamaño hipotético para un texto determinado
        (o para el actual), con la configuración de fuente actual.
        """

        layout = self.get_layout()
        layout.set_markup(text)
        return layout.get_pixel_size()

    def set_font_size(self, size):
        self.set_font(str(size))

    def get_font_size(self):
        if self.fontd is not None:
            return self.fontd.get_size() / Pango.SCALE

        return 0

    def set_font(self, font):
        self.fontd = Pango.FontDescription(font)
        self.override_font(self.fontd)

    def copy(self):
        tb = TextBlock(self.get_text())

        if self.fontd is not None:
            tb.override_font(self.fontd)

        else:
            tb.set_font_size(self.get_font_size())

        return tb

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
        self.set_vexpand(False)
        self.set_hexpand(False)

        self.connect("size-allocate", self.__size_allocate_cb)

    def get_size(self):
        return self.get_allocation()

    def set_label(self, text):
        self.label.set_text(text)

    def set_label_widget(self, label):
        if self.label in self.get_children():
            self.remove(self.label)

        self.label = label
        self.set_center_widget(self.label)

    def set_font_size(self, size):
        self.label.set_font_size(size)

        for child in self.children:
            child.set_font_size(size)

    def get_font_size(self):
        return self.label.get_font_size()

    def replace_child_at(self, idx, new_child, start=True, a=False, b=False, s=0):
        if len(self.get_children()) - 2 >= idx:
            # 2 Porque len() da un número mayor al requerido
            # y porque hay que ignorar el label 

            current_child = self.children[idx]
            current_child.disconnect_signal("size-changed")
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

        new_child.connect("size-changed", self._child_size_changed_cb)
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

    def _child_size_changed_cb(self, child, width, height):
        pass

    def __size_allocate_cb(self, textblock, allocation):
        self.emit("size-changed", allocation.width, allocation.height)


class VContainerBlock(ContainerBlock):

    def __init__(self):
        ContainerBlock.__init__(self)

        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_valign(Gtk.Align.CENTER)


class HContainerBlock(ContainerBlock):

    def __init__(self):
        ContainerBlock.__init__(self)

        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_halign(Gtk.Align.CENTER)


class TwoValuesBlock(HContainerBlock):

    def __init__(self, a=None, b=None):
        HContainerBlock.__init__(self)

        self.children = []
        self.a = a
        self.b = b

        self.set_children(a, b)

    def set_children(self, a=None, b=None):
        if a is not None:
            self.a = a
            self.replace_child_at(0, a)

        if b is not None:
            self.b = b
            self.replace_child_at(1, b, False)

        self.children = [self.a, self.b]
        self.show_all()


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

        self._plabela1 = TextBlock("(")
        self._plabela2 = TextBlock(")")
        self._plabelb1 = TextBlock("(")
        self._plabelb2 = TextBlock(")")

        self.set_children(a, b)
        self.set_font_size(self.label.get_font_size())

    def set_children(self, a=None, b=None):
        pa = self.a
        pb = self.b

        TwoValuesBlock.set_children(self, a=a, b=b)

        multiple = [AddBlock, SubtractBlock]
        _a = current_multple = subclass_in(self.a.__class__, multiple)
        prev_multiple = subclass_in(pa.__class__, multiple)

        if current_multple and not prev_multiple:
            self.pack_start(self._plabela1, False, False, 0)
            self.pack_start(self._plabela2, False, False, 0)

            self.show_all()

        elif not current_multple and prev_multiple:
            self.remove(self._plabela1)
            self.remove(self._plabela2)

        if current_multple:
            self.reorder_child(self._plabela1, 0)
            self.reorder_child(self._plabela2, 3)

        _b = current_multple = subclass_in(self.b.__class__, multiple)
        prev_multiple = subclass_in(pb.__class__, multiple)

        if current_multple and not prev_multiple:
            self.pack_end(self._plabelb1, False, False, 0)
            self.pack_end(self._plabelb2, False, False, 0)

            self.show_all()

        elif not current_multple and prev_multiple:
            self.remove(self._plabelb1)
            self.remove(self._plabelb2)

        if current_multple:
            self.reorder_child(self._plabelb1, -1)
            self.reorder_child(self._plabelb2, 0)

        if (_a and not _b) or (_b and not _a):
            self.set_label("")

        else:
            if self.a.__class__ == self.b.__class__ == TextBlock:
                _text_a = self.a.get_text()
                _text_b = self.b.get_text()

                if (_text_a == "x" and _text_b != "x") or \
                   (_text_b == "x" and _text_a != "x"):

                    self.set_label("")

                else:
                    self.set_label("×")

    def set_font_size(self, size):
        for block in [self.label, self._plabela1, self._plabela2, self._plabelb1, self._plabelb2, self.a, self.b]:
            if block is not None:
                block.set_font_size(size)


class DivisionBlock(TwoValuesBlock):

    def __init__(self, a=None, b=None):
        TwoValuesBlock.__init__(self, a, b)

        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_label(Chars.HORIZONTAL_BAR)
        self.set_font_size(20)   # FIXME: Depende del padre
        self.set_valign(Gtk.Align.CENTER)

    def _child_size_changed_cb(self, child, width, height):
        char_width = self.label.get_hypothetical_size(Chars.HORIZONTAL_BAR).width

        def queue(label, clock):
            """
            Hay que esperar un poco para que tome el nuevo tamaño.
            """
            max_width = max(self.a.get_size().width, self.b.get_size().width)
            w = (max_width / char_width + 1)

            label.queue_resize()
            label.set_label(Chars.HORIZONTAL_BAR * w)

        self.label.add_tick_callback(queue)


class EqualBlock(TwoValuesBlock):

    def __init__(self, a=None, b=None):
        TwoValuesBlock.__init__(self, a, b)

        self.set_label("=")


class LogBlock(ContainerBlock):

    def __init__(self, base=None, result=None):
        ContainerBlock.__init__(self)

        self.set_label("log")
        self.remove(self.label)
        self.pack_start(self.label, False, False, 0)

        if base is not None:
            self.base_block = base
        else:
            self.base_block = TextBlock("0")

        self.__vbox = Gtk.VBox()
        self.pack_start(self.__vbox, False, False, 0)
        self.__vbox.pack_end(self.base_block, False, False, 0)

        self._plabel1 = TextBlock("(")
        self.pack_start(self._plabel1, False, False, 0)

        if result is not None:
            self.result_block = result
        else:
            self.result_block = TextBlock("1")

        self.pack_start(self.result_block, False, False, 5)

        self._plabel2 = TextBlock(")")
        self.pack_start(self._plabel2, False, False, 0)

        self.set_font_size(48)  # FIXME: Depende del padre
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

        self.children = [self.base_block, self.result_block]

    def show_base(self, show=True):
        if show and self.__vbox not in self.get_children():
            self.pack_end(self.__vbox, False, False, 0)

        elif not show and self.__vbox in self.get_children():
            self.remove(self.__vbox)

    def set_font_size(self, size):
        self.label.set_font_size(size)
        self._plabel1.set_font_size(size)
        self._plabel2.set_font_size(size)
        self.base_block.set_font_size(size / 2)
        self.result_block.set_font_size(size)


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

    # TODO: Cuando base_block es un contenedor con múltiples
    # hijos (como una suma, resta, multiplicación (en algunos
    # casos)) se deberían agregar paréntesis

    def __init__(self, base=None, exponent=None):
        ContainerBlock.__init__(self)

        self.remove(self.label)

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

        self.__vbox.pack_start(self.exponent_block, False, False, 0)

        self.set_font_size(self.label.get_font_size())

    def set_font_size(self, size):
        self.base_block.set_font_size(size)
        self.exponent_block.set_font_size(size / 2)


class SummationBlock(ContainerBlock):

    """
    Debería agregar paréntesis? En qué casos?
    """

    def __init__(self, lower_limit=None, upper_limit=None, expression=None):
        ContainerBlock.__init__(self)

        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_label(Chars.CAPITAL_SIGMA)

        self.lower_limit_block = lower_limit
        self.upper_limit_block = upper_limit
        self.expression_block = expression

        self._vbox = Gtk.VBox()
        self.pack_start(self._vbox, False, False, 5)

        self.remove(self.label)
        self._vbox.pack_start(self.label, False, False, 0)

        self.set_children(lower_limit, upper_limit, expression)
        self.set_font_size(68)  # FIXME: Depende del padre
        self.show_all()

    def set_children(self, lower_limit=None, upper_limit=None, expression=None):
        if upper_limit is not None:  # FIXME: Y si el usuario quiere que upper_limit_block sea None ?
            if self.upper_limit_block is not None:
                self._vbox.remove(self.upper_limit_block)

            self.upper_limit_block = upper_limit
            self.upper_limit_block.set_halign(Gtk.Align.CENTER)
            self._vbox.pack_start(self.upper_limit_block, False, False, 0)
            self._vbox.reorder_child(self.upper_limit_block, 0)

        if lower_limit is not None:  # FIXME: Y si el usuario quiere que lower_limit_block sea None ?
            if self.lower_limit_block is not None:
                self._vbox.remove(self.lower_limit_block)

            self.lower_limit_block = lower_limit
            self.lower_limit_block.set_halign(Gtk.Align.CENTER)
            self._vbox.pack_end(self.lower_limit_block, False, False, 0)
            self._vbox.reorder_child(self.lower_limit_block, 0)

        if expression is not None:  # FIXME: Y si el usuario quiere que expression_block sea None ?
            if self.expression_block is not None:
                self.remove(self.expression_block)

            self.expression_block = expression
            self.expression_block.set_halign(Gtk.Align.START)
            self.pack_start(self.expression_block, False, False, 0)

        self.children = [self.lower_limit_block, self.upper_limit_block, self.expression_block]
        # FIXME: Resetear fuente a los hijos nuevos

    def set_font_size(self, size):
        self.label.set_font_size(size)
        if self.upper_limit_block is not None:
            self.upper_limit_block.set_font_size(size / 4)

        if self.lower_limit_block is not None:
            self.lower_limit_block.set_font_size(size / 4)

        if self.expression_block is not None:
            # Tal vez debería establecer un alto máximo (el de Sigma)
            self.expression_block.set_font_size(size / 2)


ONE_VALUE = {
    "ln": LnBlock,
    #"log": Log10Block,
    "log": LnBlock,
}


TWO_VALUES = {
    "+":   AddBlock,
    "-":   SubtractBlock,
    "*":   MultiplicationBlock,
    "/":   DivisionBlock,
    "**":  PowerBlock,
}


TRHEE_VALUES = {
    "Sum": SummationBlock,
}


def parse_rpn(expression):
    """
    Tiene que ser en este archivo, de lo contrario la función
    issubclass devuelve False (ContainerBlock.replace_child_at).
    """

    stack = []
 
    if type(expression) == str:
        expression = expression.split(" ")

    one_v = ONE_VALUE.keys()
    two_v = TWO_VALUES.keys()
    three_v = TRHEE_VALUES.keys()

    for val in expression:
        if val in one_v:
            stack.append(ONE_VALUE[val](stack.pop()))

        elif val in two_v:
            op1 = stack.pop()
            op2 = stack.pop()
            stack.append(TWO_VALUES[val](op2, op1))

        elif val in three_v:
            op1 = stack.pop()
            op2 = stack.pop()
            op3 = stack.pop()
            stack.append(TRHEE_VALUES[val](op3, op2, op1))

        else:
            val = Chars.get_char(val, val)
            stack.append(TextBlock(val))
 
    return stack.pop()


class MathView(Gtk.Fixed):

    def __init__(self):
        Gtk.Fixed.__init__(self)

        self.block = None

        self.set_border_width(10)

        # Test settings:
        f = (x - 2) / (4*x - sympy.ln(x**2))
        upper = EqualBlock(TextBlock("i"), parse_rpn(rpn.expr_to_rpn(str(x**3))))
        lower = EqualBlock(TextBlock("i"), parse_rpn(rpn.expr_to_rpn(str(x-2))))
        expr = parse_rpn(rpn.expr_to_rpn(str(f)))

        s = SummationBlock(lower, upper, expr)
        self.set_block(EqualBlock("f(x)", s))

    def set_block(self, block):
        if self.block is not None:
            self.remove(self.block)

        self.block = block
        if self.block is not None:
            self.put(self.block, 0, 0)

    def set_from_expression(self, expression):
        expr = str(expression)
        block = parse_rpn(rpn.expr_to_rpn(expr))
        self.set_block(block)


if __name__ == "__main__":
    def _test_something(button, view):
        # Una función para probar algo como callback
        x = sympy.Symbol("x")
        f = 3*x**2+2+sympy.pi*x+sympy.E*x**2
        block = parse_rpn(rpn.expr_to_rpn(str(f)))

        s = view.block.children[1]
        d = s.children[2]
        d.set_children(a=block)

    w = Gtk.Window()
    #w.set_default_size(600, 480)
    w.connect("destroy", Gtk.main_quit)

    v = Gtk.VBox()
    w.add(v)

    x = sympy.Symbol("x")
    f = sympy.log(-3*sympy.E+15)*((x**2)-1)/(x+2)

    import rpn

    view = MathView()
    #view.set_from_expression(f)
    v.pack_start(view, True, True, 0)

    b = Gtk.Button("test")  # Un botón de pruebas
    b.connect("clicked", _test_something, view)
    v.pack_end(b, False, False, 0)

    w.show_all()
    Gtk.main()
