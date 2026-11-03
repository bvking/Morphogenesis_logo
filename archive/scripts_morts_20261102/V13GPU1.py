# archive du DAT /project1/V13GPU1 (purge du 2026-11-02)
# morphogenesis_dna_td_v13d_CLEAN_GPU_ERRORS_CPU_PERF.py
# TouchDesigner 2025.32460 / Python 3.11
#
# À lancer après le rollback V13C.
#
# But:
# 1) Nettoyer les erreurs GLSL restantes de la V13:
#    - les GLSL MAT mat_letter_gpu_v13_* peuvent encore cooker même si on est revenu au CPU.
#    - ce script les supprime par défaut.
#
# 2) Revenir clairement au mode CPU stable V12D/V11:
#    - lettres rendues avec mat_letter_blue / mat_letter_violet;
#    - sortie SOP = facet_normals_v12d si disponible, sinon bend_letter_v09;
#    - render1 ne référence plus aucune matière GLSL.
#
# 3) Alléger l'animation CPU:
#    - Curvecookrate = 2 par défaut;
#    - résolution render abaissée si les paramètres existent;
#    - tube moins dense;
#    - Text LOD abaissé;
#    - extrusion légèrement réduite.
#
# Si tu veux garder les objets GLSL pour diagnostic, passe DELETE_GPU_OBJECTS à False.
#
# Usage:
# 1) Colle ce script dans un Text DAT.
# 2) Run Script.
# 3) Ouvre /project1/MORPHOGENESIS_DNA_TD/OUT_RENDER_VIEW_THIS

ROOT_PATH = '/project1/MORPHOGENESIS_DNA_TD'
WORD = 'MORPHOGENESIS'

DELETE_GPU_OBJECTS = True

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

def ensure_float(par_name, label, default, norm_min=None, norm_max=None, page_name='DNA V13D CLEAN'):
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
        return True
    except Exception as e:
        print('WARNING connect failed', src.path if src else None, '->', dst.path if dst else None, e)
        return False

def expr_par(name):
    return "op('%s').par.%s" % (ROOT_PATH, name)

# -------------------------------------------------------------------------
# 1) Clean GLSL V13 objects
# -------------------------------------------------------------------------
deleted = []
kept = []

gpu_names = []
for c in root.children:
    try:
        if c.name.startswith('mat_letter_gpu_v13_') or c.name in ['v13_gpu_letter_vert', 'v13_gpu_letter_frag']:
            gpu_names.append(c.name)
    except Exception:
        pass

for name in gpu_names:
    o = root.op(name)
    if o is None:
        continue
    if DELETE_GPU_OBJECTS:
        try:
            deleted.append(o.path)
            o.destroy()
            print('DELETED GPU V13 object:', name)
        except Exception as e:
            kept.append(o.path + ' delete failed: ' + repr(e))
            print('WARNING could not delete', o.path, e)
    else:
        kept.append(o.path)
        # Make it harmless if possible.
        try:
            o.nodeX += 800
        except Exception:
            pass

# -------------------------------------------------------------------------
# 2) Essential stable params / performance params
# -------------------------------------------------------------------------
params = [
    ('V13gpuactive', 'V13 GPU active', 0.0, 0.0, 1.0),
    ('Curvecookactive', 'Curve cook active', 1.0, 0.0, 1.0),
    ('Curvecookrate', 'Curve cook rate', 2.0, 1.0, 8.0),
    ('Renderresx', 'Render res X', 960.0, 320.0, 3840.0),
    ('Renderresy', 'Render res Y', 540.0, 180.0, 2160.0),
    ('Extrude3dtextlod', 'Text LOD', 0.35, 0.0, 2.0),
    ('Extrude3ddepth', 'Extrude depth', 0.050, 0.0, 0.5),
    ('Letterthickness', 'Letter thickness', 0.050, 0.0, 1.5),
    ('Curveextrudegain', 'Curve extrusion gain', 1.0, 0.0, 5.0),
    ('Tubesurfrows', 'Tube surface rows', 12.0, 4.0, 96.0),
    ('Tubesurfcols', 'Tube surface cols', 20.0, 8.0, 128.0),
    ('Tubewirerowsv12', 'Tube wire rows', 5.0, 2.0, 48.0),
    ('Tubewirecolsv12', 'Tube wire cols', 28.0, 8.0, 160.0),
    ('Viewscale', 'View scale', 0.1, 0.01, 4.0),
    ('Cameradistance', 'Camera distance', 7.2, 1.0, 50.0),
]
for pname, label, default, nmin, nmax in params:
    ensure_float(pname, label, default, nmin, nmax)

