# archive du DAT /project1/only_Y (purge du 2026-11-02)
# morphogenesis_dna_td_v15i_Y_ONLY_WITH_BUTTON.py
# TouchDesigner 2025.32460 / Python 3.11
#
# V15I corrective
# À lancer après V15D / V15E / V15F / V15G / V15H.
#
# But:
# - revenir à une rotation locale sur l'axe Y uniquement;
# - ajouter un petit bouton/toggle dans les paramètres du container:
#     /project1/MORPHOGENESIS_DNA_TD > DNA V15I Y BUTTON > V15iyonly
#
# Comportement:
# - V15iyonly = 1 : chaque lettre passe par une rotation Y = 180°
# - V15iyonly = 0 : rotation Y = 0°, donc bypass visuel du pré-flip
#
# Chaîne cible par lettre:
# Text SOP -> (Subdivide optionnel) -> preflip_y_toggle_v15i -> bend_letter_v09
#
# Important:
# - ne touche pas à la logique de déformation autour du tube;
# - ne réactive pas l'extrusion lourde;
# - ne réactive pas les normal maps;
# - masque les anciens preflip de test V15F/V15G/V15H pour éviter les doubles rotations.

ROOT_PATH = '/project1/MORPHOGENESIS_DNA_TD'
WORD = 'MORPHOGENESIS'

root = op(ROOT_PATH)
if root is None:
    raise Exception('Container introuvable: ' + ROOT_PATH)

# -------------------------------------------------------------------------
# Utils
# -------------------------------------------------------------------------
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

def set_flag(o, flag, value):
    try:
        setattr(o, flag, value)
        return True
    except Exception:
        return False

def create_or_get(parent, type_names, name):
    existing = parent.op(name)
    if existing is not None:
        return existing
    for tn in type_names:
        try:
            o = parent.create(tn, name)
            print('CREATED', o.path, 'type', tn)
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

def ensure_toggle(par_name, label, default=1):
    p = find_par(root, par_name)
    if p is not None:
        try:
            p.val = default
        except Exception:
            pass
        return p

    page = None
    for page_name in ['DNA V15I Y BUTTON', 'DNA V15I Y BUTTON B', 'DNA V15I Y BUTTON C']:
        try:
            page = root.appendCustomPage(page_name)
            break
        except Exception:
            pass

    if page is None:
        print('WARNING cannot create custom page for V15I')
        return None

    # Prefer a real toggle. Fallback to Float if this TD build refuses appendToggle.
    try:
        pars = page.appendToggle(par_name, label=label)
        p = pars[0]
        p.default = default
        p.val = default
        print('ADDED TOGGLE', par_name, '=', default, 'actual:', p.name)
        return p
    except Exception as e:
        print('appendToggle failed, fallback to Float:', e)
        try:
            pars = page.appendFloat(par_name, label=label)
            p = pars[0]
            p.default = default
            p.val = default
            p.normMin = 0
            p.normMax = 1
            print('ADDED FLOAT TOGGLE', par_name, '=', default, 'actual:', p.name)
            return p
        except Exception as e2:
            print('WARNING cannot add toggle parameter', par_name, e2)
            return None

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
# 1) Add small toggle button
# -------------------------------------------------------------------------
button_par = ensure_toggle('V15iyonly', 'Y only 180 toggle', 1)
if button_par is None:
    raise Exception('Impossible de créer le bouton/toggle V15iyonly')

# Expression used on every preflip transform.
# Important: use actual parameter name as created by TD.
button_expr = "180 if op('%s').par.%s.eval() > 0.5 else 0" % (ROOT_PATH, button_par.name)

# -------------------------------------------------------------------------
# 2) Per-letter Y-only preflip controlled by button
# -------------------------------------------------------------------------
processed = 0
rows = []

