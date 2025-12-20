application_id = 'io.github.vdoesui.Isomorphicon'

size = '512x512'
icon_dir = 'hicolor' / size / 'apps'
install_data(
  icon_dir / ('@0@.png').format(application_id),
  install_dir: get_option('datadir') / 'icons' / icon_dir
)

symbolic_dir = 'hicolor' / 'symbolic' / 'apps'
install_data(
  symbolic_dir / ('@0@-symbolic.svg').format(application_id),
  install_dir: get_option('datadir') / 'icons' / symbolic_dir
)