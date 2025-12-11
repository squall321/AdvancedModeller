# DOE-Based Package Placement Feature Plan

## Overview
After selecting a source part in the Adjacent Parts Viewer, provide a Design of Experiments (DOE) feature that generates multiple placement options for the selected package by finding empty spaces in the XY plane.

## Core Concept

### User Workflow
1. User selects a source part (e.g., "Part 6")
2. Adjacent parts are detected and visualized (current feature)
3. User specifies **DOE count** (e.g., 10, 20, 50 variations)
4. System generates N different (dx, dy) displacement pairs using Latin Hypercube Sampling
5. 3D viewer displays:
   - **Original position**: Black marker at source part center
   - **DOE placement positions**: Dark red markers at each (dx, dy) location
   - **Selected placement preview**: Semi-transparent red source part at selected position
6. User can click through placement options to preview each one
7. Export selected placements to CSV or generate modified keyword cards

### Goal
Generate diverse placement options that:
- Avoid overlapping with adjacent packages in the XY plane
- Sample the available empty space uniformly
- Use Latin Hypercube Sampling (LHS) for efficient space exploration
- Provide clear visual feedback with multiple visualization layers

## Technical Requirements

### 1. Empty Space Detection

**Input:**
- Source part: Selected package with its bounding box
- Adjacent parts: Currently visible parts from detection
- Selected surface: The surface/plane being analyzed (already known from Adjacent Parts Viewer)

**Process:**
1. Extract bounding box of source part in XY plane (ignore Z for now)
2. For each adjacent part:
   - Get its XY bounding box
   - Check if any nodes exist within the source part's bounding box
   - If NO nodes overlap → this part represents a "collision zone" if source moves in XY
3. Build a list of "occupied regions" in XY space

**Output:**
- List of occupied XY bounding boxes (regions to avoid)
- Feasible movement range (min/max dx, min/max dy)

### 2. Latin Hypercube Sampling (LHS)

**Why LHS?**
- Ensures uniform coverage of the feasible space
- Better than random sampling for small sample sizes
- Each displacement is well-distributed in 2D (dx, dy) space

**Implementation:**
```python
from scipy.stats import qmc

def generate_doe_placements(
    occupied_regions: List[BBox2D],
    source_bbox: BBox2D,
    adjacent_bboxes: List[BBox2D],
    num_samples: int
) -> List[Tuple[float, float]]:
    """
    Generate DOE placement options using Latin Hypercube Sampling.

    Returns:
        List of (dx, dy) displacement pairs
    """
    # 1. Determine feasible range
    # Find min/max dx and dy where source doesn't overlap with adjacent parts

    # 2. Create LHS sampler in 2D
    sampler = qmc.LatinHypercube(d=2)
    samples = sampler.random(n=num_samples)

    # 3. Scale samples to feasible range
    # samples are in [0, 1]^2, map to [dx_min, dx_max] × [dy_min, dy_max]

    # 4. Filter out placements that cause collisions
    # Check if source_bbox + (dx, dy) overlaps with any adjacent_bbox

    # 5. Return valid (dx, dy) pairs
    return valid_displacements
```

### 3. Collision Detection Logic

**Definition of Collision:**
A collision occurs when the displaced source part bounding box overlaps with any adjacent part bounding box in XY plane.

```python
def check_collision_2d(
    source_bbox: BBox2D,
    dx: float,
    dy: float,
    adjacent_bboxes: List[BBox2D]
) -> bool:
    """
    Check if moving source by (dx, dy) causes overlap with adjacent parts.

    Returns:
        True if collision detected, False if safe
    """
    # Displaced source bbox
    new_min_x = source_bbox.min_x + dx
    new_max_x = source_bbox.max_x + dx
    new_min_y = source_bbox.min_y + dy
    new_max_y = source_bbox.max_y + dy

    for adj_bbox in adjacent_bboxes:
        # Check 2D box overlap
        x_overlap = not (new_max_x < adj_bbox.min_x or new_min_x > adj_bbox.max_x)
        y_overlap = not (new_max_y < adj_bbox.min_y or new_min_y > adj_bbox.max_y)

        if x_overlap and y_overlap:
            return True  # Collision!

    return False  # Safe
```

