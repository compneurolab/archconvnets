from gpu_flag import *
import numpy as np
import copy
from archconvnets.unsupervised.ntm_module2.ntm_module2 import *

def check_weights(WEIGHTS, LAYERS):
	check_network(LAYERS)
	for layer_ind in range(len(LAYERS)):
		L = LAYERS[layer_ind]
		N_ARGS = len(L['in_shape'])
		
		for arg in range(N_ARGS):
			if isinstance(L['in_source'][arg], int) == False or L['in_source'][arg] == -1:
				assert WEIGHTS[layer_ind][arg] is not None, 'layer %i argument %i not initialized' % (layer_ind, arg)
				assert WEIGHTS[layer_ind][arg][1] == L['in_shape'][arg], 'layer %i argument %i not initialized to right size' % (layer_ind, arg)
			else:
				assert WEIGHTS[layer_ind][arg] is None, 'layer %i argument %i should not have weightings because it should be computed from layer %i' % (layer_ind, arg,  L['in_source'][arg])


def check_network(LAYERS):
	n_allocated = return_n_allocated()
	for layer_ind in range(len(LAYERS)):
		L = LAYERS[layer_ind]
		assert isinstance(L['name'],str)
		assert L['name'] != '-' # reserved for prior time step layer outputs
		assert isinstance(L['out_shape'],tuple)
		assert len(L['in_prev']) == len(L['in_shape']) == len(L['deriv_F']) == len(L['in_source'])
		
		if 'additional_forward_args' in L:
			assert len(L['additional_deriv_args']) == len(L['deriv_F'])
		
		# build arguments
		N_ARGS = len(L['in_shape'])
		args = [None] * N_ARGS
		for arg in range(N_ARGS):
			args[arg] = init_buffer(np.asarray(np.random.random(L['in_shape'][arg]),dtype='single'))
		
		# check if function corretly produces specified output dimensions
		if 'additional_forward_args' in L:
			LAYER_OUT = L['forward_F'](args, additional_args=L['additional_forward_args'])
		else:
			LAYER_OUT = L['forward_F'](args)
		assert LAYER_OUT[1] == L['out_shape'], "layer %s (%i) didn't produce expected output (%i, %i)" % (L['name'], layer_ind, np.prod(LAYER_OUT[1]), np.prod(L['out_shape']))
		
		# check if deriv functions correctly produce correct shapes
		for arg in range(N_ARGS):
			expected_shape = tuple(np.concatenate((L['out_shape'], L['in_shape'][arg])))
			if 'additional_forward_args' in L:
				OUT = L['deriv_F'][arg](args, LAYER_OUT, additional_args=L['additional_deriv_args'][arg])
			else:
				OUT = L['deriv_F'][arg](args, LAYER_OUT)
			assert OUT[1] == expected_shape, 'deriv not expected size (layer %s)' % L['name']
			free_buffer(OUT)
		free_buffer(LAYER_OUT)
		
		# free mem
		for arg in range(N_ARGS):
			free_buffer(args[arg])
		
		# check if other layers claim to produce expected inputs
		for arg in range(N_ARGS):
			if L['in_source'][arg] >= 0 and isinstance(L['in_source'][arg], int):
				assert L['in_shape'][arg] == LAYERS[L['in_source'][arg]]['out_shape'], '%i %i' % (layer_ind, arg)
				
		# check if layers are ordered (no inputs to this layer come after this one in the list... unless recursive mem layer)
		for arg in range(N_ARGS):
			if L['in_source'][arg] >= 0 and isinstance(L['in_source'][arg], int):
				assert L['in_source'][arg] < layer_ind or L['in_prev'][arg]
	assert n_allocated == return_n_allocated(), 'check_network() leaked memory'

def check_output_prev(OUTPUT_PREV, LAYERS):
	for layer_ind in range(len(LAYERS)):
		L = LAYERS[layer_ind]
		if layer_ind in L['in_source']:
			assert OUTPUT_PREV[layer_ind][1] == L['out_shape']

