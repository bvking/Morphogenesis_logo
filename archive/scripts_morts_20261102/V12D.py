# archive du DAT /project1/V12D (purge du 2026-11-02)
# morphogenesis_dna_td_v12d_EXTRUDED_LETTERS.py
# TouchDesigner 2025.32460 / Python 3.11
#
# À lancer après V11/V12.
#
# V12D = lettres légèrement extrudées, tout en continuant à épouser le tube.
#
# Principe:
# - chaque Text SOP est réglé en Closed Polygons si possible;
# - un Hole SOP est inséré si disponible pour mieux préserver les trous des lettres;
# - un Extrude SOP crée une faible épaisseur 3D;
# - le Script SOP bend_letter_v09 reçoit maintenant la géométrie extrudée;
# - le module V11 continue à courber tous les points sur la surface du tube.
#
# Résultat attendu:
# - lettres plus 3D;
# - extrusion légère dans l'axe normal de chaque lettre;
# - courbure conservée autour du tube;
# - miroir arrière et étirement de hauteur conservés.
#
# Usage:
# 1) Colle ce script dans un Text DAT.
# 2) Run Script.
# 3) Ouvre /project1/MORPHOGENESIS_DNA_TD/OUT_RENDER_VIEW_THIS ou render1.

ROOT_PATH = '/project1/MORPHOGENESIS_DNA_TD'
WORD = 'MORPHOGENESIS'

root = op(ROOT_PATH)
if root is None:
    raise Exception('Container introuvable: ' + ROOT_PATH)

# -------------------------------------------------------------------------
# UTILS
# -------------------------------------------------------------------------
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

def ensure_float(par_name, label, default, norm_min=None, norm_max=None, page_name='DNA V12D'):
    p = get_par(root, par_name)
    if p is not None:
        print('PARAM already exists:', par_name, '=', p.eval())
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

def create_or_get(parent, type_names, name, destroy=False):
    existing = parent.op(name)
    if existing is not None:
        if not destroy:
            return existing
        try:
            existing.destroy()
        except Exception as e:
            print('WARNING could not destroy', existing.path, e)

    errors = []
    for tn in type_names:
        try:
            o = parent.create(tn, name)
            print('CREATED', o.path, 'type', tn)
            return o
        except Exception as e:
            errors.append(tn + ': ' + repr(e))
    print('WARNING cannot create', name, errors)
    return None

def connect(src, dst, index=0):
    if src is None or dst is None:
        return False
    try:
        dst.inputConnectors[index].connect(src)
        print('CONNECTED', src.path, '->', dst.path)
        return True
    except Exception as e:
        print('WARNING connect failed:', src.path, '->', dst.path, e)
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
# 1) Parameters
# -------------------------------------------------------------------------
ensure_float('Extrude3dactive', 'Extrude 3D active', 1.0, 0.0, 1.0)
ensure_float('Extrude3ddepth', 'Extrude 3D depth', 0.070, 0.0, 0.35)
ensure_float('Extrude3dfrontback', 'Extrude front/back faces', 1.0, 0.0, 1.0)
ensure_float('Extrude3dsides', 'Extrude side mesh', 1.0, 0.0, 1.0)
ensure_float('Extrude3dcusp', 'Extrude cusp edges', 1.0, 0.0, 1.0)
ensure_float('Extrude3dcuspangle', 'Extrude cusp angle', 24.0, 0.0, 90.0)
ensure_float('Extrude3dnormalgain', 'Extrude normal gain', 1.25, 0.0, 3.0)
ensure_float('Extrude3dtextlod', 'Text LOD', 0.65, 0.0, 2.0)
ensure_float('Extrude3dmatboost', '3D material boost', 0.12, 0.0, 1.0)

# Keep old parameters stable.
ensure_float('Letterthickness', 'Letter thickness', 0.070, 0.0, 1.5)
ensure_float('Curveextrudegain', 'Curve extrusion gain', 1.25, 0.0, 3.0)
ensure_float('Curvecookactive', 'Curve cook active', 1.0, 0.0, 1.0)
ensure_float('Curvecookrate', 'Curve cook rate', 1.0, 1.0, 8.0)

