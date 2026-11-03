# archive du DAT /project1/text14 (purge du 2026-11-02)
# morphogenesis_dna_td_v15m_CLEAN_STATIC_LOGO.py
# TouchDesigner 2025.32460 / Python 3.11
#
# V15M CLEAN STATIC LOGO
# À lancer depuis la version V15J / V15L static, en évitant la V15K lourde.
#
# Objectif:
# - repartir d'une base V15J propre;
# - produire un logo statique, non une animation;
# - démarrer en qualité FAST, donc basse consommation CPU;
# - corriger le problème de V15lqualitymode fractionnaire;
# - éviter Text SOP LOD = 0;
# - bypasser les noeuds lourds ou expérimentaux V15K/V15L;
# - garder tous les réglages manuels accessibles;
# - permettre un refresh manuel quand Live Edit est off.
#
# Nouveau bloc:
# /project1/MORPHOGENESIS_DNA_TD > DNA V15M CLEAN LOGO
#
# Contrôles principaux:
# V15mqualitymode     : 0 FAST / 1 MEDIUM / 2 FINAL
# V15mstatic          : 1 = logo statique, stop animation
# V15mliveedit        : 0 = CPU minimal, 1 = recook lent pendant réglage
# V15mrefresh         : incrémenter pour recuire le logo
# V15mcleanlimits     : 1 = applique des limites douces anti-arrondi/crop
# V15musecleanchain   : 1 = force la chaîne propre V15J/V15M
#
# Chaîne active par lettre:
# Text SOP
#   -> subdivide_clean_v15m
#   -> switch_clean_subdiv_v15m si disponible
#   -> preflip_xy_toggle_v15j
#   -> bend_letter_v09
#
# IMPORTANT:
# - pas de normal map;
# - pas de bump map;
# - pas d'extrusion lourde;
# - pas de V15K subdivide_circular;
# - par défaut, aucun recook continu.

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

def find_par_by_keywords(o, keywords):
    if o is None:
        return None
    kws = [k.lower() for k in keywords]
    try:
        pars = o.pars()
    except Exception:
        return None
    for p in pars:
        try:
            label = p.label
        except Exception:
            label = ''
        key = (p.name + ' ' + label).lower()
        if all(k in key for k in kws):
            return p
    for p in pars:
        try:
            label = p.label
        except Exception:
            label = ''
        key = (p.name + ' ' + label).lower()
        if any(k in key for k in kws):
            return p
    return None

def par_expr(name, fallback='0'):
    p = find_par(root, name)
    if p is None:
        return str(fallback)
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
        p = find_par_by_keywords(o, keywords)
        if p is not None:
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
        p = find_par_by_keywords(o, keywords)
        if p is not None:
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
        print('CONNECTED', src.path, '->', dst.path, 'input', index)
        return True
    except Exception as e:
        print('WARNING connect failed', src.path if src else None, '->', dst.path if dst else None, 'input', index, e)
        return False

def ensure_page():
    for page_name in ['DNA V15M CLEAN LOGO', 'DNA V15M CLEAN LOGO B', 'DNA V15M CLEAN LOGO C']:
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
        print('ADDED FLOAT', par_name, '=', default, 'actual:', p.name)
        return p
    except Exception as e:
        print('WARNING cannot add float', par_name, e)
        return None

def ensure_int(par_name, label, default, norm_min=None, norm_max=None):
    p = find_par(root, par_name)
    if p is not None:
        return p
    page = ensure_page()
    if page is None:
        print('WARNING cannot create custom page')
        return None
    try:
        p = page.appendInt(par_name, label=label)[0]
        p.default = int(default)
        p.val = int(default)
        if norm_min is not None:
            p.normMin = norm_min
        if norm_max is not None:
            p.normMax = norm_max
        print('ADDED INT', par_name, '=', default, 'actual:', p.name)
        return p
    except Exception as e:
        print('appendInt failed, fallback float:', e)
        return ensure_float(par_name, label, default, norm_min, norm_max)

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