def init_weights(LAYERS):
	check_network(LAYERS)
	WEIGHTS = [None]*len(LAYERS)
	for layer_ind in range(len(LAYERS)):
		L = LAYERS[layer_ind]
		N_INPUTS = len(L['in_shape'])
		WEIGHTS[layer_ind] = [None]*N_INPUTS
		for arg in range(N_INPUTS):
			if isinstance(L['in_source'][arg], int) != True:
				WEIGHTS[layer_ind][arg] = init_buffer(L['in_source'][arg]( L['in_shape'][arg] ))
			elif L['in_source'][arg] == -1: # user supplied
				WEIGHTS[layer_ind][arg] = init_buffer()
				
	return WEIGHTS

def mult_partials(A, B, B_out_shape, OUT=None):
	A_ndim = len(A[1]) - len(B_out_shape)
	B_ndim = len(B[1]) - len(B_out_shape)
	assert A_ndim > 0
	assert B_ndim > 0
	assert np.sum(np.asarray(A[1][A_ndim:]) == np.asarray(B[1][:len(B_out_shape)])) == len(B_out_shape)
	
	A_dim0 = np.prod(A[1][:A_ndim])
	B_dim1 = np.prod(B[1][len(B_out_shape):])
	collapsed = np.prod(B_out_shape)

	A_shape = (A_dim0, collapsed)
	B_shape = (collapsed, B_dim1)
	
	out_shape = np.concatenate((A[1][:A_ndim], B[1][len(B_out_shape):]))
	
	Ar = copy.deepcopy(A)
	Br = copy.deepcopy(B)
	
	Ar[1] = A_shape
	Br[1] = B_shape
	
	OUT = dot([Ar, Br], OUT)
	OUT[1] = tuple(out_shape)
	return OUT
	
def build_forward_args(L, layer_ind, OUTPUT, OUTPUT_PREV, WEIGHTS):
	N_ARGS = len(L['in_shape'])
	args = [None] * N_ARGS
	
	for arg in range(N_ARGS):
		src = L['in_source'][arg]
		
		# input is from another layer
		if isinstance(src, int) and src != -1:
			if L['in_prev'][arg]: # from prior timestep
				args[arg] = OUTPUT_PREV[src]
			else: # from current timestep
				args[arg] = OUTPUT[src]
		else: # input is a weighting
			args[arg] = WEIGHTS[layer_ind][arg]
		
	return args

def forward_network(LAYERS, WEIGHTS, OUTPUT, OUTPUT_PREV):
	check_weights(WEIGHTS, LAYERS)
	check_output_prev(OUTPUT_PREV, LAYERS)
	
	OUTPUT = init_gpu_list(OUTPUT, LAYERS, args=False)
	
	for layer_ind in range(len(LAYERS)):
		L = LAYERS[layer_ind]
		N_ARGS = len(L['in_shape'])

		args = build_forward_args(L, layer_ind, OUTPUT, OUTPUT_PREV, WEIGHTS)
		
		if 'additional_forward_args' in L:
			L['forward_F'](args, OUTPUT[layer_ind], additional_args=L['additional_forward_args'])
		else:
			L['forward_F'](args, OUTPUT[layer_ind])
	return OUTPUT
	
def init_gpu_list(LIST, LAYERS, args=True):
	if LIST is None:
		LIST = [None] * len(LAYERS)
		for layer_ind in range(len(LAYERS)):
			L = LAYERS[layer_ind]
			N_ARGS = len(L['in_shape'])
			
			# buffers for each layer's args
			if args:
				LIST[layer_ind] = [None]*N_ARGS
				for arg in range(N_ARGS):
					LIST[layer_ind][arg] = init_buffer()
					
			# buffer only for each layer (ex. layer outputs)
			else:
				LIST[layer_ind] = init_buffer()
	return LIST

def zero_buffer_list(WEIGHTS):
	for layer_ind in range(len(WEIGHTS)):
		for arg in range(len(WEIGHTS[layer_ind])):
			if WEIGHTS[layer_ind][arg] is not None:
				zero_buffer(WEIGHTS[layer_ind][arg])

