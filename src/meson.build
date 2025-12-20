pkgdatadir = join_paths(get_option('prefix'), 'share', 'isomorphicon')

gnome = import('gnome')

# Recursos
gnome.compile_resources('isomorphicon',
  'isomorphicon.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

# Python sources
install_data(
  ['main.py', 'window.py', 'converter.py'],
  install_dir: pkgdatadir
)

# Config
install_subdir('Config', install_dir: pkgdatadir)

# Script de arranque manual
install_data('main.py',
  rename: 'isomorphicon',
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x'
)