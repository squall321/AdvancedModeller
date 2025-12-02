#pragma once
#include <string>
#include <cstdint>

namespace kfile {

/**
 * LS-DYNA Part structure
 *
 * K-file format:
 * *PART
 * $# title
 * Part Name Here (80 chars max)
 * $#     pid     secid       mid     eosid      hgid      grav    adpopt      tmid
 *          1         1       100         0         0         0         0         0
 *
 * Line 1 column widths: [80]
 * Line 2 column widths: [10, 10, 10, 10, 10, 10, 10, 10]
 */
struct Part {
    std::string name;    // Part name (max 80 chars)
    int32_t pid;         // Part ID
    int32_t secid;       // Section ID
    int32_t mid;         // Material ID
    int32_t eosid;       // Equation of State ID
    int32_t hgid;        // Hourglass ID
    int32_t grav;        // Gravity load curve
    int32_t adpopt;      // Adaptive option
    int32_t tmid;        // Thermal material ID

    Part()
        : name("")
        , pid(0), secid(0), mid(0), eosid(0)
        , hgid(0), grav(0), adpopt(0), tmid(0) {}
};

} // namespace kfile