def clamp_root_param(exact_names, max_value=None, min_value=None, keywords=None):
    p = None
    for n in exact_names:
        p = find_par(root, n)
        if p is not None:
            break
    if p is None and keywords:
        p = find_par_by_keywords(root, keywords)
    if p is None:
        return ['missing', '', '']
    try:
        old = float(p.eval())
        new = old
        if max_value is not None:
            new = min(new, float(max_value))
        if min_value is not None:
            new = max(new, float(min_value))
        if abs(new - old) > 1e-6:
            p.val = new
            return [p.name, old, new]
        return [p.name, old, old]
    except Exception:
        return [p.name, 'error', 'error']

# -------------------------------------------------------------------------
# 1) V15M parameters
# -------------------------------------------------------------------------
p_quality = ensure_int('V15mqualitymode', 'Quality mode 0 fast 1 medium 2 final', 0, 0, 2)
p_static = ensure_toggle('V15mstatic', 'Static logo mode', 1)
p_live = ensure_toggle('V15mliveedit', 'Live edit recook', 0)
p_refresh = ensure_float('V15mrefresh', 'Manual refresh value', 1, 0, 9999)
p_cookrate = ensure_int('V15mcookrate', 'Live edit cook rate', 24, 1, 240)
p_clean = ensure_toggle('V15musecleanchain', 'Use clean chain', 1)
p_limits = ensure_toggle('V15mcleanlimits', 'Apply clean anti-round/crop limits', 1)

# Quality values, deliberately light by default.
p_fast_lod = ensure_float('V15mfasttextlod', 'Fast Text LOD', 0.08, 0.01, 1.0)
p_med_lod = ensure_float('V15mmediumtextlod', 'Medium Text LOD', 0.14, 0.01, 1.0)
p_final_lod = ensure_float('V15mfinaltextlod', 'Final Text LOD', 0.24, 0.01, 1.0)

p_fast_sub = ensure_int('V15mfastsubdiv', 'Fast letter subdiv', 0, 0, 4)
p_med_sub = ensure_int('V15mmediumsubdiv', 'Medium letter subdiv', 1, 0, 4)
p_final_sub = ensure_int('V15mfinalsubdiv', 'Final letter subdiv', 2, 0, 4)

p_thin_bonus = ensure_int('V15mthinbonus', 'Thin letter bonus', 0, 0, 3)
p_hard_bonus = ensure_int('V15mhardbonus', 'Hard letter bonus', 0, 0, 3)

p_fast_rows = ensure_int('V15mfasttuberows', 'Fast tube rows', 3, 2, 64)
p_fast_cols = ensure_int('V15mfasttubecols', 'Fast tube cols', 18, 8, 160)
p_med_rows = ensure_int('V15mmediumtuberows', 'Medium tube rows', 5, 2, 64)
p_med_cols = ensure_int('V15mmediumtubecols', 'Medium tube cols', 28, 8, 160)
p_final_rows = ensure_int('V15mfinaltuberows', 'Final tube rows', 8, 2, 96)
p_final_cols = ensure_int('V15mfinaltubecols', 'Final tube cols', 42, 8, 200)

# Clean limits for the specific rounding/cropping issue.
p_max_letter = ensure_float('V15mmaxlettersize', 'Max Letter size', 1.25, 0.1, 5)
p_max_view = ensure_float('V15mmaxviewscale', 'Max View scale', 0.42, 0.02, 2)
p_max_depth = ensure_float('V15mmaxdepthscale', 'Max depth scale', 0.80, 0, 5)
p_max_curve_angle = ensure_float('V15mmaxcurveangle', 'Max curve angle', 45, 0, 120)
p_max_height = ensure_float('V15mmaxheightamount', 'Max height stretch amount', 1.30, 0, 8)
p_max_height_curve = ensure_float('V15mmaxheightcurve', 'Max height stretch curve', 2.40, 0, 8)

# Preserve V15J X/Y toggles; create if missing.
p_x = find_par(root, 'V15ixonly')
if p_x is None:
    p_x = ensure_toggle('V15ixonly', 'X only 180 toggle', 1)

