#! /bin/bash
set -eo pipefail

rm -rf dist
rm -rf build
rm -rf Output
rm -rf app
mkdir -p dist
mkdir -p build
mkdir -p Output
mkdir -p app

pacman -Sy --noconfirm --needed \
    mingw-w64-x86_64-meson \
    mingw-w64-x86_64-gtk3 \
    mingw-w64-x86_64-python3-gobject \
    mingw-w64-x86_64-gtk-update-icon-cache \
    mingw-w64-x86_64-desktop-file-utils \
    tar \
    mingw-w64-x86_64-python-pip \
    mingw-w64-x86_64-innoextract \
    mingw-w64-x86_64-python-numpy \
    mingw-w64-x86_64-python-pandas \
    mingw-w64-x86_64-python-scikit-learn \
    mingw-w64-x86_64-python-matplotlib
wget -O build/inno.exe https://jrsoftware.org/download.php/is.exe
innoextract -m build/inno.exe
pip install pyinstaller

meson . build
meson install -C build

wget -O build/fluent-icon.tar.xz https://github.com/vinceliuice/Fluent-icon-theme/raw/master/release/Fluent.tar.xz

set +e
/bin/tar -xf build/fluent-icon.tar.xz -C build \
    'Fluent/symbolic/actions' 'Fluent/symbolic/mimetypes' \
    'Fluent/symbolic/status/process-working-symbolic.svg' \
    'Fluent/icon-theme.cache' 'Fluent/index.theme' \
    'Fluent/scalable/apps/system-search.svg'
set -e

mv 'build/Fluent' 'build/fluent-icon'
rm -rf /mingw64/share/icons/Fluent
mkdir -p /mingw64/share/icons/Fluent
cp -rf build/fluent-icon/* /mingw64/share/icons/Fluent

wget -O build/fluent-theme.tar.xz https://github.com/vinceliuice/Fluent-gtk-theme/raw/master/release/Fluent.tar.xz

set +e
/bin/tar -xf build/fluent-theme.tar.xz -C build 'Fluent-light-compact'
set -e

mv 'build/Fluent-light-compact' 'build/fluent-theme'
rm -rf /mingw64/share/themes/Fluent
mkdir -p /mingw64/share/themes/Fluent
cp -rf build/fluent-theme/* /mingw64/share/themes/Fluent

mkdir -p /mingw64/etc/gtk-3.0
echo -e "[Settings]\ngtk-theme-name=Fluent\ngtk-icon-theme-name=Fluent" > /mingw64/etc/gtk-3.0/settings.ini
glib-compile-schemas /mingw64/share/glib-2.0/schemas

pyinstaller build-aux/clusterify.spec --clean
./app/iscc build-aux/inno.iss
