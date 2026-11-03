# archive du DAT /project1/only_x (purge du 2026-11-02)
# morphogenesis_dna_td_v15j_X_Y_TOGGLE_BUTTONS.py
# TouchDesigner 2025.32460 / Python 3.11
#
# V15J corrective
# À lancer après V15I.
#
# But:
# - ajouter un bouton/toggle "only X" pour une rotation locale de 180° sur X;
# - conserver le bouton/toggle "Y only" déjà créé en V15I;
# - contrôler proprement les deux axes dans un seul Transform SOP:
#     preflip_xy_toggle_v15j
#
# Paramètres créés / utilisés:
# /project1/MORPHOGENESIS_DNA_TD > DNA V15J XY BUTTONS
#   V15ixonly : 1 = rotate X 180°, 0 = rotate X 0°
#   V15iyonly : 1 = rotate Y 180°, 0 = rotate Y 0°
#
# Résultat:
# - X=1, Y=0 : rotation X seulement
# - X=0, Y=1 : rotation Y seulement
# - X=1, Y=1 : rotation X + Y
# - X=0, Y=0 : pas de pré-rotation
#
# Chaîne cible par lettre:
# Text SOP -> (Subdivide optionnel) -> preflip_xy_toggle_v15j -> bend_letter_v09
#
# Important:
# - masque les anciens preflips de test pour éviter les doubles rotations;
# - ne change pas la logique de déformation autour du tube;
# - ne réactive pas l'extrusion lourde;
# - ne réactive pas normal map / bump map.

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

def ensure_toggle(par_name, label, default=0):
    p = find_par(root, par_name)
    if p is not None:
        try:
            p.val = default
        except Exception:
            pass
        return p

    page = None
    for page_name in ['DNA V15J XY BUTTONS', 'DNA V15J XY BUTTONS B', 'DNA V15J XY BUTTONS C']:
        try:
            page = root.appendCustomPage(page_name)
            break
        except Exception:
            pass

    if page is None:
        print('WARNING cannot create custom page for V15J')
        return None

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
# 1) Add / preserve buttons
# -------------------------------------------------------------------------
x_par = ensure_toggle('V15ixonly', 'X only 180 toggle', 1)
y_par = find_par(root, 'V15iyonly')
if y_par is None:
    y_par = ensure_toggle('V15iyonly', 'Y only 180 toggle', 0)
else:
    # Preserve current V15I setting instead of forcing it.
    print('FOUND existing Y toggle:', ROOT_PATH + '.par.' + y_par.name, '=', y_par.eval())

if x_par is None or y_par is None:
    raise Exception('Impossible de créer ou trouver les toggles V15ixonly / V15iyonly')

x_expr = "180 if op('%s').par.%s.eval() > 0.5 else 0" % (ROOT_PATH, x_par.name)
y_expr = "180 if op('%s').par.%s.eval() > 0.5 else 0" % (ROOT_PATH, y_par.name)

# -------------------------------------------------------------------------
# 2) Per-letter controlled preflip
# -------------------------------------------------------------------------
processed = 0
rows = []

old_preflip_names = [
    'preflip_xy_v15f',
    'preflip_y_v15g',
    'preflip_xy_v15h',
    'preflip_y_toggle_v15i',
]

for i, ch in enumerate(WORD):
    geo = root.op('letter_%02d_%s' % (i, ch))
    if geo is None:
        rows.append([ch, 'missing_geo'])
        continue

    text_sop = None
    subdiv_sop = None
    divide_sop = None

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

    preflip = geo.op('preflip_xy_toggle_v15j')
    if preflip is None:
        preflip = create_or_get(geo, ['xformSOP', 'transformSOP'], 'preflip_xy_toggle_v15j')

    if preflip is None:
        rows.append([ch, 'cannot_create_preflip'])
        continue

    try:
        preflip.nodeX = source.nodeX + 140
        preflip.nodeY = source.nodeY
    except Exception:
        pass

    connect(source, preflip, 0)

    # Neutral local transform except toggle-controlled X/Y rotations.
    set_val(preflip, ['tx'], 0, verbose=False)
    set_val(preflip, ['ty'], 0, verbose=False)
    set_val(preflip, ['tz'], 0, verbose=False)

    set_expr(preflip, ['rx'], x_expr, keywords=['rotate x', 'x rotate'], verbose=True)
    set_expr(preflip, ['ry'], y_expr, keywords=['rotate y', 'y rotate'], verbose=True)
    set_val(preflip, ['rz'], 0, keywords=['rotate z', 'z rotate'], verbose=False)

    set_val(preflip, ['sx'], 1, verbose=False)
    set_val(preflip, ['sy'], 1, verbose=False)
    set_val(preflip, ['sz'], 1, verbose=False)

    set_val(preflip, ['px'], 0, keywords=['pivot x'], verbose=False)
    set_val(preflip, ['py'], 0, keywords=['pivot y'], verbose=False)
    set_val(preflip, ['pz'], 0, keywords=['pivot z'], verbose=False)

    connect(preflip, deform, 0)

    # Hide all old preflip tests and all intermediate SOPs.
    for old_name in old_preflip_names:
        old = geo.op(old_name)
        if old is not None:
            set_flag(old, 'display', False)
            set_flag(old, 'render', False)

    for c in geo.children:
        if c.family == 'SOP':
            set_flag(c, 'display', False)
            set_flag(c, 'render', False)

    # Display/render only the final deformation.
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
debug = root.op('debug_v15j_x_y_toggle_buttons')
if debug is None:
    try:
        debug = root.create('tableDAT', 'debug_v15j_x_y_toggle_buttons')
    except Exception:
        debug = None

if debug is not None:
    try:
        debug.clear()
        debug.appendRow(['key', 'value'])
        debug.appendRow(['mode', 'V15J X/Y 180 toggles'])
        debug.appendRow(['x_toggle_parameter', ROOT_PATH + '.par.' + x_par.name])
        debug.appendRow(['x_toggle_value', x_par.eval()])
        debug.appendRow(['y_toggle_parameter', ROOT_PATH + '.par.' + y_par.name])
        debug.appendRow(['y_toggle_value', y_par.eval()])
        debug.appendRow(['rx_expression', x_expr])
        debug.appendRow(['ry_expression', y_expr])
        debug.appendRow(['letters_processed', processed])
        debug.appendRow(['open', ROOT_PATH + '/OUT_RENDER_VIEW_THIS'])
        debug.appendRow([])
        debug.appendRow(['letter', 'source', 'preflip_xy_toggle', 'deform', 'source_points', 'deform_points'])
        for r in rows:
            debug.appendRow(r)
    except Exception:
        pass

print('=' * 72)
print('MORPHOGENESIS DNA V15J X/Y 180 TOGGLE BUTTONS OK')
print('Buttons:')
print('  X:', ROOT_PATH + '.par.' + x_par.name, '=> 1 means rotate X 180°')
print('  Y:', ROOT_PATH + '.par.' + y_par.name, '=> 1 means rotate Y 180°')
print('Combinations:')
print('  X=1 Y=0 : X only')
print('  X=0 Y=1 : Y only')
print('  X=1 Y=1 : X+Y')
print('  X=0 Y=0 : no local preflip')
print('Open:', ROOT_PATH + '/OUT_RENDER_VIEW_THIS')
print('Debug:', ROOT_PATH + '/debug_v15j_x_y_toggle_buttons')
print('=' * 72)
