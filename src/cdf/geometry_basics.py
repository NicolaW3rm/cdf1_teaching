import math
import random
import  Rhino.Geometry as rg


'GEOMETRIES'

def create_sphere(base_point=None, radius=5.0):
    """
    Build a sphere as a Brep.

    base_point : Rhino.Geometry.Point3d -- center of the sphere
    radius     : float -- sphere radius

    Returns a Rhino.Geometry.Brep.
    """
    if base_point is None:
        base_point = rg.Point3d(0, 0, 0)
    if radius is None:
        radius = 5.0

    sphere = rg.Sphere(base_point, radius)
    return sphere.ToBrep()

def random_colors_for_spheres(spheres, seed, color1, color2, color3):
    """
    Pick a reproducible random color from a palette for each sphere.

    spheres : Rhino.Geometry.Brep or sequence -- sphere Brep(s) to color
    seed : int or str -- seed controlling the repeatable color assignments
    color1, color2, color3 : colors supplied by Grasshopper color swatches

    Returns a list of colors in the same order as the spheres, suitable for
    Grasshopper Custom Preview.
    """
    if spheres is None:
        raise ValueError("spheres must be provided.")
    sphere_items = [spheres] if isinstance(spheres, rg.Brep) else list(spheres)
    if not sphere_items:
        return []
    provided_colors = [color1, color2, color3]
    if any(color is None for color in provided_colors):
        raise ValueError("color1, color2, and color3 must all be provided.")
    palette = []
    for color in provided_colors:
        if color not in palette:
            palette.append(color)
    if len(palette) < 2:
        raise ValueError("At least two different colors must be provided.")

    generator = random.Random(seed)
    colors = []
    while len(colors) < len(sphere_items):
        color_cycle = palette[:]
        generator.shuffle(color_cycle)
        if len(color_cycle) > 1 and colors and color_cycle[0] == colors[-1]:
            color_cycle[0], color_cycle[1] = color_cycle[1], color_cycle[0]
        colors.extend(color_cycle)
    return colors[:len(sphere_items)]

def create_cuboid_frame(
    base_plane=None,
    width=10.0,
    height=5.0,
    length=8.0,
    border_width=1.0,
):
    """
    Build an open cuboid cage from twelve joined edge beams.

    base_plane : Rhino.Geometry.Plane -- center plane defining the cuboid axes
    width : float -- overall size along the plane's X axis
    height : float -- overall size along the plane's Y axis
    length : float -- overall size along the plane's normal
    border_width : float -- square cross-section width of each edge beam

    Returns a closed Rhino.Geometry.Brep with open faces.
    """
    if width <= 0 or height <= 0 or length <= 0:
        raise ValueError("width, height, and length must be positive.")
    if border_width <= 0 or 2 * border_width >= min(width, height, length):
        raise ValueError(
            "border_width must be positive and leave an opening on every face."
        )
    if base_plane is None:
        base_plane = rg.Plane.WorldXY

    half_width = width / 2.0
    half_height = height / 2.0
    half_length = length / 2.0
    half_border = border_width / 2.0
    origin = base_plane.Origin

    def make_beam(center, beam_axis, cross_axis, depth_axis, beam_length):
        beam_plane = rg.Plane(
            center
            - beam_axis * (beam_length / 2.0)
            - cross_axis * half_border
            - depth_axis * half_border,
            beam_axis,
            cross_axis,
        )
        box = rg.Box(
            beam_plane,
            rg.Interval(0.0, beam_length),
            rg.Interval(0.0, border_width),
            rg.Interval(0.0, border_width),
        )
        return box.ToBrep()

    beams = []
    for y_sign in (-1.0, 1.0):
        for z_sign in (-1.0, 1.0):
            center = (
                origin
                + base_plane.YAxis * (y_sign * (half_height - half_border))
                + base_plane.Normal * (z_sign * (half_length - half_border))
            )
            beams.append(
                make_beam(
                    center,
                    base_plane.XAxis,
                    base_plane.YAxis,
                    base_plane.Normal,
                    width,
                )
            )

    for x_sign in (-1.0, 1.0):
        for z_sign in (-1.0, 1.0):
            center = (
                origin
                + base_plane.XAxis * (x_sign * (half_width - half_border))
                + base_plane.Normal * (z_sign * (half_length - half_border))
            )
            beams.append(
                make_beam(
                    center,
                    base_plane.YAxis,
                    base_plane.Normal,
                    base_plane.XAxis,
                    height,
                )
            )

    for x_sign in (-1.0, 1.0):
        for y_sign in (-1.0, 1.0):
            center = (
                origin
                + base_plane.XAxis * (x_sign * (half_width - half_border))
                + base_plane.YAxis * (y_sign * (half_height - half_border))
            )
            beams.append(
                make_beam(
                    center,
                    base_plane.ZAxis,
                    base_plane.XAxis,
                    base_plane.YAxis,
                    length,
                )
            )

    tolerance = 0.001
    frame = rg.Brep.CreateBooleanUnion(beams, tolerance)
    if not frame:
        raise RuntimeError("Could not join the cuboid frame beams.")
    if len(frame) != 1:
        raise RuntimeError("The cuboid frame beams did not join into one solid.")
    return frame[0]

