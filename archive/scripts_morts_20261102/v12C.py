# archive du DAT /project1/v12C (purge du 2026-11-02)
# morphogenesis_dna_td_v12c_CAMERA_VIEW_FIX.py
# TouchDesigner 2025.32460 / Python 3.11
#
# À lancer après V11/V12 si la scène devient invisible ou si Camera distance semble sans effet.
#
# Ce script corrige/précise 3 choses:
# 1) Il remet une vue sûre basée sur tes derniers réglages visibles:
#      Viewscale = 0.1
#      Viewtx = -0.16
#      Viewty = 0
#      Viewtz = -3.97
#      Cameradistance = 7.2
#
# 2) Il force cam1 à être la caméra de render1, avec une expression fiable:
#      cam1.tz = Cameradistance
#
# 3) Il crée un TOP de sortie clair:
#      /project1/MORPHOGENESIS_DNA_TD/OUT_RENDER_VIEW_THIS
#
# IMPORTANT:
# - Camera distance n'a d'effet que dans le Render TOP / OUT_RENDER_VIEW_THIS.
# - Dans le viewer 3D de la Base COMP ou du Network Editor, tu regardes avec la caméra du viewer,
#   pas forcément avec cam1.
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
        print('WARNING could not set expr', o.path if o else None, names, expr)
    return None

def ensure_float(par_name, label, default, norm_min=None, norm_max=None):
    p = get_par(root, par_name)
    if p is not None:
        return p
    try:
        page = root.appendCustomPage('DNA V12C')
    except Exception:
        try:
            page = root.appendCustomPage('DNA V12C B')
        except Exception:
            print('WARNING cannot create page DNA V12C')
            return None
    try:
        p = page.appendFloat(par_name, label=label)[0]
        p.default = default
        p.val = default
        if norm_min is not None:
            p.normMin = norm_min
        if norm_max is not None:
            p.normMax = norm_max
        print('ADDED PARAM', par_name, default)
        return p
    except Exception as e:
        print('WARNING cannot add parameter', par_name, e)
        return None

def create_if_missing(parent, type_names, name):
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

# -------------------------------------------------------------------------
# 1) Ensure required parameters exist
# -------------------------------------------------------------------------
for pname, label, default, nmin, nmax in [
    ('Viewrotx', 'View rotate X', 0, -180, 180),
    ('Viewroty', 'View rotate Y', 0, -180, 180),
    ('Viewrotz', 'View rotate Z', 0, -180, 180),
    ('Viewscale', 'View scale', 0.1, 0.01, 4),
    ('Viewtx', 'View translate X', -0.16, -10, 10),
    ('Viewty', 'View translate Y', 0, -10, 10),
    ('Viewtz', 'View translate Z', -3.97, -20, 20),
    ('Cameradistance', 'Camera distance', 7.2, 1, 50),
    ('Curvecookactive', 'Curve cook active', 1, 0, 1),
    ('Curvecookrate', 'Curve cook rate', 1, 1, 8),
    ('Renderresx', 'Render res X', 1280, 320, 3840),
    ('Renderresy', 'Render res Y', 720, 180, 2160),
]:
    ensure_float(pname, label, default, nmin, nmax)

# -------------------------------------------------------------------------
# 2) Apply safe view from your screenshot
# -------------------------------------------------------------------------
safe_values = {
    'Viewrotx': 0,
    'Viewroty': 0,
    'Viewrotz': 0,
    'Viewscale': 0.1,
    'Viewtx': -0.16,
    'Viewty': 0,
    'Viewtz': -3.97,
    'Cameradistance': 7.2,
    'Curvecookactive': 1,
    'Curvecookrate': 1,
}
for pname, val in safe_values.items():
    p = get_par(root, pname)
    if p is not None:
        try:
            p.val = val
            print('ROOT', pname, '=', val)
        except Exception:
            pass

# -------------------------------------------------------------------------
# 3) Camera repair
# -------------------------------------------------------------------------
cam = create_if_missing(root, ['cameraCOMP'], 'cam1')
if cam is not None:
    cam.nodeX = 900
    cam.nodeY = -170
    set_val(cam, ['lookat'], '')
    set_val(cam, ['tx'], 0)
    set_val(cam, ['ty'], 0)
    set_expr(cam, 'tz', "op('%s').par.Cameradistance" % ROOT_PATH)
    set_val(cam, ['rx'], 0)
    set_val(cam, ['ry'], 0)
    set_val(cam, ['rz'], 0)

    # Make sure perspective camera and clipping do not hide geometry.
    set_val(cam, ['projection'], 'perspective', verbose=False)
    set_val(cam, ['near'], 0.01, verbose=False)
    set_val(cam, ['far'], 1000, verbose=False)
    set_val(cam, ['fov'], 45, verbose=False)
    set_val(cam, ['fovx'], 45, verbose=False)
    set_val(cam, ['fovy'], 45, verbose=False)

