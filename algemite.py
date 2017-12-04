#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gi
import sys
import sympy
import signal

from consts import (
    TESTING,
    GI_REQUIREMENTS,
)

gi.require_versions(GI_REQUIREMENTS)

from gi.repository import Gtk

from window import Window
from utils import x


class Algemite(Gtk.Application):

    def __init__(self):
        Gtk.Application.__init__(self)

        self.window = None

    def do_startup(self):
        Gtk.Application.do_startup(self)

        # TODO: crear acciones

        self.activate()

    def do_activate(self):
        if not self.window:
            self.window = Window(application=self)

            if TESTING:
                #expr = sympy.sqrt(x) ** 4
                #expr = 4*sympy.log(x)/(sympy.E**x)

                # FIXME:
                # expr = (x**2-4/3*x)/(sympy.E**x)
                # D1: (-x**2 + 3*x - 1)*exp(-x)
                # D2: (-x**2 + 7*x - 9)*exp(-x)

                #expr = sympy.E**x/x**2

                expr = 3/(x*sympy.E**x)#*x**2)
                self.window.analyze(expr)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = Algemite()
    exit_status = app.run(sys.argv)

    sys.exit(exit_status)
