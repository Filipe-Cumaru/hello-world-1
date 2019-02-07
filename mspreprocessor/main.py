
import numpy as np
import time
import pdb
import geoUtil.geoTools as gtool
import xlsxwriter
from math import pi, sqrt
from pymoab import rng, types
from meshHandle.multiscaleMesh import FineScaleMeshMS as msh
from meshHandle.corePymoab import CoreMoab as core
from tpfa.boundary_conditions import BoundaryConditions
from scipy.sparse import csr_matrix, lil_matrix
from scipy.sparse.linalg import spsolve

def equiv_perm(k1, k2):
    return (2*k1*k2)/(k1 + k2)

def centroid_dist(c1, c2):
    return ((c1-c2)**2).sum()

print("Initializating mesh")
start = time.time()
dx, dy, dz = 1, 1, 1
nx, ny, nz = 20, 20, 20
num_elements = nx*ny*nz
M = msh("malha-teste.h5m", dim = 3)
vec = np.arange(len(M.alma)).astype(int)
end = time.time()
print("This step lasted {0}s".format(end-start))

print("Setting the permeability")
M.permeability[:] = 1

print("Assembly")
start = time.time()
perm = M.permeability[:]
adj = M.volumes.bridge_adjacencies(M.volumes.all, 2, 3)
center = M.volumes.center[M.volumes.all]
coef = lil_matrix((num_elements, num_elements), dtype=np.float_)
for i in range(num_elements):
    adjacencies = adj[i]
    for j in range(len(adjacencies)):
        id = np.array([adjacencies[j]],  dtype= np.int)
        coef[i,id] = equiv_perm(perm[i], perm[id])/centroid_dist(center[i], center[id])
    coef[i,i] = (-1)*coef[i].sum()
end = time.time()
print("This step lasted {0}s".format(end-start))

print("Setting boundary conditions")
start = time.time()
bc = BoundaryConditions(num_elements, nx, ny, coef)
end = time.time()
print("This step lasted {0}s".format(end-start))

'''
workbook = xlsxwriter.Workbook('coef_mspreprocessor.xlsx')
worksheet = workbook.add_worksheet()
matrix = lil_matrix.toarray(coef)

row = 0
col = 0

for row in range(125):
  for col in range(125):
    worksheet.write(row, col, matrix[row][col])

workbook.close()
'''

print("Solving the problem")
start = time.time()
coef = lil_matrix.tocsr(bc.coef)
q = lil_matrix.tocsr(bc.q)
P = spsolve(coef,q)
end = time.time()
print("This step lasted {0}s".format(end-start))

print("Storing results")
start = time.time()
for i in range(num_elements):
    M.pressure[i] = P[i]
    #M.erro[i] = P[i]-P_analitico[i]
end = time.time()
print("This step lasted {0}s".format(end-start))

print("Printing results")
M.core.print()
