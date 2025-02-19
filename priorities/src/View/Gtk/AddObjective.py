from collections import OrderedDict
from datetime import datetime

from gtk import MessageDialog
from gtk import BUTTONS_YES_NO,MESSAGE_QUESTION,RESPONSE_YES

from View.Gtk import _,Gtk

from View.Gtk.DeleteCascade import *


class AddObjective(Gtk):
	__destroy = True

	def __init__(self, objective=None):
		Gtk.__init__(self, "AddObjective")

		self.__objective = objective
		self.oldName = None

		# Objective & quantity
		self.txtObjective = self.builder.get_object("txtObjective")
		self.spnQuantity = self.builder.get_object("spnQuantity")

		# Expiration
		self.chkExpiration = self.builder.get_object("chkExpiration")

		self.vbCalendarHour = self.builder.get_object("vbCalendarHour")
		self.calExpiration = self.builder.get_object("calExpiration")
		self.sbHour = self.builder.get_object("sbHour")
		self.sbMinute = self.builder.get_object("sbMinute")
		self.sbSecond = self.builder.get_object("sbSecond")

		# Requirements
		self.requirements = RequirementList(self.builder.get_object("vbRequirements"))
		self.__btnDel = self.builder.get_object("btnDel_Requirement")

		self.oldRequirements = []

		# Set data
		if objective:
			objective = self.controller.GetObjective(objective)

			if objective:
				# Delete button
				btnDelete = self.builder.get_object("btnDelete")
				btnDelete.show()

				# Name
				self.oldName = objective["name"]
				self.txtObjective.set_text(self.oldName)

				# Quantity
				self.spnQuantity.set_value(objective["quantity"])

				# Expiration
				self.expiration=None
				if objective["expiration"]:
					self.chkExpiration.set_active(True)
					self.chkExpiration.toggled()

					self.expiration = datetime.strptime(objective["expiration"],
														"%Y-%m-%d %H:%M:%S")

					self.calExpiration.select_month(self.expiration.month-1, self.expiration.year)
					self.calExpiration.select_day(self.expiration.day)
					self.sbHour.set_value(self.expiration.hour)
					self.sbMinute.set_value(self.expiration.minute)
					self.sbSecond.set_value(self.expiration.second)

				# Requirements
				self.oldRequirements = self.controller.Requirements(self.oldName)

				self.requirements.Fill(self.controller.ObjectivesNames(),
									   self.oldRequirements)

		# Old data
		self.oldObjective = self.txtObjective.get_text()
		self.oldQuantity = self.spnQuantity.get_text()



	def __StoreData(self):

		name = self.txtObjective.get_text()

		# [To-Do] Also check expiration modification
		if name:
			# Name
			if self.oldName != name:
				self.controller.UpdateName(self.oldName, name)

			# Expiration
			if self.chkExpiration.get_active():
				self.expiration = self.calExpiration.get_date()
				self.expiration = datetime(self.expiration[0],
											self.expiration[1]+1,
											self.expiration[2],
											self.sbHour.get_value_as_int(),
											self.sbMinute.get_value_as_int(),
											self.sbSecond.get_value_as_int())
			else:
				self.expiration = None

			self.controller.AddObjective(name, self.spnQuantity.get_value(),
										self.expiration)

			# Requirements and alternatives
			requirements = self.requirements.GetData()

			if requirements != self.oldRequirements:
				orphans = None

				if self.config.Get('removeOrphanRequirements'):
					orphans = self.controller.Requirements(name)

				self.controller.SetRequirements(name, requirements)
				self.controller.DelOrphans(orphans)

			return True


	def __Delete(self):
		if self.__objective:

			# Delete in cascade
			if(self.config.Get('deleteCascade')
			and len(self.controller.Requirements(self.__objective)) > 1):
				dialog = DeleteCascade(self.__objective)

				dialog.window.set_transient_for(self.window)
				response = dialog.window.run()
				dialog.window.destroy()

#				if response > 0:
#					self.__CreateTree()

			# Delete only the objective
			else:
				dialog = MessageDialog(self.window, 0,
									   MESSAGE_QUESTION, BUTTONS_YES_NO,
									   _("Do you want to delete the objective ")
									   +self.__objective+"?")
				response = dialog.run()
				dialog.destroy()
				if response == RESPONSE_YES:
					self.controller.DeleteObjective(self.__objective)
#					self.__CreateTree()

		return True


	def __Cancel(self):
		closeDialog = self.oldObjective == self.txtObjective.get_text()

		if not closeDialog:
			dialog = MessageDialog(self.window,
									0,
									MESSAGE_QUESTION,
									BUTTONS_YES_NO,
									_("The objective have been modified"))
			dialog.format_secondary_text(_("The objective have been modified and the changes will be lost. Are you sure do you want to continue?"))
			response = dialog.run()
			dialog.destroy()
			if response == RESPONSE_YES:
				return True

		return closeDialog


	def on_AddObjective_delete_event(self, widget,data=None):
		if not self.__destroy:
			self.__destroy = True
			return True


	def on_AddObjective_response(self, widget, response):
		closeDialog = True

		if response == 1:
			closeDialog = self.__StoreData()
		elif response == 2:
			closeDialog = self.__Delete()
		else:
			closeDialog = self.__Cancel()

			if response == -4 and not closeDialog:
				self.__destroy = False

		if not closeDialog:
			self.window.emit_stop_by_name('response')


	def on_chkExpiration_toggled(self, widget):
		self.vbCalendarHour.set_sensitive(widget.get_active())


	def on_btnAdd_Requirement_clicked(self, widget):
		objectives = self.controller.ObjectivesNames()

		requirement = Requirement(objectives, True)