### 4. Feasible Range Calculation

**Strategy:**
- Analyze the layout of adjacent parts
- Find the "empty corridors" in XY space
- Define conservative bounds for dx and dy

**Options:**
1. **Conservative:** Only allow movements within gaps between adjacent parts
2. **Aggressive:** Allow movements up to 2× or 3× the source part size
3. **User-defined:** Let user specify max displacement range

**Recommendation:** Start with conservative approach, add user control later.

## 3D Visualization Design

### Visualization Layers

The 3D viewer will display **three distinct visual elements** simultaneously:

#### Layer 1: Adjacent Parts (Background)
- **What**: All adjacent parts detected by the algorithm
- **Color**: Original CAE palette colors with depth-based brightness
- **Render**: Solid surfaces, no edges/wireframe
- **Purpose**: Show the surrounding context

#### Layer 2: Position Markers (Always Visible)
- **Original Position Marker**:
  - **What**: Small sphere or cross at source part center (original location)
  - **Color**: **Black** (RGB: 0.0, 0.0, 0.0)
  - **Size**: Small fixed size (e.g., 5% of source part size)
  - **Purpose**: Reference point to compare displacements

- **DOE Placement Markers**:
  - **What**: Small spheres or crosses at each (dx, dy) displaced center
  - **Color**: **Dark red** (RGB: 0.6, 0.0, 0.0) - distinct from bright source red
  - **Size**: Slightly smaller than original marker (e.g., 3% of source part size)
  - **Count**: N markers for N DOE placements
  - **Purpose**: Show all possible placement locations at once

#### Layer 3: Selected Placement Preview (On Demand)
- **What**: Source part geometry displaced to selected (dx, dy) position
- **Color**: **Semi-transparent bright red** (RGBA: 1.0, 0.2, 0.2, 0.5)
  - Alpha = 0.5 for 50% transparency
  - Bright red to distinguish from dark red markers
- **Render**: Solid surfaces with transparency, no edges
- **Visibility**: Only shown when user clicks/hovers over a placement option
- **Purpose**: Preview what the source part looks like at new position

### Visualization States

**State 1: Initial DOE Generation**
```
User clicks "Generate Placements" button
→ Compute DOE samples
→ Show all markers (black + N dark red dots)
→ No preview geometry yet
```

**State 2: Placement Selection**
```
User clicks "Option 5: dx=+12.3, dy=-8.7" in list
→ Keep all markers visible
→ Add semi-transparent red geometry at (dx=+12.3, dy=-8.7)
→ Camera may optionally focus on this location
```

**State 3: Cycling Through Placements**
```
User clicks through multiple options rapidly
→ All markers stay visible (static)
→ Semi-transparent geometry moves to new position instantly
→ Smooth visual feedback
```

### OpenGL Rendering Implementation

#### Marker Rendering

```python
class DOEMarkerRenderer:
    """Renders position markers for original and DOE placements."""

    def __init__(self):
        self._marker_vbo = None
        self._marker_positions = []
        self._marker_colors = []

    def set_markers(
        self,
        original_pos: np.ndarray,  # [x, y, z]
        doe_positions: List[np.ndarray]  # List of [x+dx, y+dy, z]
    ):
        """
        Set marker positions for rendering.

        Args:
            original_pos: Center of source part at original location
            doe_positions: Centers at each DOE displaced location
        """
        self._marker_positions = []
        self._marker_colors = []

        # Original position marker - BLACK
        self._marker_positions.append(original_pos)
        self._marker_colors.append([0.0, 0.0, 0.0, 1.0])  # Black, opaque

        # DOE placement markers - DARK RED
        for doe_pos in doe_positions:
            self._marker_positions.append(doe_pos)
            self._marker_colors.append([0.6, 0.0, 0.0, 1.0])  # Dark red, opaque

        self._build_vbo()

    def _build_vbo(self):
        """Build VBO for point rendering or small sphere geometry."""
        # Option 1: GL_POINTS with large point size
        # Option 2: Small sphere meshes at each position
        # Option 3: Billboard quads always facing camera
        pass

    def render(self, camera: Camera):
        """Render all markers."""
        # Enable point rendering or instanced sphere rendering
        # Use _marker_vbo to draw all markers in single call
        pass
```

