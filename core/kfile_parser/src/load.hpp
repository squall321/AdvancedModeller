#pragma once
#include <vector>
#include <string>
#include <cstdint>

namespace kfile {

/**
 * Load type enumeration
 */
enum class LoadType : int8_t {
    NODE = 1,                       // *LOAD_NODE_*
    SEGMENT = 2,                    // *LOAD_SEGMENT
    SHELL_SET = 3,                  // *LOAD_SHELL_SET
    BODY = 4,                       // *LOAD_BODY_*
    RIGID_BODY = 5,                 // *LOAD_RIGID_BODY
    THERMAL = 6,                    // *LOAD_THERMAL_*
    OTHER = 0
};

/**
 * LS-DYNA Load Node structure
 *
 * K-file format:
 * *LOAD_NODE_POINT
 * $#     nid       dof      lcid        sf       cid        m1        m2        m3
 *          1         3         1       1.0         0         0         0         0
 *
 * *LOAD_NODE_SET
 * $#    nsid       dof      lcid        sf       cid        m1        m2        m3
 *          1         3         1       1.0         0         0         0         0
 *
 * Column widths: [10, 10, 10, 10, 10, 10, 10, 10]
 */
struct LoadNode {
    LoadType type;                  // Load type
    int32_t nid;                    // Node ID or Node Set ID
    int8_t dof;                     // DOF (1=X, 2=Y, 3=Z, etc.)
    int32_t lcid;                   // Load curve ID
    double sf;                      // Scale factor
    int32_t cid;                    // Coordinate system ID
    int32_t m1, m2, m3;             // Additional parameters
    bool is_set;                    // true if _SET variant

    // Title (for _TITLE option)
    std::string title;

    LoadNode()
        : type(LoadType::NODE), nid(0), dof(0)
        , lcid(0), sf(1.0), cid(0)
        , m1(0), m2(0), m3(0)
        , is_set(false), title("") {}
};

/**
 * LS-DYNA Load Segment structure
 *
 * K-file format:
 * *LOAD_SEGMENT
 * $#    lcid        sf        at        n1        n2        n3        n4
 *          1       1.0       0.0         1         2         3         4
 *
 * Column widths: [10, 10, 10, 10, 10, 10, 10]
 */
struct LoadSegment {
    int32_t lcid;                   // Load curve ID
    double sf;                      // Scale factor
    double at;                      // Arrival time
    int32_t n1, n2, n3, n4;         // Node IDs defining segment

    // Title (for _TITLE option)
    std::string title;

    LoadSegment()
        : lcid(0), sf(1.0), at(0.0)
        , n1(0), n2(0), n3(0), n4(0)
        , title("") {}
};

/**
 * LS-DYNA Load Body structure
 *
 * K-file format:
 * *LOAD_BODY_X (or _Y, _Z)
 * $#    lcid        sf      lciddr        xc        yc        zc       cid
 *          1       9.8         0       0.0       0.0       0.0         0
 *
 * Column widths: [10, 10, 10, 10, 10, 10, 10]
 */
struct LoadBody {
    int8_t direction;               // 1=X, 2=Y, 3=Z
    int32_t lcid;                   // Load curve ID
    double sf;                      // Scale factor (e.g., gravitational acceleration)
    int32_t lciddr;                 // Load curve for dynamic relaxation
    double xc, yc, zc;              // Center of rotation (for parts option)
    int32_t cid;                    // Coordinate system ID

    LoadBody()
        : direction(0), lcid(0), sf(0.0), lciddr(0)
        , xc(0.0), yc(0.0), zc(0.0), cid(0) {}
};

} // namespace kfile
