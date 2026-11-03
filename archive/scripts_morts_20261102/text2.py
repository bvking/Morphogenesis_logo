# archive du DAT /project1/text2 (purge du 2026-11-02)
# morphogenesis_dna_td_v04_HORIZONTAL_AXIS_ROLL.py
# TouchDesigner 2025.32460
#
# À lancer après la V03 réparée.
#
# Effet:
# - Transforme la double spirale MORPHOGENESIS pour que son axe principal soit horizontal.
# - Les deux brins tournent autour de cet axe horizontal X.
# - Ajoute deux contrôles:
#     Axisrollspeed : vitesse de rotation autour de l'axe horizontal
#     Axisrollangle : offset manuel de rotation
#
# Usage:
# 1) Colle ce script dans un Text DAT.
# 2) Run Script.
# 3) Ouvre /project1/MORPHOGENESIS_DNA_TD/render1
# 4) Va sur /project1/MORPHOGENESIS_DNA_TD > page "DNA V04"

import math

ROOT_PATH = '/project1/MORPHOGENESIS_DNA_TD'
WORD = 'MORPHOGENESIS'

root = op(ROOT_PATH)
if root is None:
    raise Exception('Container introuvable: ' + ROOT_PATH)

def set_par_safe(o, names, value):
    if o is None:
        return False
    for name in names:
        try:
            getattr(o.par, name).val = value
            print('SET', o.path + '.par.' + name, '=', value)
            return True
        except Exception:
            pass
    print('WARNING could not set', o.path if o else None, names, value)
    return False

def set_expr_safe(o, pname, expr):
    try:
        p = getattr(o.par, pname)
        p.expr = expr
        return True
    except Exception as e:
        print('WARNING expr failed:', o.path, pname, e)
        return False

def ensure_float_param(root, page, par_name, label, default, norm_min, norm_max):
    try:
        p = getattr(root.par, par_name)
        return p
    except Exception:
        pass

    pars = page.appendFloat(par_name, label=label)
    p = pars[0]
    p.default = default
    p.val = default
    p.normMin = norm_min
    p.normMax = norm_max
    print('ADDED PARAM', par_name, '=', default)
    return p

# Add V04 controls
try:
    page = root.appendCustomPage('DNA V04')
except Exception:
    # If page creation fails because it already exists, create a new safe page.
    try:
        page = root.appendCustomPage('DNA V04b')
    except Exception as e:
        raise Exception('Impossible de créer une page custom V04: ' + repr(e))

ensure_float_param(root, page, 'Axisrollspeed', 'Axis roll speed', 0.12, -2.0, 2.0)
ensure_float_param(root, page, 'Axisrollangle', 'Axis roll angle', 0.0, -360.0, 360.0)

# Replace the math module.
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

    # Speed = vitesse de progression des lettres dans la spirale.
    speed = par_value('Speed', 0.18)

    # V04:
    # Axisrollspeed = rotation globale autour de l'axe horizontal X.
    axis_roll_speed = par_value('Axisrollspeed', 0.12)
    axis_roll_angle = par_value('Axisrollangle', 0.0)

    letterscale = par_value('Letterscale', 0.34)
    globalspin = par_value('Globalspin', 0.0)

    t = 0.0 if n <= 1 else i / float(n - 1)

    # Phase interne de la spirale.
    phase = absTime.seconds * speed * math.tau

    # Deux brins opposés.
    strand_offset = (i % 2) * math.pi

    # Angle hélicoïdal local.
    angle = t * math.tau * turns + phase + strand_offset + math.radians(globalspin)

    # Axe principal horizontal:
    # x = longueur de la spirale
    # y/z = section circulaire autour de l'axe X
    x = (i - (n - 1) * 0.5) * pitch
    y0 = math.cos(angle) * radius
    z0 = math.sin(angle) * radius

    # Rotation globale autour de l'axe horizontal X.
    roll = absTime.seconds * axis_roll_speed * math.tau + math.radians(axis_roll_angle)

    cy = math.cos(roll)
    sy = math.sin(roll)

    y = y0 * cy - z0 * sy
    z = y0 * sy + z0 * cy

    # Orientation:
    # On garde la ligne de base des lettres dans l'axe X.
    # Puis on fait tourner chaque lettre autour de X pour qu'elle regarde vers l'extérieur.
    total_angle = angle + roll
    rx = math.degrees(total_angle) - 90.0

    # Petite torsion graphique, optionnelle, pour éviter un rendu trop mécanique.
    rz = math.sin(angle * 1.37 + phase) * 8.0

    pulse = 1.0 + 0.10 * math.sin(phase * 2.0 + i * 0.71)
    sc = letterscale * pulse

    if field == 'tx': return x
    if field == 'ty': return y
    if field == 'tz': return z
    if field == 'rx': return rx
    if field == 'ry': return 0.0
    if field == 'rz': return rz
    if field == 'sx': return sc
    if field == 'sy': return sc
    if field == 'sz': return sc

    return 0.0
"""

module_abs = module_dat.path

# Re-apply absolute expressions on letters
geo_paths = []
for i, ch in enumerate(WORD):
    geo = root.op('letter_%02d_%s' % (i, ch))
    if geo is None:
        print('WARNING missing:', 'letter_%02d_%s' % (i, ch))
        continue

    for pname in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']:
        set_expr_safe(geo, pname, "op('%s').module.value(%d, '%s')" % (module_abs, i, pname))

    try: geo.display = True
    except Exception: pass
    try: geo.render = True
    except Exception: pass

    for c in geo.children:
        if c.family == 'SOP':
            try: c.display = True
            except Exception: pass
            try: c.render = True
            except Exception: pass

    geo_paths.append(geo.path)

# Hide or rotate the previous optional vertical axis if present.
# It was only decorative, not needed for V04.
axis = root.op('center_axis_optional')
if axis is not None:
    try:
        axis.display = False
        axis.render = False
        print('center_axis_optional hidden for V04')
    except Exception:
        pass

# Stabilize camera: no moving lookat target, camera faces origin from +Z.
cam = root.op('cam1')
if cam is not None:
    set_par_safe(cam, ['lookat'], '')
    set_par_safe(cam, ['tx'], 0)
    set_par_safe(cam, ['ty'], 0)
    set_par_safe(cam, ['tz'], 10.5)
    set_par_safe(cam, ['rx'], 0)
    set_par_safe(cam, ['ry'], 0)
    set_par_safe(cam, ['rz'], 0)

# Ensure Render TOP has absolute references.
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
print('MORPHOGENESIS DNA V04 HORIZONTAL AXIS ROLL OK')
print('Axe principal: horizontal X')
print('Rotation globale autour de X: Axisrollspeed + Axisrollangle')
print('Open:', ROOT_PATH + '/render1')
print('Controls:', ROOT_PATH, '> page DNA V04')
print('=' * 72)
