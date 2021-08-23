# data.py
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

import os
import gc
import numpy as np
import pandas as pd
from sklearn.cluster import MiniBatchKMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA


class Data():
    data = None
    predata = None
    nmax = None
    sep = None
    sample = None
    cols = None
    scale = None
    kmeanses = []
    elbow = []
    delbow = []
    bncluster = 0
    clusters = [None] * 10

    def clear_prep(self):
        # only for None values
        # no need to clear predata
        self.data = None
        self.sample = None
        self.cols = None
        self.scale = None
        self.sep = None

    def clear_train(self):
        # only for non-None values
        self.kmeanses = []
        self.elbow = []
        self.delbow = []
        self.bncluster = 0
        self.clusters = [None] * 10

    def check_open(self):
        if self.predata is None:
            raise IOError("Please open your database first")

    def check_prep(self):
        self.check_open()

        if self.data is None:
            raise IOError("Please prepare your database first")

    def check_train(self):
        self.check_open()
        self.check_prep()

        if self.cols is None:
            raise IOError("Please train your database first")

    def filter_num(self, _num):
        num = str(_num)
        result = np.nan

        if self.sep == ' ':
            try:
                result = float(
                    num.replace(',', '.').replace(' ', ''))
            except ValueError:
                pass
        else:
            for i in num.split():
                try:
                    if self.sep == '.':
                        result = float(num.replace('.', '').replace(',', '.'))
                    else:
                        result = float(num.replace(',', ''))
                    break
                except ValueError:
                    continue

        return result

    def open(self, oridata, sep=','):
        self.clear_prep()

        if isinstance(oridata, pd.DataFrame):
            data = oridata
        elif isinstance(oridata, str):
            if os.path.splitext(oridata)[-1] == ".csv":
                try:
                    data = pd.read_csv(oridata)
                except ValueError:
                    data = pd.read_csv(oridata, encoding='ISO-8859-1')
            else:
                data = pd.read_excel(oridata)

        if len(data.index) > 5000:
            self.predata = data.sample(5000)
        else:
            self.predata = data

        gc.collect()

    def prep(self, _sep=','):
        self.check_open()
        self.clear_train()

        if _sep:
            sep = str(_sep)
        else:
            sep = ','

        if self.sep == sep:
            return True

        self.sep = sep
        self.data = self.predata.applymap(
            self.filter_num
        ).dropna(
            axis=1, how='all', thresh=len(self.predata.index) / 2
        ).dropna().dropna(axis=1, how='all')

        gc.collect()

    def train(self, cols=None, nmax=750):
        self.check_prep()

        if nmax < 1:
            raise IOError("N max cannot be less than 1")
        elif nmax > 2500:
            raise IOError("N max cannot exceed 2500")

        if self.cols == cols and self.nmax == nmax:
            return True

        self.nmax = nmax
        self.prep(self.sep)

        if cols:
            self.mydata = self.data[cols]
        else:
            self.mydata = self.data

        self.cols = self.mydata.columns.to_list()

        if len(self.mydata.index) > nmax:
            self.sample = self.mydata.sample(nmax)
        else:
            self.sample = self.mydata

        tmpscale = StandardScaler().fit_transform(self.sample)

        if len(self.cols) > 3:
            self.scale = PCA(n_components=3).fit_transform(tmpscale)
        else:
            self.scale = tmpscale

        lastbow = None

        for i in range(1, 10):
            kmeans = MiniBatchKMeans(i).fit(self.scale)
            self.kmeanses.append(kmeans)
            self.elbow.append(kmeans.inertia_)

            if lastbow:
                if kmeans.inertia_ > lastbow:
                    self.delbow.append(kmeans.inertia_ / lastbow)
                else:
                    self.delbow.append(lastbow / kmeans.inertia_)

            lastbow = kmeans.inertia_

        try:
            vmin = (np.percentile(self.delbow, 75) + np.mean(self.delbow)) / 2

            for i, v in enumerate(self.delbow[:-1]):
                if v > vmin:
                    self.bncluster = i + 2
        except BaseException:
            self.bncluster = 2

    def get_columns(self):
        self.check_prep()
        return self.cols

    def get_columns_ori(self):
        self.check_prep()
        return self.data.columns.to_list()

    def get_sample(self):
        self.check_train()
        return self.sample

    def get_scale(self):
        self.check_train()
        return self.scale

    def get_kmeanses(self):
        self.check_train()
        return self.kmeanses

    def get_elbow(self):
        self.check_train()
        return self.elbow

    def get_delbow(self):
        self.check_train()
        return self.delbow

    def get_bncluster(self):
        self.check_train()
        return self.bncluster

    def get_clusters(self, n):
        self.check_train()

        if not n:
            n = self.self.bncluster
        elif n < 1:
            raise IOError("N should at least 1")

        if self.clusters[n - 1] is None:
            self.clusters[n -
                          1] = self.kmeanses[n - 1].predict(self.scale)

        return self.clusters[n - 1]

