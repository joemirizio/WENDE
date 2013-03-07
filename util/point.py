class Point(object):

	def __init__(self, x=0, y=0):
		self.x = x
		self.y = y

	def __add__(self, point):
		return Point(self.x + point.x, self.y + point.y)

	def __repr__(self):
		return "Point(%d, %d)" % (self.x, self.y)
