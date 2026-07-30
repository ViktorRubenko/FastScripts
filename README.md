# FastScripts

A [Glyphs](https://glyphsapp.com) palette plugin for running your favorite scripts with one click from the sidebar — no more digging through the Script menu.

<img src="https://github.com/ViktorRubenko/FastScripts/blob/master/FastScriptsScreenshot.png" width="350">

## Features

- Adds a palette section (Window → Palette) listing your pinned scripts as buttons
- One click to run a script, one click to unpin it
- Pins persist across restarts (stored in `Glyphs.defaults`)
- Works with Glyphs 2, 3, and 4

## Requirements

Glyphs 2, 3, or 4 on macOS.

## Installation

**Recommended:** Search for "FastScripts" in Window → Plugin Manager and click Install.

**Manual:**

```bash
git clone https://github.com/ViktorRubenko/FastScripts.git
```

Double-click `FastScripts.glyphsPalette`, or move it into `~/Library/Application Support/Glyphs 3/Plugins` (or the matching `Glyphs 4`/`Glyphs 2` folder), then restart Glyphs.

## Usage

1. Open the palette: Window → Palette.
2. Click **+** and pick a `.py` script file. The script must start with a `# MenuTitle: ...` comment (the same convention Glyphs uses for its own Script menu) — that comment becomes the button label.
3. Click a script's button to run it.
4. Click the **−** next to a script to unpin it.

## License

[Apache License 2.0](LICENSE)
