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

    def get_label(self):
        return self.label.get_text()

    def set_label_widget(self, label):
        if self.label in self.get_children():
            self.remove(self.label)

        self.label = label
        self.set_center_widget(self.label)

    def set_font_size(self, size):
        self.label.set_font_size(size)

        for child in self.children:
            if child is not None:
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

        parent = new_child.get_parent()
        if parent is not None:
            parent.remove(new_child)

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

        self.label.set_margin_left(5)  # FIXME: Depende de la fuente
        self.label.set_margin_end(5)   # FIXME: Depende de la fuente
        self.set_children(a, b)

    def set_children(self, a=None, b=None, c=None):
        if a is not None:
            self.a = a
            self.a.set_hexpand(False)
            self.a.set_vexpand(False)
            self.replace_child_at(0, a)

        if b is not None:
            self.b = b
            self.b.set_hexpand(False)
            self.b.set_vexpand(False)
            self.replace_child_at(1, b, False)

        self.children = [self.a, self.b]
        self.show_all()

    def get_font_size(self):
        return self.label.get_font_size()


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

        self.set_label("×")
        self.set_children(a, b)
        self.set_font_size(self.label.get_font_size())

    def set_children(self, a=None, b=None):
        pa = self.a
        pb = self.b

        TwoValuesBlock.set_children(self, a=a, b=b, c="nri")

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
            self.label.set_margin_left(0)
            self.label.set_margin_right(0)

        else:
            if self.a.__class__ == self.b.__class__ == TextBlock:
                _text_a = self.a.get_text()
                _text_b = self.b.get_text()

                if _text_b == "x" and _text_a != "x":
                    self.set_label("")
                    self.label.set_margin_left(0)
                    self.label.set_margin_end(0)

                elif _text_a == "x" and _text_b != "x":
                    self.set_children(self.b, self.a)

                else:
                    self.set_label("×")
                    self.label.set_margin_left(5)
                    self.label.set_margin_end(5)

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

    def set_children(self, a=None, b=None):
        # Centrar los hijos evita la posibilidad de que se expandan
        # infinitamente al cambiar el tamaño del label
        if a is not None:
            a.set_halign(Gtk.Align.CENTER)

        if b is not None:
            b.set_halign(Gtk.Align.CENTER)

        TwoValuesBlock.set_children(self, a, b)


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

        self._vbox = Gtk.VBox()
        self.pack_start(self._vbox, False, False, 0)
        self._vbox.pack_end(self.base_block, False, False, 0)

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
                self._vbox.remove(self.base_block)

            self.base_block = base
            self._vbox.pack_end(self.base_block, False, False, 0)

        self.children = [self.base_block, self.result_block]

    def show_base(self, show=True):
        if show and self._vbox not in self.get_children():
            self.pack_end(self._vbox, False, False, 0)

        elif not show and self._vbox in self.get_children():
            self.remove(self._vbox)

    def set_font_size(self, size):
        for block in [self.label, self._plabel1, self._plabel2, self.result_block]:
            if block is not None:
                block.set_font_size(size)

        if self.base_block is not None:
            self.base_block.set_font_size(size / 2)


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

        self.base_block = None
        self.exponent_block = None

        self.remove(self.label)

        self._vbox = Gtk.VBox()
        self.pack_end(self._vbox, False, False, 0)

        self.set_children(base, exponent)
        self.set_font_size(self.label.get_font_size())

    def set_children(self, base=None, exponent=None):
        if base is not None:
            if self.base_block is not None:
                self.remove(self.base_block)

            self.base_block = base
            self.pack_start(self.base_block, False, False, 0)

        if exponent is not None:
            if self.exponent_block is not None:
                self._vbox.remove(self.exponent_block)

            self.exponent_block = exponent
            self.exponent_block.set_halign(Gtk.Align.START)
            self.exponent_block.set_valign(Gtk.Align.START)
            self._vbox.pack_start(self.exponent_block, False, False, 0)

        self.children = [self.base_block, self.exponent_block]

    def get_font_size(self):
        if self.base_block is not None:
            return self.base_block.get_font_size() / 2

        elif self.exponent_block is not None:
            return self.exponent_block.get_font_size()

        return 0

    def set_font_size(self, size):
        if self.base_block is not None:
            self.base_block.set_font_size(size)

            # FIXME: Y si no hay base_block ?
            if self.exponent_block is not None:
                self.exponent_block.set_font_size(self.base_block.get_font_size() / 2)


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


class IntegralBlock(ContainerBlock):

    """
    TODO
    """

    def __init__(self):
        ContainerBlock.__init__(self)

        self.set_orientation(Gtk.Orientation.HORIZONTAL)

        self.set_label(Chars.INTEGRAL)
        self.set_font_size(68)


class TrendBlock(TwoValuesBlock):

    def __init__(self, a=None, b=None):
        TwoValuesBlock.__init__(self, a, b)

        self.set_label(Chars.TREND)


