# archive du DAT /project1/text4 (purge du 2026-11-02)
# morphogenesis_dna_td_v06_LETTER_MIRROR_TUBE.py
# TouchDesigner 2025.32460
#
# À lancer après la V05.
#
# Effet:
# - Corrige les lettres qui apparaissent à l'envers avec un miroir local X.
# - Ajoute un tube transparent visible autour de la double spirale.
# - Le tube est centré sur l'axe horizontal X.
# - Le rayon du tube suit automatiquement le paramètre Radius.
# - La longueur du tube suit automatiquement Pitch et le nombre de lettres.
#
# Usage:
# 1) Colle ce script dans un Text DAT.
# 2) Run Script.
# 3) Ouvre /project1/MORPHOGENESIS_DNA_TD/render1
# 4) Réglages sur /project1/MORPHOGENESIS_DNA_TD > page DNA V06

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

def destroy_if_exists(parent, name):
    o = parent.op(name)
    if o is not None:
        try:
            o.destroy()
        except Exception as e:
            print('WARNING could not destroy', o.path, e)

def create_op(parent, type_names, name):
    destroy_if_exists(parent, name)
    errors = []
    for tn in type_names:
        try:
            return parent.create(tn, name)
        except Exception as e:
            errors.append('%s: %s' % (tn, repr(e)))
    raise Exception('Cannot create %s. Tried: %s' % (name, errors))

def clear_children(comp):
    for c in list(comp.children):
        try:
            c.destroy()
        except Exception:
            pass

def set_flag_safe(o, flag_name, value):
    try:
        setattr(o, flag_name, value)
        return True
    except Exception:
        return False

# -------------------------------------------------------------------------
# CUSTOM PARAMS V06
# -------------------------------------------------------------------------
try:
    page = root.appendCustomPage('DNA V06')
except Exception:
    try:
        page = root.appendCustomPage('DNA V06b')
    except Exception as e:
        raise Exception('Impossible de créer une page custom V06: ' + repr(e))

# Default = 1 car les lettres apparaissent actuellement à l'envers.
ensure_float_param(root, page, 'Lettermirrorx', 'Letter mirror X', 1.0, 0.0, 1.0)

# Tube controls.
ensure_float_param(root, page, 'Tubevisible', 'Tube visible', 1.0, 0.0, 1.0)
ensure_float_param(root, page, 'Tubealpha', 'Tube surface alpha', 0.13, 0.0, 1.0)
ensure_float_param(root, page, 'Tubewirealpha', 'Tube wire alpha', 0.65, 0.0, 1.0)
ensure_float_param(root, page, 'Tubewirewidth', 'Tube wire width', 1.6, 0.1, 8.0)
ensure_float_param(root, page, 'Tubeextra', 'Tube extra length', 0.85, 0.0, 4.0)

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

    # Ordre spatial:
    # Mirrororder = 1 garde la lecture M O R P H O G E N E S I S de gauche à droite.
    if mirrororder >= 0.5:
        j = (n - 1) - i
    else:
        j = i

    t = 0.0 if n <= 1 else j / float(n - 1)

    # Axe principal horizontal X.
    x = (j - (n - 1) * 0.5) * pitch

    # Alternance des deux brins selon la lettre réelle.
    strand_offset = (i % 2) * math.pi

    phase = absTime.seconds * speed * math.tau
    angle = t * math.tau * turns + phase + strand_offset + math.radians(globalspin)

    y0 = math.cos(angle) * radius
    z0 = math.sin(angle) * radius

    # Rotation globale autour de l'axe X.
    roll = absTime.seconds * axis_roll_speed * math.tau + math.radians(axis_roll_angle)

    cy = math.cos(roll)
    sy = math.sin(roll)

    y = y0 * cy - z0 * sy
    z = y0 * sy + z0 * cy

    total_angle = angle + roll

    # Deux modes:
    # Facecamera = 1 : lettres lisibles de face.
    # Facecamera = 0 : lettres orientées sur la double hélice.
    if facecamera >= 0.5:
        rx = 0.0
        ry = 0.0
        rz = 0.0
    else:
        rx = math.degrees(total_angle) - 90.0
        ry = 0.0
        rz = math.sin(angle * 1.37 + phase) * 8.0

    pulse = 1.0 + 0.08 * math.sin(phase * 2.0 + i * 0.71)
    sc = lettersize * pulse

    # V06:
    # Si les lettres sont vues à l'envers, on applique un miroir local X.
    # Cela ne change pas leur position sur la spirale.
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

    # Keep distinct thickness control on the Text SOP.
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
# TUBE MATERIALS
# -------------------------------------------------------------------------
mat_surface = create_op(root, ['phongMAT'], 'mat_tube_transparent_v06')
set_par_safe(mat_surface, ['diffuser'], 0.35)
set_par_safe(mat_surface, ['diffuseg'], 0.85)
set_par_safe(mat_surface, ['diffuseb'], 1.00)
set_par_safe(mat_surface, ['ambientr'], 0.08)
set_par_safe(mat_surface, ['ambientg'], 0.18)
set_par_safe(mat_surface, ['ambientb'], 0.24)

alpha_surface_expr = "op('%s').par.Tubevisible * op('%s').par.Tubealpha" % (ROOT_PATH, ROOT_PATH)
set_expr_by_names(mat_surface, ['alphafront'], alpha_surface_expr, fallback_keywords=['alpha front', 'opacity', 'alpha'])
set_expr_by_names(mat_surface, ['alphaside'], alpha_surface_expr, fallback_keywords=['alpha side'])
set_par_safe(mat_surface, ['alphamode'], True)
set_par_safe(mat_surface, ['blending'], True)
set_par_safe(mat_surface, ['depthwriting'], False)
set_par_safe(mat_surface, ['cullface'], 'neither')
set_par_safe(mat_surface, ['wireframe'], 'off')

