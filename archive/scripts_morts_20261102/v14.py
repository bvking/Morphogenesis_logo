# archive du DAT /project1/v14 (purge du 2026-11-02)
# morphogenesis_dna_td_v14_CPU_LITE_FAST.py
# TouchDesigner 2025.32460 / Python 3.11
#
# À lancer après V13D clean / rollback CPU.
#
# Problème visé:
# - même à Renderresx 320 / Renderresy 180, le patch reste à ~4 fps.
# - cela indique que le Render TOP n'est probablement pas le goulot principal.
# - le coût principal vient plutôt des Script SOP Python qui déforment les points,
#   surtout si les lettres passent par Extrude SOP + Facet SOP.
#
# V14 = mode CPU LITE:
# - supprime le rendu des lettres extrudées lourdes;
# - reconnecte chaque bend_letter_v09 directement à un Text SOP très simplifié;
# - réduit fortement le Level Of Detail du texte;
# - garde la déformation sur le tube, mais avec beaucoup moins de points;
# - cache le tube surface, garde seulement le tube wire léger;
# - baisse le nombre de lignes du tube wire;
# - règle Curvecookrate sur 2 par défaut, modifiable;
# - crée un debug de nombre de points pour identifier le coût.
#
# Résultat attendu:
# - animation beaucoup plus fluide;
# - lettres moins 3D qu'en V12D, mais toujours courbées autour du tube;
# - base saine avant de retenter une version GPU propre sur une seule lettre.
#
# Usage:
# 1) Colle ce script dans un Text DAT.
# 2) Run Script.
# 3) Ouvre /project1/MORPHOGENESIS_DNA_TD/OUT_RENDER_VIEW_THIS

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

def set_val(o, names, value, verbose=True):
    if o is None:
        return False
    for name in names:
        p = get_par(o, name)
        if p is not None:
            try:
                p.val = value
                if verbose:
                    print('SET', o.path + '.par.' + p.name, '=', value)
                return True
            except Exception:
                pass
    if verbose:
        print('WARNING could not set', o.path if o else None, names, value)
    return False

def set_expr(o, pname, expr, verbose=True):
    p = get_par(o, pname)
    if p is None:
        if verbose:
            print('WARNING missing parameter', o.path if o else None, pname)
        return False
    try:
        p.expr = expr
        if verbose:
            print('EXPR', o.path + '.par.' + p.name, '=', expr)
        return True
    except Exception as e:
        if verbose:
            print('WARNING expr failed', o.path if o else None, pname, e)
        return False

def set_expr_by_names(o, names, expr, keywords=None, verbose=True):
    if o is None:
        return None

    for name in names:
        p = get_par(o, name)
        if p is not None:
            try:
                p.expr = expr
                if verbose:
                    print('EXPR', o.path + '.par.' + p.name, '=', expr)
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
                    p.expr = expr
                    if verbose:
                        print('EXPR fallback', o.path + '.par.' + p.name, '=', expr)
                    return p
                except Exception:
                    pass

    if verbose:
        print('WARNING could not set expression on', o.path if o else None, names, expr)
    return None

def ensure_float(par_name, label, default, norm_min=None, norm_max=None, page_name='DNA V14 LITE'):
    p = get_par(root, par_name)
    if p is not None:
        return p
    try:
        page = root.appendCustomPage(page_name)
    except Exception:
        try:
            page = root.appendCustomPage(page_name + ' B')
        except Exception:
            return None
    try:
        p = page.appendFloat(par_name, label=label)[0]
        p.default = default
        p.val = default
        if norm_min is not None:
            p.normMin = norm_min
        if norm_max is not None:
            p.normMax = norm_max
        print('ADDED PARAM', par_name, '=', default)
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
        except Exception as e:
            print('try create failed', tn, e)
    return None

def set_flag(o, flag, value):
    try:
        setattr(o, flag, value)
        return True
    except Exception:
        return False

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

def expr_par(name):
    return "op('%s').par.%s" % (ROOT_PATH, name)

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
# 1) Paramètres V14
# -------------------------------------------------------------------------
params = [
    ('V14liteactive', 'V14 lite active', 1.0, 0.0, 1.0),
    ('V14textlod', 'V14 text LOD', 0.08, 0.0, 1.0),
    ('V14useextrude', 'V14 use extrusion', 0.0, 0.0, 1.0),
    ('V14cookrate', 'V14 cook rate', 2.0, 1.0, 12.0),
    ('V14hideSurfaceTube', 'V14 hide surface tube', 1.0, 0.0, 1.0),
    ('V14wireRows', 'V14 wire rows', 3.0, 2.0, 24.0),
    ('V14wireCols', 'V14 wire cols', 18.0, 8.0, 96.0),
    ('V14renderX', 'V14 render X', 320.0, 160.0, 1920.0),
    ('V14renderY', 'V14 render Y', 180.0, 90.0, 1080.0),
    ('V14lettersize', 'V14 letter size multiplier', 1.0, 0.1, 4.0),
]
for p in params:
    ensure_float(*p)