# Force chosen lightweight values.
for pname, val in [
    ('V13gpuactive', 0.0),
    ('Curvecookactive', 1.0),
    ('Curvecookrate', 2.0),
    ('Renderresx', 960.0),
    ('Renderresy', 540.0),
    ('Extrude3dtextlod', 0.35),
    ('Extrude3ddepth', 0.050),
    ('Letterthickness', 0.050),
    ('Curveextrudegain', 1.0),
    ('Tubesurfrows', 12.0),
    ('Tubesurfcols', 20.0),
    ('Tubewirerowsv12', 5.0),
    ('Tubewirecolsv12', 28.0),
]:
    p = get_par(root, pname)
    if p is not None:
        try:
            p.val = val
            print('ROOT PARAM', pname, '=', val)
        except Exception:
            pass

# -------------------------------------------------------------------------
# 3) Restore CPU materials
# -------------------------------------------------------------------------
mat_a = root.op('mat_letter_blue')
if mat_a is None:
    mat_a = create_or_get(root, ['phongMAT'], 'mat_letter_blue')

mat_b = root.op('mat_letter_violet')
if mat_b is None:
    mat_b = create_or_get(root, ['phongMAT'], 'mat_letter_violet')

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

# -------------------------------------------------------------------------
# 4) Restore letters CPU SOP output and force cook rate
# -------------------------------------------------------------------------
force_expr = "int(absTime.frame / max(1, int(op('%s').par.Curvecookrate.eval()))) if op('%s').par.Curvecookactive.eval() > 0.5 else 0" % (ROOT_PATH, ROOT_PATH)

letter_paths = []
letter_report = []

for i, ch in enumerate(WORD):
    geo = root.op('letter_%02d_%s' % (i, ch))
    if geo is None:
        print('WARNING missing geo', i, ch)
        continue

    set_flag(geo, 'display', True)
    set_flag(geo, 'render', True)

    # identity transforms
    for pname, val in [('tx',0),('ty',0),('tz',0),('rx',0),('ry',0),('rz',0),('sx',1),('sy',1),('sz',1)]:
        set_val(geo, [pname], val, verbose=False)

    set_val(geo, ['material', 'mat'], mat_a.path if (i % 2 == 0 and mat_a is not None) else (mat_b.path if mat_b is not None else ''), verbose=False)

    # Prefer CPU final from V12D
    final_sop = geo.op('facet_normals_v12d')
    deform_sop = geo.op('bend_letter_v09')
    extrude_sop = geo.op('extrude_letter_v12d')

    if deform_sop is not None:
        try:
            p = get_par(deform_sop, 'Forcecook')
            if p is None:
                page = deform_sop.appendCustomPage('V13D')
                p = page.appendFloat('Forcecook', label='Force cook frame')[0]
            p.expr = force_expr
        except Exception as e:
            print('WARNING Forcecook failed on', deform_sop.path, e)

    if final_sop is None:
        final_sop = deform_sop
    if final_sop is None:
        # fallback text if needed
        for c in geo.children:
            if c.family == 'SOP' and c.name.startswith('text_'):
                final_sop = c
                break

    # Hide all SOPs, then show CPU final.
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

    letter_paths.append(geo.path)
    letter_report.append([ch, final_sop.path if final_sop is not None else 'missing'])

