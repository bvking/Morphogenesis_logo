# archive du DAT /project1/light (purge du 2026-11-02)
# morphogenesis_dna_td_v15c_VISIBILITY_REPAIR.py
# TouchDesigner 2025.32460 / Python 3.11
#
# À lancer après V15/V15B si render1 est noir ou si rien n’apparaît.
#
# Objectif:
# - rendre les lettres à nouveau visibles;
# - désactiver le normal/bump mapping qui déclenche l’avertissement:
#   "MAT is Normal Mapping, but SOP does not have tangent attributes"
# - revenir à un matériau organique simple, opaque, lumineux, sans normal map;
# - garder la déformation V14/V15 CPU Lite;
# - reconnecter render1 aux lettres + tube wire;
# - forcer les SOP de lettres à utiliser bend_letter_v09 comme sortie visible.
#
# Important:
# Le warning de normal mapping n’est pas l’erreur principale, mais il peut rendre
# le rendu instable/invisible selon les paramètres de matériau. Ici on retire
# la normal/bump map pour repartir sur une base visible.

ROOT_PATH = '/project1/MORPHOGENESIS_DNA_TD'
WORD = 'MORPHOGENESIS'

root = op(ROOT_PATH)
if root is None:
    raise Exception('Container introuvable: ' + ROOT_PATH)

def find_par(o, wanted):
    if o is None:
        return None
    try:
        p = getattr(o.par, wanted)
        if p is not None:
            return p
    except Exception:
        pass
    lw = wanted.lower()
    try:
        for p in o.pars():
            if p.name.lower() == lw:
                return p
    except Exception:
        pass
    return None

def par_expr(name, default_literal=None):
    p = find_par(root, name)
    if p is None:
        return str(default_literal) if default_literal is not None else '0'
    return "op('%s').par.%s" % (ROOT_PATH, p.name)

def set_val(o, names, value, keywords=None, verbose=True):
    if o is None:
        return None
    for name in names:
        p = find_par(o, name)
        if p is not None:
            try:
                p.val = value
                if verbose:
                    print('SET', o.path + '.par.' + p.name, '=', value)
                return p
            except Exception:
                pass

    if keywords:
        kws = [k.lower() for k in keywords]
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
                    p.val = value
                    if verbose:
                        print('SET fallback', o.path + '.par.' + p.name, '=', value)
                    return p
                except Exception:
                    pass

    if verbose:
        print('WARNING could not set', o.path if o else None, names, value)
    return None

def set_expr(o, names, expr, keywords=None, verbose=True):
    if o is None:
        return None
    for name in names:
        p = find_par(o, name)
        if p is not None:
            try:
                p.expr = expr
                if verbose:
                    print('EXPR', o.path + '.par.' + p.name, '=', expr)
                return p
            except Exception as e:
                if verbose:
                    print('WARNING expr failed', o.path, p.name, e)

    if keywords:
        kws = [k.lower() for k in keywords]
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
                    if verbose:
                        print('EXPR fallback', o.path + '.par.' + p.name, '=', expr)
                    return p
                except Exception:
                    pass

    if verbose:
        print('WARNING could not set expr', o.path if o else None, names, expr)
    return None

def ensure_float(par_name, label, default, norm_min=None, norm_max=None, page_name='DNA V15C REPAIR'):
    p = find_par(root, par_name)
    if p is not None:
        return p
    try:
        page = root.appendCustomPage(page_name)
    except Exception:
        try:
            page = root.appendCustomPage(page_name + ' B')
        except Exception as e:
            print('WARNING cannot create page', page_name, e)
            return None
    try:
        p = page.appendFloat(par_name, label=label)[0]
        p.default = default
        p.val = default
        if norm_min is not None:
            p.normMin = norm_min
        if norm_max is not None:
            p.normMax = norm_max
        print('ADDED PARAM', par_name, '=', default, 'actual:', p.name)
        return p
    except Exception as e:
        print('WARNING cannot add parameter', par_name, e)
        return None

def create_or_get(parent, type_names, name):
    existing = parent.op(name)
    if existing is not None:
        return existing
    for tn in type_names:
        try:
            o = parent.create(tn, name)
            print('CREATED', o.path)
            return o
        except Exception:
            pass
    return None

