#include "parser.hpp"
#include <fstream>
#include <sstream>
#include <algorithm>
#include <cctype>
#include <stdexcept>

namespace kfile {

KFileParser::KFileParser() {}

ParseResult KFileParser::parse_file(const std::string& filepath) {
    std::ifstream file(filepath);
    if (!file.is_open()) {
        ParseResult result;
        result.errors.push_back("Failed to open file: " + filepath);
        return result;
    }

    std::stringstream buffer;
    buffer << file.rdbuf();
    return parse_string(buffer.str());
}

ParseResult KFileParser::parse_string(const std::string& content) {
    auto start_time = std::chrono::high_resolution_clock::now();

    ParseResult result;
    result.clear();

    // Pre-allocate for performance
    result.nodes.reserve(100000);
    result.parts.reserve(1000);
    result.elements.reserve(500000);
    result.sets.reserve(1000);
    result.sections.reserve(100);
    result.contacts.reserve(100);
    result.materials.reserve(500);
    result.curves.reserve(100);
    result.boundary_spcs.reserve(1000);
    result.load_nodes.reserve(1000);

    ParseState state = ParseState::IDLE;
    std::string part_name;

    std::istringstream stream(content);
    std::string line;
    size_t line_count = 0;

    while (std::getline(stream, line)) {
        ++line_count;
        process_line(line, state, part_name, result);
    }

    result.total_lines = line_count;

    // Save any remaining set being parsed
    if (current_set_.sid > 0 && current_set_.count() > 0) {
        result.sets.push_back(current_set_);
        current_set_ = Set();
    }

    // Save any remaining material being parsed
    if (current_material_.mid > 0) {
        result.materials.push_back(current_material_);
        current_material_ = Material();
    }

    // Save any remaining curve being parsed
    if (current_curve_.lcid > 0) {
        result.curves.push_back(current_curve_);
        current_curve_ = Curve();
    }

    // Build indices if requested
    if (build_index_) {
        result.build_indices();
    }

    auto end_time = std::chrono::high_resolution_clock::now();
    result.parse_time_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        end_time - start_time).count();

    return result;
}

