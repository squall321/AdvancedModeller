#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/stl_bind.h>
#include "parser.hpp"

namespace py = pybind11;

PYBIND11_MAKE_OPAQUE(std::vector<kfile::Node>);
PYBIND11_MAKE_OPAQUE(std::vector<kfile::Part>);
PYBIND11_MAKE_OPAQUE(std::vector<kfile::Element>);
PYBIND11_MAKE_OPAQUE(std::vector<kfile::Set>);
PYBIND11_MAKE_OPAQUE(std::vector<kfile::Section>);
PYBIND11_MAKE_OPAQUE(std::vector<kfile::Contact>);
PYBIND11_MAKE_OPAQUE(std::vector<kfile::Material>);
PYBIND11_MAKE_OPAQUE(std::vector<kfile::Include>);
PYBIND11_MAKE_OPAQUE(std::vector<kfile::Curve>);
PYBIND11_MAKE_OPAQUE(std::vector<kfile::BoundarySPC>);
PYBIND11_MAKE_OPAQUE(std::vector<kfile::BoundaryPrescribedMotion>);
PYBIND11_MAKE_OPAQUE(std::vector<kfile::LoadNode>);
PYBIND11_MAKE_OPAQUE(std::vector<kfile::LoadSegment>);
PYBIND11_MAKE_OPAQUE(std::vector<kfile::LoadBody>);
PYBIND11_MAKE_OPAQUE(std::vector<kfile::ControlTermination>);
PYBIND11_MAKE_OPAQUE(std::vector<kfile::ControlTimestep>);
PYBIND11_MAKE_OPAQUE(std::vector<kfile::ControlEnergy>);
PYBIND11_MAKE_OPAQUE(std::vector<kfile::ControlOutput>);
PYBIND11_MAKE_OPAQUE(std::vector<kfile::ControlShell>);
PYBIND11_MAKE_OPAQUE(std::vector<kfile::ControlContact>);
PYBIND11_MAKE_OPAQUE(std::vector<kfile::ControlHourglass>);
PYBIND11_MAKE_OPAQUE(std::vector<kfile::ControlBulkViscosity>);
PYBIND11_MAKE_OPAQUE(std::vector<kfile::DatabaseBinary>);
PYBIND11_MAKE_OPAQUE(std::vector<kfile::DatabaseASCII>);
PYBIND11_MAKE_OPAQUE(std::vector<kfile::DatabaseHistoryNode>);
PYBIND11_MAKE_OPAQUE(std::vector<kfile::DatabaseHistoryElement>);
PYBIND11_MAKE_OPAQUE(std::vector<kfile::DatabaseCrossSection>);
PYBIND11_MAKE_OPAQUE(std::vector<kfile::InitialVelocity>);
PYBIND11_MAKE_OPAQUE(std::vector<kfile::InitialStress>);
PYBIND11_MAKE_OPAQUE(std::vector<kfile::ConstrainedNodalRigidBody>);
PYBIND11_MAKE_OPAQUE(std::vector<kfile::ConstrainedExtraNodes>);
PYBIND11_MAKE_OPAQUE(std::vector<kfile::ConstrainedJoint>);
PYBIND11_MAKE_OPAQUE(std::vector<kfile::ConstrainedSpotweld>);

