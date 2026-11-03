# archive du DAT /project1/high_reso (purge du 2026-11-02)
# morphogenesis_dna_td_v15l_STATIC_LOGO_FROM_V15J.py
# TouchDesigner 2025.32460 / Python 3.11
#
# V15L STATIC LOGO
# À lancer comme si on repartait de V15J.
#
# Contexte:
# - La V15K ralentit trop le projet.
# - On ne cherche plus à faire une animation fluide.
# - On cherche maintenant à construire un LOGO statique à partir des lettres.
#
# Objectifs:
# 1) Repartir d'une base V15J propre:
#    Text SOP -> preflip_xy_toggle_v15j -> bend_letter_v09
#    avec les boutons X/Y de V15J conservés.
#
# 2) Bypasser les éléments lourds de V15K/V15L précédents:
#    subdivide_circular_v15k
#    subdivide_thin_bonus_v15l
#    et autres sources lourdes si présentes.
#
# 3) Rendre le logo statique par défaut:
#    Speed = 0
#    Axisrollspeed = 0
#    Curvecookactive = 0
#
# 4) Consommer le moins de CPU par défaut:
#    V15lqualitymode = 0 FAST
#    V15lliveedit = 0
#    Les lettres ne recuisent pas en continu.
#
# 5) Permettre les réglages manuels:
#    - tous les anciens paramètres du container restent utilisables;
#    - pour mettre à jour le logo après un réglage, augmente V15lrefresh;
#    - ou active temporairement V15lliveedit = 1 pendant les réglages.
#
# Nouveau bloc:
# /project1/MORPHOGENESIS_DNA_TD > DNA V15L STATIC LOGO
#
# Contrôles principaux:
# V15lqualitymode : 0 fast / 1 medium / 2 high
# V15llogostatic : 1 = animation arrêtée
# V15lliveedit   : 1 = recook lent pendant les réglages, 0 = aucun recook continu
# V15lrefresh    : incrémenter pour forcer une mise à jour statique
#
# À ouvrir:
# /project1/MORPHOGENESIS_DNA_TD/OUT_RENDER_VIEW_THIS

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

def par_expr(name, default_literal='0'):
    p = find_par(root, name)
    if p is None:
        return str(default_literal)
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

    print('WARNING cannot create', name, 'with', type_names)
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

def ensure_page():
    for page_name in ['DNA V15L STATIC LOGO', 'DNA V15L STATIC LOGO B', 'DNA V15L STATIC LOGO C']:
        try:
            return root.appendCustomPage(page_name)
        except Exception:
            pass
    return None

def ensure_float(par_name, label, default, norm_min=None, norm_max=None):
    p = find_par(root, par_name)
    if p is not None:
        return p
    page = ensure_page()
    if page is None:
        print('WARNING cannot create custom page')
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
        print('WARNING cannot add float', par_name, e)
        return None

def ensure_toggle(par_name, label, default=0):
    p = find_par(root, par_name)
    if p is not None:
        return p
    page = ensure_page()
    if page is None:
        print('WARNING cannot create custom page')
        return None
    try:
        p = page.appendToggle(par_name, label=label)[0]
        p.default = default
        p.val = default
        print('ADDED TOGGLE', par_name, '=', default, 'actual:', p.name)
        return p
    except Exception:
        try:
            p = page.appendFloat(par_name, label=label)[0]
            p.default = default
            p.val = default
            p.normMin = 0
            p.normMax = 1
            print('ADDED FLOAT TOGGLE', par_name, '=', default, 'actual:', p.name)
            return p
        except Exception as e:
            print('WARNING cannot add toggle', par_name, e)
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
# 1) Static logo parameters
# -------------------------------------------------------------------------
p_quality = ensure_float('V15lqualitymode', 'Quality mode 0 fast 1 medium 2 high', 0, 0, 2)
p_static = ensure_toggle('V15llogostatic', 'Static logo mode', 1)
p_live = ensure_toggle('V15lliveedit', 'Live edit recook', 0)
p_refresh = ensure_float('V15lrefresh', 'Manual refresh value', 1, 0, 9999)
p_cookrate = ensure_float('V15lcookrate', 'Live edit cook rate', 12, 1, 120)