p_y = find_par(root, 'V15iyonly')
if p_y is None:
    p_y = ensure_toggle('V15iyonly', 'Y only 180 toggle', 0)

if p_quality is None or p_static is None or p_live is None or p_refresh is None:
    raise Exception('V15M: paramètres principaux manquants')

# Force the clean defaults now.
try:
    p_quality.val = 0
except Exception:
    pass
try:
    p_static.val = 1
except Exception:
    pass
try:
    p_live.val = 0
except Exception:
    pass
try:
    p_clean.val = 1
except Exception:
    pass

# Old V15L parameters are synced to avoid ambiguity in the UI.
for old_name, value in [
    ('V15lqualitymode', 0),
    ('V15llogostatic', 1),
    ('V15lliveedit', 0),
]:
    p = find_par(root, old_name)
    if p is not None:
        try:
            p.val = value
            print('SYNC OLD', old_name, '=', value)
        except Exception:
            pass

# -------------------------------------------------------------------------
# 2) Static mode and clean limits
# -------------------------------------------------------------------------
limit_report = []

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
                print('STATIC', name, '=', value)
            except Exception:
                pass

if p_limits.eval() > 0.5:
    limit_report.append(['Lettersize', *clamp_root_param(['Lettersize'], max_value=p_max_letter.eval())])
    limit_report.append(['Viewscale', *clamp_root_param(['Viewscale'], max_value=p_max_view.eval())])
    limit_report.append(['Depthscaleamount', *clamp_root_param(['Depthscaleamount'], max_value=p_max_depth.eval())])
    limit_report.append(['Curvemaxangle', *clamp_root_param(['Curvemaxangle', 'Curvemaxangledegrees'], max_value=p_max_curve_angle.eval(), keywords=['curve', 'angle'])])
    limit_report.append(['Heightstretchamount', *clamp_root_param(['Heightstretchamount'], max_value=p_max_height.eval())])
    limit_report.append(['Heightstretchcurve', *clamp_root_param(['Heightstretchcurve'], max_value=p_max_height_curve.eval())])
    # Only if such a parameter exists. It was not in the last audit, but may exist in some versions.
    limit_report.append(['Curvecurvaturegain', *clamp_root_param(['Curvecurvaturegain', 'Curvaturegain'], max_value=1.0, keywords=['curvature', 'gain'])])

# -------------------------------------------------------------------------
# 3) Expressions
# -------------------------------------------------------------------------
mode_expr = "int(max(0, min(2, round(op('%s').par.%s.eval()))))" % (ROOT_PATH, p_quality.name)

lod_expr = (
    "(op('{r}').par.{fl}.eval() if {m} <= 0 else "
    "(op('{r}').par.{ml}.eval() if {m} == 1 else op('{r}').par.{hl}.eval()))"
).format(r=ROOT_PATH, fl=p_fast_lod.name, ml=p_med_lod.name, hl=p_final_lod.name, m=mode_expr)

subdiv_expr_base = (
    "(int(op('{r}').par.{fs}.eval()) if {m} <= 0 else "
    "(int(op('{r}').par.{ms}.eval()) if {m} == 1 else int(op('{r}').par.{hs}.eval())))"
).format(r=ROOT_PATH, fs=p_fast_sub.name, ms=p_med_sub.name, hs=p_final_sub.name, m=mode_expr)

tube_rows_expr = (
    "(int(op('{r}').par.{fr}.eval()) if {m} <= 0 else "
    "(int(op('{r}').par.{mr}.eval()) if {m} == 1 else int(op('{r}').par.{hr}.eval())))"
).format(r=ROOT_PATH, fr=p_fast_rows.name, mr=p_med_rows.name, hr=p_final_rows.name, m=mode_expr)

