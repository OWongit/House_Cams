#!/usr/bin/env python3
# GTK UI for dual-camera viewer using gtksink widgets
from __future__ import annotations

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gst", "1.0")
from gi.repository import Gtk, Gdk, Gst

Gst.init(None)

class VideoView(Gtk.Box):
    def __init__(self, title: str = "Camera"):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.set_border_width(6)

        header = Gtk.Label()
        header.set_markup(f"<b>{Gtk.utils.escape(title) if hasattr(Gtk, 'utils') else title}</b>")
        header.set_halign(Gtk.Align.START)

        # Create gtksink; we pack its widget directly
        self.sink = Gst.ElementFactory.make("gtksink", None)
        if self.sink is None:
            # Fallback to autovideosink; less optimal for embedding
            self.sink = Gst.ElementFactory.make("autovideosink", None)

        video_widget = None
        try:
            video_widget = self.sink.get_property("widget")
        except Exception:
            pass

        if video_widget is None:
            # Some sinks don't expose a widget; fallback to a DrawingArea placeholder
            video_widget = Gtk.DrawingArea()
            video_widget.set_size_request(320, 240)

        frame = Gtk.Frame()
        frame.set_shadow_type(Gtk.ShadowType.IN)
        frame.add(video_widget)

        self.status = Gtk.Label(label=" ")
        self.status.get_style_context().add_class("dim-label")
        self.status.set_halign(Gtk.Align.START)

        self.pack_start(header, False, False, 0)
        self.pack_start(frame, True, True, 0)
        self.pack_start(self.status, False, False, 0)

    def set_status(self, text: str):
        self.status.set_text(text)

    def get_sink(self):
        return self.sink

class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(title="UniFi Dual-Cam Viewer (GTK + GStreamer)", application=app)
        self.set_default_size(1200, 600)

        self.front_view = VideoView("Front Camera")
        self.back_view  = VideoView("Back Camera")

        # Use a horizontal Paned so the user can resize the two feeds
        paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
        paned.pack1(self.front_view, resize=True, shrink=False)
        paned.pack2(self.back_view,  resize=True, shrink=False)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_border_width(10)
        box.pack_start(paned, True, True, 0)

        self.add(box)

        # Maximize on show to mimic previous fullscreen behavior
        self.connect("show", lambda *_: self.maximize())

    def bind_streams(self, front_player, back_player):
        # Wire status callbacks
        front_player.status_cb = self.front_view.set_status
        back_player.status_cb  = self.back_view.set_status
