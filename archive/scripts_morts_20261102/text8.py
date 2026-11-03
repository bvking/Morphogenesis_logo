# archive du DAT /project1/text8 (purge du 2026-11-02)
# morphogenesis_dna_td_v10_HEIGHT_STRETCH_BACK_MIRROR.py
# TouchDesigner 2025.32460 / Python 3.11
# A lancer apres la V09.
#
# V10 ajoute :
# 1) Etirement dynamique de la hauteur des lettres selon avant/arriere.
# 2) Retournement miroir automatique quand une lettre passe derriere le tube.

ROOT_PATH = '/project1/MORPHOGENESIS_DNA_TD'
WORD = 'MORPHOGENESIS'

root = op(ROOT_PATH)
if root is None:
    raise Exception('Container introuvable: ' + ROOT_PATH)

# ---------------------------------------------------------------------
# Helpers TouchDesigner
# ---------------------------------------------------------------------
def par(o, name):
    try:
        return getattr(o.par, name)
    except Exception:
        return None

def setv(o, names, value):
    if o is None:
        return False
    for n in names:
        p = par(o, n)
        if p is not None:
            try:
                p.val = value
                return True
            except Exception:
                pass
    print('WARNING set failed:', o.path if o else None, names, value)
    return False

def setexpr(o, name, expr):
    p = par(o, name)
    if p is None:
        return False
    try:
        p.expr = expr
        return True
    except Exception as e:
        print('WARNING expr failed:', o.path, name, e)
        return False

def set_expr_by_names(o, names, expr, keywords=None):
    if o is None:
        return None
    for n in names:
        p = par(o, n)
        if p is not None:
            try:
                p.expr = expr
                return p
            except Exception:
                pass
    if keywords:
        kws = [k.lower() for k in keywords]
        for p in o.pars():
            try:
                label = p.label
            except Exception:
                label = ''
            key = (p.name + ' ' + label).lower()
            if any(k in key for k in kws):
                try:
                    p.expr = expr
                    return p
                except Exception:
                    pass
    return None

def ensure_float(page, name, label, default, nmin, nmax):
    p = par(root, name)
    if p is not None:
        print('PARAM already exists:', name, '=', p.eval())
        return p
    ps = page.appendFloat(name, label=label)
    p = ps[0]
    p.default = default
    p.val = default
    p.normMin = nmin
    p.normMax = nmax
    print('ADDED PARAM', name, '=', default)
    return p

def flag(o, name, value):
    try:
        setattr(o, name, value)
        return True
    except Exception:
        return False

def create_or_get(parent, type_name, name):
    o = parent.op(name)
    if o is not None:
        return o
    return parent.create(type_name, name)

# ---------------------------------------------------------------------
# Custom parameters V10
# ---------------------------------------------------------------------
try:
    page = root.appendCustomPage('DNA V10')
except Exception:
    page = root.appendCustomPage('DNA V10b')

# Etirement de hauteur : min a l'arriere, max a l'avant.
ensure_float(page, 'Heightstretchactive', 'Height stretch active', 1.0, 0.0, 1.0)
ensure_float(page, 'Heightstretchamount', 'Height stretch amount', 1.0, 0.0, 2.0)
ensure_float(page, 'Heightstretchminback', 'Height min/back', 0.72, 0.05, 3.0)
ensure_float(page, 'Heightstretchmaxfront', 'Height max/front', 1.42, 0.05, 5.0)
ensure_float(page, 'Heightstretchcurve', 'Height stretch curve', 1.10, 0.2, 5.0)
ensure_float(page, 'Heightstretchflip', 'Height stretch flip', 0.0, 0.0, 1.0)
ensure_float(page, 'Heightstretchmode', 'Height stretch mode', 0.0, 0.0, 1.0)

# Miroir automatique quand la lettre passe derriere.
ensure_float(page, 'Backmirroractive', 'Back mirror active', 1.0, 0.0, 1.0)
ensure_float(page, 'Backmirrorthreshold', 'Back mirror threshold', 0.0, -1.0, 1.0)
ensure_float(page, 'Backmirrorinvert', 'Back mirror invert', 0.0, 0.0, 1.0)
ensure_float(page, 'Backmirrormode', 'Back mirror mode', 0.0, 0.0, 1.0)

