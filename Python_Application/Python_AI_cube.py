try:
    from js import window
    from pyodide.ffi import create_proxy, to_js
    IN_PYODIDE = True
except Exception:
    IN_PYODIDE = False
    class _Window:
        pass
    window = _Window()
    def create_proxy(fn):
        return fn
    def to_js(x):
        return x

UNIT_SIZE = 1.0


def snap_to_grid(x: float, y: float, z: float, unit_size: float = UNIT_SIZE):
    sx = round(x / unit_size) * unit_size
    sy = round(y / unit_size) * unit_size
    sz = round(z / unit_size) * unit_size
    return to_js([sx, sy, sz])


def compute_box_dims(n: int):
    if n <= 0:
        return (0, 0, 0)
    best = (1, 1, n)
    best_score = float("inf")
    max_x = int(n ** (1 / 3)) + 3
    for x in range(1, max_x + 1):
        max_y = int(((n / x) ** 0.5)) + 3
        for y in range(x, max_y + 1):
            z = int(((n + x * y - 1) // (x * y)))
            if z < y:
                z = y
            vol = x * y * z
            score = (z - x) + (vol - n)
            if score < best_score:
                best_score = score
                best = (x, y, z)
    return best


def compute_positions(n: int, dims, unit_size: float = UNIT_SIZE):
    x, y, z = dims
    positions = []
    if n <= 0 or x * y * z <= 0:
        return to_js(positions)
    cx = (x - 1) / 2.0
    cy = (y - 1) / 2.0
    cz = (z - 1) / 2.0
    count = 0
    for yi in range(y):
        for zi in range(z):
            for xi in range(x):
                if count >= n:
                    break
                px = (xi - cx) * unit_size
                py = (yi - cy) * unit_size
                pz = (zi - cz) * unit_size
                positions.append([px, py, pz])
                count += 1
        if count >= n:
            break
    return to_js(positions)


def is_tight_block(positions, unit_size: float = UNIT_SIZE):
    try:
        py_positions = positions.to_py()
    except Exception:
        py_positions = positions
    if not py_positions:
        return None
    norm = []
    for p in py_positions:
        nx = round(p[0] / unit_size)
        ny = round(p[1] / unit_size)
        nz = round(p[2] / unit_size)
        norm.append((nx, ny, nz))
    xs = [a for a, _, _ in norm]
    ys = [b for _, b, _ in norm]
    zs = [c for _, _, c in norm]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    z_min, z_max = min(zs), max(zs)
    dimx = x_max - x_min + 1
    dimy = y_max - y_min + 1
    dimz = z_max - z_min + 1
    required = {
        (i, j, k)
        for i in range(x_min, x_min + dimx)
        for j in range(y_min, y_min + dimy)
        for k in range(z_min, z_min + dimz)
    }
    actual = set(norm)
    if len(actual) != len(py_positions):
        return None
    if actual == required:
        return to_js([dimx, dimy, dimz])
    return None


def auto_arrange(n: int, unit_size: float = UNIT_SIZE):
    dims = compute_box_dims(n)
    positions = compute_positions(n, dims, unit_size)
    return {"dims": to_js(list(dims)), "positions": positions}


window.pySnap = create_proxy(snap_to_grid)
window.pyAutoArrange = create_proxy(auto_arrange)
window.pyIsTightBlock = create_proxy(is_tight_block)
window.UNIT_SIZE = UNIT_SIZE
