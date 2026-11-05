import math
import  Rhino.Geometry as rg


'GEOMETRY FUNCTIONS'

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

def create_sphere(base_point=None, radius=5.0):
    """
    Build a sphere as a Brep.

    base_point : Rhino.Geometry.Point3d -- center of the sphere
    radius     : float -- sphere radius

    Returns a Rhino.Geometry.Brep.
    """
    if base_point is None:
        base_point = rg.Point3d(0, 0, 0)

    sphere = rg.Sphere(base_point, radius)
    return sphere.ToBrep()

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

def copy_brep_along_xyz(brep, distance_x, distance_y, distance_z,
                        copy_count_x=None, copy_count_y=None, copy_count_z=None):
    """
    Create a 3D grid of Brep copies using independent axis spacing and counts.

    brep : Rhino.Geometry.Brep -- the Brep to copy
    distance_x : float -- spacing between copies along the +X axis
    distance_y : float -- spacing between copies along the +Y axis
    distance_z : float -- spacing between copies along the +Z axis
    copy_count_x : int -- number of grid steps along the +X axis
    copy_count_y : int -- number of grid steps along the +Y axis
    copy_count_z : int -- number of grid steps along the +Z axis

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
    for i in range(int(copy_count_x) + 1):
        for j in range(int(copy_count_y) + 1):
            for k in range(int(copy_count_z) + 1):
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


def copy_brep_along_xyz_inside(
    brep,
    container_brep,
    distance_x,
    distance_y,
    distance_z,
    copy_count_x=None,
    copy_count_y=None,
    copy_count_z=None,
    tolerance=0.001,
):
    """
    Create a 3D grid and keep only copies fully inside a closed container Brep.

    brep : Rhino.Geometry.Brep -- the Brep to copy
    container_brep : Rhino.Geometry.Brep -- closed Brep defining the allowed volume
    distance_x : float -- spacing between copies along the +X axis
    distance_y : float -- spacing between copies along the +Y axis
    distance_z : float -- spacing between copies along the +Z axis
    copy_count_x : int -- number of grid steps along the +X axis
    copy_count_y : int -- number of grid steps along the +Y axis
    copy_count_z : int -- number of grid steps along the +Z axis
    tolerance : float -- absolute tolerance used for boolean intersections

    
    """
    if not isinstance(brep, rg.Brep) or not isinstance(container_brep, rg.Brep):
        raise TypeError("brep and container_brep must be Rhino.Geometry.Brep objects.")
    if not brep.IsSolid or not container_brep.IsSolid:
        raise ValueError("brep and container_brep must both be closed solid Breps.")
    if tolerance <= 0:
        raise ValueError("tolerance must be positive.")

    source_volume_props = rg.VolumeMassProperties.Compute(brep)
    if source_volume_props is None:
        raise ValueError("Could not calculate the source Brep volume.")
    source_volume = source_volume_props.Volume
    volume_tolerance = max(tolerance ** 3, source_volume * 1e-8)

    contained_copies = []
    for copy in copy_brep_along_xyz(
        brep,
        distance_x,
        distance_y,
        distance_z,
        copy_count_x,
        copy_count_y,
        copy_count_z,):
        intersections = rg.Brep.CreateBooleanIntersection(
            copy, container_brep, tolerance
        )
        if intersections is None:
            raise RuntimeError(
                "Rhino could not test whether a grid copy is inside the container. "
                "Check the Breps and the boolean tolerance."
            )

        intersection_volume = 0.0
        for intersection in intersections:
            volume_props = rg.VolumeMassProperties.Compute(intersection)
            if volume_props is None:
                raise RuntimeError("Could not calculate an intersection Brep volume.")
            intersection_volume += volume_props.Volume

        if abs(source_volume - intersection_volume) <= volume_tolerance:
            contained_copies.append(copy)

    return contained_copies


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