#pragma once
#include <vector>
#include <string>
#include <cstdint>
#include <utility>

namespace kfile {

/**
 * LS-DYNA Define Curve structure
 *
 * K-file format:
 * *DEFINE_CURVE
 * $#    lcid      sidr       sfa       sfo      offa      offo    dattyp
 *        1         0       1.0       1.0       0.0       0.0         0
 * $#                a1                  o1
 *                 0.0                 0.0
 *                 1.0               100.0
 *                 2.0               200.0
 *
 * Column widths: [10, 10, 10, 10, 10, 10, 10, 10] for header
 *                [20, 20] for data points
 *
 * *DEFINE_CURVE_TITLE
 * Curve Title Here
 * $# ... (same as above)
 */
struct Curve {
    int32_t lcid;                   // Load curve ID
    int32_t sidr;                   // Stress initialization by dynamic relaxation
    double sfa;                     // Scale factor for abscissa (X)
    double sfo;                     // Scale factor for ordinate (Y)
    double offa;                    // Offset for abscissa
    double offo;                    // Offset for ordinate
    int32_t dattyp;                 // Data type (0=general, 1=time)

    // Data points (abscissa, ordinate pairs)
    std::vector<std::pair<double, double>> points;

    // Title (for _TITLE option)
    std::string title;

    Curve()
        : lcid(0), sidr(0), sfa(1.0), sfo(1.0)
        , offa(0.0), offo(0.0), dattyp(0)
        , title("") {}

    Curve(int32_t id)
        : lcid(id), sidr(0), sfa(1.0), sfo(1.0)
        , offa(0.0), offo(0.0), dattyp(0)
        , title("") {}

    // Add a data point
    void add_point(double a, double o) {
        points.emplace_back(a, o);
    }

    // Get number of points
    size_t num_points() const {
        return points.size();
    }

    // Get point at index
    std::pair<double, double> get_point(size_t idx) const {
        if (idx < points.size()) {
            return points[idx];
        }
        return {0.0, 0.0};
    }
};

} // namespace kfile
