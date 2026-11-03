# archive du DAT /project1/text7 (purge du 2026-11-02)
# morphogenesis_dna_td_v09_CURVED_LETTERS.py
# TouchDesigner 2025.32460 / Python 3.11
#
# À lancer après la V08.
#
# V09 = vraie déformation de géométrie:
# - Chaque Text SOP est envoyé dans un Script SOP.
# - Le Script SOP copie les points du texte.
# - Chaque point est remappé sur une portion de cylindre/tube.
# - Les lettres épousent donc réellement la surface du tube.
#
# IMPORTANT:
# - Cette version est plus coûteuse CPU que les V04-V08, car elle modifie
#   les points des lettres par Python à chaque frame.
# - Si le patch devient lourd, baisse Lettersize, Letterthickness,
#   Curvedeformamount, ou désactive temporairement Curvedeformactive.
#
# Usage:
# 1) Colle ce script dans un Text DAT.
# 2) Run Script.
# 3) Ouvre /project1/MORPHOGENESIS_DNA_TD/render1
# 4) Réglages sur /project1/MORPHOGENESIS_DNA_TD > page DNA V09

import math

ROOT_PATH = '/project1/MORPHOGENESIS_DNA_TD'
WORD = 'MORPHOGENESIS'

root = op(ROOT_PATH)
if root is None:
    raise Exception('Container introuvable: ' + ROOT_PATH)

# -------------------------------------------------------------------------
# UTILS
# -------------------------------------------------------------------------
def get_par(o, name):
    try:
        return getattr(o.par, name)
    except Exception:
        return None

def set_par_safe(o, names, value, print_ok=False):
    if o is None:
        return False
    for name in names:
        p = get_par(o, name)
        if p is not None:
            try:
                p.val = value
                if print_ok:
                    print('SET', o.path + '.par.' + p.name, '=', value)
                return True
            except Exception:
                pass
    print('WARNING could not set', o.path if o else None, names, value)
    return False

def set_expr_safe(o, pname, expr, print_ok=False):
    p = get_par(o, pname)
    if p is None:
        return False
    try:
        p.expr = expr
        if print_ok:
            print('EXPR', o.path + '.par.' + pname, '=', expr)
        return True
    except Exception as e:
        print('WARNING expr failed:', o.path, pname, e)
        return False

def set_expr_by_names(o, names, expr, fallback_keywords=None, print_ok=False):
    if o is None:
        return None

    for name in names:
        p = get_par(o, name)
        if p is not None:
            try:
                p.expr = expr
                if print_ok:
                    print('EXPR', o.path + '.par.' + p.name, '=', expr)
                return p
            except Exception:
                pass

    if fallback_keywords:
        kws = [k.lower() for k in fallback_keywords]
        try:
            pars = o.pars()
        except Exception:
            pars = []
        for p in pars:
            try:
                label = p.label
            except Exception:
                label = ''
            key = (p.name + ' ' + label).lower()
            if any(k in key for k in kws):
                try:
                    p.expr = expr
                    if print_ok:
                        print('EXPR fallback', o.path + '.par.' + p.name, '=', expr)
                    return p
                except Exception:
                    pass

    print('WARNING could not set expression on', o.path if o else None, names, expr)
    return None

def ensure_float_param(root, page, par_name, label, default, norm_min, norm_max):
    p = get_par(root, par_name)
    if p is not None:
        print('PARAM already exists:', par_name, 'current =', p.eval())
        return p

    pars = page.appendFloat(par_name, label=label)
    p = pars[0]
    p.default = default
    p.val = default
    p.normMin = norm_min
    p.normMax = norm_max
    print('ADDED PARAM', par_name, '=', default)
    return p

def destroy_if_exists(parent, name):
    o = parent.op(name)
    if o is not None:
        try:
            o.destroy()
        except Exception as e:
            print('WARNING could not destroy', o.path, e)

def create_op(parent, type_names, name, destroy=True):
    if destroy:
        destroy_if_exists(parent, name)
    else:
        existing = parent.op(name)
        if existing is not None:
            return existing

    errors = []
    for tn in type_names:
        try:
            return parent.create(tn, name)
        except Exception as e:
            errors.append('%s: %s' % (tn, repr(e)))
    raise Exception('Cannot create %s. Tried: %s' % (name, errors))

def connect_ops(src, dst, input_index=0):
    try:
        dst.inputConnectors[input_index].connect(src)
        return True
    except Exception as e:
        print('WARNING connect failed:', src.path if src else None, '->', dst.path if dst else None, e)
        return False

