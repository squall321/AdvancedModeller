#pragma once

#include <vector>
#include <string>
#include <unordered_map>
#include <chrono>
#include "node.hpp"
#include "part.hpp"
#include "element.hpp"
#include "set.hpp"
#include "section.hpp"
#include "contact.hpp"
#include "material.hpp"
#include "include.hpp"
#include "curve.hpp"
#include "boundary.hpp"
#include "load.hpp"
#include "control.hpp"
#include "database.hpp"
#include "initial.hpp"
#include "constrained.hpp"

namespace kfile {

/**
 * Parse result container
 */
struct ParseResult {
    // Parsed data
    std::vector<Node> nodes;
    std::vector<Part> parts;
    std::vector<Element> elements;
    std::vector<Set> sets;
    std::vector<Section> sections;
    std::vector<Contact> contacts;
    std::vector<Material> materials;
    std::vector<Include> includes;
    std::vector<Curve> curves;
    std::vector<BoundarySPC> boundary_spcs;
    std::vector<BoundaryPrescribedMotion> boundary_motions;
    std::vector<LoadNode> load_nodes;
    std::vector<LoadSegment> load_segments;
    std::vector<LoadBody> load_bodies;
    // Control keywords
    std::vector<ControlTermination> control_terminations;
    std::vector<ControlTimestep> control_timesteps;
    std::vector<ControlEnergy> control_energies;
    std::vector<ControlOutput> control_outputs;
    std::vector<ControlShell> control_shells;
    std::vector<ControlContact> control_contacts;
    std::vector<ControlHourglass> control_hourglasses;
    std::vector<ControlBulkViscosity> control_bulk_viscosities;
    // Database keywords
    std::vector<DatabaseBinary> database_binaries;
    std::vector<DatabaseASCII> database_asciis;
    std::vector<DatabaseHistoryNode> database_history_nodes;
    std::vector<DatabaseHistoryElement> database_history_elements;
    std::vector<DatabaseCrossSection> database_cross_sections;
    // Initial keywords
    std::vector<InitialVelocity> initial_velocities;
    std::vector<InitialStress> initial_stresses;
    // Constrained keywords
    std::vector<ConstrainedNodalRigidBody> constrained_nodal_rigid_bodies;
    std::vector<ConstrainedExtraNodes> constrained_extra_nodes;
    std::vector<ConstrainedJoint> constrained_joints;
    std::vector<ConstrainedSpotweld> constrained_spotwelds;

    // Fast lookup maps (id -> index in vector)
    std::unordered_map<int32_t, size_t> node_index;
    std::unordered_map<int32_t, size_t> part_index;
    std::unordered_map<int32_t, size_t> element_index;
    std::unordered_map<int32_t, size_t> set_index;
    std::unordered_map<int32_t, size_t> section_index;
    // Contact uses ssid as key for lookup
    std::unordered_map<int32_t, size_t> contact_index;
    std::unordered_map<int32_t, size_t> material_index;
    // Curve uses lcid as key
    std::unordered_map<int32_t, size_t> curve_index;

    // Statistics
    size_t total_lines = 0;
    size_t parse_time_ms = 0;
    std::vector<std::string> warnings;
    std::vector<std::string> errors;

    // Helpers
    void clear() {
        nodes.clear();
        parts.clear();
        elements.clear();
        sets.clear();
        sections.clear();
        contacts.clear();
        materials.clear();
        includes.clear();
        curves.clear();
        boundary_spcs.clear();
        boundary_motions.clear();
        load_nodes.clear();
        load_segments.clear();
        load_bodies.clear();
        control_terminations.clear();
        control_timesteps.clear();
        control_energies.clear();
        control_outputs.clear();
        control_shells.clear();
        control_contacts.clear();
        control_hourglasses.clear();
        control_bulk_viscosities.clear();
        database_binaries.clear();
        database_asciis.clear();
        database_history_nodes.clear();
        database_history_elements.clear();
        database_cross_sections.clear();
        initial_velocities.clear();
        initial_stresses.clear();
        constrained_nodal_rigid_bodies.clear();
        constrained_extra_nodes.clear();
        constrained_joints.clear();
        constrained_spotwelds.clear();
        node_index.clear();
        part_index.clear();
        element_index.clear();
        set_index.clear();
        section_index.clear();
        contact_index.clear();
        material_index.clear();
        curve_index.clear();
        warnings.clear();
        errors.clear();
        total_lines = 0;
        parse_time_ms = 0;
    }

