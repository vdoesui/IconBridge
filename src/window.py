import os
import threading
import json
from gi.repository import Adw, Gtk, Gio, GLib, Gdk

class IsomorphiconWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_title("Isomorphicon")
        self.set_default_size(900, 700)

        self.base_path = '/app/share/isomorphicon'
        self.output_folder = os.path.join(os.path.expanduser("~"), "Isomorphicon_Output")
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

        self.selected_apk = None

        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.toast_overlay.set_child(main_box)

        header = Adw.HeaderBar()
        main_box.append(header)

        about_btn = Gtk.Button.new_from_icon_name("help-about-symbolic")
        about_btn.connect("clicked", self.show_about_dialog)
        header.pack_end(about_btn)

        page = Adw.PreferencesPage()
        main_box.append(page)

        group_input = Adw.PreferencesGroup(title="Input", description="Select Android Icon Pack (.apk)")
        page.add(group_input)

        self.apk_row = Adw.ActionRow(title="APK File")
        self.apk_row.set_subtitle("No file selected")
        self.apk_row.add_prefix(Gtk.Image.new_from_icon_name("package-x-generic-symbolic"))

        browse_btn = Gtk.Button(label="Browse", valign=Gtk.Align.CENTER)
        browse_btn.connect("clicked", self.on_browse_clicked)
        self.apk_row.add_suffix(browse_btn)
        group_input.add(self.apk_row)

        group_config = Adw.PreferencesGroup(title="Configuration", description="Output options")
        page.add(group_config)

        self.inherits_row = Adw.EntryRow(title="Inherits")
        self.inherits_row.set_text("breeze-dark,breeze,Adwaita,hicolor")
        self.inherits_row.set_show_apply_button(True)
        group_config.add(self.inherits_row)

        self.install_switch = Adw.SwitchRow(title="Install Theme")
        self.install_switch.set_subtitle("Automatically install to ~/.local/share/icons after conversion")
        self.install_switch.set_active(False)
        group_config.add(self.install_switch)

        group_action = Adw.PreferencesGroup()
        page.add(group_action)

        vbox_center = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        vbox_center.set_halign(Gtk.Align.CENTER)
        group_action.add(vbox_center)

        self.run_btn = Gtk.Button(label="Convert")
        self.run_btn.add_css_class("suggested-action")
        self.run_btn.add_css_class("pill")
        self.run_btn.set_size_request(200, 50)
        self.run_btn.set_halign(Gtk.Align.CENTER)
        self.run_btn.connect("clicked", self.on_run_clicked)
        vbox_center.append(self.run_btn)

        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        status_box.set_halign(Gtk.Align.CENTER)

        self.spinner = Gtk.Spinner()
        status_box.append(self.spinner)

        self.status_label = Gtk.Label(label="Ready")
        self.status_label.add_css_class("dim-label")
        status_box.append(self.status_label)

        vbox_center.append(status_box)

    def on_browse_clicked(self, btn):
        dialog = Gtk.FileDialog(title="Select APK")
        filter_apk = Gtk.FileFilter()
        filter_apk.set_name("APK Files")
        filter_apk.add_pattern("*.apk")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_apk)
        dialog.set_filters(filters)
        dialog.open(self, None, self.on_file_selected)

    def on_file_selected(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            self.selected_apk = file.get_path()
            self.apk_row.set_subtitle(os.path.basename(self.selected_apk))
            self.apk_row.set_title(self.selected_apk)
        except Exception as e:
            print(f"Error selecting file: {e}")

    def on_run_clicked(self, btn):
        if not self.selected_apk:
            self.toast_overlay.add_toast(Adw.Toast.new("Please select an APK first"))
            return

        self.run_btn.set_sensitive(False)
        self.apk_row.set_sensitive(False)
        self.inherits_row.set_sensitive(False)
        self.install_switch.set_sensitive(False)
        self.spinner.start()
        self.status_label.set_label("Processing...")

        thread = threading.Thread(target=self.run_conversion_process)
        thread.daemon = True
        thread.start()

    def run_conversion_process(self):
        try:
            import converter

            config_dir = os.path.join(self.base_path, "Config")
            mappings_path = os.path.join(config_dir, "mappings.json")
            synonyms_path = os.path.join(config_dir, "synonyms.json")

            if not os.path.exists(mappings_path):
                raise FileNotFoundError(f"Missing mappings.json at {mappings_path}")

            theme_name = os.path.splitext(os.path.basename(self.selected_apk))[0]
            theme_name = "".join([c if c.isalnum() else "_" for c in theme_name]).strip("_")

            with open(mappings_path, 'r') as f:
                mappings = json.load(f)

            synonyms = {}
            if os.path.exists(synonyms_path):
                with open(synonyms_path, 'r') as f:
                    synonyms = json.load(f)

            inherits = self.inherits_row.get_text()
            should_install = self.install_switch.get_active()

            result_path = converter.convert_apk(
                self.selected_apk,
                mappings,
                synonyms,
                self.output_folder,
                theme_name,
                inherits,
                install=should_install
            )

            GLib.idle_add(self.on_conversion_finished, True, result_path)

        except Exception as e:
            print(f"Conversion Error: {e}")
            GLib.idle_add(self.on_conversion_finished, False, str(e))

    def on_conversion_finished(self, success, message):
        self.spinner.stop()
        self.run_btn.set_sensitive(True)
        self.apk_row.set_sensitive(True)
        self.inherits_row.set_sensitive(True)
        self.install_switch.set_sensitive(True)

        if success:
            self.status_label.set_label("Completed")
            toast = Adw.Toast.new(f"Success! Output: {message}")
            toast.set_timeout(5)
            self.toast_overlay.add_toast(toast)
        else:
            self.status_label.set_label("Error")
            toast = Adw.Toast.new(f"Error: {message}")
            self.toast_overlay.add_toast(toast)

    def show_about_dialog(self, btn):
        dialog = Adw.AboutDialog(
            application_name="Isomorphicon",
            developer_name="vdoesui",
            version="0.1.0",
            copyright="© 2025 vdoesui",
            website="https://github.com/vdoesui/Isomorphicon",
            license_type=Gtk.License.CUSTOM,
            license="EUPL 1.2"
        )
        dialog.add_legal_section(
            "Apktool",
            "Copyright © 2010 Ryszard Wiśniewski, Connor Tumbleson",
            Gtk.License.APACHE_2_0,
            None
        )
        dialog.present(self)
