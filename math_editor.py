#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gi
gi.require_version("Gtk", "3.0")

from gi.repository import Gtk
from gi.repository import GdkPixbuf

from math_view import MathView

from utils import (
    get_category_icon,
    get_button_icon,
)

from consts import (
    EDITOR_BUTTONS,
    EDITOR_BUTTONS_CATEGORIES,
)

def make_image(name, size=None):
    if size is not None:
        src = get_button_icon(name)
        p = GdkPixbuf.Pixbuf.new_from_file_at_size(src, size, size)
        return Gtk.Image.new_from_pixbuf(p)

    else:
        src = get_category_icon(name)
        return Gtk.Image.new_from_file(src)


class MathTools(Gtk.Notebook):

    def __init__(self):
        Gtk.Notebook.__init__(self)

        for category in EDITOR_BUTTONS_CATEGORIES:
            hbox = Gtk.HBox()
            image = make_image(category)
            image.set_tooltip_text(category.capitalize())

            self.append_page(hbox, image)

            for section in EDITOR_BUTTONS[category]:
                for button in section:
                    img = make_image(button, 32)
                    _button = Gtk.Button()
                    _button.set_image(img)
                    _button.set_tooltip_text(button.capitalize())
                    hbox.pack_start(_button, False, False, 0)

                hbox.pack_start(Gtk.HSeparator(), False, False, 0)
                #hbox


class MathEditor(Gtk.VBox):

    def __init__(self):
        Gtk.VBox.__init__(self)

        self.tools = MathTools()
        self.pack_start(self.tools, False, False, 0)

        self.view = MathView()


if __name__ == "__main__":
    w = Gtk.Window()
    w.set_title("Algemite math editor")

    e = MathEditor()
    w.add(e)
    w.show_all()

    w.connect("destroy", Gtk.main_quit)
    Gtk.main()
