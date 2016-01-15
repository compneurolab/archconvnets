from ntm_core import *

def init_model():
	LAYERS = []

	N_CONTROLLERS = 16
	N_MEM_SLOTS = 6
	M_LENGTH = 8

	mem_shape = (N_MEM_SLOTS, M_LENGTH)

	U_F1_FILTER_SZ = 3
	
	U_F1 = 7
	U_F2 = 4
	U_F3 = 9
	
	A_F1 = 4
	A_F2 = 7
	HEAD_INPUT = 'F3'

	for init in [0,1]:
		# below
		add_conv_layer(LAYERS, 'F1', U_F1, U_F1_FILTER_SZ, source = -1, imgs_shape=(1,2,12,12), init=init)
		add_linear_F_bias_layer(LAYERS, 'F2', U_F2, init=init)
		add_sq_points_layer(LAYERS, 'SQ_ERR', init=init)
		add_sum_layer(LAYERS, 'SUM_ERR', init=init)

	check_network(LAYERS)
	
	################ init weights and inputs
	WEIGHTS = init_weights(LAYERS)
	MEM_INDS = []
	PREV_VALS = random_function_list(LAYERS, MEM_INDS)
	
	return LAYERS, WEIGHTS, MEM_INDS, PREV_VALS

