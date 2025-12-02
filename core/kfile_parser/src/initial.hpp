#pragma once

#include <cstdint>
#include <string>

namespace kfile {

/**
 * Initial velocity type enum
 */
enum class InitialVelocityType : int8_t {
    NODE = 1,
    SET = 2,
    GENERATION = 3,
    OTHER = 0
};

/**
 * Initial velocity for nodes
 * *INITIAL_VELOCITY, *INITIAL_VELOCITY_NODE, *INITIAL_VELOCITY_SET
 */
struct InitialVelocity {
    InitialVelocityType type = InitialVelocityType::OTHER;
    int32_t nsid = 0;       // Node/Set ID
    int32_t nsidex = 0;     // Excluded node set
    int32_t boxid = 0;      // Box ID
    int32_t irigid = 0;     // Rigid body flag
    double vx = 0.0;        // X velocity
    double vy = 0.0;        // Y velocity
    double vz = 0.0;        // Z velocity
    double vxr = 0.0;       // X rotational velocity
    double vyr = 0.0;       // Y rotational velocity
    double vzr = 0.0;       // Z rotational velocity
    // For generation
    double omega = 0.0;     // Angular velocity
    double xc = 0.0, yc = 0.0, zc = 0.0;  // Center of rotation
    double ax = 0.0, ay = 0.0, az = 0.0;  // Axis of rotation
    int8_t icid = 0;        // Coordinate ID flag

    InitialVelocity() = default;
    explicit InitialVelocity(InitialVelocityType t) : type(t) {}
};

/**
 * Initial stress for shell/solid elements
 * *INITIAL_STRESS_SHELL, *INITIAL_STRESS_SOLID
 */
struct InitialStress {
    int32_t eid = 0;        // Element ID
    int32_t nplane = 0;     // Number of integration points
    int32_t nthick = 0;     // Through thickness points
    int32_t large = 0;      // Large format flag
    int8_t nhisv = 0;       // Number of history variables
    // Stress components per integration point
    double sigxx = 0.0, sigyy = 0.0, sigzz = 0.0;
    double sigxy = 0.0, sigyz = 0.0, sigzx = 0.0;
    double eps = 0.0;       // Effective plastic strain

    InitialStress() = default;
};

/**
 * Initial foam reference geometry
 * *INITIAL_FOAM_REFERENCE_GEOMETRY
 */
struct InitialFoamReference {
    int32_t pid = 0;        // Part ID
    int32_t nid = 0;        // Node ID
    double x = 0.0, y = 0.0, z = 0.0;  // Reference coordinates

    InitialFoamReference() = default;
};

} // namespace kfile
