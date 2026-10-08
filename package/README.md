## Notes

Thanks to [Askiisoft](https://askiisoft.com/) for creating **Katana ZERO**, an action platformer with sword combat, bullet deflection and time manipulation. PortMaster adaptation by **Pixelforge Ports (Ronax)**.

This BYO data package is for **ARM64 (aarch64)** Linux firmware with **glibc 2.30 or newer**, current **PortMaster**, **gptokeyb2** and **Python 3**. The base build was reported working on **RG34XX SP with muOS**, including menus, gameplay, sound, controller input and saving. The BYO first-launch flow and other devices still need handheld testing. R36S, ArkOS and ROCKNIX are further testing targets; this package requires ARM64 firmware.

## Supply Katana ZERO Android APK

1. Install this ZIP through **PortMaster Auto Install** to register the cover and screenshot in your firmware's ports menu. For a manual installation, extract it into your firmware's **Ports** directory; **Katana ZERO.sh** and the **katanazero** folder must be next to each other, but artwork registration requires PortMaster installation.
2. Supply your own legally obtained, supported **Katana ZERO Android v1.1.10 APK**. Rename it to **katanazero.apk**. Enable file extensions in Explorer to check the full filename.
3. Copy it to **`<ports directory>/katanazero/assets/katanazero.apk`**.
4. Launch **Katana ZERO** from your firmware's ports menu. The **PortMaster patch screen** opens on first launch. Press **A** when prompted to begin; it checks the APK and prepares **`katanazero/game.port`**. Press **A** at the completion message to start the game. Allow several minutes and keep the handheld powered on during preparation.
5. Later launches use the prepared game automatically.

Reference APK SHA-256 (the tested input):
```text
d21c8319aecb655ebbe8544f3c92e5213c83bdc6e32ca79c7d3f14e02cb844e7
```

The importer checks the APK's original game assets and ARM64 runner. The version number alone does not guarantee compatibility. Other APK builds, and Steam or GOG desktop game files, are unsupported by this importer. The [original game's Steam page](https://store.steampowered.com/app/460950/Katana_ZERO/) is a link to support the developer; the desktop purchase does not supply the Android APK used here.

Allow space for your APK and approximately **251 MB** for the prepared game. Replacing an existing prepared game also needs temporary space for another archive. After successful preparation, the input remains as **`assets/katanazero.apk.imported`** (or a numbered backup). You can move that backup off the SD card once the game works.

Back up **`katanazero/saves/`** before updating. Preparation preserves existing saves. If startup fails, check **`katanazero/log.txt`** and **`katanazero/patcherr.txt`**. A failed import keeps the input APK and any previous prepared game; correct or replace the APK and launch again. When reporting a problem, include the device, firmware version, reproduction steps and logs. Share this BYO ZIP without your APK, prepared game or personal saves.

To apply this update to an installed port, back up your saves and install the updated ZIP through **PortMaster Auto Install** again. This registers the artwork under **Katana ZERO** without deleting existing game data or saves. Reopen the ports list afterward. On muOS, the menu theme must display box art. The patch screen uses PortMaster's included **Love 11.5** runtime; update PortMaster if the launcher reports that it is missing. A prepared game with no new APK starts directly without the patch screen.

## Controls

The port uses the game's native controller bindings. The table describes default button positions and Xbox labels; the printed face-button letters on your handheld can differ. Follow the in-game prompts if you change the bindings.

| Control | Action |
|---|---|
| D-pad / left stick | Move / navigate |
| Down | Crouch |
| Bottom face button (Xbox A) | Jump / confirm / advance dialogue / pause replay |
| Left face button (Xbox X) | Sword attack |
| Right face button (Xbox B) | Use item / back |
| Top face button (Xbox Y) | Interact / walk / leave replay |
| L2 / LT | Slow time / rewind replay |
| R2 / RT | Dodge roll / advance replay |
| Start | Pause |
| Select + Start | Firmware exit shortcut on most devices; save through the game first |

Use the game's controller settings to remap actions. PortMaster supplies the firmware's exit shortcut.