tube_cols_expr = (
    "(int(op('{r}').par.{fc}.eval()) if {m} <= 0 else "
    "(int(op('{r}').par.{mc}.eval()) if {m} == 1 else int(op('{r}').par.{hc}.eval())))"
).format(r=ROOT_PATH, fc=p_fast_cols.name, mc=p_med_cols.name, hc=p_final_cols.name, m=mode_expr)

x_expr = "180 if op('%s').par.%s.eval() > 0.5 else 0" % (ROOT_PATH, p_x.name)
y_expr = "180 if op('%s').par.%s.eval() > 0.5 else 0" % (ROOT_PATH, p_y.name)

forcecook_expr = (
    "int(op('{r}').par.{refresh}.eval()) + "
    "(int(absTime.frame / max(1, int(op('{r}').par.{rate}.eval()))) "
    "if op('{r}').par.{live}.eval() > 0.5 else 0)"
).format(r=ROOT_PATH, refresh=p_refresh.name, rate=p_cookrate.name, live=p_live.name)

# -------------------------------------------------------------------------
# 4) Clean material: visible, no normal/bump
# -------------------------------------------------------------------------
mat = root.op('mat_letters_readable_v15d') or root.op('mat_letters_visible_v15c')
if mat is None:
    mat = create_or_get(root, ['phongMAT'], 'mat_letters_clean_v15m')

if mat is not None:
    # Ensure no normal/bump map or unstable maps.
    for slot in ['normalmap', 'bumpmap', 'normalmap1', 'bumpmap1', 'normalmaptop', 'bumpmaptop']:
        p = find_par(mat, slot)
        if p is not None:
            try:
                p.val = ''
            except Exception:
                pass
    set_val(mat, ['blending'], False, keywords=['blend'], verbose=False)
    set_val(mat, ['depthwriting'], True, keywords=['depth writing'], verbose=False)
    set_val(mat, ['cullface'], 'neither', keywords=['cull'], verbose=False)

