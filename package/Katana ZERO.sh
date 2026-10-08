#!/bin/bash

XDG_DATA_HOME=${XDG_DATA_HOME:-$HOME/.local/share}

if [ -d "/opt/system/Tools/PortMaster/" ]; then
  controlfolder="/opt/system/Tools/PortMaster"
elif [ -d "/opt/tools/PortMaster/" ]; then
  controlfolder="/opt/tools/PortMaster"
elif [ -d "$XDG_DATA_HOME/PortMaster/" ]; then
  controlfolder="$XDG_DATA_HOME/PortMaster"
else
  controlfolder="/roms/ports/PortMaster"
fi

source "$controlfolder/control.txt"
[ -f "${controlfolder}/mod_${CFW_NAME}.txt" ] && source "${controlfolder}/mod_${CFW_NAME}.txt"
get_controls

# Variables
GAMEDIR="/$directory/ports/katanazero"

# CD and set logging
cd "$GAMEDIR" || exit 1
> "$GAMEDIR/log.txt" && exec > >(tee "$GAMEDIR/log.txt") 2>&1

# ARM64 compatibility: this template includes only the aarch64 loader.
if [ "$DEVICE_ARCH" != "aarch64" ] || [ -z "$GPTOKEYB2" ]; then
    echo "This package requires ARM64 firmware and current PortMaster with gptokeyb2."
    pm_finish
    exit 1
fi

# Setup permissions
$ESUDO chmod +xwr "$GAMEDIR/gmloadernext.aarch64"
$ESUDO chmod +xr "$GAMEDIR/tools/splash"
$ESUDO chmod +xr "$GAMEDIR/tools/patchscript"


# Exports
export SDL_GAMECONTROLLERCONFIG="$sdl_controllerconfig"

# Check if we need to patch the game
# Android compatibility: an existing game.port does not need a patch log.
if [ ! -s "$GAMEDIR/game.port" ] || [ -f "$GAMEDIR/assets/katanazero.apk" ]; then
    export PATCHER_FILE="$GAMEDIR/tools/patchscript"
    export PATCHER_GAME="$(basename "${0%.*}")"
    export PATCHER_TIME="2 to 5 minutes"
    export PATCHER_QUESTIONS="$GAMEDIR/tools/patcher-name.lua"
    export controlfolder
    export ESUDO
    if [ -f "$controlfolder/utils/patcher.txt" ] &&
       [ -f "$controlfolder/runtimes/love_11.5/love.txt" ] &&
       [ -x "$controlfolder/runtimes/love_11.5/love.$DEVICE_ARCH" ] &&
       [ -n "$GPTOKEYB" ]; then
        source "$controlfolder/utils/patcher.txt"
    else
        echo "The patch screen requires current PortMaster with its Love 11.5 runtime."
        echo "Update PortMaster, then launch Katana ZERO again."
        pm_finish
        exit 1
    fi
    if [ ! -s "$GAMEDIR/game.port" ] || [ -f "$GAMEDIR/patcherr.txt" ] ||
       [ -f "$GAMEDIR/assets/katanazero.apk" ]; then
        echo "Preparation failed. Check katanazero/patcherr.txt."
        pm_finish
        exit 1
    fi
fi

# Display loading splash
if [ -f "$GAMEDIR/splash.png" ]; then
    [ "$CFW_NAME" == "muOS" ] && $ESUDO "$GAMEDIR/tools/splash" "$GAMEDIR/splash.png" 1
    $ESUDO "$GAMEDIR/tools/splash" "$GAMEDIR/splash.png" 8000 &
fi

# Assign gptokeyb and load the game
$GPTOKEYB2 "gmloadernext.aarch64" -c "katanazero.ini" &
pm_platform_helper "$GAMEDIR/gmloadernext.aarch64" >/dev/null
./gmloadernext.aarch64 -c gmloader.json

# Cleanup
pm_finish