# ---------------------------------------------------------------------
# Replace V09 geometry module
# ---------------------------------------------------------------------
geom_module = create_or_get(root, 'textDAT', 'dna_v09_geom_module')
geom_module.text = r'''
import math

ROOT_PATH = '/project1/MORPHOGENESIS_DNA_TD'
WORD = 'MORPHOGENESIS'

def root_op():
    return op(ROOT_PATH)

def par_value(name, default):
    try:
        return float(getattr(root_op().par, name).eval())
    except Exception:
        return default

def clamp(x, a, b):
    return max(a, min(b, x))

def lerp(a, b, t):
    return a + (b - a) * t

def rotate_point_xyz(x, y, z, rx_deg, ry_deg, rz_deg):
    rx = math.radians(rx_deg)
    ry = math.radians(ry_deg)
    rz = math.radians(rz_deg)
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    y, z = y * cx - z * sx, y * sx + z * cx
    x, z = x * cy + z * sy, -x * sy + z * cy
    x, y = x * cz - y * sz, x * sz + y * cz
    return x, y, z

def normalized_frontness(local_front_z, camera_front_z, radius, view_scale, mode):
    if mode >= 0.5:
        denom = max(0.001, abs(radius * view_scale))
        f = camera_front_z / denom
    else:
        denom = max(0.001, abs(radius))
        f = local_front_z / denom
    return clamp(f, -1.0, 1.0)

def depth_scale_multiplier(local_front_z, camera_front_z, radius, view_scale):
    if par_value('Depthscaleactive', 1.0) < 0.5:
        return 1.0
    amount = par_value('Depthscaleamount', 1.0)
    min_s = par_value('Depthscalemin', 0.58)
    max_s = par_value('Depthscalemax', 1.38)
    curve = max(0.001, par_value('Depthscalecurve', 1.15))
    flip = par_value('Depthscaleflip', 0.0)
    mode = par_value('Depthscalemode', 0.0)
    f = normalized_frontness(local_front_z, camera_front_z, radius, view_scale, mode)
    if flip >= 0.5:
        f = -f
    t = clamp(0.5 + 0.5 * f, 0.0, 1.0)
    t = math.pow(t, curve)
    return lerp(1.0, lerp(min_s, max_s, t), amount)

def height_stretch_multiplier(local_front_z, camera_front_z, radius, view_scale):
    if par_value('Heightstretchactive', 1.0) < 0.5:
        return 1.0
    amount = par_value('Heightstretchamount', 1.0)
    min_back = par_value('Heightstretchminback', 0.72)
    max_front = par_value('Heightstretchmaxfront', 1.42)
    curve = max(0.001, par_value('Heightstretchcurve', 1.10))
    flip = par_value('Heightstretchflip', 0.0)
    mode = par_value('Heightstretchmode', 0.0)
    f = normalized_frontness(local_front_z, camera_front_z, radius, view_scale, mode)
    if flip >= 0.5:
        f = -f
    # -1 = arriere, +1 = avant
    t = clamp(0.5 + 0.5 * f, 0.0, 1.0)
    t = math.pow(t, curve)
    return lerp(1.0, lerp(min_back, max_front, t), amount)

def is_back_region(local_front_z, camera_front_z, radius, view_scale):
    if par_value('Backmirroractive', 1.0) < 0.5:
        return False
    threshold = par_value('Backmirrorthreshold', 0.0)
    invert = par_value('Backmirrorinvert', 0.0)
    mode = par_value('Backmirrormode', 0.0)
    f = normalized_frontness(local_front_z, camera_front_z, radius, view_scale, mode)
    back = f < threshold
    if invert >= 0.5:
        back = not back
    return back

def letter_state(i):
    n = len(WORD)
    radius = par_value('Radius', 2.15)
    pitch = par_value('Pitch', 0.48)
    turns = par_value('Turns', 2.25)
    speed = par_value('Speed', 0.18)
    axis_roll_speed = par_value('Axisrollspeed', 0.12)
    axis_roll_angle = par_value('Axisrollangle', 0.0)
    lettersize = par_value('Lettersize', par_value('Letterscale', 0.34))
    mirrororder = par_value('Mirrororder', 1.0)
    lettermirrorx = par_value('Lettermirrorx', 1.0)
    globalspin = par_value('Globalspin', 0.0)
    view_rx = par_value('Viewrotx', 0.0)
    view_ry = par_value('Viewroty', -18.0)
    view_rz = par_value('Viewrotz', 0.0)
    view_scale = par_value('Viewscale', 1.0)
    view_tx = par_value('Viewtx', 0.0)
    view_ty = par_value('Viewty', 0.0)
    view_tz = par_value('Viewtz', 0.0)

    j = (n - 1) - i if mirrororder >= 0.5 else i
    t_word = 0.0 if n <= 1 else j / float(n - 1)
    axis_x = (j - (n - 1) * 0.5) * pitch
    strand_offset = (i % 2) * math.pi
    phase = absTime.seconds * speed * math.tau
    angle = t_word * math.tau * turns + phase + strand_offset + math.radians(globalspin)
    roll = absTime.seconds * axis_roll_speed * math.tau + math.radians(axis_roll_angle)
    theta = angle + roll

    base_x = axis_x
    base_y = math.cos(theta) * radius
    base_z = math.sin(theta) * radius

    axis_vec = (1.0, 0.0, 0.0)
    tangent_vec = (0.0, -math.sin(theta), math.cos(theta))
    normal_vec = (0.0, math.cos(theta), math.sin(theta))

    cx = base_x * view_scale
    cy = base_y * view_scale
    cz = base_z * view_scale
    _, _, camera_z_center = rotate_point_xyz(cx, cy, cz, view_rx, view_ry, view_rz)

    dsm = depth_scale_multiplier(base_z, camera_z_center, radius, view_scale)
    hsm = height_stretch_multiplier(base_z, camera_z_center, radius, view_scale)

    static_mirror = lettermirrorx >= 0.5
    back_mirror = is_back_region(base_z, camera_z_center, radius, view_scale)
    final_mirror = static_mirror
    if back_mirror:
        final_mirror = not final_mirror

    pulse = 1.0 + 0.035 * math.sin(phase * 2.0 + i * 0.71)
    glyph_scale = lettersize * pulse * dsm

    return {
        'radius': radius,
        'theta': theta,
        'base': (base_x, base_y, base_z),
        'axis': axis_vec,
        'tangent': tangent_vec,
        'normal': normal_vec,
        'glyph_scale': glyph_scale,
        'height_scale': hsm,
        'view_rx': view_rx,
        'view_ry': view_ry,
        'view_rz': view_rz,
        'view_scale': view_scale,
        'view_tx': view_tx,
        'view_ty': view_ty,
        'view_tz': view_tz,
        'final_mirror': final_mirror,
        'back_mirror': back_mirror,
        'frontness_local': normalized_frontness(base_z, camera_z_center, radius, view_scale, 0.0),
        'frontness_camera': normalized_frontness(base_z, camera_z_center, radius, view_scale, 1.0),
    }

def world_transform_local_point(x, y, z, state):
    x *= state['view_scale']
    y *= state['view_scale']
    z *= state['view_scale']
    x, y, z = rotate_point_xyz(x, y, z, state['view_rx'], state['view_ry'], state['view_rz'])
    x += state['view_tx']
    y += state['view_ty']
    z += state['view_tz']
    return x, y, z

def deform_point(i, px, py, pz, bbox):
    state = letter_state(i)
    active = par_value('Curvedeformactive', 1.0)
    amount = par_value('Curvedeformamount', 1.0)
    curvature = par_value('Curvecurvature', 1.0)
    offset = par_value('Curveoffset', 0.075)
    extrusion_gain = par_value('Curveextrudegain', 1.0)
    curve_mode = par_value('Curvemode', 0.0)
    curve_flip = par_value('Curveflip', 0.0)
    max_angle_deg = par_value('Curvemaxangle', 38.0)
    if active < 0.5:
        amount = 0.0

    radius = max(0.001, abs(state['radius']))
    base = state['base']
    axis_vec = state['axis']
    tangent_vec = state['tangent']
    normal_vec = state['normal']
    glyph_scale = state['glyph_scale']
    height_scale = state['height_scale']
    minx, maxx, miny, maxy, minz, maxz = bbox
    cx = 0.5 * (minx + maxx)
    cy = 0.5 * (miny + maxy)
    cz = 0.5 * (minz + maxz)

    # Local glyph coordinates.
    lx = (px - cx) * glyph_scale
    ly = (py - cy) * glyph_scale * height_scale  # V10: height-specific stretch
    lz = (pz - cz) * glyph_scale * extrusion_gain

    if state['final_mirror']:
        lx = -lx

    flat_x = base[0] + axis_vec[0] * lx + tangent_vec[0] * ly + normal_vec[0] * (offset + lz)
    flat_y = base[1] + axis_vec[1] * lx + tangent_vec[1] * ly + normal_vec[1] * (offset + lz)
    flat_z = base[2] + axis_vec[2] * lx + tangent_vec[2] * ly + normal_vec[2] * (offset + lz)

    if curve_mode < 0.5:
        axial_offset = lx
        angular_source = ly
    else:
        axial_offset = ly
        angular_source = lx

    if curve_flip >= 0.5:
        angular_source = -angular_source

    max_angle = math.radians(max(0.001, max_angle_deg))
    angular_offset = clamp((angular_source / radius) * curvature, -max_angle, max_angle)
    theta_p = state['theta'] + angular_offset
    r_p = radius + offset + lz

    curved_x = base[0] + axial_offset
    curved_y = math.cos(theta_p) * r_p
    curved_z = math.sin(theta_p) * r_p

    amount = clamp(amount, 0.0, 1.0)
    x = lerp(flat_x, curved_x, amount)
    y = lerp(flat_y, curved_y, amount)
    z = lerp(flat_z, curved_z, amount)
    return world_transform_local_point(x, y, z, state)

def deform_script_sop(scriptOp, letter_index):
    try:
        _ = scriptOp.par.Forcecook.eval()
    except Exception:
        pass

    pts = list(scriptOp.points)
    if not pts:
        return
    minx = min(p.x for p in pts)
    maxx = max(p.x for p in pts)
    miny = min(p.y for p in pts)
    maxy = max(p.y for p in pts)
    minz = min(p.z for p in pts)
    maxz = max(p.z for p in pts)
    bbox = (minx, maxx, miny, maxy, minz, maxz)
    for p in pts:
        x, y, z = deform_point(letter_index, p.x, p.y, p.z, bbox)
        p.x = x
        p.y = y
        p.z = z

def update_debug():
    t = op(ROOT_PATH + '/debug_v10_height_mirror')
    if t is None:
        return
    t.clear()
    t.appendRow(['letter', 'frontness_local', 'frontness_camera', 'height_scale', 'back_mirror', 'final_mirror'])
    for i in range(len(WORD)):
        s = letter_state(i)
        t.appendRow([
            WORD[i],
            '%.4f' % s['frontness_local'],
            '%.4f' % s['frontness_camera'],
            '%.4f' % s['height_scale'],
            1 if s['back_mirror'] else 0,
            1 if s['final_mirror'] else 0,
        ])
'''

