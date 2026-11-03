# archive du DAT /project1/rollback (purge du 2026-11-02)
# morphogenesis_dna_td_v13c_ROLLBACK_TO_V12D_CPU_STABLE.py
# TouchDesigner 2025.32460 / Python 3.11
#
# À lancer si la V13 GPU/GLSL ne fonctionne pas.
#
# But:
# - revenir à une version saine CPU type V12D / V11;
# - désactiver visuellement le chemin GPU V13 sans le supprimer;
# - réactiver les Script SOP bend_letter_v09 et facet_normals_v12d;
# - réassigner les callbacks;
# - remettre les matériaux classiques mat_letter_blue / mat_letter_violet;
# - reconnecter render1 vers les lettres CPU + tube;
# - créer un OUT clair.
#
# À faire:
# 1) Colle ce script dans un Text DAT.
# 2) Run Script.
# 3) Ouvre /project1/MORPHOGENESIS_DNA_TD/OUT_RENDER_VIEW_THIS
#
# Ensuite sauvegarde ton .toe sous un nouveau nom:
# MORPHOGENESIS_DNA_CPU_STABLE_V12D.toe

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

def ensure_float(par_name, label, default, norm_min=None, norm_max=None, page_name='DNA ROLLBACK'):
    p = get_par(root, par_name)
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

def connect(src, dst, index=0):
    if src is None or dst is None:
        return False
    try:
        dst.inputConnectors[index].connect(src)
        print('CONNECTED', src.path, '->', dst.path)
        return True
    except Exception as e:
        print('WARNING connect failed:', src.path if src else None, '->', dst.path if dst else None, e)
        return False

def set_flag(o, flag, value):
    try:
        setattr(o, flag, value)
        return True
    except Exception:
        return False

def expr_par(name):
    return "op('%s').par.%s" % (ROOT_PATH, name)

# -------------------------------------------------------------------------
# 1) Paramètres essentiels pour retour CPU stable
# -------------------------------------------------------------------------
for pname, label, default, nmin, nmax in [
    ('Curvecookactive', 'Curve cook active', 1.0, 0.0, 1.0),
    ('Curvecookrate', 'Curve cook rate', 1.0, 1.0, 8.0),
    ('Viewscale', 'View scale', 0.1, 0.01, 4.0),
    ('Viewtx', 'View translate X', -0.16, -20.0, 20.0),
    ('Viewty', 'View translate Y', 0.0, -20.0, 20.0),
    ('Viewtz', 'View translate Z', -3.97, -20.0, 20.0),
    ('Cameradistance', 'Camera distance', 7.2, 1.0, 50.0),
    ('Letteralpha', 'Letter alpha', 1.0, 0.0, 1.0),
    ('Extrude3ddepth', 'Extrude 3D depth', 0.070, 0.0, 0.5),
    ('Letterthickness', 'Letter thickness', 0.070, 0.0, 1.5),
    ('Curveextrudegain', 'Curve extrusion gain', 1.25, 0.0, 5.0),
    ('V13gpuactive', 'V13 GPU active', 0.0, 0.0, 1.0),
]:
    ensure_float(pname, label, default, nmin, nmax)

# Force safe CPU values.
for pname, val in [
    ('Curvecookactive', 1.0),
    ('Curvecookrate', 1.0),
    ('V13gpuactive', 0.0),
    ('Letteralpha', 1.0),
]:
    p = get_par(root, pname)
    if p is not None:
        try:
            p.val = val
        except Exception:
            pass

