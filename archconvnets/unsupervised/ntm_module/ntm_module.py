import _ntm_module
import numpy as np

# a += b * scalar
def point_wise_add(a_ind, b_ind, scalar=1, gpu_ind=0):
	assert isinstance(gpu_ind,int)
	assert isinstance(b_ind,int)
	assert isinstance(a_ind,int)
	
	return _ntm_module.point_wise_add(a_ind, b_ind, np.single(scalar), gpu_ind)

def mult_partials(da_db_ind, da_db_shape, db_dc_ind, db_dc_shape, b_ndim, out_buffer_ind, gpu_ind=0):
	assert isinstance(gpu_ind,int)
	assert isinstance(da_db_ind,int)
	assert isinstance(db_dc_ind,int)
	assert isinstance(out_buffer_ind,int)
	assert isinstance(da_db_shape,tuple)
	assert isinstance(db_dc_shape, tuple)
	assert isinstance(b_ndim,int)
	assert b_ndim > 0
	
	da_db_shape = np.asarray(da_db_shape)
	db_dc_shape = np.asarray(db_dc_shape)
	
	a_ndim = len(da_db_shape) - b_ndim
	c_ndim = len(db_dc_shape) - b_ndim
	
	assert a_ndim >= 0
	assert c_ndim > 0
	
	da_db_shape = (np.prod(da_db_shape[:a_ndim]), np.prod(da_db_shape[a_ndim:]))
	db_dc_shape = (np.prod(db_dc_shape[:b_ndim]), np.prod(db_dc_shape[b_ndim:]))
	
	return _ntm_module.dot(da_db_ind, da_db_shape, db_dc_ind, db_dc_shape, out_buffer_ind, gpu_ind)

# multiply list of partials
'''def mult_partials_chain(DA_DB_IND, B_NDIM):
	DA_DX_IND = DA_DB_IND[0]
	for x in range(1, len(DA_DB_IND)):
		DA_DX_IND = mult_partials(DA_DX_IND, DA_DB_IND[x], B_NDIM[x-1])
	return DA_DX_IND'''

# mult_partials for all layers in DB_DC (a list of indices)
def mult_partials__layers(da_db_ind, da_db_ind_shape, DB_DC_IND, DB_DC_SHAPE, b_ndim, \
						OUT_BUFFER_IND, DB_DC_INIT_IND=None, gpu_ind=0):
	assert len(DB_DC_IND) == len(DB_DC_SHAPE)
	
	if DB_DC_INIT_IND != None:
		assert len(DB_DC_IND) == len(DB_DC_INIT_IND)
	
	for l in range(len(DB_DC_IND)):
		mult_partials(da_db_ind, da_db_ind_shape, DB_DC_IND[l], DB_DC_SHAPE[l], b_ndim, \
						OUT_BUFFER_IND[l], gpu_ind)
		
		if DB_DC_INIT_IND != None:
			point_wise_add(OUT_BUFFER_IND[l], DB_DC_INIT[l], gpu_ind=gpu_ind)

def shift_w_dw_interp(shift_out_ind, w_interp_shape, out_buffer_ind, gpu_ind=0):
	assert isinstance(gpu_ind,int)
	assert isinstance(out_buffer_ind,int)
	assert isinstance(shift_out_ind,int)
	assert isinstance(w_interp_shape,tuple)
	assert len(w_interp_shape) == 2
	
	return _ntm_module.shift_w_dw_interp(shift_out_ind, w_interp_shape, out_buffer_ind, gpu_ind)

def shift_w_dshift_out(w_interp_ind, w_interp_shape, out_buffer_ind, gpu_ind=0):
	assert isinstance(gpu_ind,int)
	assert isinstance(out_buffer_ind,int)
	assert isinstance(w_interp_ind,int)
	assert isinstance(w_interp_shape,tuple)
	assert len(w_interp_shape) == 2
	
	return _ntm_module.shift_w_dshift_out(w_interp_ind, w_interp_shape, out_buffer_ind, gpu_ind)


def interpolate_dinterp_gate_out(o_content_ind, o_content_shape, o_prev_ind, out_buffer_ind, gpu_ind=0):
	assert isinstance(gpu_ind,int)
	assert isinstance(out_buffer_ind,int)
	assert isinstance(o_prev_ind,int)
	assert isinstance(o_content_shape,tuple)
	assert len(o_content_shape) == 2
	
	return _ntm_module.interpolate_dinterp_gate_out(o_content_ind, o_content_shape, o_prev_ind, out_buffer_ind, gpu_ind)

