# archive du DAT /project1/text1 (purge du 2026-11-02)
# morphogenesis_dna_td_builder_v02_FIXED.py
# TouchDesigner 2025.32460 / Python 3.11
#
# Correctif V02:
# - Ne dépend plus de globals()['baseCOMP'], globals()['geometryCOMP'], etc.
# - Crée les opérateurs via parent.create('typeString', name)
#
# Usage:
# 1) Crée un Text DAT dans /project1.
# 2) Colle ce script.
# 3) Run Script.
# 4) Ouvre /project1/MORPHOGENESIS_DNA_TD/render1

import math

PROJECT = op('/project1')
ROOT_NAME = 'MORPHOGENESIS_DNA_TD'
WORD = 'MORPHOGENESIS'

def destroy_if_exists(parent, name):
    o = parent.op(name)
    if o is not None:
        try:
            o.destroy()
        except Exception as e:
            print('Could not destroy', o.path, e)

def create_op(parent, type_names, name):
    """
    Robust TD creation.
    TD supports create(opType, name) where opType can be a type object
    OR a string such as 'waveCHOP' / 'baseCOMP'.
    In this build, globals()['baseCOMP'] is missing, so strings are safer.
    """
    destroy_if_exists(parent, name)
    errors = []
    for tn in type_names:
        try:
            return parent.create(tn, name)
        except Exception as e:
            errors.append('%s: %s' % (tn, repr(e)))
    raise Exception('Cannot create %s. Tried: %s' % (name, errors))

def set_par_safe(o, names, value):
    if o is None:
        return False
    for name in names:
        try:
            getattr(o.par, name).val = value
            return True
        except Exception:
            pass
    return False

def set_expr_safe(o, pname, expr):
    try:
        p = getattr(o.par, pname)
        p.expr = expr
        return True
    except Exception:
        return False

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

# ROOT
destroy_if_exists(PROJECT, ROOT_NAME)
root = create_op(PROJECT, ['baseCOMP'], ROOT_NAME)
root.nodeX = 200
root.nodeY = -100

# CUSTOM CONTROLS
try:
    page = root.appendCustomPage('DNA')
    defaults = [
        ('Radius', 2.15, 0.1, 6.0),
        ('Pitch', 0.48, 0.05, 1.5),
        ('Turns', 2.25, 0.25, 6.0),
        ('Speed', 0.18, -2.0, 2.0),
        ('Letterscale', 0.34, 0.02, 1.5),
        ('Depth', 0.10, 0.0, 0.8),
        ('Globalspin', 0.0, -360.0, 360.0),
    ]
    for name, default, nmin, nmax in defaults:
        pars = page.appendFloat(name, label=name)
        p = pars[0]
        p.default = default
        p.val = default
        p.normMin = nmin
        p.normMax = nmax
except Exception as e:
    print('Custom parameter creation warning:', e)

# MODULE DAT FOR EXPRESSIONS
module_dat = create_op(root, ['textDAT'], 'dna_math_module')
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
    letterscale = par_value('Letterscale', 0.34)
    globalspin = par_value('Globalspin', 0.0)

    t = 0.0 if n <= 1 else i / float(n - 1)
    phase = absTime.seconds * speed * math.tau
    strand_offset = (i % 2) * math.pi
    angle = t * math.tau * turns + phase + strand_offset + math.radians(globalspin)

    x = math.cos(angle) * radius
    y = (i - (n - 1) * 0.5) * pitch
    z = math.sin(angle) * radius

    ry = -math.degrees(angle) + 90.0
    rz = math.sin(angle * 1.37 + phase) * 16.0
    pulse = 1.0 + 0.12 * math.sin(phase * 2.0 + i * 0.71)
    sc = letterscale * pulse

    if field == 'tx': return x
    if field == 'ty': return y
    if field == 'tz': return z
    if field == 'rx': return 0.0
    if field == 'ry': return ry
    if field == 'rz': return rz
    if field == 'sx': return sc
    if field == 'sy': return sc
    if field == 'sz': return sc
    return 0.0
