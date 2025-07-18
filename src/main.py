# main.py
#
# Copyright 2025 Stephan Raabe
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
import gi
import subprocess
import os
import pathlib

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw
from .window import DotfilesSidebarWindow

# The main application singleton class.
class DotfilesSidebarApplication(Adw.Application):

    home_folder = os.path.expanduser('~')
    block_reload = True

    def __init__(self):
        super().__init__(application_id='com.ml4w.sidebar',
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS)

        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('keybindings', self.on_keybindings_action)
        self.create_action('welcome', self.on_welcome_action)
        self.create_action('settings', self.on_settings_action)
        self.create_action('hyprland', self.on_hyprland_action)
        self.create_action('wallpaper', self.on_wallpaper_action)
        self.create_action('wallpaper_random', self.on_wallpaper_random_action)
        self.create_action('wallpaper_effects', self.on_wallpaper_effects_action)
        self.create_action('screenshot', self.on_screenshot_action)
        self.create_action('picker', self.on_picker_action)
        self.create_action('waybar_theme', self.on_waybar_theme_action)
        self.create_action('waybar_reload', self.on_waybar_reload_action)
        self.create_action('waybar_quicklinks', self.on_waybar_quicklinks)
        self.create_action('theme_gtk', self.on_theme_gtk)
        self.create_action('theme_qt', self.on_theme_qt)
        self.create_action('theme_refresh', self.on_theme_refresh)

        self.current_cancellable = None

    # Called when the application is activated.
    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = DotfilesSidebarWindow(application=self)

        self.dock_toggle = win.dock_toggle
        self.gamemode_toggle = win.gamemode_toggle
        self.waybar_toggle = win.waybar_toggle
        self.emojipicker = ""
        self.terminal = ""
        self.editor = ""
        self.emoji_chooser = win.emoji_chooser

        win.waybar_toggle.connect("notify::active",self.on_waybar_toggle)
        win.dock_toggle.connect("notify::active",self.on_dock_toggle)
        win.gamemode_toggle.connect("notify::active",self.on_gamemode_toggle)
        win.emoji_chooser.connect("emoji-picked", lambda _chooser, emoji: subprocess.Popen(["flatpak-spawn", "--host", "wl-copy", emoji ]))

        self.loadWaybar()
        self.loadGamemode()
        self.loadDock()
        self.loadEmojiPicker()
        self.loadTerminal()
        self.loadEditor()
        self.block_reload = False

        win.present()

    def on_welcome_action(self, widget, _):
        subprocess.Popen(["flatpak-spawn", "--host", "flatpak", "run", "com.ml4w.welcome"])
        self.quit()

    def on_settings_action(self, widget, _):
        subprocess.Popen(["flatpak-spawn", "--host", "flatpak", "run", "com.ml4w.settings"])
        self.quit()

    def on_hyprland_action(self, widget, _):
        subprocess.Popen(["flatpak-spawn", "--host", "flatpak", "run", "com.ml4w.hyprlandsettings"])
        self.quit()

    def on_wallpaper_action(self, widget, _):
        task = Gio.Task.new(self, self.current_cancellable, self.on_open_waypaper_completed, None)
        # task.set_task_data("task_data", None) # Pass our custom data instance to the task
        task.run_in_thread(self.open_waypaper)

    def open_waypaper(self, task, source_object, task_data, cancellable):
        subprocess.Popen(["flatpak-spawn", "--host", "waypaper"])
        self.quit()

    def on_open_waypaper_completed(self, source_object, result, _):
        print("completed")

    def on_wallpaper_random_action(self, widget, _):
        subprocess.Popen(["flatpak-spawn", "--host", "waypaper", "--random"])

    def on_wallpaper_effects_action(self, widget, _):
        subprocess.Popen(["flatpak-spawn", "--host", "bash", "-c", self.home_folder + "/.config/hypr/scripts/wallpaper-effects.sh"])

    def on_screenshot_action(self, widget, _):
        subprocess.Popen(["flatpak-spawn", "--host", "bash", "-c", self.home_folder + "/.config/hypr/scripts/screenshot.sh"])
        self.quit()

    def on_picker_action(self, widget, _):
        subprocess.Popen(["flatpak-spawn", "--host", "bash", "-c", self.home_folder + "/.config/ml4w/settings/hyprpicker.sh"])
        self.quit()

    def on_waybar_theme_action(self, widget, _):
        subprocess.Popen(["flatpak-spawn", "--host", "bash", "-c", self.home_folder + "/.config/waybar/themeswitcher.sh"])

    def on_waybar_reload_action(self, widget, _):
        subprocess.Popen(["flatpak-spawn", "--host", "bash", "-c", self.home_folder + "/.config/waybar/launch.sh"])

    def on_waybar_toggle(self, widget, _):
        if not self.block_reload:
            if (os.path.exists(self.home_folder + "/.config/ml4w/settings/waybar-disabled")):
                os.remove(self.home_folder + "/.config/ml4w/settings/waybar-disabled")
            else:
                file = open(self.home_folder + "/.config/ml4w/settings/waybar-disabled", "w+")
            self.reloadWaybar()

    def on_gamemode_toggle(self, widget, _):
        if not self.block_reload:
            subprocess.Popen(["flatpak-spawn", "--host", "bash", self.home_folder + "/.config/hypr/scripts/gamemode.sh"])

    def on_dock_toggle(self, widget, _):
        if not self.block_reload:
            if (os.path.exists(self.home_folder + "/.config/ml4w/settings/dock-disabled")):
                os.remove(self.home_folder + "/.config/ml4w/settings/dock-disabled")
                subprocess.Popen(["flatpak-spawn", "--host", "bash", self.home_folder + "/.config/nwg-dock-hyprland/launch.sh"])
            else:
                file = open(self.home_folder + "/.config/ml4w/settings/dock-disabled", "w+")
                subprocess.Popen(["flatpak-spawn", "--host", "killall", "nwg-dock-hyprland"])

    def loadDock(self):
        if os.path.isfile(self.home_folder + "/.config/ml4w/settings/dock-disabled"):
            self.dock_toggle.set_active(False)
        else:
            self.dock_toggle.set_active(True)

    def loadGamemode(self):
        if os.path.isfile(self.home_folder + "/.config/ml4w/settings/gamemode-enabled"):
            self.gamemode_toggle.set_active(True)
        else:
            self.gamemode_toggle.set_active(False)

    def loadWaybar(self):
        if os.path.isfile(self.home_folder + "/.config/ml4w/settings/waybar-disabled"):
            self.waybar_toggle.set_active(False)
        else:
            self.waybar_toggle.set_active(True)

    # Open editor with quicklinks.conf
    def on_waybar_quicklinks(self, widget, _):
        subprocess.Popen(["flatpak-spawn", "--host", self.editor, self.home_folder + "/.config/ml4w/settings/waybar-quicklinks.json"])

    # Set GTK Theme
    def on_theme_gtk(self, widget, _):
        subprocess.Popen(["flatpak-spawn", "--host", "nwg-look"])

    # Set QT Theme
    def on_theme_qt(self, widget, _):
        subprocess.Popen(["flatpak-spawn", "--host", "qt6ct"])

    # Refresh GTK Theme
    def on_theme_refresh(self, widget, _):
        subprocess.Popen(["flatpak-spawn", "--host", "bash", self.home_folder + "/.config/hypr/scripts/gtk.sh"])

    # Load default app
    def loadEmojiPicker(self):
        with open(self.home_folder + "/.config/ml4w/settings/emojipicker.sh", 'r') as file:
            value = file.read()
        self.emojipicker = value.strip()

    # Load default app
    def loadTerminal(self):
        with open(self.home_folder + "/.config/ml4w/settings/terminal.sh", 'r') as file:
            value = file.read()
        self.terminal = value.strip()

    # Load editor app
    def loadEditor(self):
        with open(self.home_folder + "/.config/ml4w/settings/editor.sh", 'r') as file:
            value = file.read()
        self.editor = value.strip()

    def reloadWaybar(self):
        launch_script = self.home_folder + "/.config/waybar/launch.sh"
        subprocess.Popen(["flatpak-spawn", "--host", "setsid", launch_script, "1>/dev/null" ,"2>&1" "&"])

    def on_keybindings_action(self, widget, _):
        subprocess.Popen(["flatpak-spawn", "--host", "bash", self.home_folder + "/.config/hypr/scripts/keybindings.sh"])

    # Callback for the app.about action.
    def on_about_action(self, *args):
        about = Adw.AboutDialog(
            application_name="ML4W Sidebar App",
            application_icon='com.ml4w.sidebar',
            developer_name="Stephan Raabe",
            version="2.9.8.7",
            website="https://github.com/mylinuxforwork/dotfiles-sidebar",
            issue_url="https://github.com/mylinuxforwork/dotfiles-sidebar/issues",
            support_url="https://github.com/mylinuxforwork/dotfiles-sidebar/issues",
            copyright="© 2025 Stephan Raabe",
            license_type=Gtk.License.GPL_3_0_ONLY
        )
        about.present(self.props.active_window)

    # Add an application action.
    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)

# The application's entry point.
def main(version):
    app = DotfilesSidebarApplication()
    return app.run(sys.argv)
