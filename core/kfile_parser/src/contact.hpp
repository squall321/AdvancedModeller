#pragma once
#include <cstdint>
#include <string>

namespace kfile {

/**
 * Contact type enumeration
 * Common LS-DYNA contact types
 */
enum class ContactType : int8_t {
    AUTOMATIC_SINGLE_SURFACE = 0,
    AUTOMATIC_SURFACE_TO_SURFACE = 1,
    AUTOMATIC_NODES_TO_SURFACE = 2,
    AUTOMATIC_GENERAL = 3,
    TIED_SURFACE_TO_SURFACE = 4,
    TIED_NODES_TO_SURFACE = 5,
    TIED_SHELL_EDGE_TO_SURFACE = 6,
    SURFACE_TO_SURFACE = 7,
    NODES_TO_SURFACE = 8,
    OTHER = 99
};

/**
 * LS-DYNA Contact structure
 *
 * K-file format (example for AUTOMATIC_SURFACE_TO_SURFACE):
 *
 * *CONTACT_AUTOMATIC_SURFACE_TO_SURFACE
 * $#    ssid      msid     sstyp     mstyp    sboxid    mboxid       spr       mpr
 *          1         2         0         0         0         0         0         0
 * $#      fs        fd        dc        vc       vdc    penchk        bt        dt
 *       0.0       0.0       0.0       0.0       0.0         0       0.0     1e+20
 * $#     sfs       sfm       sst       mst      sfst      sfmt       fsf       vsf
 *       1.0       1.0       0.0       0.0       1.0       1.0       1.0       1.0
 *
 * Card 1: [10, 10, 10, 10, 10, 10, 10, 10]
 * Card 2: [10, 10, 10, 10, 10, 10, 10, 10]
 * Card 3: [10, 10, 10, 10, 10, 10, 10, 10]
 */
struct Contact {
    // Contact type
    ContactType type;
    std::string type_name;      // Full keyword name (e.g., "AUTOMATIC_SURFACE_TO_SURFACE")

    // Card 1: Required for all contacts
    int32_t ssid;               // Slave segment set ID
    int32_t msid;               // Master segment set ID
    int32_t sstyp;              // Slave surface type (0=segment set, 1=part set, 2=part ID, 3=node set)
    int32_t mstyp;              // Master surface type
    int32_t sboxid;             // Slave box ID (for searching)
    int32_t mboxid;             // Master box ID (for searching)
    int32_t spr;                // Include secondary (slave) in SPR output
    int32_t mpr;                // Include primary (master) in MPR output

    // Card 2: Friction/contact parameters (optional, most contacts)
    double fs;                  // Static friction coefficient
    double fd;                  // Dynamic friction coefficient
    double dc;                  // Exponential decay coefficient
    double vc;                  // Viscous friction coefficient
    double vdc;                 // Viscous damping coefficient
    int32_t penchk;             // Penetration check option
    double bt;                  // Birth time
    double dt;                  // Death time

    // Card 3: Scale factors (optional)
    double sfs;                 // Scale factor for slave penalty stiffness
    double sfm;                 // Scale factor for master penalty stiffness
    double sst;                 // Optional slave surface thickness
    double mst;                 // Optional master surface thickness
    double sfst;                // Scale factor for slave surface thickness
    double sfmt;                // Scale factor for master surface thickness
    double fsf;                 // Coulomb friction scale factor
    double vsf;                 // Viscous friction scale factor

    // Parsing state
    int8_t cards_parsed;        // Number of cards parsed (1-3)

    Contact()
        : type(ContactType::OTHER), type_name(""),
          ssid(0), msid(0), sstyp(0), mstyp(0), sboxid(0), mboxid(0), spr(0), mpr(0),
          fs(0.0), fd(0.0), dc(0.0), vc(0.0), vdc(0.0), penchk(0), bt(0.0), dt(1.0e20),
          sfs(1.0), sfm(1.0), sst(0.0), mst(0.0), sfst(1.0), sfmt(1.0), fsf(1.0), vsf(1.0),
          cards_parsed(0) {}

    Contact(ContactType type, const std::string& name)
        : type(type), type_name(name),
          ssid(0), msid(0), sstyp(0), mstyp(0), sboxid(0), mboxid(0), spr(0), mpr(0),
          fs(0.0), fd(0.0), dc(0.0), vc(0.0), vdc(0.0), penchk(0), bt(0.0), dt(1.0e20),
          sfs(1.0), sfm(1.0), sst(0.0), mst(0.0), sfst(1.0), sfmt(1.0), fsf(1.0), vsf(1.0),
          cards_parsed(0) {}
};

} // namespace kfile