# Force lightweight values now.
for pname, val in [
    ('V14liteactive', 1.0),
    ('V14textlod', 0.08),
    ('V14useextrude', 0.0),
    ('V14cookrate', 2.0),
    ('V14hideSurfaceTube', 1.0),
    ('V14wireRows', 3.0),
    ('V14wireCols', 18.0),
    ('V14renderX', 320.0),
    ('V14renderY', 180.0),
]:
    p = get_par(root, pname)
    if p is not None:
        try:
            p.val = val
        except Exception:
            pass

# Map old performance params to V14 controls.
ensure_float('Curvecookactive', 'Curve cook active', 1.0, 0.0, 1.0)
ensure_float('Curvecookrate', 'Curve cook rate', 2.0, 1.0, 12.0)
ensure_float('Renderresx', 'Render res X', 320.0, 160.0, 1920.0)
ensure_float('Renderresy', 'Render res Y', 180.0, 90.0, 1080.0)
ensure_float('Extrude3dtextlod', 'Text LOD', 0.08, 0.0, 1.0)

try: root.par.Curvecookactive.val = 1.0
except Exception: pass
try: root.par.Curvecookrate.expr = expr_par('V14cookrate')
except Exception: pass
try: root.par.Renderresx.expr = expr_par('V14renderX')
except Exception: pass
try: root.par.Renderresy.expr = expr_par('V14renderY')
except Exception: pass
try: root.par.Extrude3dtextlod.expr = expr_par('V14textlod')
except Exception: pass

# Slightly reduce geometric deformation cost.
for pname, val in [
    ('Extrude3ddepth', 0.0),
    ('Letterthickness', 0.0),
    ('Curveextrudegain', 0.0),
]:
    p = get_par(root, pname)
    if p is not None:
        try:
            p.val = val
        except Exception:
            pass

# -------------------------------------------------------------------------
# 2) CPU Script SOP callbacks
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
            scriptOp.addWarning('V14 lite deform failed: ' + repr(e))
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
        p = get_par(script_sop, pname)
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
        print('WARNING could not assign callbacks to', script_sop.path)
    return ok

# -------------------------------------------------------------------------
# 3) Reconnect each letter to ultra-light text-only deformation
# -------------------------------------------------------------------------
force_expr = "int(absTime.frame / max(1, int(op('%s').par.V14cookrate.eval()))) if op('%s').par.Curvecookactive.eval() > 0.5 else 0" % (ROOT_PATH, ROOT_PATH)

letter_paths = []
report = []

for i, ch in enumerate(WORD):
    geo = root.op('letter_%02d_%s' % (i, ch))
    if geo is None:
        print('WARNING missing letter geo', i, ch)
        continue

    # Identity transform
    for pname, val in [('tx',0),('ty',0),('tz',0),('rx',0),('ry',0),('rz',0),('sx',1),('sy',1),('sz',1)]:
        set_val(geo, [pname], val, verbose=False)

    set_flag(geo, 'display', True)
    set_flag(geo, 'render', True)

    # material classic
    mat_a = root.op('mat_letter_blue')
    mat_b = root.op('mat_letter_violet')
    if i % 2 == 0 and mat_a is not None:
        set_val(geo, ['material', 'mat'], mat_a.path, verbose=False)
    elif mat_b is not None:
        set_val(geo, ['material', 'mat'], mat_b.path, verbose=False)

    text_sop = None
    for c in geo.children:
        if c.family == 'SOP' and c.name.startswith('text_'):
            text_sop = c
            break

    if text_sop is None:
        print('WARNING no text SOP for', geo.path)
        continue

    # Very low LOD / simplest possible text.
    set_val(text_sop, ['text'], ch, verbose=False)
    set_expr_by_names(text_sop, ['levelofdetail'], expr_par('V14textlod'), keywords=['lod', 'level of detail'], verbose=False)

    # Try lighter output modes. If invalid, TD just keeps previous value.
    # For speed, prefer open polygons/outline over extruded closed meshes.
    set_val(text_sop, ['output'], 'polygons', verbose=False)
    set_val(text_sop, ['align', 'halign', 'Halign'], 1, verbose=False)

    deform = geo.op('bend_letter_v09')
    if deform is None:
        deform = create_or_get(geo, ['scriptSOP'], 'bend_letter_v09')

    if deform is None:
        print('WARNING no deform SOP for', geo.path)
        continue

    # Connect direct Text -> Script, bypassing Extrude/Facet.
    connect(text_sop, deform, 0)

    cb = geo.op('bend_letter_v09_callbacks')
    if cb is None:
        cb = geo.create('textDAT', 'bend_letter_v09_callbacks')
    cb.text = callback_template.replace('__LETTER_INDEX__', str(i))
    assign_callbacks(deform, cb)

    try:
        p = get_par(deform, 'Forcecook')
        if p is None:
            page = deform.appendCustomPage('V14')
            p = page.appendFloat('Forcecook', label='Force cook frame')[0]
        p.expr = force_expr
    except Exception as e:
        print('WARNING Forcecook failed on', deform.path, e)

    # Display only the Script SOP output.
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
# 4) Tube: keep only light wire tube
# -------------------------------------------------------------------------
tube_paths = []