def create_cylinder_along_curve(curve, radius):
    """
    Create a capped cylindrical pipe following a curve.

    curve : Rhino.Geometry.Curve -- centerline path for the cylinder
    radius : float -- radius of the circular cross-section

    Returns a list of Rhino.Geometry.Brep pipe sections.
    """
    if not isinstance(curve, rg.Curve):
        raise TypeError("curve must be a Rhino.Geometry.Curve.")
    if not curve.IsValid or curve.GetLength() <= 0:
        raise ValueError("curve must be a valid, non-zero-length curve.")
    if radius is None or radius <= 0:
        raise ValueError("radius must be positive.")

    tolerance = 0.001
    angle_tolerance = math.radians(1.0)
    pipes = rg.Brep.CreatePipe(
        curve,
        radius,
        False,
        rg.PipeCapMode.Flat,
        False,
        tolerance,
        angle_tolerance,
    )
    if not pipes:
        raise RuntimeError("Rhino could not create a cylinder along the curve.")
    if any(not pipe.IsValid for pipe in pipes):
        raise RuntimeError("Rhino created an invalid cylinder along the curve.")
    return list(pipes)

#NOT USED
def create_cone(base_point=None, height=10.0, radius=5.0, cap_bottom=True):
    """
    Build a cone as a Brep.

    base_point : Rhino.Geometry.Point3d -- center of the cone's base circle
    height     : float -- cone height along the base plane's normal (Z by default)
    radius     : float -- base circle radius
    cap_bottom : bool  -- whether to cap the base circle (closed vs open cone)

    Returns a Rhino.Geometry.Brep.
    """
    if base_point is None:
        base_point = rg.Point3d(0, 0, 0)

    plane = rg.Plane(base_point, rg.Vector3d.ZAxis)
    cone = rg.Cone(plane, height, radius)
    return cone.ToBrep(cap_bottom)
def create_twelve_frames(
    base_plane=None,
    width=10.0,
    height=5.0,
    length=1.0,
    vertical_distance=10.0,
    horizontal_distance=10.0,
    border_width=1.0,
):
    """
    Create twelve frames in three 2x2 grids on mutually orthogonal planes.

    base_plane : Rhino.Geometry.Plane -- center plane for the frame arrangement
    width : float -- frame width along the base plane's X axis
    height : float -- frame height along the base plane's Y axis
    length : float -- frame depth along the base plane's normal
    vertical_distance : float -- clear edge-to-edge gap between rows
    horizontal_distance : float -- clear edge-to-edge gap between columns
    border_width : float -- uniform width of each frame border

    Returns a list of twelve Rhino.Geometry.Brep frames.
    """
    if base_plane is None:
        base_plane = rg.Plane.WorldXY
    if vertical_distance < 0 or horizontal_distance < 0:
        raise ValueError("Grid distances must not be negative.")

    column_spacing = width + horizontal_distance
    row_spacing = height + vertical_distance
    arrangement_center = base_plane.Origin + base_plane.Normal * (length / 2.0)
    rotations = (
        None,
        rg.Transform.Rotation(
            math.pi / 2.0,
            base_plane.XAxis,
            arrangement_center,
        ),
        rg.Transform.Rotation(
            math.pi / 2.0,
            base_plane.YAxis,
            arrangement_center,
        ),
    )
    frames = []
    for rotation in rotations:
        for x_sign in (-0.5, 0.5):
            for y_sign in (-0.5, 0.5):
                offset = (
                    base_plane.XAxis * (column_spacing * x_sign)
                    + base_plane.YAxis * (row_spacing * y_sign)
                )
                frame_plane = rg.Plane(
                    base_plane.Origin + offset,
                    base_plane.XAxis,
                    base_plane.YAxis,
                )
                frame = create_frame(
                    frame_plane,
                    width,
                    height,
                    length,
                    border_width,
                )
                if rotation is not None:
                    frame.Transform(rotation)
                frames.append(frame)

    return frames
