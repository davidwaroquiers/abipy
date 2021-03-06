#!/usr/bin/env python
"""
This example shows how to plot a band structure
using the eigenvalues stored in the GSR file produced by abinit.
"""
from abipy.abilab import abiopen
import abipy.data as abidata

# Here we use one of the GSR files shipped with abipy.
# Replace filename with the path to your GSR file or your WFK file.
filename = abidata.ref_file("si_nscf_GSR.nc")

# Open the GSR file and extract the band structure. 
with abiopen(filename) as ncfile:
    ebands = ncfile.ebands

# Plot the band energies. Note that the labels for the k-points
# are found automatically in an internal database.
ebands.plot(title="Silicon band structure")

# Plot the BZ and the k-point path.
ebands.kpoints.plot()
