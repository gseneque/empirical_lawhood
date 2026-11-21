/* SPDX-License-Identifier: MPL-2.0
 * Complete nonperiodic Amber movable pair energy and Cartesian forces.
 * Each selected row interacts with every fixed particle and every later
 * movable particle. Original exception pairs are omitted here and evaluated
 * by their original OpenMM force. No cutoffs, fitted coefficients, single
 * precision, fast-math transformations, or altered pair denominator.
 */
#include <math.h>
#include <stddef.h>
#include <stdint.h>

int rubisco_mobile_pairs(
    int64_t n, int64_t first, int64_t stop, const int64_t *moving,
    const unsigned char *is_moving, const int64_t *offsets,
    const int64_t *excluded, const double *xyz, const double *q,
    const double *sigma, const double *sqrt_epsilon, double coulomb_constant,
    double *energy, double *forces)
{
    double total = 0.0;
    for (int64_t row = first; row < stop; ++row) {
        const int64_t i = moving[row];
        const double xi = xyz[3*i], yi = xyz[3*i+1], zi = xyz[3*i+2];
        const double qi = coulomb_constant*q[i], si = sigma[i];
        const double ei = 4.0*sqrt_epsilon[i];
        double fx = 0.0, fy = 0.0, fz = 0.0;
        int64_t exception = offsets[row];
        const int64_t exception_stop = offsets[row+1];
        for (int64_t j = 0; j < n; ++j) {
            if (exception < exception_stop && excluded[exception] == j) {
                ++exception;
                continue;
            }
            if (is_moving[j] && j <= i) continue;
            const double dx = xi-xyz[3*j], dy = yi-xyz[3*j+1], dz = zi-xyz[3*j+2];
            const double r2 = dx*dx+dy*dy+dz*dz;
            if (!(r2 > 0.0) || !isfinite(r2)) return 1;
            const double inverse_r2 = 1.0/r2;
            const double charge = qi*q[j]/sqrt(r2);
            const double s = 0.5*(si+sigma[j]);
            const double ratio2 = s*s*inverse_r2;
            const double ratio6 = ratio2*ratio2*ratio2;
            const double epsilon4 = ei*sqrt_epsilon[j];
            const double potential = charge+epsilon4*ratio6*(ratio6-1.0);
            const double coefficient = (charge+epsilon4*ratio6*(12.0*ratio6-6.0))*inverse_r2;
            const double xforce = coefficient*dx, yforce = coefficient*dy, zforce = coefficient*dz;
            if (!isfinite(potential) || !isfinite(coefficient)) return 2;
            total += potential;
            fx += xforce; fy += yforce; fz += zforce;
            forces[3*j] -= xforce; forces[3*j+1] -= yforce; forces[3*j+2] -= zforce;
        }
        forces[3*i] += fx; forces[3*i+1] += fy; forces[3*i+2] += fz;
    }
    if (!isfinite(total)) return 3;
    *energy = total;
    return 0;
}