def create_six_frames(
    base_plane=None,
    width=10.0,
    height=5.0,
    length=1.0,
    border_width=1.0,
    distance=10.0,
):
    """
    Create six identical frames in three opposing pairs around a center.

    base_plane : Rhino.Geometry.Plane -- center plane for the frame arrangement
    width : float -- frame width along its local X axis
    height : float -- frame height along its local Y axis
    length : float -- frame depth along its local normal
    border_width : float -- uniform width of each frame border
    distance : float -- clear gap between the frames in each opposing pair

    Returns a list of six Rhino.Geometry.Brep frames.
    """
    if base_plane is None:
        base_plane = rg.Plane.WorldXY
    if distance < 0:
        raise ValueError("Distance must not be negative.")

    axis_frames = (
        (
            base_plane.XAxis,
            (base_plane.YAxis, base_plane.ZAxis),
            (base_plane.YAxis, -base_plane.ZAxis),
        ),
        (
            base_plane.YAxis,
            (base_plane.ZAxis, base_plane.XAxis),
            (base_plane.ZAxis, -base_plane.XAxis),
        ),
        (
            base_plane.Normal,
            (base_plane.XAxis, base_plane.YAxis),
            (base_plane.XAxis, -base_plane.YAxis),
        ),
    )
    center_spacing = (length + distance) / 2.0
    frames = []
    for axis, positive_axes, negative_axes in axis_frames:
        for sign, (frame_x_axis, frame_y_axis) in (
            (1.0, positive_axes),
            (-1.0, negative_axes),
        ):
            normal = rg.Vector3d.CrossProduct(frame_x_axis, frame_y_axis)
            center = base_plane.Origin + axis * (sign * center_spacing)
            frame_plane = rg.Plane(
                center - normal * (length / 2.0),
                frame_x_axis,
                frame_y_axis,
            )
            frames.append(
                create_frame(
                    frame_plane,
                    width,
                    height,
                    length,
                    border_width,
                )
            )

    return frames
def create_torus(major_radius=5.0, minor_radius=2.0, base_plane=None):
    """
    Build a torus as a Brep.

    base_point   : Rhino.Geometry.Point3d -- center of the torus
    major_radius : float -- distance from the torus center to the tube center
    minor_radius : float -- radius of the tube
    base_plane   : Rhino.Geometry.Plane -- plane defining the torus position and orientation

    Returns a Rhino.Geometry.Brep.
    """
    if base_plane is None:
        if base_point is None:
            base_point = rg.Point3d(0, 0, 0)
        base_plane = rg.Plane(base_point, rg.Vector3d.ZAxis)

    torus = rg.Torus(base_plane, major_radius, minor_radius)
    return torus.ToBrep()
def create_pyramid(base_plane=None, height=10.0, base_width=10.0, cap_bottom=True):
    """
    Build a square pyramid as a mesh.

    base_plane : Rhino.Geometry.Plane -- plane defining the base position and orientation
    height     : float -- pyramid height along the base plane's normal
    base_width : float -- width of each side of the square base
    cap_bottom : bool  -- whether to cap the base (closed vs open pyramid)

    Returns a Rhino.Geometry.Mesh.
    """
    if base_plane is None:
        base_plane = rg.Plane.WorldXY

    half_width = base_width / 2.0
    base_corners = [
        base_plane.PointAt(-half_width, -half_width),
        base_plane.PointAt(half_width, -half_width),
        base_plane.PointAt(half_width, half_width),
        base_plane.PointAt(-half_width, half_width),
    ]
    apex = base_plane.Origin + base_plane.Normal * height

    pyramid = rg.Mesh()
    for point in base_corners:
        pyramid.Vertices.Add(point.X, point.Y, point.Z)
    pyramid.Vertices.Add(apex.X, apex.Y, apex.Z)

    if cap_bottom:
        pyramid.Faces.AddFace(0, 3, 2, 1)
    for i in range(4):
        pyramid.Faces.AddFace(i, (i + 1) % 4, 4)

    pyramid.Normals.ComputeNormals()
    pyramid.Compact()
    return pyramid
