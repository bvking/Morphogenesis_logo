# archive du DAT /project1/text13 (purge du 2026-11-02)
# morphogenesis_dna_td_v15m_AUDIT_ROUNDED_EDGES.py
# TouchDesigner 2025.32460 / Python 3.11
#
# Script NON DESTRUCTIF.
#
# But:
# - comprendre pourquoi certaines lettres deviennent arrondies / trop courbées / tronquées;
# - inspecter les paramètres sensibles;
# - inspecter la chaîne SOP active de chaque lettre;
# - compter les points avant/après subdivision/déformation;
# - repérer si des Subdivide SOP ou Divide SOP ajoutent du smoothing;
# - générer un diagnostic dans:
#   /project1/MORPHOGENESIS_DNA_TD/debug_v15m_audit_rounded_edges
#
# À lancer dans un Text DAT, puis ouvrir le DAT debug.

ROOT_PATH = '/project1/MORPHOGENESIS_DNA_TD'
WORD = 'MORPHOGENESIS'

root = op(ROOT_PATH)
if root is None:
    raise Exception('Container introuvable: ' + ROOT_PATH)

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

def peval(o, name, default='missing'):
    p = fp(o, name)
    if p is None:
        return default
    try:
        return p.eval()
    except Exception:
        try:
            return p.val
        except Exception:
            return default

def pexpr(o, name):
    p = fp(o, name)
    if p is None:
        return ''
    try:
        return p.expr
    except Exception:
        return ''

def count_pts(o):
    if o is None:
        return -1
    try:
        return int(o.numPoints)
    except Exception:
        try:
            return int(o.numPoints())
        except Exception:
            return -1

def warn_level(name, value):
    try:
        v = float(value)
    except Exception:
        return ''
    # These thresholds are empirical for this project.
    if name.lower() in ['curvecurvaturegain'] and v > 1.2:
        return 'HIGH: can over-round letter sides'
    if name.lower() in ['curvemaxangle'] and v > 70:
        return 'HIGH: strong wrap/circular deformation'
    if name.lower() in ['heightstretchamount'] and v > 1.5:
        return 'HIGH: can stretch/crop letters'
    if name.lower() in ['heightstretchmaxfront'] and v > 4.0:
        return 'HIGH: front letters may become huge'
    if name.lower() in ['depthscaleamount'] and v > 1.0:
        return 'HIGH: depth scaling may enlarge front/back'
    if name.lower() in ['lettersize'] and v > 1.3:
        return 'HIGH: risk of cropping/overlap'
    if name.lower() in ['viewscale'] and v > 0.2:
        return 'HIGH: framing/cropping risk'
    if name.lower() in ['tubesurfacecols', 'tubewirecols'] and v > 96:
        return 'VERY HIGH: static OK, live CPU heavy'
    if name.lower() in ['tubesurfacerows', 'tubewirerows'] and v > 48:
        return 'HIGH: static OK, live CPU heavy'
    return ''

debug = root.op('debug_v15m_audit_rounded_edges')
if debug is None:
    debug = root.create('tableDAT', 'debug_v15m_audit_rounded_edges')

debug.clear()
debug.appendRow(['SECTION', 'KEY', 'VALUE', 'EXPR', 'COMMENT'])

debug.appendRow(['SUMMARY', 'mode', 'audit only - no modification', '', ''])
debug.appendRow(['SUMMARY', 'root', ROOT_PATH, '', ''])
debug.appendRow(['SUMMARY', 'word', WORD, '', ''])

# -------------------------------------------------------------------------
# 1) Root parameters suspected of rounding/cropping
# -------------------------------------------------------------------------
suspects = [
    'Radius',
    'Pitch',
    'Turns',
    'Speed',
    'Axisrollspeed',
    'Globalscale',
    'Letterscale',
    'Lettersize',
    'Lettermirrorx',
    'Viewrotx',
    'Viewroty',
    'Viewrotz',
    'Viewscale',
    'Viewtx',
    'Viewty',
    'Viewtz',
    'Cameradistance',
    'Depthscaleamount',
    'Depthscaleminback',
    'Depthscalemaxfront',
    'Depthscalecurve',
    'Depthscaleflip',
    'Depthscalemode',
    'Curveamount',
    'Curvedeformamount',
    'Curvecurvaturegain',
    'Curvesurfaceoffset',
    'Curveextrusiongain',
    'Curvemaxangle',
    'Curvemaxangledegrees',
    'Heightstretchamount',
    'Heightminback',
    'Heightmaxfront',
    'Heightstretchcurve',
    'Heightstretchflip',
    'Heightstretchmode',
    'Backmirroractive',
    'Backmirroraxis',
    'Backmirrorthreshold',
    'Backmirrorinvert',
    'V15ixonly',
    'V15iyonly',
    'V15lqualitymode',
    'V15llogostatic',
    'V15lliveedit',
    'V15lrefresh',
    'V15lfasttextlod',
    'V15lmediumtextlod',
    'V15lhightextlod',
    'V15lfastsubdiv',
    'V15lmediumsubdiv',
    'V15lhighsubdiv',
    'V15lthinbonus',
    'V15lhardbonus',
    'Tubesurfacerows',
    'Tubesurfacecols',
    'Tubewirerows',
    'Tubewirecols',
    'Renderresx',
    'Renderresy',
]