#### Transparent Geometry Rendering

```python
class DOEPreviewRenderer:
    """Renders semi-transparent source part at selected DOE position."""

    def __init__(self, mesh_data: MeshData):
        self._mesh_data = mesh_data
        self._preview_vbo = None
        self._displacement = (0.0, 0.0)  # Current (dx, dy)
        self._visible = False

    def set_preview(
        self,
        source_part_id: int,
        dx: float,
        dy: float,
        visible: bool = True
    ):
        """
        Set which placement to preview.

        Args:
            source_part_id: Part ID to render
            dx, dy: Displacement from original position
            visible: Whether to show preview
        """
        self._source_part_id = source_part_id
        self._displacement = (dx, dy)
        self._visible = visible

        if visible:
            self._build_preview_vbo()

    def _build_preview_vbo(self):
        """
        Build VBO for displaced source part geometry.

        Steps:
        1. Extract source part vertices from mesh_data
        2. Apply displacement: vertices[:, 0] += dx, vertices[:, 1] += dy
        3. Set color to semi-transparent red: (1.0, 0.2, 0.2, 0.5)
        4. Build VBO with displaced vertices + colors
        """
        part_id = self._source_part_id
        dx, dy = self._displacement

        # Get source part geometry
        elem_indices = self._mesh_data.part_elements[part_id]
        vertices = []

        for elem_idx in elem_indices:
            node_list = self._mesh_data.elements[elem_idx]
            coords = self._mesh_data.nodes[node_list].copy()

            # Apply displacement in XY plane
            coords[:, 0] += dx
            coords[:, 1] += dy

            vertices.append(coords)

        vertices = np.vstack(vertices)

        # Create color array: semi-transparent red
        colors = np.full((len(vertices), 4), [1.0, 0.2, 0.2, 0.5], dtype=np.float32)

        # Build VBO
        self._preview_vbo = self._create_vbo(vertices, colors)

    def render(self, camera: Camera):
        """Render preview if visible."""
        if not self._visible or self._preview_vbo is None:
            return

        # Enable alpha blending for transparency
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Disable depth write to prevent occlusion artifacts
        glDepthMask(GL_FALSE)

        # Render preview geometry
        self._render_vbo(self._preview_vbo)

        # Restore state
        glDepthMask(GL_TRUE)
        glDisable(GL_BLEND)
```

#### Integration with VBO Renderer