surface = root.op('helix_tube_surface_v06')
if surface is not None:
    if get_par(root, 'V14hideSurfaceTube') is not None and root.par.V14hideSurfaceTube.eval() > 0.5:
        set_flag(surface, 'display', False)
        set_flag(surface, 'render', False)
    else:
        set_flag(surface, 'display', True)
        set_flag(surface, 'render', True)
        tube_paths.append(surface.path)

wire = root.op('helix_tube_wire_v06')
if wire is not None:
    set_flag(wire, 'display', True)
    set_flag(wire, 'render', True)

    set_expr(wire, 'tx', expr_par('Viewtx'), verbose=False)
    set_expr(wire, 'ty', expr_par('Viewty'), verbose=False)
    set_expr(wire, 'tz', expr_par('Viewtz'), verbose=False)
    set_expr(wire, 'rx', expr_par('Viewrotx'), verbose=False)
    set_expr(wire, 'ry', expr_par('Viewroty'), verbose=False)
    set_expr(wire, 'rz', expr_par('Viewrotz'), verbose=False)
    set_expr(wire, 'sx', expr_par('Viewscale'), verbose=False)
    set_expr(wire, 'sy', expr_par('Viewscale'), verbose=False)
    set_expr(wire, 'sz', expr_par('Viewscale'), verbose=False)

    for c in wire.children:
        if c.family == 'SOP':
            set_expr_by_names(c, ['rows'], "int(" + expr_par('V14wireRows') + ")", keywords=['rows'], verbose=False)
            set_expr_by_names(c, ['cols'], "int(" + expr_par('V14wireCols') + ")", keywords=['cols', 'columns'], verbose=False)
            set_flag(c, 'display', True)
            set_flag(c, 'render', True)

    tube_paths.append(wire.path)

# -------------------------------------------------------------------------
# 5) Render TOP
# -------------------------------------------------------------------------
render = root.op('render1')
if render is None:
    render = create_or_get(root, ['renderTOP'], 'render1')

cam = root.op('cam1')
if cam is not None:
    set_val(cam, ['lookat'], '', verbose=False)
    set_val(cam, ['tx'], 0, verbose=False)
    set_val(cam, ['ty'], 0, verbose=False)
    set_expr(cam, 'tz', expr_par('Cameradistance'), verbose=False)
    set_val(cam, ['rx'], 0, verbose=False)
    set_val(cam, ['ry'], 0, verbose=False)
    set_val(cam, ['rz'], 0, verbose=False)

light_paths = []
for lname in ['light_key', 'light_fill', 'light_rim_v12']:
    l = root.op(lname)
    if l is not None:
        light_paths.append(l.path)

if render is not None:
    if cam is not None:
        set_val(render, ['camera', 'cameras'], cam.path, verbose=False)
    set_val(render, ['geometry', 'geo', 'geometries'], ' '.join(letter_paths + tube_paths))
    if light_paths:
        set_val(render, ['lights', 'light'], ' '.join(light_paths), verbose=False)
    set_expr_by_names(render, ['resx', 'w'], "int(" + expr_par('V14renderX') + ")", keywords=['width','resolution x'], verbose=False)
    set_expr_by_names(render, ['resy', 'h'], "int(" + expr_par('V14renderY') + ")", keywords=['height','resolution y'], verbose=False)
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
# 6) Debug point count
# -------------------------------------------------------------------------
debug = root.op('debug_v14_cpu_lite_fast')
if debug is None:
    debug = create_or_get(root, ['tableDAT'], 'debug_v14_cpu_lite_fast')

if debug is not None:
    try:
        debug.clear()
        debug.appendRow(['key', 'value'])
        debug.appendRow(['mode', 'CPU LITE text-only Script SOP deformation'])
        debug.appendRow(['V14textlod', root.par.V14textlod.eval() if get_par(root, 'V14textlod') else 'missing'])
        debug.appendRow(['V14cookrate', root.par.V14cookrate.eval() if get_par(root, 'V14cookrate') else 'missing'])
        debug.appendRow(['V14render', str(root.par.V14renderX.eval() if get_par(root, 'V14renderX') else '?') + ' x ' + str(root.par.V14renderY.eval() if get_par(root, 'V14renderY') else '?')])
        debug.appendRow(['surface_tube_render', surface.render if surface is not None else 'missing'])
        debug.appendRow(['wire_tube_render', wire.render if wire is not None else 'missing'])
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
print('V14 CPU LITE FAST DONE')
print('Open:', ROOT_PATH + '/OUT_RENDER_VIEW_THIS')
print('Debug:', ROOT_PATH + '/debug_v14_cpu_lite_fast')
print('If still slow:')
print('  V14cookrate = 3 or 4')
print('  V14textlod = 0.03')
print('  V14wireRows = 2')
print('  V14wireCols = 12')
print('If animation is too choppy:')
print('  V14cookrate = 1')
print('=' * 72)

