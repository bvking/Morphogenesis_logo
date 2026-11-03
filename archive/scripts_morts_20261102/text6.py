# archive du DAT /project1/text6 (purge du 2026-11-02)
# morphogenesis_dna_td_v08_DEPTH_SCALE.py
# TouchDesigner 2025.32460
#
# À lancer après la V07.
#
# Effet:
# - Corrige la logique de taille dynamique:
#   quand une lettre passe vers l'avant du tube, elle grossit;
#   quand elle passe vers l'arrière du tube, elle rapetisse.
# - La taille n'est plus seulement un effet de perspective caméra:
#   elle est explicitement calculée depuis la position de rotation autour du tube.
#
# Nouveaux contrôles:
#   Depthscaleactive
#   Depthscaleamount
#   Depthscalemin
#   Depthscalemax
#   Depthscalecurve
#   Depthscaleflip
#   Depthscalemode
#
# Usage:
# 1) Colle ce script dans un Text DAT.
# 2) Run Script.
# 3) Ouvre /project1/MORPHOGENESIS_DNA_TD/render1
# 4) Réglages sur /project1/MORPHOGENESIS_DNA_TD > page DNA V08

import math

ROOT_PATH = '/project1/MORPHOGENESIS_DNA_TD'
WORD = 'MORPHOGENESIS'

root = op(ROOT_PATH)
if root is None:
    raise Exception('Container introuvable: ' + ROOT_PATH)

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

def set_flag_safe(o, flag_name, value):
    try:
        setattr(o, flag_name, value)
        return True
    except Exception:
        return False

# -------------------------------------------------------------------------
# CUSTOM PARAMS V08
# -------------------------------------------------------------------------
try:
    page = root.appendCustomPage('DNA V08')
except Exception:
    try:
        page = root.appendCustomPage('DNA V08b')
    except Exception as e:
        raise Exception('Impossible de créer une page custom V08: ' + repr(e))

ensure_float_param(root, page, 'Depthscaleactive', 'Depth scale active', 1.0, 0.0, 1.0)
ensure_float_param(root, page, 'Depthscaleamount', 'Depth scale amount', 1.0, 0.0, 2.0)
ensure_float_param(root, page, 'Depthscalemin', 'Depth scale min/back', 0.58, 0.05, 1.5)
ensure_float_param(root, page, 'Depthscalemax', 'Depth scale max/front', 1.38, 0.2, 3.0)
ensure_float_param(root, page, 'Depthscalecurve', 'Depth scale curve', 1.15, 0.2, 4.0)
ensure_float_param(root, page, 'Depthscaleflip', 'Depth scale flip', 0.0, 0.0, 1.0)

# 0 = front/back calculé selon la rotation locale autour du tube.
# 1 = front/back calculé selon la profondeur caméra après Viewrotx/y/z.
# Pour ton cas actuel, 0 est normalement plus précis et plus stable.
ensure_float_param(root, page, 'Depthscalemode', 'Depth scale mode', 0.0, 0.0, 1.0)

# -------------------------------------------------------------------------
# REPLACE MATH MODULE
# -------------------------------------------------------------------------
module_dat = root.op('dna_math_module')
if module_dat is None:
    module_dat = root.create('textDAT', 'dna_math_module')