# -------------------------------------------------------------------------
# 2) Callback CPU V09/V11 stable
# -------------------------------------------------------------------------
callback_template = r"""
ROOT_PATH = '/project1/MORPHOGENESIS_DNA_TD'
LETTER_INDEX = __LETTER_INDEX__

def _cook_impl(scriptOp):
    if len(scriptOp.inputs) < 1 or scriptOp.inputs[0] is None:
        scriptOp.clear()
        return

    in_sop = scriptOp.inputs[0]
    scriptOp.copy(in_sop)

    try:
        op(ROOT_PATH + '/dna_v09_geom_module').module.deform_script_sop(scriptOp, LETTER_INDEX)
    except Exception as e:
        try:
            scriptOp.addWarning('ROLLBACK CPU deform failed: ' + repr(e))
        except Exception:
            pass
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
                print('CALLBACK PARAM', script_sop.path, pname, callback_dat.path)
                ok = True
                break
            except Exception:
                pass
    try:
        for d in script_sop.docked:
            if d.family == 'DAT':
                d.text = callback_dat.text
                print('UPDATED DOCKED DAT', d.path)
                ok = True
    except Exception:
        pass
    if not ok:
        print('WARNING could not assign callbacks to', script_sop.path)
    return ok

# Check CPU geometry module.
geom_module = root.op('dna_v09_geom_module')
if geom_module is None:
    print('WARNING: dna_v09_geom_module absent. Il faut relancer V11 avant ce rollback.')
else:
    print('FOUND CPU geometry module:', geom_module.path)

# -------------------------------------------------------------------------
# 3) Restaurer les lettres CPU
# -------------------------------------------------------------------------
mat_a = root.op('mat_letter_blue')
mat_b = root.op('mat_letter_violet')
if mat_a is None:
    mat_a = create_or_get(root, ['phongMAT'], 'mat_letter_blue')
if mat_b is None:
    mat_b = create_or_get(root, ['phongMAT'], 'mat_letter_violet')

# Réglage simple des matériaux classiques
if mat_a is not None:
    set_val(mat_a, ['diffuser'], 0.38, verbose=False)
    set_val(mat_a, ['diffuseg'], 0.72, verbose=False)
    set_val(mat_a, ['diffuseb'], 1.0, verbose=False)
    set_val(mat_a, ['blending'], False, verbose=False)
    set_val(mat_a, ['depthwriting'], True, verbose=False)
    set_val(mat_a, ['cullface'], 'neither', verbose=False)

if mat_b is not None:
    set_val(mat_b, ['diffuser'], 1.0, verbose=False)
    set_val(mat_b, ['diffuseg'], 0.52, verbose=False)
    set_val(mat_b, ['diffuseb'], 0.95, verbose=False)
    set_val(mat_b, ['blending'], False, verbose=False)
    set_val(mat_b, ['depthwriting'], True, verbose=False)
    set_val(mat_b, ['cullface'], 'neither', verbose=False)

force_expr = "int(absTime.frame / max(1, int(op('%s').par.Curvecookrate.eval()))) if op('%s').par.Curvecookactive.eval() > 0.5 else 0" % (ROOT_PATH, ROOT_PATH)
letter_paths = []
report = []

for i, ch in enumerate(WORD):
    geo = root.op('letter_%02d_%s' % (i, ch))
    if geo is None:
        print('WARNING missing letter geo', i, ch)
        continue

    set_flag(geo, 'display', True)
    set_flag(geo, 'render', True)

    # Geometry identity because Script SOP outputs transformed points.
    for pname, val in [('tx',0),('ty',0),('tz',0),('rx',0),('ry',0),('rz',0),('sx',1),('sy',1),('sz',1)]:
        set_val(geo, [pname], val, verbose=False)

    # Assign classical material, not GLSL.
    set_val(geo, ['material', 'mat'], mat_a.path if (i % 2 == 0 and mat_a is not None) else (mat_b.path if mat_b is not None else ''))

    # Find CPU chain.
    text = None
    for c in geo.children:
        if c.family == 'SOP' and c.name.startswith('text_'):
            text = c
            break

    extrude = geo.op('extrude_letter_v12d')
    deform = geo.op('bend_letter_v09')
    facet = geo.op('facet_normals_v12d')

    # If V12D was not launched or parts are missing, create minimal missing operators.
    if deform is None:
        deform = create_or_get(geo, ['scriptSOP'], 'bend_letter_v09')
    if facet is None:
        facet = create_or_get(geo, ['facetSOP'], 'facet_normals_v12d')

    # Reconnect CPU source to deform.
    # Prefer v12d extrusion if present, else text SOP fallback.
    source = extrude if extrude is not None else text
    if source is not None and deform is not None:
        connect(source, deform, 0)

    # Reassign callback
    if deform is not None:
        cb = geo.op('bend_letter_v09_callbacks')
        if cb is None:
            cb = geo.create('textDAT', 'bend_letter_v09_callbacks')
        cb.text = callback_template.replace('__LETTER_INDEX__', str(i))
        assign_callbacks(deform, cb)

        try:
            p = get_par(deform, 'Forcecook')
            if p is None:
                page = deform.appendCustomPage('ROLLBACK')
                p = page.appendFloat('Forcecook', label='Force cook frame')[0]
            p.expr = force_expr
        except Exception as e:
            print('WARNING cannot set Forcecook', deform.path, e)

    final_sop = deform
    if deform is not None and facet is not None:
        connect(deform, facet, 0)
        set_val(facet, ['docusp'], True, verbose=False)
        set_val(facet, ['cuspangle'], 32, verbose=False)
        set_val(facet, ['postnml'], True, verbose=False)
        set_val(facet, ['normals'], True, verbose=False)
        final_sop = facet

    # Hide GPU final SOP and every other SOP, display CPU final.
    for c in geo.children:
        if c.family == 'SOP':
            set_flag(c, 'display', False)
            set_flag(c, 'render', False)

    if final_sop is not None:
        set_flag(final_sop, 'display', True)
        set_flag(final_sop, 'render', True)
        try:
            final_sop.cook(force=True)
        except Exception:
            pass

    # Old GPU GLSL mat remains in project but not used.
    gpu_out = geo.op('OUT_LETTER_GPU_V13')
    if gpu_out is not None:
        set_flag(gpu_out, 'display', False)
        set_flag(gpu_out, 'render', False)

    letter_paths.append(geo.path)
    report.append([ch, source.path if source else 'missing source', final_sop.path if final_sop else 'missing final'])

# -------------------------------------------------------------------------
# 4) Tube + render + OUT
# -------------------------------------------------------------------------
tube_paths = []
for name in ['helix_tube_surface_v06', 'helix_tube_wire_v06']:
    tg = root.op(name)
    if tg is None:
        continue
    set_flag(tg, 'display', True)
    set_flag(tg, 'render', True)

    set_expr(tg, 'tx', expr_par('Viewtx'), verbose=False)
    set_expr(tg, 'ty', expr_par('Viewty'), verbose=False)
    set_expr(tg, 'tz', expr_par('Viewtz'), verbose=False)
    set_expr(tg, 'rx', expr_par('Viewrotx'), verbose=False)
    set_expr(tg, 'ry', expr_par('Viewroty'), verbose=False)
    set_expr(tg, 'rz', expr_par('Viewrotz'), verbose=False)
    set_expr(tg, 'sx', expr_par('Viewscale'), verbose=False)
    set_expr(tg, 'sy', expr_par('Viewscale'), verbose=False)
    set_expr(tg, 'sz', expr_par('Viewscale'), verbose=False)

    tube_paths.append(tg.path)

cam = root.op('cam1')
if cam is None:
    cam = create_or_get(root, ['cameraCOMP'], 'cam1')
if cam is not None:
    set_val(cam, ['lookat'], '', verbose=False)
    set_val(cam, ['tx'], 0, verbose=False)
    set_val(cam, ['ty'], 0, verbose=False)
    set_expr(cam, 'tz', expr_par('Cameradistance'), verbose=False)
    set_val(cam, ['rx'], 0, verbose=False)
    set_val(cam, ['ry'], 0, verbose=False)
    set_val(cam, ['rz'], 0, verbose=False)

lights = []
for name in ['light_key', 'light_fill', 'light_rim_v12']:
    l = root.op(name)
    if l is not None:
        lights.append(l.path)

render = root.op('render1')
if render is None:
    render = create_or_get(root, ['renderTOP'], 'render1')

if render is not None:
    if cam is not None:
        set_val(render, ['camera', 'cameras'], cam.path)
    set_val(render, ['geometry', 'geo', 'geometries'], ' '.join(letter_paths + tube_paths))
    if lights:
        set_val(render, ['lights', 'light'], ' '.join(lights))
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
# 5) Debug report
# -------------------------------------------------------------------------
debug = root.op('debug_v13c_rollback_to_v12d')
if debug is None:
    debug = create_or_get(root, ['tableDAT'], 'debug_v13c_rollback_to_v12d')
if debug is not None:
    try:
        debug.clear()
        debug.appendRow(['key', 'value'])
        debug.appendRow(['mode', 'CPU rollback V12D/V11'])
        debug.appendRow(['letters', len(letter_paths)])
        debug.appendRow(['tubes', len(tube_paths)])
        debug.appendRow(['V13gpuactive', get_par(root, 'V13gpuactive').eval() if get_par(root, 'V13gpuactive') else 'missing'])
        debug.appendRow(['open', ROOT_PATH + '/OUT_RENDER_VIEW_THIS'])
        debug.appendRow([])
        debug.appendRow(['letter', 'source', 'final_sop'])
        for row in report:
            debug.appendRow(row)
    except Exception as e:
        print('WARNING debug failed', e)

try:
    root.layout(root.children)
except Exception:
    pass

print('=' * 72)
print('V13C ROLLBACK TO V12D CPU STABLE DONE')
print('Open:', ROOT_PATH + '/OUT_RENDER_VIEW_THIS')
print('Debug:', ROOT_PATH + '/debug_v13c_rollback_to_v12d')
print('Recommendation: save this as MORPHOGENESIS_DNA_CPU_STABLE_V12D.toe')
print('=' * 72)