def create_rectangle(base_plane=None, width=10.0, height=5.0, length=1.0):
    """
    Build a rectangular solid as a Brep.

    base_plane : Rhino.Geometry.Plane -- plane defining the base position and orientation
    width      : float -- solid width along the plane's X axis
    height     : float -- solid height along the plane's Y axis
    length     : float -- solid length along the plane's normal

    Returns a closed Rhino.Geometry.Brep.
    """
    if width <= 0 or height <= 0 or length <= 0:
        raise ValueError("width, height, and length must be positive.")
    if base_plane is None:
        base_plane = rg.Plane.WorldXY

    box = rg.Box(
        base_plane,
        rg.Interval(-width / 2.0, width / 2.0),
        rg.Interval(-height / 2.0, height / 2.0),
        rg.Interval(0.0, length),
    )
    return box.ToBrep()
def create_frame(base_plane=None, width=10.0, height=5.0, length=1.0, border_width=1.0):
    """
    Build a rectangular solid frame as a Brep with a through-opening.

    base_plane   : Rhino.Geometry.Plane -- plane defining the frame base and orientation
    width        : float -- overall frame width along the plane's X axis
    height       : float -- overall frame height along the plane's Y axis
    length       : float -- frame depth along the plane's normal
    border_width : float -- uniform width of the frame border

    Returns a Rhino.Geometry.Brep.
    """
    if width <= 0 or height <= 0 or length <= 0:
        raise ValueError("width, height, and length must be positive.")
    if border_width <= 0 or 2 * border_width >= min(width, height):
        raise ValueError("border_width must be positive and leave an opening in the frame.")
    if base_plane is None:
        base_plane = rg.Plane.WorldXY

    inner_width = width - 2 * border_width
    inner_height = height - 2 * border_width
    tolerance = 0.001
    cutter_plane = rg.Plane(
        base_plane.PointAt(0.0, 0.0, -tolerance * 10),
        base_plane.XAxis,
        base_plane.YAxis,
    )
    outer = create_rectangle(base_plane, width, height, length)
    opening = create_rectangle(cutter_plane, inner_width, inner_height, length + 2 * tolerance * 10)

    frames = rg.Brep.CreateBooleanDifference(outer, opening, tolerance)
    if not frames:
        raise ValueError("Could not create a solid frame from the provided dimensions.")
    return frames[0]

'OPERATIONS'

def boolean_difference(brep_a, brep_b, tolerance=0.001):
    """
    Subtract brep_b from brep_a, accepting either a Brep or a sequence of Breps.

    brep_a : Rhino.Geometry.Brep or sequence -- Brep(s) to subtract from
    brep_b : Rhino.Geometry.Brep or sequence -- Brep(s) to subtract
    tolerance : float -- absolute tolerance used by the boolean operation

    Returns a list of Rhino.Geometry.Brep resulting from the difference.
    """
    if brep_a is None or brep_b is None:
        raise ValueError("Both brep_a and brep_b must be provided.")
    if tolerance <= 0:
        raise ValueError("tolerance must be positive.")

    breps_a = [brep_a] if isinstance(brep_a, rg.Brep) else list(brep_a)
    breps_b = [brep_b] if isinstance(brep_b, rg.Brep) else list(brep_b)
    if not breps_a or not breps_b:
        raise ValueError("brep_a and brep_b must each contain at least one Brep.")
    if not all(isinstance(brep, rg.Brep) for brep in breps_a + breps_b):
        raise TypeError("All inputs must be Rhino.Geometry.Brep objects.")
    if not all(brep.IsSolid for brep in breps_a + breps_b):
        raise ValueError("Boolean difference requires both inputs to be closed solid Breps.")

    result = rg.Brep.CreateBooleanDifference(breps_a, breps_b, tolerance)
    if not result:
        raise RuntimeError(
            "Rhino could not compute the boolean difference. Check that the Breps "
            "intersect and that the tolerance suits the model units."
        )
    return result


