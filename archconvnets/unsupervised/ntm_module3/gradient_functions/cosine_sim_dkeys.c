#define GPU_KEYS gpu_buffers[gpu_ind][keys_ind]
#define GPU_MEM gpu_buffers[gpu_ind][mem_ind]

#define KEYS(I, A, B) keys[(I)*n_controllers*mem_length + (A)*mem_length + B]
#define MEM(I, A, B) mem[(I)*M*mem_length + (A)*mem_length + B]

#define MEM_SZ buffer_sz[gpu_ind][mem_ind]
#define KEYS_SZ buffer_sz[gpu_ind][keys_ind]

#define COSED_SZ (dim_above*n_imgs*n_controllers*mem_length*sizeof(DATA_TYPE))
	
__global__ void cosine_sim_dkeys_kernel(float * keys, float * mem, float * deriv_above,
			float * data_out, long n_controllers, long mem_length, long M, long n_imgs){
	int a = blockIdx.x / n_imgs;
	int img = blockIdx.x % n_imgs;
	int i = threadIdx.x / mem_length;
	int k = threadIdx.x % mem_length;
	
	float denom, keys_sq_sum = 0, cosed;
	
	for(int k_local = 0; k_local < mem_length; k_local++){
		keys_sq_sum += KEYS(img,i,k_local) * KEYS(img,i,k_local);
	}
	keys_sq_sum = sqrt(keys_sq_sum);
	
	unsigned ind = a*n_imgs*n_controllers*mem_length + img*n_controllers*mem_length + i*mem_length + k;
	data_out[ind] = 0; // a,img,i,k
	
	unsigned ind_temp = a*n_imgs*n_controllers*M + img*n_controllers*M + i*M;
	
	for(int j = 0; j < M; j++){
		float numer = 0, mem_sq_sum = 0;
		
		for(int k_local = 0; k_local < mem_length; k_local++){
			mem_sq_sum += MEM(img,j,k_local) * MEM(img,j,k_local);
			numer += KEYS(img,i,k_local) * MEM(img,j,k_local);
		}
		mem_sq_sum = sqrt(mem_sq_sum);
		
		denom = keys_sq_sum * mem_sq_sum;
		
		//COSED(i,j,k) = (MEM(j,k) - (mem_sq_sum * KEYS(i,k) * numer / (keys_sq_sum * denom))) / denom;
		cosed = (MEM(img,j,k) - (mem_sq_sum * KEYS(img,i,k) * numer / (keys_sq_sum * denom))) / denom;
		
		//data_out[ind] += cosed * deriv_above[a,img,i,j];
		data_out[ind] += cosed * deriv_above[ind_temp + j];
	}
}

/* keys: N_CONTROLLERS, M_LENGTH
 mem: N_MEM_SLOTS, M_LENGTH
 out: N_CONTROLLERS, N_MEM_SLOTS*/
 // deriv_above [a, n_imgs, n_controllers, M]
 // cosed [n_imgs, n_controllers, M, mem_length]
 // deriv_above * cosedm = [a, n_imgs, n_controllers, mem_length] (sum across M)


static PyObject *cosine_sim_dkeys(PyObject *self, PyObject *args){
	PyObject *keys_shape, *mem_shape;
	int keys_ind, mem_ind, out_buffer_ind, gpu_ind, deriv_above_ind, n_imgs, dim_above;
	cudaError_t err;
	
	if (!PyArg_ParseTuple(args, "iO!iO!iiiii", &keys_ind, &PyTuple_Type, &keys_shape, 
			&mem_ind, &PyTuple_Type, &mem_shape, &deriv_above_ind, &dim_above, &out_buffer_ind, 
			&n_imgs, &gpu_ind))
		return NULL;
	
	if(keys_ind >= N_BUFFERS || keys_ind < 0 || 
			out_buffer_ind >= N_BUFFERS || out_buffer_ind < 0 || 
			mem_ind >= N_BUFFERS || mem_ind < 0){
		printf("buffer index incorrect, set_buffers().\n");
		return NULL;
	}
	
	if(gpu_ind >= N_GPUS || gpu_ind < 0){
		printf("gpu index incorrect, set_buffers().\n");
		return NULL;
	}
	
	if(MEM_SZ == 0 || KEYS_SZ == 0){
		printf("buffer not initialized. use set_buffers()\n");
		return NULL;
	}
	
	int dim_offset = 0; // skip over img dimension
	if(n_imgs > 1)
		dim_offset ++;
	
	// get sizes
	long n_controllers = PyLong_AsLong(PyTuple_GetItem(keys_shape, dim_offset));
	long mem_length = PyLong_AsLong(PyTuple_GetItem(keys_shape, 1 + dim_offset));
	long M = PyLong_AsLong(PyTuple_GetItem(mem_shape, dim_offset));
	
	if(n_imgs*n_controllers*mem_length*sizeof(DATA_TYPE) != KEYS_SZ || n_imgs*M*mem_length*sizeof(DATA_TYPE) != MEM_SZ){
		printf("specified input sizes do not equal to stored gpu buffer. %s\n",__FILE__);
		return NULL;
	}
	
	//cudaSetDevice(gpu_ind); CHECK_CUDA_ERR
	
	if(OUT_BUFFER_SZ == 0){ // init output buffer
		err = cudaMalloc((void**) &GPU_BUFFER_OUT, COSED_SZ); MALLOC_ERR_CHECK
		
		OUT_BUFFER_SZ = COSED_SZ;
	}else if(COSED_SZ != OUT_BUFFER_SZ){ // does the output size match the buffer size?
		printf("output buffer size not allocated to correct size\n");
		return NULL;
	}
	
	// run kernel
	cosine_sim_dkeys_kernel <<< dim_above*n_imgs, n_controllers*mem_length >>> (GPU_KEYS, 
			GPU_MEM, gpu_buffers[gpu_ind][deriv_above_ind], GPU_BUFFER_OUT, n_controllers, mem_length, M, n_imgs);
	
	#ifdef TIMING_DEBUG
		err = cudaDeviceSynchronize(); CHECK_CUDA_ERR
	#endif
	
	//cudaSetDevice(0); CHECK_CUDA_ERR
	
	Py_INCREF(Py_None);
	return Py_None;
}