# ---------------------------------------------------------------------
# Reconnect/refresh existing V09 network
# ---------------------------------------------------------------------
geo_paths = []
force_expr = 'absTime.frame'
thickness_expr = "op('%s').par.Letterthickness" % ROOT_PATH

for i, ch in enumerate(WORD):
    geo = root.op('letter_%02d_%s' % (i, ch))
    if geo is None:
        print('WARNING missing letter geo:', i, ch)
        continue

    deform_sop = geo.op('bend_letter_v09')
    if deform_sop is None:
        print('WARNING: bend_letter_v09 introuvable dans', geo.path, '— lance d’abord la V09.')
    else:
        p = par(deform_sop, 'Forcecook')
        if p is None:
            try:
                page_fc = deform_sop.appendCustomPage('V10')
                p = page_fc.appendFloat('Forcecook', label='Force cook frame')[0]
            except Exception:
                p = None
        if p is not None:
            try:
                p.expr = force_expr
            except Exception:
                pass

        for c in geo.children:
            if c.family == 'SOP':
                flag(c, 'display', False)
                flag(c, 'render', False)
        flag(deform_sop, 'display', True)
        flag(deform_sop, 'render', True)

    # Thickness remains independent.
    for c in geo.children:
        if c.family == 'SOP' and c.name.startswith('text_'):
            set_expr_by_names(c, ['extrude', 'depth', 'Depth'], thickness_expr, ['extrude', 'depth', 'thick'])

    # Script SOP outputs world-space points, so the Geometry COMP must stay identity.
    for pname, val in [('tx',0),('ty',0),('tz',0),('rx',0),('ry',0),('rz',0),('sx',1),('sy',1),('sz',1)]:
        setv(geo, [pname], val)

    flag(geo, 'display', True)
    flag(geo, 'render', True)
    geo_paths.append(geo.path)