```python
# In results_panel.py or gl_widget.py

class DOEVisualizationManager:
    """Manages all DOE visualization layers."""

    def __init__(self, gl_widget):
        self._gl_widget = gl_widget
        self._marker_renderer = DOEMarkerRenderer()
        self._preview_renderer = DOEPreviewRenderer(gl_widget.mesh_data)

        self._source_part_id = None
        self._doe_placements = []  # List of (dx, dy) tuples
        self._selected_placement_idx = None

    def set_doe_results(
        self,
        source_part_id: int,
        placements: List[Tuple[float, float]],
        source_center: np.ndarray
    ):
        """
        Set DOE results and prepare visualization.

        Args:
            source_part_id: Source part ID
            placements: List of (dx, dy) displacement pairs
            source_center: [x, y, z] center of source part
        """
        self._source_part_id = source_part_id
        self._doe_placements = placements
        self._selected_placement_idx = None

        # Calculate displaced centers for markers
        doe_centers = []
        for dx, dy in placements:
            displaced_center = source_center.copy()
            displaced_center[0] += dx
            displaced_center[1] += dy
            doe_centers.append(displaced_center)

        # Update marker renderer
        self._marker_renderer.set_markers(
            original_pos=source_center,
            doe_positions=doe_centers
        )

        # Hide preview initially
        self._preview_renderer.set_preview(
            source_part_id, 0.0, 0.0, visible=False
        )

        self._gl_widget.update()

    def select_placement(self, placement_idx: int):
        """
        Select a placement option to preview.

        Args:
            placement_idx: Index into self._doe_placements list
        """
        if placement_idx < 0 or placement_idx >= len(self._doe_placements):
            # Hide preview if invalid index
            self._preview_renderer.set_preview(
                self._source_part_id, 0.0, 0.0, visible=False
            )
            self._selected_placement_idx = None
        else:
            dx, dy = self._doe_placements[placement_idx]
            self._preview_renderer.set_preview(
                self._source_part_id, dx, dy, visible=True
            )
            self._selected_placement_idx = placement_idx

        self._gl_widget.update()

    def render(self, camera: Camera):
        """Render all DOE visualization layers."""
        # Layer 1: Adjacent parts (rendered by main VBO renderer)
        # Layer 2: Position markers
        self._marker_renderer.render(camera)
        # Layer 3: Selected placement preview
        self._preview_renderer.render(camera)

    def clear(self):
        """Clear all DOE visualization."""
        self._marker_renderer.set_markers(
            original_pos=np.zeros(3),
            doe_positions=[]
        )
        self._preview_renderer.set_preview(
            None, 0.0, 0.0, visible=False
        )
        self._gl_widget.update()
```

### Visual Design Specifications

| Element | Color (RGB/RGBA) | Size | Render Mode | Purpose |
|---------|------------------|------|-------------|---------|
| Original Position Marker | (0.0, 0.0, 0.0, 1.0) Black | 5% of source bbox | Point/Sphere | Reference |
| DOE Placement Markers | (0.6, 0.0, 0.0, 1.0) Dark Red | 3% of source bbox | Point/Sphere | Show all options |
| Preview Geometry | (1.0, 0.2, 0.2, 0.5) Semi-transparent Red | Full source part | Transparent mesh | Selected preview |
| Adjacent Parts | Original CAE colors | Full geometry | Solid | Context |

### User Interaction Flow

```
1. User: Click "Generate Placements"
   → System: Compute DOE samples
   → Viewer: Show black marker + dark red markers
   → List: Populate placement options

2. User: Hover over "Option 3" in list
   → Viewer: Highlight corresponding dark red marker (optional)

3. User: Click "Option 3: dx=+12.3, dy=-8.7"
   → Viewer: Show semi-transparent red geometry at (dx, dy)
   → List: Highlight selected row

4. User: Click "Option 7: dx=-5.1, dy=+22.4"
   → Viewer: Move semi-transparent geometry to new position
   → All markers remain visible

5. User: Click empty space or "Clear Preview"
   → Viewer: Hide semi-transparent geometry
   → Markers remain visible
```

## UI Design

### New Control Panel Elements

Add to `control_panel.py`:

```
┌─────────────────────────────────┐
│ Adjacent Parts Detection        │
├─────────────────────────────────┤
│ Max Adjacency:    [50    ] m    │
│ Bbox Offset:      [5.0   ]      │
│ View Direction:   [Top  ▼]      │
│                                 │
│ ─── DOE Placement ───           │
│ DOE Count:        [20    ]      │
│ Max Displacement: [100   ] mm   │
│                                 │
│ [Generate Placements]           │
│ [Clear Preview]                 │
│ [Export to CSV]                 │
└─────────────────────────────────┘
```

**New Parameters:**
- `doe_count`: Number of placement options (default: 20)
- `max_displacement`: Maximum XY movement allowed (default: 100mm)

**New Buttons:**
- `Generate Placements`: Compute DOE samples and show markers
- `Clear Preview`: Hide semi-transparent preview geometry
- `Export to CSV`: Save (dx, dy) pairs to file

### Results Display