def remove_breps_on_intersection(breps, cutter, tolerance=0.001):
    """
    Remove intersecting units from a Brep assembly.

    Assembly inputs may be sequences or Grasshopper data trees. Each Brep is
    checked independently, so only intersecting units are removed.

    breps : Rhino.Geometry.Brep or sequence/tree -- assembly units to check
    cutter : Rhino.Geometry.Brep or sequence/tree -- Brep(s) acting as the test volume
    tolerance : float -- tolerance passed to Rhino's intersection check

    Returns a list of Rhino.Geometry.Brep values that do not intersect.
    """
    if breps is None or cutter is None:
        raise ValueError("breps and cutter must both be provided.")
    if tolerance <= 0:
        raise ValueError("tolerance must be positive.")

    def flatten_breps(value):
        if isinstance(value, rg.Brep):
            return [value]

        branches = getattr(value, "Branches", None)
        if branches is not None:
            value = branches

        try:
            items = list(value)
        except TypeError as error:
            raise TypeError(
                "Inputs must be Breps or sequences/data trees of Breps."
            ) from error

        flattened = []
        for item in items:
            flattened.extend(flatten_breps(item))
        return flattened

    source_items = flatten_breps(breps)
    cutter_items = flatten_breps(cutter)

    if not source_items:
        return []
    if not cutter_items:
        return list(source_items)
    if not all(item.IsValid for item in source_items + cutter_items):
        raise ValueError("All source and cutter Breps must be valid.")

    kept = []
    for source in source_items:
        intersected = False
        for cutter_brep in cutter_items:
            hits = rg.Brep.CreateBooleanIntersection(source, cutter_brep, tolerance)
            if hits is None:
                raise RuntimeError(
                    "Rhino could not test whether an assembly unit intersects the cutter."
                )
            if len(hits) > 0:
                intersected = True
                break

        if not intersected:
            kept.append(source)

    return kept

def copy_brep_along_xyz(brep, distance_x, distance_y, distance_z,
                        copy_count_x=None, copy_count_y=None, copy_count_z=None):
    """
    Create a 3D grid of Brep copies using independent axis spacing and counts.

    brep : Rhino.Geometry.Brep -- the Brep to copy
    distance_x : float -- translation step between copies along the X axis
    distance_y : float -- translation step between copies along the Y axis
    distance_z : float -- translation step between copies along the Z axis
    copy_count_x : int -- number of grid steps in each direction along X
    copy_count_y : int -- number of grid steps in each direction along Y
    copy_count_z : int -- number of grid steps in each direction along Z

    Returns a list of Rhino.Geometry.Brep copies at all grid positions except
    the original Brep's position.
    """
    if brep is None:
        raise ValueError("brep must be provided.")

    copy_count_x = 0 if copy_count_x is None else copy_count_x
    copy_count_y = 0 if copy_count_y is None else copy_count_y
    copy_count_z = 0 if copy_count_z is None else copy_count_z

    if min(copy_count_x, copy_count_y, copy_count_z) < 0:
        raise ValueError("copy counts must not be negative.")

    copies = []
    for i in range(-int(copy_count_x), int(copy_count_x) + 1):
        for j in range(-int(copy_count_y), int(copy_count_y) + 1):
            for k in range(-int(copy_count_z), int(copy_count_z) + 1):
                if i == 0 and j == 0 and k == 0:
                    continue

                offset = (
                    rg.Vector3d.XAxis * (distance_x * i)
                    + rg.Vector3d.YAxis * (distance_y * j)
                    + rg.Vector3d.ZAxis * (distance_z * k)
                )
                copy = brep.DuplicateBrep()
                copy.Transform(rg.Transform.Translation(offset))
                copies.append(copy)

    return copies

