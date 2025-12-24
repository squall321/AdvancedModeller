"""DOE Script Generator

Generates KooMeshModifier scripts from DOE placement results.
"""
from typing import List, Optional
from pathlib import Path
from .spatial_utils import DOEResult, Placement


class DOEScriptGenerator:
    """Generate scripts for DOE-based package translation"""

    def __init__(self, k_file_path: Optional[str] = None):
        """
        Initialize script generator.

        Args:
            k_file_path: Path to input K-file (optional)
        """
        self.k_file_path = k_file_path
        self.script_content = None

    def generate_script(
        self,
        doe_result: DOEResult,
        output_name: str = "doe_translation"
    ) -> str:
        """
        Generate script from DOE result.

        Args:
            doe_result: DOE placement result
            output_name: Output file name prefix

        Returns:
            Generated script content as string
        """
        lines = []

        # Header
        lines.append("*Inputfile")
        if self.k_file_path:
            lines.append(Path(self.k_file_path).name)
        else:
            lines.append("InputFileExample.k")

        lines.append("*Mode")
        lines.append("TRANSLATION_DOE,1")
        lines.append("**Translation_DOE,1")

        # Get valid placements only
        valid_placements = [p for p in doe_result.placements if p.is_valid]

        if not valid_placements:
            raise ValueError("No valid placements to generate script")

        # Extract X, Y displacements from all placements
        pid = doe_result.source_part_id
        x_displacements = [p.dx for p in valid_placements]
        y_displacements = [p.dy for p in valid_placements]
        z_displacements = [0.0] * len(valid_placements)  # Z is always 0 for XY movement

        # Format displacement lists
        x_str = self._format_displacement_list(x_displacements)
        y_str = self._format_displacement_list(y_displacements)
        z_str = self._format_displacement_list(z_displacements)

        # Add translation commands
        lines.append(f"*TranslationX,PID,{x_str}")
        lines.append(f"*TranslationY,PID,{y_str}")
        lines.append(f"*TranslationZ,PID,{z_str}")

        lines.append("**EndTranslation_DOE")
        lines.append("*End")
        lines.append("")  # Empty line at end

        # Store and return
        self.script_content = "\n".join(lines)
        return self.script_content

    def _format_displacement_list(self, displacements: List[float]) -> str:
        """
        Format displacement list as comma-separated string.

        Args:
            displacements: List of displacement values

        Returns:
            Formatted string like "0.1,2.4,0.3"
        """
        # Format each value with 1 decimal place, remove trailing zeros
        formatted = []
        for d in displacements:
            # Format to 2 decimal places
            val_str = f"{d:.2f}"
            # Remove trailing zeros after decimal point
            if '.' in val_str:
                val_str = val_str.rstrip('0').rstrip('.')
            formatted.append(val_str)

        return ",".join(formatted)

    def save_script(self, output_path: str) -> bool:
        """
        Save generated script to file.

        Args:
            output_path: Output file path

        Returns:
            True if successful, False otherwise
        """
        if not self.script_content:
            raise ValueError("No script content to save. Call generate_script() first.")

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(self.script_content)
            return True
        except Exception as e:
            print(f"Failed to save script: {e}")
            return False

    def get_script_preview(self, max_lines: int = 50) -> str:
        """
        Get preview of generated script.

        Args:
            max_lines: Maximum number of lines to show

        Returns:
            Preview text
        """
        if not self.script_content:
            return "No script generated yet."

        lines = self.script_content.split('\n')
        if len(lines) <= max_lines:
            return self.script_content

        # Show first part and indicate truncation
        preview_lines = lines[:max_lines]
        preview_lines.append(f"\n... ({len(lines) - max_lines} more lines)")
        return '\n'.join(preview_lines)
