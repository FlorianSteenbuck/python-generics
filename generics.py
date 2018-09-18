import inspect

def show(var):
	return repr(var)+"{"+str(var)+"}"

# same like ? 
class X():
	pass

class _operation():
	# Operation
	# use it for operation that can validated and compatibled against each other
	# and got the ability to show all possible value operations and match them to variables
	
	# @return success, (value|error) - check if the variable is valid with the operational_args
	@classmethod
	def valid(cls, var, *operational_args):
		return False, cls.__name__+" operation can not validate data"

	# @return success, (value|error) - check if the generic compatible with this operation
	@classmethod
	def compatible(cls, ref, *operational_args):
		return False, cls.__name__+" operation is not compatible with any other generic"
	
	# @return success, [[needed, operations],[needy]] - list of operation-list, that need to match all operations with a variable, and need to match one of these conditions
	@classmethod
	def possibles(cls, *operational_args):
		return False, cls.__name__+" operation can not resolve all possibles"

	# @optional @return success, (value|error) - check if the operation match the variable
	@classmethod
	def match(cls, var, operation):
		return False, cls.__name__+" operation can not match internal operation with a variable"

# operators for java operations
class OR():
	pass

class AND():
	pass

class _javaoperation(_operation):
	@classmethod
	def typ(cls):
		return OR

	@classmethod
	def get_operations(cls, operation_arg):
		return []

	@classmethod
	def get_error_msg(cls, errors, operations):
		error_msg = ""
		for x in range(len(errors)):
			error_msg += errors[x]
			if (x+2) == len(errors):
				error_msg += " and "
			elif (x+1) == len(errors):
				continue
			else:
				error_msg += ", "

		name_msg = ""
		for x in range(len(operations)):
			operation = operations[0]
			if type(operation) == type:
				name_msg += str(operation)
			if inspect.isclass(operation):
				name_msg += operation.__name__

			if (x+2) == len(errors):
				error_msg += " and "
			elif (x+1) == len(errors):
				continue
			else:
				error_msg += ", "

		got_name_msg = len(name_msg) > 0
		got_error_msg = len(error_msg) > 0

		complete_msg = ""
		if got_name_msg:
			name_msg = "is not instance/type of "+name_msg
		if got_error_msg:
			error_msg = "is not valid caused by "+error_msg
		if got_name_msg and got_error_msg:
			complete_msg = name_msg+" "+error_msg
		elif got_name_msg:
			complete_msg = name_msg
		elif got_error_msg:
			complete_msg = error_msg
		else:
			complete_msg = "is not valid for unknow reasons"
		return complete_msg

	@classmethod
	def match(cls, var, operation):
		if type(operation) == type and type(var) == operation:
			return True, var
		if inspect.isclass(operation) and isinstance(var, operation):
			return True, var
		if isinstance(operation, G):
			success, value = operation.valid(var)
			if success:
				return True, value
			else:
				return False, value
		return False, cls.__name__+" unknown operation "+repr(operation)


	@classmethod
	def valid_or(cls, var, operations):
		if len(operations) <= 0:
			return True, None

		errors = []
		for operation in operations:
			success, value = cls.match(var, operation)
			if success:
				return True, value
			else:
				errors.append(value)

		return False, cls.__name__+" "+show(var)+" "+get_error_msg(errors, operations)

	@classmethod
	def valid_and(cls, var, operations):
		for operation in operations:
			success, value = cls.match(var, operation)
			if not success:
				return False, value
			else:
				var = value
		return True, var

	@classmethod
	def prepare_resolve(cls, *operational_args):
		operations = []
		for operation_arg in operational_args:
			for operation in cls.get_operations(operation_arg):
				operations.append(operation)

		fully_compareable = True
		compare_pairs = []
		last_operation = None
		x=0
		while x < len(operations):
			operation = operations[x]
			if x % 2 == 0:
				got_next_operation = (x+1) < len(operations)
				if got_next_operation and (operation == OR or operation == AND) and (not (last_operation == OR or last_operation == AND)):
					x+=1

					operation_pair = [operation]

					next_operation = operations[x]
					if next_operation == operation:
						operation_pair.append(next_operation)
						while x < len(operations):
							next_operation = operations[x]
							
							if x % 2 == 0:
								if (not next_operation == operation):
									break
								continue
							operation_pair.append(next_operation)
							x+=1
						x-=1
					compare_pairs.append(operation_pair)
				else:
					fully_compareable = False
					break
			last_operation = operation
			x+=1

		if fully_compareable:
			fully_compareable = len(compare_pairs) == operations

		return fully_compareable, compare_pairs, operations

	@classmethod
	def valid(cls, var, *operational_args):
		fully_compareable, compare_pairs, operations = cls.prepare_resolve(*operational_args)
		if fully_compareable:
			for compare_pair in compare_pairs:
				typ = compare_pair[0]
				compare_operations = compare_pair[1:]
				success, value = False, cls.__name__+" can not find java operation typ for "+repr(typ)
				if typ == OR:
					success, value = cls.valid_or(var, *compare_operations)
				elif typ == AND:
					success, value = cls.valid_and(var, *compare_operations)

				if not success:
					return success, value
				else:
					var = value
			return True, var
		else:
			typ = cls.typ()
			if typ == OR:
				return cls.valid_or(var, operations)
			elif typ == AND:
				return cls.valid_and(var, operations)
			else:
				return False, cls.__name__+" can not find java operation typ for "+repr(typ)

	@classmethod
	def possibles(cls, *operational_args):
		results = []

		fully_compareable, compare_pairs, operations = cls.prepare_resolve(*operational_args)
		if fully_compareable:
			for compare_pair in compare_pairs:
				typ = compare_pair[0]
				compare_operations = compare_pair[1:]
				if typ == OR:
					for compare_operation in compare_operations:
						results.append([compare_operation]) 
				elif typ == AND:
					results.append(compare_operations)
		else:
			typ = cls.typ()
			if typ == OR:
				for operation in operations:
					results.append([operation]) 
			elif typ == AND:
				results.append(operations)

		return True, results