# compute derivs at each layer
def local_derivs(LAYERS, WEIGHTS, OUTPUT, OUTPUT_PREV, LOCAL_DERIVS):
	check_output_prev(OUTPUT_PREV, LAYERS)
	LOCAL_DERIVS = init_gpu_list(LOCAL_DERIVS, LAYERS)
	
	for layer_ind in range(len(LAYERS)):
		L = LAYERS[layer_ind]
		N_ARGS = len(L['in_shape'])
		
		args = build_forward_args(L, layer_ind, OUTPUT, OUTPUT_PREV, WEIGHTS)
		
		for arg in range(N_ARGS):
			if 'additional_forward_args' in L:
				L['deriv_F'][arg](args, OUTPUT[layer_ind], LOCAL_DERIVS[layer_ind][arg], additional_args=L['additional_deriv_args'][arg])
			else:
				L['deriv_F'][arg](args, OUTPUT[layer_ind], LOCAL_DERIVS[layer_ind][arg])
	return LOCAL_DERIVS

# apply chain-rule down the network
def reverse_network(deriv_above, layer_ind, LAYERS, LOCAL_DERIVS, PARTIALS, WEIGHT_DERIVS, keep_dims=False): # multiply all partials together
	WEIGHT_DERIVS = init_gpu_list(WEIGHT_DERIVS, LAYERS)
	zero_buffer_list(WEIGHT_DERIVS)

	return reverse_network_recur(deriv_above, layer_ind, LAYERS, LOCAL_DERIVS, PARTIALS, WEIGHT_DERIVS, keep_dims)

def reverse_network_recur(deriv_above, layer_ind, LAYERS, LOCAL_DERIVS, PARTIALS, WEIGHT_DERIVS, keep_dims): # multiply all partials together
	L = LAYERS[layer_ind]
	N_ARGS = len(L['in_shape'])
	
	for arg in range(N_ARGS):
		if deriv_above is None:
			deriv_above_new = LOCAL_DERIVS[layer_ind][arg]
		else:
			deriv_above_new = mult_partials(deriv_above, LOCAL_DERIVS[layer_ind][arg], LAYERS[layer_ind]['out_shape'])
		src = L['in_source'][arg]
		
		# input is a layer:
		if isinstance(src, int) and src != -1:
			# memory partials, stop here, add these partials to the correct weight derivs:
			if L['in_prev'][arg]:
				P = PARTIALS[src]
				N_ARGS2 = len(P['in_source'])
				for arg2 in range(N_ARGS2):
					p_layer_ind = P['in_source'][arg2]
					p_arg = P['in_arg'][arg2]
					p_partial = P['partial'][arg2]
					
					deriv_temp = mult_partials(deriv_above_new, p_partial, LAYERS[src]['out_shape'])
					
					WEIGHT_DERIVS[p_layer_ind][p_arg] = point_wise_add((WEIGHT_DERIVS[p_layer_ind][p_arg], deriv_temp))
					
					free_buffer(deriv_temp)
					
			# another layer (At this time step, go back to earlier layers)
			else: 
				reverse_network_recur(deriv_above_new, src, LAYERS, LOCAL_DERIVS, PARTIALS, WEIGHT_DERIVS, keep_dims)
		
		# input is not a layer, end here
		else:
			WEIGHT_DERIVS[layer_ind][arg] = point_wise_add((WEIGHT_DERIVS[layer_ind][arg], deriv_above_new))
			if keep_dims == False: # squeeze
				assert WEIGHT_DERIVS[layer_ind][arg][1][0] == 1
				WEIGHT_DERIVS[layer_ind][arg][1] = tuple(WEIGHT_DERIVS[layer_ind][arg][1][1:])
		
		if deriv_above is not None:
			free_buffer(deriv_above_new)
	return WEIGHT_DERIVS

