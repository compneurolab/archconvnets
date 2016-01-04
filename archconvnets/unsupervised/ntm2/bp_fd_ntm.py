from gpu_flag import *
import numpy as np
import copy
import time
import scipy.optimize
from ntm_core import *

N_FRAMES = 5
N_CONTROLLERS = 16
M_LENGTH = 6
N_MEM_SLOTS = 8
mem_shape = (N_MEM_SLOTS, M_LENGTH)

free_all_buffers()

#############
LAYERS = []

add_linear_F_layer(LAYERS, 'FW', N_MEM_SLOTS, (8, M_LENGTH))
add_add_layer(LAYERS, 'MEM', ['FW', 'MEM'])
#add_focus_keys_layer(LAYERS, 'FM', ['MEM', -1])
add_linear_F_layer(LAYERS, 'F3', 25)
add_sum_layer(LAYERS, 'SUM')				


################
FW_IND = find_layer(LAYERS, 'FW')
FM_IND = find_layer(LAYERS, 'FM')
MEM_IND = find_layer(LAYERS, 'MEM')

WEIGHTS = init_weights(LAYERS)
xt = random_function(np.concatenate(((N_FRAMES,), LAYERS[FW_IND]['in_shape'][1])))
set_buffer(xt[0], WEIGHTS[FW_IND][1])
check_weights(WEIGHTS, LAYERS)

DERIV_TOP = init_buffer(np.ones((1,1), dtype='single'))

mem_init = random_function(LAYERS[MEM_IND]['out_shape'])

################
gradient_layer = FW_IND
gradient_arg = 0
assert isinstance(LAYERS[gradient_layer]['in_source'][gradient_arg], int) != True, 'derivative of intermediate layer'
ref = return_buffer(WEIGHTS[gradient_layer][gradient_arg])

def f(y):
	OUTPUT = None; OUTPUT_PREV = [None] * len(LAYERS)
	OUTPUT_PREV[MEM_IND] = init_buffer(mem_init)
	Wy = return_buffer(WEIGHTS[gradient_layer][gradient_arg])
	weights_shape = Wy.shape; Wy = Wy.ravel(); Wy[i_ind] = y
	set_buffer(Wy.reshape(weights_shape), WEIGHTS[gradient_layer][gradient_arg])
	
	for frame in range(N_FRAMES):
		set_buffer(xt[frame], WEIGHTS[FW_IND][1])  # inputs
		check_weights(WEIGHTS, LAYERS)
		
		OUTPUT = forward_network(LAYERS, WEIGHTS, OUTPUT, OUTPUT_PREV)
		
		free_list(OUTPUT_PREV)
		OUTPUT_PREV = copy_list(OUTPUT)
	
	z = return_buffer(OUTPUT[-1])[0]
	free_list(OUTPUT)
	free_list(OUTPUT_PREV)
	return z

def g(y):
	OUTPUT = None; LOCAL_DERIVS = None; WEIGHT_DERIVS = None
	OUTPUT_PREV = [None] * len(LAYERS); MEM_WEIGHT_DERIVS = None
	OUTPUT_PREV[MEM_IND] = init_buffer(mem_init)
	Wy = return_buffer(WEIGHTS[gradient_layer][gradient_arg])
	weights_shape = Wy.shape; Wy = Wy.ravel(); Wy[i_ind] = y
	set_buffer(Wy.reshape(weights_shape), WEIGHTS[gradient_layer][gradient_arg])
	
	PARTIALS_PREV = init_partials(LAYERS)
	for frame in range(N_FRAMES):
		if frame != 0: # todo: reverse_network should zero out weight_derivs before beginning
			free_list(WEIGHT_DERIVS); WEIGHT_DERIVS = None
			free_list(MEM_WEIGHT_DERIVS); MEM_WEIGHT_DERIVS = None
		
		set_buffer(xt[frame], WEIGHTS[FW_IND][1])  # inputs
		check_weights(WEIGHTS, LAYERS)
		
		OUTPUT = forward_network(LAYERS, WEIGHTS, OUTPUT, OUTPUT_PREV)
		
		LOCAL_DERIVS = local_derivs(LAYERS, WEIGHTS, OUTPUT, OUTPUT_PREV, LOCAL_DERIVS)
		WEIGHT_DERIVS = reverse_network(DERIV_TOP, len(LAYERS)-1, LAYERS, LOCAL_DERIVS, PARTIALS_PREV, WEIGHT_DERIVS)
		
		# update partials_prev
		MEM_WEIGHT_DERIVS = reverse_mem_network(MEM_IND, LAYERS, LOCAL_DERIVS, PARTIALS_PREV, MEM_WEIGHT_DERIVS)
		PARTIALS_PREV = copy_partials(MEM_IND, LAYERS, PARTIALS_PREV, MEM_WEIGHT_DERIVS)
		free_list(OUTPUT_PREV)
		OUTPUT_PREV = copy_list(OUTPUT)
		
	z = return_buffer(WEIGHT_DERIVS[gradient_layer][gradient_arg]).ravel()[i_ind]
	
	free_partials(PARTIALS_PREV)
	free_list(LOCAL_DERIVS)
	free_list(OUTPUT)
	free_list(WEIGHT_DERIVS)
	free_list(OUTPUT_PREV)
	return z

np.random.seed(np.int64(time.time()))
eps = np.sqrt(np.finfo(np.float).eps)*1e5

N_SAMPLES = 25
ratios = np.zeros(N_SAMPLES)
t_start = time.time()
for sample in range(N_SAMPLES):
	i_ind = np.random.randint(np.prod(ref.shape))
	y = ref.ravel()[i_ind]
	gt = g(y); gtx = scipy.optimize.approx_fprime(np.ones(1)*y, f, eps)
	
	if gtx == 0:
		ratios[sample] = 1
	else:
		ratios[sample] = gtx/gt
	print gt, gtx, ratios[sample]
	
print ratios.mean(), ratios.std(), time.time() - t_start, GPU
