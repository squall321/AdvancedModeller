#pragma once
#include <string>
#include <cstdint>

namespace kfile {

/**
 * LS-DYNA Include file reference
 *
 * K-file format:
 * *INCLUDE
 * /path/to/file.k
 *
 * *INCLUDE_PATH
 * /path/to/search/directory
 *
 * *INCLUDE_PATH_RELATIVE
 * relative/path
 */
struct Include {
    std::string filepath;           // Path to included file
    bool is_path_only;              // true for *INCLUDE_PATH, false for *INCLUDE
    bool is_relative;               // true for *INCLUDE_PATH_RELATIVE

    Include()
        : filepath(""), is_path_only(false), is_relative(false) {}

    Include(const std::string& path, bool path_only = false, bool relative = false)
        : filepath(path), is_path_only(path_only), is_relative(relative) {}
};

} // namespace kfile
