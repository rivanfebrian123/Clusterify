# window.py
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

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Handy
from threading import Thread
from itertools import cycle
from .data import Data
from .clustering import ClusteringStack


@Gtk.Template(resource_path='/org/gnome/Clusterify/window.ui')
class ClusterifyWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'ClusterifyWindow'

    hb = Gtk.Template.Child()
    fc = Gtk.Template.Child()
    sp = Gtk.Template.Child()
    sq = Gtk.Template.Child()
    st_main = Gtk.Template.Child()
    ll_main = Gtk.Template.Child()
    st_contents = Gtk.Template.Child()
    rv_edit = Gtk.Template.Child()
    tb_edit = Gtk.Template.Child()
    img_edit = Gtk.Template.Child()
    rv_vs = Gtk.Template.Child()
    rv_view = Gtk.Template.Child()
    st_view = Gtk.Template.Child()
    img_view = Gtk.Template.Child()
    rv_sidebar = Gtk.Template.Child()
    vsb = Gtk.Template.Child()
    st_hint = Gtk.Template.Child()

    # On Linux, Matplotlib can only draw on ScrolledWindow for some reason

    data = Data()
    clustering = None
    log = None
    iter_view = None
    next_view = None
    avail = None

    def __init__(self, log, **kwargs):
        super().__init__(**kwargs)
        self.log = log
        self.avail = "Choose a dataset to continue"
        Thread(target=self._init).start()

    def __init(self, plt):
        from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as Canvas
        plt.style.use('seaborn')
        plt.ioff()

        self.clustering = ClusteringStack(self.data, self.log, self.update_avail, plt, Canvas)

        self.st_contents.add_titled(self.clustering, 'clustering', 'Clustering')
        self.st_contents.child_set_property(self.clustering, 'icon-name', 'starred-symbolic')
        self.rv_sidebar.add(self.clustering.b_sidebar)

        self.flexy()

        self.ll_main.connect("notify::folded", self.flexy)
        self.sq.connect("notify::visible-child", self.flexy)
        self.rv_vs.connect("notify::reveal-child", self.flexy)
        self.tb_edit.bind_property("active", self.rv_sidebar, "reveal-child")
        self.rv_edit.bind_property("reveal-child", self.rv_edit, "sensitive")
        self.rv_sidebar.bind_property("reveal-child", self.rv_sidebar, "sensitive")
        self.ll_main.set_transition_type(Handy.LeafletTransitionType.SLIDE)
        self.ll_main.set_mode_transition_duration(350)

        self.unbusy()
        self.st_main.set_visible_child_name("splash")
        self.set_hint(self.avail)

    def _init(self):
        import matplotlib.pyplot as plt

        GLib.idle_add(self.__init, plt)

    def set_hint(self, txt):
        if self.st_hint.get_visible_child_name() == '0':
            n = '1'
        else:
            n = '0'

        c = self.st_hint.get_child_by_name(n)
        _c = self.st_hint.get_visible_child()

        c.set_label(txt)
        self.st_hint.set_visible_child(c)
        _c.set_label('')

    def get_avail(self):
        return self.avail

    def has_view(self):
        return False

    def flexy(self, cw=None, data=None):
        if self.rv_vs.get_reveal_child():
            self.vsb.set_reveal(
                self.sq.get_visible_child() is not self.rv_vs)
        else:
            self.vsb.set_reveal(False)

        if self.ll_main.get_folded() or self.vsb.get_reveal():
            if self.tb_edit.get_active():
                self.st_view.set_visible_child_name('done')
            else:
                self.st_view.set_visible_child_name('view')
            self.img_edit.set_from_icon_name('edit-symbolic',
                Gtk.IconSize.BUTTON)
        else:
            self.st_view.set_visible_child_name('view')
            self.img_edit.set_from_icon_name('view-sidebar-symbolic',
                Gtk.IconSize.BUTTON)

        self.update_avail()

    @Gtk.Template.Callback()
    def done(self, cw=None):
        self.tb_edit.set_active(False)

    def partial_idle(self, cw=None):
        self.clustering.partial_idle()
        self.st_main.set_visible_child_name("splash")
        self.rv_vs.set_reveal_child(False)
        self.rv_edit.set_reveal_child(False)
        self.rv_view.set_reveal_child(False)
        self.rv_sidebar.set_reveal_child(False)

    def idle(self, cw=None):
        self.partial_idle()

    def busy(self):
        self.idle()
        self.st_main.set_visible_child_name("spinner")
        self.sp.start()

        for w in self.hb.get_children():
            w.set_sensitive(False)

    def unbusy(self):
        for w in self.hb.get_children():
            w.set_sensitive(True)

        self.sp.stop()

    def partial_update_file(self, cw=None):
        self.partial_idle()
        self.clustering.partial_update_file()

    def __update_file(self):
        if self.fc.get_filename():
            self.partial_update_file()
            self.rv_vs.set_reveal_child(True)
        else:
            self.idle()

        self.update_contents()
        self.unbusy()

    def _update_file(self):
        GLib.idle_add(self.busy)

        try:
            self.data.open(self.fc.get_filename())
        except BaseException as e:
            return self.log(e)

        GLib.idle_add(self.__update_file)

    @Gtk.Template.Callback()
    def update_file(self, cw=None):
        Thread(target=self._update_file).start()

    def cycle_view(self):
        w = self.st_contents.get_visible_child()
        self.iter_view = cycle(w.get_children())

        try:
            for i in self.iter_view:
                if i is w.get_visible_child():
                    break

            self.next_view = next(self.iter_view)
        except BaseException:
            return False

        self.img_view.set_from_icon_name(w.child_get_property(
            self.next_view, "icon-name"), Gtk.IconSize.BUTTON)

    @Gtk.Template.Callback()
    def update_contents(self, cw=None, data=None):
        self.update_avail()
        self.cycle_view()

        c = self.st_contents.get_visible_child()

        if self.fc.get_filename():
            if c is self.clustering:
                self.rv_edit.set_reveal_child(True)

                if self.tb_edit.get_active():
                    self.rv_sidebar.set_reveal_child(True)
            else:
                self.rv_edit.set_reveal_child(False)
                self.rv_sidebar.set_reveal_child(False)

    @Gtk.Template.Callback()
    def update_view(self, cw=None, data=None):
        w = self.st_contents.get_visible_child()

        if self.next_view:
            w.set_visible_child(self.next_view)

        self.cycle_view()

    def update_avail(self):
        c = self.st_contents.get_visible_child()

        if hasattr(c, 'has_edit'):
            self.rv_edit.set_reveal_child(not self.ll_main.get_folded())
        else:
            self.rv_edit.set_reveal_child(False)

        if hasattr(c, 'get_avail') and hasattr(c, 'has_view'):
            if self.ll_main.get_folded() and c.has_view():
                self.rv_view.set_reveal_child(True)
            elif c.has_view() and c.get_avail() == "":
                self.rv_view.set_reveal_child(True)
            else:
                self.rv_view.set_reveal_child(False)

            if c.get_avail() == "":
                self.st_main.set_visible_child_name("contents")
            else:
                self.st_main.set_visible_child_name("splash")

            self.set_hint(c.get_avail())
        else:
            self.rv_view.set_reveal_child(False)
            self.set_hint("Unknown hint/object")
            self.st_main.set_visible_child_name("splash")
