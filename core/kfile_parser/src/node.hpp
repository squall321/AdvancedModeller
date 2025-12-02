#pragma once
#include <cstdint>

namespace kfile {

/**
 * LS-DYNA Node structure
 *
 * K-file format:
 * *NODE
 * $#   nid               x               y               z      tc      rc
 *   123456      100.0000000      200.0000000      300.0000000       0       0
 *
 * Column widths: [8, 16, 16, 16, 8, 8]
 */
struct Node {
    int32_t nid;      // Node ID (column 0-7)
    double x, y, z;   // Coordinates (columns 8-23, 24-39, 40-55)
    int32_t tc;       // Translational constraint (column 56-63)
    int32_t rc;       // Rotational constraint (column 64-71)

    Node() : nid(0), x(0.0), y(0.0), z(0.0), tc(0), rc(0) {}

    Node(int32_t nid, double x, double y, double z, int32_t tc = 0, int32_t rc = 0)
        : nid(nid), x(x), y(y), z(z), tc(tc), rc(rc) {}
};

} // namespace kfile
