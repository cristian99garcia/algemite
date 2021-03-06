#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sympy

from gi.repository import Gtk
from gi.repository import Pango

from math_view import MathView
from analysis import Analyzer

from utils import (
    x,
    interval_to_string,
    set_to_string,
    subclass_in,
)


from math_view import (
    Block,
    MathView,
    TextBlock,
    EqualBlock,
    TrendBlock,
    PointBlock,
    UnionBlock,
)

from consts import (
    Branch,
    Chars,
)

FONT_SIZE = 15


def make_interval_points(interval):
    if interval.__class__ == sympy.EmptySet:
        return TextBlock("")

    elif interval.__class__ == sympy.Interval:
        _start = str(interval.start)
        _end = str(interval.end)

        if interval.start == -sympy.oo:
            start = TextBlock("-%s" % Chars.INFINITY)

        else:
            start = MathView.new_from_expression(str(sympy.simplify(interval.start)))

        if interval.end == sympy.oo:
            end = TextBlock("+%s" % Chars.INFINITY)

        else:
            end = MathView.new_from_expression(str(sympy.simplify(interval.end)))

        return PointBlock(start, end)

    elif interval.__class__ == sympy.Union:
        p1 = make_interval_points(interval.args[0])
        p2 = make_interval_points(interval.args[1])
        union = UnionBlock(p1, p2)

        if len(interval.args) > 2:
            for arg in interval.args[2:]:
                union = UnionBlock(union, make_interval_points(arg))

        return union

    return TextBlock("")


class Row(Gtk.ListBoxRow):

    def __init__(self, text=None):
        Gtk.ListBoxRow.__init__(self)

        self._hbox = Gtk.HBox()
        self._hbox.set_margin_top(5)
        self._hbox.set_margin_bottom(5)
        self._hbox.set_margin_left(15)
        self._hbox.set_margin_right(15)
        self._hbox.set_size_request(1, 30)
        self._hbox.set_valign(Gtk.Align.CENTER)
        self.add(self._hbox)

    def add_child(self, widget):
        if subclass_in(widget.__class__, [Block, MathView]):
            widget.set_font_size(FONT_SIZE)

        widget.set_halign(Gtk.Align.START)
        widget.set_valign(Gtk.Align.CENTER)
        self._hbox.pack_start(widget, False, False, 0)


class ListBox(Gtk.VBox):

    def __init__(self, section=None):
        Gtk.VBox.__init__(self)

        self.set_size_request(550, 1)
        self.set_halign(Gtk.Align.CENTER)
        self.set_hexpand(False)
        self.set_vexpand(False)
        self.set_margin_top(10)
        self.set_margin_bottom(10)

        self.label = Gtk.Label()
        self.label.set_margin_left(10)
        self.label.set_margin_top(10)
        self.label.set_margin_bottom(10)
        self.label.set_halign(Gtk.Align.START)
        self.label.override_font(Pango.FontDescription("Bold 16"))
        self.pack_start(self.label, False, False, 0)

        if section is not None:
            self.label.set_text(section)

        self.lbox = Gtk.ListBox()
        self.lbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.pack_start(self.lbox, False, False, 0)

    def make_row_with_child(self, child):
        row = Row()
        row.add_child(child)
        self.lbox.add(row)

        return row


