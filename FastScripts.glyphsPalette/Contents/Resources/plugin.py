# -*- encoding: utf-8 -*-
from __future__ import division, print_function, unicode_literals


import re
import io
import os
import platform
import objc
from AppKit import (
    NSButton,
    NSFont,
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
    NSLayoutConstraintOrientationHorizontal,
    NSImage,
    NSView,
    NSNotificationCenter,
    NSMakeRect,
    NSOpenPanel,
    NSModalResponseOK,
)
try:
    from AppKit import NSBezelStyleRecessed, NSButtonTypeMomentaryLight
    hasRecessedStyleImported = True
except:
    hasRecessedStyleImported = False

from GlyphsApp import Glyphs, GSGlyphsInfo
from GlyphsApp.plugins import PalettePlugin

if int(Glyphs.versionNumber) >= 3:
    GSMouseOverButton = objc.lookUpClass("GSMouseOverButton")
    GSScriptingHandler = objc.lookUpClass("GSScriptingHandler")
else:
    GSMouseOverButton = NSButton
    GSScriptingHandler = objc.lookUpClass("GSMenu")


try:
    scriptsPath = (
        GSGlyphsInfo.applicationSupportPath() + "/Scripts"
    )  # Glyphs 3
except:
    scriptsPath = (
        GSGlyphsInfo.applicationSupportFolder() + "/Scripts"
    )  # Glyphs 2

button_height = 18 if hasRecessedStyleImported else 14  # I think these have no impact anymore
button_gap = 1 if hasRecessedStyleImported else 4       # I think these have no impact anymore
defaultsName = "com.ViktorRubenko.FastScripts.button_scripts"
notificationName = "com.ViktorRubenko.FastScripts.reload"


def add_constraint(owner, item, attribute, other=None, other_attribute=0, multiplier=1.0, constant=0):
    """Build an NSLayoutConstraint (item.attribute = multiplier * other.attribute + constant) and add it to owner."""
    owner.addConstraint_(
        NSLayoutConstraint.constraintWithItem_attribute_relatedBy_toItem_attribute_multiplier_constant_(
            item, attribute, NSLayoutRelationEqual, other, other_attribute, multiplier, constant
        )
    )


def newButton(frame, title, action, target):
    new_button = NSButton.alloc().initWithFrame_(frame)
    if hasRecessedStyleImported:
        osVersion = int(platform.mac_ver()[0].split(".")[0])
        if osVersion >= 10:  # NSBezelStyleRecessed looks oddly dark in macOS 10.
            new_button.setBezelStyle_(NSBezelStyleRecessed)
            new_button.setButtonType_(NSButtonTypeMomentaryLight)
    else:
        new_button.setBezelStyle_(NSShadowlessSquareBezelStyle)
    new_button.setControlSize_(NSMiniControlSize)
    new_button.setTitle_(title)
    new_button.setFont_(NSFont.systemFontOfSize_(10))
    new_button.setAction_(action)
    new_button.setTarget_(target)
    new_button.setTranslatesAutoresizingMaskIntoConstraints_(False)
    add_constraint(new_button, new_button, NSLayoutAttributeHeight, constant=button_height)
    new_button.setContentCompressionResistancePriority_forOrientation_(100, NSLayoutConstraintOrientationHorizontal)
    return new_button


def removeButton(frame, imageName, action, target):
    new_button = GSMouseOverButton.alloc().initWithFrame_(frame)
    new_button.setBezelStyle_(NSCircularBezelStyle)
    new_button.setBordered_(False)
    new_button.setImage_(NSImage.imageNamed_(imageName))
    new_button.setControlSize_(NSMiniControlSize)
    new_button.setTitle_("")
    new_button.setAction_(action)
    new_button.setTarget_(target)
    new_button.setTranslatesAutoresizingMaskIntoConstraints_(False)
    add_constraint(new_button, new_button, NSLayoutAttributeHeight, constant=button_height)
    add_constraint(new_button, new_button, NSLayoutAttributeWidth, constant=18)
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
        # Pin buttonContainer to fill dialog (bottom leaves room for the add button row).
        for attribute, offset in (
            (NSLayoutAttributeTop, 0),
            (NSLayoutAttributeLeading, 0),
            (NSLayoutAttributeTrailing, 0),
            (NSLayoutAttributeBottom, 15),
        ):
            add_constraint(self.dialog, self.dialog, attribute, self.buttonContainer, attribute, constant=offset)
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
        for subview in list(self.buttonContainer.subviews()):
            subview.removeFromSuperview()
        if quantity == 0:
            return
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
                NSMakeRect(width - 16, height - button_start - 15, button_height, 18),
                "NSRemoveTemplate",
                self.removeScriptCallback_,
                self,
            )
            remove_button.setRepresentedObject_(button_script)
            self.buttonContainer.addSubview_(remove_button)
            # script_button fills the row, remove_button sits flush at the trailing edge.
            add_constraint(self.buttonContainer, script_button, NSLayoutAttributeLeading, self.buttonContainer, NSLayoutAttributeLeading, constant=8)
            add_constraint(self.buttonContainer, script_button, NSLayoutAttributeTrailing, remove_button, NSLayoutAttributeLeading, constant=-2)
            add_constraint(self.buttonContainer, remove_button, NSLayoutAttributeTrailing, self.buttonContainer, NSLayoutAttributeTrailing, constant=-8)
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
        scriptPath = button.representedObject()
        if int(Glyphs.versionNumber) >= 4:
            GSScriptingHandler.runScriptFile_filePath_(scriptPath, scriptPath)
        else:
            GSScriptingHandler.alloc().runMacroFile_(scriptPath)

    def removeScriptCallback_(self, button):
        self.button_scripts.remove(button.representedObject())
        self.dataHasChanged()

    def addScript_(self, sender):
        filepaths = None
        try:
            panel = NSOpenPanel.new()
            panel.setCanChooseFiles_(True)
            panel.setCanChooseDirectories_(False)
            panel.setCanCreateDirectories_(True)
            panel.setAllowsMultipleSelection_(True)
            panel.setDirectory_(scriptsPath)
            panel.setAllowedFileTypes_(["py"])
            if panel.runModal() == NSModalResponseOK:
                filepaths = list(panel.filenames())
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

            button.setRepresentedObject_(script_path)

            menu_title = menu_title[0]
            button.setTitle_(menu_title)