def set_flag_safe(o, flag_name, value):
    try:
        setattr(o, flag_name, value)
        return True
    except Exception:
        return False

def assign_callbacks(script_sop, callback_dat):
    # Different TD builds expose slightly different callback parameter names.
    ok = False
    for pname in ['callbacks', 'callbacksdat', 'callbackdat', 'dat', 'script']:
        p = get_par(script_sop, pname)
        if p is not None:
            try:
                p.val = callback_dat.path
                print('SET callback DAT:', script_sop.path, pname, callback_dat.path)
                ok = True
                break
            except Exception:
                pass

    # Also replace docked DAT text when available.
    try:
        for d in script_sop.docked:
            if d.family == 'DAT':
                d.text = callback_dat.text
                print('UPDATED docked DAT:', d.path)
                ok = True
    except Exception:
        pass

    if not ok:
        print('WARNING: could not assign callbacks to', script_sop.path)
    return ok

# -------------------------------------------------------------------------
# CUSTOM PARAMS V09
# -------------------------------------------------------------------------
try:
    page = root.appendCustomPage('DNA V09')
except Exception:
    try:
        page = root.appendCustomPage('DNA V09b')
    except Exception as e:
        raise Exception('Impossible de créer une page custom V09: ' + repr(e))

ensure_float_param(root, page, 'Curvedeformactive', 'Curve deform active', 1.0, 0.0, 1.0)
ensure_float_param(root, page, 'Curvedeformamount', 'Curve deform amount', 1.0, 0.0, 1.0)
ensure_float_param(root, page, 'Curvecurvature', 'Curve curvature gain', 1.0, 0.0, 3.0)
ensure_float_param(root, page, 'Curveoffset', 'Curve surface offset', 0.075, -0.5, 0.5)
ensure_float_param(root, page, 'Curveextrudegain', 'Curve extrusion gain', 1.0, 0.0, 3.0)

# 0 = largeur de la lettre sur l'axe X du tube, hauteur de la lettre courbée autour du tube.
# 1 = largeur de la lettre courbée autour du tube, hauteur de la lettre sur l'axe X.
ensure_float_param(root, page, 'Curvemode', 'Curve mode', 0.0, 0.0, 1.0)

# Inversion locale de la courbure si le sens d'enroulement semble mauvais.
ensure_float_param(root, page, 'Curveflip', 'Curve flip', 0.0, 0.0, 1.0)

# Évite une trop forte déformation si une lettre a une boîte très grande.
ensure_float_param(root, page, 'Curvemaxangle', 'Curve max angle degrees', 38.0, 2.0, 120.0)

# Si 1, la V09 prend le dessus et met les Geometry COMP des lettres à transform identité.
# Si 0, retour au mode V08: les geos reprennent les expressions transform classiques.
ensure_float_param(root, page, 'Curvescriptmode', 'Curve script mode', 1.0, 0.0, 1.0)

# -------------------------------------------------------------------------
# CENTRAL GEOMETRY MODULE
# -------------------------------------------------------------------------
geom_module = create_op(root, ['textDAT'], 'dna_v09_geom_module', destroy=False)