def connect(src, dst, index=0):
    if src is None or dst is None:
        return False
    try:
        dst.inputConnectors[index].connect(src)
        print('CONNECTED', src.path, '->', dst.path)
        return True
    except Exception as e:
        print('WARNING connect failed', src.path if src else None, '->', dst.path if dst else None, e)
        return False

def set_flag(o, flag, value):
    try:
        setattr(o, flag, value)
        return True
    except Exception:
        return False

def count_points(o):
    if o is None:
        return -1
    try:
        return int(o.numPoints)
    except Exception:
        try:
            return int(o.numPoints())
        except Exception:
            return -1

# -------------------------------------------------------------------------
# 1) Paramètres de sécurité visibles
# -------------------------------------------------------------------------
for args in [
    ('V15cvisibleactive', 'V15C visible active', 1.0, 0.0, 1.0),
    ('V15cbrightness', 'V15C brightness', 1.0, 0.0, 4.0),
    ('V15cemission', 'V15C emission', 0.18, 0.0, 2.0),
    ('V15cshininess', 'V15C shininess', 0.72, 0.0, 2.0),
    ('V15cspecular', 'V15C specular', 0.95, 0.0, 2.0),
    ('V15cusetexture', 'V15C use texture', 0.0, 0.0, 1.0),
    ('V14cookrate', 'V14 cook rate', 1.0, 1.0, 12.0),
    ('V14textlod', 'V14 text LOD', 0.08, 0.0, 1.0),
    ('Renderresx', 'Render res X', 640.0, 160.0, 1920.0),
    ('Renderresy', 'Render res Y', 360.0, 90.0, 1080.0),
]:
    ensure_float(*args)

# Force a visible/fairly light state.
for pname, val in [
    ('V15cvisibleactive', 1.0),
    ('V15cusetexture', 0.0),
    ('V14cookrate', 1.0),
    ('V14textlod', 0.08),
    ('Renderresx', 640.0),
    ('Renderresy', 360.0),
]:
    p = find_par(root, pname)
    if p is not None:
        try:
            p.val = val
        except Exception:
            pass

# -------------------------------------------------------------------------
# 2) Matériau visible sans normal/bump map
# -------------------------------------------------------------------------
mat = create_or_get(root, ['phongMAT'], 'mat_letters_visible_v15c')
if mat is None:
    raise Exception('Impossible de créer mat_letters_visible_v15c')

# Couleur claire, vivante, opaque
set_val(mat, ['diffuser'], 0.88, keywords=['diffuse r'], verbose=False)
set_val(mat, ['diffuseg'], 0.70, keywords=['diffuse g'], verbose=False)
set_val(mat, ['diffuseb'], 1.00, keywords=['diffuse b'], verbose=False)

set_expr(mat, ['ambientr'], '0.88 * 0.28 * ' + par_expr('V15cbrightness', '1'), keywords=['ambient r'], verbose=False)
set_expr(mat, ['ambientg'], '0.70 * 0.28 * ' + par_expr('V15cbrightness', '1'), keywords=['ambient g'], verbose=False)
set_expr(mat, ['ambientb'], '1.00 * 0.28 * ' + par_expr('V15cbrightness', '1'), keywords=['ambient b'], verbose=False)

set_expr(mat, ['emitr'], '0.88 * ' + par_expr('V15cemission', '0.18'), keywords=['emit r', 'emission r'], verbose=False)
set_expr(mat, ['emitg'], '0.70 * ' + par_expr('V15cemission', '0.18'), keywords=['emit g', 'emission g'], verbose=False)
set_expr(mat, ['emitb'], '1.00 * ' + par_expr('V15cemission', '0.18'), keywords=['emit b', 'emission b'], verbose=False)

set_expr(mat, ['specularr'], par_expr('V15cspecular', '0.95'), keywords=['specular r'], verbose=False)
set_expr(mat, ['specularg'], par_expr('V15cspecular', '0.95'), keywords=['specular g'], verbose=False)
set_expr(mat, ['specularb'], par_expr('V15cspecular', '0.95'), keywords=['specular b'], verbose=False)
set_expr(mat, ['shininess'], par_expr('V15cshininess', '0.72'), keywords=['shininess'], verbose=False)

