import numpy as np
import archconvnets.unsupervised.ntm_module2._ntm_module2 as _ntm_module2
from archconvnets.unsupervised.ntm_module2.ntm_module2 import *
from archconvnets.unsupervised.ntm2.gpu_flag import *
from archconvnets.unsupervised.ntm2.ntm_core import *

def sharpen_test(args, OUT_BUFFER=None, gpu_ind=0):
	assert isinstance(gpu_ind,int)
	W, GAMMA = args
	check_buffer(W)
	check_buffer(GAMMA)
	assert len(GAMMA[1]) == len(W[1]) == 2
	assert GAMMA[1][0] == W[1][0]
	
	if OUT_BUFFER != None:
		check_buffer(OUT_BUFFER)
	else:
		OUT_BUFFER = init_buffer()
	
	_ntm_module2.sharpen(W[0], W[1], GAMMA[0], OUT_BUFFER[0], gpu_ind)
	
	####### CPU
	w = return_buffer(W,gpu_ind)
	gamma = return_buffer(GAMMA,gpu_ind)
	
	assert np.min(w) >= 0
	
	wg = w ** gamma
	z = wg / wg.sum(1)[:,np.newaxis]
		
	OUT_BUFFER[1] = copy.deepcopy(W[1])
	z2 = return_buffer(OUT_BUFFER)
	
	print np.isclose(z, z2).sum()/np.single(np.prod(z.shape))
		
	return OUT_BUFFER

############# sharpen across mem_slots separately for each controller
# w: [dim1, dim0]
# gamma: [dim1, 1]
def sharpen(args, OUT_BUFFER=None, gpu_ind=0):
	assert isinstance(gpu_ind,int)
	W, GAMMA = args
	check_buffer(W)
	check_buffer(GAMMA)
	assert len(GAMMA[1]) == len(W[1]) == 2
	assert GAMMA[1][0] == W[1][0]
	
	if OUT_BUFFER != None:
		check_buffer(OUT_BUFFER)
	else:
		OUT_BUFFER = init_buffer()
	
	if GPU:
		_ntm_module2.sharpen(W[0], W[1], GAMMA[0], OUT_BUFFER[0], gpu_ind)
	else:
		####### CPU
		w = return_buffer(W,gpu_ind)
		gamma = return_buffer(GAMMA,gpu_ind)
		
		assert np.min(w) >= 0
		
		wg = w ** gamma
		OUT_BUFFER = set_buffer(wg / wg.sum(1)[:,np.newaxis], OUT_BUFFER, gpu_ind)
		
	OUT_BUFFER[1] = copy.deepcopy(W[1])
		
	return OUT_BUFFER

def sharpen_dgamma(args, LAYER_OUT, OUT_BUFFER=None, gpu_ind=0):
	assert isinstance(gpu_ind,int)
	W, GAMMA = args
	check_buffer(W)
	check_buffer(GAMMA)
	assert len(GAMMA[1]) == len(W[1]) == 2
	assert GAMMA[1][0] == W[1][0]
	
	if OUT_BUFFER != None:
		check_buffer(OUT_BUFFER)
	else:
		OUT_BUFFER = init_buffer()
	
	if GPU:
		_ntm_module2.sharpen_dgamma(W[0], W[1], GAMMA[0], GAMMA[1], OUT_BUFFER[0], gpu_ind)
	else: 
		############ CPU
		w = return_buffer(W,gpu_ind)
		gamma = return_buffer(GAMMA,gpu_ind)
		
		n = w.shape[0]
		g = np.zeros(np.concatenate((w.shape, gamma.shape)),dtype='single')
		
		wg = w ** gamma
		ln_w_wg = np.log(w)*wg
		wg_sum = wg.sum(1)[:,np.newaxis]
		ln_w_wg_sum = ln_w_wg.sum(1)[:,np.newaxis]
		
		t = (ln_w_wg * wg_sum - wg * ln_w_wg_sum) / (wg_sum ** 2)
		
		g[range(n),:,range(n)] = t[:,:,np.newaxis]
		OUT_BUFFER = set_buffer(g, OUT_BUFFER, gpu_ind)
	
	OUT_BUFFER[1] = tuple(np.concatenate((W[1], GAMMA[1])))
	return OUT_BUFFER
	
def sharpen_dw(args, LAYER_OUT, OUT_BUFFER=None, gpu_ind=0):
	assert isinstance(gpu_ind,int)
	W, GAMMA = args
	check_buffer(W)
	check_buffer(GAMMA)
	assert len(GAMMA[1]) == len(W[1]) == 2
	assert GAMMA[1][0] == W[1][0]
	
	if OUT_BUFFER != None:
		check_buffer(OUT_BUFFER)
	else:
		OUT_BUFFER = init_buffer()
	
	if GPU:
		_ntm_module2.sharpen_dw(W[0], W[1], GAMMA[0], GAMMA[1], OUT_BUFFER[0], gpu_ind)
	else: 
		############ CPU
		w = return_buffer(W,gpu_ind)
		gamma = return_buffer(GAMMA,gpu_ind)
		
		n = w.shape[0]
		g = np.zeros(np.concatenate((w.shape, w.shape)),dtype='single')
		
		wg = w ** gamma
		wg_sum = wg.sum(1)[:,np.newaxis]
		wg_sum2 = wg_sum ** 2
		g_wgm1 = gamma * (w ** (gamma-1))
		
		t = (g_wgm1 / wg_sum2) * (wg_sum - wg)
		
		for i in range(w.shape[0]):
			g[i,:,i,:] = t[i]
		
		for j in range(w.shape[1]):
			for b in range(w.shape[1]):
				if b != j:
					g[range(n),j,range(n),b] = -g_wgm1[:,b] * wg[:,j] / np.squeeze(wg_sum2)
		OUT_BUFFER = set_buffer(g, OUT_BUFFER, gpu_ind)
	
	OUT_BUFFER[1] = tuple(np.concatenate((W[1], W[1])))
	return OUT_BUFFER

def add_sharpen_layer(LAYERS, name, source):
	assert isinstance(name, str)
	assert isinstance(source, list)
	assert len(source) == 2
	assert find_layer(LAYERS, name) is None, 'layer %s has already been added' % name
	
	in_shape = [None]*2
	
	source[0] = find_layer(LAYERS, source[0])
	assert source[0] is not None, 'could not find source layer 0'
	
	if isinstance(source[1],int) != True and source[1] != -1:
		source[1] = find_layer(LAYERS, source[1])
	
	in_shape[0] = LAYERS[source[0]]['out_shape']
	in_shape[1] = (in_shape[0][0], 1)
	
	LAYERS.append({ 'name': name, 'forward_F': sharpen, \
				'out_shape': LAYERS[source[0]]['out_shape'], \
				'in_shape': in_shape, \
				'in_source': source, \
				'deriv_F': [sharpen_dw, sharpen_dgamma] })
	
	check_network(LAYERS)
	return len(LAYERS)-1