#		requirement.id = self.requirements.GetMaxID() + 1
		self.requirements.elem.pack_start(requirement, False)


class RequirementList:
	def __init__(self, elem):
		self.elem = elem

	def GetData(self):
		result = []

		def ForEach(requirement):
			data = requirement.GetData()
			if data:
				result.append(data)

		self.elem.foreach(ForEach)

		return result

	def Fill(self, objectives, requirements):
		for requirement in requirements:
			req = Requirement(objectives, False)
			self.elem.pack_start(req, False)

			for alternative in requirement.items():
				req.Add(alternative)

#	def GetMaxID(self):
#		"""Get the bigger requirement ID inside the requirement list
#
#		If requirement list is empty, return -1
#		"""
#		result = -1
#
#		for requirement in self.elem.get_children():
#			if  result < requirement.id:
#				result = requirement.id
#
#		return result


from gtk import ICON_SIZE_MENU
from gtk import Adjustment, Button, CellRendererCombo, CellRendererSpin
from gtk import Expander, HBox, HButtonBox, Image, Label, ListStore, TreeView
from gtk import TreeViewColumn, VBox

class Requirement(Expander):

	def __init__(self, objectives, new):
		Expander.__init__(self)

		self.connect("enter-notify-event",self.onEnterNotifyEvent)
		self.connect("leave-notify-event",self.onLeaveNotifyEvent)

		vBox = VBox()
		self.add(vBox)

		# Data model
		self.model = ListStore(str,float)

		# Title bar
		hBox = HBox()
		self.set_property("label-widget", hBox)

		self.title = Label()
		hBox.pack_start(self.title)

		# Alternatives
		treeView = TreeView(self.model)
#		treeView.set_headers_visible(False)
		vBox.pack_start(treeView)

		listStore_objectives = ListStore(str)
		for name in objectives:
			listStore_objectives.append((name,))

		def combo_changed(_, path, text, model):
			model[path][0] = text

		cellRenderer = CellRendererCombo()
		cellRenderer.connect("edited", combo_changed, self.model)
		cellRenderer.set_property("text-column", 0)
		cellRenderer.set_property("editable", True)
		cellRenderer.set_property("has-entry", True)
		cellRenderer.set_property("model", listStore_objectives)

		treeViewColumn = TreeViewColumn("Alternative",cellRenderer,text=0)
#		treeViewColumn = TreeViewColumn(None,cellRenderer,text=0)
		treeView.append_column(treeViewColumn)

		def spin_changed(_, path, value, model):
			model[path][1] = float(value.replace(",","."))

		cellRenderer = CellRendererSpin()
		cellRenderer.connect("edited", spin_changed, self.model)
		cellRenderer.set_property("adjustment", Adjustment(1, 0, 100, 1, 10, 0))
		cellRenderer.set_property("editable", True)
		cellRenderer.set_property("digits", 2)

		treeViewColumn = TreeViewColumn(None,cellRenderer,text=1)
		treeView.append_column(treeViewColumn)

		# Add/remove alternative button box
#		hButtonBox = HButtonBox()
#		vBox.pack_start(hButtonBox, False)

		# Add alternative
		button = Button("gtk-add")
		button.connect("clicked",self.on_btnAdd_Alternative_clicked)
		button.set_use_stock(True)
#		hButtonBox.pack_start(button)
		vBox.pack_start(button, False)

#		# Remove alternative
#		button = Button("gtk-remove")
#		button.connect("clicked",self.on_btnDel_Alternative_clicked)
#		button.set_use_stock(True)
#		hButtonBox.pack_start(button)

		# Expand the requirement and add an alternative if it's new
		if new:
			self.set_expanded(True)
			self.model.append((None,1.0))

		# Show requirement
		self.show_all()

		# Delete requirement button (default is hidden)
		self.imgRemove = Image()
		self.imgRemove.connect("button-press-event",self.onDelRequirement)
		self.imgRemove.set_from_stock("gtk-cancel", ICON_SIZE_MENU)
		hBox.pack_start(self.imgRemove)


	def Add(self, alternative):
		self.model.append(alternative)

		names = []
		iter = self.model.get_iter_first()
		while iter:
			alt = self.model.get_value(iter,0)
			if alt:
				names.append(alt)

			iter = self.model.iter_next(iter)

		self.title.set_text(','.join(names))


	def GetData(self):
		result = OrderedDict()

		iter = self.model.get_iter_first()
		while iter:
			alt = self.model.get_value(iter,0)
			if alt:
				result[alt] = self.model.get_value(iter,1)

			iter = self.model.iter_next(iter)

		return result


	def onDelRequirement(self, widget):
		self.get_parent().remove(self)


	def onEnterNotifyEvent(self, widget,event):
		self.imgRemove.show()

	def onLeaveNotifyEvent(self, widget,event):
		self.imgRemove.hide()


	def __btnDel_Alternative_Sensitivity(self):
		pass
#		self.__btnDel.set_sensitive(len(self.__model.))


	def on_btnAdd_Alternative_clicked(self, widget):
		self.model.append((None,1.0))

		self.__btnDel_Alternative_Sensitivity()

	def on_btnDel_Alternative_clicked(self, widget):

		self.__btnDel_Alternative_Sensitivity()