PYBIND11_MODULE(_kfile_parser, m) {
    m.doc() = "High-performance LS-DYNA K-file parser";

    // Bind std::array<int32_t, 8> for Element.nodes
    py::class_<std::array<int32_t, 8>>(m, "NodeArray")
        .def("__getitem__", [](const std::array<int32_t, 8>& arr, size_t i) {
            if (i >= 8) throw py::index_error();
            return arr[i];
        })
        .def("__len__", [](const std::array<int32_t, 8>&) { return 8; })
        .def("__iter__", [](const std::array<int32_t, 8>& arr) {
            return py::make_iterator(arr.begin(), arr.end());
        }, py::keep_alive<0, 1>());

    // Bind std::array<int32_t, 4> for Segment nodes
    py::class_<std::array<int32_t, 4>>(m, "SegmentNodes")
        .def("__getitem__", [](const std::array<int32_t, 4>& arr, size_t i) {
            if (i >= 4) throw py::index_error();
            return arr[i];
        })
        .def("__len__", [](const std::array<int32_t, 4>&) { return 4; })
        .def("__iter__", [](const std::array<int32_t, 4>& arr) {
            return py::make_iterator(arr.begin(), arr.end());
        }, py::keep_alive<0, 1>());

    // ElementType enum
    py::enum_<kfile::ElementType>(m, "ElementType")
        .value("SHELL", kfile::ElementType::SHELL)
        .value("SOLID", kfile::ElementType::SOLID)
        .value("BEAM", kfile::ElementType::BEAM)
        .export_values();

    // SetType enum
    py::enum_<kfile::SetType>(m, "SetType")
        .value("NODE_LIST", kfile::SetType::NODE_LIST)
        .value("PART_LIST", kfile::SetType::PART_LIST)
        .value("SEGMENT", kfile::SetType::SEGMENT)
        .value("SHELL", kfile::SetType::SHELL)
        .value("SOLID", kfile::SetType::SOLID)
        .export_values();

    // SectionType enum
    py::enum_<kfile::SectionType>(m, "SectionType")
        .value("SHELL", kfile::SectionType::SHELL)
        .value("SOLID", kfile::SectionType::SOLID)
        .value("BEAM", kfile::SectionType::BEAM)
        .export_values();

    // ContactType enum
    py::enum_<kfile::ContactType>(m, "ContactType")
        .value("AUTOMATIC_SINGLE_SURFACE", kfile::ContactType::AUTOMATIC_SINGLE_SURFACE)
        .value("AUTOMATIC_SURFACE_TO_SURFACE", kfile::ContactType::AUTOMATIC_SURFACE_TO_SURFACE)
        .value("AUTOMATIC_NODES_TO_SURFACE", kfile::ContactType::AUTOMATIC_NODES_TO_SURFACE)
        .value("AUTOMATIC_GENERAL", kfile::ContactType::AUTOMATIC_GENERAL)
        .value("TIED_SURFACE_TO_SURFACE", kfile::ContactType::TIED_SURFACE_TO_SURFACE)
        .value("TIED_NODES_TO_SURFACE", kfile::ContactType::TIED_NODES_TO_SURFACE)
        .value("TIED_SHELL_EDGE_TO_SURFACE", kfile::ContactType::TIED_SHELL_EDGE_TO_SURFACE)
        .value("SURFACE_TO_SURFACE", kfile::ContactType::SURFACE_TO_SURFACE)
        .value("NODES_TO_SURFACE", kfile::ContactType::NODES_TO_SURFACE)
        .value("OTHER", kfile::ContactType::OTHER)
        .export_values();

    // MaterialType enum
    py::enum_<kfile::MaterialType>(m, "MaterialType")
        .value("ELASTIC", kfile::MaterialType::ELASTIC)
        .value("ORTHOTROPIC_ELASTIC", kfile::MaterialType::ORTHOTROPIC_ELASTIC)
        .value("PLASTIC_KINEMATIC", kfile::MaterialType::PLASTIC_KINEMATIC)
        .value("RIGID", kfile::MaterialType::RIGID)
        .value("PIECEWISE_LINEAR_PLASTICITY", kfile::MaterialType::PIECEWISE_LINEAR_PLASTICITY)
        .value("FABRIC", kfile::MaterialType::FABRIC)
        .value("COMPOSITE_DAMAGE", kfile::MaterialType::COMPOSITE_DAMAGE)
        .value("LAMINATED_COMPOSITE_FABRIC", kfile::MaterialType::LAMINATED_COMPOSITE_FABRIC)
        .value("COMPOSITE_FAILURE", kfile::MaterialType::COMPOSITE_FAILURE)
        .value("OTHER", kfile::MaterialType::OTHER)
        .export_values();

    // BoundaryType enum
    py::enum_<kfile::BoundaryType>(m, "BoundaryType")
        .value("SPC_NODE", kfile::BoundaryType::SPC_NODE)
        .value("SPC_SET", kfile::BoundaryType::SPC_SET)
        .value("PRESCRIBED_MOTION_NODE", kfile::BoundaryType::PRESCRIBED_MOTION_NODE)
        .value("PRESCRIBED_MOTION_SET", kfile::BoundaryType::PRESCRIBED_MOTION_SET)
        .value("OTHER", kfile::BoundaryType::OTHER)
        .export_values();

    // LoadType enum
    py::enum_<kfile::LoadType>(m, "LoadType")
        .value("NODE", kfile::LoadType::NODE)
        .value("SEGMENT", kfile::LoadType::SEGMENT)
        .value("SHELL_SET", kfile::LoadType::SHELL_SET)
        .value("BODY", kfile::LoadType::BODY)
        .value("RIGID_BODY", kfile::LoadType::RIGID_BODY)
        .value("THERMAL", kfile::LoadType::THERMAL)
        .value("OTHER", kfile::LoadType::OTHER)
        .export_values();

    // DatabaseType enum
    py::enum_<kfile::DatabaseType>(m, "DatabaseType")
        .value("BINARY_D3PLOT", kfile::DatabaseType::BINARY_D3PLOT)
        .value("BINARY_D3THDT", kfile::DatabaseType::BINARY_D3THDT)
        .value("BINARY_D3DUMP", kfile::DatabaseType::BINARY_D3DUMP)
        .value("BINARY_RUNRSF", kfile::DatabaseType::BINARY_RUNRSF)
        .value("BINARY_INTFOR", kfile::DatabaseType::BINARY_INTFOR)
        .value("GLSTAT", kfile::DatabaseType::GLSTAT)
        .value("MATSUM", kfile::DatabaseType::MATSUM)
        .value("NODOUT", kfile::DatabaseType::NODOUT)
        .value("ELOUT", kfile::DatabaseType::ELOUT)
        .value("RCFORC", kfile::DatabaseType::RCFORC)
        .value("SLEOUT", kfile::DatabaseType::SLEOUT)
        .value("NODFOR", kfile::DatabaseType::NODFOR)
        .value("SECFORC", kfile::DatabaseType::SECFORC)
        .value("RWFORC", kfile::DatabaseType::RWFORC)
        .value("ABSTAT", kfile::DatabaseType::ABSTAT)
        .value("BNDOUT", kfile::DatabaseType::BNDOUT)
        .value("SPCFORC", kfile::DatabaseType::SPCFORC)
        .value("JNTFORC", kfile::DatabaseType::JNTFORC)
        .value("DEFORC", kfile::DatabaseType::DEFORC)
        .value("OTHER", kfile::DatabaseType::OTHER)
        .export_values();

    // InitialVelocityType enum
    py::enum_<kfile::InitialVelocityType>(m, "InitialVelocityType")
        .value("NODE", kfile::InitialVelocityType::NODE)
        .value("SET", kfile::InitialVelocityType::SET)
        .value("GENERATION", kfile::InitialVelocityType::GENERATION)
        .value("OTHER", kfile::InitialVelocityType::OTHER)
        .export_values();

    // ConstrainedType enum
    py::enum_<kfile::ConstrainedType>(m, "ConstrainedType")
        .value("NODAL_RIGID_BODY", kfile::ConstrainedType::NODAL_RIGID_BODY)
        .value("EXTRA_NODES", kfile::ConstrainedType::EXTRA_NODES)
        .value("JOINT_REVOLUTE", kfile::ConstrainedType::JOINT_REVOLUTE)
        .value("JOINT_SPHERICAL", kfile::ConstrainedType::JOINT_SPHERICAL)
        .value("JOINT_CYLINDRICAL", kfile::ConstrainedType::JOINT_CYLINDRICAL)
        .value("JOINT_TRANSLATIONAL", kfile::ConstrainedType::JOINT_TRANSLATIONAL)
        .value("JOINT_UNIVERSAL", kfile::ConstrainedType::JOINT_UNIVERSAL)
        .value("JOINT_PLANAR", kfile::ConstrainedType::JOINT_PLANAR)
        .value("RIGID_BODY_STOPPERS", kfile::ConstrainedType::RIGID_BODY_STOPPERS)
        .value("SPOTWELD", kfile::ConstrainedType::SPOTWELD)
        .value("GENERALIZED_WELD", kfile::ConstrainedType::GENERALIZED_WELD)
        .value("OTHER", kfile::ConstrainedType::OTHER)
        .export_values();

    // Bind std::array<double, 4> for Section.thickness
    py::class_<std::array<double, 4>>(m, "ThicknessArray")
        .def("__getitem__", [](const std::array<double, 4>& arr, size_t i) {
            if (i >= 4) throw py::index_error();
            return arr[i];
        })
        .def("__len__", [](const std::array<double, 4>&) { return 4; })
        .def("__iter__", [](const std::array<double, 4>& arr) {
            return py::make_iterator(arr.begin(), arr.end());
        }, py::keep_alive<0, 1>());

    // Bind std::array<double, 2> for Section.ts/tt
    py::class_<std::array<double, 2>>(m, "BeamThicknessArray")
        .def("__getitem__", [](const std::array<double, 2>& arr, size_t i) {
            if (i >= 2) throw py::index_error();
            return arr[i];
        })
        .def("__len__", [](const std::array<double, 2>&) { return 2; })
        .def("__iter__", [](const std::array<double, 2>& arr) {
            return py::make_iterator(arr.begin(), arr.end());
        }, py::keep_alive<0, 1>());

    // Node structure
    py::class_<kfile::Node>(m, "Node")
        .def(py::init<>())
        .def(py::init<int32_t, double, double, double, int32_t, int32_t>(),
             py::arg("nid"), py::arg("x"), py::arg("y"), py::arg("z"),
             py::arg("tc") = 0, py::arg("rc") = 0)
        .def_readwrite("nid", &kfile::Node::nid)
        .def_readwrite("x", &kfile::Node::x)
        .def_readwrite("y", &kfile::Node::y)
        .def_readwrite("z", &kfile::Node::z)
        .def_readwrite("tc", &kfile::Node::tc)
        .def_readwrite("rc", &kfile::Node::rc)
        .def("__repr__", [](const kfile::Node& n) {
            return "<Node nid=" + std::to_string(n.nid) +
                   " x=" + std::to_string(n.x) +
                   " y=" + std::to_string(n.y) +
                   " z=" + std::to_string(n.z) + ">";
        });

    // Part structure
    py::class_<kfile::Part>(m, "Part")
        .def(py::init<>())
        .def_readwrite("name", &kfile::Part::name)
        .def_readwrite("pid", &kfile::Part::pid)
        .def_readwrite("secid", &kfile::Part::secid)
        .def_readwrite("mid", &kfile::Part::mid)
        .def_readwrite("eosid", &kfile::Part::eosid)
        .def_readwrite("hgid", &kfile::Part::hgid)
        .def_readwrite("grav", &kfile::Part::grav)
        .def_readwrite("adpopt", &kfile::Part::adpopt)
        .def_readwrite("tmid", &kfile::Part::tmid)
        .def("__repr__", [](const kfile::Part& p) {
            return "<Part pid=" + std::to_string(p.pid) +
                   " name=\"" + p.name +
                   "\" mid=" + std::to_string(p.mid) + ">";
        });

    // Element structure
    py::class_<kfile::Element>(m, "Element")
        .def(py::init<>())
        .def_readwrite("eid", &kfile::Element::eid)
        .def_readwrite("pid", &kfile::Element::pid)
        .def_readwrite("nodes", &kfile::Element::nodes)
        .def_readwrite("type", &kfile::Element::type)
        .def_readwrite("node_count", &kfile::Element::node_count)
        .def("__repr__", [](const kfile::Element& e) {
            std::string type_str;
            switch (e.type) {
                case kfile::ElementType::SHELL: type_str = "SHELL"; break;
                case kfile::ElementType::SOLID: type_str = "SOLID"; break;
                case kfile::ElementType::BEAM: type_str = "BEAM"; break;
            }
            return "<Element eid=" + std::to_string(e.eid) +
                   " pid=" + std::to_string(e.pid) +
                   " type=" + type_str +
                   " nodes=" + std::to_string(e.node_count) + ">";
        });

    // Set structure
    py::class_<kfile::Set>(m, "Set")
        .def(py::init<>())
        .def(py::init<int32_t, kfile::SetType>(),
             py::arg("sid"), py::arg("type"))
        .def_readwrite("sid", &kfile::Set::sid)
        .def_readwrite("type", &kfile::Set::type)
        .def_readwrite("da1", &kfile::Set::da1)
        .def_readwrite("da2", &kfile::Set::da2)
        .def_readwrite("da3", &kfile::Set::da3)
        .def_readwrite("da4", &kfile::Set::da4)
        .def_readwrite("solver", &kfile::Set::solver)
        .def_readwrite("ids", &kfile::Set::ids)
        .def_readwrite("segments", &kfile::Set::segments)
        .def("count", &kfile::Set::count)
        .def("add_id", &kfile::Set::add_id)
        .def("add_segment", &kfile::Set::add_segment)
        .def("__repr__", [](const kfile::Set& s) {
            std::string type_str;
            switch (s.type) {
                case kfile::SetType::NODE_LIST: type_str = "NODE_LIST"; break;
                case kfile::SetType::PART_LIST: type_str = "PART_LIST"; break;
                case kfile::SetType::SEGMENT: type_str = "SEGMENT"; break;
                case kfile::SetType::SHELL: type_str = "SHELL"; break;
                case kfile::SetType::SOLID: type_str = "SOLID"; break;
            }
            return "<Set sid=" + std::to_string(s.sid) +
                   " type=" + type_str +
                   " count=" + std::to_string(s.count()) + ">";
        });

    // Section structure
    py::class_<kfile::Section>(m, "Section")
        .def(py::init<>())
        .def(py::init<int32_t, kfile::SectionType>(),
             py::arg("secid"), py::arg("type"))
        .def_readwrite("secid", &kfile::Section::secid)
        .def_readwrite("type", &kfile::Section::type)
        .def_readwrite("elform", &kfile::Section::elform)
        // Shell fields
        .def_readwrite("shrf", &kfile::Section::shrf)
        .def_readwrite("nip", &kfile::Section::nip)
        .def_readwrite("propt", &kfile::Section::propt)
        .def_readwrite("qr_irid", &kfile::Section::qr_irid)
        .def_readwrite("icomp", &kfile::Section::icomp)
        .def_readwrite("setyp", &kfile::Section::setyp)
        .def_readwrite("thickness", &kfile::Section::thickness)
        .def_readwrite("nloc", &kfile::Section::nloc)
        .def_readwrite("marea", &kfile::Section::marea)
        .def_readwrite("idof", &kfile::Section::idof)
        .def_readwrite("edgset", &kfile::Section::edgset)
        // Solid fields
        .def_readwrite("aet", &kfile::Section::aet)
        // Beam fields
        .def_readwrite("cst", &kfile::Section::cst)
        .def_readwrite("scoor", &kfile::Section::scoor)
        .def_readwrite("ts", &kfile::Section::ts)
        .def_readwrite("tt", &kfile::Section::tt)
        .def_readwrite("nsloc", &kfile::Section::nsloc)
        .def_readwrite("ntloc", &kfile::Section::ntloc)
        .def("__repr__", [](const kfile::Section& s) {
            std::string type_str;
            switch (s.type) {
                case kfile::SectionType::SHELL: type_str = "SHELL"; break;
                case kfile::SectionType::SOLID: type_str = "SOLID"; break;
                case kfile::SectionType::BEAM: type_str = "BEAM"; break;
            }
            return "<Section secid=" + std::to_string(s.secid) +
                   " type=" + type_str +
                   " elform=" + std::to_string(s.elform) + ">";
        });

    // Contact structure
    py::class_<kfile::Contact>(m, "Contact")
        .def(py::init<>())
        .def(py::init<kfile::ContactType, const std::string&>(),
             py::arg("type"), py::arg("name"))
        .def_readwrite("type", &kfile::Contact::type)
        .def_readwrite("type_name", &kfile::Contact::type_name)
        // Card 1
        .def_readwrite("ssid", &kfile::Contact::ssid)
        .def_readwrite("msid", &kfile::Contact::msid)
        .def_readwrite("sstyp", &kfile::Contact::sstyp)
        .def_readwrite("mstyp", &kfile::Contact::mstyp)
        .def_readwrite("sboxid", &kfile::Contact::sboxid)
        .def_readwrite("mboxid", &kfile::Contact::mboxid)
        .def_readwrite("spr", &kfile::Contact::spr)
        .def_readwrite("mpr", &kfile::Contact::mpr)
        // Card 2
        .def_readwrite("fs", &kfile::Contact::fs)
        .def_readwrite("fd", &kfile::Contact::fd)
        .def_readwrite("dc", &kfile::Contact::dc)
        .def_readwrite("vc", &kfile::Contact::vc)
        .def_readwrite("vdc", &kfile::Contact::vdc)
        .def_readwrite("penchk", &kfile::Contact::penchk)
        .def_readwrite("bt", &kfile::Contact::bt)
        .def_readwrite("dt", &kfile::Contact::dt)
        // Card 3
        .def_readwrite("sfs", &kfile::Contact::sfs)
        .def_readwrite("sfm", &kfile::Contact::sfm)
        .def_readwrite("sst", &kfile::Contact::sst)
        .def_readwrite("mst", &kfile::Contact::mst)
        .def_readwrite("sfst", &kfile::Contact::sfst)
        .def_readwrite("sfmt", &kfile::Contact::sfmt)
        .def_readwrite("fsf", &kfile::Contact::fsf)
        .def_readwrite("vsf", &kfile::Contact::vsf)
        // Parsing state
        .def_readwrite("cards_parsed", &kfile::Contact::cards_parsed)
        .def("__repr__", [](const kfile::Contact& c) {
            return "<Contact type=\"" + c.type_name +
                   "\" ssid=" + std::to_string(c.ssid) +
                   " msid=" + std::to_string(c.msid) +
                   " cards=" + std::to_string(c.cards_parsed) + ">";
        });

    // Material structure
    py::class_<kfile::Material>(m, "Material")
        .def(py::init<>())
        .def(py::init<int32_t, kfile::MaterialType>(),
             py::arg("mid"), py::arg("type"))
        .def_readwrite("mid", &kfile::Material::mid)
        .def_readwrite("type", &kfile::Material::type)
        .def_readwrite("type_name", &kfile::Material::type_name)
        // Common properties
        .def_readwrite("ro", &kfile::Material::ro)
        .def_readwrite("e", &kfile::Material::e)
        .def_readwrite("pr", &kfile::Material::pr)
        // Orthotropic properties
        .def_readwrite("eb", &kfile::Material::eb)
        .def_readwrite("ec", &kfile::Material::ec)
        .def_readwrite("prca", &kfile::Material::prca)
        .def_readwrite("prcb", &kfile::Material::prcb)
        .def_readwrite("gab", &kfile::Material::gab)
        .def_readwrite("gbc", &kfile::Material::gbc)
        .def_readwrite("gca", &kfile::Material::gca)
        // Plasticity properties
        .def_readwrite("sigy", &kfile::Material::sigy)
        .def_readwrite("etan", &kfile::Material::etan)
        .def_readwrite("fail", &kfile::Material::fail)
        .def_readwrite("tdel", &kfile::Material::tdel)
        // Rigid properties
        .def_readwrite("cmo", &kfile::Material::cmo)
        .def_readwrite("con1", &kfile::Material::con1)
        .def_readwrite("con2", &kfile::Material::con2)
        // Composite strength properties
        .def_readwrite("xc", &kfile::Material::xc)
        .def_readwrite("xt", &kfile::Material::xt)
        .def_readwrite("yc", &kfile::Material::yc)
        .def_readwrite("yt", &kfile::Material::yt)
        .def_readwrite("sc", &kfile::Material::sc)
        // Additional options
        .def_readwrite("aopt", &kfile::Material::aopt)
        .def_readwrite("macf", &kfile::Material::macf)
        // Raw card data
        .def_readwrite("cards", &kfile::Material::cards)
        .def_readwrite("cards_parsed", &kfile::Material::cards_parsed)
        .def_readwrite("title", &kfile::Material::title)
        // Helper methods
        .def("get_card_value", &kfile::Material::get_card_value,
             py::arg("card_idx"), py::arg("col_idx"),
             "Get a value from a specific card and column (0-indexed)")
        .def("num_cards", &kfile::Material::num_cards,
             "Get the number of cards stored")
        .def("__repr__", [](const kfile::Material& m) {
            return "<Material mid=" + std::to_string(m.mid) +
                   " type=\"" + m.type_name +
                   "\" E=" + std::to_string(m.e) +
                   " cards=" + std::to_string(m.cards_parsed) + ">";
        });

    // Include structure
    py::class_<kfile::Include>(m, "Include")
        .def(py::init<>())
        .def_readwrite("filepath", &kfile::Include::filepath)
        .def_readwrite("is_path_only", &kfile::Include::is_path_only)
        .def_readwrite("is_relative", &kfile::Include::is_relative)
        .def("__repr__", [](const kfile::Include& inc) {
            return "<Include filepath=\"" + inc.filepath + "\">";
        });

    // Curve structure
    py::class_<kfile::Curve>(m, "Curve")
        .def(py::init<>())
        .def(py::init<int32_t>(), py::arg("lcid"))
        .def_readwrite("lcid", &kfile::Curve::lcid)
        .def_readwrite("sidr", &kfile::Curve::sidr)
        .def_readwrite("sfa", &kfile::Curve::sfa)
        .def_readwrite("sfo", &kfile::Curve::sfo)
        .def_readwrite("offa", &kfile::Curve::offa)
        .def_readwrite("offo", &kfile::Curve::offo)
        .def_readwrite("dattyp", &kfile::Curve::dattyp)
        .def_readwrite("points", &kfile::Curve::points)
        .def_readwrite("title", &kfile::Curve::title)
        .def("add_point", &kfile::Curve::add_point,
             py::arg("a"), py::arg("o"))
        .def("num_points", &kfile::Curve::num_points)
        .def("get_point", &kfile::Curve::get_point, py::arg("idx"))
        .def("__repr__", [](const kfile::Curve& c) {
            return "<Curve lcid=" + std::to_string(c.lcid) +
                   " points=" + std::to_string(c.num_points()) + ">";
        });

    // BoundarySPC structure
    py::class_<kfile::BoundarySPC>(m, "BoundarySPC")
        .def(py::init<>())
        .def(py::init<kfile::BoundaryType, int32_t>(),
             py::arg("type"), py::arg("nid"))
        .def_readwrite("type", &kfile::BoundarySPC::type)
        .def_readwrite("nid", &kfile::BoundarySPC::nid)
        .def_readwrite("cid", &kfile::BoundarySPC::cid)
        .def_readwrite("dofx", &kfile::BoundarySPC::dofx)
        .def_readwrite("dofy", &kfile::BoundarySPC::dofy)
        .def_readwrite("dofz", &kfile::BoundarySPC::dofz)
        .def_readwrite("dofrx", &kfile::BoundarySPC::dofrx)
        .def_readwrite("dofry", &kfile::BoundarySPC::dofry)
        .def_readwrite("dofrz", &kfile::BoundarySPC::dofrz)
        .def_readwrite("dof", &kfile::BoundarySPC::dof)
        .def_readwrite("vad", &kfile::BoundarySPC::vad)
        .def_readwrite("title", &kfile::BoundarySPC::title)
        .def("__repr__", [](const kfile::BoundarySPC& b) {
            return "<BoundarySPC nid=" + std::to_string(b.nid) + ">";
        });

    // BoundaryPrescribedMotion structure
    py::class_<kfile::BoundaryPrescribedMotion>(m, "BoundaryPrescribedMotion")
        .def(py::init<>())
        .def_readwrite("type", &kfile::BoundaryPrescribedMotion::type)
        .def_readwrite("nid", &kfile::BoundaryPrescribedMotion::nid)
        .def_readwrite("dof", &kfile::BoundaryPrescribedMotion::dof)
        .def_readwrite("vad", &kfile::BoundaryPrescribedMotion::vad)
        .def_readwrite("lcid", &kfile::BoundaryPrescribedMotion::lcid)
        .def_readwrite("sf", &kfile::BoundaryPrescribedMotion::sf)
        .def_readwrite("vid", &kfile::BoundaryPrescribedMotion::vid)
        .def_readwrite("death", &kfile::BoundaryPrescribedMotion::death)
        .def_readwrite("birth", &kfile::BoundaryPrescribedMotion::birth)
        .def_readwrite("title", &kfile::BoundaryPrescribedMotion::title)
        .def("__repr__", [](const kfile::BoundaryPrescribedMotion& b) {
            return "<BoundaryPrescribedMotion nid=" + std::to_string(b.nid) +
                   " lcid=" + std::to_string(b.lcid) + ">";
        });

    // LoadNode structure
    py::class_<kfile::LoadNode>(m, "LoadNode")
        .def(py::init<>())
        .def_readwrite("type", &kfile::LoadNode::type)
        .def_readwrite("nid", &kfile::LoadNode::nid)
        .def_readwrite("dof", &kfile::LoadNode::dof)
        .def_readwrite("lcid", &kfile::LoadNode::lcid)
        .def_readwrite("sf", &kfile::LoadNode::sf)
        .def_readwrite("cid", &kfile::LoadNode::cid)
        .def_readwrite("m1", &kfile::LoadNode::m1)
        .def_readwrite("m2", &kfile::LoadNode::m2)
        .def_readwrite("m3", &kfile::LoadNode::m3)
        .def_readwrite("is_set", &kfile::LoadNode::is_set)
        .def_readwrite("title", &kfile::LoadNode::title)
        .def("__repr__", [](const kfile::LoadNode& l) {
            return "<LoadNode nid=" + std::to_string(l.nid) +
                   " dof=" + std::to_string(l.dof) +
                   " lcid=" + std::to_string(l.lcid) + ">";
        });

    // LoadSegment structure
    py::class_<kfile::LoadSegment>(m, "LoadSegment")
        .def(py::init<>())
        .def_readwrite("lcid", &kfile::LoadSegment::lcid)
        .def_readwrite("sf", &kfile::LoadSegment::sf)
        .def_readwrite("at", &kfile::LoadSegment::at)
        .def_readwrite("n1", &kfile::LoadSegment::n1)
        .def_readwrite("n2", &kfile::LoadSegment::n2)
        .def_readwrite("n3", &kfile::LoadSegment::n3)
        .def_readwrite("n4", &kfile::LoadSegment::n4)
        .def_readwrite("title", &kfile::LoadSegment::title)
        .def("__repr__", [](const kfile::LoadSegment& l) {
            return "<LoadSegment lcid=" + std::to_string(l.lcid) +
                   " nodes=[" + std::to_string(l.n1) + "," +
                   std::to_string(l.n2) + "," + std::to_string(l.n3) +
                   "," + std::to_string(l.n4) + "]>";
        });

    // LoadBody structure
    py::class_<kfile::LoadBody>(m, "LoadBody")
        .def(py::init<>())
        .def_readwrite("direction", &kfile::LoadBody::direction)
        .def_readwrite("lcid", &kfile::LoadBody::lcid)
        .def_readwrite("sf", &kfile::LoadBody::sf)
        .def_readwrite("lciddr", &kfile::LoadBody::lciddr)
        .def_readwrite("xc", &kfile::LoadBody::xc)
        .def_readwrite("yc", &kfile::LoadBody::yc)
        .def_readwrite("zc", &kfile::LoadBody::zc)
        .def_readwrite("cid", &kfile::LoadBody::cid)
        .def("__repr__", [](const kfile::LoadBody& l) {
            std::string dir = (l.direction == 1) ? "X" :
                              (l.direction == 2) ? "Y" :
                              (l.direction == 3) ? "Z" : "?";
            return "<LoadBody direction=" + dir +
                   " lcid=" + std::to_string(l.lcid) +
                   " sf=" + std::to_string(l.sf) + ">";
        });

    // ControlTermination structure
    py::class_<kfile::ControlTermination>(m, "ControlTermination")
        .def(py::init<>())
        .def_readwrite("endtim", &kfile::ControlTermination::endtim)
        .def_readwrite("endcyc", &kfile::ControlTermination::endcyc)
        .def_readwrite("dtmin", &kfile::ControlTermination::dtmin)
        .def_readwrite("endeng", &kfile::ControlTermination::endeng)
        .def_readwrite("endmas", &kfile::ControlTermination::endmas)
        .def_readwrite("nosol", &kfile::ControlTermination::nosol);

    // ControlTimestep structure
    py::class_<kfile::ControlTimestep>(m, "ControlTimestep")
        .def(py::init<>())
        .def_readwrite("dtinit", &kfile::ControlTimestep::dtinit)
        .def_readwrite("tssfac", &kfile::ControlTimestep::tssfac)
        .def_readwrite("isdo", &kfile::ControlTimestep::isdo)
        .def_readwrite("tslimt", &kfile::ControlTimestep::tslimt)
        .def_readwrite("dt2ms", &kfile::ControlTimestep::dt2ms)
        .def_readwrite("lctm", &kfile::ControlTimestep::lctm)
        .def_readwrite("erode", &kfile::ControlTimestep::erode)
        .def_readwrite("ms1st", &kfile::ControlTimestep::ms1st);

    // ControlEnergy structure
    py::class_<kfile::ControlEnergy>(m, "ControlEnergy")
        .def(py::init<>())
        .def_readwrite("hgen", &kfile::ControlEnergy::hgen)
        .def_readwrite("rwen", &kfile::ControlEnergy::rwen)
        .def_readwrite("slnten", &kfile::ControlEnergy::slnten)
        .def_readwrite("rylen", &kfile::ControlEnergy::rylen);

    // ControlOutput structure
    py::class_<kfile::ControlOutput>(m, "ControlOutput")
        .def(py::init<>())
        .def_readwrite("npopt", &kfile::ControlOutput::npopt)
        .def_readwrite("netefm", &kfile::ControlOutput::netefm)
        .def_readwrite("nflcit", &kfile::ControlOutput::nflcit)
        .def_readwrite("nprint", &kfile::ControlOutput::nprint)
        .def_readwrite("ikedit", &kfile::ControlOutput::ikedit)
        .def_readwrite("iflush", &kfile::ControlOutput::iflush)
        .def_readwrite("iprtf", &kfile::ControlOutput::iprtf)
        .def_readwrite("ierode", &kfile::ControlOutput::ierode);

    // ControlShell structure
    py::class_<kfile::ControlShell>(m, "ControlShell")
        .def(py::init<>())
        .def_readwrite("wrpang", &kfile::ControlShell::wrpang)
        .def_readwrite("esort", &kfile::ControlShell::esort)
        .def_readwrite("irnxx", &kfile::ControlShell::irnxx)
        .def_readwrite("istupd", &kfile::ControlShell::istupd)
        .def_readwrite("theory", &kfile::ControlShell::theory)
        .def_readwrite("bwc", &kfile::ControlShell::bwc)
        .def_readwrite("miter", &kfile::ControlShell::miter)
        .def_readwrite("proj", &kfile::ControlShell::proj);

    // ControlContact structure
    py::class_<kfile::ControlContact>(m, "ControlContact")
        .def(py::init<>())
        .def_readwrite("slsfac", &kfile::ControlContact::slsfac)
        .def_readwrite("rwpnal", &kfile::ControlContact::rwpnal)
        .def_readwrite("islchk", &kfile::ControlContact::islchk)
        .def_readwrite("shlthk", &kfile::ControlContact::shlthk)
        .def_readwrite("penopt", &kfile::ControlContact::penopt)
        .def_readwrite("thkchg", &kfile::ControlContact::thkchg)
        .def_readwrite("otefm", &kfile::ControlContact::otefm)
        .def_readwrite("enmass", &kfile::ControlContact::enmass);

    // ControlHourglass structure
    py::class_<kfile::ControlHourglass>(m, "ControlHourglass")
        .def(py::init<>())
        .def_readwrite("ihq", &kfile::ControlHourglass::ihq)
        .def_readwrite("qh", &kfile::ControlHourglass::qh);

    // ControlBulkViscosity structure
    py::class_<kfile::ControlBulkViscosity>(m, "ControlBulkViscosity")
        .def(py::init<>())
        .def_readwrite("q1", &kfile::ControlBulkViscosity::q1)
        .def_readwrite("q2", &kfile::ControlBulkViscosity::q2)
        .def_readwrite("type", &kfile::ControlBulkViscosity::type);

    // DatabaseBinary structure
    py::class_<kfile::DatabaseBinary>(m, "DatabaseBinary")
        .def(py::init<>())
        .def_readwrite("type", &kfile::DatabaseBinary::type)
        .def_readwrite("dt", &kfile::DatabaseBinary::dt)
        .def_readwrite("lcdt", &kfile::DatabaseBinary::lcdt)
        .def_readwrite("beam", &kfile::DatabaseBinary::beam)
        .def_readwrite("npltc", &kfile::DatabaseBinary::npltc)
        .def_readwrite("psetid", &kfile::DatabaseBinary::psetid);

    // DatabaseASCII structure
    py::class_<kfile::DatabaseASCII>(m, "DatabaseASCII")
        .def(py::init<>())
        .def_readwrite("type", &kfile::DatabaseASCII::type)
        .def_readwrite("dt", &kfile::DatabaseASCII::dt)
        .def_readwrite("lcdt", &kfile::DatabaseASCII::lcdt)
        .def_readwrite("binary", &kfile::DatabaseASCII::binary)
        .def_readwrite("lcur", &kfile::DatabaseASCII::lcur)
        .def_readwrite("ioopt", &kfile::DatabaseASCII::ioopt);

    // DatabaseHistoryNode structure
    py::class_<kfile::DatabaseHistoryNode>(m, "DatabaseHistoryNode")
        .def(py::init<>())
        .def_readwrite("node_ids", &kfile::DatabaseHistoryNode::node_ids)
        .def_readwrite("title", &kfile::DatabaseHistoryNode::title)
        .def("add_node", &kfile::DatabaseHistoryNode::add_node)
        .def("num_nodes", &kfile::DatabaseHistoryNode::num_nodes);

    // DatabaseHistoryElement structure
    py::class_<kfile::DatabaseHistoryElement>(m, "DatabaseHistoryElement")
        .def(py::init<>())
        .def_readwrite("element_ids", &kfile::DatabaseHistoryElement::element_ids)
        .def_readwrite("title", &kfile::DatabaseHistoryElement::title)
        .def_readwrite("element_type", &kfile::DatabaseHistoryElement::element_type)
        .def("add_element", &kfile::DatabaseHistoryElement::add_element)
        .def("num_elements", &kfile::DatabaseHistoryElement::num_elements);

    // DatabaseCrossSection structure
    py::class_<kfile::DatabaseCrossSection>(m, "DatabaseCrossSection")
        .def(py::init<>())
        .def_readwrite("csid", &kfile::DatabaseCrossSection::csid)
        .def_readwrite("title", &kfile::DatabaseCrossSection::title)
        .def_readwrite("psid", &kfile::DatabaseCrossSection::psid)
        .def_readwrite("ssid", &kfile::DatabaseCrossSection::ssid)
        .def_readwrite("tsid", &kfile::DatabaseCrossSection::tsid)
        .def_readwrite("dsid", &kfile::DatabaseCrossSection::dsid);

    // InitialVelocity structure
    py::class_<kfile::InitialVelocity>(m, "InitialVelocity")
        .def(py::init<>())
        .def_readwrite("type", &kfile::InitialVelocity::type)
        .def_readwrite("nsid", &kfile::InitialVelocity::nsid)
        .def_readwrite("nsidex", &kfile::InitialVelocity::nsidex)
        .def_readwrite("boxid", &kfile::InitialVelocity::boxid)
        .def_readwrite("irigid", &kfile::InitialVelocity::irigid)
        .def_readwrite("vx", &kfile::InitialVelocity::vx)
        .def_readwrite("vy", &kfile::InitialVelocity::vy)
        .def_readwrite("vz", &kfile::InitialVelocity::vz)
        .def_readwrite("vxr", &kfile::InitialVelocity::vxr)
        .def_readwrite("vyr", &kfile::InitialVelocity::vyr)
        .def_readwrite("vzr", &kfile::InitialVelocity::vzr)
        .def_readwrite("omega", &kfile::InitialVelocity::omega)
        .def_readwrite("xc", &kfile::InitialVelocity::xc)
        .def_readwrite("yc", &kfile::InitialVelocity::yc)
        .def_readwrite("zc", &kfile::InitialVelocity::zc);

    // InitialStress structure
    py::class_<kfile::InitialStress>(m, "InitialStress")
        .def(py::init<>())
        .def_readwrite("eid", &kfile::InitialStress::eid)
        .def_readwrite("nplane", &kfile::InitialStress::nplane)
        .def_readwrite("nthick", &kfile::InitialStress::nthick);

    // ConstrainedNodalRigidBody structure
    py::class_<kfile::ConstrainedNodalRigidBody>(m, "ConstrainedNodalRigidBody")
        .def(py::init<>())
        .def_readwrite("pid", &kfile::ConstrainedNodalRigidBody::pid)
        .def_readwrite("cid", &kfile::ConstrainedNodalRigidBody::cid)
        .def_readwrite("nsid", &kfile::ConstrainedNodalRigidBody::nsid)
        .def_readwrite("pnode", &kfile::ConstrainedNodalRigidBody::pnode)
        .def_readwrite("iprt", &kfile::ConstrainedNodalRigidBody::iprt)
        .def_readwrite("drflag", &kfile::ConstrainedNodalRigidBody::drflag)
        .def_readwrite("rrflag", &kfile::ConstrainedNodalRigidBody::rrflag)
        .def_readwrite("title", &kfile::ConstrainedNodalRigidBody::title)
        .def_readwrite("has_inertia", &kfile::ConstrainedNodalRigidBody::has_inertia);

    // ConstrainedExtraNodes structure
    py::class_<kfile::ConstrainedExtraNodes>(m, "ConstrainedExtraNodes")
        .def(py::init<>())
        .def_readwrite("pid", &kfile::ConstrainedExtraNodes::pid)
        .def_readwrite("nsid", &kfile::ConstrainedExtraNodes::nsid)
        .def_readwrite("node_ids", &kfile::ConstrainedExtraNodes::node_ids)
        .def_readwrite("iflag", &kfile::ConstrainedExtraNodes::iflag)
        .def_readwrite("title", &kfile::ConstrainedExtraNodes::title)
        .def_readwrite("is_set", &kfile::ConstrainedExtraNodes::is_set)
        .def("add_node", &kfile::ConstrainedExtraNodes::add_node)
        .def("num_nodes", &kfile::ConstrainedExtraNodes::num_nodes);

    // ConstrainedJoint structure
    py::class_<kfile::ConstrainedJoint>(m, "ConstrainedJoint")
        .def(py::init<>())
        .def_readwrite("joint_type", &kfile::ConstrainedJoint::joint_type)
        .def_readwrite("jid", &kfile::ConstrainedJoint::jid)
        .def_readwrite("n1", &kfile::ConstrainedJoint::n1)
        .def_readwrite("n2", &kfile::ConstrainedJoint::n2)
        .def_readwrite("n3", &kfile::ConstrainedJoint::n3)
        .def_readwrite("n4", &kfile::ConstrainedJoint::n4)
        .def_readwrite("n5", &kfile::ConstrainedJoint::n5)
        .def_readwrite("n6", &kfile::ConstrainedJoint::n6)
        .def_readwrite("rps", &kfile::ConstrainedJoint::rps)
        .def_readwrite("damp", &kfile::ConstrainedJoint::damp)
        .def_readwrite("title", &kfile::ConstrainedJoint::title);

    // ConstrainedSpotweld structure
    py::class_<kfile::ConstrainedSpotweld>(m, "ConstrainedSpotweld")
        .def(py::init<>())
        .def_readwrite("n1", &kfile::ConstrainedSpotweld::n1)
        .def_readwrite("n2", &kfile::ConstrainedSpotweld::n2)
        .def_readwrite("sn", &kfile::ConstrainedSpotweld::sn)
        .def_readwrite("ss", &kfile::ConstrainedSpotweld::ss)
        .def_readwrite("n", &kfile::ConstrainedSpotweld::n)
        .def_readwrite("m", &kfile::ConstrainedSpotweld::m)
        .def_readwrite("tf", &kfile::ConstrainedSpotweld::tf)
        .def_readwrite("pid", &kfile::ConstrainedSpotweld::pid)
        .def_readwrite("ep_fail", &kfile::ConstrainedSpotweld::ep_fail)
        .def_readwrite("title", &kfile::ConstrainedSpotweld::title);

    // Bind vectors for efficient access
    py::bind_vector<std::vector<kfile::Node>>(m, "NodeVector");
    py::bind_vector<std::vector<kfile::Part>>(m, "PartVector");
    py::bind_vector<std::vector<kfile::Element>>(m, "ElementVector");
    py::bind_vector<std::vector<kfile::Set>>(m, "SetVector");
    py::bind_vector<std::vector<kfile::Section>>(m, "SectionVector");
    py::bind_vector<std::vector<kfile::Contact>>(m, "ContactVector");
    py::bind_vector<std::vector<kfile::Material>>(m, "MaterialVector");
    py::bind_vector<std::vector<kfile::Include>>(m, "IncludeVector");
    py::bind_vector<std::vector<kfile::Curve>>(m, "CurveVector");
    py::bind_vector<std::vector<kfile::BoundarySPC>>(m, "BoundarySPCVector");
    py::bind_vector<std::vector<kfile::BoundaryPrescribedMotion>>(m, "BoundaryPrescribedMotionVector");
    py::bind_vector<std::vector<kfile::LoadNode>>(m, "LoadNodeVector");
    py::bind_vector<std::vector<kfile::LoadSegment>>(m, "LoadSegmentVector");
    py::bind_vector<std::vector<kfile::LoadBody>>(m, "LoadBodyVector");
    py::bind_vector<std::vector<kfile::ControlTermination>>(m, "ControlTerminationVector");
    py::bind_vector<std::vector<kfile::ControlTimestep>>(m, "ControlTimestepVector");
    py::bind_vector<std::vector<kfile::ControlEnergy>>(m, "ControlEnergyVector");
    py::bind_vector<std::vector<kfile::ControlOutput>>(m, "ControlOutputVector");
    py::bind_vector<std::vector<kfile::ControlShell>>(m, "ControlShellVector");
    py::bind_vector<std::vector<kfile::ControlContact>>(m, "ControlContactVector");
    py::bind_vector<std::vector<kfile::ControlHourglass>>(m, "ControlHourglassVector");
    py::bind_vector<std::vector<kfile::ControlBulkViscosity>>(m, "ControlBulkViscosityVector");
    py::bind_vector<std::vector<kfile::DatabaseBinary>>(m, "DatabaseBinaryVector");
    py::bind_vector<std::vector<kfile::DatabaseASCII>>(m, "DatabaseASCIIVector");
    py::bind_vector<std::vector<kfile::DatabaseHistoryNode>>(m, "DatabaseHistoryNodeVector");
    py::bind_vector<std::vector<kfile::DatabaseHistoryElement>>(m, "DatabaseHistoryElementVector");
    py::bind_vector<std::vector<kfile::DatabaseCrossSection>>(m, "DatabaseCrossSectionVector");
    py::bind_vector<std::vector<kfile::InitialVelocity>>(m, "InitialVelocityVector");
    py::bind_vector<std::vector<kfile::InitialStress>>(m, "InitialStressVector");
    py::bind_vector<std::vector<kfile::ConstrainedNodalRigidBody>>(m, "ConstrainedNodalRigidBodyVector");
    py::bind_vector<std::vector<kfile::ConstrainedExtraNodes>>(m, "ConstrainedExtraNodesVector");
    py::bind_vector<std::vector<kfile::ConstrainedJoint>>(m, "ConstrainedJointVector");
    py::bind_vector<std::vector<kfile::ConstrainedSpotweld>>(m, "ConstrainedSpotweldVector");

    // ParseResult structure
    py::class_<kfile::ParseResult>(m, "ParseResult")
        .def(py::init<>())
        .def_readwrite("nodes", &kfile::ParseResult::nodes)
        .def_readwrite("parts", &kfile::ParseResult::parts)
        .def_readwrite("elements", &kfile::ParseResult::elements)
        .def_readwrite("sets", &kfile::ParseResult::sets)
        .def_readwrite("sections", &kfile::ParseResult::sections)
        .def_readwrite("contacts", &kfile::ParseResult::contacts)
        .def_readwrite("materials", &kfile::ParseResult::materials)
        .def_readwrite("includes", &kfile::ParseResult::includes)
        .def_readwrite("curves", &kfile::ParseResult::curves)
        .def_readwrite("boundary_spcs", &kfile::ParseResult::boundary_spcs)
        .def_readwrite("boundary_motions", &kfile::ParseResult::boundary_motions)
        .def_readwrite("load_nodes", &kfile::ParseResult::load_nodes)
        .def_readwrite("load_segments", &kfile::ParseResult::load_segments)
        .def_readwrite("load_bodies", &kfile::ParseResult::load_bodies)
        // Control keywords
        .def_readwrite("control_terminations", &kfile::ParseResult::control_terminations)
        .def_readwrite("control_timesteps", &kfile::ParseResult::control_timesteps)
        .def_readwrite("control_energies", &kfile::ParseResult::control_energies)
        .def_readwrite("control_outputs", &kfile::ParseResult::control_outputs)
        .def_readwrite("control_shells", &kfile::ParseResult::control_shells)
        .def_readwrite("control_contacts", &kfile::ParseResult::control_contacts)
        .def_readwrite("control_hourglasses", &kfile::ParseResult::control_hourglasses)
        .def_readwrite("control_bulk_viscosities", &kfile::ParseResult::control_bulk_viscosities)
        // Database keywords
        .def_readwrite("database_binaries", &kfile::ParseResult::database_binaries)
        .def_readwrite("database_asciis", &kfile::ParseResult::database_asciis)
        .def_readwrite("database_history_nodes", &kfile::ParseResult::database_history_nodes)
        .def_readwrite("database_history_elements", &kfile::ParseResult::database_history_elements)
        .def_readwrite("database_cross_sections", &kfile::ParseResult::database_cross_sections)
        // Initial keywords
        .def_readwrite("initial_velocities", &kfile::ParseResult::initial_velocities)
        .def_readwrite("initial_stresses", &kfile::ParseResult::initial_stresses)
        // Constrained keywords
        .def_readwrite("constrained_nodal_rigid_bodies", &kfile::ParseResult::constrained_nodal_rigid_bodies)
        .def_readwrite("constrained_extra_nodes", &kfile::ParseResult::constrained_extra_nodes)
        .def_readwrite("constrained_joints", &kfile::ParseResult::constrained_joints)
        .def_readwrite("constrained_spotwelds", &kfile::ParseResult::constrained_spotwelds)
        // Index maps
        .def_readwrite("node_index", &kfile::ParseResult::node_index)
        .def_readwrite("part_index", &kfile::ParseResult::part_index)
        .def_readwrite("element_index", &kfile::ParseResult::element_index)
        .def_readwrite("set_index", &kfile::ParseResult::set_index)
        .def_readwrite("section_index", &kfile::ParseResult::section_index)
        .def_readwrite("contact_index", &kfile::ParseResult::contact_index)
        .def_readwrite("material_index", &kfile::ParseResult::material_index)
        .def_readwrite("curve_index", &kfile::ParseResult::curve_index)
        .def_readwrite("total_lines", &kfile::ParseResult::total_lines)
        .def_readwrite("parse_time_ms", &kfile::ParseResult::parse_time_ms)
        .def_readwrite("warnings", &kfile::ParseResult::warnings)
        .def_readwrite("errors", &kfile::ParseResult::errors)
        .def("clear", &kfile::ParseResult::clear)
        .def("build_indices", &kfile::ParseResult::build_indices);

    // KFileParser class
    py::class_<kfile::KFileParser>(m, "KFileParser")
        .def(py::init<>())
        .def("set_parse_nodes", &kfile::KFileParser::set_parse_nodes)
        .def("set_parse_parts", &kfile::KFileParser::set_parse_parts)
        .def("set_parse_elements", &kfile::KFileParser::set_parse_elements)
        .def("set_parse_sets", &kfile::KFileParser::set_parse_sets)
        .def("set_parse_sections", &kfile::KFileParser::set_parse_sections)
        .def("set_parse_contacts", &kfile::KFileParser::set_parse_contacts)
        .def("set_parse_materials", &kfile::KFileParser::set_parse_materials)
        .def("set_parse_includes", &kfile::KFileParser::set_parse_includes)
        .def("set_parse_curves", &kfile::KFileParser::set_parse_curves)
        .def("set_parse_boundaries", &kfile::KFileParser::set_parse_boundaries)
        .def("set_parse_loads", &kfile::KFileParser::set_parse_loads)
        .def("set_parse_controls", &kfile::KFileParser::set_parse_controls)
        .def("set_parse_databases", &kfile::KFileParser::set_parse_databases)
        .def("set_parse_initials", &kfile::KFileParser::set_parse_initials)
        .def("set_parse_constraineds", &kfile::KFileParser::set_parse_constraineds)
        .def("set_build_index", &kfile::KFileParser::set_build_index)
        .def("get_parse_nodes", &kfile::KFileParser::get_parse_nodes)
        .def("get_parse_parts", &kfile::KFileParser::get_parse_parts)
        .def("get_parse_elements", &kfile::KFileParser::get_parse_elements)
        .def("get_parse_sets", &kfile::KFileParser::get_parse_sets)
        .def("get_parse_sections", &kfile::KFileParser::get_parse_sections)
        .def("get_parse_contacts", &kfile::KFileParser::get_parse_contacts)
        .def("get_parse_materials", &kfile::KFileParser::get_parse_materials)
        .def("get_parse_includes", &kfile::KFileParser::get_parse_includes)
        .def("get_parse_curves", &kfile::KFileParser::get_parse_curves)
        .def("get_parse_boundaries", &kfile::KFileParser::get_parse_boundaries)
        .def("get_parse_loads", &kfile::KFileParser::get_parse_loads)
        .def("get_parse_controls", &kfile::KFileParser::get_parse_controls)
        .def("get_parse_databases", &kfile::KFileParser::get_parse_databases)
        .def("get_parse_initials", &kfile::KFileParser::get_parse_initials)
        .def("get_parse_constraineds", &kfile::KFileParser::get_parse_constraineds)
        .def("get_build_index", &kfile::KFileParser::get_build_index)
        .def("parse_file", &kfile::KFileParser::parse_file,
             py::arg("filepath"),
             "Parse a K-file from disk")
        .def("parse_string", &kfile::KFileParser::parse_string,
             py::arg("content"),
             "Parse K-file content from a string")
        .def_static("parse_node_line", &kfile::KFileParser::parse_node_line,
                    py::arg("line"),
                    "Parse a single node line")
        .def_static("parse_part_lines", &kfile::KFileParser::parse_part_lines,
                    py::arg("name_line"), py::arg("data_line"),
                    "Parse part name and data lines")
        .def_static("parse_element_line", &kfile::KFileParser::parse_element_line,
                    py::arg("line"), py::arg("type"),
                    "Parse a single element line")
        .def_static("parse_set_header", &kfile::KFileParser::parse_set_header,
                    py::arg("line"), py::arg("type"),
                    "Parse a set header line");
}
