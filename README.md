Extract and convert Android icon packs to Linux theme format.

Automatically converts Android `.apk` icon packs into standard Linux icon themes compatible with KDE Plasma, GNOME, XFCE, and other desktop environments.

## Requirements

- Python 3.7+
- Pillow
- apktool (system dependency)

## Installation

```bash
git clone https://github.com/vdoesui/Isomorphicon.git
cd Isomorphicon
pip install -r requirements.txt
```

Ensure `apktool` is installed and in your PATH.

## Usage

Basic usage:

```bash
python main.py path/to/iconpack.apk
```

Install to system themes:

```bash
python main.py path/to/iconpack.apk --install
```

Custom theme parents:

```bash
python main.py path/to/iconpack.apk --inherits "Adwaita,hicolor"
```

### Options

- `-i, --install` — Install theme to `~/.local/share/icons/`
- `--inherits` — Comma-separated list of parent themes (default: `breeze-dark,breeze,Adwaita,hicolor`)

## Output

Generated theme structure:

```
theme_name/
├── index.theme
├── apps/
│   └── 512x512/
└── places/
    └── 512x512/
```

## How it works

IconBridge processes Android icon packs in three phases:

1. **Parse official mappings** from `appfilter.xml` and group candidate icons by package
2. **Mildly intelligent search** with fuzzy matching to find icons when official mappings don't exist
3. **Extract remaining** icons that weren't explicitly mapped in case they happen to match an unmapped app.

The fuzzy matcher scores files based on:
- Exact name match (1000)
- Full token match (800)
- Acronym match (600)
- Prefix match (500)
- Fuzzy substring match (0-100)

## Contributing

Contributions are welcome. The mapping definitions in `Config/mappings.json` can be improved by adding new applications or refining existing entries. If you find icons that aren't being matched correctly, feel free to submit improvements. The mappings are indeed as shitty as they look.

## Disclaimer

This software is provided as-is without warranty. The authors are not responsible for any damages caused by its use, including data loss or system issues. Use at your own risk.

## License

IconBridge is licensed under the European Union Public Licence v1.2 (EUPL-1.2).

Icon themes are derivative works of the original Android icon packs and remain subject to their respective licenses, what you do, or can do, or can't do, is your problem. Check whatever the author says. (No apks or icon packs are included, but still, don't go around breaking icon pack copyright or whatever)