# Debug table.
debug_dat = create_or_get(root, 'tableDAT', 'debug_v10_height_mirror')
debug_dat.nodeX = 760
debug_dat.nodeY = -720
try:
    geom_module.module.update_debug()
except Exception as e:
    print('WARNING debug update failed:', e)

# Tube follows V07 perspective.
for name in ['helix_tube_surface_v06', 'helix_tube_wire_v06']:
    tube_geo = root.op(name)
    if tube_geo is None:
        continue
    setexpr(tube_geo, 'tx', "op('%s').par.Viewtx" % ROOT_PATH)
    setexpr(tube_geo, 'ty', "op('%s').par.Viewty" % ROOT_PATH)
    setexpr(tube_geo, 'tz', "op('%s').par.Viewtz" % ROOT_PATH)
    setexpr(tube_geo, 'rx', "op('%s').par.Viewrotx" % ROOT_PATH)
    setexpr(tube_geo, 'ry', "op('%s').par.Viewroty" % ROOT_PATH)
    setexpr(tube_geo, 'rz', "op('%s').par.Viewrotz" % ROOT_PATH)
    setexpr(tube_geo, 'sx', "op('%s').par.Viewscale" % ROOT_PATH)
    setexpr(tube_geo, 'sy', "op('%s').par.Viewscale" % ROOT_PATH)
    setexpr(tube_geo, 'sz', "op('%s').par.Viewscale" % ROOT_PATH)
    flag(tube_geo, 'display', True)
    flag(tube_geo, 'render', True)
    geo_paths.append(tube_geo.path)

