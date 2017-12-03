#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sympy

from gi.repository import Gtk
from gi.repository import Pango

from math_view import MathView
from analysis import Analyzer

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
)


from math_view import (
    TextBlock,
    EqualBlock,
    TrendBlock,
    PointBlock,
)

from consts import (
    Branch,
    Chars,
)


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

        """
        self.label = Gtk.Label()
        self.label.override_font(Pango.FontDescription("13"))
        self.label.set_halign(Gtk.Align.START)
        self.label.set_valign(Gtk.Align.CENTER)
        hbox.pack_start(self.label, False, False, 0)

        if text is not None:
            self.label.set_text(text)
        """

    def add_child(self, widget):
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

    def make_row(self, text):  
        row = Row(text)
        label = Gtk.Label(text)
        self.lbox.add(row)

        return row

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
        fsize = 15

        self.analyzer = Analyzer(expr)
        self.function_view.set_from_expression(expr, name=name + "(x)")
        self.function_view.set_font_size(40)

        box = ListBox("Dominio")
        self.box.pack_start(box, False, False, 0)

        domain_block = EqualBlock(TextBlock("D(f)"), TextBlock(interval_to_string(self.analyzer.domain)))
        domain_block.set_font_size(fsize)
        box.make_row_with_child(domain_block)

        box = ListBox("Raíces")
        self.box.pack_start(box, False, False, 0)

        roots_block = TextBlock(set_to_string(self.analyzer.roots.keys()))
        roots_block.set_font_size(fsize)
        box.make_row_with_child(roots_block)

        box = ListBox("Signo")
        self.box.pack_start(box, False, False, 0)

        positive_block = TextBlock("+  " + interval_to_string(self.analyzer.positive))
        positive_block.set_font_size(fsize)
        box.make_row_with_child(positive_block)

        negative_block = TextBlock("-  " + interval_to_string(self.analyzer.negative))
        negative_block.set_font_size(fsize)
        box.make_row_with_child(negative_block)

        box = ListBox("Continuidad")
        self.box.pack_start(box, False, False, 0)

        if self.analyzer.continuity == self.analyzer.domain:
            block = TextBlock("f es continua en todo su dominio.")

        else:
            block = TextBlock("f es continua para los x %s %s\n" % (Chars.BELONGS, interval_to_string(self.analyzer.continuity)))

        block.set_font_size(fsize)
        box.make_row_with_child(block)

        box = ListBox("Ramas")
        self.box.pack_start(box, False, False, 0)

        if self.analyzer.branches[sympy.oo] is not None:
            block = TextBlock("f posee %s cuando" % Branch.get_name(*self.analyzer.branches[sympy.oo]).lower())
            block.set_font_size(fsize)
            row = box.make_row_with_child(block)
            trend_block = TrendBlock(TextBlock("x"), TextBlock("+" + Chars.INFINITY))
            trend_block.set_font_size(fsize)
            row.add_child(trend_block)

        if self.analyzer.branches[-sympy.oo] is not None:
            block = TextBlock("f posee %s cuando" % Branch.get_name(*self.analyzer.branches[-sympy.oo]).lower())
            block.set_font_size(fsize)
            row = box.make_row_with_child(block)
            trend_block = TrendBlock(TextBlock("x"), TextBlock("-" + Chars.INFINITY))
            trend_block.set_font_size(fsize)
            row.add_child(trend_block)

        box = ListBox("Crecimiento")
        self.box.pack_start(box, False, False, 0)

        block = MathView.new_from_expression(self.analyzer.derived, name + "'(x)")
        block.set_font_size(fsize)
        block.set_margin_right(0)
        box.make_row_with_child(block)

        block = TextBlock(name + " crece en %s" % interval_to_string(self.analyzer.derived_things.positive))
        block.set_font_size(fsize)
        box.make_row_with_child(block)

        block = TextBlock(name + " decrece en %s" % interval_to_string(self.analyzer.derived_things.negative))
        block.set_font_size(fsize)
        box.make_row_with_child(block)

        mins, maxs = self.analyzer.get_minimums_and_maximums()

        if mins or maxs:
            if mins:
                block = TextBlock("Mínimos: ")
                block.set_font_size(fsize)
                row = box.make_row_with_child(block)

                for point in mins:
                    block = TextBlock("(%s; %s)" % (str(point[0]), str(point[1])))
                    block.set_font_size(fsize)
                    row.add_child(block)

            if maxs:
                block = TextBlock("Máximos: ")
                block.set_font_size(fsize)
                row = box.make_row_with_child(block)

                for point in maxs:
                    block = TextBlock("(%s; %s)" % (str(point[0]), str(point[1])))
                    block.set_font_size(fsize)
                    row.add_child(block)

        """
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
        """

        self.show_all()
