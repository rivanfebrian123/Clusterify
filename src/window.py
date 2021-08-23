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
from gi.repository import Gtk, Gio, GLib
from threading import Thread
from .data import Data


@Gtk.Template(resource_path='/org/example/App/window.ui')
class ClusterifyWindow(Gtk.ApplicationWindow):
    __gtype_name__ = 'ClusterifyWindow'

    hb = Gtk.Template.Child()
    fc = Gtk.Template.Child()
    sp = Gtk.Template.Child()
    st_main = Gtk.Template.Child()
    lb_cols = Gtk.Template.Child()
    rv_ncluster = Gtk.Template.Child()
    sb_ncluster = Gtk.Template.Child()
    tb_auto = Gtk.Template.Child()
    rv_edit = Gtk.Template.Child()
    rv_sts = Gtk.Template.Child()
    rb_comma = Gtk.Template.Child()
    rb_period = Gtk.Template.Child()
    rb_space = Gtk.Template.Child()
    mb_edit = Gtk.Template.Child()

    # On Linux, Matplotlib can only draw on ScrolledWindow for some reason

    sw_clusters = Gtk.Template.Child()
    fi_clusters = None
    sp_clusters = None
    cv_clusters = None

    sw_elbow = Gtk.Template.Child()
    fi_elbow = None
    sp_elbow = None
    cv_elbow = None

    data = Data()
    log = None
    last_ncluster = None
    last_cols = None

    def __init__(self, log, **kwargs):
        super().__init__(**kwargs)
        self.log = log
        Thread(target=self.init).start()

    def _init(self, matplotlib, plt):
        matplotlib.use('GTK3Agg')
        plt.ioff()
        plt.style.use('seaborn')
        from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as Canvas

        self.fi_clusters = plt.figure()
        self.fi_clusters.subplots_adjust(bottom=0.175)
        self.cv_clusters = Canvas(self.fi_clusters)
        self.cv_clusters.show()
        self.sw_clusters.add(self.cv_clusters)

        self.fi_elbow = plt.figure()
        self.fi_elbow.subplots_adjust(bottom=0.175)
        self.cv_elbow = Canvas(self.fi_elbow)
        self.cv_elbow.show()
        self.sw_elbow.add(self.cv_elbow)

    def init(self):
        import matplotlib
        import matplotlib.pyplot as plt
        GLib.idle_add(self._init, matplotlib, plt)
        GLib.idle_add(self.unbusy)

    def get_sep(self):
        if self.rb_comma.get_active():
            return ','
        elif self.rb_period.get_active():
            return '.'
        elif self.rb_space.get_active():
            return ' '

    def partial_idle(self, cw=None):
        self.st_main.set_visible_child_name("splash")
        self.rv_sts.set_reveal_child(False)
        self.rv_ncluster.set_reveal_child(False)

    def idle(self, cw=None):
        self.partial_idle()
        self.rv_edit.set_reveal_child(False)
        self.mb_edit.set_active(False)

    def busy(self):
        self.idle()
        self.st_main.set_visible_child_name("spinner")
        self.sp.start()

        for w in self.hb.get_children():
            w.set_sensitive(False)

    def unbusy(self):
        self.st_main.set_visible_child_name("splash")

        for w in self.hb.get_children():
            w.set_sensitive(True)

        self.sp.stop()

    @Gtk.Template.Callback()
    def partial_update_file(self, cw=None):
        self.data.prep(self.get_sep())

        for w in self.lb_cols.get_children():
            self.lb_cols.remove(w)

        for i in self.data.get_columns_ori():
            w = Gtk.CheckButton.new_with_label(i)
            w.connect("toggled", self.update)
            self.lb_cols.prepend(w)

        self.lb_cols.show_all()
        self.partial_idle()

    def _update_file(self):
        GLib.idle_add(self.busy)

        try:
            self.data.open(self.fc.get_filename())
        except BaseException as e:
            return self.log(e)

        GLib.idle_add(self.partial_update_file)

        GLib.idle_add(self.unbusy)
        GLib.idle_add(self.rv_edit.set_reveal_child, True)
        GLib.idle_add(self.mb_edit.set_active, True)

    @Gtk.Template.Callback()
    def update_file(self, cw=None):
        Thread(target=self._update_file).start()

    def _update(self):
        # depends on update_file
        cols = []

        for w in self.lb_cols.get_children():
            c = w.get_children()[0]

            if c.get_active():
                cols.append(c.get_label())

        if not cols:
            self.partial_idle()
            return None

        try:
            self.data.train(cols)
        except BaseException as e:
            return self.log(e)

        sample = self.data.get_sample()

        if self.last_cols != cols:
            self.fi_elbow.clear()
            self.sp_elbow = self.fi_elbow.add_subplot()

            try:
                self.sp_elbow.plot(range(1, 10), self.data.get_elbow())
            except BaseException as e:
                return self.log(e)

            self.cv_elbow.draw()

        if self.tb_auto.get_active():
            try:
                self.sb_ncluster.set_value(self.data.get_bncluster())
            except BaseException as e:
                return self.log(e)

        ncluster = self.sb_ncluster.get_value_as_int()

        if self.last_cols != cols or self.last_ncluster != ncluster:
            self.fi_clusters.clear()

            if len(cols) >= 3:
                self.sp_clusters = self.fi_clusters.add_subplot(
                    projection="3d")
            else:
                self.sp_clusters = self.fi_clusters.add_subplot()

            try:
                clusters = self.data.get_clusters(ncluster)
            except BaseException as e:
                return self.log(e)

            if len(cols) == 1:
                self.sp_clusters.plot(sample[cols[0]])
            elif len(cols) == 2:
                self.sp_clusters.scatter(sample[cols[0]], sample[cols[1]],
                                         c=clusters, cmap="rainbow")
                self.sp_clusters.set_xlabel(cols[0])
                self.sp_clusters.set_ylabel(cols[1])
            elif len(cols) >= 3:
                self.sp_clusters.scatter(sample[cols[0]], sample[cols[1]],
                                         sample[cols[2]], c=clusters,
                                         cmap="rainbow")
                self.sp_clusters.set_xlabel(cols[0])
                self.sp_clusters.set_ylabel(cols[1])
                self.sp_clusters.set_zlabel(cols[2])

            self.cv_clusters.draw()

        self.last_cols = cols
        self.last_ncluster = ncluster
        self.rv_ncluster.set_reveal_child(len(cols) >= 2)
        self.rv_sts.set_reveal_child(True)
        self.sb_ncluster.set_editable(not self.tb_auto.get_active())
        self.st_main.set_visible_child_name("content")

    @Gtk.Template.Callback()
    def update(self, cw=None):
        Thread(target=GLib.idle_add, args=[self._update]).start()
