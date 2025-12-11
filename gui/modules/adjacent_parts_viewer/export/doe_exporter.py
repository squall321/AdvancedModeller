"""
DOE placement exporter.

Exports DOE results to CSV format for analysis or further processing.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Optional

from gui.modules.adjacent_parts_viewer.core.spatial_utils import DOEResult


class DOEExporter:
    """Exports DOE placement results to CSV."""

    @staticmethod
    def export_to_csv(
        doe_result: DOEResult,
        output_path: str,
        include_invalid: bool = False
    ) -> bool:
        """
        Export DOE result to CSV file.

        Args:
            doe_result: DOE result to export
            output_path: Output CSV file path
            include_invalid: Whether to include invalid (collision) placements

        Returns:
            True if export successful, False otherwise
        """
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Write header metadata
                writer.writerow(['# DOE Placement Export'])
                writer.writerow(['# Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow(['# Source Part ID:', doe_result.source_part_id])
                writer.writerow(['# Source Center:',
                                f'x={doe_result.source_center[0]:.3f}, '
                                f'y={doe_result.source_center[1]:.3f}, '
                                f'z={doe_result.source_center[2]:.3f}'])
                writer.writerow(['# Max Displacement:', f'{doe_result.max_displacement:.1f} mm'])
                writer.writerow(['# Feasible Bounds (dx_min, dx_max, dy_min, dy_max):',
                                f'{doe_result.feasible_bounds[0]:.2f}, '
                                f'{doe_result.feasible_bounds[1]:.2f}, '
                                f'{doe_result.feasible_bounds[2]:.2f}, '
                                f'{doe_result.feasible_bounds[3]:.2f}'])
                writer.writerow(['# Valid Placements:', f'{doe_result.num_valid}/{doe_result.num_total}'])
                writer.writerow([])  # Empty line

                # Write column headers
                headers = [
                    'Option',
                    'dx (mm)',
                    'dy (mm)',
                    'Valid',
                    'New_X',
                    'New_Y',
                    'New_Z',
                    'Score',
                    'Collision_Parts'
                ]
                writer.writerow(headers)

                # Write placement data
                for placement in doe_result.placements:
                    # Skip invalid placements if requested
                    if not include_invalid and not placement.is_valid:
                        continue

                    row = [
                        placement.index + 1,  # 1-indexed for user
                        f'{placement.dx:.3f}',
                        f'{placement.dy:.3f}',
                        'Yes' if placement.is_valid else 'No',
                        f'{placement.center[0]:.3f}',
                        f'{placement.center[1]:.3f}',
                        f'{placement.center[2]:.3f}',
                        f'{placement.score:.3f}',
                        ','.join(map(str, placement.collision_parts)) if placement.collision_parts else ''
                    ]
                    writer.writerow(row)

            return True

        except Exception as e:
            print(f"Error exporting DOE results: {e}")
            return False

    @staticmethod
    def get_default_filename(doe_result: DOEResult) -> str:
        """
        Generate default filename for export.

        Args:
            doe_result: DOE result

        Returns:
            Default filename string
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"doe_placement_part{doe_result.source_part_id}_{timestamp}.csv"

    @staticmethod
    def export_summary(doe_result: DOEResult, output_path: str) -> bool:
        """
        Export a summary text file with DOE statistics.

        Args:
            doe_result: DOE result to export
            output_path: Output text file path

        Returns:
            True if export successful, False otherwise
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("DOE Placement Summary\n")
                f.write("=" * 50 + "\n\n")

                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                f.write(f"Source Part ID: {doe_result.source_part_id}\n")
                f.write(f"Source Center: ({doe_result.source_center[0]:.2f}, "
                       f"{doe_result.source_center[1]:.2f}, "
                       f"{doe_result.source_center[2]:.2f})\n\n")

                f.write(f"Max Displacement: {doe_result.max_displacement:.1f} mm\n")
                f.write(f"Feasible Bounds:\n")
                f.write(f"  dx: [{doe_result.feasible_bounds[0]:.2f}, {doe_result.feasible_bounds[1]:.2f}] mm\n")
                f.write(f"  dy: [{doe_result.feasible_bounds[2]:.2f}, {doe_result.feasible_bounds[3]:.2f}] mm\n\n")

                f.write(f"Total Samples: {doe_result.num_total}\n")
                f.write(f"Valid Placements: {doe_result.num_valid}\n")
                f.write(f"Invalid Placements: {doe_result.num_total - doe_result.num_valid}\n")
                f.write(f"Success Rate: {doe_result.num_valid / doe_result.num_total * 100:.1f}%\n\n")

                # Statistics on valid placements
                valid_placements = [p for p in doe_result.placements if p.is_valid]
                if valid_placements:
                    f.write("Valid Placement Statistics:\n")
                    f.write("-" * 50 + "\n")

                    dx_values = [p.dx for p in valid_placements]
                    dy_values = [p.dy for p in valid_placements]
                    scores = [p.score for p in valid_placements]

                    f.write(f"dx range: [{min(dx_values):.2f}, {max(dx_values):.2f}] mm\n")
                    f.write(f"dy range: [{min(dy_values):.2f}, {max(dy_values):.2f}] mm\n")
                    f.write(f"Score range: [{min(scores):.2f}, {max(scores):.2f}]\n\n")

                    # Best placement (highest score)
                    best = max(valid_placements, key=lambda p: p.score)
                    f.write(f"Best Placement (highest score):\n")
                    f.write(f"  Option {best.index + 1}\n")
                    f.write(f"  dx = {best.dx:.2f} mm, dy = {best.dy:.2f} mm\n")
                    f.write(f"  Score = {best.score:.2f}\n")

            return True

        except Exception as e:
            print(f"Error exporting summary: {e}")
            return False
