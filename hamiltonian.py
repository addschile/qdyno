import numpy as np
import qdynos.constants as const

from .utils import dag,is_hermitian,is_vector,is_matrix

class Hamiltonian(object):
    """
    Base Hamiltonian class.
    """

    def __init__(self, H, baths=None, hbar=1.):
        """
        Parameters
        ----------
        H: np.ndarray
            Hamiltonian matrix
        bath: list of Bath classes
            Baths that independently couple to the system
        hbar: float
        """
        const.hbar = hbar
        self.nstates = H.shape[0]
        self.check_hermiticity(H)
        self.ham = H
        self.eigensystem()
        self.baths = baths
        if self.baths != None: self.nbaths = len(self.baths)
        
    def __repr__(self):
        return "Hamiltonian class"

    def check_hermiticity(self, H):
        """
        Check hermiticity of the Hamiltonian
        """
        if is_hermitian(H):
            self.is_hermitian = True
        else:
            raise ValueError('Hamiltonian is not Hermitian')

    def eigensystem(self):
        self.ev,self.ek = np.linalg.eigh(self.ham)
        self.compute_frequencies()

    def compute_frequencies(self):
        self.omegas = np.zeros((self.nstates,self.nstates))
        for i in range(self.nstates):
            for j in range(self.nstates):
                self.omegas[i,j] = (self.ev[i]-self.ev[j])/const.hbar

    def compute_unique_freqs(self):
        self.frequencies = np.unique(self.omegas)

    def to_eigenbasis(self, op):
        if is_vector(op):
            return np.dot(dag(self.ek), op)
        elif is_matrix(op):
            return np.dot(dag(self.ek), np.dot(op, self.ek))
        else:
            raise AttributeError("Not a valid operator")

    def from_eigenbasis(self, op):
        if is_vector(op):
            return np.dot(self.ek, op)
        elif is_matrix(op):
            return np.dot(self.ek, np.dot(op, dag(self.ek)))
        else:
            raise AttributeError("Not a valid operator")

    def commutator(self, op, eig=True):
        if eig:
            return np.dot(np.diag(self.ev),op) - np.dot(op,np.diag(self.ev))
        else:
            return np.dot(self.ham,op) - np.dot(op,self.ham)

    """
    def thermal_dm(self):
        if bath!=None
            rho_eq = np.zeros((self.nstates,self.nstates), dtype=complex)
            rho_eq += np.diag(np.exp(-self.ev/bath.kT))
            return rho_eq/np.trace(rho_eq)
        else:
            raise NotImplementedError("Bath must be initialized before calling")
    """