# Opacité/depth sûres
set_val(mat, ['alphafront'], 1.0, keywords=['alpha front', 'opacity', 'alpha'], verbose=False)
set_val(mat, ['alphaside'], 1.0, keywords=['alpha side'], verbose=False)
set_val(mat, ['blending'], False, keywords=['blend'], verbose=False)
set_val(mat, ['depthwriting'], True, keywords=['depth writing'], verbose=False)
set_val(mat, ['cullface'], 'neither', keywords=['cull'], verbose=False)

# Désactiver explicitement normal/bump map en vidant les slots si présents.
for slot in ['normalmap', 'bumpmap', 'normalmap1', 'bumpmap1', 'normalmaptop', 'bumpmaptop']:
    p = find_par(mat, slot)
    if p is not None:
        try:
            p.val = ''
            print('CLEARED', mat.path + '.par.' + p.name)
        except Exception:
            pass

# Color map désactivée pour récupérer la visibilité.
# On pourra la réactiver après, mais pas tant que le rendu est invisible.
for slot in ['colormap', 'colormap1', 'colormaptop']:
    p = find_par(mat, slot)
    if p is not None:
        try:
            p.val = ''
            print('CLEARED', mat.path + '.par.' + p.name)
        except Exception:
            pass

# -------------------------------------------------------------------------
# 3) Callback robuste pour bend_letter_v09
# -------------------------------------------------------------------------
callback_template = r"""
ROOT_PATH = '/project1/MORPHOGENESIS_DNA_TD'
LETTER_INDEX = __LETTER_INDEX__

def _cook_impl(scriptOp):
    if len(scriptOp.inputs) < 1 or scriptOp.inputs[0] is None:
        scriptOp.clear()
        return

    scriptOp.copy(scriptOp.inputs[0])

    try:
        op(ROOT_PATH + '/dna_v09_geom_module').module.deform_script_sop(scriptOp, LETTER_INDEX)
    except Exception as e:
        try:
            scriptOp.addWarning('V15C visible deform failed: ' + repr(e))
        except Exception:
            pass

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
    try:
        return CookLevel.WHEN_USED
    except Exception:
        return
"""

def assign_callbacks(script_sop, callback_dat):
    ok = False
    for pname in ['callbacks', 'callbacksdat', 'callbackdat', 'dat', 'script']:
        p = find_par(script_sop, pname)
        if p is not None:
            try:
                p.val = callback_dat.path
                ok = True
                break
            except Exception:
                pass
    try:
        for d in script_sop.docked:
            if d.family == 'DAT':
                d.text = callback_dat.text
                ok = True
    except Exception:
        pass
    if not ok:
        print('WARNING could not assign callback to', script_sop.path)
    return ok

force_expr = "int(absTime.frame / max(1, int(" + par_expr('V14cookrate', '1') + "))) if " + par_expr('Curvecookactive', '1') + " > 0.5 else 0"

# -------------------------------------------------------------------------
# 4) Réparer chaque lettre: Text SOP direct -> bend_letter_v09, matériau visible
# -------------------------------------------------------------------------
letter_paths = []
report = []

