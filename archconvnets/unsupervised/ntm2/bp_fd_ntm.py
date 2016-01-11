import numpy as np
import time
import scipy.optimize
from ntm_core import *

N_FRAMES = 10
N_CONTROLLERS = 16
N_MEM_SLOTS = 6
M_LENGTH = 8
N_SHIFTS = 3

mem_shape = (N_MEM_SLOTS, M_LENGTH)

free_all_buffers()

############# init layers
LAYERS = []

N_F1 = 12
N_F2 = 7
N_F3 = 9
HEAD_INPUT = 'F3'

for init in [0,1]:
	# below
	F1_IND = add_linear_F_layer(LAYERS, 'F1', N_F1, (2, 1), init=init)
	F2_IND = add_linear_F_layer(LAYERS, 'F2', N_F2, init=init)
	F3_IND = add_linear_F_layer(LAYERS, HEAD_INPUT, N_F3, init=init)

	###### read
	# content
	R_KEY_IND = add_linear_F_layer(LAYERS, 'R_KEY', (N_CONTROLLERS, M_LENGTH), HEAD_INPUT, init=init)
	R_CONTENT_IND = add_cosine_sim_layer(LAYERS, 'R_CONTENT', ['R_KEY', 'MEM-'], mem_shape, init=init)
	R_BETA_IND = add_linear_F_layer(LAYERS, 'R_BETA', N_CONTROLLERS, HEAD_INPUT, init=init)
	R_CONTENT_FOCUSED_IND = add_focus_keys_layer(LAYERS, 'R_CONTENT_FOCUSED', ['R_CONTENT', 'R_BETA'], init=init)
	R_CONTENT_SM_IND = add_softmax_layer(LAYERS, 'R_CONTENT_SM', init=init)
	
	# interpolate
	R_IN_GATE_PRE_IND = add_linear_F_layer(LAYERS, 'R_IN_GATE_PRE', N_CONTROLLERS, HEAD_INPUT, init=init)
	R_IN_GATE_IND = add_sigmoid_layer(LAYERS, 'R_IN_GATE', init=init)
	
	R_T_F_IND = add_linear_F_layer(LAYERS, 'R_T_F', N_CONTROLLERS, (4, N_MEM_SLOTS), init=init)
	
	R_IN_PRE = add_interpolate_layer(LAYERS, 'R_IN_PRE', ['R_IN_GATE', 'R_CONTENT_SM', 'R_T_F'], init=init)
	R_IN = add_softmax_layer(LAYERS, 'R_IN', init=init)
	
	# shift
	R_SHIFT_PRE = add_linear_F_layer(LAYERS, 'R_SHIFT_PRE', (N_CONTROLLERS, N_SHIFTS), HEAD_INPUT, init=init)
	R_SHIFT = add_softmax_layer(LAYERS, 'R_SHIFT', init=init)
	
	R_T_IND = add_linear_F_layer(LAYERS, 'R_T', N_MEM_SLOTS, (3, M_LENGTH), init=init)
	
	MEM_IND = add_add_layer(LAYERS, 'MEM', ['R_T', 'MEM-'], -1, init=init)
	SQ_IND = add_sq_points_layer(LAYERS, 'SQ', init=init)
	add_sum_layer(LAYERS, 'SUM', init=init)

'''for init in [0,1]:
	F1_IND = add_linear_F_layer(LAYERS, 'F1', N_CONTROLLERS, (3,M_LENGTH), init=init)
	F2_IND = add_linear_F_layer(LAYERS, 'F2', N_CONTROLLERS, (3,M_LENGTH), init=init)
	RCONTENT_SUM_IND = add_add_layer(LAYERS, 'RCONTENT_SUM', ['F1', 'MEM-'], init=init)
	RCONTENT_SUM2_IND = add_add_layer(LAYERS, 'RCONTENT_SUM2', ['F2', 'MEM2-'], init=init)

	MEM_IND = add_add_layer(LAYERS, 'MEM', ['RCONTENT_SUM', 'MEM-'], init=init)
	MEM2_IND = add_add_layer(LAYERS, 'MEM2', ['RCONTENT_SUM2', 'MEM2-'], init=init)
	MEM3_IND = add_add_layer(LAYERS, 'MEM3', ['MEM-', 'MEM2'], init=init)
	add_sum_layer(LAYERS, 'SUM', init=init)'''

check_network(LAYERS)

################ init weights and inputs

WEIGHTS = init_weights(LAYERS)
x1t = random_function(np.concatenate(((N_FRAMES,), LAYERS[F1_IND]['in_shape'][1])))
x2t = random_function(np.concatenate(((N_FRAMES,), LAYERS[R_T_IND]['in_shape'][1])))
x3t = random_function(np.concatenate(((N_FRAMES,), LAYERS[R_T_F_IND]['in_shape'][1])))
mem_init = random_function(LAYERS[MEM_IND]['out_shape'])
#mem2_init = random_function(LAYERS[MEM2_IND]['out_shape'])