Extend `results_panel.py` to show:

```
┌─────────────────────────────────┐
│ 🔴 Part 6 [SOURCE]              │
│ ────────────────────────────    │
│ Part 12                         │
│ Part 15                         │
│ Part 23                         │
│                                 │
│ ─── DOE Placements (20) ───     │
│ ○ Option 1: dx=+15.3, dy=-8.2   │ ← Not selected (○)
│ ● Option 2: dx=-22.1, dy=+12.4  │ ← Selected (●)
│ ○ Option 3: dx=+8.7, dy=+18.9   │
│ ○ Option 4: dx=-3.2, dy=-15.6   │
│ ...                             │
│                                 │
│ [3D Viewer - Interactive]       │
│  • Black dot: Original position │
│  • Dark red dots: DOE options   │
│  • Transparent red: Preview     │
└─────────────────────────────────┘
```

**Interaction:**
- Click placement option → Show semi-transparent preview + highlight marker
- Hover over option → Highlight corresponding dark red marker (optional)
- Double-click option → Export this specific placement to keyword
- Click empty space → Clear preview geometry

## Implementation Plan

### Phase 1: Core Algorithm
**Files**: `gui/modules/adjacent_parts_viewer/core/doe_placement.py`

Tasks:
1. ✅ Create `DOEPlacementGenerator` class
2. ✅ Implement `get_2d_bbox()` to extract XY bounding boxes
3. ✅ Implement `check_collision()` for 2D overlap detection
4. ✅ Implement `sample_lhs()` using scipy.stats.qmc
5. ✅ Implement `calculate_feasible_range()` to find min/max dx/dy
6. ✅ Implement `generate_placements()` main function
7. ✅ Add filtering to remove collision placements
8. ✅ Return list of valid (dx, dy) pairs with metadata

**Time Estimate**: 3-4 hours

### Phase 2: Visualization Rendering
**Files**:
- `gui/modules/model_viewer/backends/vbo_renderer.py` (extend)
- `gui/modules/adjacent_parts_viewer/rendering/doe_markers.py` (new)
- `gui/modules/adjacent_parts_viewer/rendering/doe_preview.py` (new)

Tasks:
1. ✅ Create `DOEMarkerRenderer` class
2. ✅ Implement marker position calculation (original + displaced)
3. ✅ Build marker VBO (sphere geometry or GL_POINTS)
4. ✅ Render markers with black/dark red colors
5. ✅ Create `DOEPreviewRenderer` class
6. ✅ Implement displaced geometry VBO building
7. ✅ Enable OpenGL alpha blending for transparency
8. ✅ Render semi-transparent geometry (RGBA: 1.0, 0.2, 0.2, 0.5)
9. ✅ Create `DOEVisualizationManager` to coordinate rendering
10. ✅ Integrate with existing VBO renderer pipeline

**Time Estimate**: 4-5 hours

### Phase 3: UI Integration
**Files**:
- `gui/modules/adjacent_parts_viewer/widgets/control_panel.py` (modify)
- `gui/modules/adjacent_parts_viewer/widgets/results_panel.py` (modify)

Tasks:
1. ✅ Add DOE controls to control panel (count, max displacement)
2. ✅ Add "Generate Placements" button with signal
3. ✅ Add "Clear Preview" and "Export to CSV" buttons
4. ✅ Extend results panel to display placement list
5. ✅ Add selection indicator (● vs ○) for placement items
6. ✅ Connect list item click to preview rendering
7. ✅ Update 3D viewer when placement selected
8. ✅ Store DOE results in results panel state
9. ✅ Add legend/help text explaining marker colors

**Time Estimate**: 3-4 hours

### Phase 4: Module Coordination
**Files**:
- `gui/modules/adjacent_parts_viewer/module.py` (modify)

Tasks:
1. ✅ Connect "Generate Placements" button to DOE generator
2. ✅ Pass MeshData and source/adjacent part IDs to generator
3. ✅ Receive DOE results and forward to results panel
4. ✅ Initialize DOEVisualizationManager in results panel
5. ✅ Connect placement selection signal to visualization
6. ✅ Handle clear preview action
7. ✅ Implement CSV export functionality

