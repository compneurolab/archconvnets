cudnnTensor4dDescriptor_t srcDescL3;
cudnnFilterDescriptor_t filterDescL3;
cudnnConvolutionDescriptor_t convDescL3;
cudnnTensor4dDescriptor_t destDescL3;

int n_channelsL3, filter_szL3, n_filtersL3, img_szL3, n_imgsL3;

float *srcDataL3 = NULL;
float *filterDataL3;
float *destDataL3;

int dimsL3[1];

//-------------------------------------
// conv_L3(): perform convolution of inputs.
// this function differs from conv() in that the initial call creates a GPU buffer and data structures that are re-used
// on subsequent calls (instead of re-allocing/freeing memory each call like conv(). therefore, all calls
// to this function should have filter[] and imgs[] be of the same dimensions. the buffer re-use results
// in about 40% speed-up relative to conv().


// inputs: np raveled arrays: filters [n_filters, n_channels, filter_sz, filter_sz], imgs [n_imgs, n_channels, img_sz, img_sz]
//				ints: n_channels, filter_sz, n_filters, img_sz, n_imgs
// returns: conv_out [n_imgs, n_filters, conv_out_sz, conv_out_sz]
static PyObject *conv_L3(PyObject *self, PyObject *args)  {
	PyArrayObject *filters_in, *imgs_in, *vecout;
	float *filters, *imgs, *cout;
	int i;
	int n_channels, filter_sz, n_filters, img_sz, n_imgs;
	
	if (!PyArg_ParseTuple(args, "O!O!iiiii", &PyArray_Type, &filters_in, &PyArray_Type, &imgs_in, &n_channels, &filter_sz, &n_filters, &img_sz, &n_imgs)) 
		return NULL;
	if (NULL == filters || NULL == imgs)  return NULL;
	
	filters = (float *) filters_in -> data;
	imgs = (float *) imgs_in -> data;
	
	int n_imgs_out;
	int n_filters_out;
	int conv_out_sz_x;
	int conv_out_sz_y;
	cudaError_t err;

	cudnnStatus_t status;

	if(srcDataL3 == NULL){
		printf("init L3\n");
		//---------------------------------------
		// Set decriptors
		//---------------------------------------
		status = cudnnSetTensor4dDescriptor(srcDescL3, CUDNN_TENSOR_NCHW, dataType, n_imgs, n_channels, img_sz, img_sz);  ERR_CHECK
		status = cudnnSetFilterDescriptor(filterDescL3, dataType, n_filters, n_channels, filter_sz, filter_sz);  ERR_CHECK
		status = cudnnSetConvolutionDescriptor(convDescL3, srcDesc, filterDesc, 0, 0, 1, 1, 1, 1, CUDNN_CONVOLUTION);  ERR_CHECK

		//---------------------------------------
		// Query output layout
		//---------------------------------------
		status = cudnnGetOutputTensor4dDim(convDescL3, CUDNN_CONVOLUTION_FWD, &n_imgs_out, &n_filters_out, &conv_out_sz_x, &conv_out_sz_y);    ERR_CHECK

		//--------------------------------------
		// Set and allocate output tensor descriptor
		//----------------------------------------
		status = cudnnSetTensor4dDescriptor(destDescL3, CUDNN_TENSOR_NCHW, dataType, n_imgs_out, n_filters_out, conv_out_sz_x, conv_out_sz_x); ERR_CHECK
		dimsL3[0] = n_imgs_out*n_filters_out*conv_out_sz_x*conv_out_sz_x;
		
		err = cudaMalloc((void**) &destDataL3, dimsL3[0] * DATA_TYPE_SZ); MALLOC_ERR_CHECK
		
		//--------------------------------------
		// allocate filter, image, alpha, and beta tensors
		//----------------------------------------
		err = cudaMalloc((void**) &srcDataL3, n_imgs*n_channels*img_sz*img_sz * DATA_TYPE_SZ); MALLOC_ERR_CHECK
		err = cudaMalloc((void**) &filterDataL3, n_filters*n_channels*filter_sz*filter_sz * DATA_TYPE_SZ); MALLOC_ERR_CHECK
		
		//----------------------------------------
		// save input dimensions for error checking on subsequent calls to conv()
		//---------------------------------------
		n_channelsL3 = n_channels;
		filter_szL3 = filter_sz;
		n_filtersL3 = n_filters;
		img_szL3 = img_sz;
		n_imgsL3 = n_imgs;
	}else{
		//-------------------------------------------
		// check to make sure inputs match the previously initialized buffer sizes
		//---------------------------------------------
		if(n_channelsL3 != n_channels || filter_szL3 != filter_sz || n_filtersL3 != n_filters || img_szL3 != img_sz || n_imgsL3 != n_imgs){
			printf("---------------------------\ninput dimensions [n_channels: %i, filter_sz: %i, n_filters: %i, img_sz: %i, n_imgs: %i] do not match the initial input dimensions on the first call to this function [n_channels: %i, filter_sz: %i, n_filters: %i, img_sz: %i, n_imgs: %i]. use conv() for general-purpose convolution.\n------------------\n", n_channels, filter_sz, n_filters, img_sz, n_imgs, n_channelsL3, filter_szL3, n_filtersL3, img_szL3, n_imgsL3);
			return NULL;
		}
	}
	
	
	
	/* Make a new double vector of same dimension */
	vecout=(PyArrayObject *) PyArray_FromDims(1, dimsL3, NPY_FLOAT);
	cout = (float *) vecout -> data;
	
	//--------------------------------------
	// set filter and image values
	//--------------------------------------
	err = cudaMemcpy(srcDataL3, imgs, n_imgs*n_channels*img_sz*img_sz * DATA_TYPE_SZ, cudaMemcpyHostToDevice);  MALLOC_ERR_CHECK
	err = cudaMemcpy(filterDataL3, filters, n_filters*n_channels*filter_sz*filter_sz * DATA_TYPE_SZ, cudaMemcpyHostToDevice);  MALLOC_ERR_CHECK

	//--------------------------------------
	// Convolution
	//--------------------------------------
	status = cudnnConvolutionForward(handle, srcDescL3, srcDataL3, filterDescL3, filterDataL3, convDescL3, destDescL3, destDataL3, CUDNN_RESULT_NO_ACCUMULATE);  ERR_CHECK

	//--------------------------------------
	// Get output data
	//------------------------------------------
	err = (cudaError_t)cudaMemcpy(cout, destDataL3, n_imgs_out*n_filters_out*conv_out_sz_x*conv_out_sz_x * DATA_TYPE_SZ, cudaMemcpyDeviceToHost);  MALLOC_ERR_CHECK

	return PyArray_Return(vecout);
}