# -------------------------------------------------------------------------
# 5) Letter clean chain from V15J
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

    # Identity Geometry COMP, because bend_letter_v09 outputs world-ish deformation.
    for pname, val in [('tx', 0), ('ty', 0), ('tz', 0), ('rx', 0), ('ry', 0), ('rz', 0), ('sx', 1), ('sy', 1), ('sz', 1)]:
        set_val(geo, [pname], val, verbose=False)

    set_flag(geo, 'display', True)
    set_flag(geo, 'render', True)

    if mat is not None:
        set_val(geo, ['material', 'mat'], mat.path, verbose=False)

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

    # Clean lightweight subdivision. Default FAST = zero or bypass via switch.
    clean_sub = geo.op('subdivide_clean_v15m')
    if clean_sub is None:
        clean_sub = create_or_get(geo, ['subdivideSOP'], 'subdivide_clean_v15m')
    if clean_sub is None:
        clean_sub = create_or_get(geo, ['divideSOP'], 'subdivide_clean_v15m')

    source_for_preflip = text_sop
    sub_path = 'none'
    switch_path = 'none'
    sub_expr = '0'

    if clean_sub is not None:
        try:
            clean_sub.nodeX = text_sop.nodeX + 120
            clean_sub.nodeY = text_sop.nodeY
        except Exception:
            pass

        connect(text_sop, clean_sub, 0)

        thin_bonus = "int(op('%s').par.%s.eval())" % (ROOT_PATH, p_thin_bonus.name) if ch in thin_letters else "0"
        hard_bonus = "int(op('%s').par.%s.eval())" % (ROOT_PATH, p_hard_bonus.name) if ch in hard_letters else "0"
        sub_expr = "max(0, int(round(%s + %s + %s)))" % (subdiv_expr_base, thin_bonus, hard_bonus)

        set_expr(clean_sub, ['iterations'], sub_expr, keywords=['iteration'], verbose=False)
        set_expr(clean_sub, ['divisions'], sub_expr, keywords=['division'], verbose=False)
        set_expr(clean_sub, ['level'], sub_expr, keywords=['level'], verbose=False)
        set_val(clean_sub, ['smooth'], False, keywords=['smooth'], verbose=False)
        set_val(clean_sub, ['computenormals'], True, keywords=['normal'], verbose=False)
        set_val(clean_sub, ['bricker'], True, keywords=['brick'], verbose=False)
        sub_path = clean_sub.path

        # Switch SOP allows true bypass when quality subdiv = 0.
        sw = geo.op('switch_clean_subdiv_v15m')
        if sw is None:
            sw = create_or_get(geo, ['switchSOP'], 'switch_clean_subdiv_v15m')

        if sw is not None:
            try:
                sw.nodeX = clean_sub.nodeX + 120
                sw.nodeY = clean_sub.nodeY
            except Exception:
                pass
            connect(text_sop, sw, 0)
            connect(clean_sub, sw, 1)
            # Use input 0 when subdiv = 0, input 1 when subdiv > 0.
            switch_expr = "1 if (%s) > 0 else 0" % sub_expr
            set_expr(sw, ['index', 'input'], switch_expr, keywords=['index', 'input'], verbose=False)
            source_for_preflip = sw
            switch_path = sw.path
        else:
            # Fallback: direct clean_sub. If iteration 0 works, it behaves like bypass.
            source_for_preflip = clean_sub

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
        preflip.nodeX = source_for_preflip.nodeX + 140
        preflip.nodeY = source_for_preflip.nodeY
        deform.nodeX = preflip.nodeX + 160
        deform.nodeY = preflip.nodeY
    except Exception:
        pass

    connect(source_for_preflip, preflip, 0)

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

    # Manual refresh / live edit recook.
    p_force = find_par(deform, 'Forcecook')
    if p_force is None:
        try:
            page = deform.appendCustomPage('V15M')
            p_force = page.appendFloat('Forcecook', label='Force cook')[0]
        except Exception:
            p_force = None
    if p_force is not None:
        try:
            p_force.expr = forcecook_expr
        except Exception as e:
            print('WARNING cannot set Forcecook on', deform.path, e)

    # Hide heavy/experimental old nodes.
    heavy_names = [
        'subdivide_circular_v15k',
        'subdivide_thin_bonus_v15l',
        'subdivide_logo_quality_v15l',
        'preflip_xy_v15f',
        'preflip_y_v15g',
        'preflip_xy_v15h',
        'preflip_y_toggle_v15i',
        'OUT_LETTER_GPU_V13',
        'extrude_letter_v13_gpu',
        'extrude_letter_v12d',
    ]
    for old_name in heavy_names:
        old = geo.op(old_name)
        if old is not None:
            set_flag(old, 'display', False)
            set_flag(old, 'render', False)

    # Display only final deformation.
    for c in geo.children:
        if c.family == 'SOP':
            set_flag(c, 'display', False)
            set_flag(c, 'render', False)

    set_flag(deform, 'display', True)
    set_flag(deform, 'render', True)

    try:
        text_sop.cook(force=True)
        if clean_sub is not None:
            clean_sub.cook(force=True)
        if source_for_preflip is not text_sop and source_for_preflip is not clean_sub:
            source_for_preflip.cook(force=True)
        preflip.cook(force=True)
        deform.cook(force=True)
    except Exception:
        pass

    processed += 1
    rows.append([
        ch,
        text_sop.path,
        sub_path,
        switch_path,
        preflip.path,
        deform.path,
        count_points(text_sop),
        count_points(clean_sub),
        count_points(source_for_preflip),
        count_points(deform),
        sub_expr
    ])

# -------------------------------------------------------------------------
# 6) Tube wire light, surface disabled
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
        set_flag(c, 'display', True)
        set_flag(c, 'render', True)
        if pr is not None or pc is not None:
            tube_report.append([c.path, pr.name if pr else '', pc.name if pc else '', count_points(c)])

# -------------------------------------------------------------------------
# 7) Render and outputs
# -------------------------------------------------------------------------
render = root.op('render1')
if render is None:
    render = create_or_get(root, ['renderTOP'], 'render1')