p_fast_lod = ensure_float('V15lfasttextlod', 'Fast Text LOD', 0.06, 0.01, 1.0)
p_med_lod = ensure_float('V15lmediumtextlod', 'Medium Text LOD', 0.12, 0.01, 1.0)
p_high_lod = ensure_float('V15lhightextlod', 'High Text LOD', 0.22, 0.01, 1.0)

p_fast_sub = ensure_float('V15lfastsubdiv', 'Fast letter subdiv', 0, 0, 4)
p_med_sub = ensure_float('V15lmediumsubdiv', 'Medium letter subdiv', 1, 0, 4)
p_high_sub = ensure_float('V15lhighsubdiv', 'High letter subdiv', 2, 0, 4)

p_thin_bonus = ensure_float('V15lthinbonus', 'Thin letter bonus', 0, 0, 3)
p_hard_bonus = ensure_float('V15lhardbonus', 'Hard letter bonus', 0, 0, 3)

p_fast_cols = ensure_float('V15lfasttubecols', 'Fast tube cols', 18, 8, 128)
p_med_cols = ensure_float('V15lmediumtubecols', 'Medium tube cols', 28, 8, 128)
p_high_cols = ensure_float('V15lhightubecols', 'High tube cols', 42, 8, 160)

p_fast_rows = ensure_float('V15lfasttuberows', 'Fast tube rows', 3, 2, 64)
p_med_rows = ensure_float('V15lmediumtuberows', 'Medium tube rows', 5, 2, 64)
p_high_rows = ensure_float('V15lhightuberows', 'High tube rows', 8, 2, 96)

p_render_auto = ensure_toggle('V15lautorenderres', 'Auto render res by quality', 0)
p_fast_rx = ensure_float('V15lfastresx', 'Fast render X', 480, 160, 1920)
p_fast_ry = ensure_float('V15lfastresy', 'Fast render Y', 270, 90, 1080)
p_med_rx = ensure_float('V15lmediumresx', 'Medium render X', 640, 160, 1920)
p_med_ry = ensure_float('V15lmediumresy', 'Medium render Y', 360, 90, 1080)
p_high_rx = ensure_float('V15lhighresx', 'High render X', 960, 160, 1920)
p_high_ry = ensure_float('V15lhighresy', 'High render Y', 540, 90, 1080)

if p_quality is None or p_static is None or p_live is None or p_refresh is None:
    raise Exception('Impossible de créer les paramètres principaux V15L')

# Default: lowest CPU.
try: p_quality.val = 0
except Exception: pass
try: p_static.val = 1
except Exception: pass
try: p_live.val = 0
except Exception: pass
try: p_refresh.val = 1
except Exception: pass

# Preserve V15J X/Y buttons if present, create if missing.
p_x = find_par(root, 'V15ixonly')
if p_x is None:
    p_x = ensure_toggle('V15ixonly', 'X only 180 toggle', 0)

p_y = find_par(root, 'V15iyonly')
if p_y is None:
    p_y = ensure_toggle('V15iyonly', 'Y only 180 toggle', 1)

# -------------------------------------------------------------------------
# 2) Stop animation by default, but preserve user-adjustable visual params
# -------------------------------------------------------------------------
if p_static.eval() > 0.5:
    for name, value in [
        ('Speed', 0),
        ('Axisrollspeed', 0),
        ('Curvecookactive', 0),
    ]:
        p = find_par(root, name)
        if p is not None:
            try:
                p.val = value
                print('STATIC SET', name, '=', value)
            except Exception:
                pass