for i, ch in enumerate(WORD):
    geo = root.op('letter_%02d_%s' % (i, ch))
    if geo is None:
        print('WARNING missing letter geo', i, ch)
        continue

    # Geometry COMP identité
    for pname, val in [('tx',0),('ty',0),('tz',0),('rx',0),('ry',0),('rz',0),('sx',1),('sy',1),('sz',1)]:
        set_val(geo, [pname], val, verbose=False)

    set_flag(geo, 'display', True)
    set_flag(geo, 'render', True)
    set_val(geo, ['material', 'mat'], mat.path, verbose=False)

    text_sop = None
    for c in geo.children:
        if c.family == 'SOP' and c.name.startswith('text_'):
            text_sop = c
            break

    if text_sop is None:
        print('WARNING no text SOP for', geo.path)
        continue

    set_val(text_sop, ['text'], ch, verbose=False)
    set_expr(text_sop, ['levelofdetail'], par_expr('V14textlod', '0.08'), keywords=['lod', 'level of detail'], verbose=False)
    set_val(text_sop, ['output'], 'polygons', keywords=['output'], verbose=False)

    deform = geo.op('bend_letter_v09')
    if deform is None:
        deform = create_or_get(geo, ['scriptSOP'], 'bend_letter_v09')

    if deform is None:
        print('WARNING no deform SOP for', geo.path)
        continue

    connect(text_sop, deform, 0)

    cb = geo.op('bend_letter_v09_callbacks')
    if cb is None:
        cb = geo.create('textDAT', 'bend_letter_v09_callbacks')
    cb.text = callback_template.replace('__LETTER_INDEX__', str(i))
    assign_callbacks(deform, cb)

    p = find_par(deform, 'Forcecook')
    if p is None:
        page = deform.appendCustomPage('V15C')
        p = page.appendFloat('Forcecook', label='Force cook frame')[0]
    try:
        p.expr = force_expr
    except Exception as e:
        print('WARNING cannot set Forcecook on', deform.path, e)

    # Afficher seulement bend_letter_v09 pour être sûr.
    for c in geo.children:
        if c.family == 'SOP':
            set_flag(c, 'display', False)
            set_flag(c, 'render', False)

    set_flag(deform, 'display', True)
    set_flag(deform, 'render', True)

    try:
        text_sop.cook(force=True)
        deform.cook(force=True)
    except Exception:
        pass

    letter_paths.append(geo.path)
    report.append([ch, count_points(text_sop), count_points(deform), deform.path])

# -------------------------------------------------------------------------
# 5) Tube wire léger, surface cachée
# -------------------------------------------------------------------------
tube_paths = []

surface = root.op('helix_tube_surface_v06')
if surface is not None:
    set_flag(surface, 'display', False)
    set_flag(surface, 'render', False)

wire = root.op('helix_tube_wire_v06')
if wire is not None:
    set_flag(wire, 'display', True)
    set_flag(wire, 'render', True)

    set_expr(wire, ['tx'], par_expr('Viewtx', '0'), verbose=False)
    set_expr(wire, ['ty'], par_expr('Viewty', '0'), verbose=False)
    set_expr(wire, ['tz'], par_expr('Viewtz', '-3.97'), verbose=False)
    set_expr(wire, ['rx'], par_expr('Viewrotx', '0'), verbose=False)
    set_expr(wire, ['ry'], par_expr('Viewroty', '0'), verbose=False)
    set_expr(wire, ['rz'], par_expr('Viewrotz', '0'), verbose=False)
    set_expr(wire, ['sx'], par_expr('Viewscale', '0.1'), verbose=False)
    set_expr(wire, ['sy'], par_expr('Viewscale', '0.1'), verbose=False)
    set_expr(wire, ['sz'], par_expr('Viewscale', '0.1'), verbose=False)

    # Corriger d'éventuelles expressions cassées avec V14wireRows/V14wireCols.
    for c in wire.children:
        if c.family == 'SOP':
            set_val(c, ['rows'], 3, keywords=['rows'], verbose=False)
            set_val(c, ['cols'], 18, keywords=['cols', 'columns'], verbose=False)
            set_flag(c, 'display', True)
            set_flag(c, 'render', True)
    tube_paths.append(wire.path)

# -------------------------------------------------------------------------
# 6) Lumières sûres, sans expressions risquées
# -------------------------------------------------------------------------
def setup_light(name, x, y, z, r, g, b, dim):
    l = root.op(name)
    if l is None:
        l = create_or_get(root, ['lightCOMP'], name)
    if l is None:
        return None
    set_val(l, ['tx'], x, verbose=False)
    set_val(l, ['ty'], y, verbose=False)
    set_val(l, ['tz'], z, verbose=False)
    set_val(l, ['lightcolorr'], r, verbose=False)
    set_val(l, ['lightcolorg'], g, verbose=False)
    set_val(l, ['lightcolorb'], b, verbose=False)
    set_val(l, ['dimmer'], dim, keywords=['dimmer', 'intensity'], verbose=False)
    return l

key = setup_light('light_key', 2.8, 3.4, 5.2, 1.0, 0.90, 0.82, 1.20)
fill = setup_light('light_fill', -3.8, -1.8, 4.2, 0.35, 0.55, 1.0, 0.55)
rim = setup_light('light_rim_v15', -3.6, 2.6, -3.2, 0.55, 0.75, 1.0, 1.80)
spark = setup_light('light_sparkle_v15', 1.6, 0.9, 3.4, 1.0, 0.78, 1.0, 0.0)

