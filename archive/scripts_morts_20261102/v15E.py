# archive du DAT /project1/v15E (purge du 2026-11-02)
# morphogenesis_dna_td_v15e_RESTORE_X_MIRROR_SWITCH.py
# TouchDesigner 2025.32460 / Python 3.11
#
# Correctif V15E
# A lancer apres V15D si les lettres switchent/mirroir en Y.
#
# Probleme:
# - V15D a force Backmirroraxis = 0.
# - Dans le module actuel, 0 correspond au miroir vertical/Y.
# - Le comportement voulu est celui d'avant: miroir selon l'axe central X de la lettre.
#
# Correction:
# - Backmirroractive = 1
# - Backmirroraxis = 1
# - Backmirrorthreshold = 0
# - Backmirrorinvert = 0
#
# Usage:
# 1) Coller dans un Text DAT.
# 2) Run Script.
# 3) Ouvrir /project1/MORPHOGENESIS_DNA_TD/OUT_RENDER_VIEW_THIS

ROOT_PATH = '/project1/MORPHOGENESIS_DNA_TD'
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

def set_root(name, value):
    p = find_par(root, name)
    if p is None:
        print('WARNING parameter missing:', name)
        return False
    try:
        p.val = value
        print('SET', ROOT_PATH + '.par.' + p.name, '=', value)
        return True
    except Exception as e:
        print('WARNING could not set', name, e)
        return False

# Restore the previous correct mirror behavior.
set_root('Backmirroractive', 1)
set_root('Backmirroraxis', 1)       # 1 = X mirror in this patch/module mapping
set_root('Backmirrorthreshold', 0)
set_root('Backmirrorinvert', 0)

# Keep V15D readability/lights, but do not modify shape/framing further.
# Force cook all letter Script SOPs once.
WORD = 'MORPHOGENESIS'
cooked = 0

for i, ch in enumerate(WORD):
    geo = root.op('letter_%02d_%s' % (i, ch))
    if geo is None:
        continue
    deform = geo.op('bend_letter_v09')
    if deform is not None:
        try:
            deform.cook(force=True)
            cooked += 1
        except Exception:
            pass

render = root.op('render1')
out_top = root.op('OUT_RENDER_VIEW_THIS')
for o in [render, out_top]:
    if o is not None:
        try:
            o.cook(force=True)
        except Exception:
            pass

debug = root.op('debug_v15e_restore_x_mirror_switch')
if debug is None:
    try:
        debug = root.create('tableDAT', 'debug_v15e_restore_x_mirror_switch')
    except Exception:
        debug = None

if debug is not None:
    try:
        debug.clear()
        debug.appendRow(['key', 'value'])
        debug.appendRow(['mode', 'V15E restore X mirror switch'])
        debug.appendRow(['Backmirroractive', find_par(root, 'Backmirroractive').eval() if find_par(root, 'Backmirroractive') else 'missing'])
        debug.appendRow(['Backmirroraxis', find_par(root, 'Backmirroraxis').eval() if find_par(root, 'Backmirroraxis') else 'missing'])
        debug.appendRow(['Backmirrorthreshold', find_par(root, 'Backmirrorthreshold').eval() if find_par(root, 'Backmirrorthreshold') else 'missing'])
        debug.appendRow(['Backmirrorinvert', find_par(root, 'Backmirrorinvert').eval() if find_par(root, 'Backmirrorinvert') else 'missing'])
        debug.appendRow(['letters_cooked', cooked])
        debug.appendRow(['open', ROOT_PATH + '/OUT_RENDER_VIEW_THIS'])
    except Exception:
        pass

print('=' * 72)
print('MORPHOGENESIS DNA V15E RESTORE X MIRROR SWITCH OK')
print('Backmirroraxis is now 1, to restore the previous X-axis switch.')
print('Open:', ROOT_PATH + '/OUT_RENDER_VIEW_THIS')
print('Debug:', ROOT_PATH + '/debug_v15e_restore_x_mirror_switch')
print('=' * 72)
