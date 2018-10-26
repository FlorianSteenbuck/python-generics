import inspect

STRICT_MODE=False

def has_item_key(value, key):
	return (hasattr(value, "keys") and get_type(key) == str and key in value.keys()) or (hasattr(value, '__len__') and get_type(key) == int and key < len(value))

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
	def match(cls, var, operation, default_msg=None):
		if isinstance(operation, GC) and isinstance(var, operation.classobj):
			not_in_use, all_generics, args, kwargs, var = process_args(operation.generics, operation.classobj, *var.args, **var.kwargs)
			print not_in_use, all_generics, args, kwargs, var
			var.args = args
			var.kwargs = kwargs
			var.g = not_in_use
			var.generics = all_generics
			return True, var
		if default_msg is not None:
			return False, cls.__name__+" operation can not match internal operation with a variable"
		else:
			return False, default_msg

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
			if get_type(operation) == type:
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
		if get_type(operation) == type and get_type(var) == operation:
			return True, var
		if inspect.isclass(operation) and isinstance(var, operation):
			return True, var
		if isinstance(operation, G):
			success, value = operation.valid(var)
			if success:
				return True, value
			else:
				return False, value
		return super.match(cls, cls.__name__+" unknown operation "+repr(operation))

	@classmethod
	def valid_or(cls, var, *operations):
		if len(operations) <= 0:
			return True, None

		errors = []
		for operation in operations:
			success, value = cls.match(var, operation)
			if success:
				return True, value
			else:
				errors.append(value)

		return False, cls.__name__+" "+show(var)+" "+cls.get_error_msg(errors, operations)

	@classmethod
	def valid_and(cls, var, *operations):
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
			if (x+1) % 2 == 0:
				got_next_operation = (x+1) < len(operations)
				if (operation == OR or operation == AND) and (not (last_operation == OR or last_operation == AND)):
					if not got_next_operation:
						continue
					x+=1

					operation_pair = [operation, last_operation]
					next_operation = operations[x]
					if (not (next_operation == OR or next_operation == AND)):
						operation_pair.append(next_operation)
						x+=1
						while x < len(operations):
							next_operation = operations[x]
							
							if (x+1) % 2 == 0:
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
			fully_compareable = x == len(operations) and len(compare_pairs) > 0
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
				return cls.valid_or(var, *operations)
			elif typ == AND:
				return cls.valid_and(var, *operations)
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
		if get_type(operation_arg) == type or inspect.isclass(operation_arg) or isinstance(operation_arg, G):
			return [operation_arg]
		else:
			return []	

	@classmethod
	def compatible(cls, ref, *operational_args):
		roperation = ref.operation
		if issubclass(roperation, extends):
			for rpossible in ref.possibles()[1:][0]:
				for possible in cls.possibles(*operational_args)[1:][0]:
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
		if "root" in kwargs.keys() and get_type(kwargs["root"]) == bool:
			root = kwargs["root"]
		
		if root and entity == X:
			raise GenericError("You need to define valid key on the root X is not allowed")
		self.entity = entity
		if not issubclass(operation, _operation):
			raise GenericError("We need a operation from the operation class")
		self.operation = operation
		self.operational_args = operational_args 

	def __str__(self):
		operational_str = ""
		
		first = True
		for operational_arg in self.operational_args:
			if not first:
				operational_str += " "
			if operational_arg == OR:
				operational_str += "|"
			elif operational_arg == AND:
				operational_str += "&"
			elif isinstance(operational_arg, GC):
				operational_str += "<"+str(operational_arg)+">"
			else:
				operational_str += str(operation_arg)

		self.entity+" "+self.operation.__name__+" "+operational_arg

	def valid(self, var):
		return self.operation.valid(var, *self.operational_args)

	def match(self, var, operation):
		return self.operation.match(var, operation)

	def possibles(self):
		return self.operation.possibles(*self.operational_args)

	def compatible(self, ref):
		return self.operation.compatible(ref, *self.operational_args)

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
	def __init__(self, generics, classobj, strict=STRICT_MODE):
		self.generics = []
		self.generic_classes = []
		for generic in generics:
			if isinstance(generic, G):
				self.generics.append(generic)
			elif (not strict) and (get_type(generic) == tuple or get_type(generic) == list):
				if len(generic) > 1:
					generic_values = resolve_generic_values(generic)
					generic = generic_values[0]
					for generic_class in generic_values[1:]:
						generic_classes.append(generic_class)
					self.generics.append(generic)
		self.classobj = classobj