class OneSidedValueBlock(PowerBlock):

    """
    Valor por derecha/izquierda, comúnmente utilizado en el
    cálculo de límites.
    """

    def __init__(self, value=None, side=None):
        """
        Side puede ser "+", "-" o un TextBlock
        """

        PowerBlock.__init__(self)

        self.set_children(value, side)

    def set_children(self, value=None, side=None):
        if side in ["+", "-"]:
            side = TextBlock(side)

        PowerBlock.set_children(self, value, side)


class LimitBlock(ContainerBlock):

    def __init__(self, trend=None, function=None):
        ContainerBlock.__init__(self)

        self.trend_block = None
        self.function_block = None

        self._vbox = Gtk.VBox()
        self.pack_start(self._vbox, False, False, 0)

        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_label("lim")
        self.remove(self.label)
        self._vbox.pack_start(self.label, False, False, 0)

        self.set_children(trend, function)
        self.set_font_size(self.label.get_font_size())

    def set_children(self, trend=None, function=None):
        if trend is not None:
            if self.trend_block is not None:
                self._vbox.remove(self.trend_block)

            self.trend_block = trend
            self._vbox.pack_end(self.trend_block, False, False, 0)

        if function is not None:
            if self.function_block is not None:
                self.remove(self.function_block)

            self.function_block = function
            self.function_block.set_valign(Gtk.Align.START)
            self.pack_end(self.function_block, False, False, 5)

        self.children = [self.trend_block, self.function_block]

    def set_font_size(self, size):
        self.label.set_font_size(size)
        self._vbox.set_margin_end(size / 2.5)

        if self.trend_block is not None:
            self.trend_block.set_font_size(size / 2)

        if self.function_block is not None:
            self.function_block.set_font_size(size)


class PointBlock(ContainerBlock):

    def __init__(self, x=None, y=None):
        ContainerBlock.__init__(self)

        self.set_orientation(Gtk.Orientation.HORIZONTAL)

        self.x = None
        self.y = None

        self._plabel1 = TextBlock("(")
        self.pack_start(self._plabel1, False, False, 0)

        self.set_label(";")
        self.reorder_child(self.label, 1)

        self._plabel2 = TextBlock(")")
        self.pack_end(self._plabel2, False, False, 0)

        self.set_children(x, y)
        self.set_font_size(self.label.get_font_size())

    def set_children(self, x=None, y=None):
        if x is not None:
            if self.x is not None:
                self.remove(self.x)

            self.x = x
            self.x.set_valign(Gtk.Align.CENTER)
            self.pack_start(self.x, False, False, 0)
            self.reorder_child(self._plabel1, 0)

        if y is not None:
            if self.y is not None:
                self.remove(self.y)

            self.y = y
            self.y.set_valign(Gtk.Align.CENTER)
            self.pack_end(self.y, False, False, 0)
            self.reorder_child(self._plabel2, 0)

        self.children = [self.x, self.y]

        self.show_all()

    def set_font_size(self, size):
        self._plabel1.set_font_size(size)
        self.label.set_font_size(size)
        self.label.set_margin_right(size / 3)
        self._plabel2.set_font_size(size)

        if self.x is not None:
            self.x.set_font_size(size)

        if self.y is not None:
            self.y.set_font_size(size)


class RootBlock(ContainerBlock):

    def __init__(self, radicand=None, index=None):
        ContainerBlock.__init__(self)

        self.radicand_block = None
        self.index_block = None

        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_label(Chars.RADIX)

        self._vbox = Gtk.VBox()
        self.pack_start(self._vbox, False, False, 0)

        self.remove(self.label)
        self.pack_start(self.label, False, False, 0)

        # TODO: Borrar los paréntesis y alargar el signo de
        # raíz cuadrada en la parte superior
        self._plabel1 = TextBlock("(")
        self.pack_start(self._plabel1, False, False, 0)

        self._plabel2 = TextBlock(")")
        self.pack_end(self._plabel2, False, False, 0)

        self.set_children(radicand, index)
        #self.set_font_size(self.label.get_font_size())
        self.set_font_size(100)

    def set_children(self, radicand=None, index=None):
        if radicand is not None:
            if self.radicand_block is not None:
                self.remove(self.radicand_block)

            self.radicand_block = radicand
            self.pack_start(self.radicand_block, False, False, 0)

        if index is not None:
            if self.index_block is not None:
                self._vbox.remove(self.index_block)

            self.index_block = index
            self.index_block.set_halign(Gtk.Align.END)
            self.index_block.set_valign(Gtk.Align.START)
            self._vbox.pack_start(self.index_block, False, False, 0)

        self.children = [self.radicand_block, self.index_block]

    def set_font_size(self, size):
        if self.radicand_block is not None:
            self.radicand_block.set_font_size(size)

        if self.index_block is not None:
            self.index_block.set_font_size(size / 2)

        self.label.set_font_size(size)
        self._plabel1.set_font_size(size)
        self._plabel2.set_font_size(size)

    def set_show_index(self, show):
        if show and self._vbox not in self.get_children():
            self.pack_end(self._vbox, False, False, 0)

        elif not show and self._vbox in self.get_children():
            self.remove(self._vbox)


