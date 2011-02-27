"This module implements residuals used for adaptivity."

__author__ = "Kristoffer Selim and Anders Logg"
__copyright__ = "Copyright (C) 2010 Simula Research Laboratory and %s" % __author__
__license__  = "GNU GPL Version 3 or any later version"

# Last changed: 2011-02-27

from dolfin import *

from operators import Sigma_F as _Sigma_F

def inner_product(v, w):
    "Return inner product for mixed fluid/structure space"

    # Define cell integrals
    dx_F = dx(0)
    dx_S = dx(1)
    dx_M = dx_F

    # Extract variables
    v1_F, q1_F, v1_S, q1_S, v1_M, q1_M = v
    v2_F, q2_F, v2_S, q2_S, v2_M, q2_M = w

    # Inner product on subdomains, requiring ident_zeros
    m1 = (inner(v1_F, v2_F) + q1_F*q2_F)*dx_F + \
         (inner(v1_S, v2_S) + inner(q1_S, q2_S))*dx_S + \
         (inner(v1_M, v2_M) + inner(q1_M, q2_M))*dx_M

    # Inner product on the whole domain
    m2 = (inner(v1_F, v2_F) + q1_F*q2_F)*dx + \
         (inner(v1_S, v2_S) + inner(q1_S, q2_S))*dx + \
         (inner(v1_M, v2_M) + inner(q1_M, q2_M))*dx

    return m2

def weak_residual(U0, U1, U, w, kn, problem):
    "Return weak residuals"

    # Extract variables
    U_F0, P_F0, U_S0, P_S0, U_M0 = U0
    U_F1, P_F1, U_S1, P_S1, U_M1 = U1
    U_F,  P_F,  U_S,  P_S,  U_M  = U
    v_F, q_F, v_S, q_S, v_M, q_M = w

    # Get problem parameters
    Omega   = problem.mesh()
    rho_F   = problem.fluid_density()
    mu_F    = problem.fluid_viscosity()
    rho_S   = problem.structure_density()
    mu_S    = problem.structure_mu()
    lmbda_S = problem.structure_lmbda()
    alpha_M = problem.mesh_alpha()
    mu_M    = problem.mesh_mu()
    lmbda_M = problem.mesh_lmbda()

    # Define normals
    N = FacetNormal(Omega)
    N_F = N
    N_S = -N

    # Define cell integrals
    dx_F = dx(0)
    dx_S = dx(1)

    # Define time derivative
    Dt_U_F = rho_F*((U_F1 - U_F0)/kn + dot(grad(U_F), U_F))

    # Define stress
    Sigma_F = _Sigma_F(U_F, P_F, mu_F)

    # Fluid residual
    R_F = inner(v_F, Dt_U_F)*dx_F + inner(grad(v_F), Sigma_F)*dx_F \
        - inner(v_F, mu_F*dot(grad(U_F).T, N_F))*ds \
        + inner(v_F, P_F*N_F)*ds \
        + inner(q_F, div(U_F))*dx_F

    return R_F

def strong_residual(U0, U1, U, Z, EZ, w, kn, problem):
    "Return strong residuals (integrated by parts)"

    # Extract variables
    U_F0, P_F0, U_S0, P_S0, U_M0       = U0
    U_F1, P_F1, U_S1, P_S1, U_M1       = U1
    U_F,  P_F,  U_S,  P_S,  U_M        = U
    Z_F,  Y_F,  Z_S,  Y_S,  Z_M,  Y_M  = Z
    EZ_F, EY_F, EZ_S, EY_S, EZ_M, EY_M = EZ

    # Get problem parameters
    Omega   = problem.mesh()
    Omega_F = problem.fluid_mesh()
    Omega_S = problem.structure_mesh()
    rho_F   = problem.fluid_density()
    mu_F    = problem.fluid_viscosity()
    rho_S   = problem.structure_density()
    mu_S    = problem.structure_mu()
    lmbda_S = problem.structure_lmbda()
    alpha_M = problem.mesh_alpha()
    mu_M    = problem.mesh_mu()
    lmbda_M = problem.mesh_lmbda()

    # Define normals
    N = FacetNormal(Omega)
    N_F = N
    N_S = N

    # FIXME: Check sign of N_S, should it be -N?

    # Define inner products
    dx_F = dx(0)
    dx_S = dx(1)

    # Define "facet" products
    dS_F  = dS(0)
    dS_S  = dS(1)
    d_FSI = dS(2)

    # Define midpoint values
    U_F = 0.5 * (U_F0 + U_F1)
    P_F = 0.5 * (P_F0 + P_F1)

    # Define time derivative
    Dt_U_F = rho_F * ((U_F1 - U_F0)/kn + dot(grad(U_F), U_F))

    # Define stress
    Sigma_F = _Sigma_F(U_F, P_F, mu_F)

    # Fluid residual contributions
    R_F0 = w*inner(EZ_F - Z_F, Dt_U_F - div(Sigma_F))*dx_F
    R_F1 = avg(w)*inner(EZ_F('+') - Z_F('+'), jump(Sigma_F, N_F))*dS_F
    R_F2 = w*inner(EZ_F - Z_F, dot(Sigma_F, N_F))*ds
    R_F3 = w*inner(EY_F - Y_F, div(U_F))*dx_F

    return (R_F0, R_F1, R_F2, R_F3)
