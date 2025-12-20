#!/usr/bin/env python3
import sys
import os

# Asegurar rutas
sys.path.append('/app/share/isomorphicon')
sys.stdout.reconfigure(line_buffering=True)

print("🐍 [PYTHON] Main script iniciado.", flush=True)

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Gio, Adw

class IsomorphiconApplication(Adw.Application):
    def __init__(self):
        super().__init__(application_id='io.github.vdoesui.Isomorphicon',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self):
        print("🖥️ [PYTHON] Activando ventana...", flush=True)
        win = self.props.active_window
        if not win:
            try:
                from window import IsomorphiconWindow
                win = IsomorphiconWindow(application=self)
                print("✅ [PYTHON] Ventana window.py cargada.", flush=True)
            except Exception as e:
                print(f"❌ [PYTHON] Error importando window: {e}", flush=True)
                win = Adw.ApplicationWindow(application=self)
                win.set_title("Error Fatal")
                lbl = Gtk.Label(label=f"Error iniciando:\n{e}")
                win.set_content(lbl)
        win.present()

def main(version):
    app = IsomorphiconApplication()
    return app.run(sys.argv)

if __name__ == '__main__':
    main(None)
