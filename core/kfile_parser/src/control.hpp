#pragma once

#include <cstdint>
#include <string>

namespace kfile {

/**
 * Control termination settings
 * *CONTROL_TERMINATION
 */
struct ControlTermination {
    double endtim = 0.0;    // Termination time
    double endcyc = 0.0;    // Termination cycle
    double dtmin = 0.0;     // Minimum time step
    double endeng = 0.0;    // Energy ratio for termination
    double endmas = 0.0;    // Mass ratio for termination
    int32_t nosol = 0;      // No solution flag

    ControlTermination() = default;
};

/**
 * Control timestep settings
 * *CONTROL_TIMESTEP
 */
struct ControlTimestep {
    double dtinit = 0.0;    // Initial time step
    double tssfac = 0.9;    // Time step scale factor
    int32_t isdo = 0;       // Shell time step option
    double tslimt = 0.0;    // Shell element time step limit
    double dt2ms = 0.0;     // Time step for mass scaling
    int32_t lctm = 0;       // Load curve for time step
    int32_t erode = 0;      // Erosion flag
    int32_t ms1st = 0;      // Mass scaling 1st cycle flag

    ControlTimestep() = default;
};

/**
 * Control energy settings
 * *CONTROL_ENERGY
 */
struct ControlEnergy {
    int32_t hgen = 2;       // Hourglass energy
    int32_t rwen = 2;       // Rigid wall energy
    int32_t slnten = 2;     // Sliding interface energy
    int32_t rylen = 2;      // Rayleigh energy dissipation

    ControlEnergy() = default;
};

/**
 * Control output settings
 * *CONTROL_OUTPUT
 */
struct ControlOutput {
    int32_t npopt = 0;      // Print suppression option
    int32_t netefm = 0;     // Energy file options
    int32_t nflcit = 0;     // Flush interval
    int32_t nprint = 0;     // Print frequency
    int32_t ikedit = 0;     // Edit frequency
    int32_t iflush = 5000;  // Flush interval
    int32_t iprtf = 0;      // Print frequency flag
    int32_t ierode = 0;     // Eroded element output

    ControlOutput() = default;
};

/**
 * Control shell settings
 * *CONTROL_SHELL
 */
struct ControlShell {
    double wrpang = 20.0;   // Shell warpage angle
    int32_t esort = 0;      // Element sort option
    int32_t irnxx = -1;     // Shell normal update
    int32_t istupd = 0;     // Shell thickness update
    int32_t theory = 2;     // Shell theory type
    int32_t bwc = 2;        // Warping stiffness
    int32_t miter = 1;      // Membrane iteration
    int32_t proj = 0;       // Projection method

    ControlShell() = default;
};

/**
 * Control contact settings
 * *CONTROL_CONTACT
 */
struct ControlContact {
    double slsfac = 0.1;    // Slave penalty scale
    double rwpnal = 0.0;    // Rigid wall penalty
    int32_t islchk = 1;     // Initial penetration check
    int32_t shlthk = 0;     // Shell thickness
    int32_t penopt = 1;     // Penetration option
    double thkchg = 0;      // Shell thickness change
    int32_t otefm = 0;      // Optional tie enforcement
    int32_t enmass = 0;     // Extra nodes for mass

    ControlContact() = default;
};

/**
 * Control hourglass settings
 * *CONTROL_HOURGLASS
 */
struct ControlHourglass {
    int32_t ihq = 1;        // Hourglass type
    double qh = 0.1;        // Hourglass coefficient

    ControlHourglass() = default;
};

/**
 * Control bulk viscosity settings
 * *CONTROL_BULK_VISCOSITY
 */
struct ControlBulkViscosity {
    double q1 = 1.5;        // Quadratic viscosity
    double q2 = 0.06;       // Linear viscosity
    int32_t type = 1;       // Viscosity type

    ControlBulkViscosity() = default;
};

} // namespace kfile