class SqrtBlock(RootBlock):

    def __init__(self, radicand=None):
        RootBlock.__init__(self, radicand, TextBlock("2"))

        self.set_show_index(False)


class UnionBlock(TwoValuesBlock):

    def __init__(self, a=None, b=None):
        TwoValuesBlock.__init__(self, a, b)

        self.set_label(Chars.UNION)

    def set_children(self, a=None, b=None):
        if a is not None:
            a.set_valign(Gtk.Align.CENTER)

        if b is not None:
            b.set_valign(Gtk.Align.CENTER)

        TwoValuesBlock.set_children(self, a, b)


ONE_VALUE = {
    "ln": LnBlock,
    #"log": Log10Block,
    "log": LnBlock,
    "sqrt": SqrtBlock,
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

    one_v = ONE_VALUE.keys()
    two_v = TWO_VALUES.keys()
    three_v = TRHEE_VALUES.keys()

    count = 0

    for val in expression:
        negative = False
        if val.startswith("-") and (val != "-" or count == 0):
            negative = True
            val = val[1:]

        elif val == "-" and count == len(expression) - 1 and len(stack) == 1:
            stack[0] = SubtractBlock(b=stack[0])
            continue

        if val in one_v:
            block = ONE_VALUE[val](stack.pop())

        elif val in two_v:
            op1 = stack.pop()
            op2 = stack.pop()
            block = TWO_VALUES[val](op2, op1)

        elif val in three_v:
            op1 = stack.pop()
            op2 = stack.pop()
            op3 = stack.pop()
            block = TRHEE_VALUES[val](op3, op2, op1)

        else:
            val = Chars.get_char(val, val)
            block = TextBlock(val)

        if negative:
            block = SubtractBlock(b=block)

        count += 1
        stack.append(block)

    return stack.pop()


import rpn


class MathView(Gtk.Fixed):

    def __init__(self):
        Gtk.Fixed.__init__(self)

        self.block = None

        # Test settings:
        """
        f = (x - 2) / (x*4 - sympy.ln(x**2))
        upper = EqualBlock(TextBlock("i"), parse_rpn(rpn.expr_to_rpn(str(x**3-4*x**2+2))))
        lower = EqualBlock(TextBlock("i"), parse_rpn(rpn.expr_to_rpn(str(x-2))))
        expr = parse_rpn(rpn.expr_to_rpn(str(f)))
        s = SummationBlock(lower, upper, expr)
        """

        """
        i = sympy.Symbol("i")
        s = sympy.Sum(x**2, (i, 0, sympy.oo))
        print rpn.split_expr(s)
        print rpn.expr_to_rpn(s)
        block = parse_rpn(rpn.expr_to_rpn(s))

        self.set_block(EqualBlock("f(x)", block))
        """ 

        """
        side = OneSidedValueBlock(TextBlock("0"), "-")
        trend = TrendBlock(TextBlock("x"), side)
        function = parse_rpn(rpn.expr_to_rpn(x**2 - 2))
        block = LimitBlock(trend, function)
        block.set_font_size(120)
        self.set_block(block)
        """

        """
        index = TextBlock("3")
        radicand = TextBlock("x")
        block = SqrtBlock(radicand)
        self.set_block(block)
        """

    @classmethod
    def new_from_expression(self, expression, name=None):
        view = MathView()
        view.set_from_expression(expression, name)
        return view

    def set_block(self, block):
        if self.block is not None:
            self.remove(self.block)

        self.block = block
        if self.block is not None:
            self.put(self.block, 0, 0)

    def set_from_expression(self, expression, name=None):
        expr = str(expression)
        block = parse_rpn(rpn.expr_to_rpn(expr))

        if name is not None:
            block = EqualBlock(TextBlock(name), block)

        self.set_block(block)
        self.show_all()

    def set_font_size(self, size):
        if self.block is not None:
            self.block.set_font_size(size)


if __name__ == "__main__":
    import signal, sys
    signal.signal(signal.SIGINT, signal.SIG_DFL)

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
    #f = sympy.log(-3*sympy.E+15)*((x**2)-1)/(x+2)

    import rpn

    expr = "-(3*x + 3)*exp(-x)/x**2"
    #print rpn.split_expr(expr)
    #print parse_rpn(rpn.split_expr(expr))

    view = MathView.new_from_expression(expr)
    v.pack_start(view, True, True, 0)
    w.show_all()
    Gtk.main()

    """
    view = MathView()
    #view.set_from_expression("-sqrt(7)/3")
    #view.set_from_expression("x**3+x**2-2*x")
    #view.set_from_expression(3/(sympy.E**x*x**2))
    block = parse_rpn(['-3', 'x', '*', '3', '-', 'e', '-x', '**', '*', 'x', '2', '**', '/'])
    view.set_block(block)
    v.pack_start(view, True, True, 0)

    b = Gtk.Button("test")  # Un botón de pruebas
    b.connect("clicked", _test_something, view)
    #v.pack_end(b, False, False, 0)

    w.show_all()
    Gtk.main()
    """
    sys.exit(1)