def interpolate_do_content(interp_gate_out_ind, o_prev_shape, out_buffer_ind, gpu_ind=0):
	assert isinstance(interp_gate_out_ind,int)
	assert isinstance(gpu_ind,int)
	assert isinstance(out_buffer_ind,int)
	assert isinstance(o_prev_shape,tuple)
	assert len(o_prev_shape) == 2
	
	return _ntm_module.interpolate_do_content(interp_gate_out_ind, o_prev_shape, out_buffer_ind, gpu_ind)


def interpolate_do_prev(interp_gate_out_ind, o_prev_shape, out_buffer_ind, gpu_ind=0):
	assert isinstance(interp_gate_out_ind,int)
	assert isinstance(gpu_ind,int)
	assert isinstance(out_buffer_ind,int)
	assert isinstance(o_prev_shape,tuple)
	assert len(o_prev_shape) == 2
	
	return _ntm_module.interpolate_do_prev(interp_gate_out_ind, o_prev_shape, out_buffer_ind, gpu_ind)

def linear_F_dx(F_ind, x_shape, F_shape, out_buffer_ind, gpu_ind=0):
	assert isinstance(F_ind,int)
	assert isinstance(gpu_ind,int)
	assert isinstance(out_buffer_ind,int)
	assert isinstance(x_shape,tuple)
	assert isinstance(F_shape,tuple)
	assert len(F_shape) == len(x_shape) == 2
	assert F_shape[1] == x_shape[0]
	
	return _ntm_module.linear_F_dx(F_ind, x_shape, F_shape, out_buffer_ind, gpu_ind)

def linear_F_dF(x_ind, x_shape, F_shape, out_buffer_ind, gpu_ind=0):
	assert isinstance(x_ind,int)
	assert isinstance(gpu_ind,int)
	assert isinstance(out_buffer_ind,int)
	assert isinstance(x_shape,tuple)
	assert isinstance(F_shape,tuple)
	assert len(F_shape) == len(x_shape) == 2
	assert F_shape[1] == x_shape[0]
	
	return _ntm_module.linear_F_dF(x_ind, x_shape, F_shape, out_buffer_ind, gpu_ind)

def relu_dlayer_in(layer_in_ind, layer_in_shape, out_buffer_ind, thresh=0, gpu_ind=0):
	assert isinstance(layer_in_ind,int)
	assert isinstance(gpu_ind,int)
	assert isinstance(thresh,int)
	assert isinstance(out_buffer_ind,int)
	assert isinstance(layer_in_shape,tuple)
	assert len(layer_in_shape) == 2
	
	return _ntm_module.relu_dlayer_in(layer_in_ind, layer_in_shape, out_buffer_ind, thresh, gpu_ind)

def sigmoid_dlayer_in(layer_out_ind, layer_out_shape, out_buffer_ind, gpu_ind=0):
	assert isinstance(layer_out_ind,int)
	assert isinstance(gpu_ind,int)
	assert isinstance(out_buffer_ind,int)
	assert isinstance(layer_out_shape,tuple)
	assert len(layer_out_shape) == 2
	
	return _ntm_module.sigmoid_dlayer_in(layer_out_ind, layer_out_shape, out_buffer_ind, gpu_ind)

def focus_key_dkeys(beta_out_ind, keys_shape, out_buffer_ind, gpu_ind=0):
	assert isinstance(beta_out_ind,int)
	assert isinstance(gpu_ind,int)
	assert isinstance(out_buffer_ind,int)
	assert isinstance(keys_shape,tuple)
	assert len(keys_shape) == 2
	
	return _ntm_module.focus_key_dkeys(beta_out_ind, keys_shape, out_buffer_ind, gpu_ind)

def focus_key_dbeta_out(keys_ind, keys_shape, out_buffer_ind, gpu_ind=0):
	assert isinstance(keys_ind,int)
	assert isinstance(gpu_ind,int)
	assert isinstance(out_buffer_ind,int)
	assert isinstance(keys_shape,tuple)
	assert len(keys_shape) == 2

	return _ntm_module.focus_key_dbeta_out(keys_ind, keys_shape, out_buffer_ind, gpu_ind)