geom_module.text = r"""
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

    cx = math.cos(rx)
    sx = math.sin(rx)
    cy = math.cos(ry)
    sy = math.sin(ry)
    cz = math.cos(rz)
    sz = math.sin(rz)

    # X
    y, z = y * cx - z * sx, y * sx + z * cx

    # Y
    x, z = x * cy + z * sy, -x * sy + z * cy

    # Z
    x, y = x * cz - y * sz, x * sz + y * cz

    return x, y, z

def depth_scale_multiplier(local_front_z, camera_front_z, radius, view_scale):
    active = par_value('Depthscaleactive', 1.0)
    if active < 0.5:
        return 1.0

    amount = par_value('Depthscaleamount', 1.0)
    min_s = par_value('Depthscalemin', 0.58)
    max_s = par_value('Depthscalemax', 1.38)
    curve = max(0.001, par_value('Depthscalecurve', 1.15))
    flip = par_value('Depthscaleflip', 0.0)
    mode = par_value('Depthscalemode', 0.0)

    if mode >= 0.5:
        denom = max(0.001, abs(radius * view_scale))
        frontness = camera_front_z / denom
    else:
        denom = max(0.001, abs(radius))
        frontness = local_front_z / denom

    frontness = clamp(frontness, -1.0, 1.0)

    if flip >= 0.5:
        frontness = -frontness

    t = 0.5 + 0.5 * frontness
    t = clamp(t, 0.0, 1.0)
    t = math.pow(t, curve)

    target = lerp(min_s, max_s, t)
    return lerp(1.0, target, amount)

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

    if mirrororder >= 0.5:
        j = (n - 1) - i
    else:
        j = i

    t_word = 0.0 if n <= 1 else j / float(n - 1)

    axis_x = (j - (n - 1) * 0.5) * pitch

    strand_offset = (i % 2) * math.pi

    phase = absTime.seconds * speed * math.tau
    angle = t_word * math.tau * turns + phase + strand_offset + math.radians(globalspin)

    roll = absTime.seconds * axis_roll_speed * math.tau + math.radians(axis_roll_angle)
    theta = angle + roll

    # Position locale de la lettre sur le cylindre.
    base_x = axis_x
    base_y = math.cos(theta) * radius
    base_z = math.sin(theta) * radius

    # Repère local du tube:
    # axis_vec = axe horizontal du tube.
    # tangent_vec = direction tangentielle autour du tube.
    # normal_vec = normale sortante du tube.
    axis_vec = (1.0, 0.0, 0.0)
    tangent_vec = (0.0, -math.sin(theta), math.cos(theta))
    normal_vec = (0.0, math.cos(theta), math.sin(theta))

    # Depth scale computed from local position, plus possible camera-depth mode.
    # First compute camera z of the center point after View rotation.
    cx = base_x * view_scale
    cy = base_y * view_scale
    cz = base_z * view_scale
    _, _, camera_z_center = rotate_point_xyz(cx, cy, cz, view_rx, view_ry, view_rz)

    dsm = depth_scale_multiplier(base_z, camera_z_center, radius, view_scale)

    pulse = 1.0 + 0.035 * math.sin(phase * 2.0 + i * 0.71)
    glyph_scale = lettersize * pulse * dsm

    return {
        'radius': radius,
        'pitch': pitch,
        'theta': theta,
        'base': (base_x, base_y, base_z),
        'axis': axis_vec,
        'tangent': tangent_vec,
        'normal': normal_vec,
        'glyph_scale': glyph_scale,
        'view_rx': view_rx,
        'view_ry': view_ry,
        'view_rz': view_rz,
        'view_scale': view_scale,
        'view_tx': view_tx,
        'view_ty': view_ty,
        'view_tz': view_tz,
        'lettermirrorx': lettermirrorx,
    }

def world_transform_local_point(x, y, z, state):
    # Apply global View transform around the tube center.
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

    minx, maxx, miny, maxy, minz, maxz = bbox

    cx = 0.5 * (minx + maxx)
    cy = 0.5 * (miny + maxy)
    cz = 0.5 * (minz + maxz)

    # Coordonnées locales centrées du point dans la lettre.
    lx = (px - cx) * glyph_scale
    ly = (py - cy) * glyph_scale
    lz = (pz - cz) * glyph_scale * extrusion_gain

    # Correction miroir locale conservée depuis V06.
    if state['lettermirrorx'] >= 0.5:
        lx = -lx

    # Repère tangent "plat" au point de la lettre sur le tube.
    # C'est le fallback amount=0.
    flat_x = base[0] + axis_vec[0] * lx + tangent_vec[0] * ly + normal_vec[0] * (offset + lz)
    flat_y = base[1] + axis_vec[1] * lx + tangent_vec[1] * ly + normal_vec[1] * (offset + lz)
    flat_z = base[2] + axis_vec[2] * lx + tangent_vec[2] * ly + normal_vec[2] * (offset + lz)

    # Mapping cylindrique.
    # Mode 0:
    #   lx = axe horizontal du tube
    #   ly = enroulement autour du tube
    # Mode 1:
    #   lx = enroulement autour du tube
    #   ly = axe horizontal du tube
    if curve_mode < 0.5:
        axial_offset = lx
        angular_source = ly
    else:
        axial_offset = ly
        angular_source = lx

    if curve_flip >= 0.5:
        angular_source = -angular_source

    max_angle = math.radians(max(0.001, max_angle_deg))
    angular_offset = (angular_source / radius) * curvature
    angular_offset = clamp(angular_offset, -max_angle, max_angle)

    theta_p = state['theta'] + angular_offset
    r_p = radius + offset + lz

    curved_x = base[0] + axial_offset
    curved_y = math.cos(theta_p) * r_p
    curved_z = math.sin(theta_p) * r_p

    amount = clamp(amount, 0.0, 1.0)

    # Blend plat -> courbé.
    x = lerp(flat_x, curved_x, amount)
    y = lerp(flat_y, curved_y, amount)
    z = lerp(flat_z, curved_z, amount)

    return world_transform_local_point(x, y, z, state)

def deform_script_sop(scriptOp, letter_index):
    # Force a dependency on this changing parameter if available.
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

def v08_transform_value(i, field):
    # Fallback mode if Curvescriptmode = 0.
    # This reproduces the V08 transform-driven behavior enough to revert quickly.
    s = letter_state(i)
    x, y, z = world_transform_local_point(s['base'][0], s['base'][1], s['base'][2], s)
    sc = s['glyph_scale'] * s['view_scale']
    sx = -sc if s['lettermirrorx'] >= 0.5 else sc

    if field == 'tx': return x
    if field == 'ty': return y
    if field == 'tz': return z
    if field == 'rx': return s['view_rx']
    if field == 'ry': return s['view_ry']
    if field == 'rz': return s['view_rz']
    if field == 'sx': return sx
    if field == 'sy': return sc
    if field == 'sz': return sc
    return 0.0
"""

