#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar  5 15:31:42 2019

@author: engels
"""
import numpy as np

def get_dset_name( fname ):
    from os.path import basename
    dset_name = basename(fname)
    dset_name = dset_name[0:dset_name.find('_')]

    return dset_name


def get_timestamp_name( fname ):
    from os.path import basename
    dset_name = basename(fname)
    dset_name = dset_name[dset_name.find('_')+1:dset_name.find('.')]

    return dset_name

def read_flusi_HDF5( fname, dtype=np.float32, twoD=False, verbose=True):
    """  Read HDF5 file generated by FLUSI.
    Returns: time, box, origin, data
    """
    import h5py

    f = h5py.File(fname, 'r')


    # list all hdf5 datasets in the file - usually, we expect
    # to find only one.
    datasets = list(f.keys())
    # if we find more than one dset we warn that this is unusual
    if (len(datasets) != 1):
        raise ValueError("we found more than one dset in the file (problemo)"+fname)

    else:
        # as there should be only one, this should be our dataset:
        dset_name = datasets[0]

        # get the dataset handle
        dset_id = f.get(dset_name)

        # from the dset handle, read the attributes
        time = dset_id.attrs.get('time')
        res = dset_id.attrs.get('nxyz')
        box = dset_id.attrs.get('domain_size')
        origin = dset_id.attrs.get('origin')
        if origin is None:
            origin = np.array([0,0,0])

        b = f[dset_name][:]
        data = np.array(b, dtype=dtype)
        
        if len(data.shape) == 3:
            # its a funny flusi convention that we have to swap axes here, and I
            # never understood why it is this way.
            # NB: this applies to 3D data only (even though if running in 2D mode,
            # flusi stores 3d array with 1 index length 1, but other softwares
            # such as UP2D produce real 2D arrays)
            data = np.swapaxes(data, 0, 2)

        if (np.max(res-data.shape)>0):
            print('WARNING!!!!!!')
            print('read_flusi_HDF5: array dimensions look funny')

        f.close()

        if twoD and data.shape[0] == 1:
            data = data[0,:,:].copy()
            data = data.transpose()

    if verbose:
        print("We read FLUSI file %s at time=%f \nResolution :" % (fname, time), data.shape)


    return time, box, origin, data




def write_flusi_HDF5( fname, time, box, data, viscosity=0.0, origin=np.array([0.0,0.0,0.0]), dtype=np.float32 ):
    import h5py

    dset_name = get_dset_name( fname )

    if len(data.shape)==3:
        #3d data
        nx, ny, nz = data.shape
        print( "Writing to file=%s dset=%s max=%e min=%e size=%i %i %i " % (fname, dset_name, np.max(data), np.min(data), nx,ny,nz) )
        # i dont really know why, but there is a messup in fortran vs c ordering, so here we have to swap
        # axis
        # data = np.swapaxes(data, 0, 2)
        nxyz = np.array([nz,nx,ny])
    else:
        #2d data
        nx, ny = data.shape
        print( "Writing to file=%s dset=%s max=%e min=%e size=%i %i" % (fname, dset_name, np.max(data), np.min(data), nx,ny) )
        data = np.swapaxes(data, 0, 1)
        nxyz = np.array([1, nx,ny])

    fid = h5py.File( fname, 'w')

    fid.create_dataset( dset_name, data=data, dtype=dtype )#, shape=data.shape[::-1] )
    fid.close()

    fid = h5py.File(fname,'a')
    dset_id = fid.get( dset_name )
    dset_id.attrs.create('time', time)
    dset_id.attrs.create('viscosity', viscosity)
    dset_id.attrs.create('domain_size', box )
    dset_id.attrs.create('origin', origin )
    dset_id.attrs.create('nxyz', nxyz )

    fid.close()
    
    
    
def crop_flusi_HDF5(file, Nxcut=[0, 0], Nycut=[0, 0], Nzcut=[0, 0]):
    """
        Crop the data matrix.
        
            Input:
            N[x|y|t]_cut: 1d-array of size 2
            Array will be croped from Nx_cut[0]:-Nx_cut[1] in x dimension,
                                      Ny_cut[0]:-Ny_cut[1] in y dimension,
                                      Nz_cut[0]:-Nz_cut[1] in z dimension
    """
    time, box, origin, data = read_flusi_HDF5( file )
    data = np.squeeze(data)
    
    if len(data.shape)==2:
        # this is the lazy variant:
        y = np.linspace(0,box[-1],np.size(data,-1)) + origin[-1]
        x = np.linspace(0,box[-2],np.size(data,-2)) + origin[-2]
        x_cut= x[Nxcut[0]:-Nxcut[1]] - x[Nxcut[0]]
        y_cut= y[Nycut[0]:-Nycut[1]] - y[Nycut[0]]
        box[-2] = max(x_cut)- min(x_cut)
        box[-1] = max(y_cut)- min(y_cut)
        origin[-2] = x_cut[0]
        origin[-1] = y_cut[0]
        data_cut = data[ Nxcut[0] : -Nxcut[1], Nycut[0] : -Nycut[1]]
        data = np.expand_dims(data_cut,2) # we have to add the z dimension again

    else:
        print("crop_flusi_hdf5: 3d not implemented")
        return 
    
    
    write_flusi_HDF5( file, time, box, data, origin )
    
def resample_flusi_HDF5(file, N):
    """
        Sample the data matrix up
        
            Input:
            shape
            
    """
    import fourier_tools
    time, box, origin, data = read_flusi_HDF5( file )
    data = np.squeeze(data)
    
    if len(data.shape)==2:
        data = fourier_tools.fft2_resample( data, N  )
        data = np.expand_dims(data,2) # we have to add the z dimension again
    
    else:
        print("crop_flusi_hdf5: 3d not implemented")
        return 
    
    write_flusi_HDF5( file, time, box, data, origin )