"""

# MATERIALS
mat_a = create_op(root, ['phongMAT'], 'mat_letter_blue')
set_par_safe(mat_a, ['diffuser'], 0.45)
set_par_safe(mat_a, ['diffuseg'], 0.68)
set_par_safe(mat_a, ['diffuseb'], 1.00)
set_par_safe(mat_a, ['ambientr'], 0.10)
set_par_safe(mat_a, ['ambientg'], 0.14)
set_par_safe(mat_a, ['ambientb'], 0.28)
set_par_safe(mat_a, ['shininess'], 0.8)

mat_b = create_op(root, ['phongMAT'], 'mat_letter_violet')
set_par_safe(mat_b, ['diffuser'], 0.95)
set_par_safe(mat_b, ['diffuseg'], 0.50)
set_par_safe(mat_b, ['diffuseb'], 1.00)
set_par_safe(mat_b, ['ambientr'], 0.22)
set_par_safe(mat_b, ['ambientg'], 0.10)
set_par_safe(mat_b, ['ambientb'], 0.30)
set_par_safe(mat_b, ['shininess'], 0.8)

# LETTER GEOMETRIES
geo_paths = []
for i, ch in enumerate(WORD):
    geo = create_op(root, ['geometryCOMP', 'geoCOMP'], 'letter_%02d_%s' % (i, ch))
    geo.nodeX = 40 + (i % 4) * 190
    geo.nodeY = -170 - (i // 4) * 120
    clear_children(geo)

    txt = create_op(geo, ['textSOP'], 'text_%02d_%s' % (i, ch))
    set_par_safe(txt, ['text', 'Text'], ch)
    set_par_safe(txt, ['font', 'Font'], 'Arial')
    set_par_safe(txt, ['bold', 'Bold'], True)
    set_par_safe(txt, ['align', 'halign', 'Halign'], 1)
    set_par_safe(txt, ['extrude', 'depth', 'Depth'], 0.10)
    set_flag_safe(txt, 'display', True)
    set_flag_safe(txt, 'render', True)

    for pname in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']:
        set_expr_safe(geo, pname, "op('dna_math_module').module.value(%d, '%s')" % (i, pname))

    set_par_safe(geo, ['material', 'mat'], './mat_letter_blue' if i % 2 == 0 else './mat_letter_violet')
    set_flag_safe(geo, 'display', True)
    set_flag_safe(geo, 'render', True)
    geo_paths.append('./' + geo.name)

# OPTIONAL CENTRAL AXIS
try:
    axis = create_op(root, ['geometryCOMP', 'geoCOMP'], 'center_axis_optional')
    axis.nodeX = 40
    axis.nodeY = -560
    clear_children(axis)
    cyl = create_op(axis, ['cylinderSOP'], 'axis_cylinder')
    set_par_safe(cyl, ['rad', 'radius', 'Radius'], 0.018)
    set_par_safe(cyl, ['height', 'Height'], len(WORD) * 0.48)
    set_flag_safe(cyl, 'display', True)
    set_flag_safe(cyl, 'render', True)
    set_par_safe(axis, ['material', 'mat'], './mat_letter_blue')
    set_flag_safe(axis, 'display', True)
    set_flag_safe(axis, 'render', True)
    geo_paths.append('./' + axis.name)
except Exception as e:
    print('Optional central axis skipped:', e)

# CAMERA + LIGHTS + RENDER
cam = create_op(root, ['cameraCOMP'], 'cam1')
cam.nodeX = 900
cam.nodeY = -170
set_par_safe(cam, ['tx'], 0)
set_par_safe(cam, ['ty'], 0)
set_par_safe(cam, ['tz'], 10.5)
set_par_safe(cam, ['rx'], 0)
set_par_safe(cam, ['ry'], 0)
set_par_safe(cam, ['rz'], 0)
set_par_safe(cam, ['lookat'], './letter_05_O')

light_key = create_op(root, ['lightCOMP'], 'light_key')
light_key.nodeX = 900
light_key.nodeY = -280
set_par_safe(light_key, ['tx'], 2.5)
set_par_safe(light_key, ['ty'], 3.0)
set_par_safe(light_key, ['tz'], 5.0)
set_par_safe(light_key, ['lightcolorr'], 1.0)
set_par_safe(light_key, ['lightcolorg'], 1.0)
set_par_safe(light_key, ['lightcolorb'], 1.0)

light_fill = create_op(root, ['lightCOMP'], 'light_fill')
light_fill.nodeX = 900
light_fill.nodeY = -390
set_par_safe(light_fill, ['tx'], -3.5)
set_par_safe(light_fill, ['ty'], -1.0)
set_par_safe(light_fill, ['tz'], 3.0)
set_par_safe(light_fill, ['lightcolorr'], 0.35)
set_par_safe(light_fill, ['lightcolorg'], 0.45)
set_par_safe(light_fill, ['lightcolorb'], 1.0)

render = create_op(root, ['renderTOP'], 'render1')
render.nodeX = 1120
render.nodeY = -170
set_par_safe(render, ['camera', 'cameras'], './cam1')
set_par_safe(render, ['geometry', 'geo', 'geometries'], ' '.join(geo_paths))
set_par_safe(render, ['lights', 'light'], './light_key ./light_fill')
set_par_safe(render, ['resx', 'w'], 1280)
set_par_safe(render, ['resy', 'h'], 720)
set_par_safe(render, ['bgcolorr'], 0.015)
set_par_safe(render, ['bgcolorg'], 0.015)
set_par_safe(render, ['bgcolorb'], 0.025)
set_par_safe(render, ['bgcolora'], 1.0)
set_flag_safe(render, 'viewer', True)

try:
    root.layout(root.children)
except Exception:
    pass

print('=' * 72)
print('MORPHOGENESIS DNA TD V02 FIXED created at:', root.path)
print('Open:', root.path + '/render1')
print('Controls:', root.path, '> custom page DNA')
print('Created geometries:', len(geo_paths))
print('=' * 72)