**Time Estimate**: 2-3 hours

### Phase 5: Export/Output
**Files**:
- `gui/modules/adjacent_parts_viewer/export/doe_exporter.py` (new)

Tasks:
1. ✅ Implement CSV export (columns: placement_id, dx, dy, is_valid)
2. ✅ Add header with metadata (source part, DOE count, timestamp)
3. ✅ Optional: Generate modified keyword cards for selected placement
4. ✅ Optional: Batch export all placements as separate keyword files

**Time Estimate**: 2-3 hours

**Total Estimated Time**: 14-19 hours

## File Structure

```
gui/modules/adjacent_parts_viewer/
├── core/
│   ├── fast_detector.py          # Existing
│   ├── doe_placement.py          # NEW - LHS sampling & collision detection
│   └── spatial_utils.py          # NEW - 2D bbox operations
├── rendering/
│   ├── __init__.py               # NEW
│   ├── doe_markers.py            # NEW - Marker rendering (black/dark red)
│   ├── doe_preview.py            # NEW - Transparent geometry preview
│   └── visualization_manager.py  # NEW - Coordinate all DOE rendering
├── export/
│   ├── __init__.py               # NEW
│   └── doe_exporter.py           # NEW - CSV export, keyword generation
├── widgets/
│   ├── control_panel.py          # MODIFY - Add DOE controls
│   └── results_panel.py          # MODIFY - Display placements, manage viz
└── module.py                     # MODIFY - Connect DOE pipeline
```

## Key Functions to Implement

### `doe_placement.py`

```python
class DOEPlacementGenerator:
    def __init__(self, mesh_data: MeshData):
        self.mesh_data = mesh_data

    def generate_placements(
        self,
        source_part_id: int,
        adjacent_part_ids: List[int],
        num_samples: int,
        max_displacement: float
    ) -> DOEResult:
        """
        Generate DOE-based placement options.

        Returns:
            DOEResult with placements, source center, and metadata
        """
        pass

    def get_2d_bbox(self, part_id: int) -> BBox2D:
        """Extract XY bounding box for a part."""
        pass

    def get_part_center(self, part_id: int) -> np.ndarray:
        """Get [x, y, z] center of a part."""
        pass

    def check_collision(
        self,
        source_bbox: BBox2D,
        dx: float,
        dy: float,
        adjacent_bboxes: List[BBox2D]
    ) -> bool:
        """Check if displacement causes collision."""
        pass

    def calculate_feasible_range(
        self,
        source_bbox: BBox2D,
        adjacent_bboxes: List[BBox2D],
        max_displacement: float
    ) -> Tuple[float, float, float, float]:
        """
        Calculate feasible (dx_min, dx_max, dy_min, dy_max).

        Returns conservative bounds where source won't collide.
        """
        pass

    def sample_lhs(
        self,
        num_samples: int,
        bounds: Tuple[float, float, float, float]
    ) -> np.ndarray:
        """Generate LHS samples in feasible region."""
        from scipy.stats import qmc
        sampler = qmc.LatinHypercube(d=2)
        samples = sampler.random(n=num_samples)
        # Scale to bounds
        return scaled_samples
```

### Data Structures

