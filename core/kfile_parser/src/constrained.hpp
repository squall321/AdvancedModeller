#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace kfile {

/**
 * Constrained type enum
 */
enum class ConstrainedType : int8_t {
    NODAL_RIGID_BODY = 1,
    EXTRA_NODES = 2,
    JOINT_REVOLUTE = 3,
    JOINT_SPHERICAL = 4,
    JOINT_CYLINDRICAL = 5,
    JOINT_TRANSLATIONAL = 6,
    JOINT_UNIVERSAL = 7,
    JOINT_PLANAR = 8,
    RIGID_BODY_STOPPERS = 9,
    SPOTWELD = 10,
    GENERALIZED_WELD = 11,
    OTHER = 0
};

/**
 * Constrained nodal rigid body
 * *CONSTRAINED_NODAL_RIGID_BODY, *CONSTRAINED_NODAL_RIGID_BODY_INERTIA
 */
struct ConstrainedNodalRigidBody {
    int32_t pid = 0;        // Part ID (or rigid body ID)
    int32_t cid = 0;        // Coordinate system ID
    int32_t nsid = 0;       // Node set ID
    int32_t pnode = 0;      // Pivot node
    int32_t iprt = 0;       // Print flag
    int32_t drflag = 0;     // Dynamic relaxation flag
    int32_t rrflag = 0;     // Rerouting flag
    std::string title;
    // For _INERTIA option
    double cmo = 0.0;       // Mass
    double xc = 0.0, yc = 0.0, zc = 0.0;  // Center of mass
    double ixx = 0.0, ixy = 0.0, ixz = 0.0;
    double iyy = 0.0, iyz = 0.0, izz = 0.0;
    bool has_inertia = false;

    ConstrainedNodalRigidBody() = default;
};

/**
 * Constrained extra nodes for rigid body
 * *CONSTRAINED_EXTRA_NODES_SET, *CONSTRAINED_EXTRA_NODES_NODE
 */
struct ConstrainedExtraNodes {
    int32_t pid = 0;        // Part ID (rigid body)
    int32_t nsid = 0;       // Node set ID (for SET option)
    std::vector<int32_t> node_ids;  // Individual nodes (for NODE option)
    int32_t iflag = 0;      // Flag
    std::string title;
    bool is_set = false;    // True if SET option

    void add_node(int32_t nid) { node_ids.push_back(nid); }
    size_t num_nodes() const { return node_ids.size(); }
};

/**
 * Constrained joint (generic for various joint types)
 * *CONSTRAINED_JOINT_*
 */
struct ConstrainedJoint {
    ConstrainedType joint_type = ConstrainedType::OTHER;
    int32_t jid = 0;        // Joint ID
    int32_t n1 = 0;         // Node 1
    int32_t n2 = 0;         // Node 2
    int32_t n3 = 0;         // Node 3 (for some joint types)
    int32_t n4 = 0;         // Node 4 (for some joint types)
    int32_t n5 = 0;         // Node 5
    int32_t n6 = 0;         // Node 6
    int32_t rps = 0;        // Rigid/penalty/slide flag
    int32_t damp = 0;       // Damping flag
    double lcid = 0;        // Load curve ID for failure
    std::string title;
    // Additional parameters for joint stiffness/failure
    double stiff = 0.0;     // Joint stiffness
    double pf = 0.0;        // Penalty scale factor

    ConstrainedJoint() = default;
    explicit ConstrainedJoint(ConstrainedType t) : joint_type(t) {}
};

/**
 * Constrained spotweld
 * *CONSTRAINED_SPOTWELD
 */
struct ConstrainedSpotweld {
    int32_t n1 = 0;         // Node 1
    int32_t n2 = 0;         // Node 2
    double sn = 0.0;        // Normal strength
    double ss = 0.0;        // Shear strength
    int32_t n = 0;          // Exponent
    int32_t m = 0;          // Exponent
    double tf = 0.0;        // Failure time
    int32_t pid = 0;        // Part ID for spotweld
    double ep_fail = 0.0;   // Plastic strain at failure
    std::string title;

    ConstrainedSpotweld() = default;
};

/**
 * Constrained rigid body stoppers
 * *CONSTRAINED_RIGID_BODY_STOPPERS
 */
struct ConstrainedRigidBodyStoppers {
    int32_t pid = 0;        // Rigid body part ID
    int32_t lcmax = 0;      // Max load curve ID
    int32_t lcmin = 0;      // Min load curve ID
    int32_t dof = 0;        // Degree of freedom (1-6)
    double vmax = 0.0;      // Max stopper displacement
    double vmin = 0.0;      // Min stopper displacement
    std::string title;

    ConstrainedRigidBodyStoppers() = default;
};

} // namespace kfile