void KFileParser::process_line(const std::string& line, ParseState& state,
                                std::string& part_name, ParseResult& result) {
    // Skip empty lines
    if (is_empty_or_whitespace(line)) {
        return;
    }

    // Check for keyword
    if (is_keyword(line)) {
        std::string upper_line = to_upper(line);

        if (upper_line.find("*NODE") == 0 && upper_line.find("*NODE_") == std::string::npos) {
            state = parse_nodes_ ? ParseState::IN_NODE : ParseState::IDLE;
        }
        else if (upper_line.find("*PART") == 0 && upper_line.find("*PART_") == std::string::npos) {
            state = parse_parts_ ? ParseState::IN_PART_NAME : ParseState::IDLE;
            part_name.clear();
        }
        else if (upper_line.find("*ELEMENT_SHELL") == 0) {
            state = parse_elements_ ? ParseState::IN_ELEMENT_SHELL : ParseState::IDLE;
        }
        else if (upper_line.find("*ELEMENT_SOLID") == 0) {
            state = parse_elements_ ? ParseState::IN_ELEMENT_SOLID : ParseState::IDLE;
        }
        else if (upper_line.find("*ELEMENT_BEAM") == 0) {
            state = parse_elements_ ? ParseState::IN_ELEMENT_BEAM : ParseState::IDLE;
        }
        // SET keywords
        else if (upper_line.find("*SET_NODE_LIST") == 0) {
            if (parse_sets_) {
                // Save current set if exists
                if (current_set_.sid > 0 && current_set_.count() > 0) {
                    result.sets.push_back(current_set_);
                }
                current_set_ = Set();
                current_set_.type = SetType::NODE_LIST;
                // Check for _TITLE suffix
                if (upper_line.find("_TITLE") != std::string::npos) {
                    state = ParseState::IN_SET_TITLE;
                } else {
                    state = ParseState::IN_SET_NODE_HEADER;
                }
            } else {
                state = ParseState::IDLE;
            }
        }
        else if (upper_line.find("*SET_PART_LIST") == 0) {
            if (parse_sets_) {
                if (current_set_.sid > 0 && current_set_.count() > 0) {
                    result.sets.push_back(current_set_);
                }
                current_set_ = Set();
                current_set_.type = SetType::PART_LIST;
                // Check for _TITLE suffix
                if (upper_line.find("_TITLE") != std::string::npos) {
                    state = ParseState::IN_SET_TITLE;
                } else {
                    state = ParseState::IN_SET_PART_HEADER;
                }
            } else {
                state = ParseState::IDLE;
            }
        }
        else if (upper_line.find("*SET_SEGMENT") == 0) {
            if (parse_sets_) {
                if (current_set_.sid > 0 && current_set_.count() > 0) {
                    result.sets.push_back(current_set_);
                }
                current_set_ = Set();
                current_set_.type = SetType::SEGMENT;
                // Check for _TITLE suffix
                if (upper_line.find("_TITLE") != std::string::npos) {
                    state = ParseState::IN_SET_TITLE;
                } else {
                    state = ParseState::IN_SET_SEGMENT_HEADER;
                }
            } else {
                state = ParseState::IDLE;
            }
        }
        else if (upper_line.find("*SET_SHELL") == 0) {
            if (parse_sets_) {
                if (current_set_.sid > 0 && current_set_.count() > 0) {
                    result.sets.push_back(current_set_);
                }
                current_set_ = Set();
                current_set_.type = SetType::SHELL;
                // Check for _TITLE suffix
                if (upper_line.find("_TITLE") != std::string::npos) {
                    state = ParseState::IN_SET_TITLE;
                } else {
                    state = ParseState::IN_SET_SHELL_HEADER;
                }
            } else {
                state = ParseState::IDLE;
            }
        }
        else if (upper_line.find("*SET_SOLID") == 0) {
            if (parse_sets_) {
                if (current_set_.sid > 0 && current_set_.count() > 0) {
                    result.sets.push_back(current_set_);
                }
                current_set_ = Set();
                current_set_.type = SetType::SOLID;
                // Check for _TITLE suffix
                if (upper_line.find("_TITLE") != std::string::npos) {
                    state = ParseState::IN_SET_TITLE;
                } else {
                    state = ParseState::IN_SET_SOLID_HEADER;
                }
            } else {
                state = ParseState::IDLE;
            }
        }
        // SECTION keywords
        else if (upper_line.find("*SECTION_SHELL") == 0) {
            if (parse_sections_) {
                current_section_ = Section();
                current_section_.type = SectionType::SHELL;
                // Check for _TITLE suffix
                if (upper_line.find("_TITLE") != std::string::npos) {
                    state = ParseState::IN_SECTION_SHELL_TITLE;
                } else {
                    state = ParseState::IN_SECTION_SHELL_HEADER;
                }
            } else {
                state = ParseState::IDLE;
            }
        }
        else if (upper_line.find("*SECTION_SOLID") == 0) {
            if (parse_sections_) {
                current_section_ = Section();
                current_section_.type = SectionType::SOLID;
                // Check for _TITLE suffix
                if (upper_line.find("_TITLE") != std::string::npos) {
                    state = ParseState::IN_SECTION_SOLID_TITLE;
                } else {
                    state = ParseState::IN_SECTION_SOLID;
                }
            } else {
                state = ParseState::IDLE;
            }
        }
        else if (upper_line.find("*SECTION_BEAM") == 0) {
            if (parse_sections_) {
                current_section_ = Section();
                current_section_.type = SectionType::BEAM;
                // Check for _TITLE suffix
                if (upper_line.find("_TITLE") != std::string::npos) {
                    state = ParseState::IN_SECTION_BEAM_TITLE;
                } else {
                    state = ParseState::IN_SECTION_BEAM_HEADER;
                }
            } else {
                state = ParseState::IDLE;
            }
        }
        // CONTACT keywords
        else if (upper_line.find("*CONTACT_") == 0) {
            if (parse_contacts_) {
                current_contact_ = Contact();
                // Extract contact type name from keyword
                std::string type_name = upper_line.substr(9); // After "*CONTACT_"

                // Check for _ID or _TITLE suffix and determine initial state
                bool has_id = false;
                bool has_title = false;

                // Remove any trailing options like _ID, _TITLE, etc.
                size_t option_pos = type_name.find('_');
                while (option_pos != std::string::npos) {
                    std::string suffix = type_name.substr(option_pos + 1);
                    if (suffix == "ID" || suffix.find("ID") == 0) {
                        has_id = true;
                        type_name = type_name.substr(0, option_pos);
                        break;
                    } else if (suffix == "TITLE" || suffix.find("TITLE") == 0) {
                        has_title = true;
                        type_name = type_name.substr(0, option_pos);
                        break;
                    } else if (suffix == "MPP" || suffix.find("MPP") == 0) {
                        type_name = type_name.substr(0, option_pos);
                        break;
                    }
                    option_pos = type_name.find('_', option_pos + 1);
                }
                current_contact_.type_name = type_name;

                // Determine contact type
                if (type_name.find("AUTOMATIC_SINGLE_SURFACE") == 0) {
                    current_contact_.type = ContactType::AUTOMATIC_SINGLE_SURFACE;
                } else if (type_name.find("AUTOMATIC_SURFACE_TO_SURFACE") == 0) {
                    current_contact_.type = ContactType::AUTOMATIC_SURFACE_TO_SURFACE;
                } else if (type_name.find("AUTOMATIC_NODES_TO_SURFACE") == 0) {
                    current_contact_.type = ContactType::AUTOMATIC_NODES_TO_SURFACE;
                } else if (type_name.find("AUTOMATIC_GENERAL") == 0) {
                    current_contact_.type = ContactType::AUTOMATIC_GENERAL;
                } else if (type_name.find("TIED_SURFACE_TO_SURFACE") == 0) {
                    current_contact_.type = ContactType::TIED_SURFACE_TO_SURFACE;
                } else if (type_name.find("TIED_NODES_TO_SURFACE") == 0) {
                    current_contact_.type = ContactType::TIED_NODES_TO_SURFACE;
                } else if (type_name.find("TIED_SHELL_EDGE_TO_SURFACE") == 0) {
                    current_contact_.type = ContactType::TIED_SHELL_EDGE_TO_SURFACE;
                } else if (type_name.find("SURFACE_TO_SURFACE") == 0) {
                    current_contact_.type = ContactType::SURFACE_TO_SURFACE;
                } else if (type_name.find("NODES_TO_SURFACE") == 0) {
                    current_contact_.type = ContactType::NODES_TO_SURFACE;
                } else {
                    current_contact_.type = ContactType::OTHER;
                }

                // Set initial state based on suffix
                if (has_id) {
                    state = ParseState::IN_CONTACT_ID;
                } else if (has_title) {
                    state = ParseState::IN_CONTACT_TITLE;
                } else {
                    state = ParseState::IN_CONTACT_CARD1;
                }
            } else {
                state = ParseState::IDLE;
            }
        }
        // MAT_* keywords
        else if (upper_line.find("*MAT_") == 0) {
            if (parse_materials_) {
                // Save current material if exists
                if (current_material_.mid > 0) {
                    result.materials.push_back(current_material_);
                }
                current_material_ = Material();

                // Extract material type from keyword (after *MAT_)
                std::string type_str = upper_line.substr(5);

                // Check for _TITLE suffix
                bool has_title = (type_str.find("_TITLE") != std::string::npos);
                if (has_title) {
                    size_t title_pos = type_str.find("_TITLE");
                    type_str = type_str.substr(0, title_pos);
                }

                current_material_.type_name = type_str;

                // Determine material type and expected card count
                if (type_str == "ELASTIC" || type_str == "001") {
                    current_material_.type = MaterialType::ELASTIC;
                    material_expected_cards_ = 1;
                } else if (type_str == "ORTHOTROPIC_ELASTIC" || type_str == "002") {
                    current_material_.type = MaterialType::ORTHOTROPIC_ELASTIC;
                    material_expected_cards_ = 2;
                } else if (type_str == "PLASTIC_KINEMATIC" || type_str == "003") {
                    current_material_.type = MaterialType::PLASTIC_KINEMATIC;
                    material_expected_cards_ = 1;
                } else if (type_str == "RIGID" || type_str == "020") {
                    current_material_.type = MaterialType::RIGID;
                    material_expected_cards_ = 3;
                } else if (type_str == "PIECEWISE_LINEAR_PLASTICITY" || type_str == "024") {
                    current_material_.type = MaterialType::PIECEWISE_LINEAR_PLASTICITY;
                    material_expected_cards_ = 2;
                } else if (type_str == "FABRIC" || type_str == "034") {
                    current_material_.type = MaterialType::FABRIC;
                    material_expected_cards_ = 4;
                } else if (type_str == "COMPOSITE_DAMAGE" || type_str == "054" || type_str == "055") {
                    current_material_.type = MaterialType::COMPOSITE_DAMAGE;
                    material_expected_cards_ = 6;
                } else if (type_str == "LAMINATED_COMPOSITE_FABRIC" || type_str == "058") {
                    current_material_.type = MaterialType::LAMINATED_COMPOSITE_FABRIC;
                    material_expected_cards_ = 5;
                } else if (type_str == "COMPOSITE_FAILURE" || type_str == "ENHANCED_COMPOSITE_DAMAGE" || type_str == "059") {
                    current_material_.type = MaterialType::COMPOSITE_FAILURE;
                    material_expected_cards_ = 5;
                } else {
                    current_material_.type = MaterialType::OTHER;
                    material_expected_cards_ = 10;  // Parse up to 10 cards for unknown materials
                }

                // Set initial state
                state = has_title ? ParseState::IN_MATERIAL_TITLE : ParseState::IN_MATERIAL_DATA;
            } else {
                state = ParseState::IDLE;
            }
        }
        // *INCLUDE keywords
        else if (upper_line.find("*INCLUDE") == 0) {
            if (parse_includes_) {
                bool is_path = (upper_line.find("*INCLUDE_PATH") == 0);
                bool is_relative = (upper_line.find("*INCLUDE_PATH_RELATIVE") == 0);
                // Note: For INCLUDE, we just set state - actual path is on next line
                state = ParseState::IN_INCLUDE;
            } else {
                state = ParseState::IDLE;
            }
        }
        // *DEFINE_CURVE keywords
        else if (upper_line.find("*DEFINE_CURVE") == 0) {
            if (parse_curves_) {
                // Save current curve if exists
                if (current_curve_.lcid > 0) {
                    result.curves.push_back(current_curve_);
                }
                current_curve_ = Curve();

                bool has_title = (upper_line.find("_TITLE") != std::string::npos);
                state = has_title ? ParseState::IN_CURVE_TITLE : ParseState::IN_CURVE_HEADER;
            } else {
                state = ParseState::IDLE;
            }
        }
        // *BOUNDARY_SPC keywords
        else if (upper_line.find("*BOUNDARY_SPC") == 0) {
            if (parse_boundaries_) {
                current_boundary_spc_ = BoundarySPC();
                if (upper_line.find("*BOUNDARY_SPC_SET") == 0) {
                    current_boundary_spc_.type = BoundaryType::SPC_SET;
                } else if (upper_line.find("*BOUNDARY_SPC_NODE") == 0) {
                    current_boundary_spc_.type = BoundaryType::SPC_NODE;
                } else {
                    current_boundary_spc_.type = BoundaryType::SPC_NODE;  // Default
                }
                state = ParseState::IN_BOUNDARY_SPC;
            } else {
                state = ParseState::IDLE;
            }
        }
        // *BOUNDARY_PRESCRIBED_MOTION keywords
        else if (upper_line.find("*BOUNDARY_PRESCRIBED_MOTION") == 0) {
            if (parse_boundaries_) {
                current_boundary_motion_ = BoundaryPrescribedMotion();
                if (upper_line.find("_SET") != std::string::npos) {
                    current_boundary_motion_.type = BoundaryType::PRESCRIBED_MOTION_SET;
                } else {
                    current_boundary_motion_.type = BoundaryType::PRESCRIBED_MOTION_NODE;
                }
                state = ParseState::IN_BOUNDARY_MOTION;
            } else {
                state = ParseState::IDLE;
            }
        }
        // *LOAD_NODE keywords
        else if (upper_line.find("*LOAD_NODE") == 0) {
            if (parse_loads_) {
                current_load_node_ = LoadNode();
                current_load_node_.type = LoadType::NODE;
                current_load_node_.is_set = (upper_line.find("_SET") != std::string::npos);
                state = ParseState::IN_LOAD_NODE;
            } else {
                state = ParseState::IDLE;
            }
        }
        // *LOAD_SEGMENT keyword
        else if (upper_line.find("*LOAD_SEGMENT") == 0) {
            if (parse_loads_) {
                state = ParseState::IN_LOAD_SEGMENT;
            } else {
                state = ParseState::IDLE;
            }
        }
        // *LOAD_BODY keywords
        else if (upper_line.find("*LOAD_BODY") == 0) {
            if (parse_loads_) {
                current_load_body_ = LoadBody();
                if (upper_line.find("*LOAD_BODY_X") == 0) {
                    current_load_body_.direction = 1;
                } else if (upper_line.find("*LOAD_BODY_Y") == 0) {
                    current_load_body_.direction = 2;
                } else if (upper_line.find("*LOAD_BODY_Z") == 0) {
                    current_load_body_.direction = 3;
                }
                state = ParseState::IN_LOAD_BODY;
            } else {
                state = ParseState::IDLE;
            }
        }
        // *CONTROL_TERMINATION
        else if (upper_line.find("*CONTROL_TERMINATION") == 0) {
            if (parse_controls_) {
                current_control_termination_ = ControlTermination();
                state = ParseState::IN_CONTROL_TERMINATION;
            } else {
                state = ParseState::IDLE;
            }
        }
        // *CONTROL_TIMESTEP
        else if (upper_line.find("*CONTROL_TIMESTEP") == 0) {
            if (parse_controls_) {
                current_control_timestep_ = ControlTimestep();
                state = ParseState::IN_CONTROL_TIMESTEP;
            } else {
                state = ParseState::IDLE;
            }
        }
        // *CONTROL_ENERGY
        else if (upper_line.find("*CONTROL_ENERGY") == 0) {
            if (parse_controls_) {
                state = ParseState::IN_CONTROL_ENERGY;
            } else {
                state = ParseState::IDLE;
            }
        }
        // *CONTROL_OUTPUT
        else if (upper_line.find("*CONTROL_OUTPUT") == 0) {
            if (parse_controls_) {
                state = ParseState::IN_CONTROL_OUTPUT;
            } else {
                state = ParseState::IDLE;
            }
        }
        // *CONTROL_SHELL
        else if (upper_line.find("*CONTROL_SHELL") == 0) {
            if (parse_controls_) {
                state = ParseState::IN_CONTROL_SHELL;
            } else {
                state = ParseState::IDLE;
            }
        }
        // *CONTROL_CONTACT
        else if (upper_line.find("*CONTROL_CONTACT") == 0) {
            if (parse_controls_) {
                state = ParseState::IN_CONTROL_CONTACT;
            } else {
                state = ParseState::IDLE;
            }
        }
        // *CONTROL_HOURGLASS
        else if (upper_line.find("*CONTROL_HOURGLASS") == 0) {
            if (parse_controls_) {
                state = ParseState::IN_CONTROL_HOURGLASS;
            } else {
                state = ParseState::IDLE;
            }
        }
        // *CONTROL_BULK_VISCOSITY
        else if (upper_line.find("*CONTROL_BULK_VISCOSITY") == 0) {
            if (parse_controls_) {
                state = ParseState::IN_CONTROL_BULK_VISCOSITY;
            } else {
                state = ParseState::IDLE;
            }
        }
        // *DATABASE_BINARY keywords
        else if (upper_line.find("*DATABASE_BINARY_D3PLOT") == 0) {
            if (parse_databases_) {
                current_database_binary_ = DatabaseBinary(DatabaseType::BINARY_D3PLOT);
                state = ParseState::IN_DATABASE_BINARY;
            } else {
                state = ParseState::IDLE;
            }
        }
        else if (upper_line.find("*DATABASE_BINARY_D3THDT") == 0) {
            if (parse_databases_) {
                current_database_binary_ = DatabaseBinary(DatabaseType::BINARY_D3THDT);
                state = ParseState::IN_DATABASE_BINARY;
            } else {
                state = ParseState::IDLE;
            }
        }
        // *DATABASE ASCII keywords (GLSTAT, MATSUM, NODOUT, ELOUT, RCFORC, etc.)
        else if (upper_line.find("*DATABASE_GLSTAT") == 0) {
            if (parse_databases_) {
                current_database_ascii_ = DatabaseASCII(DatabaseType::GLSTAT);
                state = ParseState::IN_DATABASE_ASCII;
            } else {
                state = ParseState::IDLE;
            }
        }
        else if (upper_line.find("*DATABASE_MATSUM") == 0) {
            if (parse_databases_) {
                current_database_ascii_ = DatabaseASCII(DatabaseType::MATSUM);
                state = ParseState::IN_DATABASE_ASCII;
            } else {
                state = ParseState::IDLE;
            }
        }
        else if (upper_line.find("*DATABASE_NODOUT") == 0) {
            if (parse_databases_) {
                current_database_ascii_ = DatabaseASCII(DatabaseType::NODOUT);
                state = ParseState::IN_DATABASE_ASCII;
            } else {
                state = ParseState::IDLE;
            }
        }
        else if (upper_line.find("*DATABASE_ELOUT") == 0) {
            if (parse_databases_) {
                current_database_ascii_ = DatabaseASCII(DatabaseType::ELOUT);
                state = ParseState::IN_DATABASE_ASCII;
            } else {
                state = ParseState::IDLE;
            }
        }
        else if (upper_line.find("*DATABASE_RCFORC") == 0) {
            if (parse_databases_) {
                current_database_ascii_ = DatabaseASCII(DatabaseType::RCFORC);
                state = ParseState::IN_DATABASE_ASCII;
            } else {
                state = ParseState::IDLE;
            }
        }
        else if (upper_line.find("*DATABASE_SECFORC") == 0) {
            if (parse_databases_) {
                current_database_ascii_ = DatabaseASCII(DatabaseType::SECFORC);
                state = ParseState::IN_DATABASE_ASCII;
            } else {
                state = ParseState::IDLE;
            }
        }
        else if (upper_line.find("*DATABASE_SPCFORC") == 0) {
            if (parse_databases_) {
                current_database_ascii_ = DatabaseASCII(DatabaseType::SPCFORC);
                state = ParseState::IN_DATABASE_ASCII;
            } else {
                state = ParseState::IDLE;
            }
        }
        // *DATABASE_HISTORY_NODE
        else if (upper_line.find("*DATABASE_HISTORY_NODE") == 0) {
            if (parse_databases_) {
                current_database_history_node_ = DatabaseHistoryNode();
                state = ParseState::IN_DATABASE_HISTORY_NODE;
            } else {
                state = ParseState::IDLE;
            }
        }
        // *DATABASE_HISTORY_SHELL/SOLID/BEAM
        else if (upper_line.find("*DATABASE_HISTORY_SHELL") == 0) {
            if (parse_databases_) {
                current_database_history_element_ = DatabaseHistoryElement();
                current_database_history_element_.element_type = 1;
                state = ParseState::IN_DATABASE_HISTORY_ELEMENT;
            } else {
                state = ParseState::IDLE;
            }
        }
        else if (upper_line.find("*DATABASE_HISTORY_SOLID") == 0) {
            if (parse_databases_) {
                current_database_history_element_ = DatabaseHistoryElement();
                current_database_history_element_.element_type = 2;
                state = ParseState::IN_DATABASE_HISTORY_ELEMENT;
            } else {
                state = ParseState::IDLE;
            }
        }
        else if (upper_line.find("*DATABASE_HISTORY_BEAM") == 0) {
            if (parse_databases_) {
                current_database_history_element_ = DatabaseHistoryElement();
                current_database_history_element_.element_type = 3;
                state = ParseState::IN_DATABASE_HISTORY_ELEMENT;
            } else {
                state = ParseState::IDLE;
            }
        }
        // *INITIAL_VELOCITY keywords
        else if (upper_line.find("*INITIAL_VELOCITY_GENERATION") == 0) {
            if (parse_initials_) {
                current_initial_velocity_ = InitialVelocity(InitialVelocityType::GENERATION);
                state = ParseState::IN_INITIAL_VELOCITY_GENERATION;
            } else {
                state = ParseState::IDLE;
            }
        }
        else if (upper_line.find("*INITIAL_VELOCITY") == 0) {
            if (parse_initials_) {
                current_initial_velocity_ = InitialVelocity();
                if (upper_line.find("_SET") != std::string::npos) {
                    current_initial_velocity_.type = InitialVelocityType::SET;
                } else if (upper_line.find("_NODE") != std::string::npos) {
                    current_initial_velocity_.type = InitialVelocityType::NODE;
                } else {
                    current_initial_velocity_.type = InitialVelocityType::NODE;  // Default
                }
                state = ParseState::IN_INITIAL_VELOCITY;
            } else {
                state = ParseState::IDLE;
            }
        }
        // *CONSTRAINED_NODAL_RIGID_BODY
        else if (upper_line.find("*CONSTRAINED_NODAL_RIGID_BODY") == 0) {
            if (parse_constraineds_) {
                current_constrained_nodal_rigid_body_ = ConstrainedNodalRigidBody();
                if (upper_line.find("_INERTIA") != std::string::npos) {
                    current_constrained_nodal_rigid_body_.has_inertia = true;
                    state = ParseState::IN_CONSTRAINED_NODAL_RIGID_BODY_INERTIA;
                } else {
                    state = ParseState::IN_CONSTRAINED_NODAL_RIGID_BODY;
                }
            } else {
                state = ParseState::IDLE;
            }
        }
        // *CONSTRAINED_EXTRA_NODES
        else if (upper_line.find("*CONSTRAINED_EXTRA_NODES") == 0) {
            if (parse_constraineds_) {
                current_constrained_extra_nodes_ = ConstrainedExtraNodes();
                current_constrained_extra_nodes_.is_set = (upper_line.find("_SET") != std::string::npos);
                state = ParseState::IN_CONSTRAINED_EXTRA_NODES;
            } else {
                state = ParseState::IDLE;
            }
        }
        // *CONSTRAINED_JOINT keywords
        else if (upper_line.find("*CONSTRAINED_JOINT") == 0) {
            if (parse_constraineds_) {
                current_constrained_joint_ = ConstrainedJoint();
                if (upper_line.find("_REVOLUTE") != std::string::npos) {
                    current_constrained_joint_.joint_type = ConstrainedType::JOINT_REVOLUTE;
                } else if (upper_line.find("_SPHERICAL") != std::string::npos) {
                    current_constrained_joint_.joint_type = ConstrainedType::JOINT_SPHERICAL;
                } else if (upper_line.find("_CYLINDRICAL") != std::string::npos) {
                    current_constrained_joint_.joint_type = ConstrainedType::JOINT_CYLINDRICAL;
                } else if (upper_line.find("_TRANSLATIONAL") != std::string::npos) {
                    current_constrained_joint_.joint_type = ConstrainedType::JOINT_TRANSLATIONAL;
                } else if (upper_line.find("_UNIVERSAL") != std::string::npos) {
                    current_constrained_joint_.joint_type = ConstrainedType::JOINT_UNIVERSAL;
                } else if (upper_line.find("_PLANAR") != std::string::npos) {
                    current_constrained_joint_.joint_type = ConstrainedType::JOINT_PLANAR;
                }
                state = ParseState::IN_CONSTRAINED_JOINT;
            } else {
                state = ParseState::IDLE;
            }
        }
        // *CONSTRAINED_SPOTWELD
        else if (upper_line.find("*CONSTRAINED_SPOTWELD") == 0) {
            if (parse_constraineds_) {
                current_constrained_spotweld_ = ConstrainedSpotweld();
                state = ParseState::IN_CONSTRAINED_SPOTWELD;
            } else {
                state = ParseState::IDLE;
            }
        }
        else {
            // Other keyword, save current set if parsing and reset state
            if (current_set_.sid > 0 && current_set_.count() > 0) {
                result.sets.push_back(current_set_);
                current_set_ = Set();
            }
            // Save current material if parsing
            if (current_material_.mid > 0) {
                result.materials.push_back(current_material_);
                current_material_ = Material();
            }
            // Save current curve if parsing
            if (current_curve_.lcid > 0) {
                result.curves.push_back(current_curve_);
                current_curve_ = Curve();
            }
            state = ParseState::IDLE;
        }
        return;
    }

    // Skip comments
    if (is_comment(line)) {
        return;
    }

    // Process data based on state
    switch (state) {
        case ParseState::IN_NODE: {
            try {
                Node node = parse_node_line(line);
                result.nodes.push_back(node);
            } catch (const std::exception& e) {
                result.warnings.push_back("Node parse warning: " + std::string(e.what()));
            }
            break;
        }

        case ParseState::IN_PART_NAME: {
            part_name = parse_string_field(line, 0, 80);
            state = ParseState::IN_PART_DATA;
            break;
        }

        case ParseState::IN_PART_DATA: {
            try {
                Part part = parse_part_lines(part_name, line);
                result.parts.push_back(part);
            } catch (const std::exception& e) {
                result.warnings.push_back("Part parse warning: " + std::string(e.what()));
            }
            state = ParseState::IDLE;
            break;
        }

        case ParseState::IN_ELEMENT_SHELL: {
            try {
                Element elem = parse_element_line(line, ElementType::SHELL);
                result.elements.push_back(elem);
            } catch (const std::exception& e) {
                result.warnings.push_back("Element parse warning: " + std::string(e.what()));
            }
            break;
        }

        case ParseState::IN_ELEMENT_SOLID: {
            try {
                Element elem = parse_element_line(line, ElementType::SOLID);
                result.elements.push_back(elem);
            } catch (const std::exception& e) {
                result.warnings.push_back("Element parse warning: " + std::string(e.what()));
            }
            break;
        }

        case ParseState::IN_ELEMENT_BEAM: {
            try {
                Element elem = parse_element_line(line, ElementType::BEAM);
                result.elements.push_back(elem);
            } catch (const std::exception& e) {
                result.warnings.push_back("Element parse warning: " + std::string(e.what()));
            }
            break;
        }

        // SET _TITLE state: skip title line and move to appropriate header state
        case ParseState::IN_SET_TITLE: {
            // Title is just a text line, skip it and move to header based on set type
            switch (current_set_.type) {
                case SetType::NODE_LIST:
                    state = ParseState::IN_SET_NODE_HEADER;
                    break;
                case SetType::PART_LIST:
                    state = ParseState::IN_SET_PART_HEADER;
                    break;
                case SetType::SEGMENT:
                    state = ParseState::IN_SET_SEGMENT_HEADER;
                    break;
                case SetType::SHELL:
                    state = ParseState::IN_SET_SHELL_HEADER;
                    break;
                case SetType::SOLID:
                    state = ParseState::IN_SET_SOLID_HEADER;
                    break;
            }
            break;
        }

        // SET_NODE_LIST
        case ParseState::IN_SET_NODE_HEADER: {
            try {
                current_set_ = parse_set_header(line, SetType::NODE_LIST);
                state = ParseState::IN_SET_NODE_DATA;
            } catch (const std::exception& e) {
                result.warnings.push_back("Set header parse warning: " + std::string(e.what()));
                state = ParseState::IDLE;
            }
            break;
        }
        case ParseState::IN_SET_NODE_DATA: {
            try {
                parse_set_data_line(line, current_set_);
            } catch (const std::exception& e) {
                result.warnings.push_back("Set data parse warning: " + std::string(e.what()));
            }
            break;
        }

        // SET_PART_LIST
        case ParseState::IN_SET_PART_HEADER: {
            try {
                current_set_ = parse_set_header(line, SetType::PART_LIST);
                state = ParseState::IN_SET_PART_DATA;
            } catch (const std::exception& e) {
                result.warnings.push_back("Set header parse warning: " + std::string(e.what()));
                state = ParseState::IDLE;
            }
            break;
        }
        case ParseState::IN_SET_PART_DATA: {
            try {
                parse_set_data_line(line, current_set_);
            } catch (const std::exception& e) {
                result.warnings.push_back("Set data parse warning: " + std::string(e.what()));
            }
            break;
        }

        // SET_SEGMENT
        case ParseState::IN_SET_SEGMENT_HEADER: {
            try {
                current_set_ = parse_set_header(line, SetType::SEGMENT);
                state = ParseState::IN_SET_SEGMENT_DATA;
            } catch (const std::exception& e) {
                result.warnings.push_back("Set header parse warning: " + std::string(e.what()));
                state = ParseState::IDLE;
            }
            break;
        }
        case ParseState::IN_SET_SEGMENT_DATA: {
            try {
                parse_segment_data_line(line, current_set_);
            } catch (const std::exception& e) {
                result.warnings.push_back("Segment data parse warning: " + std::string(e.what()));
            }
            break;
        }

        // SET_SHELL
        case ParseState::IN_SET_SHELL_HEADER: {
            try {
                current_set_ = parse_set_header(line, SetType::SHELL);
                state = ParseState::IN_SET_SHELL_DATA;
            } catch (const std::exception& e) {
                result.warnings.push_back("Set header parse warning: " + std::string(e.what()));
                state = ParseState::IDLE;
            }
            break;
        }
        case ParseState::IN_SET_SHELL_DATA: {
            try {
                parse_set_data_line(line, current_set_);
            } catch (const std::exception& e) {
                result.warnings.push_back("Set data parse warning: " + std::string(e.what()));
            }
            break;
        }

        // SET_SOLID
        case ParseState::IN_SET_SOLID_HEADER: {
            try {
                current_set_ = parse_set_header(line, SetType::SOLID);
                state = ParseState::IN_SET_SOLID_DATA;
            } catch (const std::exception& e) {
                result.warnings.push_back("Set header parse warning: " + std::string(e.what()));
                state = ParseState::IDLE;
            }
            break;
        }
        case ParseState::IN_SET_SOLID_DATA: {
            try {
                parse_set_data_line(line, current_set_);
            } catch (const std::exception& e) {
                result.warnings.push_back("Set data parse warning: " + std::string(e.what()));
            }
            break;
        }

        // SECTION _TITLE states: skip title line and move to header/data state
        case ParseState::IN_SECTION_SHELL_TITLE: {
            // Title is just a text line, skip it and move to header
            state = ParseState::IN_SECTION_SHELL_HEADER;
            break;
        }
        case ParseState::IN_SECTION_SOLID_TITLE: {
            // Title is just a text line, skip it and move to data
            state = ParseState::IN_SECTION_SOLID;
            break;
        }
        case ParseState::IN_SECTION_BEAM_TITLE: {
            // Title is just a text line, skip it and move to header
            state = ParseState::IN_SECTION_BEAM_HEADER;
            break;
        }

        // SECTION_SHELL (2 lines: header + data)
        case ParseState::IN_SECTION_SHELL_HEADER: {
            try {
                // Parse header: secid, elform, shrf, nip, propt, qr/irid, icomp, setyp
                current_section_.secid = parse_int(line, 0, 10);
                current_section_.elform = parse_int(line, 10, 10);
                current_section_.shrf = parse_double(line, 20, 10);
                current_section_.nip = parse_int(line, 30, 10);
                current_section_.propt = parse_double(line, 40, 10);
                current_section_.qr_irid = parse_int(line, 50, 10);
                current_section_.icomp = parse_int(line, 60, 10);
                current_section_.setyp = parse_int(line, 70, 10);
                state = ParseState::IN_SECTION_SHELL_DATA;
            } catch (const std::exception& e) {
                result.warnings.push_back("Section shell header parse warning: " + std::string(e.what()));
                state = ParseState::IDLE;
            }
            break;
        }
        case ParseState::IN_SECTION_SHELL_DATA: {
            try {
                // Parse data: t1, t2, t3, t4, nloc, marea, idof, edgset
                current_section_.thickness[0] = parse_double(line, 0, 10);
                current_section_.thickness[1] = parse_double(line, 10, 10);
                current_section_.thickness[2] = parse_double(line, 20, 10);
                current_section_.thickness[3] = parse_double(line, 30, 10);
                current_section_.nloc = parse_double(line, 40, 10);
                current_section_.marea = parse_double(line, 50, 10);
                current_section_.idof = parse_double(line, 60, 10);
                current_section_.edgset = parse_double(line, 70, 10);
                result.sections.push_back(current_section_);
                current_section_ = Section();
            } catch (const std::exception& e) {
                result.warnings.push_back("Section shell data parse warning: " + std::string(e.what()));
            }
            state = ParseState::IDLE;
            break;
        }

        // SECTION_SOLID (1 line only)
        case ParseState::IN_SECTION_SOLID: {
            try {
                // Parse: secid, elform, aet
                current_section_.secid = parse_int(line, 0, 10);
                current_section_.elform = parse_int(line, 10, 10);
                current_section_.aet = parse_int(line, 20, 10);
                result.sections.push_back(current_section_);
                current_section_ = Section();
            } catch (const std::exception& e) {
                result.warnings.push_back("Section solid parse warning: " + std::string(e.what()));
            }
            state = ParseState::IDLE;
            break;
        }

        // SECTION_BEAM (2 lines: header + data)
        case ParseState::IN_SECTION_BEAM_HEADER: {
            try {
                // Parse header: secid, elform, shrf, qr/irid, cst, scoor
                current_section_.secid = parse_int(line, 0, 10);
                current_section_.elform = parse_int(line, 10, 10);
                current_section_.shrf = parse_double(line, 20, 10);
                current_section_.qr_irid = parse_int(line, 30, 10);
                current_section_.cst = parse_double(line, 40, 10);
                current_section_.scoor = parse_double(line, 50, 10);
                state = ParseState::IN_SECTION_BEAM_DATA;
            } catch (const std::exception& e) {
                result.warnings.push_back("Section beam header parse warning: " + std::string(e.what()));
                state = ParseState::IDLE;
            }
            break;
        }
        case ParseState::IN_SECTION_BEAM_DATA: {
            try {
                // Parse data: ts1, ts2, tt1, tt2, nsloc, ntloc
                current_section_.ts[0] = parse_double(line, 0, 10);
                current_section_.ts[1] = parse_double(line, 10, 10);
                current_section_.tt[0] = parse_double(line, 20, 10);
                current_section_.tt[1] = parse_double(line, 30, 10);
                current_section_.nsloc = parse_double(line, 40, 10);
                current_section_.ntloc = parse_double(line, 50, 10);
                result.sections.push_back(current_section_);
                current_section_ = Section();
            } catch (const std::exception& e) {
                result.warnings.push_back("Section beam data parse warning: " + std::string(e.what()));
            }
            state = ParseState::IDLE;
            break;
        }

        // CONTACT _ID option: parse ID card first (cid + heading), then go to CARD1
        case ParseState::IN_CONTACT_ID: {
            // _ID card format: CID (10), HEADING (70)
            // We skip parsing cid/heading for now, just move to CARD1
            state = ParseState::IN_CONTACT_CARD1;
            break;
        }

        // CONTACT _TITLE option: parse title line, then go to CARD1
        case ParseState::IN_CONTACT_TITLE: {
            // Title is just a text line, skip it and move to CARD1
            state = ParseState::IN_CONTACT_CARD1;
            break;
        }

        // CONTACT Card 1: ssid, msid, sstyp, mstyp, sboxid, mboxid, spr, mpr
        case ParseState::IN_CONTACT_CARD1: {
            try {
                current_contact_.ssid = parse_int(line, 0, 10);
                current_contact_.msid = parse_int(line, 10, 10);
                current_contact_.sstyp = parse_int(line, 20, 10);
                current_contact_.mstyp = parse_int(line, 30, 10);
                current_contact_.sboxid = parse_int(line, 40, 10);
                current_contact_.mboxid = parse_int(line, 50, 10);
                current_contact_.spr = parse_int(line, 60, 10);
                current_contact_.mpr = parse_int(line, 70, 10);
                current_contact_.cards_parsed = 1;
                state = ParseState::IN_CONTACT_CARD2;
            } catch (const std::exception& e) {
                result.warnings.push_back("Contact card1 parse warning: " + std::string(e.what()));
                state = ParseState::IDLE;
            }
            break;
        }

        // CONTACT Card 2: fs, fd, dc, vc, vdc, penchk, bt, dt
        case ParseState::IN_CONTACT_CARD2: {
            try {
                current_contact_.fs = parse_double(line, 0, 10);
                current_contact_.fd = parse_double(line, 10, 10);
                current_contact_.dc = parse_double(line, 20, 10);
                current_contact_.vc = parse_double(line, 30, 10);
                current_contact_.vdc = parse_double(line, 40, 10);
                current_contact_.penchk = parse_int(line, 50, 10);
                current_contact_.bt = parse_double(line, 60, 10);
                current_contact_.dt = parse_double(line, 70, 10);
                current_contact_.cards_parsed = 2;
                state = ParseState::IN_CONTACT_CARD3;
            } catch (const std::exception& e) {
                result.warnings.push_back("Contact card2 parse warning: " + std::string(e.what()));
                // Still save contact with card1 data
                result.contacts.push_back(current_contact_);
                current_contact_ = Contact();
                state = ParseState::IDLE;
            }
            break;
        }

        // CONTACT Card 3: sfs, sfm, sst, mst, sfst, sfmt, fsf, vsf
        case ParseState::IN_CONTACT_CARD3: {
            try {
                current_contact_.sfs = parse_double(line, 0, 10);
                current_contact_.sfm = parse_double(line, 10, 10);
                current_contact_.sst = parse_double(line, 20, 10);
                current_contact_.mst = parse_double(line, 30, 10);
                current_contact_.sfst = parse_double(line, 40, 10);
                current_contact_.sfmt = parse_double(line, 50, 10);
                current_contact_.fsf = parse_double(line, 60, 10);
                current_contact_.vsf = parse_double(line, 70, 10);
                current_contact_.cards_parsed = 3;
                result.contacts.push_back(current_contact_);
                current_contact_ = Contact();
            } catch (const std::exception& e) {
                result.warnings.push_back("Contact card3 parse warning: " + std::string(e.what()));
                // Still save contact with card1+card2 data
                result.contacts.push_back(current_contact_);
                current_contact_ = Contact();
            }
            state = ParseState::IDLE;
            break;
        }

        // MATERIAL _TITLE state: skip title line and move to data state
        case ParseState::IN_MATERIAL_TITLE: {
            current_material_.title = trim(line);
            state = ParseState::IN_MATERIAL_DATA;
            break;
        }

        // MATERIAL data cards
        case ParseState::IN_MATERIAL_DATA: {
            try {
                // Parse all 8 fields as doubles and store in cards vector
                std::vector<double> card_values;
                for (int i = 0; i < 8; ++i) {
                    size_t start = i * 10;
                    double val = parse_double(line, start, 10);
                    card_values.push_back(val);
                }
                current_material_.cards.push_back(card_values);
                current_material_.cards_parsed++;

                // First card always contains MID, RO, E, PR (common fields)
                if (current_material_.cards_parsed == 1) {
                    current_material_.mid = static_cast<int32_t>(card_values[0]);
                    current_material_.ro = card_values[1];
                    current_material_.e = card_values[2];
                    current_material_.pr = card_values[3];

                    // For plasticity materials, card 1 may have sigy, etan, fail, tdel
                    if (current_material_.type == MaterialType::PIECEWISE_LINEAR_PLASTICITY ||
                        current_material_.type == MaterialType::PLASTIC_KINEMATIC) {
                        current_material_.sigy = card_values[4];
                        current_material_.etan = card_values[5];
                        current_material_.fail = card_values[6];
                        current_material_.tdel = card_values[7];
                    }
                    // For orthotropic/composite materials: mid, ro, ea, eb, ec, prba, prca, prcb
                    else if (current_material_.type == MaterialType::ORTHOTROPIC_ELASTIC) {
                        // e is ea (already set), eb, ec, prba in different positions
                        current_material_.eb = card_values[3];
                        current_material_.ec = card_values[4];
                        current_material_.pr = card_values[5];  // prba
                        current_material_.prca = card_values[6];
                        current_material_.prcb = card_values[7];
                    }
                    // For composite damage: mid, ro, ea, eb, (ec), prba, tau1, gamma1
                    else if (current_material_.type == MaterialType::COMPOSITE_DAMAGE ||
                             current_material_.type == MaterialType::LAMINATED_COMPOSITE_FABRIC ||
                             current_material_.type == MaterialType::COMPOSITE_FAILURE) {
                        current_material_.eb = card_values[3];
                        current_material_.ec = card_values[4];
                        current_material_.pr = card_values[5];  // prba
                    }
                }
                // Second card parsing for orthotropic/composite/rigid materials
                else if (current_material_.cards_parsed == 2) {
                    if (current_material_.type == MaterialType::ORTHOTROPIC_ELASTIC) {
                        current_material_.gab = card_values[0];
                        current_material_.gbc = card_values[1];
                        current_material_.gca = card_values[2];
                        current_material_.aopt = static_cast<int32_t>(card_values[3]);
                    } else if (current_material_.type == MaterialType::COMPOSITE_DAMAGE ||
                               current_material_.type == MaterialType::LAMINATED_COMPOSITE_FABRIC ||
                               current_material_.type == MaterialType::COMPOSITE_FAILURE) {
                        current_material_.gab = card_values[0];
                        current_material_.gbc = card_values[1];
                        current_material_.gca = card_values[2];
                    } else if (current_material_.type == MaterialType::RIGID) {
                        // RIGID card 2: cmo, con1, con2, a1, a2, a3, v1, v2
                        current_material_.cmo = card_values[0];
                        current_material_.con1 = card_values[1];
                        current_material_.con2 = card_values[2];
                    }
                }
                // Third card parsing for composite materials (strength values)
                else if (current_material_.cards_parsed == 3) {
                    if (current_material_.type == MaterialType::COMPOSITE_DAMAGE ||
                        current_material_.type == MaterialType::LAMINATED_COMPOSITE_FABRIC ||
                        current_material_.type == MaterialType::COMPOSITE_FAILURE) {
                        // Card 3: xc, xt, yc, yt, sc, ...
                        current_material_.xc = card_values[0];
                        current_material_.xt = card_values[1];
                        current_material_.yc = card_values[2];
                        current_material_.yt = card_values[3];
                        current_material_.sc = card_values[4];
                    }
                }

                // Check if we've parsed enough cards for this material type
                if (current_material_.cards_parsed >= material_expected_cards_) {
                    result.materials.push_back(current_material_);
                    current_material_ = Material();
                    state = ParseState::IDLE;
                }
            } catch (const std::exception& e) {
                result.warnings.push_back("Material data parse warning: " + std::string(e.what()));
                // Save whatever we have so far
                if (current_material_.mid > 0) {
                    result.materials.push_back(current_material_);
                    current_material_ = Material();
                }
                state = ParseState::IDLE;
            }
            break;
        }

        // INCLUDE: filepath is on this line
        case ParseState::IN_INCLUDE: {
            Include inc;
            inc.filepath = trim(line);
            inc.is_path_only = false;
            inc.is_relative = false;
            result.includes.push_back(inc);
            state = ParseState::IDLE;
            break;
        }

        // CURVE _TITLE state: read title and move to header
        case ParseState::IN_CURVE_TITLE: {
            current_curve_.title = trim(line);
            state = ParseState::IN_CURVE_HEADER;
            break;
        }

        // CURVE header: lcid, sidr, sfa, sfo, offa, offo, dattyp
        case ParseState::IN_CURVE_HEADER: {
            try {
                current_curve_.lcid = parse_int(line, 0, 10);
                current_curve_.sidr = parse_int(line, 10, 10);
                current_curve_.sfa = parse_double(line, 20, 10);
                current_curve_.sfo = parse_double(line, 30, 10);
                current_curve_.offa = parse_double(line, 40, 10);
                current_curve_.offo = parse_double(line, 50, 10);
                current_curve_.dattyp = parse_int(line, 60, 10);
                state = ParseState::IN_CURVE_DATA;
            } catch (const std::exception& e) {
                result.warnings.push_back("Curve header parse warning: " + std::string(e.what()));
                state = ParseState::IDLE;
            }
            break;
        }

        // CURVE data points: a1, o1 (20-char wide columns)
        case ParseState::IN_CURVE_DATA: {
            try {
                double a = parse_double(line, 0, 20);
                double o = parse_double(line, 20, 20);
                current_curve_.add_point(a, o);
            } catch (const std::exception& e) {
                result.warnings.push_back("Curve data parse warning: " + std::string(e.what()));
            }
            break;
        }

        // BOUNDARY_SPC: parse data line
        case ParseState::IN_BOUNDARY_SPC: {
            try {
                if (current_boundary_spc_.type == BoundaryType::SPC_SET) {
                    // SET format: nsid, cid, dofx, dofy, dofz, dofrx, dofry, dofrz
                    current_boundary_spc_.nid = parse_int(line, 0, 10);
                    current_boundary_spc_.cid = parse_int(line, 10, 10);
                    current_boundary_spc_.dofx = static_cast<int8_t>(parse_int(line, 20, 10));
                    current_boundary_spc_.dofy = static_cast<int8_t>(parse_int(line, 30, 10));
                    current_boundary_spc_.dofz = static_cast<int8_t>(parse_int(line, 40, 10));
                    current_boundary_spc_.dofrx = static_cast<int8_t>(parse_int(line, 50, 10));
                    current_boundary_spc_.dofry = static_cast<int8_t>(parse_int(line, 60, 10));
                    current_boundary_spc_.dofrz = static_cast<int8_t>(parse_int(line, 70, 10));
                } else {
                    // NODE format: nid, dof, vad
                    current_boundary_spc_.nid = parse_int(line, 0, 10);
                    current_boundary_spc_.dof = static_cast<int8_t>(parse_int(line, 10, 10));
                    current_boundary_spc_.vad = static_cast<int8_t>(parse_int(line, 20, 10));
                }
                result.boundary_spcs.push_back(current_boundary_spc_);
                current_boundary_spc_ = BoundarySPC();
            } catch (const std::exception& e) {
                result.warnings.push_back("Boundary SPC parse warning: " + std::string(e.what()));
            }
            // Continue in same state for multiple entries
            break;
        }

        // BOUNDARY_PRESCRIBED_MOTION: parse data line
        case ParseState::IN_BOUNDARY_MOTION: {
            try {
                // nid, dof, vad, lcid, sf, vid, death, birth
                current_boundary_motion_.nid = parse_int(line, 0, 10);
                current_boundary_motion_.dof = static_cast<int8_t>(parse_int(line, 10, 10));
                current_boundary_motion_.vad = static_cast<int8_t>(parse_int(line, 20, 10));
                current_boundary_motion_.lcid = parse_int(line, 30, 10);
                current_boundary_motion_.sf = parse_double(line, 40, 10);
                current_boundary_motion_.vid = parse_int(line, 50, 10);
                current_boundary_motion_.death = parse_double(line, 60, 10);
                current_boundary_motion_.birth = parse_double(line, 70, 10);
                result.boundary_motions.push_back(current_boundary_motion_);
                current_boundary_motion_ = BoundaryPrescribedMotion();
            } catch (const std::exception& e) {
                result.warnings.push_back("Boundary motion parse warning: " + std::string(e.what()));
            }
            // Continue in same state for multiple entries
            break;
        }

        // LOAD_NODE: parse data line
        case ParseState::IN_LOAD_NODE: {
            try {
                // nid, dof, lcid, sf, cid, m1, m2, m3
                current_load_node_.nid = parse_int(line, 0, 10);
                current_load_node_.dof = static_cast<int8_t>(parse_int(line, 10, 10));
                current_load_node_.lcid = parse_int(line, 20, 10);
                current_load_node_.sf = parse_double(line, 30, 10);
                current_load_node_.cid = parse_int(line, 40, 10);
                current_load_node_.m1 = parse_int(line, 50, 10);
                current_load_node_.m2 = parse_int(line, 60, 10);
                current_load_node_.m3 = parse_int(line, 70, 10);
                result.load_nodes.push_back(current_load_node_);
                current_load_node_ = LoadNode();
            } catch (const std::exception& e) {
                result.warnings.push_back("Load node parse warning: " + std::string(e.what()));
            }
            // Continue in same state for multiple entries
            break;
        }

        // LOAD_SEGMENT: parse data line
        case ParseState::IN_LOAD_SEGMENT: {
            try {
                LoadSegment seg;
                // lcid, sf, at, n1, n2, n3, n4
                seg.lcid = parse_int(line, 0, 10);
                seg.sf = parse_double(line, 10, 10);
                seg.at = parse_double(line, 20, 10);
                seg.n1 = parse_int(line, 30, 10);
                seg.n2 = parse_int(line, 40, 10);
                seg.n3 = parse_int(line, 50, 10);
                seg.n4 = parse_int(line, 60, 10);
                result.load_segments.push_back(seg);
            } catch (const std::exception& e) {
                result.warnings.push_back("Load segment parse warning: " + std::string(e.what()));
            }
            // Continue in same state for multiple entries
            break;
        }

        // LOAD_BODY: parse data line
        case ParseState::IN_LOAD_BODY: {
            try {
                // lcid, sf, lciddr, xc, yc, zc, cid
                current_load_body_.lcid = parse_int(line, 0, 10);
                current_load_body_.sf = parse_double(line, 10, 10);
                current_load_body_.lciddr = parse_int(line, 20, 10);
                current_load_body_.xc = parse_double(line, 30, 10);
                current_load_body_.yc = parse_double(line, 40, 10);
                current_load_body_.zc = parse_double(line, 50, 10);
                current_load_body_.cid = parse_int(line, 60, 10);
                result.load_bodies.push_back(current_load_body_);
                current_load_body_ = LoadBody();
            } catch (const std::exception& e) {
                result.warnings.push_back("Load body parse warning: " + std::string(e.what()));
            }
            state = ParseState::IDLE;
            break;
        }

        // CONTROL_TERMINATION: endtim, endcyc, dtmin, endeng, endmas, nosol
        case ParseState::IN_CONTROL_TERMINATION: {
            try {
                ControlTermination ctrl;
                ctrl.endtim = parse_double(line, 0, 10);
                ctrl.endcyc = parse_double(line, 10, 10);
                ctrl.dtmin = parse_double(line, 20, 10);
                ctrl.endeng = parse_double(line, 30, 10);
                ctrl.endmas = parse_double(line, 40, 10);
                ctrl.nosol = parse_int(line, 50, 10);
                result.control_terminations.push_back(ctrl);
            } catch (const std::exception& e) {
                result.warnings.push_back("Control termination parse warning: " + std::string(e.what()));
            }
            state = ParseState::IDLE;
            break;
        }

        // CONTROL_TIMESTEP: dtinit, tssfac, isdo, tslimt, dt2ms, lctm, erode, ms1st
        case ParseState::IN_CONTROL_TIMESTEP: {
            try {
                ControlTimestep ctrl;
                ctrl.dtinit = parse_double(line, 0, 10);
                ctrl.tssfac = parse_double(line, 10, 10);
                ctrl.isdo = parse_int(line, 20, 10);
                ctrl.tslimt = parse_double(line, 30, 10);
                ctrl.dt2ms = parse_double(line, 40, 10);
                ctrl.lctm = parse_int(line, 50, 10);
                ctrl.erode = parse_int(line, 60, 10);
                ctrl.ms1st = parse_int(line, 70, 10);
                result.control_timesteps.push_back(ctrl);
            } catch (const std::exception& e) {
                result.warnings.push_back("Control timestep parse warning: " + std::string(e.what()));
            }
            state = ParseState::IDLE;
            break;
        }

        // CONTROL_ENERGY: hgen, rwen, slnten, rylen
        case ParseState::IN_CONTROL_ENERGY: {
            try {
                ControlEnergy ctrl;
                ctrl.hgen = parse_int(line, 0, 10);
                ctrl.rwen = parse_int(line, 10, 10);
                ctrl.slnten = parse_int(line, 20, 10);
                ctrl.rylen = parse_int(line, 30, 10);
                result.control_energies.push_back(ctrl);
            } catch (const std::exception& e) {
                result.warnings.push_back("Control energy parse warning: " + std::string(e.what()));
            }
            state = ParseState::IDLE;
            break;
        }

        // CONTROL_OUTPUT: npopt, netefm, nflcit, nprint, ikedit, iflush, iprtf, ierode
        case ParseState::IN_CONTROL_OUTPUT: {
            try {
                ControlOutput ctrl;
                ctrl.npopt = parse_int(line, 0, 10);
                ctrl.netefm = parse_int(line, 10, 10);
                ctrl.nflcit = parse_int(line, 20, 10);
                ctrl.nprint = parse_int(line, 30, 10);
                ctrl.ikedit = parse_int(line, 40, 10);
                ctrl.iflush = parse_int(line, 50, 10);
                ctrl.iprtf = parse_int(line, 60, 10);
                ctrl.ierode = parse_int(line, 70, 10);
                result.control_outputs.push_back(ctrl);
            } catch (const std::exception& e) {
                result.warnings.push_back("Control output parse warning: " + std::string(e.what()));
            }
            state = ParseState::IDLE;
            break;
        }

        // CONTROL_SHELL: wrpang, esort, irnxx, istupd, theory, bwc, miter, proj
        case ParseState::IN_CONTROL_SHELL: {
            try {
                ControlShell ctrl;
                ctrl.wrpang = parse_double(line, 0, 10);
                ctrl.esort = parse_int(line, 10, 10);
                ctrl.irnxx = parse_int(line, 20, 10);
                ctrl.istupd = parse_int(line, 30, 10);
                ctrl.theory = parse_int(line, 40, 10);
                ctrl.bwc = parse_int(line, 50, 10);
                ctrl.miter = parse_int(line, 60, 10);
                ctrl.proj = parse_int(line, 70, 10);
                result.control_shells.push_back(ctrl);
            } catch (const std::exception& e) {
                result.warnings.push_back("Control shell parse warning: " + std::string(e.what()));
            }
            state = ParseState::IDLE;
            break;
        }

        // CONTROL_CONTACT: slsfac, rwpnal, islchk, shlthk, penopt, thkchg, otefm, enmass
        case ParseState::IN_CONTROL_CONTACT: {
            try {
                ControlContact ctrl;
                ctrl.slsfac = parse_double(line, 0, 10);
                ctrl.rwpnal = parse_double(line, 10, 10);
                ctrl.islchk = parse_int(line, 20, 10);
                ctrl.shlthk = parse_int(line, 30, 10);
                ctrl.penopt = parse_int(line, 40, 10);
                ctrl.thkchg = parse_double(line, 50, 10);
                ctrl.otefm = parse_int(line, 60, 10);
                ctrl.enmass = parse_int(line, 70, 10);
                result.control_contacts.push_back(ctrl);
            } catch (const std::exception& e) {
                result.warnings.push_back("Control contact parse warning: " + std::string(e.what()));
            }
            state = ParseState::IDLE;
            break;
        }

        // CONTROL_HOURGLASS: ihq, qh
        case ParseState::IN_CONTROL_HOURGLASS: {
            try {
                ControlHourglass ctrl;
                ctrl.ihq = parse_int(line, 0, 10);
                ctrl.qh = parse_double(line, 10, 10);
                result.control_hourglasses.push_back(ctrl);
            } catch (const std::exception& e) {
                result.warnings.push_back("Control hourglass parse warning: " + std::string(e.what()));
            }
            state = ParseState::IDLE;
            break;
        }

        // CONTROL_BULK_VISCOSITY: q1, q2, type
        case ParseState::IN_CONTROL_BULK_VISCOSITY: {
            try {
                ControlBulkViscosity ctrl;
                ctrl.q1 = parse_double(line, 0, 10);
                ctrl.q2 = parse_double(line, 10, 10);
                ctrl.type = parse_int(line, 20, 10);
                result.control_bulk_viscosities.push_back(ctrl);
            } catch (const std::exception& e) {
                result.warnings.push_back("Control bulk viscosity parse warning: " + std::string(e.what()));
            }
            state = ParseState::IDLE;
            break;
        }

        // DATABASE_BINARY: dt, lcdt, beam, npltc, psetid
        case ParseState::IN_DATABASE_BINARY: {
            try {
                current_database_binary_.dt = parse_double(line, 0, 10);
                current_database_binary_.lcdt = parse_int(line, 10, 10);
                current_database_binary_.beam = parse_int(line, 20, 10);
                current_database_binary_.npltc = parse_int(line, 30, 10);
                current_database_binary_.psetid = parse_int(line, 40, 10);
                result.database_binaries.push_back(current_database_binary_);
                current_database_binary_ = DatabaseBinary();
            } catch (const std::exception& e) {
                result.warnings.push_back("Database binary parse warning: " + std::string(e.what()));
            }
            state = ParseState::IDLE;
            break;
        }

        // DATABASE_ASCII: dt, lcdt, binary, lcur, ioopt
        case ParseState::IN_DATABASE_ASCII: {
            try {
                current_database_ascii_.dt = parse_double(line, 0, 10);
                current_database_ascii_.lcdt = parse_int(line, 10, 10);
                current_database_ascii_.binary = parse_int(line, 20, 10);
                current_database_ascii_.lcur = parse_int(line, 30, 10);
                current_database_ascii_.ioopt = parse_int(line, 40, 10);
                result.database_asciis.push_back(current_database_ascii_);
                current_database_ascii_ = DatabaseASCII();
            } catch (const std::exception& e) {
                result.warnings.push_back("Database ASCII parse warning: " + std::string(e.what()));
            }
            state = ParseState::IDLE;
            break;
        }

        // DATABASE_HISTORY_NODE: list of node IDs
        case ParseState::IN_DATABASE_HISTORY_NODE: {
            try {
                // Parse up to 8 node IDs per line (10 chars each)
                for (int i = 0; i < 8; ++i) {
                    size_t start = i * 10;
                    if (start < line.length()) {
                        int32_t nid = parse_int(line, start, 10);
                        if (nid > 0) {
                            current_database_history_node_.add_node(nid);
                        }
                    }
                }
            } catch (const std::exception& e) {
                result.warnings.push_back("Database history node parse warning: " + std::string(e.what()));
            }
            // Stay in same state for multi-line data
            break;
        }

        // DATABASE_HISTORY_ELEMENT: list of element IDs
        case ParseState::IN_DATABASE_HISTORY_ELEMENT: {
            try {
                // Parse up to 8 element IDs per line (10 chars each)
                for (int i = 0; i < 8; ++i) {
                    size_t start = i * 10;
                    if (start < line.length()) {
                        int32_t eid = parse_int(line, start, 10);
                        if (eid > 0) {
                            current_database_history_element_.add_element(eid);
                        }
                    }
                }
            } catch (const std::exception& e) {
                result.warnings.push_back("Database history element parse warning: " + std::string(e.what()));
            }
            // Stay in same state for multi-line data
            break;
        }

        // DATABASE_CROSS_SECTION: csid, psid, ssid, tsid, dsid
        case ParseState::IN_DATABASE_CROSS_SECTION: {
            try {
                DatabaseCrossSection cs;
                cs.csid = parse_int(line, 0, 10);
                cs.psid = parse_int(line, 10, 10);
                cs.ssid = parse_int(line, 20, 10);
                cs.tsid = parse_int(line, 30, 10);
                cs.dsid = parse_int(line, 40, 10);
                result.database_cross_sections.push_back(cs);
            } catch (const std::exception& e) {
                result.warnings.push_back("Database cross section parse warning: " + std::string(e.what()));
            }
            state = ParseState::IDLE;
            break;
        }

        // INITIAL_VELOCITY: nsid, nsidex, boxid, irigid, vx, vy, vz, vxr, vyr, vzr
        case ParseState::IN_INITIAL_VELOCITY: {
            try {
                current_initial_velocity_.nsid = parse_int(line, 0, 10);
                current_initial_velocity_.nsidex = parse_int(line, 10, 10);
                current_initial_velocity_.boxid = parse_int(line, 20, 10);
                current_initial_velocity_.irigid = parse_int(line, 30, 10);
                current_initial_velocity_.vx = parse_double(line, 40, 10);
                current_initial_velocity_.vy = parse_double(line, 50, 10);
                current_initial_velocity_.vz = parse_double(line, 60, 10);
                current_initial_velocity_.vxr = parse_double(line, 70, 10);
                result.initial_velocities.push_back(current_initial_velocity_);
                current_initial_velocity_ = InitialVelocity();
            } catch (const std::exception& e) {
                result.warnings.push_back("Initial velocity parse warning: " + std::string(e.what()));
            }
            state = ParseState::IDLE;
            break;
        }

        // INITIAL_VELOCITY_GENERATION: nsid, omega, vx, vy, vz, xc, yc, zc, ax, ay, az, icid
        case ParseState::IN_INITIAL_VELOCITY_GENERATION: {
            try {
                current_initial_velocity_.nsid = parse_int(line, 0, 10);
                current_initial_velocity_.omega = parse_double(line, 10, 10);
                current_initial_velocity_.vx = parse_double(line, 20, 10);
                current_initial_velocity_.vy = parse_double(line, 30, 10);
                current_initial_velocity_.vz = parse_double(line, 40, 10);
                current_initial_velocity_.xc = parse_double(line, 50, 10);
                current_initial_velocity_.yc = parse_double(line, 60, 10);
                current_initial_velocity_.zc = parse_double(line, 70, 10);
                result.initial_velocities.push_back(current_initial_velocity_);
                current_initial_velocity_ = InitialVelocity();
            } catch (const std::exception& e) {
                result.warnings.push_back("Initial velocity generation parse warning: " + std::string(e.what()));
            }
            state = ParseState::IDLE;
            break;
        }

        // INITIAL_STRESS: not implemented fully, just placeholder
        case ParseState::IN_INITIAL_STRESS: {
            // Initial stress requires complex multi-line parsing
            // Just skip for now
            state = ParseState::IDLE;
            break;
        }

        // CONSTRAINED_NODAL_RIGID_BODY: pid, cid, nsid, pnode, iprt, drflag, rrflag
        case ParseState::IN_CONSTRAINED_NODAL_RIGID_BODY: {
            try {
                current_constrained_nodal_rigid_body_.pid = parse_int(line, 0, 10);
                current_constrained_nodal_rigid_body_.cid = parse_int(line, 10, 10);
                current_constrained_nodal_rigid_body_.nsid = parse_int(line, 20, 10);
                current_constrained_nodal_rigid_body_.pnode = parse_int(line, 30, 10);
                current_constrained_nodal_rigid_body_.iprt = parse_int(line, 40, 10);
                current_constrained_nodal_rigid_body_.drflag = parse_int(line, 50, 10);
                current_constrained_nodal_rigid_body_.rrflag = parse_int(line, 60, 10);
                result.constrained_nodal_rigid_bodies.push_back(current_constrained_nodal_rigid_body_);
                current_constrained_nodal_rigid_body_ = ConstrainedNodalRigidBody();
            } catch (const std::exception& e) {
                result.warnings.push_back("Constrained nodal rigid body parse warning: " + std::string(e.what()));
            }
            state = ParseState::IDLE;
            break;
        }

        // CONSTRAINED_NODAL_RIGID_BODY_INERTIA: multi-card format
        case ParseState::IN_CONSTRAINED_NODAL_RIGID_BODY_INERTIA: {
            // Simplified: just parse basic fields, skip inertia for now
            try {
                current_constrained_nodal_rigid_body_.pid = parse_int(line, 0, 10);
                current_constrained_nodal_rigid_body_.cid = parse_int(line, 10, 10);
                current_constrained_nodal_rigid_body_.nsid = parse_int(line, 20, 10);
                current_constrained_nodal_rigid_body_.pnode = parse_int(line, 30, 10);
                result.constrained_nodal_rigid_bodies.push_back(current_constrained_nodal_rigid_body_);
                current_constrained_nodal_rigid_body_ = ConstrainedNodalRigidBody();
            } catch (const std::exception& e) {
                result.warnings.push_back("Constrained nodal rigid body inertia parse warning: " + std::string(e.what()));
            }
            state = ParseState::IDLE;
            break;
        }

        // CONSTRAINED_EXTRA_NODES: pid, nsid (for SET) or pid followed by node IDs
        case ParseState::IN_CONSTRAINED_EXTRA_NODES: {
            try {
                if (current_constrained_extra_nodes_.is_set) {
                    // SET option: pid, nsid
                    current_constrained_extra_nodes_.pid = parse_int(line, 0, 10);
                    current_constrained_extra_nodes_.nsid = parse_int(line, 10, 10);
                    result.constrained_extra_nodes.push_back(current_constrained_extra_nodes_);
                    current_constrained_extra_nodes_ = ConstrainedExtraNodes();
                    state = ParseState::IDLE;
                } else {
                    // NODE option: pid on first line, then node IDs
                    if (current_constrained_extra_nodes_.pid == 0) {
                        current_constrained_extra_nodes_.pid = parse_int(line, 0, 10);
                    } else {
                        // Parse node IDs
                        for (int i = 0; i < 8; ++i) {
                            size_t start = i * 10;
                            if (start < line.length()) {
                                int32_t nid = parse_int(line, start, 10);
                                if (nid > 0) {
                                    current_constrained_extra_nodes_.add_node(nid);
                                }
                            }
                        }
                    }
                }
            } catch (const std::exception& e) {
                result.warnings.push_back("Constrained extra nodes parse warning: " + std::string(e.what()));
            }
            break;
        }

        // CONSTRAINED_JOINT: n1, n2, n3, n4, n5, n6, rps, damp
        case ParseState::IN_CONSTRAINED_JOINT: {
            try {
                current_constrained_joint_.n1 = parse_int(line, 0, 10);
                current_constrained_joint_.n2 = parse_int(line, 10, 10);
                current_constrained_joint_.n3 = parse_int(line, 20, 10);
                current_constrained_joint_.n4 = parse_int(line, 30, 10);
                current_constrained_joint_.n5 = parse_int(line, 40, 10);
                current_constrained_joint_.n6 = parse_int(line, 50, 10);
                current_constrained_joint_.rps = parse_int(line, 60, 10);
                current_constrained_joint_.damp = parse_int(line, 70, 10);
                result.constrained_joints.push_back(current_constrained_joint_);
                current_constrained_joint_ = ConstrainedJoint();
            } catch (const std::exception& e) {
                result.warnings.push_back("Constrained joint parse warning: " + std::string(e.what()));
            }
            state = ParseState::IDLE;
            break;
        }

        // CONSTRAINED_SPOTWELD: n1, n2, sn, ss, n, m, tf
        case ParseState::IN_CONSTRAINED_SPOTWELD: {
            try {
                current_constrained_spotweld_.n1 = parse_int(line, 0, 10);
                current_constrained_spotweld_.n2 = parse_int(line, 10, 10);
                current_constrained_spotweld_.sn = parse_double(line, 20, 10);
                current_constrained_spotweld_.ss = parse_double(line, 30, 10);
                current_constrained_spotweld_.n = parse_int(line, 40, 10);
                current_constrained_spotweld_.m = parse_int(line, 50, 10);
                current_constrained_spotweld_.tf = parse_double(line, 60, 10);
                result.constrained_spotwelds.push_back(current_constrained_spotweld_);
                current_constrained_spotweld_ = ConstrainedSpotweld();
            } catch (const std::exception& e) {
                result.warnings.push_back("Constrained spotweld parse warning: " + std::string(e.what()));
            }
            state = ParseState::IDLE;
            break;
        }

        case ParseState::IDLE:
        default:
            break;
    }
}

