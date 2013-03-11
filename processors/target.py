class Target(object):
	
	def __init__(self, pos):
		self.pos = pos
		self.tracks = []
	
	def __repr__(self):
		return "Target{(%d, %d)}" % (self.pos[0], self.pos[1])