def sharpen_dgamma(w_ind, w_shape, gamma_ind, gamma_shape, out_ind, gpu_ind=0):
	assert isinstance(gpu_ind,int)
	assert isinstance(w_ind,int)
	assert isinstance(gamma_ind,int)
	assert isinstance(out_ind,int)
	assert isinstance(w_shape,tuple)
	assert isinstance(gamma_shape,tuple)
	assert len(gamma_shape) == len(w_shape) == 2
	assert gamma_shape[0] == w_shape[0]

	return _ntm_module.sharpen_dgamma(w_ind, w_shape, gamma_ind, gamma_shape, out_ind, gpu_ind)

def sharpen_dw(w_ind, w_shape, gamma_ind, gamma_shape, out_ind, gpu_ind=0):
	assert isinstance(gpu_ind,int)
	assert isinstance(w_ind,int)
	assert isinstance(gamma_ind,int)
	assert isinstance(out_ind,int)
	assert isinstance(w_shape,tuple)
	assert isinstance(gamma_shape,tuple)
	assert len(gamma_shape) == len(w_shape) == 2
	assert gamma_shape[0] == w_shape[0]
	
	return _ntm_module.sharpen_dw(w_ind, w_shape, gamma_ind, gamma_shape, out_ind, gpu_ind)

def sharpen_dgamma_cpu(w, gamma, warn=True):
	assert w.dtype == np.dtype('float32')
	assert gamma.dtype == np.dtype('float32')
	assert w.ndim == gamma.ndim == 2
	assert gamma.shape[0] == w.shape[0]
	assert gamma.shape[1] == 1

	if not w.flags.contiguous and warn:
		print 'warning: input to sharpen_dw_cpu not C-contiguous (w)'
		w = np.ascontiguousarray(w)
	
	if not gamma.flags.contiguous and warn:
		print 'warning: input to sharpen_dw_cpu not C-contiguous (gamma)'
		gamma = np.ascontiguousarray(gamma)
	
	return _ntm_module.sharpen_dgamma_cpu(w, gamma)

def sharpen_dw_cpu(w, gamma, warn=True):
	assert w.dtype == np.dtype('float32')
	assert gamma.dtype == np.dtype('float32')
	assert w.ndim == gamma.ndim == 2
	assert gamma.shape[0] == w.shape[0]
	assert gamma.shape[1] == 1

	if not w.flags.contiguous and warn:
		print 'warning: input to sharpen_dw_cpu not C-contiguous (w)'
		w = np.ascontiguousarray(w)
	
	if not gamma.flags.contiguous and warn:
		print 'warning: input to sharpen_dw_cpu not C-contiguous (gamma)'
		gamma = np.ascontiguousarray(gamma)

	return _ntm_module.sharpen_dw_cpu(w, gamma)

def softmax_dlayer_in(layer_out, layer_out_shape, out_ind, gpu_ind=0):
	assert isinstance(gpu_ind,int)
	assert isinstance(out_ind,int)
	assert isinstance(layer_out,int)
	assert isinstance(layer_out_shape,tuple)
	assert len(layer_out_shape) == 2
	
	return _ntm_module.softmax_dlayer_in(layer_out, layer_out_shape, out_ind, gpu_ind)

def softmax_dlayer_in_cpu(layer_out, warn=True):
	assert layer_out.dtype == np.dtype('float32')
	assert layer_out.ndim == 2
	
	if not layer_out.flags.contiguous and warn:
		print 'warning: input to softmax_dlayer_in_cpu not C-contiguous'
		layer_out = np.ascontiguousarray(layer_out)
		
	return _ntm_module.softmax_dlayer_in_cpu(layer_out)

def cosine_sim_expand_dmem(keys_ind, keys_shape, mem_ind, mem_shape, out_ind, gpu_ind=0):
	assert isinstance(gpu_ind,int)
	assert isinstance(keys_ind,int)
	assert isinstance(mem_ind,int)
	assert isinstance(out_ind,int)
	assert isinstance(keys_shape, tuple)
	assert isinstance(mem_shape, tuple)
	assert len(keys_shape) == len(mem_shape) == 2
	assert keys_ind != mem_ind
	assert keys_shape[1] == mem_shape[1]

	return _ntm_module.cosine_sim_expand_dmem(keys_ind, keys_shape, mem_ind, mem_shape, out_ind, gpu_ind)