class super(_javaoperation):
	pass

class extends(_javaoperation):
	@classmethod
	def typ(cls):
		return AND

	@classmethod
	def get_operations(cls, operation_arg):
		if type(operation_arg) == type or inspect.isclass(operation_arg) or isinstance(operation_arg, G):
			return [operation_arg]
		else:
			return []	

	@classmethod
	def compatible(cls, ref, *operational_args):
		roperation = ref.operation
		if isinstance(roperation, extends):
			for rpossible in ref.possibles():
				for possible in cls.possibles():
					if rpossible == possible:
						return True, None
			return False, cls.__name__+" is not compatible with ref generic"
		return False, cls.__name__+" operation of ref is not supported yet"

class GenericError(Exception):
	pass

class G():
	# Generic
	# use this for definition of a generic
	def __init__(self, entity, operation, *operational_args, **kwargs):
		root = False
		if "root" in kwargs.keys() and type(kwargs["root"]) == bool:
			root = kwargs["root"]
		
		if root and entity == X:
			raise GenericError("You need to define valid key on the root X is not allowed")
		self.entity = entity
		if not issubclass(operation, _operation):
			raise GenericError("We need a operation from the operation class")
		self.operation = operation
		self.operational_args = operational_args 

	def valid(self, var):
		return self.operation.valid(var, *self.operational_args)

	def match(self, var, operation):
		return self.operation.match(var, operation)

	def possibles(self):
		return self.operation.possibles(*self.operational_args)

	def compatible(self, ref):
		success, error = self.operation.compatible(ref, *self.operational_args)
		success_ref, error_ref = ref.valid(self)
		error_msg = None
		if (not success) and (not success_ref):
			error_msg = "Both Fail"
		else:
			error_msg = "One Fail"

		if (not success):
			error_msg += "\n[main] "+error
		if (not success_ref):
			error_msg += "\n[ref] "+error

		return success_ref and success, error_msg

class GT():
	"""
	Generic Typ
	use this for list, dict, tuple definitions
	"""
	def __init__(self, generics, typ):
		self.generics = generics
		self.typ = typ

class GC():
	"""
	Generic Class
	use this for Generics that are bounded to a class
	see Java <Z extends `A<T extends B, X extends D>`>
	see Python
	([['Z', extends, GC(
		[
			['T', extends, B],
			['X', extends, D]
		], A)
	]])
	"""
	def __init__(self, generics, classobj):
		self.generics = generics
		self.classobj = classobj

class GV():
	# Generic Value
	# use this for direct generic values
	def __init__(self, generic, value, generics=None):
		if type(generics) != list:
			generics = [generic]
		self.generics = generics
		self.generic = generic
		self.value = process_generic_value(generic, value, generics)

class GenericObject():
	def __init__(self, generics, *args, **kwargs):
		self.generics = generics
		self.g = process_args(generics, self._init, void=True, *args, **kwargs)[0]
	
	def __getattr__(self, key):
		if key in self.g.keys():
			return self.g[key]
		return super.__getitem__(self, key)

	def _init(self, *args, **kwargs):
		pass

class GenericTyp(GenericObject):
	def __init__(self, *args, **kwargs):
		generic = []
		if "typ" in kwargs.keys() and type(kwargs["typ"]) == type:
			generic = ['value',extends,kwargs["typ"]]
		GenericObject.__init__(self, [
			generic
		], *args, **kwargs)
	
	def __getattr__(self, key):
		return getattr(self._value, key)

	def __getitem__(self, key):
		return self._value[key]

	def _init(self, value):
		self._value = value