Node KFileParser::parse_node_line(const std::string& line) {
    // Column widths: [8, 16, 16, 16, 8, 8]
    Node node;
    node.nid = parse_int(line, 0, 8);
    node.x = parse_double(line, 8, 16);
    node.y = parse_double(line, 24, 16);
    node.z = parse_double(line, 40, 16);
    node.tc = (line.length() > 56) ? parse_int(line, 56, 8) : 0;
    node.rc = (line.length() > 64) ? parse_int(line, 64, 8) : 0;
    return node;
}

Part KFileParser::parse_part_lines(const std::string& name_line, const std::string& data_line) {
    // Name: [80]
    // Data: [10, 10, 10, 10, 10, 10, 10, 10]
    Part part;
    part.name = trim(name_line.substr(0, std::min(size_t(80), name_line.length())));
    part.pid = parse_int(data_line, 0, 10);
    part.secid = parse_int(data_line, 10, 10);
    part.mid = parse_int(data_line, 20, 10);
    part.eosid = (data_line.length() > 30) ? parse_int(data_line, 30, 10) : 0;
    part.hgid = (data_line.length() > 40) ? parse_int(data_line, 40, 10) : 0;
    part.grav = (data_line.length() > 50) ? parse_int(data_line, 50, 10) : 0;
    part.adpopt = (data_line.length() > 60) ? parse_int(data_line, 60, 10) : 0;
    part.tmid = (data_line.length() > 70) ? parse_int(data_line, 70, 10) : 0;
    return part;
}