def copy_brep_along_curve(brep, spline, distance, copy_count=None):
    """
    Create copies of a Brep along a spline at equal arc-length intervals.

    brep : Rhino.Geometry.Brep -- the Brep to copy
    spline : Rhino.Geometry.Curve -- the curve defining copy positions
    distance : float -- arc-length spacing between consecutive copies
    copy_count : int or None -- number of copies, or maximum that fit if None

    Each copy keeps the Brep's original orientation, with its bounding-box
    center placed on the spline. The first copy is placed at the spline start.

    Returns a list of Rhino.Geometry.Brep copies; the original is not included.
    """
    if not isinstance(brep, rg.Brep):
        raise TypeError("brep must be a Rhino.Geometry.Brep.")
    if not isinstance(spline, rg.Curve):
        raise TypeError("spline must be a Rhino.Geometry.Curve.")
    if not spline.IsValid:
        raise ValueError("spline must be a valid curve.")
    if distance <= 0:
        raise ValueError("distance must be positive.")
    if copy_count is not None and (copy_count < 0 or int(copy_count) != copy_count):
        raise ValueError("copy_count must be a non-negative integer.")

    spline_length = spline.GetLength()
    if copy_count is None:
        copy_count = math.floor(spline_length / distance) + 1
    else:
        copy_count = int(copy_count)
    if copy_count == 0:
        return []

    required_length = (copy_count - 1) * distance
    if required_length > spline_length:
        raise ValueError("The spline is too short for the requested copies and spacing.")

    bounds = brep.GetBoundingBox(True)
    if not bounds.IsValid:
        raise ValueError("Could not calculate the Brep bounding box.")
    source_center = bounds.Center

    copies = []
    for index in range(copy_count):
        target = spline.PointAtLength(index * distance)
        if not target.IsValid:
            raise RuntimeError("Could not evaluate a point at the requested spline length.")

        copy = brep.DuplicateBrep()
        translation = rg.Transform.Translation(target - source_center)
        if not copy.Transform(translation):
            raise RuntimeError("Could not translate a Brep copy along the spline.")
        copies.append(copy)

    return copies

