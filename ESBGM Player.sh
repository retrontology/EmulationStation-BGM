#!/bin/bash

INSTALL_LOC="/home/pigaming/RetroArena/scriptmodules/supplementary/esbgm/emulationstation_bgm.py"
BACKTITLE="Techitechi-chan's Toolbox"
TITLE="EmulationStation BGM Player"
INFO_DELAY=3
ERROR_DELAY=5
FADE_DURATION=600

function main() {
    local choice
    while true; do
        PKG_STATUS=0
        # Check for installation of script
        #if [ -f "$INSTALL_LOC" ]; then
        grep emulationstation_bgm /opt/retroarena/configs/all/autostart.sh > /dev/null 2>&1
        if [ $? -eq 0 ] && [ -f "$INSTALL_LOC" ]; then
            PKG_STATUS=1
        fi
        cmd=(dialog \
            --backtitle "$BACKTITLE" \
            --title "$TITLE" \
            --cancel-label "Exit" \
            --menu "Choose an option" 0 0 0 )
        if [ "$PKG_STATUS" -eq 1 ]; then
            options=( \
                1 "Next"
                2 "Prev"
                3 "Stop"
                4 "Play"
                5 "Random")
        else
            options=( \
                1 "ES BGM not installed.")
        fi
        choice=$("${cmd[@]}" "${options[@]}" 2>&1 >/dev/tty)
        case $choice in
            1) if [ "$PKG_STATUS" -eq 1 ]; then player_cmd_next; else exit; fi; ;;
            2) player_cmd_prev ;;
            3) player_cmd_stop ;;
            4) player_cmd_play ;;
            5) player_cmd_rand ;;
            *) exit ;;
        esac
    done
}

function player_cmd_next(){
    python2 $INSTALL_LOC stop --fade_duration $FADE_DURATION --force
    python2 $INSTALL_LOC next --fade_duration $FADE_DURATION
}
function player_cmd_prev(){
    python2 $INSTALL_LOC stop --fade_duration $FADE_DURATION --force
    python2 $INSTALL_LOC prev --fade_duration $FADE_DURATION
}
function player_cmd_stop(){
    python2 $INSTALL_LOC stop --fade_duration $FADE_DURATION --force
}
function player_cmd_play(){
    python2 $INSTALL_LOC play
}
function player_cmd_rand(){
    python2 $INSTALL_LOC stop --fade_duration $FADE_DURATION --force
    python2 $INSTALL_LOC play --fade_duration $FADE_DURATION --random
}

main