```python
@dataclass
class BBox2D:
    min_x: float
    max_x: float
    min_y: float
    max_y: float

    def overlaps(self, other: 'BBox2D') -> bool:
        """Check if this bbox overlaps with another in 2D."""
        x_overlap = not (self.max_x < other.min_x or self.min_x > other.max_x)
        y_overlap = not (self.max_y < other.min_y or self.min_y > other.max_y)
        return x_overlap and y_overlap

    def width(self) -> float:
        return self.max_x - self.min_x

    def height(self) -> float:
        return self.max_y - self.min_y

@dataclass
class Placement:
    index: int              # Placement option number (0, 1, 2, ...)
    dx: float               # X displacement
    dy: float               # Y displacement
    is_valid: bool          # True if no collision
    collision_parts: List[int]  # Part IDs that collide (empty if valid)
    center: np.ndarray      # [x+dx, y+dy, z] displaced center
    score: float = 0.0      # Quality metric (optional)

@dataclass
class DOEResult:
    source_part_id: int
    source_center: np.ndarray     # Original [x, y, z]
    placements: List[Placement]   # All DOE placement options
    num_valid: int                # Count of collision-free placements
    num_total: int                # Total samples attempted
    max_displacement: float       # Max displacement used
    feasible_bounds: Tuple[float, float, float, float]  # (dx_min, dx_max, dy_min, dy_max)
```

### `doe_markers.py`

```python
class DOEMarkerRenderer:
    """Renders position markers for original and DOE placements."""

    def __init__(self):
        self._vbo = None
        self._positions = np.array([])
        self._colors = np.array([])
        self._marker_size = 1.0

    def set_markers(
        self,
        original_pos: np.ndarray,
        doe_positions: List[np.ndarray],
        marker_size: float = 1.0
    ):
        """Set marker data and build VBO."""
        pass

    def render(self, camera: Camera):
        """Render all markers."""
        # Use GL_POINTS with glPointSize() or instanced sphere rendering
        pass
```

### `doe_preview.py`

```python
class DOEPreviewRenderer:
    """Renders semi-transparent source part at selected position."""

    def __init__(self, mesh_data: MeshData):
        self._mesh_data = mesh_data
        self._vbo = None
        self._visible = False

    def set_preview(
        self,
        source_part_id: int,
        dx: float,
        dy: float,
        visible: bool = True
    ):
        """Set preview displacement and rebuild VBO."""
        pass

    def render(self, camera: Camera):
        """Render with alpha blending."""
        if not self._visible:
            return

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthMask(GL_FALSE)

        # Render VBO

        glDepthMask(GL_TRUE)
        glDisable(GL_BLEND)
```

## Edge Cases to Handle

1. **No feasible space:** All sampled positions collide
   - Solution: Increase max_displacement or try more samples
   - Show warning: "No valid placements found. Try increasing max displacement."

2. **Very tight layout:** Source part surrounded by adjacent parts
   - Solution: Use smaller displacement range automatically
   - May result in very few valid placements (e.g., 3 out of 20)

3. **Isolated source part:** No adjacent parts nearby
   - Solution: Use full displacement range
   - All samples likely valid, uniformly distributed

4. **Non-convex feasible region:** Complex gap patterns
   - Solution: LHS samples uniformly, filter removes invalid ones
   - May need to generate 2-3× samples to get desired valid count

5. **Large DOE count (>100):** Rendering performance
   - Solution: Use instanced rendering for markers
   - Limit max DOE count in UI (e.g., 200)

6. **Z-coordinate handling:** Source parts at different heights
   - Solution: Keep Z unchanged in Phase 1
   - Future: Add optional Z displacement

## Testing Strategy

### Unit Tests

```python
def test_bbox_overlap():
    """Test 2D bounding box overlap detection."""
    bbox1 = BBox2D(0, 10, 0, 10)
    bbox2 = BBox2D(5, 15, 5, 15)
    assert bbox1.overlaps(bbox2) == True

    bbox3 = BBox2D(20, 30, 20, 30)
    assert bbox1.overlaps(bbox3) == False

def test_lhs_sampling():
    """Test LHS produces uniform distribution."""
    generator = DOEPlacementGenerator(mesh_data)
    samples = generator.sample_lhs(
        num_samples=100,
        bounds=(-50, 50, -50, 50)
    )
    assert samples.shape == (100, 2)
    assert np.all(samples[:, 0] >= -50) and np.all(samples[:, 0] <= 50)
    assert np.all(samples[:, 1] >= -50) and np.all(samples[:, 1] <= 50)

def test_collision_detection():
    """Test collision detection accuracy."""
    generator = DOEPlacementGenerator(mesh_data)
    source_bbox = BBox2D(0, 10, 0, 10)
    adjacent_bboxes = [BBox2D(15, 25, 0, 10)]

    # No collision
    assert generator.check_collision(source_bbox, 0, 0, adjacent_bboxes) == False

    # Collision
    assert generator.check_collision(source_bbox, 10, 0, adjacent_bboxes) == True
```