class MDHamiltonian(Hamiltonian):
    """
    Hamiltonian class for multidimensional quantum systems 
    (e.g. el-vib models, conical intersection models).
    """
    def __init__(self, H, nel, nmodes, coords=None, potentials=None, couplings=None, baths=None, hbar=1.):
        """
        Parameters
        ----------
        H: np.ndarray
            Hamiltonian matrix
        nel: int
            number of electronic states
        nmodes: int
            number of modes treated in the system (e.g. 2 for minimal conical 
            intersection)
        coords: list of list of np.ndarray
            coordinate operators for each mode in each electronic state
        potentials: list of functions
            potential energy as a function of the coordinate for each
            electronic state
        couplings: list of functions
            potential energy as a function of the coordinate for each
            electronic state
        baths: list of Bath classes
            Baths that independently couple to the system
        hbar: float
        """
        const.hbar = hbar
        self.nstates = H.shape[0]
        self.nel = nel
        self.nmodes = nmodes
        self.check_hermiticity(H)
        self.ham = H
        self.eigensystem()
        self.setup_system_operators(coords)
        if potentials==None:
            self.compute_adiabatic = False
        else:
            self.compute_adiabatic = False
            self.potentials = potentials
            self.couplings = couplings
        self.baths = baths
        if self.baths != None: self.nbaths = len(self.baths)

    def __repr__(self):
        return "Multidimensional Hamiltonian class"

    def setup_system_operators(self, coords):
        """
        """
        if coords != None:
            assert(len(coords)==self.nel)
            self.coords = list()
            for op_list in coords:
                coord_list = list()
                for op in op_list:
                    # diagonalize the coordinate opeartor
                    w,v = np.linalg.eigh(op)
                    coord_list.append( [w,v] )
                self.coords.append( coord_list.copy() )

    # TODO this needs testing
    def make_adiabatic_transform(self,coords):
        """
        """
        S = np.zeros((self.nel,self.nel))
        for i in range(self.nel):
            for j in range(self.nmodes):
                S[i,i] += self.potentials[i][j](coords[j])
        for i in range(self.nel-1):
            for j in range(i+1,self.nel):
                for k in range(self.nmodes):
                    S[i,j] += self.coupling[i][j](coords[k])
                S[j,i] = S[i,j]
        w,v = np.linalg.eigh(S)
        vad = v.copy()
        for i in range(self.nmodes):
            vad = np.kron(vad,np.identity(self.mode_states[i]))
        return vad

    # TODO this needs testing
    def compute_coordinate_surfaces(self, state):
        """
        NOTE: Currently only written for 2 modes (minimal conical intersection)
        probably need to extend with C++/Fortran for more dimensions or for parallelization
        """ 
        surfaces = []
        if is_vector(state):
            eket = np.zeros((self.nel,1))
            for i in range(self.nel):
                eket *= 0.
                eket[i,0] = 1.
                for j in range(self.nmodes):
                    surface = np.zeros(len(self.coords[i][j][0]))
                    for k,ev in enumerate(self.coords[i][j][0]):
                        kket = dag(np.array([self.coords[i][j][1][:,k]]))
                        for l in range(self.nmodes):
                            if l!=j:
                                for m,ev2 in enumerate(self.coords[i][l][0]):
                                    projket = eket.copy()
                                    mket = dag(np.array([self.coords[i][l][1][:,m]]))
                                    if l<j:
                                        projket = np.kron(projket,np.kron(mket,kket))
                                        coords = [self.coords[i][l][0][m],self.coords[i][j][0][k]]
                                    elif l>j:
                                        projket = np.kron(projket,np.kron(kket,mket))
                                        coords = [self.coords[i][j][0][k],self.coords[i][l][0][m]]
                                    if self.compute_adiabatic:
                                        vad = self.make_adiabatic_transform(coords)
                                        state = np.dot(dag(vad),state)
                                    da = np.dot(dag(projket),state)[0]
                                    surface[k] += (np.conj(da)*da).real
                                    if self.compute_adiabatic:
                                        state = np.dot(vad,state)
                    surfaces.append( surface.copy() )
        elif is_matrix(state):
            eket = np.zeros((self.nel,1))
            for i in range(self.nel):
                eket *= 0.
                eket[i,0] = 1.
                for j in range(self.nmodes):
                    surface = np.zeros(len(self.coords[i][j][0]))
                    for k,ev in enumerate(self.coords[i][j][0]):
                        kket = self.coords[i][j][1][:,k]
                        projket = eket.copy()
                        for l in range(self.nmodes):
                            for m,ev2 in enumerate(self.coords[i][l][0]):
                                mket = self.coords[i][l][1][:,m]
                                if l<j:
                                    projket = np.kron(projket,np.kron(mket,kket))
                                    coords = [self.coords[i][l][0][m],self.coords[i][j][0][k]]
                                elif l>j:
                                    projket = np.kron(projket,np.kron(kket,mket))
                                    coords = [self.coords[i][j][0][k],self.coords[i][l][0][m]]
                                if self.compute_adiabatic:
                                    vad = self.make_adiabatic_transform(coords)
                                    state = np.dot(dag(vad),np.dot(state,vad))
                                surface[k] += np.dot(dag(projket),np.dot(state,projket))[0,0].real
                                if self.compute_adiabatic:
                                    state = np.dot(vad,np.dot(state,dag(vad)))
                    surfaces.append( surface.copy() )
        return surfaces