# -------------------------------------------------------------------------
# 4) Lights
# -------------------------------------------------------------------------
light_key = create_if_missing(root, ['lightCOMP'], 'light_key')
if light_key is not None:
    set_val(light_key, ['tx'], 3.0, verbose=False)
    set_val(light_key, ['ty'], 3.8, verbose=False)
    set_val(light_key, ['tz'], 5.5, verbose=False)
    set_val(light_key, ['lightcolorr'], 1.0, verbose=False)
    set_val(light_key, ['lightcolorg'], 1.0, verbose=False)
    set_val(light_key, ['lightcolorb'], 1.0, verbose=False)

light_fill = create_if_missing(root, ['lightCOMP'], 'light_fill')
if light_fill is not None:
    set_val(light_fill, ['tx'], -3.0, verbose=False)
    set_val(light_fill, ['ty'], -2.0, verbose=False)
    set_val(light_fill, ['tz'], 4.5, verbose=False)
    set_val(light_fill, ['lightcolorr'], 0.35, verbose=False)
    set_val(light_fill, ['lightcolorg'], 0.45, verbose=False)
    set_val(light_fill, ['lightcolorb'], 1.0, verbose=False)

light_rim = create_if_missing(root, ['lightCOMP'], 'light_rim_v12')
if light_rim is not None:
    set_val(light_rim, ['tx'], -4.0, verbose=False)
    set_val(light_rim, ['ty'], 2.0, verbose=False)
    set_val(light_rim, ['tz'], -4.0, verbose=False)
    set_val(light_rim, ['lightcolorr'], 0.5, verbose=False)
    set_val(light_rim, ['lightcolorg'], 0.8, verbose=False)
    set_val(light_rim, ['lightcolorb'], 1.0, verbose=False)

# -------------------------------------------------------------------------
# 5) Re-enable letters and Script SOP outputs
# -------------------------------------------------------------------------
force_expr = "int(absTime.frame / max(1, int(op('%s').par.Curvecookrate.eval()))) if op('%s').par.Curvecookactive.eval() > 0.5 else 0" % (ROOT_PATH, ROOT_PATH)

letter_paths = []
for i, ch in enumerate(WORD):
    geo = root.op('letter_%02d_%s' % (i, ch))
    if geo is None:
        print('WARNING missing letter', i, ch)
        continue

    # Geometry identity because Script SOP is already world-transformed by module.
    for pname, val in [('tx',0),('ty',0),('tz',0),('rx',0),('ry',0),('rz',0),('sx',1),('sy',1),('sz',1)]:
        set_val(geo, [pname], val, verbose=False)

    set_flag(geo, 'display', True)
    set_flag(geo, 'render', True)

    deform = geo.op('bend_letter_v09')
    if deform is not None:
        # Only the deformed SOP should render.
        for c in geo.children:
            if c.family == 'SOP':
                set_flag(c, 'display', False)
                set_flag(c, 'render', False)

        set_flag(deform, 'display', True)
        set_flag(deform, 'render', True)

        # keep it cooking
        try:
            p = get_par(deform, 'Forcecook')
            if p is None:
                page = deform.appendCustomPage('V12C')
                p = page.appendFloat('Forcecook', label='Force cook frame')[0]
            p.expr = force_expr
        except Exception as e:
            print('WARNING Forcecook', deform.path, e)

        try:
            deform.cook(force=True)
        except Exception as e:
            print('WARNING could not cook', deform.path, e)
    else:
        # Fallback: show text SOP if deformation SOP is missing.
        print('WARNING no bend_letter_v09 in', geo.path, 'showing first Text SOP fallback')
        for c in geo.children:
            if c.family == 'SOP':
                if c.name.startswith('text_'):
                    set_flag(c, 'display', True)
                    set_flag(c, 'render', True)
                    break

    letter_paths.append(geo.path)

# -------------------------------------------------------------------------
# 6) Tube paths and transforms
# -------------------------------------------------------------------------
tube_paths = []
for name in ['helix_tube_surface_v06', 'helix_tube_wire_v06']:
    tg = root.op(name)
    if tg is None:
        print('WARNING missing tube', name)
        continue

    for pname in ['tx','ty','tz']:
        set_expr(tg, pname, "op('%s').par.View%s" % (ROOT_PATH, pname), verbose=False)
    set_expr(tg, 'rx', "op('%s').par.Viewrotx" % ROOT_PATH, verbose=False)
    set_expr(tg, 'ry', "op('%s').par.Viewroty" % ROOT_PATH, verbose=False)
    set_expr(tg, 'rz', "op('%s').par.Viewrotz" % ROOT_PATH, verbose=False)
    set_expr(tg, 'sx', "op('%s').par.Viewscale" % ROOT_PATH, verbose=False)
    set_expr(tg, 'sy', "op('%s').par.Viewscale" % ROOT_PATH, verbose=False)
    set_expr(tg, 'sz', "op('%s').par.Viewscale" % ROOT_PATH, verbose=False)

    set_flag(tg, 'display', True)
    set_flag(tg, 'render', True)
    for c in tg.children:
        if c.family == 'SOP':
            set_flag(c, 'display', True)
            set_flag(c, 'render', True)

    tube_paths.append(tg.path)

