__author__ = "Anders Logg"
__copyright__ = "Copyright (C) 2009 Simula Research Laboratory and %s" % __author__
__license__  = "GNU GPL Version 3 or any later version"

# Last changed: 2011-02-19

__all__ = ["NavierStokes", "NavierStokesDual"]

from dolfin import error, Constant, Parameters
from cbc.common import CBCProblem
from cbc.flow.solvers import NavierStokesSolver, NavierStokesDualSolver
from ufl import grad, Identity

class NavierStokes(CBCProblem):
    "Base class for all Navier-Stokes problems"

    def __init__(self, parameters=None):
        "Create Navier-Stokes problem"

        # Create solver
        self.solver = NavierStokesSolver(self)

        # Set up parameters
        self.parameters = Parameters("problem_parameters")
        self.parameters.add(self.solver.parameters)

    def solve(self):
        "Solve and return computed solution (u, p)"

        # Update solver parameters
        self.solver.parameters.update(self.parameters["solver_parameters"])

        # Call solver
        return self.solver.solve()

    def step(self, dt):
        "Make a time step of size dt"

        # Update solver parameters
        self.solver.parameters.update(self.parameters["solver_parameters"])

        # Call solver
        return self.solver.step(dt)

    def update(self, t):
        "Propagate values to next time step"
        return self.solver.update(t)

    def solution(self):
        "Return current solution values"
        return self.solver.solution()

    def solution_values(self):
        "Return solution values at t_{n-1} and t_n"
        return self.solver.solution_values()

    #--- Functions that must be overloaded by subclasses ---

    def mesh(self):
        "Return mesh"
        missing_function("mesh")

    #--- Functions that may optionally be overloaded by subclasses ---

    def density(self):
        "Return density"
        return 1.0

    def viscosity(self):
        "Return viscosity"
        return 1.0

    def body_force(self, V):
        "Return body force f"
        f = Constant((0,)*V.mesh().geometry().dim())
        return f

    def mesh_velocity(self, V):
         "Return mesh velocity (for ALE formulations)"
         w = Constant((0,)*V.mesh().geometry().dim())
         return w

    def boundary_conditions(self, V, Q):
        "Return boundary conditions for velocity and pressure"
        return [], []

    def velocity_dirichlet_values(self):
        "Return Dirichlet boundary values for the velocity"
        return []

    def velocity_dirichlet_boundaries(self):
        "Return Dirichlet boundaries for the velocity"
        return []

    def pressure_dirichlet_values(self):
        "Return Dirichlet boundary conditions for the velocity"
        return []

    def pressure_dirichlet_boundaries(self):
        "Return Dirichlet boundaries for the velocity"
        return []

    def velocity_initial_condition(self):
        "Return initial condition for velocity"
        return None

    def pressure_initial_condition(self):
        "Return initial condition for pressure"
        return 0

    def end_time(self):
        "Return end time"
        return 1.0

    def time_step(self):
        "Return preferred time step"
        return None

    def max_velocity(self):
        "Return maximum velocity (used for selecting time step)"
        return 1.0

    def __str__(self):
        "Return a short description of the problem"
        return "Navier-Stokes problem"

class NavierStokesDual(NavierStokes):
    "Base class for all Navier-Stokes dual problems"

    def __init__(self, parameters=None):
        "Create Navier-Stokes dual problem"

        # Create solver
        self.solver = NavierStokesDualSolver(self)

        # Set up parameters
        self.parameters = Parameters("dual_problem_parameters")
        self.parameters.add(self.solver.parameters)

    def functional(self, u, p, V, Q, n):
        "Return goal functional"
        missing_function("functional")

    def boundary_markers(self):
        "Return exterior boundary markers"
        return None
