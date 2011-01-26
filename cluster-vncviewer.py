#!/usr/bin/env python
# Cluster VNC viewer

version = "0.1"

import sys

import pygtk
pygtk.require("2.0")

import gtk
import gtk.glade
import gtkvnc
import gobject
import os

class VNCViewer:
	def __init__(self, info):
		info = info.split(":")
		print info
		self.hostname = info[0]
		self.port = info[1]
		self.password = info[2]

		self.wTree = gtk.glade.XML("cluster-vncviewer.glade")
		self.window = self.wTree.get_widget("window")
		self.window_label = self.wTree.get_widget("window_label")
		self.window_toolbar_note = self.wTree.get_widget("toolbar_note")
		self.window_toolbar = self.wTree.get_widget("toolbar")
		self.layout = self.wTree.get_widget("viewport1")
		self.fullscreenButton = self.wTree.get_widget("fullscreenButton")
		self.fullscreenButton.set_active(False)
		self.keysButton = self.wTree.get_widget("keysButton")
		self.keysMenu = self.wTree.get_widget("keysMenu")
		self.keysMenu.attach_to_widget(self.keysButton, None)

		dic = { "on_quitButton_clicked" : gtk.main_quit,
			"on_window_delete_event" : self.close_window,
			"on_disconnectButton_clicked" : self.disconnect,
			"on_fullscreen_toggled" : self.fullscreen,
			"on_window_motion_notify_event" : self.mouse_moved_in_window,
			"on_CtrlAltDelmenuitem_activate": self.send_cad,
			"on_CtrlAltBackmenuitem_activate": self.send_cab,
			"on_CtrlEscmenuitem_activate": self.send_ce,
			"on_keys_clicked" : self.keysMenuPop
		}
		self.wTree.signal_autoconnect(dic)
		self.vnc = gtkvnc.Display()

	def keysMenuPop (self, data):
		self.keysMenu.popup(None, None, None, 0, 0, gtk.get_current_event_time())

	def fullscreen (self, data):
		if (self.fullscreenButton.get_active()):
			self.window.fullscreen()
			self.window_toolbar_note.show_all()
			self.window_toolbar.hide_all()
		else:
			self.window.unfullscreen()
			self.window_toolbar_note.hide_all()
			self.window_toolbar.show_all()
		return False

	def send_cad (self, data):
		self.vnc.send_keys(["Control_L", "Alt_L", "Delete"])
		print "Sent Ctrl+Alt+Delete"
		self.vnc.grab_focus()

	def send_cab (self, data):
		self.vnc.send_keys(["Control_L", "Alt_L", "BackSpace"])
		print "Sent Ctrl+Alt+BackSpace"
		self.vnc.grab_focus()

	def send_ce (self, data):
		self.vnc.send_keys(["Control_L", "Escape"])
		print "Sent Ctrl+Escape"
		self.vnc.grab_focus()

	#if in fullscreen and mouse on top, show toolbar
	def mouse_moved_in_window(self, widget, data):
		coords = self.window.window.get_pointer()
		y = coords[1]
		if y <= 5 and self.fullscreenButton.get_active():
			self.window_toolbar.show_all()
			#setup timer that will hide toolbar when ended
			gobject.timeout_add(2000, self.window_toolbar.hide_all) #2 sec.

	def quit(self, data=None):
		print "Closing", self.hostname, self.port
		self.vnc.close()
		self.vnc.destroy()
		self.window.destroy()
		self.vnc = None
		self.window = None
		if VNCViewer.open_windows == 1:
			gtk.main_quit()
		VNCViewer.open_windows -= 1

	def close_window(self, widget, data):
		self.quit()
		return False
	
	def disconnect(self, data):
		self.quit()

	def connect(self):
		self.vnc.set_credential(gtkvnc.CREDENTIAL_PASSWORD, self.password)
		self.vnc.set_credential(gtkvnc.CREDENTIAL_CLIENTNAME, "cluster_vncviewer")
		self.vnc.set_depth(gtkvnc.DEPTH_COLOR_LOW)
		self.vnc.connect("vnc-connected", self.vnc_connected, self)
		self.vnc.connect("vnc-initialized", self.vnc_initialized, self)
		self.vnc.connect("vnc-disconnected", self.vnc_disconnected, self)
		self.vnc.open_host(self.hostname, self.port)

	def vnc_connected(src, vnc, self):
		print "Connected", self.hostname, self.port
		self.layout.add(vnc)
		vnc.realize()
		VNCViewer.open_windows += 1

	def vnc_initialized (src, vnc, self):
		print "Initialized", self.hostname, self.port
		title = "%s:%s" % (self.hostname, self.port)
		self.window.set_title(title)
		self.window_label.set_markup ("<big><b>%s</b></big>" % title)
		self.window.show_all()
		self.window_toolbar_note.hide_all()
		self.window.resize (vnc.get_width(), vnc.get_height())
		vnc.grab_focus()

	def vnc_disconnected(src, vnc, self):
		print "Disconnected", self.hostname, self.port
		self.quit()

def wait():
	while gtk.events_pending():
		gtk.main_iteration()

if __name__ == "__main__":
	VNCViewer.open_windows = 0

	instances = []
	for arg in sys.argv[1:]:
		instances.append(VNCViewer(arg))

	for instance in instances:
		instance.connect()
		
	if instances:
		gtk.main()

