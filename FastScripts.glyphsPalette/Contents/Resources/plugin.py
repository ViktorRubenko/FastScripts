# -*- encoding: utf-8 -*-
from __future__ import division, print_function, unicode_literals
import objc
from GlyphsApp import *
from GlyphsApp.plugins import *

if int(Glyphs.versionNumber) == 3:
    from GlyphsApp import GSMouseOverButton, GSScriptingHandler
from AppKit import (
    NSButton,
    NSMiniControlSize,
    NSShadowlessSquareBezelStyle,
    NSCircularBezelStyle,
    NSLayoutConstraint,
    NSLayoutAttributeHeight,
    NSLayoutAttributeWidth,
    NSLayoutAttributeTop,
    NSLayoutAttributeLeading,
    NSLayoutAttributeTrailing,
    NSLayoutAttributeBottom,
    NSLayoutRelationEqual,
    NSLineBreakByTruncatingTail,
)
import re
import io
import os

try:
    scriptsPath = (
        GSGlyphsInfo.applicationSupportPath() + "/Scripts"
    )  # Glyphs 3
except:
    scriptsPath = (
        GSGlyphsInfo.applicationSupportFolder() + "/Scripts"
    )  # Glyphs 2

button_height = 14
button_gap = 4
defaultsName = "com.ViktorRubenko.FastScripts.button_scripts"
notificationName = "com.ViktorRubenko.FastScripts.reload"


def newButton(frame, title, action, target):
    new_button = NSButton.alloc().initWithFrame_(frame)
    new_button.setBezelStyle_(NSShadowlessSquareBezelStyle)
    new_button.setControlSize_(NSMiniControlSize)
    new_button.setTitle_(title)
    new_button.setAction_(action)
    new_button.setTarget_(target)
    new_button.setTranslatesAutoresizingMaskIntoConstraints_(False)
    constraint = NSLayoutConstraint.constraintWithItem_attribute_relatedBy_toItem_attribute_multiplier_constant_(
        new_button,
        NSLayoutAttributeHeight,
        NSLayoutRelationEqual,
        None,
        0,
        1.0,
        button_height,
    )
    new_button.addConstraint_(constraint)
    new_button.setContentCompressionResistancePriority_forOrientation_(100, NSLayoutConstraintOrientationHorizontal)
    return new_button


def removeButton(frame, imageName, action, target):
    if int(Glyphs.versionNumber) == 2:
        new_button = NSButton.alloc().initWithFrame_(frame)
    else:
        new_button = GSMouseOverButton.alloc().initWithFrame_(frame)
    new_button.setBezelStyle_(NSCircularBezelStyle)
    new_button.setBordered_(False)
    new_button.setImage_(NSImage.imageNamed_(imageName))
    new_button.setControlSize_(NSMiniControlSize)
    new_button.setTitle_("")
    new_button.setAction_(action)
    new_button.setTarget_(target)
    new_button.setTranslatesAutoresizingMaskIntoConstraints_(False)
    constraint = NSLayoutConstraint.constraintWithItem_attribute_relatedBy_toItem_attribute_multiplier_constant_(
        new_button,
        NSLayoutAttributeHeight,
        NSLayoutRelationEqual,
        None,
        0,
        1.0,
        18,
    )
    new_button.addConstraint_(constraint)
    constraint = NSLayoutConstraint.constraintWithItem_attribute_relatedBy_toItem_attribute_multiplier_constant_(
        new_button,
        NSLayoutAttributeWidth,
        NSLayoutRelationEqual,
        None,
        0,
        1.0,
        18,
    )
    new_button.addConstraint_(constraint)
    return new_button


