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
                expr = x ** 2 - 2*x 
                self.window.analyze(expr)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = Algemite()
    exit_status = app.run(sys.argv)

    sys.exit(exit_status)