# -------------------------------------------------------------------------
# 5) Lower tube cost
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

    for c in tg.children:
        if c.family == 'SOP':
            if name == 'helix_tube_surface_v06':
                set_expr_by_names(c, ['rows'], "int(" + expr_par('Tubesurfrows') + ")", keywords=['rows'], verbose=False)
                set_expr_by_names(c, ['cols'], "int(" + expr_par('Tubesurfcols') + ")", keywords=['cols', 'columns'], verbose=False)
            else:
                set_expr_by_names(c, ['rows'], "int(" + expr_par('Tubewirerowsv12') + ")", keywords=['rows'], verbose=False)
                set_expr_by_names(c, ['cols'], "int(" + expr_par('Tubewirecolsv12') + ")", keywords=['cols', 'columns'], verbose=False)
            set_flag(c, 'display', True)
            set_flag(c, 'render', True)

    tube_paths.append(tg.path)

# -------------------------------------------------------------------------
# 6) Render and output
# -------------------------------------------------------------------------
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

light_paths = []
for lname in ['light_key', 'light_fill', 'light_rim_v12']:
    l = root.op(lname)
    if l is not None:
        light_paths.append(l.path)

render = root.op('render1')
if render is None:
    render = create_or_get(root, ['renderTOP'], 'render1')

if render is not None:
    if cam is not None:
        set_val(render, ['camera', 'cameras'], cam.path, verbose=False)
    set_val(render, ['geometry', 'geo', 'geometries'], ' '.join(letter_paths + tube_paths))
    if light_paths:
        set_val(render, ['lights', 'light'], ' '.join(light_paths), verbose=False)
    set_expr_by_names(render, ['resx', 'w'], "int(" + expr_par('Renderresx') + ")", keywords=['width','resolution x'], verbose=False)
    set_expr_by_names(render, ['resy', 'h'], "int(" + expr_par('Renderresy') + ")", keywords=['height','resolution y'], verbose=False)
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
# 7) Debug report
# -------------------------------------------------------------------------
debug = root.op('debug_v13d_clean_gpu_cpu_perf')
if debug is None:
    debug = create_or_get(root, ['tableDAT'], 'debug_v13d_clean_gpu_cpu_perf')

if debug is not None:
    try:
        debug.clear()
        debug.appendRow(['key', 'value'])
        debug.appendRow(['mode', 'CPU stable, GPU V13 cleaned'])
        debug.appendRow(['DELETE_GPU_OBJECTS', DELETE_GPU_OBJECTS])
        debug.appendRow(['deleted_gpu_objects', len(deleted)])
        debug.appendRow(['kept_gpu_objects', len(kept)])
        debug.appendRow(['letters', len(letter_paths)])
        debug.appendRow(['tubes', len(tube_paths)])
        debug.appendRow(['Curvecookrate', root.par.Curvecookrate.eval() if get_par(root,'Curvecookrate') else 'missing'])
        debug.appendRow(['Renderres', str(root.par.Renderresx.eval() if get_par(root,'Renderresx') else '?') + ' x ' + str(root.par.Renderresy.eval() if get_par(root,'Renderresy') else '?')])
        debug.appendRow(['open', ROOT_PATH + '/OUT_RENDER_VIEW_THIS'])
        debug.appendRow([])
        debug.appendRow(['deleted'])
        for d in deleted:
            debug.appendRow([d])
        debug.appendRow([])
        debug.appendRow(['letter', 'final_sop'])
        for row in letter_report:
            debug.appendRow(row)
    except Exception as e:
        print('WARNING debug failed', e)

try:
    root.layout(root.children)
except Exception:
    pass

print('=' * 72)
print('V13D CLEAN GPU ERRORS + CPU PERF DONE')
print('Deleted GPU V13 objects:', len(deleted))
print('Open:', ROOT_PATH + '/OUT_RENDER_VIEW_THIS')
print('Debug:', ROOT_PATH + '/debug_v13d_clean_gpu_cpu_perf')
print('Recommended now:')
print('  Save as MORPHOGENESIS_DNA_CPU_STABLE_CLEAN.toe')
print('  If animation is too choppy, set Curvecookrate back to 1.')
print('  If FPS is too low, keep Curvecookrate 2 and lower Renderresx/y further.')
print('=' * 72)