def init_traverse_to_end(layer_orig, layer_cur, arg, LAYERS, PARTIALS):
	dest = LAYERS[layer_cur]['in_source'][arg]
	
	# don't traverse previous states
	if LAYERS[layer_cur]['in_prev'][arg] == False:
		
		# input or weights, end:
		if (isinstance(dest, int) == False) or dest == -1:
			# have these inputs already been added?
			t1 = np.asarray(PARTIALS[layer_orig]['in_source'])
			t2 = np.asarray(PARTIALS[layer_orig]['in_arg'])
			inds = np.nonzero((t1 == layer_cur) * (t2 == arg))[0]
			assert len(inds) <= 1, 'partials have been added more than once'
			
			# inputs have not been added, add them:
			if len(inds) == 0:
				PARTIALS[layer_orig]['in_source'].append(layer_cur)
				PARTIALS[layer_orig]['in_arg'].append(arg)
				OUT = init_buffer(np.zeros(np.concatenate((LAYERS[layer_orig]['out_shape'], LAYERS[layer_cur]['in_shape'][arg])), dtype='single'))
				PARTIALS[layer_orig]['partial'].append(OUT)
		
		# another layer, go back farther through the network:
		else:
			N_ARGS2 = len(LAYERS[dest]['in_source'])
			for arg2 in range(N_ARGS2):
				init_traverse_to_end(layer_orig, dest, arg2, LAYERS, PARTIALS)

# collect all weight partials which contribute to the memory layers.
# store them at the memory layer
def init_partials(LAYERS, layer_ind):
	PARTIALS = [None]*len(LAYERS)
	
	L = LAYERS[layer_ind]
	N_ARGS = len(L['in_source'])
	PARTIALS[layer_ind] = {'in_source': [], 'in_arg': [], 'partial': []}
	
	for arg in range(N_ARGS):
		if L['in_prev'][arg] == False:
			init_traverse_to_end(layer_ind, layer_ind, arg, LAYERS, PARTIALS)
		
	return PARTIALS
	
def free_partials(PARTIALS_PREV):
	for layer_ind in range(len(PARTIALS_PREV)):
		if PARTIALS_PREV[layer_ind] is not None:
			free_list(PARTIALS_PREV[layer_ind]['partial'])

def copy_traverse_to_end(layer_orig, layer_cur, arg, LAYERS, PARTIALS, MEM_WEIGHT_DERIVS):
	dest = LAYERS[layer_cur]['in_source'][arg]
	
	if LAYERS[layer_cur]['in_prev'][arg] == False:
		# end (weighting, input or mem layer input):
		if (isinstance(dest, int) == False) or dest == -1:
			# have these inputs already been added?
			t1 = np.asarray(PARTIALS[layer_orig]['in_source'])
			t2 = np.asarray(PARTIALS[layer_orig]['in_arg'])
			inds = np.nonzero((t1 == layer_cur) * (t2 == arg))[0]
			assert len(inds) == 1, 'partials have not been added to partials list %i' % len(inds)
			
			# copy partials to mem_weight_derivs
			# note: there is redundant copying happening if a layer contributes to multiple
			# branches...this in principle should be checked for to save some time
			copy_buffer(MEM_WEIGHT_DERIVS[layer_cur][arg], PARTIALS[layer_orig]['partial'][inds[0]])
		
		# continue (another layer)
		else:
			N_ARGS2 = len(LAYERS[dest]['in_source'])
			for arg2 in range(N_ARGS2):
				PARTIALS = copy_traverse_to_end(layer_orig, dest, arg2, LAYERS, PARTIALS, MEM_WEIGHT_DERIVS)
	return PARTIALS

# copy MEM_WEIGHT_DERIVS (partials starting at memory layer) into PARTIALS_PREV
# at the memory layer entry in PARTIALS_PREV
def copy_partials(layer_ind, LAYERS, PARTIALS_PREV, MEM_WEIGHT_DERIVS):
	L = LAYERS[layer_ind]
	N_ARGS = len(L['in_source'])
	
	for arg in range(N_ARGS):
		if L['in_prev'][arg] == False:
			PARTIALS_PREV = copy_traverse_to_end(layer_ind, layer_ind, arg, LAYERS, PARTIALS_PREV, MEM_WEIGHT_DERIVS)
	return PARTIALS_PREV


def find_layer(LAYERS, name):
	if name[-1] == '-':
		name = name[:len(name)-1]
	for layer_ind in range(len(LAYERS)):
		if LAYERS[layer_ind]['name'] == name:
			return layer_ind
	return None
	
