#!/bin/bash

INSTALL_LOC="/home/pi/RetroPie/scripts/emulationstation_bgm.py"
INI_LOC="/home/pi/RetroPie/scripts/addons.ini"
SECTION="EmulationStationBGM"
BACKTITLE="Techitechi-chan's Toolbox"
TITLE="EmulationStation BGM"
INFO_DELAY=3
ERROR_DELAY=5



function extract_config() {
    # Generate short python script to print out the variable
    pyscript="import ConfigParser
config = ConfigParser.ConfigParser()
config.read(\"$INI_LOC\")
print(config.get('$SECTION', \"$1\"))"
    # Use python to obtain the variable and print out to echo
    echo "$(echo "$pyscript" | python2)"
}

function main() {
    local choice
    while true; do
        PKG_STATUS=0
        # Check for installation of script
        #if [ -f "$INSTALL_LOC" ]; then
        grep emulationstation_bgm /opt/retropie/configs/all/autostart.sh > /dev/null 2>&1
        if [ $? -eq 0 ] && [ -f "$INSTALL_LOC" ]; then
            PKG_STATUS=1
            CUR_VOL=$(extract_config max_volume | awk '{print $1 * 100}')
            FADE_DURATION=$(extract_config fade_duration)
            STEP_DURATION=$(extract_config step_duration)
            PROC_DELAY=$(extract_config proc_delay)
            PROC_FADE=$(extract_config proc_fade)
            START_DELAY=$(extract_config start_delay)
            RESET=$(extract_config reset)
            ENABLED=$(extract_config enabled)
            INIT_SONG=$(extract_config start_song)
            MUSIC_DIR=$(extract_config music_dir)
            PIPE_FILE=$(extract_config pipe_file)
        fi
        cmd=(dialog \
            --backtitle "$BACKTITLE | Music Folder: $MUSIC_DIR" \
            --title "$TITLE" \
            --cancel-label "Exit" \
            --menu "Choose an option" 0 0 0 )
        if [ "$PKG_STATUS" -eq 1 ]; then
            options=( \
                1 "BGM Enabled (${ENABLED})"
                2 "BGM Volume (${CUR_VOL}%)"
                3 "Fade Duration (${FADE_DURATION}ms)"
                4 "Step Duration (${STEP_DURATION}ms)"
                5 "Proc Delay (${PROC_DELAY}ms)"
                6 "Proc Fade Duration (${PROC_FADE}ms)"
                7 "Startup Delay (${START_DELAY}ms)"
                8 "Restart on Resume ($RESET)"
                9 "Initial Song (${INIT_SONG})"
                10 "Change Music Folder"
                11 "Uninstall ES BGM")
        else
            options=( \
                1 "Install ES BGM")
        fi
        choice=$("${cmd[@]}" "${options[@]}" 2>&1 >/dev/tty)
        case $choice in
            1) if [ "$PKG_STATUS" -eq 1 ]; then set_bgm_enable; else install_bgm; fi; ;;
            2) set_bgm_volume ;;
            3) set_fade_duration ;;
            4) set_step_duration ;;
            5) set_proc_delay ;;
            6) set_proc_fade ;;
            7) set_startup_delay ;;
            8) restart_on_resume ;;
            9) set_init_song ;;
            10) set_music_dir ;;
            11) uninstall_bgm ;;
            *) exit ;;
        esac
    done
}
function set_bgm_enable() {
    if [ "$ENABLED" == "True" ]; then
        python2 $INSTALL_LOC set --disable
        # Maybe remove from autostart.sh, runcommand, etc. and kill as well.
        echo "EmulationStation BGM is now disabled."
        sleep $INFO_DELAY
    else
        python2 $INSTALL_LOC set --enable
        python2 $INSTALL_LOC play
        echo "EmulationStation BGM is now enabled."
        sleep $INFO_DELAY
    fi
}
function set_bgm_volume() {
    local NEW_VOL
    NEW_VOL=$(dialog \
        --backtitle "$BACKTITLE" \
        --title "$TITLE" \
        --rangebox "Set volume level (D+/U-): " 0 50 0 100 "$CUR_VOL" \
        2>&1 >/dev/tty)
    if [ "$NEW_VOL" != "" ]; then
        echo "BGM volume set to $NEW_VOL%"
        NEW_VOL=`echo $NEW_VOL | awk '{print $1 / 100}'`
        python2 $INSTALL_LOC set --volume $NEW_VOL
        sleep $INFO_DELAY
    fi
}
function set_fade_duration() {
    local NEW_FADE
    NEW_FADE=$(dialog \
        --backtitle "$BACKTITLE" \
        --title "$TITLE" \
        --rangebox "Set fade duration in milliseconds (D+/U-): " 0 50 0 10000 "$FADE_DURATION" \
        2>&1 >/dev/tty)
    if [ "$NEW_FADE" != "" ]; then
        echo "Music fade duration set to ${NEW_FADE}ms"
        python2 $INSTALL_LOC set --fade_duration $NEW_FADE
        sleep $INFO_DELAY
    fi
}
function set_step_duration() {
    local NEW_STEP
    NEW_STEP=$(dialog \
        --backtitle "$BACKTITLE" \
        --title "$TITLE" \
        --rangebox "Set step duration in milliseconds (D+/U-): " 0 50 0 1000 "$STEP_DURATION" \
        2>&1 >/dev/tty)
    if [ "$NEW_STEP" != "" ]; then
        echo "Music step duration set to ${NEW_STEP}ms"
        python2 $INSTALL_LOC set --step_duration $NEW_STEP
        sleep $INFO_DELAY
    fi
}
function set_proc_delay() {
    local NEW_VAL
    NEW_VAL=$(dialog \
        --backtitle "$BACKTITLE" \
        --title "$TITLE" \
        --rangebox "Set delay after process end (ex. omxplayer) in milliseconds before restarting music (D+/U-): " 4 50 0 10000 "$PROC_DELAY" \
        2>&1 >/dev/tty)
    if [ "$NEW_VAL" != "" ]; then
        echo "Delay before music restarts set to ${NEW_VAL}ms"
        python2 $INSTALL_LOC set --proc_delay $NEW_VAL
        sleep $INFO_DELAY
    fi
}
function set_proc_fade() {
    local NEW_VAL
    NEW_VAL=$(dialog \
        --backtitle "$BACKTITLE" \
        --title "$TITLE" \
        --rangebox "Set fade duration in milliseconds for restarting after process end (D+/U-): " 4 50 0 10000 "$PROC_FADE" \
        2>&1 >/dev/tty)
    if [ "$NEW_VAL" != "" ]; then
        echo "Delay before music restarts set to ${NEW_VAL}ms"
        python2 $INSTALL_LOC set --proc_fade $NEW_VAL
        sleep $INFO_DELAY
    fi
}
function set_startup_delay() {
    local NEW_DELAY
    NEW_DELAY=$(dialog \
        --backtitle "$BACKTITLE" \
        --title "$TITLE" \
        --rangebox "Set startup delay (in seconds) (D+/U-): " 0 50 0 100 "$DELAY" \
        2>&1 >/dev/tty)
    if [ "$NEW_DELAY" != "" ]; then
        echo "Startup delay set to ${NEW_DELAY}s"
        python2 $INSTALL_LOC set --start_delay $NEW_DELAY
        sleep $INFO_DELAY
    fi
}
function restart_on_resume() {
    if [ "$RESET" == "True" ]; then
        python2 $INSTALL_LOC set --reset False
        echo "Music will now resume from previous song upon returning to ES."
        sleep $INFO_DELAY
    else
        python2 $INSTALL_LOC set --reset True
        echo "Music will now restart upon returning to ES."
        sleep $INFO_DELAY
    fi
}
function set_init_song() {
    local choice
    local index
    cmd=(dialog \
        --backtitle "$BACKTITLE | Music Folder: $MUSIC_DIR" \
        --title "$TITLE" \
        --menu "Choose a song" 0 60 0 )
    options=(0 "Clear Initial Song")
    iterator=1
    for file in "$MUSIC_DIR"/* ; do
        if [[ $file == *.mp3 ]] || [[ $file == *.ogg ]]; then
            options+=($iterator)
            filename="${file##*/}"
            options+=("$filename")
            iterator=$(($iterator+1))
        fi
    done
    if [ "$options" != "" ]; then
        choice=$("${cmd[@]}" "${options[@]}" 2>&1 >/dev/tty)
        if [ "$choice" != '' ]; then
            if [ "$choice" -eq 0 ]; then
                NEW_SONG=''
            else
                index=$((2*$choice + 1))
                NEW_SONG="${options[$index]}"
            fi
            # Escape all sed offending filepath possible characters
            # https://stackoverflow.com/questions/15783701/which-characters-need-to-be-escaped-when-using-bash
            #INIT_SONG=$(echo "$INIT_SONG"| LC_ALL=C sed -e 's/[^a-zA-Z0-9,._+@%/-]/\\&/g; 1!s/^/"/; $!s/$/"/')
            python2 $INSTALL_LOC set --start_song "$NEW_SONG"
            echo "Initial song changed to '$NEW_SONG'"
            sleep $INFO_DELAY
        fi
    else
        echo "No music found in current music directory."
        sleep $ERROR_DELAY
    fi
}
function set_music_dir() {
    local choice
    choice=$(dialog \
        --backtitle "$BACKTITLE" \
        --title "Select a folder" \
        --dselect "$MUSIC_DIR" 15 50 \
        2>&1 >/dev/tty | sed 's:/*$::')
    if [ -d "$choice" ]; then
        # Escape all sed offending filepath possible characters
        # https://stackoverflow.com/questions/15783701/which-characters-need-to-be-escaped-when-using-bash
        #MUSIC_DIR=$(echo "$MUSIC_DIR"| LC_ALL=C sed -e 's/[^a-zA-Z0-9,._+@%/-]/\\&/g; 1!s/^/"/; $!s/$/"/')
        python2 $INSTALL_LOC set --music_dir "$MUSIC_DIR"
        echo "Music directory changed to '$choice'"
        restart_bgm
        sleep $INFO_DELAY
    elif [ "$choice" != "" ]; then
        echo "Failed to find '$choice'"
        sleep $ERROR_DELAY
    fi
}
function install_bgm() {
    PKG="python-pygame"
    DISCLAIMER=""
    DISCLAIMER="${DISCLAIMER}This module installs a python script by Jurassicplayer that depends on python-pygame. "
    DISCLAIMER="${DISCLAIMER}For your convenience, the following steps will be automated: \n"
    DISCLAIMER="${DISCLAIMER}   - Installation of python-pygame \n"
    DISCLAIMER="${DISCLAIMER}   - Downloading EmulationStation BGM from github \n"
    DISCLAIMER="${DISCLAIMER}   - Backup and addition of entries to: \n"
    DISCLAIMER="${DISCLAIMER}       - /opt/retropie/configs/all/autostart.sh \n"
    DISCLAIMER="${DISCLAIMER}       - /opt/retropie/configs/all/runcommand-onstart.sh \n"
    DISCLAIMER="${DISCLAIMER}       - /opt/retropie/configs/all/runcommand-onend.sh \n"
    DISCLAIMER="${DISCLAIMER}\n\n For more information about EmulationStation BGM, visit '##FIXIT##'\n"
    dialog \
        --backtitle "$BACKTITLE" \
        --title "DISCLAIMER" \
        --msgbox "$DISCLAIMER" 0 0
    PKG_OK=$(dpkg-query -W --showformat='${Status}\n' $PKG | grep "install ok installed")
    if [ "$PKG_OK" == "" ]; then
        sudo apt-get update && sudo apt-get install -y $PKG
    fi
    echo "Installing EmulationStation BGM by Jurassicplayer..."
    #wget -O "$INSTALL_LOC" --progress=bar:force:noscroll --show-progress -q "##FIXIT##"
    echo "Adding entry to /opt/retropie/configs/all/autostart.sh..."
    sed -i.bak "s|.*emulationstation #auto$|(python2 $INSTALL_LOC) \&\n&|" /opt/retropie/configs/all/autostart.sh
    echo "Adding entry to /opt/retropie/configs/all/runcommand-onstart.sh..."
    if [ -f "/opt/retropie/configs/all/runcommand-onstart.sh" ]; then
        cp "/opt/retropie/configs/all/runcommand-onstart.sh" "/opt/retropie/configs/all/runcommand-onstart.bak"
    fi
    echo "(python2 $INSTALL_LOC stop --fade_duration 1000 --force) &" >> "/opt/retropie/configs/all/runcommand-onstart.sh"
    echo "Adding entry to /opt/retropie/configs/all/runcommand-onend.sh..."
    if [ -f "/opt/retropie/configs/all/runcommand-onend.sh" ]; then
        cp "/opt/retropie/configs/all/runcommand-onend.sh" "/opt/retropie/configs/all/runcommand-onend.bak"
    fi
    echo "(python2 $INSTALL_LOC play) &" >> "/opt/retropie/configs/all/runcommand-onend.sh"
    nohup python2 $INSTALL_LOC &
    sleep $INFO_DELAY
}