for i, ch in enumerate(WORD):
    geo = root.op('letter_%02d_%s' % (i, ch))
    if geo is None:
        rows.append([ch, 'missing_geo'])
        continue

    text_sop = None
    subdiv_sop = None
    divide_sop = None

    old_preflips = []
    for old_name in [
        'preflip_xy_v15f',
        'preflip_y_v15g',
        'preflip_xy_v15h',
    ]:
        old = geo.op(old_name)
        if old is not None:
            old_preflips.append(old)

    for c in geo.children:
        if c.family != 'SOP':
            continue
        if c.name.startswith('text_'):
            text_sop = c
        elif c.name == 'subdivide_readability_v15d':
            subdiv_sop = c
        elif c.name == 'divide_readability_v15d':
            divide_sop = c

    source = subdiv_sop or divide_sop or text_sop
    deform = geo.op('bend_letter_v09')

    if source is None or deform is None:
        rows.append([ch, 'missing_source_or_deform'])
        continue

    preflip = geo.op('preflip_y_toggle_v15i')
    if preflip is None:
        preflip = create_or_get(geo, ['xformSOP', 'transformSOP'], 'preflip_y_toggle_v15i')

    if preflip is None:
        rows.append([ch, 'cannot_create_preflip'])
        continue

    try:
        preflip.nodeX = source.nodeX + 140
        preflip.nodeY = source.nodeY
    except Exception:
        pass

    connect(source, preflip, 0)

    # Neutral transform except controlled Y rotation.
    set_val(preflip, ['tx'], 0, verbose=False)
    set_val(preflip, ['ty'], 0, verbose=False)
    set_val(preflip, ['tz'], 0, verbose=False)

    set_val(preflip, ['rx'], 0, keywords=['rotate x', 'x rotate'], verbose=True)
    set_expr(preflip, ['ry'], button_expr, keywords=['rotate y', 'y rotate'], verbose=True)
    set_val(preflip, ['rz'], 0, keywords=['rotate z', 'z rotate'], verbose=False)

    set_val(preflip, ['sx'], 1, verbose=False)
    set_val(preflip, ['sy'], 1, verbose=False)
    set_val(preflip, ['sz'], 1, verbose=False)

    set_val(preflip, ['px'], 0, keywords=['pivot x'], verbose=False)
    set_val(preflip, ['py'], 0, keywords=['pivot y'], verbose=False)
    set_val(preflip, ['pz'], 0, keywords=['pivot z'], verbose=False)

    connect(preflip, deform, 0)

    # Hide old test preflips so they do not confuse display/render.
    for old in old_preflips:
        set_flag(old, 'display', False)
        set_flag(old, 'render', False)

    # Display only the final deformation SOP.
    for c in geo.children:
        if c.family == 'SOP':
            set_flag(c, 'display', False)
            set_flag(c, 'render', False)

    set_flag(deform, 'display', True)
    set_flag(deform, 'render', True)

    try:
        source.cook(force=True)
        preflip.cook(force=True)
        deform.cook(force=True)
    except Exception:
        pass

    processed += 1
    rows.append([ch, source.path, preflip.path, deform.path, count_points(source), count_points(deform)])

# -------------------------------------------------------------------------
# 3) Force render/output recook
# -------------------------------------------------------------------------
for name in ['render1', 'OUT_RENDER_VIEW_THIS']:
    o = root.op(name)
    if o is not None:
        try:
            o.cook(force=True)
        except Exception:
            pass

# -------------------------------------------------------------------------
# 4) Debug
# -------------------------------------------------------------------------
debug = root.op('debug_v15i_y_only_button')
if debug is None:
    try:
        debug = root.create('tableDAT', 'debug_v15i_y_only_button')
    except Exception:
        debug = None

if debug is not None:
    try:
        debug.clear()
        debug.appendRow(['key', 'value'])
        debug.appendRow(['mode', 'V15I Y-only 180 with toggle button'])
        debug.appendRow(['toggle_parameter', ROOT_PATH + '.par.' + button_par.name])
        debug.appendRow(['toggle_value', button_par.eval()])
        debug.appendRow(['ry_expression', button_expr])
        debug.appendRow(['letters_processed', processed])
        debug.appendRow(['open', ROOT_PATH + '/OUT_RENDER_VIEW_THIS'])
        debug.appendRow([])
        debug.appendRow(['letter', 'source', 'preflip_y_toggle', 'deform', 'source_points', 'deform_points'])
        for r in rows:
            debug.appendRow(r)
    except Exception:
        pass

print('=' * 72)
print('MORPHOGENESIS DNA V15I Y-ONLY 180 WITH BUTTON OK')
print('Toggle button:', ROOT_PATH + '.par.' + button_par.name)
print('  1 = Y rotation 180°')
print('  0 = no local preflip')
print('Open:', ROOT_PATH + '/OUT_RENDER_VIEW_THIS')
print('Debug:', ROOT_PATH + '/debug_v15i_y_only_button')
print('=' * 72)
