# archive du DAT /project1/V15D (purge du 2026-11-02)
# morphogenesis_dna_td_v15d_READABILITY_SHAPE_FIX.py
# TouchDesigner 2025.32460 / Python 3.11
#
# A lancer apres V15C Visibility Repair.
#
# V15D corrige trois points observes:
# 1) lettres trop sombres au moment du switch avant/arriere;
# 2) M/O/R/P/H parfois tronquees a gauche quand l'etirement est extreme;
# 3) la lettre I qui epouse mal le tube faute de points suffisants.
#
# Cette version:
# - ne reactive pas l'extrusion lourde;
# - ne reactive pas normal map / bump map;
# - garde le mode CPU Lite;
# - ajoute une matiere plus lisible et des lumieres de lecture bas/arriere;
# - ajoute une subdivision legere uniquement sur I par defaut.

ROOT_PATH = '/project1/MORPHOGENESIS_DNA_TD'
WORD = 'MORPHOGENESIS'

root = op(ROOT_PATH)
if root is None:
    raise Exception('Container introuvable: ' + ROOT_PATH)

# -------------------------------------------------------------------------
# Utils
# -------------------------------------------------------------------------
def fp(o, name):
    if o is None:
        return None
    try:
        return getattr(o.par, name)
    except Exception:
        pass
    lname = name.lower()
    try:
        for p in o.pars():
            if p.name.lower() == lname:
                return p
    except Exception:
        pass
    return None

def pexpr(name, fallback='0'):
    p = fp(root, name)
    return "op('%s').par.%s" % (ROOT_PATH, p.name) if p is not None else str(fallback)

def setv(o, names, val, kws=None, silent=True):
    if o is None:
        return None
    for n in names:
        p = fp(o, n)
        if p is not None:
            try:
                p.val = val
                if not silent: print('SET', o.path + '.par.' + p.name, '=', val)
                return p
            except Exception:
                pass
    if kws:
        kl = [k.lower() for k in kws]
        try:
            pars = o.pars()
        except Exception:
            pars = []
        for p in pars:
            try: label = p.label
            except Exception: label = ''
            key = (p.name + ' ' + label).lower()
            if any(k in key for k in kl):
                try:
                    p.val = val
                    if not silent: print('SET fallback', o.path + '.par.' + p.name, '=', val)
                    return p
                except Exception:
                    pass
    if not silent: print('WARN set failed', o.path if o else None, names, val)
    return None

def sete(o, names, expr, kws=None, silent=True):
    if o is None:
        return None
    for n in names:
        p = fp(o, n)
        if p is not None:
            try:
                p.expr = expr
                if not silent: print('EXPR', o.path + '.par.' + p.name, '=', expr)
                return p
            except Exception:
                pass
    if kws:
        kl = [k.lower() for k in kws]
        try:
            pars = o.pars()
        except Exception:
            pars = []
        for p in pars:
            try: label = p.label
            except Exception: label = ''
            key = (p.name + ' ' + label).lower()
            if any(k in key for k in kl):
                try:
                    p.expr = expr
                    if not silent: print('EXPR fallback', o.path + '.par.' + p.name, '=', expr)
                    return p
                except Exception:
                    pass
    if not silent: print('WARN expr failed', o.path if o else None, names, expr)
    return None

def ensure_float(name, label, default, nmin=None, nmax=None):
    p = fp(root, name)
    if p is not None:
        return p
    page = None
    for pg in ['DNA V15D READABLE', 'DNA V15D READABLE B', 'DNA V15D READABLE C']:
        try:
            page = root.appendCustomPage(pg)
            break
        except Exception:
            pass
    if page is None:
        return None
    try:
        p = page.appendFloat(name, label=label)[0]
        p.default = default
        p.val = default
        if nmin is not None: p.normMin = nmin
        if nmax is not None: p.normMax = nmax
        print('ADDED PARAM', name, '=', default, 'actual:', p.name)
        return p
    except Exception as e:
        print('WARNING cannot add param', name, e)
        return None

