from generics import GenericError
from generics import GenericObject
from generics import extends
from generics import generic_method
from generics import AND
from generics import OR
from generics import GC

class F():
	pass

class C():
	pass

class D():
	pass

class E(C, D):
	pass

class Complex(GenericObject):
	def __init__(self, *args, **kwargs):
		GenericObject.__init__(self,[
			['b',extends,GC(['dc', extends, D],B)]
		], *args, **kwargs)

	def _init(self, b):
		print b

class G(GenericObject):
	def __init__(self, *args, **kwargs):
		GenericObject.__init__(self,[
			['e',extends,D,C]
		], *args, **kwargs)

	def _init(self, e):
		print e

class B(GenericObject):
	def __init__(self, *args, **kwargs):
		GenericObject.__init__(self,[
			['dc',extends,D,OR,C]
		], *args, **kwargs)

	def _init(self, dc):
		print dc

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
except Exception as ex:
	print ex
	print "fail!"
"""
try:
	a = A(True, a="it do not work", b=1.0)
	print "fail!"
except GenericError as ex:
	print ex
	print "success!"
except Exception as ex:
	print ex
	print "fail!"
"""

a = A(True, a="it works", b=1)
if a.T.valid(None)[0]:
	print "fail!"
else:
	print "success!"


def yeah(*nargs, **nkwargs):
    nkwargs["args"]=["a","b","c"]
    generic_method([
    	['b', extends, int],
    	['a', extends, str],
    	[0, extends, bool],
    	['T', extends, float]
    ], vars(), *nargs, **nkwargs)
    print "success c="+str(c)+" a="+str(a)+" b="+str(b)