    void build_indices() {
        node_index.clear();
        for (size_t i = 0; i < nodes.size(); ++i) {
            node_index[nodes[i].nid] = i;
        }
        part_index.clear();
        for (size_t i = 0; i < parts.size(); ++i) {
            part_index[parts[i].pid] = i;
        }
        element_index.clear();
        for (size_t i = 0; i < elements.size(); ++i) {
            element_index[elements[i].eid] = i;
        }
        set_index.clear();
        for (size_t i = 0; i < sets.size(); ++i) {
            set_index[sets[i].sid] = i;
        }
        section_index.clear();
        for (size_t i = 0; i < sections.size(); ++i) {
            section_index[sections[i].secid] = i;
        }
        contact_index.clear();
        for (size_t i = 0; i < contacts.size(); ++i) {
            contact_index[contacts[i].ssid] = i;
        }
        material_index.clear();
        for (size_t i = 0; i < materials.size(); ++i) {
            material_index[materials[i].mid] = i;
        }
        curve_index.clear();
        for (size_t i = 0; i < curves.size(); ++i) {
            curve_index[curves[i].lcid] = i;
        }
    }
};

/**
 * Parser state machine states
 */
enum class ParseState {
    IDLE,
    IN_NODE,
    IN_PART_NAME,
    IN_PART_DATA,
    IN_ELEMENT_SHELL,
    IN_ELEMENT_SOLID,
    IN_ELEMENT_BEAM,
    // Set parsing states
    IN_SET_NODE_HEADER,
    IN_SET_NODE_DATA,
    IN_SET_PART_HEADER,
    IN_SET_PART_DATA,
    IN_SET_SEGMENT_HEADER,
    IN_SET_SEGMENT_DATA,
    IN_SET_SHELL_HEADER,
    IN_SET_SHELL_DATA,
    IN_SET_SOLID_HEADER,
    IN_SET_SOLID_DATA,
    // Section parsing states
    IN_SECTION_SHELL_HEADER,
    IN_SECTION_SHELL_DATA,
    IN_SECTION_SOLID,
    IN_SECTION_BEAM_HEADER,
    IN_SECTION_BEAM_DATA,
    // Contact parsing states
    IN_CONTACT_ID,      // For _ID suffix: parse ID card first
    IN_CONTACT_TITLE,   // For _TITLE suffix: parse title line first
    IN_CONTACT_CARD1,
    IN_CONTACT_CARD2,
    IN_CONTACT_CARD3,
    // Section _TITLE states
    IN_SECTION_SHELL_TITLE,
    IN_SECTION_SOLID_TITLE,
    IN_SECTION_BEAM_TITLE,
    // Set _TITLE states
    IN_SET_TITLE,
    // Material parsing states
    IN_MATERIAL_TITLE,
    IN_MATERIAL_DATA,
    // Include parsing states
    IN_INCLUDE,
    // Curve parsing states
    IN_CURVE_TITLE,
    IN_CURVE_HEADER,
    IN_CURVE_DATA,
    // Boundary parsing states
    IN_BOUNDARY_SPC,
    IN_BOUNDARY_MOTION,
    // Load parsing states
    IN_LOAD_NODE,
    IN_LOAD_SEGMENT,
    IN_LOAD_BODY,
    // Control parsing states
    IN_CONTROL_TERMINATION,
    IN_CONTROL_TIMESTEP,
    IN_CONTROL_ENERGY,
    IN_CONTROL_OUTPUT,
    IN_CONTROL_SHELL,
    IN_CONTROL_CONTACT,
    IN_CONTROL_HOURGLASS,
    IN_CONTROL_BULK_VISCOSITY,
    // Database parsing states
    IN_DATABASE_BINARY,
    IN_DATABASE_ASCII,
    IN_DATABASE_HISTORY_NODE,
    IN_DATABASE_HISTORY_ELEMENT,
    IN_DATABASE_CROSS_SECTION,
    // Initial parsing states
    IN_INITIAL_VELOCITY,
    IN_INITIAL_VELOCITY_GENERATION,
    IN_INITIAL_STRESS,
    // Constrained parsing states
    IN_CONSTRAINED_NODAL_RIGID_BODY,
    IN_CONSTRAINED_NODAL_RIGID_BODY_INERTIA,
    IN_CONSTRAINED_EXTRA_NODES,
    IN_CONSTRAINED_JOINT,
    IN_CONSTRAINED_SPOTWELD
};

/**
 * High-performance K-file parser
 */
class KFileParser {
public:
    KFileParser();
    ~KFileParser() = default;

