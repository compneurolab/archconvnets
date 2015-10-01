import numpy as np
import copy

n_shifts = 3
C = 4 # number of controllers
M = 5 # mem slots
mem_length = 8
n_in = 3
n_head_in = 9
n1_under = 10
n2_under = 11

SCALE = 1 # scale of weight initializations
N_FRAMES = 4
SCALE_UNDER = .425

## indices
L1_UNDER = 0; L2_UNDER = 1; F_UNDER = 2

# read/write heads:
N_READ_IN_LAYERS = 5 # layers directly operating on read head inputs
N_WRITE_IN_LAYERS = N_READ_IN_LAYERS + 2 # plus the add/erase layers
IN_GATE = 0; SHIFT = 1; KEY = 2; BETA = 3; GAMMA = 4; 
ERASE = 5; ADD = 6

# intermediate layers operating on the outputs of layers processing inputs (they don't have weights)
N_HEAD_INT_LAYERS = 7 
CONTENT_FOCUSED = N_WRITE_IN_LAYERS
CONTENT = N_WRITE_IN_LAYERS + 1
CONTENT_SM = N_WRITE_IN_LAYERS + 2
IN = N_WRITE_IN_LAYERS + 3
SHIFTED = N_WRITE_IN_LAYERS + 4
SHARPENED = N_WRITE_IN_LAYERS + 5
F = N_WRITE_IN_LAYERS + 6

N_TOTAL_HEAD_LAYERS = N_WRITE_IN_LAYERS +  N_HEAD_INT_LAYERS

## inputs/targets
x = np.random.normal(size=(N_FRAMES+1, n_in,1)) * SCALE
t = np.random.normal(size=(C,mem_length))

## under weights:
w1 = np.random.normal(size=(n1_under, n_in)) * SCALE_UNDER
w2 = np.random.normal(size=(n2_under, n1_under)) * SCALE_UNDER
w3 = np.random.normal(size=(n_head_in, n2_under)) * SCALE_UNDER

b1 = np.random.normal(size=(n1_under, 1)) * SCALE_UNDER
b2 = np.random.normal(size=(n2_under, 1)) * SCALE_UNDER
b3 = np.random.normal(size=(n_head_in, 1)) * SCALE_UNDER

WUNDER = [w1, w2, w3]
BUNDER = [b1, b2, b3]
OUNDER_PREVi = np.zeros((n_head_in, 1))

## head weights:
OR_PREVi = [None] * N_TOTAL_HEAD_LAYERS; OW_PREVi = copy.deepcopy(OR_PREVi) # prev states
OR_SHAPES = copy.deepcopy(OR_PREVi); OW_SHAPES = copy.deepcopy(OR_PREVi) # prev state shapes
WR = [None] * N_READ_IN_LAYERS; WW = [None] * N_WRITE_IN_LAYERS # weights
BR = [None] * N_READ_IN_LAYERS; BW = [None] * N_WRITE_IN_LAYERS # weights
WR_SHAPES = copy.deepcopy(WR); WW_SHAPES = copy.deepcopy(WW) # weight shapes

# in
WR_SHAPES[IN_GATE] = (C, n_head_in)
WW_SHAPES[IN_GATE] = (C, n_head_in)

OR_SHAPES[IN_GATE] = (C, 1)
OW_SHAPES[IN_GATE] = (C, 1)

# shift
WR_SHAPES[SHIFT] = (C, n_shifts, n_head_in)
WW_SHAPES[SHIFT] = (C, n_shifts, n_head_in)

OR_SHAPES[SHIFT] = (C, n_shifts)
OW_SHAPES[SHIFT] = (C, n_shifts)

# key
WR_SHAPES[KEY] = (C, mem_length, n_head_in)
WW_SHAPES[KEY] = (C, mem_length, n_head_in)

OR_SHAPES[KEY] = (C, mem_length)
OW_SHAPES[KEY] = (C, mem_length)

# beta
WR_SHAPES[BETA] = (C, n_head_in)
WW_SHAPES[BETA] = (C, n_head_in)

OR_SHAPES[BETA] = (C, 1)
OW_SHAPES[BETA] = (C, 1)

# sharpen
WR_SHAPES[GAMMA] = (C, n_head_in)
WW_SHAPES[GAMMA] = (C, n_head_in)

OR_SHAPES[GAMMA] = (C, 1)
OW_SHAPES[GAMMA] = (C, 1)

