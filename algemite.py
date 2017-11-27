#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gi
import sys
import signal
import consts as C

gi.require_versions(C.GI_REQUIREMENTS)

from gi.repository import Gtk

from window import Window


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

            # if C.TESTING:
            #     self.settings = C.TEST_SETTINGS
            #     self.window.edit_area.set_objects(C.TEST_OBJECTS)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = Algemite()
    exit_status = app.run(sys.argv)

    sys.exit(exit_status)
