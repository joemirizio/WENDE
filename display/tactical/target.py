class Target:
	
	def __init__(self, name, pos):
		self.name = name
		self.pos = pos
	
	def __repr__(self):
		return "Target{%s: %s}" % (self.name, self.pos)