class GV():
	# Generic Value
	# use this for direct generic values
	def __init__(self, generic, value):
		self.generic = generic
		self.value = process_generic_value(generic, value)

class GenericObject():
	def __init__(self, generics, *args, **kwargs):
		self.g, self.generics, self.args, self.kwargs, too_many_python = process_args(generics, self._init, void=True, *args, **kwargs)
		
	def __getitem__(self, key):
		if key in self.g.keys():
			return self.g[key]
		return super.__getitem__(self, key)

	def _init(self, *args, **kwargs):
		pass

def _handle_arg_is_default(name, _type, default, *types, **kwargs):
	result = default
	if name in kwargs and type(kwargs[name]) in types:
		return _type(kwargs[name]), False
	return result, True

def handle_arg(name, _type, default, *types, **kwargs):
	return _handle_arg_is_default(name, _type, default, *types, **kwargs)[0]

def handle_args(_vars, args, **kwargs):
	if type(args) != dict:
		return

	for arg_key in args.keys():
		arg = args[arg_key]
		_vars[arg_key] = handle_arg(arg_key, arg["type"], arg["default"], *arg["types"], **kwargs) 

def generic_method(generics, _vars, *pargs, **pkwargs):
	args = handle_arg("args", list, [], list, tuple, **pkwargs)
	kwargs = handle_arg("kwargs", dict, {}, dict, **pkwargs)
	keywords = handle_arg("keywords", str, None, str, **pkwargs)
	arguments = handle_arg("arguments", str, None, str, **pkwargs)
	
	duplicated_arguments = []
	for arg in args:
		if arg in kwargs.keys():
			duplicated_arguments.append(arg)

	if len(duplicated_arguments) > 0:
		raise GenericError(",".join(duplicated_arguments)+" arguments are duplicated")

	g, generics, pargs, pkwargs, var = process_args(generics, *pargs, **pkwargs)

	if len(args) > len(pargs):
		raise GenericError("Passed arguments needs to be at least as long as all not default arguments")

	rest_args = []
	n = 0
	while n < len(args):
		n += 1
	
	while n < len(pargs):
		rest_args.append(pargs[n])
		n += 1

	rest_kwargs = {}
	for key in pkwargs.keys():
		if key not in kwargs.keys():
			rest_kwargs[key] = pkwargs[key]

	for key in pkwargs.keys():
		kwargs[key] = pkwargs[key]

	if type(keywords) == str:
		kwargs[keywords] = rest_kwargs
		_vars["__kwargs_name__"] = keywords
	elif len(rest_kwargs.keys()) > 0:
		raise GenericError("We got kwargs to handle but no kwargs handle")

	if type(arguments) == str:
		kwargs[arguments] = rest_args
		_vars["__args_name__"] = arguments
	elif len(rest_args) > 0:
		raise GenericError("We got args to handle but no args handle")

	for key in kwargs.keys():
		_vars[key] = kwargs[key]

	for key in g.keys():
		_vars[key] = g[key]

	_vars["generics"] = generics

def process_generic_special(special, generics):
	if isinstance(special, GC):
		for vgeneric in special.generics:
			for igeneric in generics:
				if igeneric.entity == vgeneric.entity:
					success, error = generic.compatible(value.generic)
					if not success:
						raise GenericError(error)
		all_generics = []
		for generic in special.generics:
			all_generics.append(generic)
		for generic_class in special.generic_classes:
			process_generic_special(generic_class, all_generics)

def process_generic_value(generic, value):
	if isinstance(value, GV):
		success, error = generic.compatible(value.generic)
		if not success:
			raise GenericError(error)
		value = value.value

	success, value = generic.valid(value)
	if not success:
		raise GenericError(value)
	return value

class GenericTyp(GenericObject):
	def __init__(self, typ, *args, **kwargs):
		generic = []

		self._attr_method = {}
		self._item_method = {}
		
		GenericObject.__init__(self, [
			generic
		], *args, **kwargs)
	
	def _init(self, value):
		self._value = value

	def _get_attr_method(self, key, method):
		if not key in self._attr_method.keys():
			self._attr_method[key] = TypedFunction(method, self._typ)
		return self._attr_method[key].call

	def _get_item_method(self, key, method):
		if not key in self._item_method.keys():
			self._item_method[key] = TypedFunction(method, self._typ)
		return self._item_method[key].call

	"""
	def __getattr__(self, key):
		var = getattr(self._value, key)
		if inspect.ismethod(var):
			return _get_attr_method(key, var)
		return var
	"""
	
	def __getitem__(self, key):
		var = self._value[key]
		if inspect.ismethod(var):
			return _get_item_method(key, var)
		return var
	
	def __setattr__(self, key, value):
		setattr(self._value, key, value)

	def __setitem__(self, key, value):
		self._value[key] = value


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