# Quality expressions
mode_expr = "int(round(op('%s').par.%s.eval()))" % (ROOT_PATH, p_quality.name)
lod_expr = (
    "(op('{r}').par.{fl}.eval() if {m} <= 0 else "
    "(op('{r}').par.{ml}.eval() if {m} == 1 else op('{r}').par.{hl}.eval()))"
).format(r=ROOT_PATH, fl=p_fast_lod.name, ml=p_med_lod.name, hl=p_high_lod.name, m=mode_expr)

subdiv_expr_base = (
    "(int(op('{r}').par.{fs}.eval()) if {m} <= 0 else "
    "(int(op('{r}').par.{ms}.eval()) if {m} == 1 else int(op('{r}').par.{hs}.eval())))"
).format(r=ROOT_PATH, fs=p_fast_sub.name, ms=p_med_sub.name, hs=p_high_sub.name, m=mode_expr)

tube_cols_expr = (
    "(int(op('{r}').par.{fc}.eval()) if {m} <= 0 else "
    "(int(op('{r}').par.{mc}.eval()) if {m} == 1 else int(op('{r}').par.{hc}.eval())))"
).format(r=ROOT_PATH, fc=p_fast_cols.name, mc=p_med_cols.name, hc=p_high_cols.name, m=mode_expr)

tube_rows_expr = (
    "(int(op('{r}').par.{fr}.eval()) if {m} <= 0 else "
    "(int(op('{r}').par.{mr}.eval()) if {m} == 1 else int(op('{r}').par.{hr}.eval())))"
).format(r=ROOT_PATH, fr=p_fast_rows.name, mr=p_med_rows.name, hr=p_high_rows.name, m=mode_expr)

render_x_expr = (
    "(int(op('{r}').par.{frx}.eval()) if {m} <= 0 else "
    "(int(op('{r}').par.{mrx}.eval()) if {m} == 1 else int(op('{r}').par.{hrx}.eval())))"
).format(r=ROOT_PATH, frx=p_fast_rx.name, mrx=p_med_rx.name, hrx=p_high_rx.name, m=mode_expr)

render_y_expr = (
    "(int(op('{r}').par.{fry}.eval()) if {m} <= 0 else "
    "(int(op('{r}').par.{mry}.eval()) if {m} == 1 else int(op('{r}').par.{hry}.eval())))"
).format(r=ROOT_PATH, fry=p_fast_ry.name, mry=p_med_ry.name, hry=p_high_ry.name, m=mode_expr)

x_expr = "180 if op('%s').par.%s.eval() > 0.5 else 0" % (ROOT_PATH, p_x.name)
y_expr = "180 if op('%s').par.%s.eval() > 0.5 else 0" % (ROOT_PATH, p_y.name)

# Static recook expression:
# - refresh value gives manual update.
# - live edit mode optionally recooks slowly.
forcecook_expr = (
    "int(op('{r}').par.{refresh}.eval()) + "
    "(int(absTime.frame / max(1, int(op('{r}').par.{rate}.eval()))) "
    "if op('{r}').par.{live}.eval() > 0.5 else 0)"
).format(r=ROOT_PATH, refresh=p_refresh.name, rate=p_cookrate.name, live=p_live.name)

# -------------------------------------------------------------------------
# 3) Restore/bypass V15K heavy nodes and rebuild V15J-style chain
# -------------------------------------------------------------------------
thin_letters = set(['I'])
hard_letters = set(['S', 'N', 'E', 'G', 'O', 'R'])

processed = 0
rows = []