DERIV_TOP = init_buffer(np.ones((1,1), dtype='single'))

################ which gradient to test
gradient_layer = R_T_IND
gradient_arg = 0

def f(y):
	OUTPUT = None; OUTPUT_PREV = [None] * len(LAYERS)
	OUTPUT_PREV[MEM_IND] = init_buffer(mem_init)
	#OUTPUT_PREV[MEM2_IND] = init_buffer(mem2_init)
	Wy = return_buffer(WEIGHTS[gradient_layer][gradient_arg])
	weights_shape = Wy.shape; Wy = Wy.ravel(); Wy[i_ind] = y
	set_buffer(Wy.reshape(weights_shape), WEIGHTS[gradient_layer][gradient_arg])
	
	for frame in range(N_FRAMES):
		set_buffer(x1t[frame], WEIGHTS[F1_IND][1])  # inputs
		set_buffer(x2t[frame], WEIGHTS[R_T_IND][1])  # inputs
		set_buffer(x3t[frame], WEIGHTS[R_T_F_IND][1])  # inputs
		OUTPUT = forward_network(LAYERS, WEIGHTS, OUTPUT, OUTPUT_PREV)
		OUTPUT_PREV = copy_list(OUTPUT, OUTPUT_PREV)
	
	z = return_buffer(OUTPUT[-1])[0]
	free_list(OUTPUT)
	free_list(OUTPUT_PREV)
	return z

def g(y):
	OUTPUT = None; LOCAL_DERIVS = None; WEIGHT_DERIVS = None
	OUTPUT_PREV = [None] * len(LAYERS); MEM_WEIGHT_DERIVS = None
	MEM2_WEIGHT_DERIVS = None
	OUTPUT_PREV[MEM_IND] = init_buffer(mem_init)
	#OUTPUT_PREV[MEM2_IND] = init_buffer(mem2_init)
	Wy = return_buffer(WEIGHTS[gradient_layer][gradient_arg])
	weights_shape = Wy.shape; Wy = Wy.ravel(); Wy[i_ind] = y
	set_buffer(Wy.reshape(weights_shape), WEIGHTS[gradient_layer][gradient_arg])
	
	PARTIALS_PREV = init_partials(LAYERS)
	for frame in range(N_FRAMES):
		set_buffer(x1t[frame], WEIGHTS[F1_IND][1])  # inputs
		set_buffer(x2t[frame], WEIGHTS[R_T_IND][1])  # inputs
		set_buffer(x3t[frame], WEIGHTS[R_T_F_IND][1])  # inputs
		OUTPUT = forward_network(LAYERS, WEIGHTS, OUTPUT, OUTPUT_PREV)
		LOCAL_DERIVS = local_derivs(LAYERS, WEIGHTS, OUTPUT, OUTPUT_PREV, LOCAL_DERIVS)
		WEIGHT_DERIVS = reverse_network(DERIV_TOP, len(LAYERS)-1, LAYERS, LOCAL_DERIVS, PARTIALS_PREV, WEIGHT_DERIVS)
		
		# update partials_prev
		MEM_WEIGHT_DERIVS = reverse_network(None, MEM_IND, LAYERS, LOCAL_DERIVS, PARTIALS_PREV, MEM_WEIGHT_DERIVS, keep_dims=True)
		#MEM2_WEIGHT_DERIVS = reverse_network(None, MEM2_IND, LAYERS, LOCAL_DERIVS, PARTIALS_PREV, MEM2_WEIGHT_DERIVS, keep_dims=True)
		PARTIALS_PREV = copy_partials(MEM_IND, LAYERS, PARTIALS_PREV, MEM_WEIGHT_DERIVS)
		#PARTIALS_PREV = copy_partials(MEM2_IND, LAYERS, PARTIALS_PREV, MEM2_WEIGHT_DERIVS)
		OUTPUT_PREV = copy_list(OUTPUT, OUTPUT_PREV)
		
	z = return_buffer(WEIGHT_DERIVS[gradient_layer][gradient_arg]).ravel()[i_ind]
	
	free_partials(PARTIALS_PREV)
	free_list(MEM_WEIGHT_DERIVS)
	free_list(LOCAL_DERIVS)
	free_list(OUTPUT)
	free_list(WEIGHT_DERIVS)
	free_list(OUTPUT_PREV)
	return z

assert isinstance(LAYERS[gradient_layer]['in_source'][gradient_arg], int) != True, 'derivative of intermediate layer'
ref = return_buffer(WEIGHTS[gradient_layer][gradient_arg])
np.random.seed(np.int64(time.time()))
eps = np.sqrt(np.finfo(np.float).eps)*5e3

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