class Window(Gtk.ApplicationWindow):

    def __init__(self, application=None):
        Gtk.ApplicationWindow.__init__(self, application=application)

        self.set_default_size(690, 428)
        self.set_title("Algemite")
        # self.set_icon_from_file(U.get_app_icon_file())

        self.analyzer = None

        self._vbox = Gtk.VBox()
        self.add(self._vbox)

        self.function_view = MathView()
        self.function_view.set_halign(Gtk.Align.CENTER)
        self._vbox.pack_start(self.function_view, False, False, 0)

        s = Gtk.ScrolledWindow()
        self._vbox.pack_start(s, True, True, 0)

        self.box = Gtk.VBox()
        s.add(self.box)

        self.show_all()

    def analyze(self, expr):
        name = "f"

        self.analyzer = Analyzer(expr)
        self.function_view.set_from_expression(expr, name=name + "(x)")
        self.function_view.set_font_size(40)

        box = ListBox("Dominio")
        self.box.pack_start(box, False, False, 0)

        domain_block = EqualBlock(TextBlock("D(f)"), TextBlock(interval_to_string(self.analyzer.domain)))
        box.make_row_with_child(domain_block)

        box = ListBox("Raíces")
        self.box.pack_start(box, False, False, 0)

        roots_block = TextBlock(set_to_string(self.analyzer.roots.keys()))
        box.make_row_with_child(roots_block)

        box = ListBox("Signo")
        self.box.pack_start(box, False, False, 0)

        if self.analyzer.positive.__class__ != sympy.EmptySet:
            positive_block = TextBlock("+  " + interval_to_string(self.analyzer.positive))
            box.make_row_with_child(positive_block)

        if self.analyzer.negative.__class__ != sympy.EmptySet:
            negative_block = TextBlock("-  " + interval_to_string(self.analyzer.negative))
            box.make_row_with_child(negative_block)

        box = ListBox("Continuidad")
        self.box.pack_start(box, False, False, 0)

        if self.analyzer.continuity == self.analyzer.domain:
            block = TextBlock("f es continua en todo su dominio.")

        else:
            block = TextBlock("f es continua para los x %s %s\n" % (Chars.BELONGS, interval_to_string(self.analyzer.continuity)))

        box.make_row_with_child(block)

        box = ListBox("Ramas")
        self.box.pack_start(box, False, False, 0)

        if self.analyzer.branches[sympy.oo] is not None:
            block = TextBlock("f posee %s cuando" % Branch.get_name(*self.analyzer.branches[sympy.oo]))
            row = box.make_row_with_child(block)
            trend_block = TrendBlock(TextBlock("x"), TextBlock("+" + Chars.INFINITY))
            trend_block.set_margin_left(10)
            row.add_child(trend_block)

        if self.analyzer.branches[-sympy.oo] is not None:
            block = TextBlock("f posee %s cuando" % Branch.get_name(*self.analyzer.branches[-sympy.oo]))
            row = box.make_row_with_child(block)
            trend_block = TrendBlock(TextBlock("x"), TextBlock("-" + Chars.INFINITY))
            trend_block.set_margin_left(10)
            row.add_child(trend_block)

        box = ListBox("Crecimiento")
        self.box.pack_start(box, False, False, 0)

        block = MathView.new_from_expression(self.analyzer.derived, name + "'(x)")
        box.make_row_with_child(block)

        if self.analyzer.derived_things.negative.__class__ != sympy.EmptySet:
            block = TextBlock(name + " decrece en ")
            row = box.make_row_with_child(block)
            row.add_child(make_interval_points(self.analyzer.derived_things.negative))

        if self.analyzer.derived_things.positive.__class__ != sympy.EmptySet:
            block = TextBlock(name + " crece en ")
            row = box.make_row_with_child(block)
            row.add_child(make_interval_points(self.analyzer.derived_things.positive))

        mins, maxs = self.analyzer.get_minimums_and_maximums()

        if mins:
            block = TextBlock("Mínimos: ")
            row = box.make_row_with_child(block)

            for point in mins:
                _x = MathView.new_from_expression(point[0])
                _y = MathView.new_from_expression(point[1])
                block = PointBlock(_x, _y)
                row.add_child(block)

        if maxs:
            block = TextBlock("Máximos: ")
            row = box.make_row_with_child(block)

            for point in maxs:
                _x = MathView.new_from_expression(point[0])
                _y = MathView.new_from_expression(point[1])
                block = PointBlock(_x, _y)
                row.add_child(block)

        box = ListBox("Concavidad")
        self.box.pack_start(box, False, False, 0)

        block = MathView.new_from_expression(self.analyzer.derived2, name + "''(x)")
        box.make_row_with_child(block)

        if self.analyzer.derived2_things.positive.__class__ != sympy.EmptySet:
            block = TextBlock("f tiene concavidad positiva en: ")
            row = box.make_row_with_child(block)
            row.add_child(make_interval_points(self.analyzer.derived2_things.positive))

        if self.analyzer.derived2_things.negative.__class__ != sympy.EmptySet:
            block = TextBlock("f tiene concavidad negativa en: ")
            row = box.make_row_with_child(block)
            row.add_child(make_interval_points(self.analyzer.derived2_things.negative))

        _analyzer = Analyzer(self.analyzer.derived)
        mins, maxs = _analyzer.get_minimums_and_maximums()
        inflection_points = mins + maxs

        if inflection_points:
            block = TextBlock("Puntos de inflexión: ")
            row = box.make_row_with_child(block)

            for point in inflection_points:
                _x = MathView.new_from_expression(point[0])
                _y = MathView.new_from_expression(point[1])
                block = PointBlock(_x, _y)
                block.set_margin_right(10)
                row.add_child(block)

        self.show_all()