def opget(parent, type_names, name, destroy=False):
    old = parent.op(name)
    if old is not None:
        if not destroy:
            return old
        try: old.destroy()
        except Exception: pass
    for tn in type_names:
        try:
            o = parent.create(tn, name)
            print('CREATED', o.path, tn)
            return o
        except Exception as e:
            print('try create failed', tn, e)
    return None

def conn(src, dst, idx=0):
    if src is None or dst is None:
        return False
    try:
        dst.inputConnectors[idx].connect(src)
        return True
    except Exception as e:
        print('WARNING connect failed', src.path if src else None, '->', dst.path if dst else None, e)
        return False

def flag(o, name, value):
    try:
        setattr(o, name, value)
        return True
    except Exception:
        return False

def count_pts(o):
    try: return int(o.numPoints)
    except Exception:
        try: return int(o.numPoints())
        except Exception: return -1

def clamp_param(name, hi=None, lo=None):
    p = fp(root, name)
    if p is None:
        return
    try:
        v = float(p.eval())
        nv = v
        if hi is not None: nv = min(nv, hi)
        if lo is not None: nv = max(nv, lo)
        if abs(nv - v) > 1e-6:
            p.val = nv
            print('CLAMP', name, v, '->', nv)
    except Exception:
        pass

# -------------------------------------------------------------------------
# Parameters and safe defaults
# -------------------------------------------------------------------------
for a in [
    ('V15dreadambient', 'Readable ambient', 0.52, 0, 2),
    ('V15dreademission', 'Readable emission', 0.34, 0, 2),
    ('V15dreadspecular', 'Readable specular', 0.72, 0, 2),
    ('V15dreadshininess', 'Readable shininess', 0.42, 0, 2),
    ('V15dbottomfill', 'Bottom fill light', 1.05, 0, 5),
    ('V15dbackfill', 'Back switch fill', 1.45, 0, 5),
    ('V15drimfill', 'Rim fill', 1.25, 0, 5),
    ('V15dsubdivthin', 'Subdivide thin letters', 1, 0, 1),
    ('V15dsubdivall', 'Subdivide all letters', 0, 0, 1),
    ('V15dsubdivlevel', 'Subdivision level', 1, 0, 3),
    ('V15dframefix', 'Safe framing fix', 1, 0, 1),
    ('V15dviewscale', 'Safe view scale', 0.092, 0.02, 1),
    ('V15dlettersizemax', 'Safe letter size max', 1.22, 0.1, 5),
    ('V15dheightfrontmax', 'Safe height max front', 3.65, 0.1, 8),
    ('V15dheightamountmax', 'Safe height amount max', 1.35, 0, 4),
    ('V15dcurvemaxangle', 'Safe curve max angle', 72, 10, 120),
    ('V15dswitchthreshold', 'Switch threshold', 0, -0.5, 0.5),
    ('V15dcookrate', 'Cook rate', 1, 1, 12),
    ('V15dtextlod', 'Text LOD', 0.10, 0, 1),
    ('V15drenderx', 'Render X', 640, 160, 1920),
    ('V15drendery', 'Render Y', 360, 90, 1080),
]:
    ensure_float(*a)

# Apply default controls.
defaults = {
    'V15dreadambient': 0.52,
    'V15dreademission': 0.34,
    'V15dbottomfill': 1.05,
    'V15dbackfill': 1.45,
    'V15drimfill': 1.25,
    'V15dsubdivthin': 1,
    'V15dsubdivall': 0,
    'V15dsubdivlevel': 1,
    'V15dframefix': 1,
    'V15dviewscale': 0.092,
    'V15dlettersizemax': 1.22,
    'V15dheightfrontmax': 3.65,
    'V15dheightamountmax': 1.35,
    'V15dcurvemaxangle': 72,
    'V15dswitchthreshold': 0,
    'V15dcookrate': 1,
    'V15dtextlod': 0.10,
    'V15drenderx': 640,
    'V15drendery': 360,
}
for n, v in defaults.items():
    p = fp(root, n)
    if p is not None:
        try: p.val = v
        except Exception: pass