    // Configuration
    void set_parse_nodes(bool enabled) { parse_nodes_ = enabled; }
    void set_parse_parts(bool enabled) { parse_parts_ = enabled; }
    void set_parse_elements(bool enabled) { parse_elements_ = enabled; }
    void set_parse_sets(bool enabled) { parse_sets_ = enabled; }
    void set_parse_sections(bool enabled) { parse_sections_ = enabled; }
    void set_parse_contacts(bool enabled) { parse_contacts_ = enabled; }
    void set_parse_materials(bool enabled) { parse_materials_ = enabled; }
    void set_parse_includes(bool enabled) { parse_includes_ = enabled; }
    void set_parse_curves(bool enabled) { parse_curves_ = enabled; }
    void set_parse_boundaries(bool enabled) { parse_boundaries_ = enabled; }
    void set_parse_loads(bool enabled) { parse_loads_ = enabled; }
    void set_parse_controls(bool enabled) { parse_controls_ = enabled; }
    void set_parse_databases(bool enabled) { parse_databases_ = enabled; }
    void set_parse_initials(bool enabled) { parse_initials_ = enabled; }
    void set_parse_constraineds(bool enabled) { parse_constraineds_ = enabled; }
    void set_build_index(bool enabled) { build_index_ = enabled; }

    bool get_parse_nodes() const { return parse_nodes_; }
    bool get_parse_parts() const { return parse_parts_; }
    bool get_parse_elements() const { return parse_elements_; }
    bool get_parse_sets() const { return parse_sets_; }
    bool get_parse_sections() const { return parse_sections_; }
    bool get_parse_contacts() const { return parse_contacts_; }
    bool get_parse_materials() const { return parse_materials_; }
    bool get_parse_includes() const { return parse_includes_; }
    bool get_parse_curves() const { return parse_curves_; }
    bool get_parse_boundaries() const { return parse_boundaries_; }
    bool get_parse_loads() const { return parse_loads_; }
    bool get_parse_controls() const { return parse_controls_; }
    bool get_parse_databases() const { return parse_databases_; }
    bool get_parse_initials() const { return parse_initials_; }
    bool get_parse_constraineds() const { return parse_constraineds_; }
    bool get_build_index() const { return build_index_; }

    // Main parsing methods
    ParseResult parse_file(const std::string& filepath);
    ParseResult parse_string(const std::string& content);

    // Static parsing utilities
    static Node parse_node_line(const std::string& line);
    static Part parse_part_lines(const std::string& name_line, const std::string& data_line);
    static Element parse_element_line(const std::string& line, ElementType type);
    static Set parse_set_header(const std::string& line, SetType type);
    static void parse_set_data_line(const std::string& line, Set& set);
    static void parse_segment_data_line(const std::string& line, Set& set);

private:
    // Configuration
    bool parse_nodes_ = true;
    bool parse_parts_ = true;
    bool parse_elements_ = true;
    bool parse_sets_ = true;
    bool parse_sections_ = true;
    bool parse_contacts_ = true;
    bool parse_materials_ = true;
    bool parse_includes_ = true;
    bool parse_curves_ = true;
    bool parse_boundaries_ = true;
    bool parse_loads_ = true;
    bool parse_controls_ = true;
    bool parse_databases_ = true;
    bool parse_initials_ = true;
    bool parse_constraineds_ = true;
    bool build_index_ = true;

    // Current set being parsed (for multi-line parsing)
    Set current_set_;

    // Current section being parsed (for multi-line parsing)
    Section current_section_;

    // Current contact being parsed (for multi-line parsing)
    Contact current_contact_;

    // Current material being parsed (for multi-line parsing)
    Material current_material_;
    int32_t material_expected_cards_;

    // Current curve being parsed (for multi-line parsing)
    Curve current_curve_;

    // Current boundary being parsed
    BoundarySPC current_boundary_spc_;
    BoundaryPrescribedMotion current_boundary_motion_;

    // Current load being parsed
    LoadNode current_load_node_;
    LoadBody current_load_body_;

    // Current control being parsed
    ControlTermination current_control_termination_;
    ControlTimestep current_control_timestep_;

    // Current database being parsed
    DatabaseBinary current_database_binary_;
    DatabaseASCII current_database_ascii_;
    DatabaseHistoryNode current_database_history_node_;
    DatabaseHistoryElement current_database_history_element_;

    // Current initial being parsed
    InitialVelocity current_initial_velocity_;

    // Current constrained being parsed
    ConstrainedNodalRigidBody current_constrained_nodal_rigid_body_;
    ConstrainedExtraNodes current_constrained_extra_nodes_;
    ConstrainedJoint current_constrained_joint_;
    ConstrainedSpotweld current_constrained_spotweld_;

    // Internal parsing
    void process_line(const std::string& line, ParseState& state,
                      std::string& part_name, ParseResult& result);

    // Utility functions
    static bool is_keyword(const std::string& line);
    static bool is_comment(const std::string& line);
    static bool is_empty_or_whitespace(const std::string& line);

    // Fixed-width column parsing
    static int32_t parse_int(const std::string& line, size_t start, size_t len);
    static double parse_double(const std::string& line, size_t start, size_t len);
    static std::string parse_string_field(const std::string& line, size_t start, size_t len);

    // String utilities
    static std::string trim(const std::string& str);
    static std::string to_upper(const std::string& str);
};

} // namespace kfile