Element KFileParser::parse_element_line(const std::string& line, ElementType type) {
    // Column widths: [8, 8, 8, 8, 8, 8, 8, 8, 8, 8]
    Element elem;
    elem.type = type;
    elem.eid = parse_int(line, 0, 8);
    elem.pid = parse_int(line, 8, 8);

    // Parse node IDs
    int8_t count = 0;
    for (int i = 0; i < 8; ++i) {
        size_t start = 16 + i * 8;
        if (start < line.length()) {
            int32_t nid = parse_int(line, start, 8);
            elem.nodes[i] = nid;
            if (nid > 0) count = i + 1;
        } else {
            elem.nodes[i] = 0;
        }
    }
    elem.node_count = (count >= 3) ? count : 0;

    return elem;
}

bool KFileParser::is_keyword(const std::string& line) {
    if (line.empty()) return false;
    return line[0] == '*';
}

bool KFileParser::is_comment(const std::string& line) {
    if (line.empty()) return false;
    return line[0] == '$';
}

bool KFileParser::is_empty_or_whitespace(const std::string& line) {
    return std::all_of(line.begin(), line.end(), [](unsigned char c) {
        return std::isspace(c);
    });
}

int32_t KFileParser::parse_int(const std::string& line, size_t start, size_t len) {
    if (start >= line.length()) return 0;
    size_t actual_len = std::min(len, line.length() - start);
    std::string field = line.substr(start, actual_len);

    // Trim whitespace
    field = trim(field);
    if (field.empty()) return 0;

    try {
        return std::stoi(field);
    } catch (...) {
        return 0;
    }
}