mat_wire = create_op(root, ['phongMAT'], 'mat_tube_wire_v06')
set_par_safe(mat_wire, ['diffuser'], 0.75)
set_par_safe(mat_wire, ['diffuseg'], 0.95)
set_par_safe(mat_wire, ['diffuseb'], 1.00)
set_par_safe(mat_wire, ['ambientr'], 0.20)
set_par_safe(mat_wire, ['ambientg'], 0.25)
set_par_safe(mat_wire, ['ambientb'], 0.30)

alpha_wire_expr = "op('%s').par.Tubevisible * op('%s').par.Tubewirealpha" % (ROOT_PATH, ROOT_PATH)
set_expr_by_names(mat_wire, ['alphafront'], alpha_wire_expr, fallback_keywords=['alpha front', 'opacity', 'alpha'])
set_expr_by_names(mat_wire, ['alphaside'], alpha_wire_expr, fallback_keywords=['alpha side'])
set_expr_by_names(mat_wire, ['wirewidth'], "op('%s').par.Tubewirewidth" % ROOT_PATH, fallback_keywords=['wire width'])
set_par_safe(mat_wire, ['alphamode'], True)
set_par_safe(mat_wire, ['blending'], True)
set_par_safe(mat_wire, ['depthwriting'], False)
set_par_safe(mat_wire, ['cullface'], 'neither')
set_par_safe(mat_wire, ['wireframe'], 'topology')

# -------------------------------------------------------------------------
# TUBE GEOMETRY
# -------------------------------------------------------------------------
tube_height_expr = "(len('%s') - 1) * op('%s').par.Pitch + op('%s').par.Tubeextra" % (WORD, ROOT_PATH, ROOT_PATH)
tube_radius_expr = "op('%s').par.Radius" % ROOT_PATH

# Surface tube
tube_surface_geo = create_op(root, ['geometryCOMP', 'geoCOMP'], 'helix_tube_surface_v06')
tube_surface_geo.nodeX = 950
tube_surface_geo.nodeY = -520
clear_children(tube_surface_geo)

tube_surface = create_op(tube_surface_geo, ['tubeSOP'], 'tube_surface_sop')
set_par_safe(tube_surface, ['type'], 'mesh')
set_par_safe(tube_surface, ['surftype'], 'quads')
set_par_safe(tube_surface, ['orient'], 'x')
set_expr_by_names(tube_surface, ['rad1'], tube_radius_expr, fallback_keywords=['radius'])
set_expr_by_names(tube_surface, ['rad2'], tube_radius_expr, fallback_keywords=['radius'])
set_expr_by_names(tube_surface, ['height'], tube_height_expr, fallback_keywords=['height'])
set_par_safe(tube_surface, ['rows'], 48)
set_par_safe(tube_surface, ['cols'], 32)
set_par_safe(tube_surface, ['cap'], False)
set_par_safe(tube_surface, ['normals'], True)
set_flag_safe(tube_surface, 'display', True)
set_flag_safe(tube_surface, 'render', True)

set_par_safe(tube_surface_geo, ['material', 'mat'], mat_surface.path)
set_flag_safe(tube_surface_geo, 'display', True)
set_flag_safe(tube_surface_geo, 'render', True)
geo_paths.append(tube_surface_geo.path)

# Wire tube overlay
tube_wire_geo = create_op(root, ['geometryCOMP', 'geoCOMP'], 'helix_tube_wire_v06')
tube_wire_geo.nodeX = 1150
tube_wire_geo.nodeY = -520
clear_children(tube_wire_geo)

tube_wire = create_op(tube_wire_geo, ['tubeSOP'], 'tube_wire_sop')
set_par_safe(tube_wire, ['type'], 'poly')
set_par_safe(tube_wire, ['surftype'], 'rowcol')
set_par_safe(tube_wire, ['orient'], 'x')
set_expr_by_names(tube_wire, ['rad1'], tube_radius_expr, fallback_keywords=['radius'])
set_expr_by_names(tube_wire, ['rad2'], tube_radius_expr, fallback_keywords=['radius'])
set_expr_by_names(tube_wire, ['height'], tube_height_expr, fallback_keywords=['height'])
set_par_safe(tube_wire, ['rows'], 12)
set_par_safe(tube_wire, ['cols'], 64)
set_par_safe(tube_wire, ['cap'], False)
set_par_safe(tube_wire, ['normals'], True)
set_flag_safe(tube_wire, 'display', True)
set_flag_safe(tube_wire, 'render', True)

set_par_safe(tube_wire_geo, ['material', 'mat'], mat_wire.path)
set_flag_safe(tube_wire_geo, 'display', True)
set_flag_safe(tube_wire_geo, 'render', True)
geo_paths.append(tube_wire_geo.path)

# Keep old optional axis hidden
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
    set_par_safe(cam, ['tz'], 10.5)
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
print('MORPHOGENESIS DNA V06 LETTER MIRROR + TRANSPARENT TUBE OK')
print('Open:', ROOT_PATH + '/render1')
print('Controls:', ROOT_PATH, '> page DNA V06')
print('Lettermirrorx = 1 : miroir local de chaque lettre')
print('Tube radius is driven by Radius:', tube_radius_expr)
print('Tube length is driven by Pitch + Tubeextra:', tube_height_expr)
print('=' * 72)
