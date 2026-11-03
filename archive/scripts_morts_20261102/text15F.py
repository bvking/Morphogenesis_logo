# archive du DAT /project1/text15F (purge du 2026-11-02)
# morphogenesis_dna_td_v15f_ROTATE_LETTERS_XY_180.py
# TouchDesigner 2025.32460 / Python 3.11
#
# V15F corrective
# À lancer après V15D / V15E.
#
# But:
# - tourner chaque lettre de 180° sur son centre
# - sur l'axe X
# - et sur l'axe Y
# afin de retrouver l'orientation attendue au moment du switch.
#
# Méthode:
# - on insère un Transform SOP avant bend_letter_v09
# - ce Transform SOP pivote la géométrie locale de la lettre
# - ainsi, on ne touche pas à la logique de placement hélicoïdal
# - on conserve la déformation autour du tube
#
# Chaîne cible par lettre:
# Text SOP -> (Subdivide optionnel) -> preflip_xy_v15f -> bend_letter_v09

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

rotated_count = 0
rows = []

for i, ch in enumerate(WORD):
    geo = root.op('letter_%02d_%s' % (i, ch))
    if geo is None:
        continue

    # locate main source SOP before bend
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

    preflip = geo.op('preflip_xy_v15f')
    if preflip is None:
        preflip = create_or_get(geo, ['xformSOP', 'transformSOP'], 'preflip_xy_v15f')

    if preflip is None:
        rows.append([ch, 'cannot_create_transform'])
        continue

    # Layout position
    try:
        preflip.nodeX = source.nodeX + 140
        preflip.nodeY = source.nodeY
    except Exception:
        pass

    connect(source, preflip, 0)

    # Rotate on local center. TouchDesigner Transform SOP usually uses pivot + rotate parms.
    # We keep pivot at local center/origin, since source letter geometry is centered locally.
    set_val(preflip, ['tx'], 0, verbose=False)
    set_val(preflip, ['ty'], 0, verbose=False)
    set_val(preflip, ['tz'], 0, verbose=False)

    # Rotation 180 around X and Y
    set_val(preflip, ['rx'], 180, keywords=['rotate x', 'x rotate'], verbose=True)
    set_val(preflip, ['ry'], 180, keywords=['rotate y', 'y rotate'], verbose=True)
    set_val(preflip, ['rz'], 0, keywords=['rotate z', 'z rotate'], verbose=False)

    # Neutral scale and pivot
    set_val(preflip, ['sx'], 1, verbose=False)
    set_val(preflip, ['sy'], 1, verbose=False)
    set_val(preflip, ['sz'], 1, verbose=False)

    set_val(preflip, ['px'], 0, keywords=['pivot x'], verbose=False)
    set_val(preflip, ['py'], 0, keywords=['pivot y'], verbose=False)
    set_val(preflip, ['pz'], 0, keywords=['pivot z'], verbose=False)

    # reconnect deform input to the preflip sop
    connect(preflip, deform, 0)

    # show only deform
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

    rotated_count += 1
    rows.append([ch, source.path, preflip.path, deform.path])

# Force recook
for name in ['render1', 'OUT_RENDER_VIEW_THIS']:
    o = root.op(name)
    if o is not None:
        try:
            o.cook(force=True)
        except Exception:
            pass

debug = root.op('debug_v15f_rotate_letters_xy_180')
if debug is None:
    try:
        debug = root.create('tableDAT', 'debug_v15f_rotate_letters_xy_180')
    except Exception:
        debug = None

if debug is not None:
    try:
        debug.clear()
        debug.appendRow(['key', 'value'])
        debug.appendRow(['mode', 'V15F rotate letters 180 on X and Y'])
        debug.appendRow(['letters_processed', rotated_count])
        debug.appendRow(['open', ROOT_PATH + '/OUT_RENDER_VIEW_THIS'])
        debug.appendRow([])
        debug.appendRow(['letter', 'source', 'preflip', 'deform'])
        for r in rows:
            debug.appendRow(r)
    except Exception:
        pass

print('=' * 72)
print('MORPHOGENESIS DNA V15F ROTATE LETTERS XY 180 OK')
print('Each letter now passes through preflip_xy_v15f before bend_letter_v09.')
print('Open:', ROOT_PATH + '/OUT_RENDER_VIEW_THIS')
print('Debug:', ROOT_PATH + '/debug_v15f_rotate_letters_xy_180')
print('=' * 72)