#NOT USED 
def copy_brep_assembly_inside(
    breps,
    container_brep,
    distance_x,
    distance_y,
    distance_z,
    copy_count_x=0,
    copy_count_y=0,
    copy_count_z=0,
    tolerance=0.001
):

    # --------------------------------------------
    # 1. VALIDATE INPUTS
    # --------------------------------------------

    if not isinstance(container_brep, rg.Brep):
        raise TypeError("Container must be a Brep.")

    if not container_brep.IsValid or not container_brep.IsSolid:
        raise ValueError("Container must be a valid closed solid.")

    if breps is None:
        raise ValueError("No source Breps supplied.")
    source_inputs = [breps] if isinstance(breps, rg.Brep) else list(breps)
    if not source_inputs:
        raise ValueError("No source Breps supplied.")

    if min(distance_x, distance_y, distance_z) < 0:
        raise ValueError("Distances cannot be negative.")

    if tolerance <= 0:
        raise ValueError("Tolerance must be positive.")

    copy_counts = (copy_count_x, copy_count_y, copy_count_z)
    if any(
        count is not None and (count < 0 or int(count) != count)
        for count in copy_counts
    ):
        raise ValueError("Copy counts must be non-negative integers or None.")

    # --------------------------------------------
    # 2. PREPARE SOURCE ASSEMBLY
    # --------------------------------------------

    source_breps = []

    for b in source_inputs:

        if not isinstance(b, rg.Brep):
            raise TypeError("All source elements must be Breps.")

        if not b.IsValid or not b.IsSolid:
            raise ValueError("Every source Brep must be a valid closed solid.")

        source_breps.append(b.DuplicateBrep())

    # --------------------------------------------
    # 3. CALCULATE COMMON BOUNDING BOX
    # --------------------------------------------

    assembly_bounds = rg.BoundingBox.Empty

    for b in source_breps:
        assembly_bounds.Union(b.GetBoundingBox(True))

    if not assembly_bounds.IsValid:
        raise ValueError("Could not calculate assembly bounding box.")

    container_bounds = container_brep.GetBoundingBox(True)
    center_offset = container_bounds.Center - assembly_bounds.Center

    # --------------------------------------------
    # 4. CALCULATE GRID SPACING
    # --------------------------------------------

    step_x = assembly_bounds.Max.X - assembly_bounds.Min.X + distance_x
    step_y = assembly_bounds.Max.Y - assembly_bounds.Min.Y + distance_y
    step_z = assembly_bounds.Max.Z - assembly_bounds.Min.Z + distance_z

    # Avoid division by zero
    if min(step_x, step_y, step_z) <= 0:
        raise ValueError("Grid spacing must be positive.")

    # --------------------------------------------
    # 5. CALCULATE GRID RANGES
    # --------------------------------------------

    index_ranges = []

    for axis, step, count in (
        ("X", step_x, copy_count_x),
        ("Y", step_y, copy_count_y),
        ("Z", step_z, copy_count_z)
    ):

        min_index = math.ceil(
            (
                getattr(container_bounds.Min, axis)
                - getattr(assembly_bounds.Min, axis)
                - getattr(center_offset, axis)
                - tolerance
            ) / step
        )

        max_index = math.floor(
            (
                getattr(container_bounds.Max, axis)
                - getattr(assembly_bounds.Max, axis)
                - getattr(center_offset, axis)
                + tolerance
            ) / step
        )

        if count:
            min_index = max(min_index, -int(count))
            max_index = min(max_index, int(count))

        index_ranges.append(range(min_index, max_index + 1))

    # --------------------------------------------
    # 6. CALCULATE SOURCE VOLUMES
    # --------------------------------------------

    source_volumes = []

    for b in source_breps:

        props = rg.VolumeMassProperties.Compute(b)

        if props is None:
            raise ValueError("Could not calculate source volume.")

        source_volumes.append(props.Volume)

    # --------------------------------------------
    # 7. GENERATE AND TEST COPIES
    # --------------------------------------------

    result = []

    for i in index_ranges[0]:
        for j in index_ranges[1]:
            for k in index_ranges[2]:

                offset = (
                    center_offset
                    + rg.Vector3d.XAxis * (step_x * i)
                    + rg.Vector3d.YAxis * (step_y * j)
                    + rg.Vector3d.ZAxis * (step_z * k)
                )

                assembly_valid = True
                translated_assembly = []

                for b, source_volume in zip(
                    source_breps, source_volumes
                ):

                    copy = b.DuplicateBrep()

                    copy.Transform(
                        rg.Transform.Translation(offset)
                    )

                    # Boolean intersection with container
                    intersections = rg.Brep.CreateBooleanIntersection(
                        copy,
                        container_brep,
                        tolerance
                    )

                    if intersections is None:
                        raise RuntimeError(
                            "Boolean intersection failed."
                        )

                    intersection_volume = 0.0

                    for intersection in intersections:

                        props = rg.VolumeMassProperties.Compute(
                            intersection
                        )

                        if props is None:
                            raise RuntimeError(
                                "Intersection volume calculation failed."
                            )

                        intersection_volume += props.Volume

                    volume_tol = max(
                        tolerance ** 3,
                        source_volume * 1e-8
                    )

                    if (
                        not intersections
                        or abs(
                            source_volume - intersection_volume
                        ) > volume_tol
                    ):

                        assembly_valid = False
                        break

                    translated_assembly.append(copy)

                # Accept only if all six Breps fit
                if assembly_valid:
                    result.extend(translated_assembly)

    return result
def copy_mesh_along_z(mesh, distance, copy_count):
    """
    Create copies of a Mesh, each offset in the +Z direction.

    mesh : Rhino.Geometry.Mesh -- the Mesh to copy
    distance : float -- the Z spacing between consecutive copies
    copy_count : int -- the number of copies to create

    Returns a list of Rhino.Geometry.Mesh copies; copy i is moved by distance * (i + 1).
    """
    if mesh is None:
        raise ValueError("mesh must be provided.")
    if copy_count < 0:
        raise ValueError("copy_count must not be negative.")

    copies = []
    for i in range(1, int(copy_count) + 1):
        copy = mesh.DuplicateMesh()
        copy.Transform(rg.Transform.Translation(rg.Vector3d(0, 0, distance * i)))
        copies.append(copy)
    return copies