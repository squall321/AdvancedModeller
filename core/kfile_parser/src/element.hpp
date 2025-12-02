#pragma once
#include <array>
#include <cstdint>

namespace kfile {

/**
 * Element type enumeration
 */
enum class ElementType : int8_t {
    SHELL = 0,
    SOLID = 1,
    BEAM = 2
};

/**
 * LS-DYNA Element structure (Shell/Solid/Beam)
 *
 * K-file format:
 * *ELEMENT_SHELL or *ELEMENT_SOLID
 * $#   eid     pid      n1      n2      n3      n4      n5      n6      n7      n8
 *        1       1       1       2       3       4       0       0       0       0
 * Column widths: [8, 8, 8, 8, 8, 8, 8, 8, 8, 8]
 *
 * *ELEMENT_BEAM
 * $#   eid     pid      n1      n2      n3
 *        1       1       1       2       3
 * Column widths: [8, 8, 8, 8, 8]
 */
struct Element {
    int32_t eid;                   // Element ID
    int32_t pid;                   // Part ID
    std::array<int32_t, 8> nodes;  // Node IDs (N1-N8, 0 if unused)
    ElementType type;              // Shell or Solid
    int8_t node_count;             // Actual number of nodes (3-8)

    Element()
        : eid(0), pid(0), nodes{}, type(ElementType::SHELL), node_count(0) {}

    Element(int32_t eid, int32_t pid, ElementType type)
        : eid(eid), pid(pid), nodes{}, type(type), node_count(0) {}
};

} // namespace kfile
