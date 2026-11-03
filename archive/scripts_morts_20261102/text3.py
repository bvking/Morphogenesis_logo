# archive du DAT /project1/text3 (purge du 2026-11-02)
# morphogenesis_dna_td_v05_MIRROR_SIZE_THICKNESS.py
# TouchDesigner 2025.32460
#
# À lancer après la V04.
#
# Effet:
# - Ajoute un mode miroir de lecture pour que MORPHOGENESIS apparaisse de gauche à droite.
# - Ajoute un contrôle distinct de la taille des lettres: Lettersize.
# - Ajoute un contrôle distinct de l'épaisseur/extrusion des lettres: Letterthickness.
# - Ajoute Facecamera pour garder les lettres lisibles même pendant la rotation autour de l'axe horizontal.
#
# Usage:
# 1) Colle ce script dans un Text DAT.
# 2) Run Script.
# 3) Ouvre /project1/MORPHOGENESIS_DNA_TD/render1
# 4) Réglages sur /project1/MORPHOGENESIS_DNA_TD > page DNA V05

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

def set_par_safe(o, names, value):
    if o is None:
        return False
    for name in names:
        p = get_par(o, name)
        if p is not None:
            try:
                p.val = value
                print('SET', o.path + '.par.' + p.name, '=', value)
                return True
            except Exception:
                pass
    print('WARNING could not set', o.path if o else None, names, value)
    return False

def set_expr_safe(o, pname, expr):
    p = get_par(o, pname)
    if p is None:
        return False
    try:
        p.expr = expr
        print('EXPR', o.path + '.par.' + pname, '=', expr)
        return True
    except Exception as e:
        print('WARNING expr failed:', o.path, pname, e)
        return False

def set_expr_by_names(o, names, expr, fallback_keywords=None):
    if o is None:
        return None

    for name in names:
        p = get_par(o, name)
        if p is not None:
            try:
                p.expr = expr
                print('EXPR', o.path + '.par.' + p.name, '=', expr)
                return p
            except Exception:
                pass

    # Fallback by parameter name/label search
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

# -------------------------------------------------------------------------
# CUSTOM PARAMS V05
# -------------------------------------------------------------------------
try:
    page = root.appendCustomPage('DNA V05')
except Exception:
    # If already exists, use a new page but do not duplicate parameters.
    try:
        page = root.appendCustomPage('DNA V05b')
    except Exception as e:
        raise Exception('Impossible de créer une page custom V05: ' + repr(e))

# Copy previous values when available
try:
    default_size = float(root.par.Letterscale.eval())
except Exception:
    default_size = 0.34

try:
    default_thickness = float(root.par.Depth.eval())
except Exception:
    default_thickness = 0.10

ensure_float_param(root, page, 'Mirrororder', 'Mirror order / left-to-right', 1.0, 0.0, 1.0)
ensure_float_param(root, page, 'Facecamera', 'Face camera / readable letters', 1.0, 0.0, 1.0)
ensure_float_param(root, page, 'Lettersize', 'Letter size', default_size, 0.02, 2.0)
ensure_float_param(root, page, 'Letterthickness', 'Letter thickness', default_thickness, 0.0, 1.5)

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

    # Speed = progression interne de la spirale.
    speed = par_value('Speed', 0.18)

    # V04/V05: rotation globale autour de l'axe horizontal X.
    axis_roll_speed = par_value('Axisrollspeed', 0.12)
    axis_roll_angle = par_value('Axisrollangle', 0.0)

    # V05: taille distincte de l'épaisseur.
    lettersize = par_value('Lettersize', par_value('Letterscale', 0.34))

    # V05: 1 = miroir de lecture, 0 = ordre V04.
    mirrororder = par_value('Mirrororder', 1.0)

    # V05: 1 = lettres toujours lisibles face caméra,
    #      0 = lettres orientées avec la double hélice.
    facecamera = par_value('Facecamera', 1.0)

    globalspin = par_value('Globalspin', 0.0)

    # On inverse l'index spatial quand Mirrororder = 1.
    # Cela donne une lecture MORPHOGENESIS de gauche à droite
    # dans la caméra standard située en +Z.
    if mirrororder >= 0.5:
        j = (n - 1) - i
    else:
        j = i

    t = 0.0 if n <= 1 else j / float(n - 1)

    # Axe principal horizontal:
    # x = longueur du mot/ADN
    # y/z = section circulaire autour de l'axe X
    x = (j - (n - 1) * 0.5) * pitch

    # Deux brins opposés.
    # On garde l'alternance selon la lettre réelle i,
    # sinon le brin changerait quand on active le miroir.
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

    # Mode hélicoïdal: les lettres suivent l'orientation de l'ADN.
    rx_helix = math.degrees(total_angle) - 90.0
    ry_helix = 0.0
    rz_helix = math.sin(angle * 1.37 + phase) * 8.0

    # Mode lisible: les lettres restent orientées vers la caméra.
    rx_cam = 0.0
    ry_cam = 0.0
    rz_cam = 0.0

    if facecamera >= 0.5:
        rx = rx_cam
        ry = ry_cam
        rz = rz_cam
    else:
        rx = rx_helix
        ry = ry_helix
        rz = rz_helix

    pulse = 1.0 + 0.08 * math.sin(phase * 2.0 + i * 0.71)
    sc = lettersize * pulse

    if field == 'tx': return x
    if field == 'ty': return y
    if field == 'tz': return z
    if field == 'rx': return rx
    if field == 'ry': return ry
    if field == 'rz': return rz
    if field == 'sx': return sc
    if field == 'sy': return sc
    if field == 'sz': return sc

    return 0.0
"""

module_abs = module_dat.path
thickness_expr = "op('%s').par.Letterthickness" % ROOT_PATH

# -------------------------------------------------------------------------
# APPLY EXPRESSIONS + THICKNESS TO LETTERS
# -------------------------------------------------------------------------
geo_paths = []

for i, ch in enumerate(WORD):
    geo = root.op('letter_%02d_%s' % (i, ch))
    if geo is None:
        print('WARNING missing:', 'letter_%02d_%s' % (i, ch))
        continue

    # Update transform expressions
    for pname in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']:
        set_expr_safe(geo, pname, "op('%s').module.value(%d, '%s')" % (module_abs, i, pname))

    # Update Text SOP thickness/extrude/depth
    for child in geo.children:
        if child.family == 'SOP':
            # Common Text SOP parameter names tried first.
            set_expr_by_names(
                child,
                ['extrude', 'depth', 'Depth'],
                thickness_expr,
                fallback_keywords=['extrude', 'depth', 'thick']
            )
            try: child.display = True
            except Exception: pass
            try: child.render = True
            except Exception: pass

    try: geo.display = True
    except Exception: pass
    try: geo.render = True
    except Exception: pass

    geo_paths.append(geo.path)

# Optional axis stays hidden by default in V05, as it can visually confuse the logo.
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
    # Stable camera facing origin from +Z.
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
print('MORPHOGENESIS DNA V05 MIRROR + SIZE + THICKNESS OK')
print('Open:', ROOT_PATH + '/render1')
print('Controls:', ROOT_PATH, '> page DNA V05')
print('Mirrororder = 1 : lecture miroir / gauche -> droite')
print('Facecamera = 1  : lettres lisibles face caméra')
print('Lettersize      : taille globale des lettres')
print('Letterthickness : épaisseur / extrusion des lettres')
print('=' * 72)