for i, ch in enumerate(WORD):
    geo = root.op('letter_%02d_%s' % (i, ch))
    if geo is None:
        rows.append([ch, 'missing_geo'])
        continue

    # identity geometry comp
    for pname, val in [('tx', 0), ('ty', 0), ('tz', 0), ('rx', 0), ('ry', 0), ('rz', 0), ('sx', 1), ('sy', 1), ('sz', 1)]:
        set_val(geo, [pname], val, verbose=False)
    set_flag(geo, 'display', True)
    set_flag(geo, 'render', True)

    text_sop = None
    for c in geo.children:
        if c.family == 'SOP' and c.name.startswith('text_'):
            text_sop = c
            break

    if text_sop is None:
        rows.append([ch, 'missing_text_sop'])
        continue

    set_val(text_sop, ['text'], ch, verbose=False)
    set_expr(text_sop, ['levelofdetail'], lod_expr, keywords=['lod', 'level of detail'], verbose=False)
    set_val(text_sop, ['output'], 'polygons', keywords=['output'], verbose=False)

    # Lightweight quality subdiv: this replaces V15K and defaults to zero.
    light_sub = geo.op('subdivide_logo_quality_v15l')
    if light_sub is None:
        light_sub = create_or_get(geo, ['subdivideSOP'], 'subdivide_logo_quality_v15l')
    if light_sub is None:
        light_sub = create_or_get(geo, ['divideSOP'], 'subdivide_logo_quality_v15l')

    if light_sub is None:
        source = text_sop
        sub_path = 'none'
        sub_expr = 'none'
    else:
        try:
            light_sub.nodeX = text_sop.nodeX + 130
            light_sub.nodeY = text_sop.nodeY
        except Exception:
            pass
        connect(text_sop, light_sub, 0)

        # Base quality + optional bonuses, but bonuses are zero by default.
        thin_bonus = "int(op('%s').par.%s.eval())" % (ROOT_PATH, p_thin_bonus.name) if ch in thin_letters else "0"
        hard_bonus = "int(op('%s').par.%s.eval())" % (ROOT_PATH, p_hard_bonus.name) if ch in hard_letters else "0"
        sub_expr = "max(0, int(round(%s + %s + %s)))" % (subdiv_expr_base, thin_bonus, hard_bonus)

        set_expr(light_sub, ['iterations'], sub_expr, keywords=['iteration'], verbose=False)
        set_expr(light_sub, ['divisions'], sub_expr, keywords=['division'], verbose=False)
        set_expr(light_sub, ['level'], sub_expr, keywords=['level'], verbose=False)
        set_val(light_sub, ['smooth'], False, keywords=['smooth'], verbose=False)
        set_val(light_sub, ['computenormals'], True, keywords=['normal'], verbose=False)
        set_val(light_sub, ['bricker'], True, keywords=['brick'], verbose=False)

        source = light_sub
        sub_path = light_sub.path

    # Use V15J preflip toggle, create if missing.
    preflip = geo.op('preflip_xy_toggle_v15j')
    if preflip is None:
        preflip = create_or_get(geo, ['xformSOP', 'transformSOP'], 'preflip_xy_toggle_v15j')

    deform = geo.op('bend_letter_v09')
    if deform is None:
        deform = create_or_get(geo, ['scriptSOP'], 'bend_letter_v09')

    if preflip is None or deform is None:
        rows.append([ch, 'missing_preflip_or_deform'])
        continue

    try:
        preflip.nodeX = source.nodeX + 130
        preflip.nodeY = source.nodeY
        deform.nodeX = preflip.nodeX + 150
        deform.nodeY = preflip.nodeY
    except Exception:
        pass

    connect(source, preflip, 0)

    set_val(preflip, ['tx'], 0, verbose=False)
    set_val(preflip, ['ty'], 0, verbose=False)
    set_val(preflip, ['tz'], 0, verbose=False)
    set_expr(preflip, ['rx'], x_expr, keywords=['rotate x', 'x rotate'], verbose=False)
    set_expr(preflip, ['ry'], y_expr, keywords=['rotate y', 'y rotate'], verbose=False)
    set_val(preflip, ['rz'], 0, keywords=['rotate z', 'z rotate'], verbose=False)
    set_val(preflip, ['sx'], 1, verbose=False)
    set_val(preflip, ['sy'], 1, verbose=False)
    set_val(preflip, ['sz'], 1, verbose=False)
    set_val(preflip, ['px'], 0, keywords=['pivot x'], verbose=False)
    set_val(preflip, ['py'], 0, keywords=['pivot y'], verbose=False)
    set_val(preflip, ['pz'], 0, keywords=['pivot z'], verbose=False)

    connect(preflip, deform, 0)

    # Forcecook dependency on manual refresh / optional live edit.
    p_force = find_par(deform, 'Forcecook')
    if p_force is None:
        try:
            page = deform.appendCustomPage('V15L')
            p_force = page.appendFloat('Forcecook', label='Force cook')[0]
        except Exception:
            p_force = None
    if p_force is not None:
        try:
            p_force.expr = forcecook_expr
        except Exception as e:
            print('WARNING cannot set Forcecook on', deform.path, e)

    # Hide heavy V15K/V15L test nodes and old preflips.
    for old_name in [
        'subdivide_circular_v15k',
        'subdivide_thin_bonus_v15l',
        'preflip_xy_v15f',
        'preflip_y_v15g',
        'preflip_xy_v15h',
        'preflip_y_toggle_v15i',
    ]:
        old = geo.op(old_name)
        if old is not None:
            set_flag(old, 'display', False)
            set_flag(old, 'render', False)

    # Only final deformation is displayed/rendered.
    for c in geo.children:
        if c.family == 'SOP':
            set_flag(c, 'display', False)
            set_flag(c, 'render', False)

    set_flag(deform, 'display', True)
    set_flag(deform, 'render', True)

    try:
        text_sop.cook(force=True)
        if source is not text_sop:
            source.cook(force=True)
        preflip.cook(force=True)
        deform.cook(force=True)
    except Exception:
        pass

    processed += 1
    rows.append([
        ch,
        text_sop.path,
        sub_path,
        preflip.path,
        deform.path,
        count_points(text_sop),
        count_points(source),
        count_points(deform),
        sub_expr
    ])

