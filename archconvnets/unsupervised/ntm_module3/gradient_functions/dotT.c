#define DATA_T_OUT_SZ (n_imgs*buffer1_dim2*buffer2_dim2*sizeof(DATA_TYPE))

static PyObject *dotT(PyObject *self, PyObject *args){
	cudaError_t err;
	int gpu_ind, buffer_ind1, buffer_ind2, out_buffer_ind;
	PyObject *buffer_shape1, *buffer_shape2;
	
	if (!PyArg_ParseTuple(args, "iO!iO!ii", &buffer_ind1, &PyTuple_Type, &buffer_shape1, &buffer_ind2, 
			&PyTuple_Type, &buffer_shape2, &out_buffer_ind, &gpu_ind)) 
		return NULL;
        
	if(buffer_ind1 >= N_BUFFERS || buffer_ind1 < 0 || 
			out_buffer_ind >= N_BUFFERS || out_buffer_ind < 0 || 
			buffer_ind2 >= N_BUFFERS || buffer_ind2 < 0){
		printf("buffer index incorrect, set_buffers().\n");
		return NULL;
	}
	
	if(gpu_ind >= N_GPUS || gpu_ind < 0){
		printf("gpu index incorrect, set_buffers().\n");
		return NULL;
	}
	
	// get sizes
	long n_imgs = PyLong_AsLong(PyTuple_GetItem(buffer_shape1, 0));
	long buffer1_dim1 = PyLong_AsLong(PyTuple_GetItem(buffer_shape1, 1));
	long buffer1_dim2 = PyLong_AsLong(PyTuple_GetItem(buffer_shape1, 2));
	
	long buffer2_dim1 = PyLong_AsLong(PyTuple_GetItem(buffer_shape2, 1));
	long buffer2_dim2 = PyLong_AsLong(PyTuple_GetItem(buffer_shape2, 2));
	
	if(buffer1_dim1 != buffer2_dim1){
		printf("inner dot product dimensions do not match %s, (%li, %li), (%li, %li)\n", __FILE__, buffer1_dim1, buffer1_dim2, buffer2_dim1, buffer2_dim2);
		return NULL;
	}
	
	if(n_imgs*buffer1_dim1*buffer1_dim2*sizeof(DATA_TYPE) != BUFFER_SZ1 || n_imgs*buffer2_dim1*buffer2_dim2*sizeof(DATA_TYPE) != BUFFER_SZ2){
		printf("specified input sizes do not equal to stored gpu buffer. %s\n", __FILE__);
		printf("%li %li %li %li", buffer1_dim1*buffer1_dim2*sizeof(DATA_TYPE), BUFFER_SZ1, buffer2_dim1*buffer2_dim2*sizeof(DATA_TYPE), BUFFER_SZ2);
		return NULL;
	}
	
	if(OUT_BUFFER_SZ == 0){ // init output buffer
		err = cudaMalloc((void**) &GPU_BUFFER_OUT, DATA_T_OUT_SZ); MALLOC_ERR_CHECK
		
		OUT_BUFFER_SZ = DATA_T_OUT_SZ;
	}else if(DATA_T_OUT_SZ != OUT_BUFFER_SZ){ // does the output size match the buffer size?
		printf("output buffer size not allocated to correct size %s\n", __FILE__);
		return NULL;
	}
	
	const float alpha = 1.0, beta = 0.0;
	
	for(int img = 0; img < n_imgs; img++){
		cublasStatus_t err_blas = cublasSgemm(handle_blas[gpu_ind], CUBLAS_OP_N, CUBLAS_OP_T, buffer2_dim2, buffer1_dim2, buffer1_dim1, &alpha,
			 GPU_BUFFER2 + img*buffer2_dim1*buffer2_dim2, buffer2_dim2, 
			 GPU_BUFFER1 + img*buffer1_dim1*buffer1_dim2, buffer1_dim2, &beta, 
			 GPU_BUFFER_OUT + img*buffer1_dim2*buffer2_dim2, buffer2_dim2);
		ERR_CHECK_BLAS
	}
	
	#ifdef TIMING_DEBUG
		err = cudaDeviceSynchronize(); CHECK_CUDA_ERR
	#endif
	
	Py_INCREF(Py_None);
	return Py_None;
}