# Gentle safety clamps for the extreme stretch/cropping situation.
if fp(root, 'V15dframefix') is not None and root.par.V15dframefix.eval() > 0.5:
    pv = fp(root, 'Viewscale')
    pt = fp(root, 'V15dviewscale')
    if pv is not None and pt is not None:
        try:
            if float(pv.eval()) > float(pt.eval()):
                print('SAFE Viewscale', pv.eval(), '->', pt.eval())
                pv.val = float(pt.eval())
        except Exception:
            pass
    clamp_param('Lettersize', hi=float(fp(root, 'V15dlettersizemax').eval()))
    clamp_param('Heightstretchmaxfront', hi=float(fp(root, 'V15dheightfrontmax').eval()))
    clamp_param('Heightstretchamount', hi=float(fp(root, 'V15dheightamountmax').eval()))
    clamp_param('Curvemaxangle', hi=float(fp(root, 'V15dcurvemaxangle').eval()))

for n, v in [
    ('Backmirroractive', 1),
    ('Backmirroraxis', 0),
    ('Backmirrorthreshold', fp(root, 'V15dswitchthreshold').eval() if fp(root, 'V15dswitchthreshold') else 0),
    ('Backmirrorinvert', 0),
    ('Curvecookactive', 1),
    ('Curvecookrate', fp(root, 'V15dcookrate').eval() if fp(root, 'V15dcookrate') else 1),
    ('Renderresx', fp(root, 'V15drenderx').eval() if fp(root, 'V15drenderx') else 640),
    ('Renderresy', fp(root, 'V15drendery').eval() if fp(root, 'V15drendery') else 360),
]:
    p = fp(root, n)
    if p is not None:
        try: p.val = v
        except Exception: pass

# -------------------------------------------------------------------------
# Readable material, no texture/normal/bump
# -------------------------------------------------------------------------
mat = opget(root, ['phongMAT'], 'mat_letters_readable_v15d')
if mat is None:
    raise Exception('Cannot create mat_letters_readable_v15d')

setv(mat, ['diffuser'], 0.96, ['diffuse r'])
setv(mat, ['diffuseg'], 0.88, ['diffuse g'])
setv(mat, ['diffuseb'], 1.00, ['diffuse b'])
sete(mat, ['ambientr'], '0.96 * ' + pexpr('V15dreadambient', 0.52), ['ambient r'])
sete(mat, ['ambientg'], '0.88 * ' + pexpr('V15dreadambient', 0.52), ['ambient g'])
sete(mat, ['ambientb'], '1.00 * ' + pexpr('V15dreadambient', 0.52), ['ambient b'])
sete(mat, ['emitr'], '0.96 * ' + pexpr('V15dreademission', 0.34), ['emit r', 'emission r'])
sete(mat, ['emitg'], '0.88 * ' + pexpr('V15dreademission', 0.34), ['emit g', 'emission g'])
sete(mat, ['emitb'], '1.00 * ' + pexpr('V15dreademission', 0.34), ['emit b', 'emission b'])
sete(mat, ['specularr'], pexpr('V15dreadspecular', 0.72), ['specular r'])
sete(mat, ['specularg'], pexpr('V15dreadspecular', 0.72), ['specular g'])
sete(mat, ['specularb'], pexpr('V15dreadspecular', 0.72), ['specular b'])
sete(mat, ['shininess'], pexpr('V15dreadshininess', 0.42), ['shininess'])
sete(mat, ['constantr'], '0.06', ['constant r'])
sete(mat, ['constantg'], '0.055', ['constant g'])
sete(mat, ['constantb'], '0.07', ['constant b'])
setv(mat, ['alphafront'], 1, ['alpha front', 'opacity', 'alpha'])
setv(mat, ['alphaside'], 1, ['alpha side'])
setv(mat, ['blending'], False, ['blend'])
setv(mat, ['depthwriting'], True, ['depth writing'])
setv(mat, ['cullface'], 'neither', ['cull'])