# -------------------------------------------------------------------------
# 7) Render TOP and clear OUT TOP
# -------------------------------------------------------------------------
render = create_if_missing(root, ['renderTOP'], 'render1')
geo_paths = letter_paths + tube_paths

if render is not None:
    render.nodeX = 1120
    render.nodeY = -170

    if cam is not None:
        set_val(render, ['camera', 'cameras'], cam.path)
    set_val(render, ['geometry', 'geo', 'geometries'], ' '.join(geo_paths))

    lights = [l.path for l in [light_key, light_fill, light_rim] if l is not None]
    set_val(render, ['lights', 'light'], ' '.join(lights))

    set_expr_by_names(render, ['resx', 'w'], "int(op('%s').par.Renderresx)" % ROOT_PATH, keywords=['width','resolution x'])
    set_expr_by_names(render, ['resy', 'h'], "int(op('%s').par.Renderresy)" % ROOT_PATH, keywords=['height','resolution y'])

    set_val(render, ['bgcolorr'], 0.012, verbose=False)
    set_val(render, ['bgcolorg'], 0.014, verbose=False)
    set_val(render, ['bgcolorb'], 0.026, verbose=False)
    set_val(render, ['bgcolora'], 1.0, verbose=False)

    try:
        render.cook(force=True)
    except Exception as e:
        print('WARNING render cook failed', e)

# Create a clear output TOP to view.
out_top = create_if_missing(root, ['nullTOP'], 'OUT_RENDER_VIEW_THIS')
if out_top is not None and render is not None:
    out_top.nodeX = render.nodeX + 220
    out_top.nodeY = render.nodeY
    try:
        out_top.inputConnectors[0].connect(render)
        print('CONNECTED render1 -> OUT_RENDER_VIEW_THIS')
    except Exception as e:
        print('WARNING could not connect OUT TOP', e)
    try:
        out_top.par.viewer = True
    except Exception:
        pass
    set_flag(out_top, 'viewer', True)
    try:
        out_top.cook(force=True)
    except Exception:
        pass

# -------------------------------------------------------------------------
# 8) Debug report
# -------------------------------------------------------------------------
debug = create_if_missing(root, ['tableDAT'], 'debug_v12c_camera_view_fix')
if debug is not None:
    debug.nodeX = 760
    debug.nodeY = -1040
    try:
        debug.clear()
        debug.appendRow(['key', 'value'])
        debug.appendRow(['open_this', ROOT_PATH + '/OUT_RENDER_VIEW_THIS'])
        debug.appendRow(['render', render.path if render else 'missing'])
        debug.appendRow(['camera', cam.path if cam else 'missing'])
        debug.appendRow(['camera_tz_expr', cam.par.tz.expr if cam and get_par(cam, 'tz') else 'missing'])
        debug.appendRow(['render_camera', render.par.camera.eval() if render and get_par(render, 'camera') else 'check manually'])
        debug.appendRow(['letters', len(letter_paths)])
        debug.appendRow(['tubes', len(tube_paths)])
        debug.appendRow(['Viewscale', root.par.Viewscale.eval() if get_par(root, 'Viewscale') else 'missing'])
        debug.appendRow(['Viewtx', root.par.Viewtx.eval() if get_par(root, 'Viewtx') else 'missing'])
        debug.appendRow(['Viewty', root.par.Viewty.eval() if get_par(root, 'Viewty') else 'missing'])
        debug.appendRow(['Viewtz', root.par.Viewtz.eval() if get_par(root, 'Viewtz') else 'missing'])
        debug.appendRow(['Cameradistance', root.par.Cameradistance.eval() if get_par(root, 'Cameradistance') else 'missing'])
        debug.appendRow(['note', 'Camera distance affects render1/OUT_RENDER_VIEW_THIS, not necessarily the Base COMP network viewer.'])
    except Exception as e:
        print('WARNING debug failed', e)

try:
    root.layout(root.children)
except Exception:
    pass

print('=' * 72)
print('V12C CAMERA / VIEW FIX DONE')
print('Open this TOP:', ROOT_PATH + '/OUT_RENDER_VIEW_THIS')
print('Safe view set to:')
print('  Viewscale = 0.1')
print('  Viewtx    = -0.16')
print('  Viewty    = 0')
print('  Viewtz    = -3.97')
print('  Camera distance = 7.2')
print('Important: Cameradistance affects render1/OUT_RENDER_VIEW_THIS.')
print('It will not necessarily affect the Base COMP 3D network viewer.')
print('Debug:', ROOT_PATH + '/debug_v12c_camera_view_fix')
print('=' * 72)
