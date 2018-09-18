from generics import GenericObject
from generics import extends

class A(GenericObject):
	def __init__(self, *args, **kwargs):
		GenericObject.__init__(self, [
			['b',extends,int],
			['a',extends,str],
			[0,extends,bool],
			['T',extends,float]
		], *args, **kwargs)
	def _init(self, c, a, b):
		print "success c="+str(c)+" a="+str(a)+" b="+str(b)

try:
	a = A(True, a="it works", b=1)
	a.T.valid(1.0)
except:
	print "fail!"

try:
	a = A(True, a="it do not work", b=1.0)
	print "fail!"
except:
	print "success!"

a = A(True, a="it works", b=1)
if a.T.valid(None)[0]:
	print "fail!"
else:
	print "success!"