# -------------------------------------------------------------------------
# 4) Tube back to lightweight V15J-style quality
# -------------------------------------------------------------------------
tube_report = []
tube_paths = []

surface = root.op('helix_tube_surface_v06')
if surface is not None:
    set_flag(surface, 'display', False)
    set_flag(surface, 'render', False)

wire = root.op('helix_tube_wire_v06')
if wire is not None:
    set_flag(wire, 'display', True)
    set_flag(wire, 'render', True)
    tube_paths.append(wire.path)

    # Preserve view transforms.
    for pname, rootp, fallback in [
        ('tx', 'Viewtx', '0'),
        ('ty', 'Viewty', '0'),
        ('tz', 'Viewtz', '-3.97'),
        ('rx', 'Viewrotx', '0'),
        ('ry', 'Viewroty', '0'),
        ('rz', 'Viewrotz', '0'),
    ]:
        set_expr(wire, [pname], par_expr(rootp, fallback), verbose=False)
    for pname in ['sx', 'sy', 'sz']:
        set_expr(wire, [pname], par_expr('Viewscale', '0.1'), verbose=False)

    for c in wire.children:
        if c.family != 'SOP':
            continue
        pr = set_expr(c, ['rows'], tube_rows_expr, keywords=['rows'], verbose=False)
        pc = set_expr(c, ['cols', 'columns'], tube_cols_expr, keywords=['cols', 'columns'], verbose=False)
        if pr is not None or pc is not None:
            tube_report.append([c.path, pr.name if pr else '', pc.name if pc else ''])
        set_flag(c, 'display', True)
        set_flag(c, 'render', True)

# -------------------------------------------------------------------------
# 5) Render / output
# -------------------------------------------------------------------------
render = root.op('render1')
if render is None:
    render = create_or_get(root, ['renderTOP'], 'render1')

if render is not None:
    if p_render_auto is not None and p_render_auto.eval() > 0.5:
        set_expr(render, ['resx', 'w'], render_x_expr, keywords=['width', 'resolution x'], verbose=False)
        set_expr(render, ['resy', 'h'], render_y_expr, keywords=['height', 'resolution y'], verbose=False)

    try:
        render.cook(force=True)
    except Exception:
        pass

