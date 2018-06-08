from __future__ import print_function,absolute_import

import numpy as np
import qdynos.constants as const

from .integrator import Integrator
from .dynamics import Dynamics
from .utils import commutator,dag,to_liouville
from .options import Options
from .results import Results

class Redfield(Dynamics):
    """Dynamics class for Redfield-like dynamics. Can perform both 
    time-dependent (TCL2) and time-independent dynamics with and without the 
    secular approximation.
    """

    def __init__(self, ham, time_dependent=False, is_secular=False):
        """Instantiates the Redfield class.

        Parameters
        ----------
        ham : Hamiltonian or MDHamiltonian class
        time_dependent : bool
        is_secular : bool
        """
        super(Redfield, self).__init__(ham)
        self.ham = ham
        self.time_dep = time_dependent
        self.is_secular = is_secular

    def setup(self, options, results):
        # generic setup
        if options==None:
            self.options = Options()
        else:
            self.options = options
            if self.options.method == "exact":
                raise NotImplementedError
        if results==None:
            self.results = Results()
        else:
            self.results = results
            if self.results.map_ops:
                assert(repr(self.ham)=="Multidimensional Hamiltonian class")
                self.results.map_function = self.ham.compute_coordinate_surfaces

        self.ode = Integrator(self.dt, self.eom, self.options)

        if self.options.method != "exact":
            if self.time_dep:
                self.coupling_operators_setup()
                self.equation_of_motion = self.td_rf_eom
            else:
                self.make_redfield_operators()
                self.equation_of_motion = self.rf_eom

    def make_redfield_operators(self):
        """Make and store the coupling operators and "dressed" copuling operators.
        """
        nstates = self.ham.nstates
        self.C = list()
        self.E = list()
        for k,bath in enumerate(self.ham.baths):
            Ga = self.ham.to_eigenbasis( bath.c_op )
            theta_plus = np.zeros((nstates,nstates),dtype=complex)
            for i in range(nstates):
                for j in range(nstates):
                    theta_plus[i,j] = bath.ft_bath_corr(-self.ham.omegas[i,j])
            Ga_plus = Ga*theta_plus
            self.C.append(Ga.copy())
            self.E.append(Ga_plus.copy())

    def coupling_operators_setup(self):
        """Make coupling operators and initialize "dressing" for copuling 
        operators.
        """
        self.C = []
        self.gamma_n = [[]]*self.ham.nbaths
        self.gamma_n_1 = [[]]*self.ham.nbaths
        ns = self.ham.nstates
        b = self.ode.b

        for op,bath in enumerate(self.ham.baths):
            self.C.append( self.ham.to_eigenbasis( bath.c_op ) )
            self.gamma_n[op] = list()
            self.gamma_n_1[op] = list()

        for op,bath in enumerate(self.ham.baths):
            for k in range(self.ode.order):
                t = b[k]*self.dt
                if k==0:
                    self.gamma_n[op].append( np.zeros((self.ham.nstates,self.ham.nstates),dtype=complex) )
                    theta_plus = np.exp(-1.j*self.ham.omegas*0.0)*bath.bath_corr_t(0.0)
                    self.gamma_n_1[op].append(theta_plus.copy())
                else:
                    theta_plus = np.exp(-1.j*self.ham.omegas*t)*bath.bath_corr_t(t)
                    self.gamma_n[op].append( self.gamma_n[op][k-1] + 0.5*(b[k]-b[k-1])*self.dt*(theta_plus + self.gamma_n_1[op][k-1]) )
                    self.gamma_n_1[op].append( theta_plus.copy() )

    def make_tcl2_operators(self, time):
        """Integrate "dressing" for copuling operators. Uses trapezoid rule 
        with grid of integration method (e.g., Runge-Kutta 4).
        """
        b = self.ode.b
        for op,bath in enumerate(self.ham.baths):
            for k in range(self.ode.order):
                t = time + b[k]*self.dt
                theta_plus = np.exp(-1.j*self.ham.omegas*t)*bath.bath_corr_t(t)
                if k==0:
                    self.gamma_n[op][k] = self.gamma_n[op][-1].copy()
                    self.gamma_n_1[op][k] = theta_plus.copy()
                else:
                    self.gamma_n[op][k] = self.gamma_n[op][k-1] + 0.5*self.dt*(b[k]-b[k-1])*(theta_plus + self.gamma_n_1[op][k-1])
                    self.gamma_n_1[op][k] = theta_plus.copy()

    def update_ops(self, time):
        """Update the dressed coupling operators by integrating Fourier-Laplace
        transform of bath correlation function in time.
        """
        self.E = [[]]*self.ham.nbaths
        for i in range(len(self.C)):
            self.E[i] = list()
            for j in range(self.ode.order):
                self.E[i].append(self.gamma_n[i][j]*self.C[i])
        if time < self.options.markov_time:
            self.make_tcl2_operators(time)

    def eom(self, state, order):
        return self.equation_of_motion(state, order)

    def rf_eom(self, state, order):
        dy = (-1.j/const.hbar)*self.ham.commutator(state)
        for j in range(len(self.ham.baths)):
            dy += (commutator(np.dot(self.E[j],state),self.C[j]) + commutator(self.C[j],np.dot(state,dag(self.E[j]))))/const.hbar**2.
        return dy

    def td_rf_eom(self, state, order):
        dy = (-1.j/const.hbar)*self.ham.commutator(state)
        for j in range(len(self.ham.baths)):
            dy += (commutator(np.dot(self.E[j][order],state),self.C[j]) + commutator(self.C[j],np.dot(state,dag(self.E[j][order]))))/const.hbar**2.
        return dy

    def solve(self, rho0, times, options=None, results=None):
        """Solve the Redfield equations of motion.

        Parameters
        ----------
        rho_0 : np.array
        times : np.array
        options : Options class
        results : Results class

        Returns
        -------
        results : Results class
        """
        self.dt = times[1]-times[0]
        self.setup(options, results)
        rho = self.ham.to_eigenbasis(rho0.copy())

        if self.options.method == 'exact':
            raise NotImplementedError
            # Redfield class setup
            if self.time_dep:
                raise NotImplementedError
            else:
                # TODO need to make exact propagator
                self.prop = np.exp(-1.j*self.ham.omegas*dt)
                self.equation_of_motion = lambda x: np.dot(self.prop,x)
                rho = self.ham.to_eigenbasis(rho)
                ode._set_y_value(rho, times[0])
                for time in times:
                    if i%self.results.every==0:
                        if self.options.progress: print(i)
                        self.results.analyze_state(i, time, self.ham.from_eigenbasis(ode.y))
                    ode.integrate()
        else:
            self.ode._set_y_value(rho, times[0])
            for i,time in enumerate(times):
                if self.time_dep:
                    self.update_ops(time)
                if i%self.results.every==0:
                    if self.options.progress: print(i)
                    self.results.analyze_state(i, time, self.ham.from_eigenbasis(self.ode.y))
                self.ode.integrate()

        return self.results
