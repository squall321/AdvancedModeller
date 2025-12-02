#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace kfile {

/**
 * Database output type enum
 */
enum class DatabaseType : int8_t {
    BINARY_D3PLOT = 1,
    BINARY_D3THDT = 2,
    BINARY_D3DUMP = 3,
    BINARY_RUNRSF = 4,
    BINARY_INTFOR = 5,
    GLSTAT = 10,
    MATSUM = 11,
    NODOUT = 12,
    ELOUT = 13,
    RCFORC = 14,
    SLEOUT = 15,
    NODFOR = 16,
    SECFORC = 17,
    RWFORC = 18,
    ABSTAT = 19,
    BNDOUT = 20,
    SPCFORC = 21,
    JNTFORC = 22,
    DEFORC = 23,
    OTHER = 0
};

/**
 * Database binary output settings
 * *DATABASE_BINARY_D3PLOT, *DATABASE_BINARY_D3THDT, etc.
 */
struct DatabaseBinary {
    DatabaseType type = DatabaseType::OTHER;
    double dt = 0.0;        // Output interval
    int32_t lcdt = 0;       // Load curve for output interval
    int32_t beam = 0;       // Beam integration output
    int32_t npltc = 0;      // Number of plot states to skip
    int32_t psetid = 0;     // Part set ID

    DatabaseBinary() = default;
    explicit DatabaseBinary(DatabaseType t) : type(t) {}
};

/**
 * Database ASCII output settings
 * *DATABASE_GLSTAT, *DATABASE_MATSUM, etc.
 */
struct DatabaseASCII {
    DatabaseType type = DatabaseType::OTHER;
    double dt = 0.0;        // Output interval
    int32_t lcdt = 0;       // Load curve for output interval
    int32_t binary = 0;     // Binary database type
    int32_t lcur = 0;       // Load curve ID
    int32_t ioopt = 0;      // I/O option

    DatabaseASCII() = default;
    explicit DatabaseASCII(DatabaseType t) : type(t) {}
};

/**
 * Database history node
 * *DATABASE_HISTORY_NODE
 */
struct DatabaseHistoryNode {
    std::vector<int32_t> node_ids;
    std::string title;

    void add_node(int32_t nid) { node_ids.push_back(nid); }
    size_t num_nodes() const { return node_ids.size(); }
};

/**
 * Database history element (shell/solid/beam)
 * *DATABASE_HISTORY_SHELL, *DATABASE_HISTORY_SOLID, *DATABASE_HISTORY_BEAM
 */
struct DatabaseHistoryElement {
    std::vector<int32_t> element_ids;
    std::string title;
    int8_t element_type = 0; // 1=shell, 2=solid, 3=beam

    void add_element(int32_t eid) { element_ids.push_back(eid); }
    size_t num_elements() const { return element_ids.size(); }
};

/**
 * Database cross section output
 * *DATABASE_CROSS_SECTION_SET, *DATABASE_CROSS_SECTION_PLANE
 */
struct DatabaseCrossSection {
    int32_t csid = 0;       // Cross section ID
    std::string title;
    int32_t psid = 0;       // Part set ID
    int32_t ssid = 0;       // Segment set ID
    int32_t tsid = 0;       // Thick shell set ID
    int32_t dsid = 0;       // Discrete element set ID
    // For PLANE definition
    double xct = 0.0, yct = 0.0, zct = 0.0;  // Center coordinates
    double xch = 0.0, ych = 0.0, zch = 0.0;  // Point on cross section
    int32_t id = 0;
    int32_t itype = 0;      // Type: 0=set, 1=plane

    DatabaseCrossSection() = default;
};

} // namespace kfile
