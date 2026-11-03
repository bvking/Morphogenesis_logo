# morphogenesis_dna_td_v17_EXTRUDE_LETTERS.py
# TouchDesigner 2025.32460 / Python 3.11
#
# V17 EXTRUSION
# But : donner une vraie epaisseur 3D au lettrage pour que la lumiere accroche
# le relief (prealable aux essais d'eclairage).
#
# Ce que fait ce patch (idempotent, rejouable) :
# 1) Remplace la section de construction de geometrie du Script SOP des lettres
#    (traits plats -> dalles : face avant + arriere + 4 cotes), epaisseur pilotee
#    par la custom par Letterthickness.
# 2) Ajoute un Facet SOP (facet_normals_v17) apres le Script SOP pour calculer
#    les normales (indispensable a l'eclairage), points uniques + cusp = aretes nettes.
# 3) Bascule les flags Render : le Facet rend, le Script SOP non.
# 4) Regle Letterthickness (0 = retour aux traits plats).
#
# Usage : coller dans un Text DAT, Run Script. Puis ouvrir
# /project1/MORPHOGENESIS_DNA_TD/OUT_RENDER_VIEW_THIS
# Pour desactiver l'extrusion sans retirer la machinerie : Letterthickness = 0.

ROOT_PATH = '/project1/MORPHOGENESIS_DNA_TD'
THICKNESS = 0.07  # epaisseur monde ; 0 => traits plats

root = op(ROOT_PATH)
if root is None:
    raise Exception('Container introuvable: ' + ROOT_PATH)

geo = root.op('other_method_single_geo_v01')
sop = geo.op('letters_texture_instances_sop')
cb = geo.op('letters_texture_instances_sop_callbacks')

# --- 1) section de construction : traits plats -> dalles extrudees ------------
OLD_BUILD = '''    pos = []
    for i in range(len(WORD)):
        bbox = _preflip_bbox(i)
        for local in _letter_strokes[i]:
            world = []
            for x, y, z in local:
                px, py, pz = _preflip_point(i, x, y, z)
                world.append(module.deform_point(i, px, py, pz, bbox))
            pos.extend(world)

    # Topology is constant while WORD and the glyph tables are fixed: rebuild
    # the polys only when the vertex count changes, otherwise just move the
    # existing points (much cheaper than clear + appendPoly every cook).
    if scriptOp.numPoints != len(pos):
        scriptOp.clear()
        for k in range(0, len(pos), 4):
            poly = scriptOp.appendPoly(4, closed=True, addPoints=True)
            for n in range(4):
                poly[n].point.P = pos[k + n]
    else:
        for pt, xyz in zip(scriptOp.points, pos):
            pt.P = xyz'''

NEW_BUILD = '''    # Extrusion thickness (world units). 0 -> flat quads (legacy look).
    try:
        thickness = float(op(ROOT_PATH).par.Letterthickness.eval())
    except Exception:
        thickness = 0.0

    # One face = 4 world corners in creation order. Flat strokes stay single
    # quads; a non-zero thickness turns each stroke into a slab (front + back +
    # 4 sides) so lights catch real depth. A downstream Facet SOP builds normals.
    faces = []
    half = thickness * 0.5
    for i in range(len(WORD)):
        bbox = _preflip_bbox(i)
        for local in _letter_strokes[i]:
            world = []
            for x, y, z in local:
                px, py, pz = _preflip_point(i, x, y, z)
                world.append(module.deform_point(i, px, py, pz, bbox))
            if len(world) < 4:
                continue
            if half <= 0.0:
                faces.append(tuple(world))
                continue
            c0, c1, c2, c3 = world[0], world[1], world[2], world[3]
            e1 = (c1[0]-c0[0], c1[1]-c0[1], c1[2]-c0[2])
            e3 = (c3[0]-c0[0], c3[1]-c0[1], c3[2]-c0[2])
            nx = e1[1]*e3[2] - e1[2]*e3[1]
            ny = e1[2]*e3[0] - e1[0]*e3[2]
            nz = e1[0]*e3[1] - e1[1]*e3[0]
            nl = (nx*nx + ny*ny + nz*nz) ** 0.5 or 1.0
            nx, ny, nz = nx/nl*half, ny/nl*half, nz/nl*half
            f = [(c[0]+nx, c[1]+ny, c[2]+nz) for c in world]
            b = [(c[0]-nx, c[1]-ny, c[2]-nz) for c in world]
            faces.append((f[0], f[1], f[2], f[3]))
            faces.append((b[3], b[2], b[1], b[0]))
            faces.append((f[0], b[0], b[1], f[1]))
            faces.append((f[1], b[1], b[2], f[2]))
            faces.append((f[2], b[2], b[3], f[3]))
            faces.append((f[3], b[3], b[0], f[0]))

    pos = [c for face in faces for c in face]

    # Rebuild polys only when the vertex count changes (thickness toggled),
    # otherwise just move the existing points.
    if scriptOp.numPoints != len(pos):
        scriptOp.clear()
        for face in faces:
            poly = scriptOp.appendPoly(4, closed=True, addPoints=True)
            for n in range(4):
                poly[n].point.P = face[n]
    else:
        for pt, xyz in zip(scriptOp.points, pos):
            pt.P = xyz'''

txt = cb.text
if 'faces.append((f[0], f[1], f[2], f[3]))' in txt:
    print('[1] extrusion builder deja present, skip')
elif OLD_BUILD in txt:
    txt = txt.replace(OLD_BUILD, NEW_BUILD)
    print('[1] extrusion builder installe')
else:
    raise Exception('[1] section de build introuvable : callbacks modifies ? patch non applique')

# Letterthickness dans l'empreinte de cache (recalcul si on change l'epaisseur a l'arret)
if "'Letterthickness'" not in txt:
    txt = txt.replace("'Lettersize', 'Letterscale',",
                      "'Lettersize', 'Letterscale', 'Letterthickness',")
cb.text = txt

# --- 2) Facet SOP pour les normales ------------------------------------------
facet = geo.op('facet_normals_v17')
if facet is None:
    facet = geo.create(facetSOP, 'facet_normals_v17')
    facet.nodeX = sop.nodeX + 200
    facet.nodeY = sop.nodeY
facet.inputConnectors[0].connect(sop)
facet.par.postnml = True     # calcule les normales
facet.par.unique = True      # points uniques -> facettes nettes
if hasattr(facet.par, 'cusp'):
    facet.par.cusp = True
if hasattr(facet.par, 'angle'):
    facet.par.angle = 30
print('[2] facet_normals_v17 pret')

# --- 3) flags Render ----------------------------------------------------------
sop.render = False
sop.display = False
facet.render = True
facet.display = True
print('[3] render -> facet')

# --- 4) epaisseur -------------------------------------------------------------
root.par.Letterthickness = THICKNESS
sop.cook(force=True)
facet.cook(force=True)
print('[4] Letterthickness =', root.par.Letterthickness.eval())
print('    letters: pts=%d prims=%d | facet hasN=%s' % (
    sop.numPoints, sop.numPrims, 'N' in [a.name for a in facet.pointAttribs]))
print('OK — ouvrir', ROOT_PATH + '/OUT_RENDER_VIEW_THIS')
