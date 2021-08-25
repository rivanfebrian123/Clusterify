# clustering.py
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
from gi.repository import Gtk, GLib


@Gtk.Template(resource_path='/org/gnome/Clusterify/clustering.ui')
class ClusteringStack(Gtk.Stack):
    __gtype_name__ = 'ClusteringStack'

    rv_ncluster = Gtk.Template.Child()
    sb_ncluster = Gtk.Template.Child()
    rb_comma = Gtk.Template.Child()
    rb_period = Gtk.Template.Child()
    rb_space = Gtk.Template.Child()
    mb_edit = Gtk.Template.Child()
    lb_cols = Gtk.Template.Child()
    tb_auto = Gtk.Template.Child()

    sw_clusters = Gtk.Template.Child()
    fi_clusters = None
    sp_clusters = None
    cv_clusters = None

    sw_elbow = Gtk.Template.Child()
    fi_elbow = None
    sp_elbow = None
    cv_elbow = None

    last_ncluster = None
    last_cols = None
    data = None
    log = None
    ava = None
    txt_unavail = "Choose some columns to continue"
    avail = ""

    def __init__(self, data, log, ava, plt, Canvas, **kwargs):
        super().__init__(**kwargs)

        self.data = data
        self.log = log
        self.ava = ava

        self.fi_clusters = plt.figure()
        self.cv_clusters = Canvas(self.fi_clusters)
        self.cv_clusters.show()
        self.sw_clusters.add(self.cv_clusters)

        self.fi_elbow = plt.figure()
        self.fi_elbow.subplots_adjust(left=0.15, bottom=0.18)
        self.cv_elbow = Canvas(self.fi_elbow)
        self.cv_elbow.show()
        self.sw_elbow.add(self.cv_elbow)

    def get_sep(self):
        if self.rb_comma.get_active():
            return ','
        elif self.rb_period.get_active():
            return '.'
        elif self.rb_space.get_active():
            return ' '

    def get_avail(self):
        return self.avail

    def has_view(self):
        return True

    def partial_idle(self, cw=None):
        self.avail = self.txt_unavail
        self.rv_ncluster.set_reveal_child(False)
        self.ava(self)

    def _update(self, cw=None):
        # depends on partial_update_file
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
                self.sp_clusters.ticklabel_format(scilimits=[-3, 4])

            try:
                clusters = self.data.get_clusters(ncluster)
            except BaseException as e:
                return self.log(e)

            if len(cols) == 1:
                self.fi_clusters.subplots_adjust(left=0.15, bottom=0.18)
                self.sp_clusters.plot(sample[cols[0]])
            elif len(cols) == 2:
                self.fi_clusters.subplots_adjust(left=0.18, bottom=0.215)
                self.sp_clusters.scatter(sample[cols[0]], sample[cols[1]],
                                         c=clusters, cmap="rainbow")
                self.sp_clusters.set_xlabel(cols[0])
                self.sp_clusters.set_ylabel(cols[1])
            elif len(cols) >= 3:
                self.fi_clusters.subplots_adjust(left=0.095, bottom=0.16)
                self.sp_clusters.scatter(sample[cols[0]], sample[cols[1]],
                                         sample[cols[2]], c=clusters,
                                         cmap="rainbow")
                self.sp_clusters.set_xlabel(cols[0])
                self.sp_clusters.set_ylabel(cols[1])
                self.sp_clusters.set_zlabel(cols[2])

            self.cv_clusters.draw()

        self.last_cols = cols
        self.last_ncluster = ncluster
        self.avail = ""
        self.ava(self)
        self.rv_ncluster.set_reveal_child(len(cols) >= 2)
        self.sb_ncluster.set_editable(not self.tb_auto.get_active())

    @Gtk.Template.Callback()
    def update(self, cw=None):
        # avoid crash
        GLib.idle_add(self._update)

    def _partial_update_file(self):
        self.partial_idle()
        self.data.prep(self.get_sep())

        for w in self.lb_cols.get_children():
            self.lb_cols.remove(w)

        for i in self.data.get_columns_ori():
            w = Gtk.CheckButton.new_with_label(i)
            w.connect("toggled", self.update)
            self.lb_cols.prepend(w)

        self.lb_cols.show_all()

    @Gtk.Template.Callback()
    def partial_update_file(self, cw=None):
        GLib.idle_add(self._partial_update_file)

    @Gtk.Template.Callback()
    def unhighlight(self, cw=None):
        self.mb_edit.get_style_context().remove_class('h')
