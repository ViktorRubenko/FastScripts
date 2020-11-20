# -*- encoding: utf-8 -*-
from __future__ import division, print_function, unicode_literals
import objc
from GlyphsApp import *
from GlyphsApp.plugins import *
import re
import io
import os
import heapq
import json
from vanilla import *


BASEDIR_ = os.path.dirname(__file__)


class SettingsWindow:
    def __init__(self, plugin):
        self.w = FloatingWindow((120, 55))
        self.w.quantity_textbox = TextBox(
            (10, 10, -10, 15), "Number of scripts:", sizeStyle="mini"
        )
        self.w.quantity_edittext = EditText(
            (10, 25, 50, 22),
            callback=None,
            placeholder="1..20",
        )
        self.w.ok_button = Button(
            (70, 25, -10, 22),
            "OK",
            callback=lambda sender, plugin=plugin: self.update_settings(sender, plugin),
        )
        self.w.open()

    def update_settings(self, sender, plugin):
        try:
            quantity = quantity = int(self.w.quantity_edittext.get())
            if 1 <= quantity <= 20:
                plugin.quantity = quantity
                plugin.save_data()
                Message("Reload Glyphs.app to apply settings")
                self.w.close()
            else:
                print("Number of scripts must in [1..20] range!")
                Glyphs.showMacroWindow()
        except Exception as e:
            print(str(e))
            Glyphs.showMacroWindow()


class FastScripts(PalettePlugin):
    @objc.python_method
    def settings(self):
        self.name = Glyphs.localize({"en": "FastScripts"})
        self.quantity = 5
        self.button_scripts = {}
        self.load_data()
        self.free_buttons = list(range(self.quantity))
        button_start = 0
        button_height = 10
        width, height = 150, self.quantity * (button_height + 5) + 15
        self.paletteView = Window((width, height))
        self.paletteView.group = Group((0, 0, width, height))

        for _ in range(self.quantity):
            setattr(
                self.paletteView.group,
                "button{}".format(_),
                SquareButton(
                    (10, button_start, -35, button_height),
                    "",
                    callback=None,
                    sizeStyle="mini",
                ),
            )
            button = getattr(self.paletteView.group, "button{}".format(_))
            button.show(False)
            setattr(
                self.paletteView.group,
                "button{}_hide".format(_),
                SquareButton(
                    (-35, button_start, 30, button_height),
                    "X",
                    callback=lambda sender, id=_: self.hide(id),
                    sizeStyle="mini",
                ),
            )
            getattr(self.paletteView.group, "button{}_hide".format(_)).show(False)
            button_start += button_height + 5

        self.paletteView.group.add_button = SquareButton(
            (-50, -15, 45, 10), "Add", callback=self.add_script, sizeStyle="mini"
        )

        self.paletteView.group.settings_button = SquareButton(
            (55, -15, -55, 10),
            "Settings",
            callback=self.open_settings,
            sizeStyle="mini",
        )

        self.paletteView.group.save_button = SquareButton(
            (5, -15, 45, 10), "Save", callback=self.save_data, sizeStyle="mini"
        )
        if self.button_scripts:
            self.load_scripts()
        self.dialog = self.paletteView.group.getNSView()

    @objc.python_method
    def hide(self, id):
        heapq.heappush(self.free_buttons, id)
        getattr(self.paletteView.group, "button{}".format(id)).show(False)
        getattr(self.paletteView.group, "button{}_hide".format(id)).show(False)
        self.button_scripts.pop(id)
        if not self.paletteView.group.add_button.isEnabled():
            self.paletteView.group.add_button.enable(True)

    @objc.python_method
    def open_settings(self, sender):
        SettingsWindow(self)

    @objc.python_method
    def load_data(self):
        filepath = os.path.join(BASEDIR_, "data.json")
        if os.path.exists(filepath):
            with open(filepath, "r") as json_file:
                data = json.load(json_file)
            self.quantity = data.get("quantity", 5)
            button_scripts = data.get("button_scripts", {})
            self.button_scripts = {
                int(id_str): script_path
                for id_str, script_path in button_scripts.items()
                if int(id_str) < self.quantity
            }

    @objc.python_method
    def save_data(self, sender=None):
        with open(os.path.join(BASEDIR_, "data.json"), "w") as json_file:
            json.dump(
                {"quantity": self.quantity, "button_scripts": self.button_scripts},
                json_file,
                indent=4,
            )

    @objc.python_method
    def load_scripts(self):
        for button_index, script_path in self.button_scripts.items():
            self.free_buttons.remove(button_index)
            self.init_button(button_index, script_path)
        if not self.free_buttons:
            self.paletteView.group.add_button.enable(False)

    @objc.python_method
    @staticmethod
    def exec_code(filepath, code):
        try:
            exec(code, globals())
        except Exception as e:
            print(str(e))
            Glyphs.showMacroWindow()

    @objc.python_method
    def add_script(self, sender):
        try:
            filepaths = GetOpenFile(
                path="~/Library/Application Support/Glyphs/Scripts",
                filetypes=["py"],
                allowsMultipleSelection=True,
            )
        except:
            filepaths = GetOpenFile(
                filetypes=["py"],
                allowsMultipleSelection=True,
            )
        if not filepaths:
            return
        if len(filepaths) > len(self.free_buttons):
            print(
                "{} scripts were selected for {} buttons".format(
                    len(filepaths),
                    len(self.free_buttons),
                )
            )
            Glyphs.showMacroWindow()
        for filepath in filepaths:
            if self.free_buttons:
                button_index = heapq.heappop(self.free_buttons)
                if not self.init_button(button_index, filepath):
                    heapq.heappush(self.free_buttons, button_index)
                    print("{}\nCan't find scripts MenuTitle".format(filepath))
                    Glyphs.showMacroWindow()
            else:
                break
        if not self.free_buttons:
            self.paletteView.group.add_button.enable(False)

    @objc.python_method
    def init_button(self, button_index, script_path):
        button = getattr(self.paletteView.group, "button{}".format(button_index))
        button_hide = getattr(
            self.paletteView.group, "button{}_hide".format(button_index)
        )
        with io.open(script_path, "r", encoding="utf-8") as f:
            code = f.read()

            menu_title = re.findall(
                r"^#\s*MenuTitle:\s*(.*)", code, flags=re.IGNORECASE
            )
            if not menu_title:
                return

            code = code.splitlines()
            main_code = False
            for line_index, line in enumerate(code):
                if line.startswith("#") and "utf" in line:
                    code[line_index] = ""
                    continue
                if "__main__" in line:
                    code[line_index] = ""
                    main_code = True
                    continue
                if main_code:
                    if line.startswith("\t"):
                        rep = "\t"
                    else:
                        rep = "    "
                    code[line_index] = line.replace(rep, "", 1)
            code = "\n".join(code)

            self.button_scripts[button_index] = script_path
            menu_title = menu_title[0]
            button._setCallback(lambda sender: self.exec_code(script_path, code))
            button.setTitle(menu_title)
            button.show(True)
            button_hide.show(True)
            return 1
