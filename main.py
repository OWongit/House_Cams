#!/usr/bin/env python3
import sys
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gst", "1.0")

from gi.repository import Gtk, Gst, Gio

from KEYS import keys
from helper import fetch_stream_url, rtsps_to_rtsp
from streaming import PlayerController
from ui_main import MainWindow

QUALITY = "high"  # 'high' | 'medium' | 'low'

class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.example.dualcam", flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self):
        # Fetch camera IDs
        front_id = keys.get("FRONT_CAMERA")
        back_id  = keys.get("BACK_CAMERA")

        if not front_id or not back_id:
            print("FRONT_CAMERA and BACK_CAMERA must be set in KEYS.py")
            win = MainWindow(self)
            win.show_all()
            return

        # Fetch RTSPS and convert to RTSP
        try:
            front_rtsps = fetch_stream_url(front_id, quality=QUALITY)
            back_rtsps  = fetch_stream_url(back_id,  quality=QUALITY)

            front_rtsp = rtsps_to_rtsp(front_rtsps)
            back_rtsp  = rtsps_to_rtsp(back_rtsps)
        except Exception as e:
            print("Failed to fetch/convert camera URLs:", e)
            front_rtsp = ""
            back_rtsp  = ""

        win = MainWindow(self)

        # Setup players
        front_player = PlayerController(win.front_view.get_sink(), name="Front", status_cb=win.front_view.set_status)
        back_player  = PlayerController(win.back_view.get_sink(),  name="Back",  status_cb=win.back_view.set_status)

        win.bind_streams(front_player, back_player)
        win.show_all()

        if front_rtsp:
            front_player.set_uri(front_rtsp)
            front_player.play()
        if back_rtsp:
            back_player.set_uri(back_rtsp)
            back_player.play()

def main():
    app = App()
    rc = app.run(sys.argv)
    sys.exit(rc)

if __name__ == "__main__":
    main()
