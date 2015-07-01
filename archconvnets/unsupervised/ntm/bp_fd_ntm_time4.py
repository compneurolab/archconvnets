#from archconvnets.unsupervised.cudnn_module.cudnn_module import *
import time
import numpy as np
from scipy.io import savemat, loadmat
import copy
from scipy.stats import zscore
import random
import scipy
from ntm_gradients import *

C = 4
M = 5
n1 = 6
n_in = 3

t = np.random.normal(size=(C,M))
o_previ = np.random.normal(size=(C,M))
g = np.random.normal(size=(C,1))

w2 = np.random.normal(size=(C,n1))
w1 = np.random.normal(size=(n1,n_in))

x = np.random.normal(size=(n_in,1))
x2 = np.random.normal(size=(n_in,1))
x3 = np.random.normal(size=(n_in,1))

do_dw2i = np.zeros((C,M,n1))

################# interpolate simplified
def interpolate_simp(w_prev, interp_gate_out):
	return w_prev * interp_gate_out

def interpolate_simp_dinterp_gate_out_partial(interp_gate_out, dprev):
	dprev = np.einsum(dprev, [0,1,2], interp_gate_out, [0], [0,1,2]) # g * do_dw
	return dprev

def f(y):
	w2[i_ind,j_ind] = y
	o_prev = copy.deepcopy(o_previ)
	
	###
	g1 = linear_F(w1,x)
	g2 = linear_F(w2,g1)
	o = interpolate_simp(o_prev, g2)
	
	'''o_prev = copy.deepcopy(o)
	
	###
	g1 = linear_F(w1,x2)
	g2 = linear_F(w2,g1)
	o = interpolate_simp(o_prev, g2)
	
	o_prev = copy.deepcopy(o)'''
	
	return ((o - t)**2).sum()


def g(y):
	w2[i_ind,j_ind] = y
	do_dw2 = copy.deepcopy(do_dw2i)
	o_prev = copy.deepcopy(o_previ)
	
	###
	g1 = linear_F(w1,x)
	g2 = linear_F(w2,g1)
	o = interpolate_simp(o_prev, g2)
	
	dg_dw2 = linear_dF(g1,1).T
	
	do_dw2 = np.einsum(do_dw2, [0,1,2], g2, [0,3], [0,1,2]) # g * do_dw
	do_dw2 += np.einsum(o_prev, [0,1], dg_dw2, [2,3], [0,1,2]) # x * o^(t-1)
	
	'''o_prev = copy.deepcopy(o)
	
	###
	g1 = linear_F(w1,x2)
	g2 = linear_F(w2,g1)
	o = interpolate_simp(o_prev, g2)
	
	dg_dw2 = linear_dF(g1,1).T
	
	do_dw2 = np.einsum(do_dw2, [0,1,2], g2, [0,3], [0,1,2]) # g * do_dw
	do_dw2 += np.einsum(o_prev, [0,1], dg_dw2, [2,3], [0,1,2]) # x * o^(t-1)
	
	o_prev = copy.deepcopy(o)
	
	###'''
	
	dw2 = np.einsum(2*(o - t), [0,1], do_dw2, [0,1,2], [0,2])
	
	return dw2[i_ind,j_ind]
	
	
np.random.seed(np.int64(time.time()))
eps = np.sqrt(np.finfo(np.float).eps)*1e0


N_SAMPLES = 25
ratios = np.zeros(N_SAMPLES)
for sample in range(N_SAMPLES):

	ref = w2
	i_ind = np.random.randint(ref.shape[0])
	j_ind = np.random.randint(ref.shape[1])
	y = -1e0*ref[i_ind,j_ind]; gt = g(y); gtx = scipy.optimize.approx_fprime(np.ones(1)*y, f, eps)
		
	if gtx == 0:
		ratios[sample] = 1
	else:
		ratios[sample] = gtx/gt
	print gt, gtx, ratios[sample]
	
print ratios.mean(), ratios.std()