for name in suspects:
    val = peval(root, name, 'missing')
    expr = pexpr(root, name)
    if val != 'missing' or expr:
        debug.appendRow(['ROOT_PARAM', name, val, expr, warn_level(name, val)])

# -------------------------------------------------------------------------
# 2) Letter chains, point counts, active SOP display/render
# -------------------------------------------------------------------------
debug.appendRow([])
debug.appendRow(['SECTION', 'LETTER', 'NODE', 'POINTS', 'DISPLAY/RENDER', 'COMMENT'])

for i, ch in enumerate(WORD):
    geo = root.op('letter_%02d_%s' % (i, ch))
    if geo is None:
        debug.appendRow(['LETTER', ch, 'missing geo', '', '', ''])
        continue

    debug.appendRow(['LETTER', ch, geo.path, '', 'geo display=%s render=%s' % (geo.display, geo.render), ''])

    for c in geo.children:
        if c.family != 'SOP':
            continue

        pts = count_pts(c)
        dr = 'display=%s render=%s' % (getattr(c, 'display', '?'), getattr(c, 'render', '?'))
        comment = ''

        lname = c.name.lower()
        if 'subdivide_circular_v15k' in lname or 'thin_bonus_v15l' in lname:
            comment = 'V15K/V15L heavy node: should be bypassed for static fast mode'
        elif 'subdivide_logo_quality_v15l' in lname:
            comment = 'active light subdivision for static logo quality'
        elif 'subdivide' in lname:
            smooth = peval(c, 'smooth', '')
            comment = 'subdivide; check smoothing=%s' % smooth
        elif 'divide' in lname:
            comment = 'divide/fallback subdivision'
        elif 'preflip' in lname:
            rx = peval(c, 'rx', '')
            ry = peval(c, 'ry', '')
            comment = 'preflip rx=%s ry=%s' % (rx, ry)
        elif 'bend_letter_v09' in lname:
            comment = 'final deformation SOP'
        elif lname.startswith('text_'):
            lod = peval(c, 'levelofdetail', '')
            comment = 'Text SOP LOD=%s' % lod

        debug.appendRow(['SOP', ch, c.path, pts, dr, comment])

# -------------------------------------------------------------------------
# 3) Tube resolution
# -------------------------------------------------------------------------
debug.appendRow([])
debug.appendRow(['SECTION', 'TUBE', 'NODE', 'VALUE', 'EXPR', 'COMMENT'])

for geo_name in ['helix_tube_wire_v06', 'helix_tube_surface_v06']:
    geo = root.op(geo_name)
    if geo is None:
        debug.appendRow(['TUBE', geo_name, 'missing', '', '', ''])
        continue

    debug.appendRow(['TUBE_GEO', geo_name, geo.path, 'display=%s render=%s' % (geo.display, geo.render), '', ''])
    for c in geo.children:
        if c.family != 'SOP':
            continue
        rows = peval(c, 'rows', '')
        cols = peval(c, 'cols', peval(c, 'columns', ''))
        debug.appendRow(['TUBE_SOP', geo_name, c.path, 'rows=%s cols=%s pts=%s' % (rows, cols, count_pts(c)), 'rows_expr=%s cols_expr=%s' % (pexpr(c, 'rows'), pexpr(c, 'cols')), ''])

# -------------------------------------------------------------------------
# 4) Diagnosis text
# -------------------------------------------------------------------------
debug.appendRow([])
debug.appendRow(['DIAGNOSIS', 'probable_causes', '', '', ''])
debug.appendRow(['DIAGNOSIS', '1', 'Curvecurvaturegain / Curvemaxangle too high', '', 'Rounds letter sides by design'])
debug.appendRow(['DIAGNOSIS', '2', 'Heightstretchamount / Heightstretchmaxfront too high', '', 'Can crop or balloon letters'])
debug.appendRow(['DIAGNOSIS', '3', 'Lettersize + Viewscale too high', '', 'Can crop left/right edges'])
debug.appendRow(['DIAGNOSIS', '4', 'Subdivide smooth enabled somewhere', '', 'Can visually round hard letter corners'])
debug.appendRow(['DIAGNOSIS', '5', 'Low Text LOD with strong curve', '', 'Can create crude/uneven curves'])
debug.appendRow(['DIAGNOSIS', '6', 'V15K heavy nodes still active', '', 'Can slow down and over-densify unexpectedly'])

print('=' * 72)
print('V15M AUDIT ROUNDED EDGES DONE')
print('Open:', ROOT_PATH + '/debug_v15m_audit_rounded_edges')
print('No modification was made.')
print('=' * 72)