out = root.op('OUT_RENDER_VIEW_THIS')
if out is None:
    out = create_or_get(root, ['nullTOP'], 'OUT_RENDER_VIEW_THIS')

if out is not None and render is not None:
    try:
        out.inputConnectors[0].connect(render)
    except Exception:
        pass
    set_flag(out, 'viewer', True)
    try:
        out.cook(force=True)
    except Exception:
        pass

# Optional additional stable logo output, same render source.
logo_out = root.op('OUT_STATIC_LOGO_V15L')
if logo_out is None:
    logo_out = create_or_get(root, ['nullTOP'], 'OUT_STATIC_LOGO_V15L')
if logo_out is not None and render is not None:
    try:
        logo_out.inputConnectors[0].connect(render)
    except Exception:
        pass
    try:
        logo_out.cook(force=True)
    except Exception:
        pass

# -------------------------------------------------------------------------
# 6) Debug
# -------------------------------------------------------------------------
debug = root.op('debug_v15l_static_logo')
if debug is None:
    try:
        debug = root.create('tableDAT', 'debug_v15l_static_logo')
    except Exception:
        debug = None

if debug is not None:
    try:
        debug.clear()
        debug.appendRow(['key', 'value'])
        debug.appendRow(['mode', 'V15L STATIC LOGO FROM V15J'])
        debug.appendRow(['starting_assumption', 'V15J base, V15K bypassed'])
        debug.appendRow(['quality_mode', p_quality.eval()])
        debug.appendRow(['quality_legend', '0 FAST / 1 MEDIUM / 2 HIGH'])
        debug.appendRow(['static_logo', p_static.eval()])
        debug.appendRow(['live_edit', p_live.eval()])
        debug.appendRow(['manual_refresh', p_refresh.eval()])
        debug.appendRow(['forcecook_expr', forcecook_expr])
        debug.appendRow(['x_toggle', ROOT_PATH + '.par.' + p_x.name if p_x else 'missing'])
        debug.appendRow(['y_toggle', ROOT_PATH + '.par.' + p_y.name if p_y else 'missing'])
        debug.appendRow(['letters_processed', processed])
        debug.appendRow(['output', ROOT_PATH + '/OUT_RENDER_VIEW_THIS'])
        debug.appendRow(['static_output', ROOT_PATH + '/OUT_STATIC_LOGO_V15L'])
        debug.appendRow([])
        debug.appendRow(['tube_node', 'rows_par', 'cols_par'])
        for r in tube_report:
            debug.appendRow(r)
        debug.appendRow([])
        debug.appendRow(['letter', 'text_sop', 'light_subdiv', 'preflip_v15j', 'deform', 'text_pts', 'source_pts', 'deform_pts', 'subdiv_expr'])
        for r in rows:
            debug.appendRow(r)
    except Exception as e:
        print('WARNING debug failed', e)

try:
    root.layout(root.children)
except Exception:
    pass

print('=' * 72)
print('MORPHOGENESIS DNA V15L STATIC LOGO FROM V15J OK')
print('Default is now static and low CPU.')
print('Open:', ROOT_PATH + '/OUT_RENDER_VIEW_THIS')
print('Alternative output:', ROOT_PATH + '/OUT_STATIC_LOGO_V15L')
print('Debug:', ROOT_PATH + '/debug_v15l_static_logo')
print('')
print('Main controls:')
print('  V15lqualitymode = 0 FAST / 1 MEDIUM / 2 HIGH')
print('  V15llogostatic = 1 stops animation')
print('  V15lliveedit = 0 lowest CPU; set 1 temporarily while adjusting')
print('  V15lrefresh: increase this value to force a static recook after changing parameters')
print('')
print('V15K heavy nodes are bypassed, not deleted.')
print('=' * 72)
