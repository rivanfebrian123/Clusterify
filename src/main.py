# main.py
#
# Copyright 2021 Muhammad Rivan
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE X CONSORTIUM BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# Except as contained in this notice, the name(s) of the above copyright
# holders shall not be used in advertising or otherwise to promote the sale,
# use or other dealings in this Software without prior written
# authorization.

import sys
import traceback
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Handy', '1')
from gi.repository import Gtk, Gio, GLib, Gdk, Handy
from .window import ClusterifyWindow


class Application(Gtk.Application):
    def __init__(self):
        Handy.init()
        super().__init__(application_id='org.gnome.Clusterify',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.win = self.props.active_window

    def on_dlg_hide(self, widget, data):
        widget.hide()
        return True

    def do_activate(self):
        if not self.win:
            css = Gtk.CssProvider()
            css.load_from_resource('/org/gnome/Clusterify/main.css')
            scr = Gdk.Screen.get_default()
            ctx = Gtk.StyleContext()

            ctx.add_provider_for_screen(scr, css, Gtk.STYLE_PROVIDER_PRIORITY_USER)

            self.win = ClusterifyWindow(application=self, log=self.log_error)

            self.dlg_about = Gtk.AboutDialog(
                program_name="Clusterify", logo_icon_name="system-search",
                title="About Clusterify",
                comments="Clustering made easy\nMade for my collage assignment",
                authors=["Muhammad Rivan"], version="1.0",
                copyright="IT Telkom Purwokerto 2021",
                modal=True, parent=self.win
            )
            self.dlg_about.connect("delete-event", self.on_dlg_hide)

            self.dlg_error = Gtk.MessageDialog(
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.CANCEL,
                modal=True, parent=self.win
            )

            act = Gio.SimpleAction.new("file_close", None)
            act.connect("activate", self.on_file_close)
            self.add_action(act)

            act = Gio.SimpleAction.new("about", None)
            act.connect("activate", self.on_app_about)
            self.add_action(act)

        self.win.present()

    def on_app_about(self, widget, data):
        self.dlg_about.present()

    def _log_error(self, log):
        self.dlg_error.props.text = "Sorry, your data is unreadable/invalid"
        self.dlg_error.props.secondary_text = str(log)
        self.dlg_error.run()
        self.on_file_close()
        self.dlg_error.hide()
        print("====================================================")
        print(str(log))
        print("====================================================")
        traceback.print_tb(log.__traceback__)
        self.win.unbusy()

    def log_error(self, log):
        GLib.idle_add(self._log_error, log)
        return False

    def on_file_close(self, cb_widget=None, data=None):
        self.win.fc.unselect_all()
        self.win.idle()


def main(version):
    app = Application()
    return app.run(sys.argv)

