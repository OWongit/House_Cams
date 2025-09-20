#!/usr/bin/env python3
# GStreamer player controller for GTK embedding
# Uses playbin + gtksink and adds a timeoverlay to mimic the original timestamp.
#
# Public surface:
#   class PlayerController:
#       def __init__(self, sink, name, status_cb=None)
#       def set_uri(self, uri: str)
#       def play(self)
#       def stop(self)
#       def dispose(self)
#
# sink is a GstElement (gtksink) whose .props.widget can be packed into GTK.
#
from __future__ import annotations
import typing as _t

import gi
gi.require_version("Gst", "1.0")
gi.require_version("GstVideo", "1.0")
from gi.repository import Gst, GLib, GstVideo

# One-time initialization (safe to call multiple times)
Gst.init(None)

class PlayerController:
    def __init__(self, sink, name: str = "Camera", status_cb: _t.Callable[[str], None] | None = None):
        self.name = name
        self.status_cb = status_cb or (lambda s: None)

        # playbin handles demux/decoding; we supply our sink and optional filters
        self._player = Gst.ElementFactory.make("playbin", f"playbin_{name}")
        if self._player is None:
            raise RuntimeError("Failed to create GStreamer element 'playbin'. Ensure GStreamer is installed.")

        if sink is None:
            raise RuntimeError("A video sink (gtksink) must be provided.")

        # Optional: Add a time overlay similar to the previous painter overlay
        try:
            overlay = Gst.parse_bin_from_description(
                "timeoverlay halignment=right valignment=top shaded-background=true font-desc='Monospace 12'",
                True
            )
            self._player.set_property("video-filter", overlay)
        except Exception:
            # If parse fails (older gstreamer), continue without overlay
            pass

        self._player.set_property("video-sink", sink)
        self._uri = None

        bus = self._player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self._on_bus_message)

        self._retry_source = None
        self._retry_backoff_ms = 500  # start at 0.5s

    # ---------- Public API ----------
    def set_uri(self, uri: str):
        self._uri = uri
        self._player.set_property("uri", uri)

    def play(self):
        if not self._uri:
            self._set_status(f"{self.name}: no URI")
            return
        self._cancel_retry()
        self._set_status(f"{self.name}: connecting …")
        self._player.set_state(Gst.State.PLAYING)

    def stop(self):
        self._cancel_retry()
        self._player.set_state(Gst.State.NULL)

    def dispose(self):
        self.stop()
        try:
            bus = self._player.get_bus()
            bus.remove_signal_watch()
        except Exception:
            pass

    # ---------- Internal helpers ----------
    def _set_status(self, msg: str):
        self.status_cb(msg)

    def _schedule_retry(self):
        if self._retry_source is not None:
            return
        delay = self._retry_backoff_ms
        self._set_status(f"{self.name}: retry in {delay/1000:.1f}s")
        self._retry_source = GLib.timeout_source_new(delay)
        self._retry_source.set_callback(self._do_retry)
        self._retry_source.attach(None)
        # Increase backoff (cap at 5s)
        self._retry_backoff_ms = min(5000, int(self._retry_backoff_ms * 1.6))

    def _cancel_retry(self):
        if self._retry_source is not None:
            try:
                self._retry_source.destroy()
            except Exception:
                pass
            self._retry_source = None
        self._retry_backoff_ms = 500

    def _do_retry(self):
        self._retry_source = None
        if self._uri:
            self._set_status(f"{self.name}: reconnecting …")
            self._player.set_state(Gst.State.READY)
            self._player.set_state(Gst.State.PLAYING)
        return False  # one-shot

    def _on_bus_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            self._set_status(f"{self.name}: error: {err.message or err}")
            # Try to reconnect
            self._player.set_state(Gst.State.READY)
            self._schedule_retry()
        elif t == Gst.MessageType.EOS:
            # Stream ended; try to restart
            self._set_status(f"{self.name}: stream ended; restarting …")
            self._player.set_state(Gst.State.READY)
            self._schedule_retry()
        elif t == Gst.MessageType.STATE_CHANGED:
            if message.src == self._player:
                old, new, _ = message.parse_state_changed()
                if new == Gst.State.PLAYING:
                    self._set_status(f"{self.name}: connected")
                    self._cancel_retry()
        elif t == Gst.MessageType.BUFFERING:
            # For (non-live) streams: pause while buffering < 100
            percent = message.parse_buffering()
            if percent < 100:
                self._player.set_state(Gst.State.PAUSED)
                self._set_status(f"{self.name}: buffering {percent}%")
            else:
                # Only resume if we were playing previously
                self._player.set_state(Gst.State.PLAYING)
        return True