# Force a visible but light 3D extrusion.
try:
    root.par.Letterthickness.val = 0.070
except Exception:
    pass
try:
    root.par.Curveextrudegain.val = 1.25
except Exception:
    pass

# -------------------------------------------------------------------------
# 2) Make sure the V11/V09 geometry module exists
# -------------------------------------------------------------------------
geom_module = root.op('dna_v09_geom_module')
if geom_module is None:
    print('WARNING: dna_v09_geom_module introuvable. Lance d’abord V11, puis relance V12D.')
else:
    print('FOUND geometry module:', geom_module.path)

# -------------------------------------------------------------------------
# 3) Callback fallback for Script SOPs, in case reopen lost callback assignment
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
            scriptOp.addWarning('V12D deform failed: ' + repr(e))
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
        print('WARNING could not assign callback DAT to', script_sop.path)

    return ok

# -------------------------------------------------------------------------
# 4) Per-letter SOP chain:
#    Text SOP -> Hole SOP optional -> Extrude SOP -> Script SOP bend -> Facet SOP optional
# -------------------------------------------------------------------------
force_expr = "int(absTime.frame / max(1, int(op('%s').par.Curvecookrate.eval()))) if op('%s').par.Curvecookactive.eval() > 0.5 else 0" % (ROOT_PATH, ROOT_PATH)

letter_paths = []
report_rows = []

