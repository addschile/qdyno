import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
# TODO
"""
I should change these to be general to take in either numpy matrices or 
scipy sparse matrices

I'll need to go back through the whole code to make sure that every bit
of linear algebra is called from here
"""

sparse_lib = False

def dag(op):
    return op.conj().T

def commutator(op1,op2):
    return op1.dot(op2) - op2.dot(op1)

def anticommutator(op1,op2):
    return op1.dot(op2) + op2.dot(op1)

def matmult(*mats):
    for i,mat in enumerate(mats):
        if i==0:
            matout = mat.copy()
        else:
            matout = matout.dot(mat)
    return mat

def norm(psi):
    if is_vector(psi):
        return dag(psi).dot(psi)[0,0].real
    if is_matrix(psi):
        return psi.diagonal().sum().real

def is_hermitian(op):
    if is_matrix(op):
        if sparse_lib:
            if np.allclose(dag(op).data, op.data):
            else:
                raise ValueError('Physical observables must be Hermitian')
        else:
            if np.allclose(dag(op), op):
                return True
            else:
                raise ValueError('Physical observables must be Hermitian')
    else:
        raise ValueError('Hermiticity check requires matrix')

def is_vector(vec):
    return vec.shape[0]!=vec.shape[1]

def is_matrix(mat):
    return mat.shape[0]==mat.shape[1]

def is_tensor(tensor):
    return (len(tensor.shape)>2)

def to_liouville(rho):
    if len(rho.shape) == 2:
        # A matrix to a vector
        return rho.flatten().astype(complex)
    else:
        # A tensor to a matrix 
        ns = rho.shape[0]
        if sparse_lib:
            rho_mat = sp.csr_matrix.zeros((ns*ns,ns*ns), dtype=complex)
        else:
            rho_mat = np.zeros((ns*ns,ns*ns), dtype=complex)
        I = 0
        for i in range(ns):
            for j in range(ns):
                J = 0
                for k in range(ns):
                    for l in range(ns):
                        rho_mat[I,J] = rho[i,j,k,l]
                        J += 1
                I += 1
        return rho_mat

def from_liouville(rho_vec, ns=None):
    if ns is None:
        ns = int(np.sqrt(len(rho_vec)))
    return rho_vec.reshape(ns,ns).astype(complex)