# Camera/render safety.
cam = root.op('cam1')
if cam is not None:
    setv(cam, ['lookat'], '')
    setv(cam, ['tx'], 0)
    setv(cam, ['ty'], 0)
    setexpr(cam, 'tz', "op('%s').par.Cameradistance" % ROOT_PATH)
    setv(cam, ['rx'], 0)
    setv(cam, ['ry'], 0)
    setv(cam, ['rz'], 0)

render = root.op('render1')
light_key = root.op('light_key')
light_fill = root.op('light_fill')
if render is not None:
    if cam is not None:
        setv(render, ['camera', 'cameras'], cam.path)
    setv(render, ['geometry', 'geo', 'geometries'], ' '.join(geo_paths))
    if light_key is not None and light_fill is not None:
        setv(render, ['lights', 'light'], light_key.path + ' ' + light_fill.path)
    setv(render, ['resx', 'w'], 1280)
    setv(render, ['resy', 'h'], 720)

try:
    root.layout(root.children)
except Exception:
    pass

print('=' * 72)
print('MORPHOGENESIS DNA V10 HEIGHT STRETCH + BACK MIRROR OK')
print('Open:', ROOT_PATH + '/render1')
print('Controls:', ROOT_PATH, '> page DNA V10')
print('Debug:', ROOT_PATH + '/debug_v10_height_mirror')
print('Height front/back: Heightstretchminback / Heightstretchmaxfront')
print('Back mirror ON/OFF: Backmirroractive')
print('=' * 72)
