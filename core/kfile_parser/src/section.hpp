#pragma once
#include <array>
#include <cstdint>
#include <string>

namespace kfile {

/**
 * Section type enumeration
 */
enum class SectionType : int8_t {
    SHELL = 0,
    SOLID = 1,
    BEAM = 2
};

/**
 * LS-DYNA Section structure (Shell/Solid/Beam)
 *
 * K-file format:
 *
 * *SECTION_SHELL
 * $#   secid    elform      shrf       nip     propt   qr/irid     icomp     setyp
 *          1         2       1.0         2       1.0         0         0         1
 * $#      t1        t2        t3        t4      nloc     marea      idof    edgset
 *        1.0       1.0       1.0       1.0       0.0       0.0       0.0       0.0
 *
 * Header: [10, 10, 10, 10, 10, 10, 10, 10]
 * Data: [10, 10, 10, 10, 10, 10, 10, 10]
 *
 * *SECTION_SOLID
 * $#   secid    elform       aet
 *          1         1         0
 *
 * Header: [10, 10, 10]
 *
 * *SECTION_BEAM (simplified)
 * $#   secid    elform      shrf   qr/irid       cst     scoor
 *          1         1       1.0         0         0       0.0
 * $#      ts1       ts2       tt1       tt2     nsloc    ntloc
 *        1.0       1.0       1.0       1.0       0.0       0.0
 *
 * Header: [10, 10, 10, 10, 10, 10]
 * Data: [10, 10, 10, 10, 10, 10]
 */
struct Section {
    int32_t secid;              // Section ID
    SectionType type;           // Section type
    int32_t elform;             // Element formulation

    // Shell-specific fields
    double shrf;                // Shell shear factor
    int32_t nip;                // Number of through thickness integration points
    double propt;               // Printout options
    int32_t qr_irid;            // QR/IRID
    int32_t icomp;              // Composite section flag
    int32_t setyp;              // Section type

    // Shell thickness (T1-T4)
    std::array<double, 4> thickness;
    double nloc;                // Location of reference surface
    double marea;               // Non-structural mass per unit area
    double idof;                // DOF for rigid body motion
    double edgset;              // Edge set

    // Solid-specific fields
    int32_t aet;                // Ambient element type

    // Beam-specific fields
    double cst;                 // Cross section type
    double scoor;               // Local coordinate system
    std::array<double, 2> ts;   // Thickness in s-direction
    std::array<double, 2> tt;   // Thickness in t-direction
    double nsloc;               // s-location
    double ntloc;               // t-location

    Section()
        : secid(0), type(SectionType::SHELL), elform(0),
          shrf(1.0), nip(2), propt(1.0), qr_irid(0), icomp(0), setyp(1),
          thickness{0.0, 0.0, 0.0, 0.0}, nloc(0.0), marea(0.0), idof(0.0), edgset(0.0),
          aet(0),
          cst(0.0), scoor(0.0), ts{0.0, 0.0}, tt{0.0, 0.0}, nsloc(0.0), ntloc(0.0) {}

    Section(int32_t secid, SectionType type)
        : secid(secid), type(type), elform(0),
          shrf(1.0), nip(2), propt(1.0), qr_irid(0), icomp(0), setyp(1),
          thickness{0.0, 0.0, 0.0, 0.0}, nloc(0.0), marea(0.0), idof(0.0), edgset(0.0),
          aet(0),
          cst(0.0), scoor(0.0), ts{0.0, 0.0}, tt{0.0, 0.0}, nsloc(0.0), ntloc(0.0) {}
};

} // namespace kfile