double KFileParser::parse_double(const std::string& line, size_t start, size_t len) {
    if (start >= line.length()) return 0.0;
    size_t actual_len = std::min(len, line.length() - start);
    std::string field = line.substr(start, actual_len);

    // Trim whitespace
    field = trim(field);
    if (field.empty()) return 0.0;

    try {
        return std::stod(field);
    } catch (...) {
        return 0.0;
    }
}

std::string KFileParser::parse_string_field(const std::string& line, size_t start, size_t len) {
    if (start >= line.length()) return "";
    size_t actual_len = std::min(len, line.length() - start);
    return trim(line.substr(start, actual_len));
}

std::string KFileParser::trim(const std::string& str) {
    auto start = std::find_if_not(str.begin(), str.end(), [](unsigned char c) {
        return std::isspace(c);
    });
    auto end = std::find_if_not(str.rbegin(), str.rend(), [](unsigned char c) {
        return std::isspace(c);
    }).base();

    return (start < end) ? std::string(start, end) : "";
}

std::string KFileParser::to_upper(const std::string& str) {
    std::string result = str;
    std::transform(result.begin(), result.end(), result.begin(),
                   [](unsigned char c) { return std::toupper(c); });
    return result;
}

Set KFileParser::parse_set_header(const std::string& line, SetType type) {
    // Header format: [10, 10, 10, 10, 10, 10]
    // $#     sid       da1       da2       da3       da4    solver
    //          1       0.0       0.0       0.0       0.0MECH
    Set set;
    set.type = type;
    set.sid = parse_int(line, 0, 10);
    set.da1 = parse_double(line, 10, 10);
    set.da2 = parse_double(line, 20, 10);
    set.da3 = parse_double(line, 30, 10);
    set.da4 = parse_double(line, 40, 10);

    // Parse solver field (last 10 chars, may contain MECH, THEM, etc.)
    if (line.length() > 50) {
        set.solver = trim(parse_string_field(line, 50, 10));
    }

    return set;
}

void KFileParser::parse_set_data_line(const std::string& line, Set& set) {
    // Data format: [10x8] - 8 IDs per line
    // $#    nid1      nid2      nid3      nid4      nid5      nid6      nid7      nid8
    //          1         2         3         4         5         6         7         8
    for (int i = 0; i < 8; ++i) {
        size_t start = i * 10;
        if (start < line.length()) {
            int32_t id = parse_int(line, start, 10);
            set.add_id(id);  // add_id ignores 0 values
        }
    }
}

void KFileParser::parse_segment_data_line(const std::string& line, Set& set) {
    // Segment data format: [10x4] - 4 node IDs per segment
    // $#      n1        n2        n3        n4
    //          1         2         3         4
    int32_t n1 = parse_int(line, 0, 10);
    int32_t n2 = parse_int(line, 10, 10);
    int32_t n3 = parse_int(line, 20, 10);
    int32_t n4 = parse_int(line, 30, 10);

    set.add_segment(n1, n2, n3, n4);
}

} // namespace kfile