natives = (
	(type, Type),
	(bool, Bool),
	(int, Int),
	(long, Long),
	(float, Float),
	(str, Str),
	(unicode, Unicode),
	(tuple, Tuple),
	(dict, Dict),
	(compile, Compile),
	(file, File),
	(xrange, XRange),
	(slice, Slice),
	(buffer, Buffer),
	(property, Property)
)

def get_type(var):
	global natives
	if type(var) == type(X):
		for nativ_pair in natives:
			typ = nativ_pair[0]
			_class = nativ_pair[1]
			if isinstance(var, _class):
				return True
	return type(var)

def is_nativ_typ(typ):
	global natives
	if type(typ) == type:
		for nativ_pair in natives:
			_typ = nativ_pair[0]
			if _typ == typ:
				return True
	elif type(var) == type(X):
		for nativ_pair in natives:
			_class = nativ_pair[1]
			if issubclass(_class, typ):
				return True
	return False

def init_nativ(typ, value):
	global natives
	for nativ_pair in natives:
		_typ = nativ_pair[0]
		_class = nativ_pair[1]
		if typ == _typ:
			return _class(value=value)
	return None

class TypedFunction():
	def __init__(self, func, typ):
		self.func = func
		self.typ = typ

	def call(self, *args, **kwargs):
		var = self.func(*args, **kwargs)
		typ = type(var)
		if is_nativ_typ(typ):
			return init_nativ(typ, var)
		return var

def resolve_generic_values(may_generic, root=True):
	operational_classes = []
	operationals = []
	i=2
	while i < len(may_generic):
		operational = may_generic[i]
		if isinstance(operational, GC):
			operational_classes.append(operational)
		
		if get_type(operational) == tuple or get_type(operational) == list and len(operational) > 1:
			new_generic_values = resolve_generic_values(operational, root=False)
	 		operational = new_generic_values[0]
	 		for operational_class in new_generic_values[1:]:
	 			operational_classes.append(operational_class)
	 	
	 	operationals.append(operational)
	 	i+=1

	generic_values = [G(may_generic[0], may_generic[1], root=root, *operationals)]
	for generic_value in operational_classes:
		generic_values.append(generic_value)
	
	return generic_values

def process_args(generics, call, *targs, **kwargs):
	all_generics = []
	all_generic_classes = []
	not_in_use = {}

	strict, stay_strict = _handle_arg_is_default("strict", bool, STRICT_MODE, bool, **kwargs)
	void, stay_void = _handle_arg_is_default("void", bool, False, bool, **kwargs)
	
	if not stay_strict:
		kwargs.pop("strict", None)
	if not stay_void:
		kwargs.pop("void", None)

	args = list(targs)
	for may_generic in generics:
		generic = None
		if (not strict) and (get_type(may_generic) == tuple or get_type(may_generic) == list):
			if len(may_generic) > 1:
				generic_values = resolve_generic_values(may_generic)
				generic = generic_values[0]
				for generic_class in generic_values[1:]:
					all_generic_classes.append(generic_class)
		elif isinstance(may_generic, G):
			generic = may_generic	

		if generic == None:
			# TODO warn
			continue

		all_generics.append(generic)

		value = None
	
		key_generic = get_type(generic.entity) == str
		args_generic = get_type(generic.entity) == int and generic.entity < len(args)
		kwargs_generic = key_generic and generic.entity in kwargs.keys()
		if args_generic:
			value = args[generic.entity]
		elif kwargs_generic:
			value = kwargs[generic.entity]
		elif key_generic:
			not_in_use[generic.entity] = generic
			continue
		else:
			# TODO warn
			continue
		
		value = process_generic_value(generic, value)
		
		if args_generic:
			args[generic.entity] = value
		elif kwargs_generic:
			kwargs[generic.entity] = value
		for generic_class in all_generic_classes:
			process_generic_special(generic_class, all_generics)

	if call == None:
		return not_in_use, all_generics, args, kwargs, None

	if void:
		call(*args, **kwargs)
		return not_in_use, all_generics, args, kwargs, None
	return not_in_use, all_generics, args, kwargs, call(*args, **kwargs)
