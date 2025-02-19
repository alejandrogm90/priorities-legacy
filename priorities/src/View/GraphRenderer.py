import glib
import gtk

from datetime import datetime,timedelta


class Requirement(gtk.Button):
	margin_x = 20

	def __init__(self, objective, parent):
		gtk.Button.__init__(self, objective)
		self.set_focus_on_click(False)

		self.objective = objective

		self.connect('clicked',parent.AddObjective, objective)
		self.connect('enter_notify_event',parent.IncreaseLineWidth, objective)
		self.connect('leave_notify_event',parent.IncreaseLineWidth)

		self.prev = None
		self.requirements = []
		self.__dependents = []

		self.__parent = parent

		self.__x = 0
		self.__y = 0

	def Add_Requirement(self, requirement):
		self.requirements.append(requirement)
		requirement.__dependents.append(self)

	def Adjust(self, positions, y):
#		def Get_Middle(array):
#			x_min = 0
#			x_max = 0
#
#			for button in array:
#				x = positions[button][0]
#				if  x_min==0 or x_min > x:
#					x_min = x
#
#				x = positions[button][0] + button.allocation.width
#				if  x_max < x:
#					x_max = x
#
#			return (x_min + x_max)/2

		x = 0
		div = 0

#		x_req = Get_Middle(self.requirements)
#		if x_req:
#			x += x_req
#			div += 1

#		x_dep = Get_Middle(self.__dependents)
#		if x_dep:
#			x += x_dep
#			div += 1

		if div:
			x = x/div - self.allocation.width/2

		# Prevent overlapping with previous requirement at the same level
		if(self.prev
		and x < positions[self.prev][0]+self.prev.allocation.width):
			x = positions[self.prev][0]+self.prev.allocation.width

			# Increase distance between "groups"
			if(self.prev.requirements != self.requirements
			or self.prev.__dependents != self.__dependents):
				x += 20

		# Ensure all requirements are showed in layout
		if  x < 0:
			x = 0

		# Update requirement position
		if self.__x != x or self.__y != y:
			self.__x = x
			self.__y = y

			self.__parent.layout.move(self, self.__x,self.__y)

			return True


	def X(self):
		return self.__x

	def Y(self):
		return self.__y


#import gobject
#gobject.type_register(Requirement)


class Objective(Requirement):
	def __init__(self, name, parent, objective, color):
		Requirement.__init__(self, name, parent)

#		self.connect('button-press-event',parent.__on_objective_clicked)

		# Tooltip
		tooltip = "Cantidad: "+str(objective['quantity'])

		expiration = objective["expiration"]
		if(expiration):
			tooltip += "\nExpiracion: "+expiration

		dependents = parent.controller.Dependents(name)
		if dependents:
			tooltip += "\nDependents: "+str(len(dependents))

		self.set_tooltip_text(tooltip)

		self.__SetExpirationColor(objective, parent.controller,color)


	def __SetExpirationColor(self, objective, controller,color):
		expiration = objective["expiration"]

		# Expired and not satisfacted - Show warning
		if(expiration
		and not controller.IsSatisfaced(self.get_label())):

			# Expired - Set inverted color
			if datetime.strptime(expiration,"%Y-%m-%d %H:%M:%S") < datetime.now():
				self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(0,0,0))
				self.child.modify_fg(gtk.STATE_NORMAL, color)
				return

			# Next to expire - Set color animation
			elif(datetime.strptime(expiration,"%Y-%m-%d %H:%M:%S")
			   < datetime.now()+timedelta(self.config.Get('expirationWarning'))):

				def expires_inverted(color):
					self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(0,0,0))
					self.child.modify_fg(gtk.STATE_NORMAL, color)

					glib.timeout_add_seconds(1, expires_normal, color)
					return False

				def expires_normal(color):
					self.modify_bg(gtk.STATE_NORMAL, color)
					self.child.modify_fg(gtk.STATE_NORMAL, gtk.gdk.Color(0,0,0))

					glib.timeout_add_seconds(1, expires_inverted, color)
					return False

				expires_normal(color)
				return

		# Non expired - Set background color
		self.modify_bg(gtk.STATE_NORMAL, color)