for s in ['colormap', 'colormap1', 'colormaptop', 'normalmap', 'bumpmap', 'normalmap1', 'bumpmap1', 'normalmaptop', 'bumpmaptop']:
    p = fp(mat, s)
    if p is not None:
        try: p.val = ''
        except Exception: pass

# -------------------------------------------------------------------------
# Callback
# -------------------------------------------------------------------------
callback_template = """
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
            scriptOp.addWarning('V15D readable deform failed: ' + repr(e))
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

def assign_cb(script_sop, cb):
    ok = False
    for pn in ['callbacks', 'callbacksdat', 'callbackdat', 'dat', 'script']:
        p = fp(script_sop, pn)
        if p is not None:
            try:
                p.val = cb.path
                ok = True
                break
            except Exception:
                pass
    try:
        for d in script_sop.docked:
            if d.family == 'DAT':
                d.text = cb.text
                ok = True
    except Exception:
        pass
    return ok

force_expr = "int(absTime.frame / max(1, int(" + pexpr('V15dcookrate', 1) + "))) if " + pexpr('Curvecookactive', 1) + " > 0.5 else 0"

# -------------------------------------------------------------------------
# Letter chain: Text -> optional Subdivide for I -> bend_letter_v09
# -------------------------------------------------------------------------
letter_paths = []
rows = []
thin_indices = set([i for i, c in enumerate(WORD) if c in ['I', 'L']])

for i, ch in enumerate(WORD):
    geo = root.op('letter_%02d_%s' % (i, ch))
    if geo is None:
        print('WARNING missing letter', i, ch)
        continue

    for pn, vv in [('tx',0),('ty',0),('tz',0),('rx',0),('ry',0),('rz',0),('sx',1),('sy',1),('sz',1)]:
        setv(geo, [pn], vv)
    flag(geo, 'display', True)
    flag(geo, 'render', True)
    setv(geo, ['material', 'mat'], mat.path)

    text = None
    for c in geo.children:
        if c.family == 'SOP' and c.name.startswith('text_'):
            text = c
            break
    if text is None:
        print('WARNING no text SOP for', geo.path)
        continue

    setv(text, ['text'], ch)
    sete(text, ['levelofdetail'], pexpr('V15dtextlod', 0.10), ['lod', 'level of detail'])
    setv(text, ['output'], 'polygons', ['output'])

    source = text
    subpath = 'none'
    use_sub = False
    if fp(root, 'V15dsubdivall') is not None and root.par.V15dsubdivall.eval() > 0.5:
        use_sub = True
    if i in thin_indices and fp(root, 'V15dsubdivthin') is not None and root.par.V15dsubdivthin.eval() > 0.5:
        use_sub = True

    if use_sub:
        sub = geo.op('subdivide_readability_v15d')
        if sub is None:
            sub = opget(geo, ['subdivideSOP'], 'subdivide_readability_v15d')
        if sub is not None:
            sub.nodeX = text.nodeX + 140
            sub.nodeY = text.nodeY
            conn(text, sub)
            expr_level = "int(" + pexpr('V15dsubdivlevel', 1) + ")"
            sete(sub, ['iterations'], expr_level, ['iteration'])
            sete(sub, ['divisions'], expr_level, ['division'])
            sete(sub, ['level'], expr_level, ['level'])
            setv(sub, ['smooth'], False, ['smooth'])
            source = sub
            subpath = sub.path
        else:
            div = geo.op('divide_readability_v15d')
            if div is None:
                div = opget(geo, ['divideSOP'], 'divide_readability_v15d')
            if div is not None:
                div.nodeX = text.nodeX + 140
                div.nodeY = text.nodeY
                conn(text, div)
                setv(div, ['computenormals'], True, ['normal'])
                source = div
                subpath = div.path

    deform = geo.op('bend_letter_v09')
    if deform is None:
        deform = opget(geo, ['scriptSOP'], 'bend_letter_v09')
    if deform is None:
        continue

    deform.nodeX = text.nodeX + 330
    deform.nodeY = text.nodeY
    conn(source, deform)

    cb = geo.op('bend_letter_v09_callbacks')
    if cb is None:
        cb = geo.create('textDAT', 'bend_letter_v09_callbacks')
    cb.text = callback_template.replace('__LETTER_INDEX__', str(i))
    assign_cb(deform, cb)

    p = fp(deform, 'Forcecook')
    if p is None:
        pg = deform.appendCustomPage('V15D')
        p = pg.appendFloat('Forcecook', label='Force cook frame')[0]
    try: p.expr = force_expr
    except Exception: pass

    for c in geo.children:
        if c.family == 'SOP':
            flag(c, 'display', False)
            flag(c, 'render', False)
    flag(deform, 'display', True)
    flag(deform, 'render', True)

    try:
        text.cook(force=True)
        if source is not text:
            source.cook(force=True)
        deform.cook(force=True)
    except Exception:
        pass

    letter_paths.append(geo.path)
    rows.append([ch, count_pts(text), subpath, count_pts(source), count_pts(deform), deform.path])

# -------------------------------------------------------------------------
# Tube and lighting
# -------------------------------------------------------------------------
tube_paths = []
surface = root.op('helix_tube_surface_v06')
if surface is not None:
    flag(surface, 'display', False)
    flag(surface, 'render', False)

wire = root.op('helix_tube_wire_v06')
if wire is not None:
    flag(wire, 'display', True)
    flag(wire, 'render', True)
    for pn in ['tx','ty','tz','rx','ry','rz']:
        mapn = {'tx':'Viewtx','ty':'Viewty','tz':'Viewtz','rx':'Viewrotx','ry':'Viewroty','rz':'Viewrotz'}[pn]
        sete(wire, [pn], pexpr(mapn, 0 if pn!='tz' else -3.97))
    for pn in ['sx','sy','sz']:
        sete(wire, [pn], pexpr('Viewscale', 0.1))
    for c in wire.children:
        if c.family == 'SOP':
            setv(c, ['rows'], 3, ['rows'])
            setv(c, ['cols'], 18, ['cols', 'columns'])
            flag(c, 'display', True)
            flag(c, 'render', True)
    tube_paths.append(wire.path)

def light(name, x,y,z, r,g,b, dim_expr_or_val):
    l = root.op(name)
    if l is None:
        l = opget(root, ['lightCOMP'], name)
    if l is None:
        return None
    setv(l, ['tx'], x); setv(l, ['ty'], y); setv(l, ['tz'], z)
    setv(l, ['lightcolorr'], r); setv(l, ['lightcolorg'], g); setv(l, ['lightcolorb'], b)
    if isinstance(dim_expr_or_val, str):
        sete(l, ['dimmer'], dim_expr_or_val, ['dimmer', 'intensity'])
    else:
        setv(l, ['dimmer'], dim_expr_or_val, ['dimmer', 'intensity'])
    return l

key = light('light_key', 2.6, 3.4, 5.3, 1.00, 0.92, 0.84, 1.25)
fill = light('light_fill', -3.6, -1.8, 4.4, 0.50, 0.66, 1.00, 0.70)
rim = light('light_rim_v15d', -3.8, 2.8, -3.4, 0.62, 0.78, 1.00, pexpr('V15drimfill', 1.25))
bottom = light('light_bottom_read_v15d', 0.0, -3.0, 3.8, 0.88, 0.72, 1.00, pexpr('V15dbottomfill', 1.05))
back = light('light_back_switch_read_v15d', 0.0, 1.2, -4.2, 0.70, 0.86, 1.00, pexpr('V15dbackfill', 1.45))
spark = root.op('light_sparkle_v15')
if spark is not None:
    setv(spark, ['dimmer'], 0.0, ['dimmer', 'intensity'])

light_paths = [l.path for l in [key, fill, rim, bottom, back] if l is not None]

# -------------------------------------------------------------------------
# Render
# -------------------------------------------------------------------------
render = root.op('render1')
if render is None:
    render = opget(root, ['renderTOP'], 'render1')

cam = root.op('cam1')
if cam is not None:
    setv(cam, ['lookat'], '')
    setv(cam, ['tx'], 0); setv(cam, ['ty'], 0)
    sete(cam, ['tz'], pexpr('Cameradistance', 7.2))
    setv(cam, ['rx'], 0); setv(cam, ['ry'], 0); setv(cam, ['rz'], 0)

if render is not None:
    if cam is not None: setv(render, ['camera', 'cameras'], cam.path)
    setv(render, ['geometry', 'geo', 'geometries'], ' '.join(letter_paths + tube_paths), silent=False)
    setv(render, ['lights', 'light'], ' '.join(light_paths))
    sete(render, ['resx', 'w'], "int(" + pexpr('V15drenderx', 640) + ")", ['width','resolution x'])
    sete(render, ['resy', 'h'], "int(" + pexpr('V15drendery', 360) + ")", ['height','resolution y'])
    setv(render, ['bgcolorr'], 0.012); setv(render, ['bgcolorg'], 0.014); setv(render, ['bgcolorb'], 0.026); setv(render, ['bgcolora'], 1.0)
    try: render.cook(force=True)
    except Exception: pass

out = root.op('OUT_RENDER_VIEW_THIS')
if out is None:
    out = opget(root, ['nullTOP'], 'OUT_RENDER_VIEW_THIS')
if out is not None and render is not None:
    try: out.inputConnectors[0].connect(render)
    except Exception: pass
    flag(out, 'viewer', True)
    try: out.cook(force=True)
    except Exception: pass

# Debug
debug = root.op('debug_v15d_readability_shape_fix')
if debug is None:
    debug = opget(root, ['tableDAT'], 'debug_v15d_readability_shape_fix')
if debug is not None:
    try:
        debug.clear()
        debug.appendRow(['key', 'value'])
        debug.appendRow(['mode', 'V15D readability + shape fix'])
        debug.appendRow(['material', mat.path])
        debug.appendRow(['letters', len(letter_paths)])
        debug.appendRow(['lights', ' '.join(light_paths)])
        debug.appendRow(['render_geometry', ' '.join(letter_paths + tube_paths)])
        debug.appendRow(['open', ROOT_PATH + '/OUT_RENDER_VIEW_THIS'])
        debug.appendRow([])
        debug.appendRow(['letter', 'text_points', 'subdivide_op', 'source_points', 'deform_points', 'deform_path'])
        for r in rows:
            debug.appendRow(r)
    except Exception as e:
        print('WARNING debug failed', e)

try:
    root.layout(root.children)
except Exception:
    pass

print('=' * 72)
print('MORPHOGENESIS DNA V15D READABILITY + SHAPE FIX OK')
print('Open:', ROOT_PATH + '/OUT_RENDER_VIEW_THIS')
print('Debug:', ROOT_PATH + '/debug_v15d_readability_shape_fix')
print('If M/O/R/P/H are still clipped: lower V15dviewscale or V15dlettersizemax.')
print('If I is still too flat: set V15dsubdivall = 1 or V15dsubdivlevel = 2.')
print('If bottom/back letters are still dark: raise V15dreademission, V15dbottomfill, V15dbackfill.')
print('=' * 72)
