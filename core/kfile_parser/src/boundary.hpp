#pragma once
#include <vector>
#include <string>
#include <cstdint>

namespace kfile {

/**
 * Boundary condition type enumeration
 */
enum class BoundaryType : int8_t {
    SPC_NODE = 1,                   // *BOUNDARY_SPC_NODE
    SPC_SET = 2,                    // *BOUNDARY_SPC_SET
    PRESCRIBED_MOTION_NODE = 3,     // *BOUNDARY_PRESCRIBED_MOTION_NODE
    PRESCRIBED_MOTION_SET = 4,      // *BOUNDARY_PRESCRIBED_MOTION_SET
    OTHER = 0
};

/**
 * LS-DYNA Boundary SPC (Single Point Constraint) structure
 *
 * K-file format:
 * *BOUNDARY_SPC_NODE
 * $#     nid       dof      vad
 *          1         1         0
 *
 * *BOUNDARY_SPC_SET
 * $#    nsid       cid      dofx      dofy      dofz     dofrx     dofry     dofrz
 *          1         0         1         1         1         0         0         0
 *
 * Column widths: [10, 10, 10, 10, 10, 10, 10, 10]
 */
struct BoundarySPC {
    BoundaryType type;              // SPC type
    int32_t nid;                    // Node ID (for _NODE) or Set ID (for _SET)
    int32_t cid;                    // Coordinate system ID (for _SET)

    // DOF constraints (1=constrained, 0=free)
    int8_t dofx;                    // X-translation
    int8_t dofy;                    // Y-translation
    int8_t dofz;                    // Z-translation
    int8_t dofrx;                   // X-rotation
    int8_t dofry;                   // Y-rotation
    int8_t dofrz;                   // Z-rotation

    // For _NODE format
    int8_t dof;                     // DOF code (1-7)
    int8_t vad;                     // VAD type

    // Title (for _TITLE option)
    std::string title;

    BoundarySPC()
        : type(BoundaryType::OTHER), nid(0), cid(0)
        , dofx(0), dofy(0), dofz(0)
        , dofrx(0), dofry(0), dofrz(0)
        , dof(0), vad(0), title("") {}

    BoundarySPC(BoundaryType t, int32_t id)
        : type(t), nid(id), cid(0)
        , dofx(0), dofy(0), dofz(0)
        , dofrx(0), dofry(0), dofrz(0)
        , dof(0), vad(0), title("") {}
};

/**
 * LS-DYNA Boundary Prescribed Motion structure
 *
 * K-file format:
 * *BOUNDARY_PRESCRIBED_MOTION_NODE
 * $#     nid       dof       vad      lcid        sf       vid     death     birth
 *          1         1         2         1       1.0         0       0.0       0.0
 *
 * Column widths: [10, 10, 10, 10, 10, 10, 10, 10]
 */
struct BoundaryPrescribedMotion {
    BoundaryType type;              // Prescribed motion type
    int32_t nid;                    // Node ID or Set ID
    int8_t dof;                     // DOF (1=X, 2=Y, 3=Z, etc.)
    int8_t vad;                     // VAD type (0=disp, 1=vel, 2=accel)
    int32_t lcid;                   // Load curve ID
    double sf;                      // Scale factor
    int32_t vid;                    // Vector ID for direction
    double death;                   // Death time
    double birth;                   // Birth time

    // Title (for _TITLE option)
    std::string title;

    BoundaryPrescribedMotion()
        : type(BoundaryType::OTHER), nid(0), dof(0), vad(0)
        , lcid(0), sf(1.0), vid(0)
        , death(0.0), birth(0.0), title("") {}
};

} // namespace kfile