class FastScripts(PalettePlugin):
    @objc.python_method
    def settings(self):
        self.name = Glyphs.localize({"en": "FastScripts"})
        self.button_scripts = []
        self.dialog = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 150, 100))
        self.dialog.setTranslatesAutoresizingMaskIntoConstraints_(False)
        self.heightConstraint = NSLayoutConstraint.constraintWithItem_attribute_relatedBy_toItem_attribute_multiplier_constant_(
            self.dialog,
            NSLayoutAttributeHeight,
            NSLayoutRelationEqual,
            None,
            0,
            1.0,
            0,
        )
        self.dialog.addConstraint_(self.heightConstraint)
        self.buttonContainer = NSView.alloc().initWithFrame_(
            NSMakeRect(0, 15, 150, 85)
        )
        self.buttonContainer.setTranslatesAutoresizingMaskIntoConstraints_(
            False
        )
        self.dialog.addSubview_(self.buttonContainer)
        constaint = NSLayoutConstraint.constraintWithItem_attribute_relatedBy_toItem_attribute_multiplier_constant_(
            self.dialog,
            NSLayoutAttributeTop,
            NSLayoutRelationEqual,
            self.buttonContainer,
            NSLayoutAttributeTop,
            1.0,
            0,
        )
        self.dialog.addConstraint_(constaint)
        constaint = NSLayoutConstraint.constraintWithItem_attribute_relatedBy_toItem_attribute_multiplier_constant_(
            self.dialog,
            NSLayoutAttributeLeading,
            NSLayoutRelationEqual,
            self.buttonContainer,
            NSLayoutAttributeLeading,
            1.0,
            0,
        )
        self.dialog.addConstraint_(constaint)
        constaint = NSLayoutConstraint.constraintWithItem_attribute_relatedBy_toItem_attribute_multiplier_constant_(
            self.dialog,
            NSLayoutAttributeTrailing,
            NSLayoutRelationEqual,
            self.buttonContainer,
            NSLayoutAttributeTrailing,
            1.0,
            0,
        )
        self.dialog.addConstraint_(constaint)
        constaint = NSLayoutConstraint.constraintWithItem_attribute_relatedBy_toItem_attribute_multiplier_constant_(
            self.dialog,
            NSLayoutAttributeBottom,
            NSLayoutRelationEqual,
            self.buttonContainer,
            NSLayoutAttributeBottom,
            1.0,
            15,
        )
        self.dialog.addConstraint_(constaint)
        self.add_button = removeButton(
            NSMakeRect(8, 0, 18, 18),
            "NSAddTemplate",
            self.addScript_,
            self,
        )
        self.dialog.addSubview_(self.add_button)
        self.setupButtons_()
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self, self.setupButtons_, notificationName, None
        )

    def __del__(self):
        NSNotificationCenter.defaultCenter().removeObserver_name_object_(
            self, notificationName, None
        )

    def setupButtons_(self, notification=None):
        self.load_data()
        button_start = 0
        quantity = len(self.button_scripts)
        width, height = 160, quantity * (button_height + button_gap)
        self.heightConstraint.setConstant_(height + 15)
        if quantity == 0:
            return
        self.buttonContainer.setSubviews_([])
        for button_script in self.button_scripts:
            script_button = newButton(
                NSMakeRect(
                    8,
                    height - button_start - button_height,
                    width - 26,
                    button_height,
                ),
                "_",
                self.runScriptCallback_,
                self,
            )
            self.init_button(script_button, button_script)
            script_button.setLineBreakMode_(NSLineBreakByTruncatingTail)
            self.buttonContainer.addSubview_(script_button)
            remove_button = removeButton(
                NSMakeRect(width - 16, height - button_start - 17, 18, 18),
                "NSRemoveTemplate",
                self.removeScriptCallback_,
                self,
            )
            remove_button.setRepresentedObject_(button_script)
            self.buttonContainer.addSubview_(remove_button)
            constaint = NSLayoutConstraint.constraintWithItem_attribute_relatedBy_toItem_attribute_multiplier_constant_(
                script_button,
                NSLayoutAttributeLeading,
                NSLayoutRelationEqual,
                self.buttonContainer,
                NSLayoutAttributeLeading,
                1.0,
                8,
            )
            self.buttonContainer.addConstraint_(constaint)
            constaint = NSLayoutConstraint.constraintWithItem_attribute_relatedBy_toItem_attribute_multiplier_constant_(
                script_button,
                NSLayoutAttributeTrailing,
                NSLayoutRelationEqual,
                remove_button,
                NSLayoutAttributeLeading,
                1.0,
                -2,
            )
            self.buttonContainer.addConstraint_(constaint)
            constaint = NSLayoutConstraint.constraintWithItem_attribute_relatedBy_toItem_attribute_multiplier_constant_(
                remove_button,
                NSLayoutAttributeTrailing,
                NSLayoutRelationEqual,
                self.buttonContainer,
                NSLayoutAttributeTrailing,
                1.0,
                -8,
            )
            self.buttonContainer.addConstraint_(constaint)
            button_start += button_height + button_gap
        self.dialog.invalidateIntrinsicContentSize()

    @objc.python_method
    def load_data(self):
        if Glyphs.defaults[defaultsName]:
            self.button_scripts = list(
                sp
                for sp in Glyphs.defaults[defaultsName]
                if os.path.exists(sp)
            )

    @objc.python_method
    def save_data(self):
        Glyphs.defaults[defaultsName] = self.button_scripts

    @objc.python_method
    def dataHasChanged(self):
        self.save_data()
        NSNotificationCenter.defaultCenter().postNotificationName_object_(
            notificationName, None
        )

    def runScriptCallback_(self, button):
        if int(Glyphs.versionNumber) == 3:
            scriptPath = button.representedObject()
            scriptHandler = GSScriptingHandler.alloc()
            scriptHandler.runMacroFile_(scriptPath)
        else:
            code = button.representedObject()
            exec(code, globals())

    def removeScriptCallback_(self, button):
        self.button_scripts.remove(button.representedObject())
        self.dataHasChanged()

    def addScript_(self, sender):
        try:
            filepaths = GetOpenFile(
                path=scriptsPath,
                filetypes=["py"],
                allowsMultipleSelection=True,
            )
        except:
            import traceback

            print(traceback.format_exc())
        if not filepaths or len(filepaths) == 0:
            return
        self.button_scripts.extend(filepaths)
        self.dataHasChanged()

    @objc.python_method
    def init_button(self, button, script_path):
        with io.open(script_path, "r", encoding="utf-8") as f:
            code = f.read()

            menu_title = re.findall(
                r"^#\s*MenuTitle:\s*(.*)", code, flags=re.IGNORECASE
            )
            if not menu_title:
                return

            if int(Glyphs.versionNumber) == 2:
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
                button.setRepresentedObject_(code)
            else:
                button.setRepresentedObject_(script_path)

            menu_title = menu_title[0]
            button.setTitle_(menu_title)
