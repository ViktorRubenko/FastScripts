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


class FastScriptsPlugin(PalettePlugin):
    @objc.python_method
    def settings(self):
        self.name = Glyphs.localize({"en": "FastScripts"})
        self.free_buttons = list(range(5))
        self.button_scripts = {}
        heapq.heapify(self.free_buttons)
        button_start = 0
        button_height = 10
        width, height = 150, 90
        self.paletteView = Window((width, height))
        self.paletteView.group = Group((0, 0, width, height))

        for _ in range(5):
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
            (-45, -15, 40, 10), "Add", callback=self.add_button, sizeStyle="mini"
        )

        self.paletteView.group.save_button = SquareButton(
            (5, -15, 40, 10), "Save", callback=self.save_scripts, sizeStyle="mini"
        )

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
    def save_scripts(self, sender):
        with open(os.path.join(BASEDIR_, "button_scripts.json"), "w") as json_file:
            json.dump(self.button_scripts, json_file, indent=4)

    @objc.python_method
    def load_scripts(self):
        if not os.path.exists(os.path.join(BASEDIR_, "button_scripts.json")):
            return
        with open(os.path.join(BASEDIR_, "button_scripts.json"), "r") as json_file:
            self.button_scripts.update(
                {
                    int(id_str): script_path
                    for id_str, script_path in json.load(json_file).items()
                }
            )
        for button_index, script_path in self.button_scripts.items():
            self.free_buttons.remove(button_index)
            self.init_button(button_index, script_path)

    @objc.python_method
    @staticmethod
    def exec_code(filepath, code):
        try:
            exec(code, globals())
        except Exception as e:
            print(str(e))
            Glyphs.showMacroWindow()

    @objc.python_method
    def add_button(self, sender):
        if self.free_buttons:
            button_index = heapq.heappop(self.free_buttons)
            try:
                filepath = GetOpenFile(
                    path="~/Library/Application Support/Glyphs/Scripts",
                    filetypes=["py"],
                )
            except:
                filepath = GetOpenFile(filetypes=["py"])
            if not filepath:
                return
            if not self.init_button(button_index, filepath):
                heapq.heappush(self.free_buttons, button_index)
                Message("Can't find scripts MenuTitle. Is the script correct?")

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
            if not self.free_buttons:
                self.paletteView.group.add_button.enable(False)
            return 1