for i, ch in enumerate(WORD):
    geo = root.op('letter_%02d_%s' % (i, ch))
    if geo is None:
        print('WARNING missing letter geo', i, ch)
        continue

    set_flag(geo, 'display', True)
    set_flag(geo, 'render', True)

    # Geometry COMP must be identity because the Script SOP outputs transformed geometry.
    for pname, val in [('tx',0), ('ty',0), ('tz',0), ('rx',0), ('ry',0), ('rz',0), ('sx',1), ('sy',1), ('sz',1)]:
        set_val(geo, [pname], val, verbose=False)

    # Find Text SOP.
    text_sop = None
    for c in geo.children:
        if c.family == 'SOP' and c.name.startswith('text_'):
            text_sop = c
            break

    if text_sop is None:
        print('WARNING no Text SOP found in', geo.path)
        continue

    # Text SOP: Closed Polygons are recommended before Extrude SOP.
    set_val(text_sop, ['text', 'Text'], ch, verbose=False)
    set_val(text_sop, ['output'], 'closedpolys')
    set_expr_by_names(text_sop, ['levelofdetail'], expr_par('Extrude3dtextlod'), keywords=['level of detail', 'lod'])
    set_flag(text_sop, 'display', False)
    set_flag(text_sop, 'render', False)

    # Optional Hole SOP improves holes in O/P-like letters.
    hole = create_or_get(geo, ['holeSOP'], 'hole_letter_v12d', destroy=False)
    if hole is not None:
        hole.nodeX = text_sop.nodeX + 150
        hole.nodeY = text_sop.nodeY
        connect(text_sop, hole, 0)
        set_flag(hole, 'display', False)
        set_flag(hole, 'render', False)
        source_for_extrude = hole
    else:
        source_for_extrude = text_sop

    # Extrude SOP.
    extrude = create_or_get(geo, ['extrudeSOP'], 'extrude_letter_v12d', destroy=False)
    if extrude is not None:
        extrude.nodeX = text_sop.nodeX + 320
        extrude.nodeY = text_sop.nodeY
        connect(source_for_extrude, extrude, 0)

        # Values page.
        # Depth Scale controls the actual extrusion depth.
        set_expr_by_names(
            extrude,
            ['depthscale'],
            expr_par('Extrude3ddepth') + ' * ' + expr_par('Extrude3dactive'),
            keywords=['depth scale']
        )

        # Keep extrusion centered-ish by shifting half depth.
        # If this parameter behaves differently in this build, disable by setting depthxlate to 0 manually.
        set_expr_by_names(
            extrude,
            ['depthxlate'],
            '-0.5 * ' + expr_par('Extrude3ddepth') + ' * ' + expr_par('Extrude3dactive'),
            keywords=['depth translate']
        )

        set_val(extrude, ['thickxlate'], 0, verbose=False)
        set_val(extrude, ['thickscale'], 1, verbose=False)

        # Faces and sides.
        set_expr_by_names(
            extrude,
            ['fronttype'],
            "'convex' if op('%s').par.Extrude3dfrontback.eval() > 0.5 else 'off'" % ROOT_PATH,
            keywords=['front face']
        )
        set_expr_by_names(
            extrude,
            ['backtype'],
            "'convex' if op('%s').par.Extrude3dfrontback.eval() > 0.5 else 'off'" % ROOT_PATH,
            keywords=['back face']
        )
        set_expr_by_names(
            extrude,
            ['sidetype'],
            "'quads' if op('%s').par.Extrude3dsides.eval() > 0.5 else 'off'" % ROOT_PATH,
            keywords=['side mesh']
        )

        set_val(extrude, ['dofuse'], 'all', verbose=False)
        set_expr_by_names(extrude, ['docusp'], expr_par('Extrude3dcusp') + ' > 0.5', keywords=['cusp'])
        set_expr_by_names(extrude, ['cuspangle'], expr_par('Extrude3dcuspangle'), keywords=['cusp angle'])
        set_val(extrude, ['sharefaces'], True, verbose=False)
        set_val(extrude, ['removesharedsides'], True, verbose=False)

        set_flag(extrude, 'display', False)
        set_flag(extrude, 'render', False)
        source_for_deform = extrude
    else:
        print('WARNING Extrude SOP failed for', ch, 'fallback to text/hole')
        source_for_deform = source_for_extrude

    # Script SOP from V09/V11.
    deform = geo.op('bend_letter_v09')
    if deform is None:
        deform = create_or_get(geo, ['scriptSOP'], 'bend_letter_v09', destroy=False)

    if deform is not None:
        deform.nodeX = text_sop.nodeX + 500
        deform.nodeY = text_sop.nodeY
        connect(source_for_deform, deform, 0)

        # Callback DAT.
        cb = geo.op('bend_letter_v09_callbacks')
        if cb is None:
            cb = geo.create('textDAT', 'bend_letter_v09_callbacks')
            print('CREATED callback DAT', cb.path)
        cb.nodeX = deform.nodeX
        cb.nodeY = deform.nodeY - 90
        cb.text = callback_template.replace('__LETTER_INDEX__', str(i))
        assign_callbacks(deform, cb)

        # Force cook.
        try:
            p = get_par(deform, 'Forcecook')
            if p is None:
                page = deform.appendCustomPage('V12D')
                p = page.appendFloat('Forcecook', label='Force cook frame')[0]
            p.expr = force_expr
        except Exception as e:
            print('WARNING cannot set Forcecook on', deform.path, e)

        # Optional Facet SOP after deformation to improve normals.
        facet = create_or_get(geo, ['facetSOP'], 'facet_normals_v12d', destroy=False)
        if facet is not None:
            facet.nodeX = deform.nodeX + 170
            facet.nodeY = deform.nodeY
            connect(deform, facet, 0)
            set_val(facet, ['docusp'], True, verbose=False)
            set_val(facet, ['cuspangle'], 32, verbose=False)
            set_val(facet, ['postnml'], True, verbose=False)
            set_val(facet, ['normals'], True, verbose=False)

            final_sop = facet
        else:
            final_sop = deform

        # Only final SOP is displayed/rendered.
        for c in geo.children:
            if c.family == 'SOP':
                set_flag(c, 'display', False)
                set_flag(c, 'render', False)

        set_flag(final_sop, 'display', True)
        set_flag(final_sop, 'render', True)

        try:
            deform.cook(force=True)
        except Exception as e:
            print('WARNING cook failed', deform.path, e)

        try:
            final_sop.cook(force=True)
        except Exception:
            pass

        report_rows.append([ch, source_for_deform.path if source_for_deform else 'none', final_sop.path])
    else:
        print('WARNING no Script SOP for', ch)

    letter_paths.append(geo.path)

# -------------------------------------------------------------------------
# 5) Materials: slightly more 3D contrast
# -------------------------------------------------------------------------
mat_a = root.op('mat_letter_blue')
mat_b = root.op('mat_letter_violet')