light_paths = [l.path for l in [key, fill, rim, spark] if l is not None]

# -------------------------------------------------------------------------
# 7) Render TOP reconnecté
# -------------------------------------------------------------------------
render = root.op('render1')
if render is None:
    render = create_or_get(root, ['renderTOP'], 'render1')

cam = root.op('cam1')
if cam is not None:
    set_val(cam, ['lookat'], '', verbose=False)
    set_val(cam, ['tx'], 0, verbose=False)
    set_val(cam, ['ty'], 0, verbose=False)
    set_expr(cam, ['tz'], par_expr('Cameradistance', '7.2'), verbose=False)
    set_val(cam, ['rx'], 0, verbose=False)
    set_val(cam, ['ry'], 0, verbose=False)
    set_val(cam, ['rz'], 0, verbose=False)

if render is not None:
    if cam is not None:
        set_val(render, ['camera', 'cameras'], cam.path, verbose=False)
    set_val(render, ['geometry', 'geo', 'geometries'], ' '.join(letter_paths + tube_paths))
    set_val(render, ['lights', 'light'], ' '.join(light_paths), verbose=False)

    set_expr(render, ['resx', 'w'], "int(" + par_expr('Renderresx', '640') + ")", keywords=['width', 'resolution x'], verbose=False)
    set_expr(render, ['resy', 'h'], "int(" + par_expr('Renderresy', '360') + ")", keywords=['height', 'resolution y'], verbose=False)

    set_val(render, ['bgcolorr'], 0.01, verbose=False)
    set_val(render, ['bgcolorg'], 0.012, verbose=False)
    set_val(render, ['bgcolorb'], 0.022, verbose=False)
    set_val(render, ['bgcolora'], 1.0, verbose=False)

    try:
        render.cook(force=True)
    except Exception:
        pass

out_top = root.op('OUT_RENDER_VIEW_THIS')
if out_top is None:
    out_top = create_or_get(root, ['nullTOP'], 'OUT_RENDER_VIEW_THIS')
if out_top is not None and render is not None:
    try:
        out_top.inputConnectors[0].connect(render)
    except Exception:
        pass
    set_flag(out_top, 'viewer', True)
    try:
        out_top.cook(force=True)
    except Exception:
        pass

# -------------------------------------------------------------------------
# 8) Debug
# -------------------------------------------------------------------------
debug = root.op('debug_v15c_visibility_repair')
if debug is None:
    debug = create_or_get(root, ['tableDAT'], 'debug_v15c_visibility_repair')

if debug is not None:
    try:
        debug.clear()
        debug.appendRow(['key', 'value'])
        debug.appendRow(['mode', 'V15C visibility repair'])
        debug.appendRow(['material', mat.path])
        debug.appendRow(['letters', len(letter_paths)])
        debug.appendRow(['tubes', len(tube_paths)])
        debug.appendRow(['lights', ' '.join(light_paths)])
        debug.appendRow(['render_geometry', ' '.join(letter_paths + tube_paths)])
        debug.appendRow(['normal_bump_mapping', 'disabled'])
        debug.appendRow(['sparkle_light', 'disabled dimmer 0 for safety'])
        debug.appendRow(['open', ROOT_PATH + '/OUT_RENDER_VIEW_THIS'])
        debug.appendRow([])
        debug.appendRow(['letter', 'text_points', 'deform_points', 'deform_path'])
        for row in report:
            debug.appendRow(row)
    except Exception as e:
        print('WARNING debug failed', e)

try:
    root.layout(root.children)
except Exception:
    pass

print('=' * 72)
print('MORPHOGENESIS DNA V15C VISIBILITY REPAIR OK')
print('Open:', ROOT_PATH + '/OUT_RENDER_VIEW_THIS')
print('Debug:', ROOT_PATH + '/debug_v15c_visibility_repair')
print('Material:', mat.path)
print('Normal/bump map disabled to remove tangent warning.')
print('If visible now, next step: V16 aesthetic organic texture without normal map.')
print('=' * 72)