def cosine_sim_expand_dkeys(keys_ind, keys_shape, mem_ind, mem_shape, out_ind, gpu_ind=0):
	assert isinstance(gpu_ind,int)
	assert isinstance(keys_ind,int)
	assert isinstance(mem_ind,int)
	assert isinstance(out_ind,int)
	assert isinstance(keys_shape, tuple)
	assert isinstance(mem_shape, tuple)
	assert len(keys_shape) == len(mem_shape) == 2
	assert keys_ind != mem_ind
	assert keys_shape[1] == mem_shape[1]

	return _ntm_module.cosine_sim_expand_dkeys(keys_ind, keys_shape, mem_ind, mem_shape, out_ind, gpu_ind)

def cosine_sim_expand_dmem_cpu(keys, mem, warn=True):
	assert keys.dtype == np.dtype('float32')
	assert mem.dtype == np.dtype('float32')
	assert keys.ndim == mem.ndim == 2
	assert keys.shape[1] == mem.shape[1]
	
	if not keys.flags.contiguous and warn:
		print 'warning: input to cosine_sim_expand_dkeys_cpu not C-contiguous (keys)'
		keys = np.ascontiguousarray(keys)
		
	if not mem.flags.contiguous and warn:
		print 'warning: input to cosine_sim_expand_dkeys_cpu not C-contiguous (mem)'
		mem = np.ascontiguousarray(mem)

	return _ntm_module.cosine_sim_expand_dmem_cpu(keys, mem)
	
def cosine_sim_expand_dkeys_cpu(keys, mem, warn=True):
	assert keys.dtype == np.dtype('float32')
	assert mem.dtype == np.dtype('float32')
	assert keys.ndim == mem.ndim == 2
	assert keys.shape[1] == mem.shape[1]
	
	if not keys.flags.contiguous and warn:
		print 'warning: input to cosine_sim_expand_dkeys_cpu not C-contiguous (keys)'
		keys = np.ascontiguousarray(keys)
		
	if not mem.flags.contiguous and warn:
		print 'warning: input to cosine_sim_expand_dkeys_cpu not C-contiguous (mem)'
		mem = np.ascontiguousarray(mem)

	return _ntm_module.cosine_sim_expand_dkeys_cpu(keys, mem)

def sync(gpu_ind=0):
	assert isinstance(gpu_ind,int)
	return _ntm_module.sync(gpu_ind)

def set_buffer(data, buffer_ind, gpu_ind=0, warn=True):
	assert data.dtype == np.dtype('float32')
	assert isinstance(gpu_ind,int)
	assert isinstance(buffer_ind,int)
	
	if not data.flags.contiguous and warn:
		print 'warning: input to set_buffer not C-contiguous (data)'
		data = np.ascontiguousarray(data)

	return _ntm_module.set_buffer(data, buffer_ind, gpu_ind)

def free_buffer(buffer_ind, gpu_ind=0):
	assert isinstance(gpu_ind,int)
	assert isinstance(buffer_ind,int)
	return _ntm_module.free_buffer(buffer_ind, gpu_ind)

def return_buffer(buffer_ind, gpu_ind=0):
	assert isinstance(gpu_ind,int)
	assert isinstance(buffer_ind,int)

	return _ntm_module.return_buffer(buffer_ind, gpu_ind)
	
def dot(buffer_ind1, buffer_shape1, buffer_ind2, buffer_shape2, out_buffer_ind, gpu_ind=0):
	assert isinstance(gpu_ind,int)
	assert isinstance(buffer_ind1,int)
	assert isinstance(buffer_ind2,int)
	assert isinstance(out_buffer_ind,int)
	assert isinstance(buffer_shape1, tuple)
	assert isinstance(buffer_shape2, tuple)
	assert len(buffer_shape1) == len(buffer_shape2) == 2
	assert buffer_shape1[1] == buffer_shape2[0]
	assert out_buffer_ind != buffer_ind1
	assert out_buffer_ind != buffer_ind2
	
	return _ntm_module.dot(buffer_ind1, buffer_shape1, buffer_ind2, buffer_shape2, out_buffer_ind, gpu_ind)