if render is not None:
    # Reconnect geometry just in case old heavy geometry remained listed.
    letter_paths = []
    for i, ch in enumerate(WORD):
        geo = root.op('letter_%02d_%s' % (i, ch))
        if geo is not None:
            letter_paths.append(geo.path)
    set_val(render, ['geometry', 'geo', 'geometries'], ' '.join(letter_paths + tube_paths), verbose=False)
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

logo_out = root.op('OUT_CLEAN_STATIC_LOGO_V15M')
if logo_out is None:
    logo_out = create_or_get(root, ['nullTOP'], 'OUT_CLEAN_STATIC_LOGO_V15M')
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
# 8) Debug
# -------------------------------------------------------------------------
debug = root.op('debug_v15m_clean_static_logo')
if debug is None:
    try:
        debug = root.create('tableDAT', 'debug_v15m_clean_static_logo')
    except Exception:
        debug = None

if debug is not None:
    try:
        debug.clear()
        debug.appendRow(['key', 'value'])
        debug.appendRow(['mode', 'V15M CLEAN STATIC LOGO'])
        debug.appendRow(['based_on', 'V15J clean chain, V15K bypassed'])
        debug.appendRow(['quality_mode', p_quality.eval()])
        debug.appendRow(['quality_legend', '0 FAST / 1 MEDIUM / 2 FINAL'])
        debug.appendRow(['static', p_static.eval()])
        debug.appendRow(['live_edit', p_live.eval()])
        debug.appendRow(['manual_refresh', p_refresh.eval()])
        debug.appendRow(['forcecook_expr', forcecook_expr])
        debug.appendRow(['text_lod_expr', lod_expr])
        debug.appendRow(['base_subdiv_expr', subdiv_expr_base])
        debug.appendRow(['x_toggle', ROOT_PATH + '.par.' + p_x.name if p_x else 'missing'])
        debug.appendRow(['y_toggle', ROOT_PATH + '.par.' + p_y.name if p_y else 'missing'])
        debug.appendRow(['material', mat.path if mat else 'missing'])
        debug.appendRow(['letters_processed', processed])
        debug.appendRow(['output', ROOT_PATH + '/OUT_RENDER_VIEW_THIS'])
        debug.appendRow(['clean_output', ROOT_PATH + '/OUT_CLEAN_STATIC_LOGO_V15M'])
        debug.appendRow([])
        debug.appendRow(['clean_limits_applied'])
        debug.appendRow(['target', 'parameter', 'old', 'new'])
        for r in limit_report:
            debug.appendRow(r)
        debug.appendRow([])
        debug.appendRow(['tube_node', 'rows_par', 'cols_par', 'points'])
        for r in tube_report:
            debug.appendRow(r)
        debug.appendRow([])
        debug.appendRow(['letter', 'text_sop', 'clean_subdiv', 'switch', 'preflip_v15j', 'deform', 'text_pts', 'sub_pts', 'source_pts', 'deform_pts', 'subdiv_expr'])
        for r in rows:
            debug.appendRow(r)
    except Exception as e:
        print('WARNING debug failed', e)

try:
    root.layout(root.children)
except Exception:
    pass

print('=' * 72)
print('MORPHOGENESIS DNA V15M CLEAN STATIC LOGO OK')
print('Open:', ROOT_PATH + '/OUT_RENDER_VIEW_THIS')
print('Clean output:', ROOT_PATH + '/OUT_CLEAN_STATIC_LOGO_V15M')
print('Debug:', ROOT_PATH + '/debug_v15m_clean_static_logo')
print('')
print('Defaults applied:')
print('  V15mqualitymode = 0 FAST')
print('  V15mstatic = 1')
print('  V15mliveedit = 0')
print('  Speed = 0')
print('  Axisrollspeed = 0')
print('  Curvecookactive = 0')
print('')
print('Workflow:')
print('  Adjust parameters manually.')
print('  If V15mliveedit = 0, increment V15mrefresh to update.')
print('  For final still: V15mqualitymode = 1 or 2, then increment V15mrefresh.')
print('=' * 72)
