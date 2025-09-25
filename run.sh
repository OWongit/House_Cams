#!/usr/bin/env bash
# Wayland/XWayland usually sets DISPLAY for you. If you ever switch to X11 and need it, uncomment:
# export DISPLAY=:0

#####################################
# MUST CHANGE DIRECTORY ACCORDINGLY #
#####################################

cd /home/owenw/cams_temp
# If you use a venv, uncomment:
# source /home/owenw/cams_temp/venv/bin/activate
exec /usr/bin/python3 /home/owenw/cams_temp/main.py