# erase
WW_SHAPES[ERASE] = (C, mem_length, n_head_in)
OW_SHAPES[ERASE] = (C, mem_length)

# add
WW_SHAPES[ADD] = (C, mem_length, n_head_in)
OW_SHAPES[ADD] = (C, mem_length)

# init weights
for layer in range(len(WR_SHAPES)):
	WR[layer] = np.random.normal(size = WR_SHAPES[layer]) * SCALE
	WW[layer] = np.random.normal(size = WW_SHAPES[layer]) * SCALE
	
	BR[layer] = np.random.normal(size = OR_SHAPES[layer]) * SCALE
	BW[layer] = np.random.normal(size = OW_SHAPES[layer]) * SCALE
	
	OR_PREVi[layer] = np.zeros(OR_SHAPES[layer])
	OW_PREVi[layer] = np.zeros(OW_SHAPES[layer])

WW[ADD] = np.random.normal(size = WW_SHAPES[ADD])
WW[ERASE] = np.random.normal(size = WW_SHAPES[ERASE])

BW[ADD] = np.random.normal(size = OW_SHAPES[ADD])
BW[ERASE] = np.random.normal(size = OW_SHAPES[ERASE])

OW_PREVi[ADD] = np.zeros(WW_SHAPES[ADD])
OW_PREVi[ERASE] = np.zeros(WW_SHAPES[ERASE])
	
###

OR_PREVi[F] = np.abs(np.random.normal(size=(C,M)))

OW_PREVi[IN] = np.zeros_like(OR_PREVi[F])
OW_PREVi[F] = np.abs(np.random.normal(size=(C,M)))

OW_PREVi[SHIFTED] = np.zeros_like(OW_PREVi[F])
OW_PREVi[SHARPENED] = np.zeros_like(OW_PREVi[F])

OW_PREV_PREVi = copy.deepcopy(OW_PREVi)
OW_PREV_PREVi[F] = np.zeros_like(OW_PREV_PREVi[F])

###

DWR = [None] * len(WR); DBR = [None] * len(WR)
DWW = [None] * len(WW); DBW = [None] * len(WW)

## address and mem partials:
DOR_DWUNDERi = [None] * len(WUNDER)
DOR_DBUNDERi = [None] * len(BUNDER)
DOR_DWRi = [None] * len(WR); DOR_DBRi = [None] * len(WR)
DOR_DWWi = [None] * len(WW); DOR_DBWi = [None] * len(WW)

DMEM_PREV_DWWi = [None] * len(WW); DMEM_PREV_DBWi = [None] * len(WW)
DMEM_PREV_DWUNDERi = [None] * len(WUNDER)
DMEM_PREV_DBUNDERi = [None] * len(BUNDER)

for layer in range(len(WR)):
	DOR_DWRi[layer] = np.zeros(np.concatenate(((C, M), WR_SHAPES[layer])))
	DOR_DBRi[layer] = np.zeros(np.concatenate(((C, M), OR_SHAPES[layer])))

for layer in range(len(WUNDER)):
	DOR_DWUNDERi[layer] = np.zeros(np.concatenate(((C, M), WUNDER[layer].shape)))
	DOR_DBUNDERi[layer] = np.zeros(np.concatenate(((C, M), BUNDER[layer].shape)))
	DMEM_PREV_DWUNDERi[layer] = np.zeros(np.concatenate(((M, mem_length), WUNDER[layer].shape)))
	DMEM_PREV_DBUNDERi[layer] = np.zeros(np.concatenate(((M, mem_length), BUNDER[layer].shape)))

for layer in range(len(WW)):
	DOR_DWWi[layer] = np.zeros(np.concatenate(((C, M), WW_SHAPES[layer])))
	DOR_DBWi[layer] = np.zeros(np.concatenate(((C, M), OW_SHAPES[layer])))
	DMEM_PREV_DWWi[layer] = np.zeros(np.concatenate(((M, mem_length), WW_SHAPES[layer])))
	DMEM_PREV_DBWi[layer] = np.zeros(np.concatenate(((M, mem_length), OW_SHAPES[layer])))

DOW_DWWi = copy.deepcopy(DOR_DWWi)
DOW_DBWi = copy.deepcopy(DOR_DBWi)
DOW_DWUNDERi = copy.deepcopy(DOR_DWUNDERi)
DOW_DBUNDERi = copy.deepcopy(DOR_DBUNDERi)

## layer outputs/initial states:
mem_previ = np.random.normal(size=(M, mem_length))
