#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gi.repository import Gtk


class Window(Gtk.ApplicationWindow):

    def __init__(self, application=None):
        Gtk.ApplicationWindow.__init__(self, application=application)

        self.set_size_request(690, 428)
        self.set_title("Algemite")
        # self.set_icon_from_file(U.get_app_icon_file())

        # self.edit_area = EditArea()
        # self.add(self.edit_area)

        self.show_all()