class Type(GenericTyp):
	def __init__(self, value):
		GenericTyp.__init__(self, value=value, typ=type)

class Bool(GenericTyp):
	def __init__(self, value):
		GenericTyp.__init__(self, value=value, typ=bool)

class Int(GenericTyp):
	def __init__(self, value):
		GenericTyp.__init__(self, value=value, typ=int)

class Long(GenericTyp):
	def __init__(self, value):
		GenericTyp.__init__(self, value=value, typ=long)

class Float(GenericTyp):
	def __init__(self, value):
		GenericTyp.__init__(self, value=value, typ=float)

class Str(GenericTyp):
	def __init__(self, value):
		GenericTyp.__init__(self, value=value, typ=str)

class Unicode(GenericTyp):
	def __init__(self, value):
		GenericTyp.__init__(self, value=value, typ=unicode)

class Tuple(GenericTyp):
	def __init__(self, value):
		GenericTyp.__init__(self, value=value, typ=tuple)

class Dict(GenericTyp):
	def __init__(self, value):
		GenericTyp.__init__(self, value=value, typ=dict)

class Compile(GenericTyp):
	def __init__(self, value):
		GenericTyp.__init__(self, value=value, typ=compile)

class File(GenericTyp):
	def __init__(self, value):
		GenericTyp.__init__(self, value=value, typ=file)

class XRange(GenericTyp):
	def __init__(self, value):
		GenericTyp.__init__(self, value=value, typ=xrange)

class Slice(GenericTyp):
	def __init__(self, value):
		GenericTyp.__init__(self, value=value, typ=slice)

class Buffer(GenericTyp):
	def __init__(self, value):
		GenericTyp.__init__(self, value=value, typ=buffer)

class Property(GenericTyp):
	def __init__(self, value):
		GenericTyp.__init__(self, value=value, typ=property)

def process_generic_value(generic, value, generics):
	if isinstance(value, GV):
		success, error = generic.compatible(value.generic)
		if not success:
			raise GenericError(error)
		value = value.value

	# TODO generic typ support

	if isinstance(generic, GC):
		if not (isinstance(value, GenericObject) and isinstance(value, generic.classobj)):
			raise GenericError(show(value)+" is instance of the given generic class")
		
		for vgeneric in value.generics:
			for igeneric in generics:
				if igeneric.entity == ygeneric.entity:
					success, error = generic.compatible(value.generic)
					if not success:
						raise GenericError(error)

		return value

	success, value = generic.valid(value)
	if not success:
		raise GenericError(value)
	return value

def resolve_generic(may_generic, root=True):
	operationals = []
	i=2
	while i < len(may_generic):
		operational = may_generic[i]
		if type(operational) == tuple or type(operational) == list and len(operational) > 1:
			operational = resolve_generic(operational, root=False)
	 	operationals.append(operational)
	 	i+=1
	return G(may_generic[0], may_generic[1], root=root, *operationals)

def process_args(generics, call, *targs, **kwargs):
	not_in_use = {}

	strict = False
	if "strict" in kwargs.keys() and type(kwargs["strict"]) == bool:
		strict = kwargs["strict"]
		kwargs.pop("strict", None)
	void = False
	if "void" in kwargs.keys() and type(kwargs["void"]) == bool:
		void = kwargs["void"]
		kwargs.pop("void", None)
	args = list(targs)
	for may_generic in generics:
		generic = None
		if (not strict) and (type(may_generic) == tuple or type(may_generic) == list):
			if len(may_generic) > 1:
				generic = resolve_generic(may_generic)
		elif isinstance(may_generic, generics.G):
			generic = may_generic	

		if generic == None:
			# TODO warn
			continue

		value = None
		readable_value = None
		
		key_generic = type(generic.entity) == str
		args_generic = type(generic.entity) == int and generic.entity < len(args)
		kwargs_generic = key_generic and generic.entity in kwargs.keys()
		if args_generic:
			value = args[generic.entity]
			readable_value = "args["+str(generic.entity)+"]{"+str(value)+"}"
		elif kwargs_generic:
			value = kwargs[generic.entity]
			readable_value = "kwargs["+str(generic.entity)+"]{"+str(value)+"}"
		elif key_generic:
			not_in_use[generic.entity] = generic
			continue
		else:
			# TODO warn
			continue
		
		value = process_generic_value(generic, value, generics)
		
		if args_generic:
			args[generic.entity] = value
		elif kwargs_generic:
			kwargs[generic.entity] = value
	if void:
		call(*args, **kwargs)
		return not_in_use, None
	return not_in_use, call(*args, **kwargs)
