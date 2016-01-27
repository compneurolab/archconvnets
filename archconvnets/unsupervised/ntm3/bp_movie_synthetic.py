# todo: save script; cifar opt
import numpy as np
import time
import scipy.optimize
from ntm_core import *
from scipy.io import loadmat, savemat
from scipy.stats import zscore, pearsonr
from center_world import generate_latents

no_mem = True
no_mem = False

if no_mem:
	from architectures.model_architecture_movie32_no_mem import *
	INPUT_SCALE = 1e-5
	EPS = 1e-3
	save_name = 'ntm_movie_syntehtic_no_mem_%f_n_pred_%i' % (-EPS, N_FRAMES_PRED)
else:
	from architectures.model_architecture_movie32 import *
	INPUT_SCALE = 1e-5
	EPS = 1e-3
	save_name = 'ntm_movie_synthetic_%f_n_pred_%i' % (-EPS, N_FRAMES_PRED)

	
free_all_buffers()


################ init save vars

frame = 0; frame_local = 0; err = 0; corr = 0; movie_ind = 0

N_MOVIES = 427

EPOCH_LEN = 10
SAVE_FREQ = 50 #250 # instantaneous checkpoint
WRITE_FREQ = 50 # new checkpoint
FRAME_LAG = 100 #SAVE_FREQ
STOP_POINT = np.inf #SAVE_FREQ*15

target_buffer = np.zeros((SAVE_FREQ, N_FRAMES_PRED*N_IN),dtype='single')
output_buffer = np.zeros((SAVE_FREQ, N_FRAMES_PRED*N_IN),dtype='single')
err_log = []; corr_log = []

t_start = time.time()

################ init weights and inputs
LAYERS, WEIGHTS, MEM_INDS, PREV_VALS, print_names = init_model()

STACK_SUM_IND = find_layer(LAYERS, 'STACK_SUM5')
TARGET_IND = find_layer(LAYERS, 'ERR')
OUT_IND = find_layer(LAYERS, 'ERR')
F1_IND = 0

OUTPUT = None; WEIGHT_DERIVS = None
MEM_DERIVS = [None]*len(MEM_INDS); WEIGHT_DERIVS_RMS = None

OUTPUT_PREV = init_output_prev(LAYERS, MEM_INDS, PREV_VALS)
PARTIALS_PREV = init_partials(LAYERS, MEM_INDS)

WEIGHTS_F1_INIT = return_buffer(WEIGHTS[find_layer(LAYERS, 'F1')][0])

#####################
while True:
	# end of movie:
	if (frame % (1 + EPOCH_LEN)) == 0:
		#### new movie
		movie_name = '/home/darren/rotating_objs32/imgs' + str(movie_ind % N_MOVIES) + '.mat'
		targets = inputs = loadmat(movie_name)['imgs']
		
		#### reset state
		free_list(OUTPUT_PREV)
		free_partials(PARTIALS_PREV)
		
		OUTPUT_PREV = init_output_prev(LAYERS, MEM_INDS, PREV_VALS)
		PARTIALS_PREV = init_partials(LAYERS, MEM_INDS)
		
		frame_local = 0
		movie_ind += 1
	
	###### forward
	frame_target = targets[frame_local:frame_local+N_FRAMES_PRED].ravel()[:,np.newaxis]
	
	set_buffer(inputs[frame_local], WEIGHTS[F1_IND][1])  # inputs
	set_buffer(frame_target, WEIGHTS[TARGET_IND][1]) # target
	
	OUTPUT = forward_network(LAYERS, WEIGHTS, OUTPUT, OUTPUT_PREV)
	
	time_series_prediction = return_buffer(OUTPUT[STACK_SUM_IND]).ravel()
	
	current_err = return_buffer(OUTPUT[-1])
	err += current_err;
	corr += pearsonr(frame_target.ravel(), time_series_prediction)[0]

	output_buffer[frame % SAVE_FREQ] = copy.deepcopy(time_series_prediction)
	target_buffer[frame % SAVE_FREQ] = copy.deepcopy(frame_target.ravel())
	
	###### reverse
	WEIGHT_DERIVS = reverse_network(len(LAYERS)-1, LAYERS, WEIGHTS, OUTPUT, OUTPUT_PREV, PARTIALS_PREV, WEIGHT_DERIVS)
		
	# update partials_prev
	MEM_DERIVS = reverse_network(MEM_INDS, LAYERS, WEIGHTS, OUTPUT, OUTPUT_PREV, PARTIALS_PREV, MEM_DERIVS, keep_dims=True)
	PARTIALS_PREV = copy_partials(MEM_INDS, LAYERS, PARTIALS_PREV, MEM_DERIVS)
	
	OUTPUT_PREV = copy_list(OUTPUT, OUTPUT_PREV)
	
	# take step
	if frame < STOP_POINT and frame > SAVE_FREQ:
		WEIGHT_DERIVS_RMS = update_weights_rms(LAYERS, WEIGHTS, WEIGHT_DERIVS, WEIGHT_DERIVS_RMS, EPS, frame, FRAME_LAG)
		
		
	# print/save
	if frame % SAVE_FREQ == 0 and frame != 0:
		corr_log.append(corr / SAVE_FREQ); corr = 0
		err_log.append(err / SAVE_FREQ); err = 0
		
		print_state(LAYERS, WEIGHTS, WEIGHT_DERIVS, OUTPUT, EPS, err_log, frame, corr_log, t_start, save_name, print_names)
		save_conv_state(LAYERS, WEIGHTS, WEIGHTS_F1_INIT, save_name, output_buffer, target_buffer, EPS, err_log, corr_log, EPOCH_LEN)
		
		t_start = time.time()
		
	frame += 1
	frame_local += 1
	if frame == STOP_POINT:
		print 'stopping'


free_list_list(MEM_DERIVS)
free_partials(PARTIALS_PREV)
free_list(OUTPUT)
free_list(WEIGHT_DERIVS)
free_list(OUTPUT_PREV)
