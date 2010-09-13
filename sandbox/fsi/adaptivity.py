"This module implements functionality for adaptivity."

__author__ = "Kristoffer Selim and Anders Logg"
__copyright__ = "Copyright (C) 2010 Simula Research Laboratory and %s" % __author__
__license__  = "GNU GPL Version 3 or any later version"

# Last changed: 2010-09-13

from dolfin import info
from numpy import zeros, argsort

from residuals import *
from storage import *
from utils import *

def estimate_error(problem):
    "Estimate error and compute error indicators"

    # Compute error indicators
    eta_K = compute_error_indicators_h(problem)

    # FIXME: Need to include E_k and E_c

    # Compute error estimate
    E_h = sum(eta_K)
    E_k = 0.0
    E_c = 0.0
    E = E_h + E_k + E_c

    return E, eta_K

def refine_mesh(mesh, indicators):
    "Refine mesh based on error indicators"

    # Set cell markers using Dorfler marking
    fraction = 0.5
    indices = list(argsort(indicators))
    indices.reverse()
    sub_sum = 0.0
    total_sum = sum(indicators)
    markers = CellFunction("bool", mesh)
    markers.set_all(False)
    for i in indices:
        sub_sum += indicators[i]
        markers[int(i)] = True
        if sub_sum >= fraction*total_sum:
            break

    # Plot markers (convert to uint so it can be plotted)
    plot_markers = CellFunction("uint", mesh)
    plot_markers.set_all(0)
    for i in range(plot_markers.size()):
        if markers[i]:
            plot_markers[i] = True
    plot(plot_markers, title="Markers")

    # Refine mesh
    mesh = refine(mesh, markers)
    plot(mesh, "Refined mesh")

    return mesh

def compute_error_indicators_h(problem):
    "Compute error indicators for space discretization error E_h"

    # Get meshes
    Omega = problem.mesh()
    Omega_F = problem.fluid_mesh()
    Omega_S = problem.structure_mesh()

    # Define projection space (piecewise constants)
    W = FunctionSpace(Omega, "DG", 0)
    w = TestFunction(W)

    # Initialize primal functions
    U_F0, P_F0, U_S0, P_S0, U_M0 = init_primal_data(Omega)
    U_F1, P_F1, U_S1, P_S1, U_M1 = init_primal_data(Omega)

    # Initialize dual functions
    Z, (Z_F, Y_F, Z_S, Y_S, Z_M, Y_M) = init_dual_data(Omega)

    # Define function spaces for extrapolation
    V2 = VectorFunctionSpace(Omega, "CG", 2)
    V3 = VectorFunctionSpace(Omega, "CG", 3)
    Q2 = FunctionSpace(Omega, "CG", 2)

    # Define functions for extrapolation
    ZZ_F = Function(V3)
    YY_F = Function(Q2)
    ZZ_S = Function(V2)
    YY_S = Function(V2)
    ZZ_M = Function(V2)
    YY_M = Function(V2)

    # Define time step (value set in each time step)
    kn = Constant(0.0)

    # Get residuals
    R_F, R_S, R_M = strong_residuals(U_F0, P_F0, U_S0, P_S0, U_M0,
                                     U_F1, P_F1, U_S1, P_S1, U_M1,
                                      Z_F,  Y_F,  Z_S,  Y_S,  Z_M,  Y_M,
                                     ZZ_F, YY_F, ZZ_S, YY_S, ZZ_M, YY_M,
                                     w, kn, problem)

    # Reset vectors for assembly of residuals
    eta_F = zeros(Omega.num_cells())
    eta_S = zeros(Omega.num_cells())
    eta_M = zeros(Omega.num_cells())

    # Sum residuals over time intervals
    timestep_range = read_timestep_range(problem)
    #for i in range(1, len(timestep_range)):
    # FIXME: Temporary while testing
    for i in range(len(timestep_range) / 2, len(timestep_range) / 2 + 1):

        # Get current time and time step
        t0 = timestep_range[i - 1]
        t1 = timestep_range[i]
        T  = problem.end_time()
        dt = t1 - t0
        kn.assign(dt)

        # Display progress
        info("")
        info("-"*80)
        begin("* Evaluating residuals on new time step")
        info_blue("  * t = %g (T = %g, dt = %g)" % (t0, T, dt))

        # Read primal data
        read_primal_data(U_F0, P_F0, U_S0, P_S0, U_M0, t0, Omega, Omega_F, Omega_S)
        read_primal_data(U_F1, P_F1, U_S1, P_S1, U_M1, t1, Omega, Omega_F, Omega_S)

        # Read dual data (pick value at right-hand side of interval)
        read_dual_data(Z, t1)

        # Extrapolate dual data
        info("Extrapolating dual solution")
        ZZ_F.extrapolate(Z_F)
        YY_F.extrapolate(Y_F)
        ZZ_S.extrapolate(Z_S)
        YY_S.extrapolate(Y_S)
        ZZ_M.extrapolate(Z_M)
        YY_M.extrapolate(Y_M)

        # Assemble error indicator contributions
        info("Assembling error contributions")
        e_F = [assemble(R_Fi, interior_facet_domains=problem.fsi_boundary) for R_Fi in R_F]
        e_S = [assemble(R_Si, interior_facet_domains=problem.fsi_boundary) for R_Si in R_S]
        e_M = [assemble(R_Mi, interior_facet_domains=problem.fsi_boundary) for R_Mi in R_M]

        # Add error contributions
        eta_F += dt * sum(abs(e.array()) for e in e_F)
        eta_S += dt * sum(abs(e.array()) for e in e_S)
        eta_M += dt * sum(abs(e.array()) for e in e_M)

        end()

    # Compute sum of error indicators
    eta_K = eta_F + eta_S + eta_M

    # Plot residuals
    #plot(array_to_meshfunction(eta_F, Omega), title="Fluid error indicators")
    #plot(array_to_meshfunction(eta_S, Omega), title="Structure error indicators")
    #plot(array_to_meshfunction(eta_M, Omega), title="Mesh error indicators")
    plot(array_to_meshfunction(eta_K, Omega), title="Total error indicators")

    return eta_K

def compute_timestep(R, S, TOL, dt, t, T):
    """Compute new time step based on residual R, stability factor S,
    tolerance TOL, and the previous time step dt. The time step is
    adjusted so that we will not step beyond the given end time."""

    # Parameters for adaptive time-stepping
    C = 1.0               # interpolation constant
    safety_factor = 0.9   # safety factor for time step selection
    snap = 0.9            # snapping to end time when close
    conservation = 1.0    # time step conservation (high value means small change)

    # Compute new time step
    dt_new = safety_factor * TOL / (C*S*R)

    # FIXME: Temporary until we get real input
    dt_new = dt

    # Modify time step to avoid oscillations
    dt_new = (1.0 + conservation) * dt * dt_new / (dt + conservation * dt_new)

    # Modify time step so we don't step beoynd end time
    at_end = False
    if dt_new > snap * (T - t):
        info("Close to t = T, snapping time step to end time: %g --> %g" % (dt_new, T - t))
        dt_new = T - t
        at_end = True

    info("Changing time step: %g --> %g" % (dt, dt_new))

    return dt_new, at_end