module_dat.text = r"""
import math
WORD = 'MORPHOGENESIS'

def root_op():
    return me.parent()

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
    # Rotation autour de l'origine:
    # 1) X, 2) Y, 3) Z.
    # L'origine est le centre du tube.
    rx = math.radians(rx_deg)
    ry = math.radians(ry_deg)
    rz = math.radians(rz_deg)

    cx = math.cos(rx)
    sx = math.sin(rx)
    cy = math.cos(ry)
    sy = math.sin(ry)
    cz = math.cos(rz)
    sz = math.sin(rz)

    # rotate X
    y, z = y * cx - z * sx, y * sx + z * cx

    # rotate Y
    x, z = x * cy + z * sy, -x * sy + z * cy

    # rotate Z
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

    # Mode 0:
    # - utilise la profondeur locale de rotation autour du tube.
    # - c'est le plus fiable pour "arrière du tube = petit / avant du tube = grand".
    #
    # Mode 1:
    # - utilise la profondeur après orientation globale Viewrotx/y/z.
    # - utile si la perspective globale est très oblique.
    if mode >= 0.5:
        denom = max(0.001, abs(radius * view_scale))
        frontness = camera_front_z / denom
    else:
        denom = max(0.001, abs(radius))
        frontness = local_front_z / denom

    frontness = clamp(frontness, -1.0, 1.0)

    if flip >= 0.5:
        frontness = -frontness

    # -1 arrière -> 0
    #  0 centre  -> 0.5
    # +1 avant   -> 1
    t = 0.5 + 0.5 * frontness
    t = clamp(t, 0.0, 1.0)
    t = math.pow(t, curve)

    target = lerp(min_s, max_s, t)

    # amount = 0 : aucun effet
    # amount = 1 : effet normal
    # amount > 1 : effet renforcé
    return lerp(1.0, target, amount)

def value(i, field):
    n = len(WORD)

    radius = par_value('Radius', 2.15)
    pitch = par_value('Pitch', 0.48)
    turns = par_value('Turns', 2.25)

    speed = par_value('Speed', 0.18)
    axis_roll_speed = par_value('Axisrollspeed', 0.12)
    axis_roll_angle = par_value('Axisrollangle', 0.0)

    lettersize = par_value('Lettersize', par_value('Letterscale', 0.34))
    mirrororder = par_value('Mirrororder', 1.0)
    facecamera = par_value('Facecamera', 1.0)
    lettermirrorx = par_value('Lettermirrorx', 1.0)

    globalspin = par_value('Globalspin', 0.0)

    # V07 orientation/perspective globale.
    view_rx = par_value('Viewrotx', 0.0)
    view_ry = par_value('Viewroty', -18.0)
    view_rz = par_value('Viewrotz', 0.0)
    view_scale = par_value('Viewscale', 1.0)
    view_tx = par_value('Viewtx', 0.0)
    view_ty = par_value('Viewty', 0.0)
    view_tz = par_value('Viewtz', 0.0)

    # Ordre spatial:
    # Mirrororder = 1 garde la lecture M O R P H O G E N E S I S de gauche à droite.
    if mirrororder >= 0.5:
        j = (n - 1) - i
    else:
        j = i

    t_word = 0.0 if n <= 1 else j / float(n - 1)

    # Axe principal horizontal local:
    # x = longueur du tube
    # y/z = section circulaire autour de l'axe X.
    x_local = (j - (n - 1) * 0.5) * pitch

    strand_offset = (i % 2) * math.pi

    phase = absTime.seconds * speed * math.tau
    angle = t_word * math.tau * turns + phase + strand_offset + math.radians(globalspin)

    y0 = math.cos(angle) * radius
    z0 = math.sin(angle) * radius

    # Rotation vivante des deux brins autour de l'axe horizontal X.
    roll = absTime.seconds * axis_roll_speed * math.tau + math.radians(axis_roll_angle)

    cy = math.cos(roll)
    sy = math.sin(roll)

    y_local = y0 * cy - z0 * sy
    z_local = y0 * sy + z0 * cy

    # z_local est l'information la plus propre:
    # positif = vers l'avant du tube/caméra dans la vue standard,
    # négatif = vers l'arrière.
    local_front_z = z_local

    total_angle = angle + roll

    # Position globale avec orientation autour du centre du tube.
    x = x_local * view_scale
    y = y_local * view_scale
    z = z_local * view_scale

    x_rot, y_rot, z_rot = rotate_point_xyz(x, y, z, view_rx, view_ry, view_rz)

    camera_front_z = z_rot

    x = x_rot + view_tx
    y = y_rot + view_ty
    z = z_rot + view_tz

    # Orientation des lettres:
    # Facecamera = 1: lettres lisibles, mais orientées avec la perspective globale.
    if facecamera >= 0.5:
        rx = view_rx
        ry = view_ry
        rz = view_rz
    else:
        rx = math.degrees(total_angle) - 90.0 + view_rx
        ry = view_ry
        rz = math.sin(angle * 1.37 + phase) * 8.0 + view_rz

    # Léger pulse conservé, mais beaucoup plus discret que l'effet profondeur.
    pulse = 1.0 + 0.035 * math.sin(phase * 2.0 + i * 0.71)

    dsm = depth_scale_multiplier(local_front_z, camera_front_z, radius, view_scale)

    sc = lettersize * pulse * view_scale * dsm

    # Miroir local de correction de lecture.
    sx = -sc if lettermirrorx >= 0.5 else sc

    if field == 'tx': return x
    if field == 'ty': return y
    if field == 'tz': return z
    if field == 'rx': return rx
    if field == 'ry': return ry
    if field == 'rz': return rz
    if field == 'sx': return sx
    if field == 'sy': return sc
    if field == 'sz': return sc

    # Debug values can be queried manually from Textport:
    # op('/project1/MORPHOGENESIS_DNA_TD/dna_math_module').module.value(0, 'frontness')
    if field == 'localfrontz': return local_front_z
    if field == 'camerafrontz': return camera_front_z
    if field == 'depthmult': return dsm

    return 0.0
"""

module_abs = module_dat.path
thickness_expr = "op('%s').par.Letterthickness" % ROOT_PATH

# -------------------------------------------------------------------------
# APPLY EXPRESSIONS TO LETTERS
# -------------------------------------------------------------------------
geo_paths = []

for i, ch in enumerate(WORD):
    geo = root.op('letter_%02d_%s' % (i, ch))
    if geo is None:
        print('WARNING missing:', 'letter_%02d_%s' % (i, ch))
        continue

    for pname in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']:
        set_expr_safe(geo, pname, "op('%s').module.value(%d, '%s')" % (module_abs, i, pname))

    # Keep distinct thickness control on Text SOP.
    for child in geo.children:
        if child.family == 'SOP':
            set_expr_by_names(
                child,
                ['extrude', 'depth', 'Depth'],
                thickness_expr,
                fallback_keywords=['extrude', 'depth', 'thick']
            )
            set_flag_safe(child, 'display', True)
            set_flag_safe(child, 'render', True)

    set_flag_safe(geo, 'display', True)
    set_flag_safe(geo, 'render', True)

    geo_paths.append(geo.path)

# -------------------------------------------------------------------------
# KEEP TUBE UNDER V07 GLOBAL PERSPECTIVE
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

# Keep old optional axis hidden.
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
print('MORPHOGENESIS DNA V08 DEPTH SCALE OK')
print('Open:', ROOT_PATH + '/render1')
print('Controls:', ROOT_PATH, '> page DNA V08')
print('Depthscalemode = 0 : scale from tube local front/back')
print('Depthscalemode = 1 : scale from camera depth after View rotation')
print('If front/back is inverted, set Depthscaleflip = 1')
print('Next step can be V09: curved letter deformation around tube surface.')
print('=' * 72)