for mat, prefix in [(mat_a, 'Stranda'), (mat_b, 'Strandb')]:
    if mat is None:
        continue

    # Add a little constant/emission if the parameters exist.
    set_expr_by_names(mat, ['constantr'], expr_par(prefix + 'r') + ' * ' + expr_par('Extrude3dmatboost'), keywords=['constant r', 'emission r'], verbose=False)
    set_expr_by_names(mat, ['constantg'], expr_par(prefix + 'g') + ' * ' + expr_par('Extrude3dmatboost'), keywords=['constant g', 'emission g'], verbose=False)
    set_expr_by_names(mat, ['constantb'], expr_par(prefix + 'b') + ' * ' + expr_par('Extrude3dmatboost'), keywords=['constant b', 'emission b'], verbose=False)

    # Keep letters opaque.
    set_val(mat, ['blending'], False, verbose=False)
    set_val(mat, ['depthwriting'], True, verbose=False)
    set_val(mat, ['cullface'], 'neither', verbose=False)

# -------------------------------------------------------------------------
# 6) Render TOP paths
# -------------------------------------------------------------------------
tube_paths = []
for name in ['helix_tube_surface_v06', 'helix_tube_wire_v06']:
    tg = root.op(name)
    if tg is not None:
        set_flag(tg, 'display', True)
        set_flag(tg, 'render', True)
        tube_paths.append(tg.path)

render = root.op('render1')
cam = root.op('cam1')
light_paths = []
for name in ['light_key', 'light_fill', 'light_rim_v12']:
    l = root.op(name)
    if l is not None:
        light_paths.append(l.path)

if render is not None:
    if cam is not None:
        set_val(render, ['camera', 'cameras'], cam.path)
    set_val(render, ['geometry', 'geo', 'geometries'], ' '.join(letter_paths + tube_paths))
    if light_paths:
        set_val(render, ['lights', 'light'], ' '.join(light_paths))
    try:
        render.cook(force=True)
    except Exception:
        pass

out_top = root.op('OUT_RENDER_VIEW_THIS')
if out_top is not None and render is not None:
    try:
        out_top.inputConnectors[0].connect(render)
    except Exception:
        pass
    try:
        out_top.cook(force=True)
    except Exception:
        pass

# -------------------------------------------------------------------------
# 7) Debug report
# -------------------------------------------------------------------------
debug = create_or_get(root, ['tableDAT'], 'debug_v12d_extruded_letters', destroy=False)
if debug is not None:
    debug.nodeX = 760
    debug.nodeY = -1100
    try:
        debug.clear()
        debug.appendRow(['key', 'value'])
        debug.appendRow(['Extrude3dactive', root.par.Extrude3dactive.eval()])
        debug.appendRow(['Extrude3ddepth', root.par.Extrude3ddepth.eval()])
        debug.appendRow(['Curveextrudegain', root.par.Curveextrudegain.eval() if get_par(root, 'Curveextrudegain') else 'missing'])
        debug.appendRow(['Letterthickness', root.par.Letterthickness.eval() if get_par(root, 'Letterthickness') else 'missing'])
        debug.appendRow(['letters', len(letter_paths)])
        debug.appendRow(['note', 'Text SOP -> Hole optional -> Extrude SOP -> Script SOP deformation -> Facet optional'])
        debug.appendRow([])
        debug.appendRow(['letter', 'source_for_deform', 'final_render_sop'])
        for row in report_rows:
            debug.appendRow(row)
    except Exception as e:
        print('WARNING debug failed', e)

try:
    root.layout(root.children)
except Exception:
    pass

print('=' * 72)
print('MORPHOGENESIS DNA V12D EXTRUDED LETTERS OK')
print('Open:', ROOT_PATH + '/OUT_RENDER_VIEW_THIS')
print('or:', ROOT_PATH + '/render1')
print('Controls:', ROOT_PATH, '> page DNA V12D')
print('Main controls:')
print('  Extrude3ddepth      : thickness of the 3D extrusion')
print('  Extrude3dnormalgain : use with Curveextrudegain for visible depth')
print('  Extrude3dactive     : 1 on / 0 off')
print('Debug:', ROOT_PATH + '/debug_v12d_extruded_letters')
print('=' * 72)
