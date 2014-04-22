
import os, sys, json
from gi.repository import Gtk

def sort_name (model, a, b, data):
	na = model.get_value (a, 0)
	nb = model.get_value (b, 0)
	
	if na > nb:
		return 1
	else:
		return -1

def sort_valid (model, a, b, data):
	va = model.get_value (a, 1)
	vb = model.get_value (b, 1)
	
	if va > vb:
		return 1
	else:
		return -1

class StoryEditor:

	def __init__ (self):
		builder = Gtk.Builder()
		builder.add_from_file ("StoryEditor.glade")
		
		window = builder.get_object ("window1")
		builder.get_object("fileopen").connect("activate", self.open_cb)
		builder.get_object("toolopen").connect("clicked", self.open_cb)
		builder.get_object("filesave").connect("activate", self.save_cb)
		builder.get_object("toolsave").connect("clicked", self.save_cb)
		builder.get_object("filesaveas").connect("activate", self.saveas_cb)
		builder.get_object("nodeadd").connect("clicked", self.node_add_cb)
		builder.get_object("nodedelete").connect("clicked", self.node_delete_cb)
		builder.get_object("nodecopy").connect("clicked", self.node_copy_cb)
		
		self.prompt_text = builder.get_object("textview1")
		self.imageentry = builder.get_object("imageentry")
		self.musicentry = builder.get_object("musicentry")
		
		# Main Treeview
		self.liststore = builder.get_object("liststore1")
		self.treeview = builder.get_object("treeview1")
		
		sel = self.treeview.get_selection()
		sel.set_mode(Gtk.SelectionMode.BROWSE)
		sel.connect("changed", self.activate_row_cb)
		
		col = builder.get_object("treeviewcolumn1")
		textrenderer = Gtk.CellRendererText()
		textrenderer.set_property("editable", True)
		textrenderer.connect("edited", self.rename_node_cb)
		col.pack_start (textrenderer, True)
		col.add_attribute(textrenderer, "text", 0)
		col.add_attribute(textrenderer, "background", 2)
		self.liststore.set_sort_func(0, sort_name)
		
		# Choices Treeview
		self.choicestore = builder.get_object ("liststore_choices")
		self.choiceview = builder.get_object ("treeview_choices")
		
		col = builder.get_object("treeviewcolumn3")
		textrenderer = Gtk.CellRendererText()
		textrenderer.set_property("editable", True)
		textrenderer.connect("edited", self.rename_choices_node_cb)
		col.pack_start (textrenderer, True)
		col.add_attribute(textrenderer, "text", 0)
		col.add_attribute(textrenderer, "background", 2)
		self.liststore.set_sort_func(0, sort_name)
		
		col = builder.get_object("treeviewcolumn4")
		textrenderer = Gtk.CellRendererText()
		textrenderer.set_property("editable", True)
		textrenderer.connect("edited", self.rename_choices_text_cb)
		col.pack_start (textrenderer, True)
		col.add_attribute(textrenderer, "text", 1)
		col.add_attribute(textrenderer, "background", 2)
		
		window.show_all()
		window.connect ("destroy", Gtk.main_quit)
		
		self.json_file = ''
		self.node = ''
		self.story_object = {}
		self.newnode = False
		
		
	def open_cb (self, caller):
		fcd = Gtk.FileChooserDialog("Open...", None, Gtk.FileChooserAction.SAVE, \
			("Cancel", Gtk.ResponseType.CANCEL, "Open", Gtk.ResponseType.ACCEPT))
		fcd.set_select_multiple(False)
		fcd.set_local_only(False)
		filter1 = Gtk.FileFilter()
		filter1.add_pattern("*.json")
		filter1.set_name("JSON Files (*.json)")
		filter2 = Gtk.FileFilter()
		filter2.add_pattern("*")
		filter2.set_name("All Files (*)")
		fcd.add_filter(filter1)
		fcd.add_filter(filter2)
		fcd.set_filter(filter1)
		response = fcd.run()
		if response == Gtk.ResponseType.ACCEPT:
			path = fcd.get_filename()
			if os.path.exists(path):
				self.load_file(path)
		fcd.destroy()
		
	def save_cb (self, caller):
		if os.path.exists(self.json_file):
			self.save_file (self.json_file)
		else:
			self.saveas_cb (caller)
		
	def saveas_cb (self, caller):
		fcd = Gtk.FileChooserDialog("Save As...", None, Gtk.FileChooserAction.SAVE, \
			("Cancel", Gtk.ResponseType.CANCEL, "Save", Gtk.ResponseType.ACCEPT))
		fcd.set_select_multiple(False)
		fcd.set_local_only(False)
		filter1 = Gtk.FileFilter()
		filter1.add_pattern("*.json")
		filter1.set_name("JSON Files (*.json)")
		filter2 = Gtk.FileFilter()
		filter2.add_pattern("*")
		filter2.set_name("All Files (*)")
		fcd.add_filter(filter1)
		fcd.add_filter(filter2)
		fcd.set_filter(filter1)
		response = fcd.run()
		if response == Gtk.ResponseType.ACCEPT:
			path = fcd.get_filename()
			self.save_file(path)
		fcd.destroy()
		
	def load_file (self, path):
		self.json_file = path
		f = open (path)
		self.story_object = json.load (f)
		
		self.liststore.clear()
		
		for key in self.story_object.keys():
			it = self.liststore.append ()
			print key
			self.liststore.set_value (it, 0, key)
			self.liststore.set_value (it, 2, 'white')
						
		first = self.liststore.get_iter_first()
		self.treeview.get_selection().select_iter(first)
		self.validate_choices()
		self.validate_current_node()
		
		print 'Story json loaded'
	
	def save_file (self, path):
		self.commit_changes()
		try:
			f = open (path, 'w')
			json.dump (self.story_object, f)
			f.close()
			self.json_file = path
		except OSError:
			pass
	
	def node_add_cb (self, caller):
		print self.node
		self.commit_changes()
		self.newnode = True
	
		it = self.liststore.append()
		path = self.liststore.get_path(it)
		col = self.treeview.get_column(0)
		self.clear_form()
		self.treeview.set_cursor(path, col, True)
		
	def node_copy_cb (self, caller):
		self.commit_changes()
		self.newnode = True
		
		# Get the current node name
		rows = self.treeview.get_selection().get_selected_rows()
		tp = rows[1][0]
		it = self.liststore.get_iter(tp)
		nodename = self.liststore.get_value(it, 0)
		
		# Make the new node
		itnew = self.liststore.append()
		self.liststore.set_value(itnew, 0, nodename)
		path = self.liststore.get_path(itnew)
		col = self.treeview.get_column(0)
		self.treeview.set_cursor(path, col, True)
	
	def node_delete_cb (self, caller):
		rows = self.treeview.get_selection().get_selected_rows()
		tp = rows[1][0]
		it = self.liststore.get_iter(tp)
		node = self.liststore.get_value(it, 0)
		if node in self.story_object.keys():
			self.story_object.pop(node)
		self.liststore.remove(it)
		
		self.validate_choices()
		self.validate_current_node()
	
	def rename_node_cb (self, caller, path, new_text):
		it = self.liststore.get_iter(path)
		node = self.liststore.get_value(it, 0)
		
		# Trying to rename to a node that exists
		if new_text in self.story_object.keys() and new_text != node:
			if node not in self.story_object.keys():
				self.liststore.remove(it)
				print 'Invalid new name'
			else:
				self.newnode = False
				print 'Invalid rename'
				return
		
		# Check if being renamed or is a new node
		if node in self.story_object.keys() and not self.newnode:
			self.story_object[new_text] = self.story_object.pop(node)
			print 'Rename'
		else:
			self.newnode = False
			if new_text == '' or new_text == None or new_text in self.story_object.keys():
				self.liststore.remove(it)
				print 'Blank new name'
				return
			self.story_object[new_text] = {}
			print 'Create new node '+new_text
			print self.story_object[new_text]
		
		self.liststore.set_value(it, 0, new_text)
		self.node = new_text
		self.commit_changes()
	
	def rename_choices_node_cb (self, caller, path, new_text):
		it = self.choicestore.get_iter(path)
		node = self.choicestore.get_value(it, 0)
		self.choicestore.set_value(it, 0, new_text)
		self.commit_changes()
		self.set_node(new_text)
		
	def rename_choices_text_cb (self, caller, path, new_text):
		it = self.choicestore.get_iter(path)
		node = self.choicestore.get_value(it, 1)
		self.choicestore.set_value(it, 1, new_text)
	
	def clear_form (self):
		self.musicentry.set_text('')
		self.imageentry.set_text('')
		self.prompt_text.get_buffer().set_text('')
		self.choicestore.clear()
	
	def commit_changes (self):
		if self.node in self.story_object.keys():
			buf = self.prompt_text.get_buffer()
			self.story_object[self.node]['text'] = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)
			self.story_object[self.node]['music'] = self.musicentry.get_text()
			self.story_object[self.node]['image'] = self.imageentry.get_text()
			choices = []
			for row in self.choicestore:
				choices.append ({'node':row[0], 'text':row[1]})
			self.story_object[self.node]['choices'] = choices
			
	
	def set_node (self, node):
		if not node in self.story_object.keys():
			print 'Invalid set node'
			return
			
		story_node = self.story_object[node]
		self.node = node
		
		if 'text' in story_node.keys():
			self.prompt_text.get_buffer().set_text (str(story_node['text']))
		else:
			self.prompt_text.get_buffer().set_text('')
		
		if 'music' in story_node.keys():
			self.musicentry.set_text(str(story_node['music']))
		else:
			self.musicentry.set_text('')
		
		if 'image' in story_node.keys():
			self.imageentry.set_text(str(story_node['image']))
		else:
			self.imageentry.set_text('')
		
		self.choicestore.clear()
		if 'choices' in story_node.keys():
			for choice in story_node['choices']:
				it = self.choicestore.append()
				if 'node' in choice.keys():
					self.choicestore.set_value(it, 0, str(choice['node']))
				if 'text' in choice.keys():
					self.choicestore.set_value(it, 1, str(choice['text']))
					
		self.validate_current_node()
		self.validate_choices()
	
	def validate_choices (self):
		for row in self.liststore:
			node = self.story_object[row[0]]
			valid = True
			
			if 'choices' in node.keys():
				choices = node['choices']
				for choice in choices:
					if 'node' in choice.keys():
						if not choice['node'] in self.story_object.keys():
							valid = False
					else:
						valid = False
			row[1] = valid
			colors = ['#FFB0B0', 'white']
			row[2] = colors[valid]
	
	def validate_current_node (self):
		for row in self.choicestore:
			if row[0] not in self.story_object.keys():
				row[2] = '#FFB0B0'
			else:
				row[2] = 'white'
	
	def activate_row_cb (self, caller):
		if not self.newnode:
			self.commit_changes()
		rows = caller.get_selected_rows()
		if len(rows[1]) > 0:
			tp = rows[1][0]
			it = self.liststore.get_iter(tp)
			self.set_node (self.liststore.get_value (it, 0))
		

s = StoryEditor()
Gtk.main()
				
