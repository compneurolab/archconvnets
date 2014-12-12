cimport numpy as npd
import numpy as np

''' filters: in_channels, filter_sz, filter_sz, n_filters
    imgs: in_channels, img_sz, img_sz, n_imgs
'''
def s31(npd.ndarray[npd.int_t, ndim=4] output_switches3_x, npd.ndarray[npd.int_t, ndim=4] output_switches3_y, npd.ndarray[npd.int_t, ndim=4] output_switches2_x, npd.ndarray[npd.int_t, ndim=4] output_switches2_y, npd.ndarray[npd.int_t, ndim=4] output_switches1_x, npd.ndarray[npd.int_t, ndim=4] output_switches1_y, int s1, int s2, int s3, npd.ndarray[npd.float64_t, ndim=2] Y, npd.ndarray[npd.float64_t, ndim=4] imgs, int N_C): 
	cdef int cat
	cdef int N_IMGS = imgs.shape[3]
	cdef int max_output_sz3 = output_switches3_x.shape[1]
	cdef int n3 = output_switches3_x.shape[0]
	cdef int n2 = output_switches2_x.shape[0]
	cdef int n1 = output_switches1_x.shape[0]
	cdef int img
	cdef int channel
	cdef int f1
	cdef int a1_x
	cdef int a1_y
	cdef int a3_y
	cdef int a3_x
	cdef int f3
	cdef int f2
	cdef int z1
	cdef int z2
	cdef int a2_x
	cdef int a2_y
	cdef int a3_x_global
	cdef int a3_y_global
	cdef int a2_x_global
	cdef int a2_y_global
	cdef int a1_x_global
	cdef int a1_y_global	
	cdef float temp_F_prod_all
	cdef npd.ndarray[npd.int_t, ndim=4] output_switches3_xt
	cdef npd.ndarray[npd.int_t, ndim=4] output_switches3_yt
	cdef  npd.ndarray[npd.float64_t, ndim=11] sigma31 = np.zeros((N_C, 3, n1, s1, s1, n2, s2, s2, n3, s3, s3))
		
	for a3_x in range(s3):
		output_switches3_xt = output_switches3_x + a3_x
		for a3_y in range(s3):
			output_switches3_yt = output_switches3_y + a3_y
			print a3_x, a3_y
			for f1 in range(n1):
				for f3 in range(n3):
					for f2 in range(n2):
						for a2_x in range(s2):
							for a2_y in range(s2):
								for z1 in range(max_output_sz3):
									for z2 in range(max_output_sz3):
										for img in range(N_IMGS):
											cat = np.nonzero(Y[:,img])[0][0]
											# pool3 -> conv3
											a3_x_global = output_switches3_xt[f3, z1, z2, img]
											a3_y_global = output_switches3_yt[f3, z1, z2, img]
											
											# pool2 -> conv2
											a2_x_global = output_switches2_x[f2, a3_x_global, a3_y_global, img] + a2_x
											a2_y_global = output_switches2_y[f2, a3_x_global, a3_y_global, img] + a2_y
											
											for a1_x in range(s1):
												# pool1 -> conv1
												a1_x_global = output_switches1_x[f1, a2_x_global, a2_y_global, img] + a1_x
												for a1_y in range(s1):
													# pool1 -> conv1
													a1_y_global = output_switches1_y[f1, a2_x_global, a2_y_global, img] + a1_y
													
													sigma31[cat,:,f1, a1_x, a1_y, f2, a2_x, a2_y, f3, a3_x, a3_y] += imgs[:, a1_x_global, a1_y_global, img]

	return sigma31