### Integration Tests

```python
def test_generate_placements_no_collision():
    """Test that valid placements have no collisions."""
    generator = DOEPlacementGenerator(mesh_data)
    result = generator.generate_placements(
        source_part_id=6,
        adjacent_part_ids=[12, 15, 23],
        num_samples=20,
        max_displacement=100.0
    )

    for placement in result.placements:
        if placement.is_valid:
            assert len(placement.collision_parts) == 0

def test_visualization_markers():
    """Test marker rendering produces correct output."""
    renderer = DOEMarkerRenderer()
    renderer.set_markers(
        original_pos=np.array([0, 0, 0]),
        doe_positions=[np.array([10, 5, 0]), np.array([-5, 15, 0])]
    )

    # Check VBO built correctly
    assert renderer._positions.shape[0] == 3  # 1 original + 2 DOE
```

### Manual Testing Scenarios

1. **Small DOE count (5 samples)**
   - Verify all 5 markers visible
   - Check color distinction (black vs dark red)
   - Preview transparency looks correct

2. **Large DOE count (50 samples)**
   - Performance acceptable (<100ms render)
   - All markers visible, not cluttered
   - Selection responsive

3. **Tight layout**
   - Few valid placements
   - Warning message displayed
   - Preview geometry doesn't overlap adjacent parts

4. **Loose layout**
   - Most/all placements valid
   - Markers well-distributed
   - Preview works at boundary positions

5. **Rapid cycling**
   - Click through 20 options quickly
   - Preview geometry updates smoothly
   - No lag or visual artifacts

## Success Criteria

✅ Feature is successful if:

1. **Algorithm**:
   - Generated placements uniformly cover available empty space
   - No valid placement causes collision with adjacent parts
   - Computation completes in <1 second for 20-50 samples

2. **Visualization**:
   - Black marker clearly visible at original position
   - Dark red markers distinct and easy to see
   - Semi-transparent preview provides clear visual feedback
   - No Z-fighting or rendering artifacts

3. **User Experience**:
   - Intuitive workflow: generate → select → preview → export
   - Responsive interaction (<100ms to update preview)
   - Clear visual feedback for selected placement
   - Export produces correct (dx, dy) values

4. **Performance**:
   - Rendering 50+ markers at 60 FPS
   - Transparent geometry render has minimal performance impact
   - No memory leaks after multiple generations

## Future Enhancements

1. **3D Placement**: Extend to (dx, dy, dz) with Z-direction constraints
2. **Interactive dragging**: User drags preview, snaps to nearest valid position
3. **Marker picking**: Click on marker in 3D view to select that placement
4. **Heatmap overlay**: Color-code feasible region by "quality" metric
5. **Multi-source DOE**: Generate placements for multiple parts simultaneously
6. **Animation**: Smooth transition when cycling through placements
7. **Collision margin**: Add user-adjustable safety gap (e.g., 2mm minimum clearance)
8. **Export to LS-OPT**: Generate input files for optimization software

## Summary

This feature transforms the Adjacent Parts Viewer into a powerful design exploration tool by:

1. **Generating** diverse placement options using rigorous Latin Hypercube Sampling
2. **Visualizing** all options simultaneously with three distinct visual layers
3. **Previewing** selected placements with semi-transparent geometry
4. **Exporting** results for further analysis or optimization

The visualization design ensures users can:
- **See the context** (adjacent parts in original colors)
- **Compare options** (all markers visible at once)
- **Evaluate placements** (transparent preview shows fit)
- **Make decisions** (click to select, export to use)

The key insight: **Empty space between adjacent parts = design space for exploration**.