geom_module_abs = geom_module.path

# -------------------------------------------------------------------------
# SCRIPT SOP CALLBACK TEMPLATE
# -------------------------------------------------------------------------
callback_template = r"""
# Auto-generated by morphogenesis_dna_td_v09_CURVED_LETTERS.py
# This DAT drives one Script SOP letter deformation.

ROOT_PATH = '/project1/MORPHOGENESIS_DNA_TD'
LETTER_INDEX = __LETTER_INDEX__

def _cook_impl(scriptOp):
    # Copy input text geometry, then deform its points on the tube surface.
    if len(scriptOp.inputs) < 1 or scriptOp.inputs[0] is None:
        scriptOp.clear()
        return

    in_sop = scriptOp.inputs[0]
    scriptOp.copy(in_sop)

    try:
        op(ROOT_PATH + '/dna_v09_geom_module').module.deform_script_sop(scriptOp, LETTER_INDEX)
    except Exception as e:
        try:
            scriptOp.addWarning('V09 deform failed: ' + repr(e))
        except Exception:
            pass
        # Keep copied geometry visible if deformation fails.
        return

def cook(scriptOp):
    _cook_impl(scriptOp)
    return

def onCook(scriptOp):
    _cook_impl(scriptOp)
    return

def setupParameters(scriptOp):
    return

def onSetupParameters(scriptOp):
    return

def onPulse(par):
    return

def onGetCookLevel(scriptOp):
    # WHEN_USED = cooks every frame when render1 asks for the result.
    # If the enum is unavailable in this build, TD will keep automatic cooking.
    try:
        return CookLevel.WHEN_USED
    except Exception:
        return
"""

# -------------------------------------------------------------------------
# APPLY V09 NETWORK TO LETTERS
# -------------------------------------------------------------------------
geo_paths = []
thickness_expr = "op('%s').par.Letterthickness" % ROOT_PATH
force_expr = "absTime.frame"

script_mode_expr = "op('%s').par.Curvescriptmode" % ROOT_PATH

for i, ch in enumerate(WORD):
    geo = root.op('letter_%02d_%s' % (i, ch))
    if geo is None:
        print('WARNING missing:', 'letter_%02d_%s' % (i, ch))
        continue

    # Find the original text SOP.
    text_sops = [c for c in geo.children if c.family == 'SOP' and c.name.startswith('text_')]
    if not text_sops:
        # fallback: first non-v09 SOP
        text_sops = [c for c in geo.children if c.family == 'SOP' and 'bend_letter_v09' not in c.name]
    if not text_sops:
        print('WARNING no text SOP found in', geo.path)
        continue

    text_sop = text_sops[0]

    # Keep thickness control.
    set_expr_by_names(
        text_sop,
        ['extrude', 'depth', 'Depth'],
        thickness_expr,
        fallback_keywords=['extrude', 'depth', 'thick']
    )

    # Create / replace Script SOP.
    deform_sop = create_op(geo, ['scriptSOP'], 'bend_letter_v09', destroy=True)
    deform_sop.nodeX = text_sop.nodeX + 180
    deform_sop.nodeY = text_sop.nodeY

    connect_ops(text_sop, deform_sop, 0)

    # Force-cook parameter.
    try:
        p = get_par(deform_sop, 'Forcecook')
        if p is None:
            page_fc = deform_sop.appendCustomPage('V09')
            pars = page_fc.appendFloat('Forcecook', label='Force cook frame')
            p = pars[0]
        p.expr = force_expr
    except Exception as e:
        print('WARNING could not create Forcecook parameter on', deform_sop.path, e)

    # Callback DAT.
    cb = create_op(geo, ['textDAT'], 'bend_letter_v09_callbacks', destroy=True)
    cb.nodeX = deform_sop.nodeX
    cb.nodeY = deform_sop.nodeY - 90
    cb.text = callback_template.replace('__LETTER_INDEX__', str(i))
    assign_callbacks(deform_sop, cb)

    # Use script SOP as visible/rendered SOP.
    for c in geo.children:
        if c.family == 'SOP':
            set_flag_safe(c, 'display', False)
            set_flag_safe(c, 'render', False)

    set_flag_safe(deform_sop, 'display', True)
    set_flag_safe(deform_sop, 'render', True)

    # The Script SOP outputs world/view-transformed points.
    # Therefore the Geometry COMP itself must be identity in script mode.
    # Curvescriptmode is left as a manual switch, but default is script mode.
    for pname, val in [
        ('tx', 0), ('ty', 0), ('tz', 0),
        ('rx', 0), ('ry', 0), ('rz', 0),
        ('sx', 1), ('sy', 1), ('sz', 1),
    ]:
        set_par_safe(geo, [pname], val)

    set_flag_safe(geo, 'display', True)
    set_flag_safe(geo, 'render', True)

    geo_paths.append(geo.path)

