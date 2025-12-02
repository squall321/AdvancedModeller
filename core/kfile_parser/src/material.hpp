#pragma once
#include <array>
#include <cstdint>
#include <string>
#include <vector>

namespace kfile {

/**
 * Material type enumeration (common types)
 */
enum class MaterialType : int8_t {
    ELASTIC = 1,                    // MAT_001
    ORTHOTROPIC_ELASTIC = 2,        // MAT_002
    PLASTIC_KINEMATIC = 3,          // MAT_003
    RIGID = 20,                     // MAT_020
    PIECEWISE_LINEAR_PLASTICITY = 24, // MAT_024
    FABRIC = 34,                    // MAT_034
    COMPOSITE_DAMAGE = 54,          // MAT_054 (ENHANCED)
    LAMINATED_COMPOSITE_FABRIC = 58, // MAT_058
    COMPOSITE_FAILURE = 59,         // MAT_059
    OTHER = 0                       // Other types
};

/**
 * LS-DYNA Material structure
 *
 * K-file format examples:
 *
 * *MAT_ELASTIC
 * $#     mid        ro         e        pr        da        db  not used
 *          1    7.85e-9     210.0       0.3       0.0       0.0       0.0       0.0
 *
 * Column widths: [10, 10, 10, 10, 10, 10, 10, 10]
 *
 * *MAT_RIGID
 * $#     mid        ro         e        pr         n    couple         m     alias
 *          1    7.85e-9     210.0       0.3       0.0       0.0       0.0
 * $#     cmo      con1      con2        a1        a2        a3        v1        v2
 *        1.0       4.0       7.0       0.0       0.0       0.0       0.0       0.0
 * $#      v3       lco
 *        0.0         0
 *
 * *MAT_PIECEWISE_LINEAR_PLASTICITY
 * $#     mid        ro         e        pr      sigy      etan      fail      tdel
 *          1    7.85e-9     210.0       0.3     0.235       0.0      1.05       0.0
 * $#       c         p      lcss      lcsr        vp
 *        0.0       0.0         0         0       0.0       0.0       0.0       0.0
 * ... (more cards)
 *
 * *MAT_ORTHOTROPIC_ELASTIC
 * $#     mid        ro        ea        eb        ec      prba      prca      prcb
 *          1    7.85e-9     210.0     210.0     210.0       0.3       0.3       0.3
 * $#     gab       gbc       gca      aopt         g      sigf
 *       80.0      80.0      80.0       0.0       0.0       0.0
 *
 * *MAT_COMPOSITE_DAMAGE (054/055)
 * $#     mid        ro        ea        eb        (ec)      prba      tau1      gamma1
 *          1    1.8e-9    130.0e3     9.0e3       0.0      0.02       0.0       0.0
 * $#     gab       gbc       gca      kfail      aopt      maxp
 *      5.2e3     3.0e3     5.2e3       0.0       0.0       0.0       0.0       0.0
 * ... (more cards for strengths)
 *
 * For flexibility, we store common fields explicitly and raw card data for all cards.
 */
struct Material {
    int32_t mid;                    // Material ID
    MaterialType type;              // Material type enum
    std::string type_name;          // Raw type name (e.g., "ELASTIC", "RIGID", "054")

    // Common material properties (Card 1 - almost all materials share these)
    double ro;                      // Mass density
    double e;                       // Young's modulus (E or EA for orthotropic)
    double pr;                      // Poisson's ratio (PR or PRBA for orthotropic)

    // Elastic/Orthotropic properties
    double eb;                      // Young's modulus in b-direction (orthotropic)
    double ec;                      // Young's modulus in c-direction (orthotropic)
    double prca;                    // Poisson's ratio CA
    double prcb;                    // Poisson's ratio CB
    double gab;                     // Shear modulus AB
    double gbc;                     // Shear modulus BC
    double gca;                     // Shear modulus CA

    // Plasticity properties
    double sigy;                    // Yield stress
    double etan;                    // Tangent modulus
    double fail;                    // Failure strain
    double tdel;                    // Time to delete element

    // Rigid material properties
    double cmo;                     // Center of mass constraint option
    double con1;                    // First constraint parameter
    double con2;                    // Second constraint parameter

    // Composite strength properties (MAT_054/058/059)
    double xc;                      // Longitudinal compressive strength
    double xt;                      // Longitudinal tensile strength
    double yc;                      // Transverse compressive strength
    double yt;                      // Transverse tensile strength
    double sc;                      // Shear strength

    // Additional options
    int32_t aopt;                   // Material axes option
    int32_t macf;                   // Material axes change flag

    // Raw card data for maximum flexibility
    // Each card is stored as a vector of doubles (up to 8 values per card)
    std::vector<std::vector<double>> cards;

    // Number of cards parsed
    int32_t cards_parsed;

    // Title (for _TITLE option)
    std::string title;

    Material()
        : mid(0), type(MaterialType::OTHER), type_name("")
        , ro(0.0), e(0.0), pr(0.0)
        , eb(0.0), ec(0.0), prca(0.0), prcb(0.0)
        , gab(0.0), gbc(0.0), gca(0.0)
        , sigy(0.0), etan(0.0), fail(0.0), tdel(0.0)
        , cmo(0.0), con1(0.0), con2(0.0)
        , xc(0.0), xt(0.0), yc(0.0), yt(0.0), sc(0.0)
        , aopt(0), macf(0)
        , cards_parsed(0), title("") {}

    Material(int32_t mid, MaterialType type)
        : mid(mid), type(type), type_name("")
        , ro(0.0), e(0.0), pr(0.0)
        , eb(0.0), ec(0.0), prca(0.0), prcb(0.0)
        , gab(0.0), gbc(0.0), gca(0.0)
        , sigy(0.0), etan(0.0), fail(0.0), tdel(0.0)
        , cmo(0.0), con1(0.0), con2(0.0)
        , xc(0.0), xt(0.0), yc(0.0), yt(0.0), sc(0.0)
        , aopt(0), macf(0)
        , cards_parsed(0), title("") {}

    // Get a value from a specific card and column (0-indexed)
    double get_card_value(size_t card_idx, size_t col_idx) const {
        if (card_idx < cards.size() && col_idx < cards[card_idx].size()) {
            return cards[card_idx][col_idx];
        }
        return 0.0;
    }

    // Get number of cards stored
    size_t num_cards() const {
        return cards.size();
    }
};

} // namespace kfile
