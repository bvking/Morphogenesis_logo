# archive du DAT /project1/text5 (purge du 2026-11-02)
# morphogenesis_dna_td_v07_PIVOT_PERSPECTIVE.py
# TouchDesigner 2025.32460
#
# À lancer après la V06.
#
# Effet:
# - Permet d'orienter l'ensemble lettres + tube autour du centre du tube.
# - Le pivot de rotation est le centre du tube, donc l'origine locale du système: (0, 0, 0).
# - Ajoute des contrôles de perspective / orientation globale:
#     Viewrotx, Viewroty, Viewrotz
#     Viewscale
#     Viewtx, Viewty, Viewtz
#     Cameradistance
#
# Remarque:
# - Cette V07 prépare proprement l'étape suivante:
#   déformer les lettres pour qu'elles épousent la courbure du tube.
# - Elle ne fait pas encore la déformation mesh des lettres.
#
# Usage:
# 1) Colle ce script dans un Text DAT.
# 2) Run Script.
# 3) Ouvre /project1/MORPHOGENESIS_DNA_TD/render1
# 4) Réglages sur /project1/MORPHOGENESIS_DNA_TD > page DNA V07

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
# CUSTOM PARAMS V07
# -------------------------------------------------------------------------
try:
    page = root.appendCustomPage('DNA V07')
except Exception:
    try:
        page = root.appendCustomPage('DNA V07b')
    except Exception as e:
        raise Exception('Impossible de créer une page custom V07: ' + repr(e))

# Rotation de l'ensemble autour du centre du tube.
ensure_float_param(root, page, 'Viewrotx', 'View rotate X', 0.0, -180.0, 180.0)
ensure_float_param(root, page, 'Viewroty', 'View rotate Y', -18.0, -180.0, 180.0)
ensure_float_param(root, page, 'Viewrotz', 'View rotate Z', 0.0, -180.0, 180.0)

# Echelle et position globale.
ensure_float_param(root, page, 'Viewscale', 'View scale', 1.0, 0.1, 4.0)
ensure_float_param(root, page, 'Viewtx', 'View translate X', 0.0, -5.0, 5.0)
ensure_float_param(root, page, 'Viewty', 'View translate Y', 0.0, -5.0, 5.0)
ensure_float_param(root, page, 'Viewtz', 'View translate Z', 0.0, -5.0, 5.0)

# Caméra stable face au centre du tube.
ensure_float_param(root, page, 'Cameradistance', 'Camera distance', 10.5, 3.0, 25.0)

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

    # V07: orientation/perspective globale de l'ensemble lettres + tube.
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

    t = 0.0 if n <= 1 else j / float(n - 1)

    # Axe principal horizontal local:
    # x = longueur du tube
    # y/z = section circulaire autour de l'axe X
    x = (j - (n - 1) * 0.5) * pitch

    strand_offset = (i % 2) * math.pi

    phase = absTime.seconds * speed * math.tau
    angle = t * math.tau * turns + phase + strand_offset + math.radians(globalspin)

    y0 = math.cos(angle) * radius
    z0 = math.sin(angle) * radius

    # Rotation vivante des deux brins autour de l'axe horizontal X.
    roll = absTime.seconds * axis_roll_speed * math.tau + math.radians(axis_roll_angle)

    cy = math.cos(roll)
    sy = math.sin(roll)

    y = y0 * cy - z0 * sy
    z = y0 * sy + z0 * cy

    total_angle = angle + roll

    # Position transformée autour du centre du tube.
    x *= view_scale
    y *= view_scale
    z *= view_scale

    x, y, z = rotate_point_xyz(x, y, z, view_rx, view_ry, view_rz)

    x += view_tx
    y += view_ty
    z += view_tz

    # Orientation des lettres:
    # Facecamera = 1: les lettres restent globalement lisibles,
    # mais elles suivent quand même la perspective globale V07.
    if facecamera >= 0.5:
        rx = view_rx
        ry = view_ry
        rz = view_rz
    else:
        rx = math.degrees(total_angle) - 90.0 + view_rx
        ry = view_ry
        rz = math.sin(angle * 1.37 + phase) * 8.0 + view_rz

    pulse = 1.0 + 0.08 * math.sin(phase * 2.0 + i * 0.71)
    sc = lettersize * pulse * view_scale

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

    # Keep V05/V06 distinct thickness control on Text SOP.
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
# APPLY SAME GLOBAL PERSPECTIVE TO TUBE GEOMETRIES
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
    # Stable camera centered on the tube center.
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

    # Use every active letter + both tube geometries.
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
print('MORPHOGENESIS DNA V07 PIVOT PERSPECTIVE OK')
print('Open:', ROOT_PATH + '/render1')
print('Controls:', ROOT_PATH, '> page DNA V07')
print('Pivot used for global orientation: tube center / origin (0, 0, 0)')
print('Next step can be V08: deform each letter mesh along the tube curvature.')
print('=' * 72)
