"""K file parser for extracting Part IDs from LS-DYNA files"""
import re
from typing import List, Set, Dict, Tuple
from pathlib import Path

class KFileParser:
    """Parser for LS-DYNA K files to extract Part IDs"""

    def parse_with_names(self, filepath: str) -> Dict[int, str]:
        """Extract Part IDs and names from K file. Returns {pid: part_name}"""
        parts: Dict[int, str] = {}

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception as e:
            raise ValueError(f"K파일을 읽을 수 없습니다: {e}")

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            line_upper = line.upper()

            # Check for *PART or *PART_TITLE (but not *PART_COMPOSITE etc)
            if line_upper.startswith('*PART_TITLE') or (line_upper.startswith('*PART') and not line_upper.startswith('*PART_')):
                # Skip to next non-comment, non-empty line (this is the title/name)
                j = i + 1
                while j < len(lines):
                    next_line = lines[j].strip()
                    if next_line and not next_line.startswith('$'):
                        break
                    j += 1

                if j >= len(lines):
                    i += 1
                    continue

                # This line is the part name (80 characters)
                title = lines[j].strip()

                # Find the data line (pid, secid, mid, ...)
                k = j + 1
                while k < len(lines):
                    data_line = lines[k].strip()
                    if data_line and not data_line.startswith('$'):
                        break
                    k += 1

                if k >= len(lines):
                    i = j + 1
                    continue

                # Parse PID from data line
                data_line = lines[k].strip()
                # Handle both comma and space separated formats
                parts_data = re.split(r'[,\s]+', data_line)
                if parts_data:
                    try:
                        pid = int(parts_data[0])
                        if 0 < pid < 1000000:
                            parts[pid] = title
                    except ValueError:
                        pass

                i = k + 1
                continue

            i += 1

        return parts

    def parse(self, filepath: str) -> List[int]:
        """Extract all Part IDs from K file"""
        part_ids: Set[int] = set()

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            raise ValueError(f"K파일을 읽을 수 없습니다: {e}")

        # Method 1: *PART keyword
        # Format: *PART followed by title line, then data line with pid as first field
        part_pattern = re.compile(
            r'\*PART(?:_TITLE)?[^\n]*\n'  # *PART or *PART_TITLE line
            r'(?:[^\n]*\n)?'               # Optional title line
            r'\s*(\d+)',                   # PID (first number)
            re.IGNORECASE | re.MULTILINE
        )

        for match in part_pattern.finditer(content):
            try:
                pid = int(match.group(1))
                if 0 < pid < 1000000:  # Reasonable PID range
                    part_ids.add(pid)
            except ValueError:
                continue

        # Method 2: *ELEMENT_SOLID with PID field
        element_pattern = re.compile(
            r'\*ELEMENT_SOLID[^\n]*\n'
            r'(?:\$[^\n]*\n)*'  # Skip comment lines
            r'\s*\d+\s*,?\s*(\d+)',  # eid, pid
            re.IGNORECASE | re.MULTILINE
        )

        for match in element_pattern.finditer(content):
            try:
                pid = int(match.group(1))
                if 0 < pid < 1000000:
                    part_ids.add(pid)
            except ValueError:
                continue

        # Method 3: *SET_PART
        set_part_pattern = re.compile(
            r'\*SET_PART[^\n]*\n'
            r'(?:\$[^\n]*\n)*'  # Skip comments
            r'[^\n]*\n'         # Set ID line
            r'([\d\s,]+)',      # Part IDs
            re.IGNORECASE | re.MULTILINE
        )

        for match in set_part_pattern.finditer(content):
            numbers = re.findall(r'\d+', match.group(1))
            for num in numbers:
                try:
                    pid = int(num)
                    if 0 < pid < 1000000:
                        part_ids.add(pid)
                except ValueError:
                    continue

        return sorted(list(part_ids))

    def parse_quick(self, filepath: str) -> List[int]:
        """Quick parse - just find numbers after *PART"""
        part_ids: Set[int] = set()

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception as e:
            raise ValueError(f"K파일을 읽을 수 없습니다: {e}")

        in_part_section = False
        for i, line in enumerate(lines):
            line_upper = line.upper().strip()

            if line_upper.startswith('*PART'):
                in_part_section = True
                continue

            if in_part_section and not line_upper.startswith('$'):
                # Try to extract PID from first field
                parts = re.split(r'[,\s]+', line.strip())
                if parts and parts[0]:
                    try:
                        pid = int(parts[0])
                        if 0 < pid < 1000000:
                            part_ids.add(pid)
                    except ValueError:
                        pass
                in_part_section = False

            if line_upper.startswith('*') and not line_upper.startswith('*PART'):
                in_part_section = False

        return sorted(list(part_ids))