# -------------------------------------------------------------------------
# TUBE: keep V07 global perspective transform.
# -------------------------------------------------------------------------
tube_geos = [
    root.op('helix_tube_surface_v06'),
    root.op('helix_tube_wire_v06')
]

for tube_geo in tube_geos:
    if tube_geo is None:
        continue

    set_expr_safe(tube_geo, 'tx', "op('%s').par.Viewtx" % ROOT_PATH)
    set_expr_safe(tube_geo, 'ty', "op('%s').par.Viewty" % ROOT_PATH)
    set_expr_safe(tube_geo, 'tz', "op('%s').par.Viewtz" % ROOT_PATH)

    set_expr_safe(tube_geo, 'rx', "op('%s').par.Viewrotx" % ROOT_PATH)
    set_expr_safe(tube_geo, 'ry', "op('%s').par.Viewroty" % ROOT_PATH)
    set_expr_safe(tube_geo, 'rz', "op('%s').par.Viewrotz" % ROOT_PATH)

    set_expr_safe(tube_geo, 'sx', "op('%s').par.Viewscale" % ROOT_PATH)
    set_expr_safe(tube_geo, 'sy', "op('%s').par.Viewscale" % ROOT_PATH)
    set_expr_safe(tube_geo, 'sz', "op('%s').par.Viewscale" % ROOT_PATH)

    set_flag_safe(tube_geo, 'display', True)
    set_flag_safe(tube_geo, 'render', True)

    geo_paths.append(tube_geo.path)

# Hide old optional center axis.
axis = root.op('center_axis_optional')
if axis is not None:
    try:
        axis.display = False
        axis.render = False
    except Exception:
        pass

# -------------------------------------------------------------------------
# CAMERA / RENDER SAFETY
# -------------------------------------------------------------------------
cam = root.op('cam1')
if cam is not None:
    set_par_safe(cam, ['lookat'], '')
    set_par_safe(cam, ['tx'], 0)
    set_par_safe(cam, ['ty'], 0)
    set_expr_safe(cam, 'tz', "op('%s').par.Cameradistance" % ROOT_PATH)
    set_par_safe(cam, ['rx'], 0)
    set_par_safe(cam, ['ry'], 0)
    set_par_safe(cam, ['rz'], 0)

render = root.op('render1')
light_key = root.op('light_key')
light_fill = root.op('light_fill')

if render is not None:
    if cam is not None:
        set_par_safe(render, ['camera', 'cameras'], cam.path)

    set_par_safe(render, ['geometry', 'geo', 'geometries'], ' '.join(geo_paths))

    if light_key is not None and light_fill is not None:
        set_par_safe(render, ['lights', 'light'], light_key.path + ' ' + light_fill.path)

    set_par_safe(render, ['resx', 'w'], 1280)
    set_par_safe(render, ['resy', 'h'], 720)

try:
    root.layout(root.children)
except Exception:
    pass

print('=' * 72)
print('MORPHOGENESIS DNA V09 CURVED LETTERS OK')
print('Open:', ROOT_PATH + '/render1')
print('Controls:', ROOT_PATH, '> page DNA V09')
print('Main controls:')
print('  Curvedeformactive = 1')
print('  Curvedeformamount = 1')
print('  Curvemode = 0  : letter width along tube axis, height curves around tube')
print('  Curvemode = 1  : letter width curves around tube, height along tube axis')
print('  Curveoffset = 0.075')
print('  Curvemaxangle = 38')
print('If deformation direction is visually wrong, set Curveflip = 1')
print('=' * 72)
