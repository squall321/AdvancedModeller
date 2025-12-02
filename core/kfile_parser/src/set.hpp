#pragma once
#include <vector>
#include <array>
#include <cstdint>
#include <string>

namespace kfile {

/**
 * Set type enumeration
 */
enum class SetType : int8_t {
    NODE_LIST = 0,
    PART_LIST = 1,
    SEGMENT = 2,
    SHELL = 3,
    SOLID = 4
};

/**
 * LS-DYNA Set structure (generic for all set types)
 *
 * K-file formats:
 *
 * *SET_NODE_LIST / *SET_PART_LIST / *SET_SHELL / *SET_SOLID:
 * $#     sid       da1       da2       da3       da4    solver
 *          1       0.0       0.0       0.0       0.0MECH
 * $#    nid1      nid2      nid3      nid4      nid5      nid6      nid7      nid8
 *          1         2         3         4         5         6         7         8
 *
 * Header: [10, 10, 10, 10, 10, 10]
 * Data: [10x8] repeated
 *
 * *SET_SEGMENT:
 * $#     sid       da1       da2       da3       da4    solver
 *          1       0.0       0.0       0.0       0.0MECH
 * $#      n1        n2        n3        n4
 *          1         2         3         4
 *
 * Header: [10, 10, 10, 10, 10, 10]
 * Data: [10x4] repeated (4 nodes per segment)
 */
struct Set {
    int32_t sid;                // Set ID
    SetType type;               // Set type
    double da1, da2, da3, da4;  // DA values (usually unused)
    std::string solver;         // Solver option (MECH, THEM, etc.)

    // For NODE_LIST, PART_LIST, SHELL, SOLID: list of IDs
    std::vector<int32_t> ids;

    // For SEGMENT: list of segments (each segment has 4 node IDs)
    std::vector<std::array<int32_t, 4>> segments;

    Set() : sid(0), type(SetType::NODE_LIST),
            da1(0.0), da2(0.0), da3(0.0), da4(0.0),
            solver("MECH") {}

    Set(int32_t sid, SetType type)
        : sid(sid), type(type),
          da1(0.0), da2(0.0), da3(0.0), da4(0.0),
          solver("MECH") {}

    // Get count of items in set
    size_t count() const {
        if (type == SetType::SEGMENT) {
            return segments.size();
        }
        return ids.size();
    }

    // Add ID to the set (for NODE_LIST, PART_LIST, SHELL, SOLID)
    void add_id(int32_t id) {
        if (id > 0) {  // 0 means unused slot
            ids.push_back(id);
        }
    }

    // Add segment (for SET_SEGMENT)
    void add_segment(int32_t n1, int32_t n2, int32_t n3, int32_t n4) {
        if (n1 > 0 || n2 > 0 || n3 > 0 || n4 > 0) {
            segments.push_back({n1, n2, n3, n4});
        }
    }
};

} // namespace kfile
