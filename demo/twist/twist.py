__author__ = "Harish Narayanan"
__copyright__ = "Copyright (C) 2009 Simula Research Laboratory and %s" % __author__
__license__  = "GNU GPL Version 3 or any later version"

from cbc.twist import *

class Twist(StaticHyperelasticity):

    def mesh(self):
        n = 8
        return UnitCube(n, n, n)

    def dirichlet_conditions(self, vector):
        clamp = Expression(("0.0", "0.0", "0.0"))
        twist = Expression(("0.0",
                            "y0 + (x[1] - y0) * cos(theta) - (x[2] - z0) * sin(theta) - x[1]",
                            "z0 + (x[1] - y0) * sin(theta) + (x[2] - z0) * cos(theta) - x[2]"))
        twist.y0 = 0.5
        twist.z0 = 0.5
        twist.theta = pi/3
        return [clamp, twist]

    def dirichlet_boundaries(self):
        left = "x[0] == 0.0"
        right = "x[0] == 1.0"
        return [left, right]

    def body_force(self, vector):
        B = Expression(("0.0", "0.0", "0.0"))
        return B

    def material_model(self):
        # Material parameters can either be numbers or spatially
        # varying fields. For example,
        mu       = 3.8461
        lmbda    = Expression("x[0]*5.8 + (1 - x[0])*5.7")
        C10 = 0.171; C01 = 4.89e-3; C20 = -2.4e-4; C30 = 5.e-4

        # It is also easy to switch material models. Uncomment one of
        # the following lines to see a particular material's response.
        #material = MooneyRivlin([mu/2, mu/2])
        material = StVenantKirchhoff([mu, lmbda])
        #material = neoHookean([mu])
        #material = Isihara([C10, C01, C20])
        #material = Biderman([C10, C01, C20, C30])

        return material

    def __str__(self):
        return "A hyperelastic cube twisted by 60 degrees"

# Setup and solve problem
twist = Twist()
print twist
u = twist.solve()
plot(u, title = "Displacement", mode = "displacement", rescale = True, interactive = True)