function uninstall_bgm() {
    local choice
    DISCLAIMER=""
    DISCLAIMER="${DISCLAIMER}This module uninstalls a python script by Jurassicplayer that depends on python-pygame. \n\n"
    DISCLAIMER="${DISCLAIMER}In order to not unknowingly break anything else that could also depend on python-pygame, "
    DISCLAIMER="${DISCLAIMER}this dialog is here to provide the option of also uninstalling pygame or leaving it. \n\n"
    DISCLAIMER="${DISCLAIMER}The music folder will not be touched to prevent inadvertently deleting user data."
    dialog \
        --backtitle "$BACKTITLE" \
        --title "Uninstall Pygame (Optional)" \
        --ok-label "Remove" \
        --cancel-label "Cancel" \
        --extra-button \
        --extra-label "Keep" \
        --yesno "$DISCLAIMER" 0 0
    choice=$?
    local UNINSTALL_PYGAME
    local UNINSTALL
    case $choice in
        0) 
            UNINSTALL_PYGAME=1
            UNINSTALL=1
            ;;
        3) UNINSTALL=1 ;;
    esac
    if [ "$UNINSTALL" == 1 ]; then
        echo "Stopping music script process..."
        python2 $INSTALL_LOC quit
        if [ "$UNINSTALL_PYGAME" == 1 ]; then
            echo "Uninstalling python-pygame..."
            sudo apt-get remove --auto-remove -y python-pygame
        fi
        echo "Uninstalling EmulationStation BGM..."
        rm "${PIPE_FILE}.*"
        rm "$INSTALL_LOC"
        echo "Removing entry from /opt/retropie/configs/all/autostart.sh..."
        sed -i.bak '/emulationstation_bgm/d' /opt/retropie/configs/all/autostart.sh
        echo "Removing entry from /opt/retropie/configs/all/runcommand-onstart.sh..."
        sed -i.bak '/emulationstation_bgm/d' /opt/retropie/configs/all/runcommand-onstart.sh
        echo "Removing entry from /opt/retropie/configs/all/runcommand-onend.sh..."
        sed -i.bak '/emulationstation_bgm/d' /opt/retropie/configs/all/runcommand-onend.sh
        sleep $READ_DELAY
    fi
}


main
