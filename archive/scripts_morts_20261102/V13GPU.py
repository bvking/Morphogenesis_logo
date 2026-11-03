# archive du DAT /project1/V13GPU (purge du 2026-11-02)
# morphogenesis_dna_td_v13_GPU_GLSL.py
# TouchDesigner 2025.32460 / Python 3.11
#
# V13 = vraie optimisation GPU/GLSL
#
# Idée:
# - la déformation des lettres n'est plus faite en Python point-par-point dans des Script SOP;
# - on conserve une géométrie statique légère par lettre (Text -> Hole -> Extrude -> Facet -> Center);
# - la courbure sur le tube, l'effet avant/arrière, le miroir arrière sur axe X,
#   l'étirement de hauteur, l'échelle avant/arrière et la vue globale sont faits dans un GLSL MAT.
#
# Bénéfice:
# - beaucoup moins de CPU que les Script SOP V09-V12;
# - animation toujours vivante;
# - extrusion 3D légère conservée;
# - les lettres continuent d'épouser le tube.
#
# IMPORTANT:
# - this script directly switches letters to the GPU path.
# - if you need to compare, you can rerun V12D later to restore the CPU deformed chain.

ROOT_PATH = '/project1/MORPHOGENESIS_DNA_TD'
WORD = 'MORPHOGENESIS'

root = op(ROOT_PATH)
if root is None:
    raise Exception('Container introuvable: ' + ROOT_PATH)

# -------------------------------------------------------------------------
# UTILS
# -------------------------------------------------------------------------
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
        print('WARNING could not set expression on', o.path if o else None, names, expr)
    return None

def ensure_float(par_name, label, default, norm_min=None, norm_max=None, page_name='DNA V13'):
    p = get_par(root, par_name)
    if p is not None:
        return p
    try:
        page = root.appendCustomPage(page_name)
    except Exception:
        try:
            page = root.appendCustomPage(page_name + ' B')
        except Exception as e:
            print('WARNING cannot create page', page_name, e)
            return None

    try:
        p = page.appendFloat(par_name, label=label)[0]
        p.default = default
        p.val = default
        if norm_min is not None:
            p.normMin = norm_min
        if norm_max is not None:
            p.normMax = norm_max
        print('ADDED PARAM', par_name, '=', default)
        return p
    except Exception as e:
        print('WARNING cannot add parameter', par_name, e)
        return None

def create_or_get(parent, type_names, name, destroy=False):
    existing = parent.op(name)
    if existing is not None:
        if not destroy:
            return existing
        try:
            existing.destroy()
        except Exception as e:
            print('WARNING could not destroy', existing.path, e)

    errors = []
    for tn in type_names:
        try:
            o = parent.create(tn, name)
            print('CREATED', o.path, 'type', tn)
            return o
        except Exception as e:
            errors.append(tn + ': ' + repr(e))
    print('WARNING cannot create', name, errors)
    return None

def connect(src, dst, index=0):
    if src is None or dst is None:
        return False
    try:
        dst.inputConnectors[index].connect(src)
        print('CONNECTED', src.path, '->', dst.path)
        return True
    except Exception as e:
        print('WARNING connect failed:', src.path, '->', dst.path, e)
        return False

def set_flag(o, flag, value):
    try:
        setattr(o, flag, value)
        return True
    except Exception:
        return False

def expr_par(name):
    return "op('%s').par.%s" % (ROOT_PATH, name)

def center_sop_with_bbox(source_sop, xform_sop):
    if source_sop is None or xform_sop is None:
        return False
    try:
        source_sop.cook(force=True)
    except Exception:
        pass

    try:
        pts = list(source_sop.points)
        if not pts:
            return False
        minx = min(p.x for p in pts)
        maxx = max(p.x for p in pts)
        miny = min(p.y for p in pts)
        maxy = max(p.y for p in pts)
        minz = min(p.z for p in pts)
        maxz = max(p.z for p in pts)
        cx = 0.5 * (minx + maxx)
        cy = 0.5 * (miny + maxy)
        cz = 0.5 * (minz + maxz)
        set_val(xform_sop, ['tx'], -cx, verbose=False)
        set_val(xform_sop, ['ty'], -cy, verbose=False)
        set_val(xform_sop, ['tz'], -cz, verbose=False)
        print('CENTERED', source_sop.path, '->', xform_sop.path, 'center=', (cx, cy, cz))
        return True
    except Exception as e:
        print('WARNING could not center SOP', source_sop.path, e)
        return False

# -------------------------------------------------------------------------
# 1) Ensure parameters exist
# -------------------------------------------------------------------------
# Core geometry/animation
ensure_float('Radius', 'Radius', 2.15, 0.1, 20.0)
ensure_float('Pitch', 'Pitch', 0.48, 0.01, 5.0)
ensure_float('Turns', 'Turns', 2.25, 0.1, 20.0)
ensure_float('Speed', 'Speed', 0.18, -5.0, 5.0)
ensure_float('Axisrollspeed', 'Axis roll speed', 0.12, -5.0, 5.0)
ensure_float('Axisrollangle', 'Axis roll angle', 0.0, -180.0, 180.0)
ensure_float('Lettersize', 'Letter size', 0.34, 0.01, 5.0)
ensure_float('Mirrororder', 'Mirror order', 1.0, 0.0, 1.0)
ensure_float('Lettermirrorx', 'Letter mirror X', 1.0, 0.0, 1.0)
ensure_float('Globalspin', 'Global spin', 0.0, -180.0, 180.0)

# View
ensure_float('Viewrotx', 'View rotate X', 0.0, -180.0, 180.0)
ensure_float('Viewroty', 'View rotate Y', 0.0, -180.0, 180.0)
ensure_float('Viewrotz', 'View rotate Z', 0.0, -180.0, 180.0)
ensure_float('Viewscale', 'View scale', 0.1, 0.01, 4.0)
ensure_float('Viewtx', 'View translate X', -0.16, -20.0, 20.0)
ensure_float('Viewty', 'View translate Y', 0.0, -20.0, 20.0)
ensure_float('Viewtz', 'View translate Z', -3.97, -20.0, 20.0)

# V08 depth scale
ensure_float('Depthscaleactive', 'Depth scale active', 1.0, 0.0, 1.0)
ensure_float('Depthscaleamount', 'Depth scale amount', 1.0, 0.0, 2.0)
ensure_float('Depthscalemin', 'Depth scale min', 0.58, 0.05, 5.0)
ensure_float('Depthscalemax', 'Depth scale max', 1.38, 0.05, 5.0)
ensure_float('Depthscalecurve', 'Depth scale curve', 1.15, 0.1, 5.0)
ensure_float('Depthscaleflip', 'Depth scale flip', 0.0, 0.0, 1.0)
ensure_float('Depthscalemode', 'Depth scale mode', 0.0, 0.0, 1.0)

# V10 height stretch
ensure_float('Heightstretchactive', 'Height stretch active', 1.0, 0.0, 1.0)
ensure_float('Heightstretchamount', 'Height stretch amount', 1.0, 0.0, 2.0)
ensure_float('Heightstretchminback', 'Height min back', 0.72, 0.05, 5.0)
ensure_float('Heightstretchmaxfront', 'Height max front', 1.42, 0.05, 5.0)
ensure_float('Heightstretchcurve', 'Height stretch curve', 1.10, 0.1, 5.0)
ensure_float('Heightstretchflip', 'Height stretch flip', 0.0, 0.0, 1.0)
ensure_float('Heightstretchmode', 'Height stretch mode', 0.0, 0.0, 1.0)

# V11 back mirror
ensure_float('Backmirroractive', 'Back mirror active', 1.0, 0.0, 1.0)
ensure_float('Backmirrorthreshold', 'Back mirror threshold', 0.0, -1.0, 1.0)
ensure_float('Backmirrorinvert', 'Back mirror invert', 0.0, 0.0, 1.0)
ensure_float('Backmirrormode', 'Back mirror mode', 0.0, 0.0, 1.0)
ensure_float('Backmirroraxis', 'Back mirror axis', 0.0, 0.0, 2.0)

# V09 curve
ensure_float('Curvedeformactive', 'Curve deform active', 1.0, 0.0, 1.0)
ensure_float('Curvedeformamount', 'Curve deform amount', 1.0, 0.0, 2.0)
ensure_float('Curvecurvature', 'Curve curvature', 1.0, 0.0, 5.0)
ensure_float('Curveoffset', 'Curve offset', 0.075, -2.0, 2.0)
ensure_float('Curveextrudegain', 'Curve extrude gain', 1.25, 0.0, 5.0)
ensure_float('Curvemode', 'Curve mode', 0.0, 0.0, 1.0)
ensure_float('Curveflip', 'Curve flip', 0.0, 0.0, 1.0)
ensure_float('Curvemaxangle', 'Curve max angle', 38.0, 1.0, 90.0)

# V12/V12D material and extrusion
ensure_float('Strandar', 'Strand A red', 0.38, 0.0, 1.0)
ensure_float('Strandag', 'Strand A green', 0.72, 0.0, 1.0)
ensure_float('Strandab', 'Strand A blue', 1.00, 0.0, 1.0)
ensure_float('Strandbr', 'Strand B red', 1.00, 0.0, 1.0)
ensure_float('Strandbg', 'Strand B green', 0.52, 0.0, 1.0)
ensure_float('Strandbb', 'Strand B blue', 0.95, 0.0, 1.0)
ensure_float('Letteralpha', 'Letter alpha', 1.0, 0.0, 1.0)
ensure_float('Letterspecular', 'Letter specular', 0.72, 0.0, 2.0)
ensure_float('Lettershininess', 'Letter shininess', 0.78, 0.0, 4.0)
ensure_float('Letteremission', 'Letter emission', 0.065, 0.0, 1.0)
ensure_float('Extrude3ddepth', 'Extrude 3D depth', 0.070, 0.0, 0.5)
ensure_float('Extrude3dtextlod', 'Text LOD', 0.65, 0.0, 2.0)

# V13 controls
ensure_float('V13gpuactive', 'V13 GPU active', 1.0, 0.0, 1.0)
ensure_float('V13gpudebugflat', 'V13 GPU debug flat', 0.0, 0.0, 1.0)
ensure_float('V13gpuspecboost', 'V13 GPU spec boost', 1.0, 0.0, 4.0)
ensure_float('V13gpurimboost', 'V13 GPU rim boost', 0.55, 0.0, 4.0)
ensure_float('V13gpuambient', 'V13 GPU ambient', 0.20, 0.0, 2.0)

# -------------------------------------------------------------------------
# 2) Shader DATs
# -------------------------------------------------------------------------
vert = create_or_get(root, ['textDAT'], 'v13_gpu_letter_vert', destroy=True)
frag = create_or_get(root, ['textDAT'], 'v13_gpu_letter_frag', destroy=True)

vert.text = '''
#version 330 core

in vec3 P;
in vec3 N;

out VS_OUT
{
    vec3 worldPos;
    vec3 worldNormal;
    vec3 baseColor;
    float alpha;
} vsOut;

uniform vec4 uLetterIndex;   // x = letter index
uniform vec4 uTimeVec;       // x = seconds

uniform vec4 uHelix0;        // radius, pitch, turns, speed
uniform vec4 uHelix1;        // axisRollSpeed, axisRollAngleDeg, globalSpinDeg, letterCount
uniform vec4 uText0;         // letterSize, mirrorOrder, letterMirrorX, unused

uniform vec4 uViewRot;       // rx, ry, rz, viewScale
uniform vec4 uViewTr;        // tx, ty, tz, unused

uniform vec4 uDepth0;        // active, amount, min, max
uniform vec4 uDepth1;        // curve, flip, mode, unused

uniform vec4 uHeight0;       // active, amount, minBack, maxFront
uniform vec4 uHeight1;       // curve, flip, mode, unused

uniform vec4 uBack0;         // active, threshold, invert, mode
uniform vec4 uBack1;         // axis, unused, unused, unused

uniform vec4 uCurve0;        // active, amount, curvature, offset
uniform vec4 uCurve1;        // extrudeGain, mode, flip, maxAngleDeg

uniform vec4 uBaseColor;     // rgb + alpha
uniform vec4 uShade0;        // specular, shininess, emission, ambient
uniform vec4 uDebug0;        // flatDebug, unused, unused, unused

const float PI  = 3.14159265358979323846;
const float TAU = 6.28318530717958647692;

float saturate(float x)
{
    return clamp(x, 0.0, 1.0);
}

vec3 rotateXYZ(vec3 p, vec3 degs)
{
    vec3 r = radians(degs);

    float cx = cos(r.x);
    float sx = sin(r.x);
    float cy = cos(r.y);
    float sy = sin(r.y);
    float cz = cos(r.z);
    float sz = sin(r.z);

    p = vec3(p.x, p.y * cx - p.z * sx, p.y * sx + p.z * cx);
    p = vec3(p.x * cy + p.z * sy, p.y, -p.x * sy + p.z * cy);
    p = vec3(p.x * cz - p.y * sz, p.x * sz + p.y * cz, p.z);

    return p;
}

float normalizedFrontness(float localFrontZ, float cameraFrontZ, float radius, float viewScale, float mode)
{
    if (mode >= 0.5)
    {
        float denom = max(0.001, abs(radius * viewScale));
        return clamp(cameraFrontZ / denom, -1.0, 1.0);
    }
    else
    {
        float denom = max(0.001, abs(radius));
        return clamp(localFrontZ / denom, -1.0, 1.0);
    }
}

float depthScaleMultiplier(float localFrontZ, float cameraFrontZ, float radius, float viewScale)
{
    float active = uDepth0.x;
    if (active < 0.5)
        return 1.0;

    float amount = uDepth0.y;
    float minS   = uDepth0.z;
    float maxS   = uDepth0.w;
    float curve  = max(0.001, uDepth1.x);
    float flip   = uDepth1.y;
    float mode   = uDepth1.z;

    float frontness = normalizedFrontness(localFrontZ, cameraFrontZ, radius, viewScale, mode);
    if (flip >= 0.5)
        frontness *= -1.0;

    float t = saturate(0.5 + 0.5 * frontness);
    t = pow(t, curve);

    float target = mix(minS, maxS, t);
    return mix(1.0, target, amount);
}

float heightStretchMultiplier(float localFrontZ, float cameraFrontZ, float radius, float viewScale)
{
    float active = uHeight0.x;
    if (active < 0.5)
        return 1.0;

    float amount   = uHeight0.y;
    float minBack  = uHeight0.z;
    float maxFront = uHeight0.w;
    float curve    = max(0.001, uHeight1.x);
    float flip     = uHeight1.y;
    float mode     = uHeight1.z;

    float frontness = normalizedFrontness(localFrontZ, cameraFrontZ, radius, viewScale, mode);
    if (flip >= 0.5)
        frontness *= -1.0;

    float t = saturate(0.5 + 0.5 * frontness);
    t = pow(t, curve);

    float target = mix(minBack, maxFront, t);
    return mix(1.0, target, amount);
}

bool backMirrorState(float localFrontZ, float cameraFrontZ, float radius, float viewScale)
{
    if (uBack0.x < 0.5)
        return false;

    float threshold = uBack0.y;
    float invertVal = uBack0.z;
    float mode      = uBack0.w;

    float frontness = normalizedFrontness(localFrontZ, cameraFrontZ, radius, viewScale, mode);
    bool back = frontness < threshold;

    if (invertVal >= 0.5)
        back = !back;

    return back;
}

void main()
{
    float i = uLetterIndex.x;
    float n = max(1.0, uHelix1.w);

    float radius        = uHelix0.x;
    float pitch         = uHelix0.y;
    float turns         = uHelix0.z;
    float speed         = uHelix0.w;
    float axisRollSpeed = uHelix1.x;
    float axisRollAngle = uHelix1.y;
    float globalSpin    = uHelix1.z;
    float letterSize    = uText0.x;
    float mirrorOrder   = uText0.y;
    float letterMirrorX = uText0.z;

    float timeSec = uTimeVec.x;

    float j = (mirrorOrder >= 0.5) ? ((n - 1.0) - i) : i;
    float tWord = (n <= 1.0) ? 0.0 : (j / (n - 1.0));
    float axisX = (j - (n - 1.0) * 0.5) * pitch;
    float strandOffset = mod(i, 2.0) * PI;

    float phase = timeSec * speed * TAU;
    float angle = tWord * TAU * turns + phase + strandOffset + radians(globalSpin);

    float roll  = timeSec * axisRollSpeed * TAU + radians(axisRollAngle);
    float theta = angle + roll;

    vec3 base = vec3(axisX, cos(theta) * radius, sin(theta) * radius);
    vec3 axisVec    = vec3(1.0, 0.0, 0.0);
    vec3 tangentVec = normalize(vec3(0.0, -sin(theta), cos(theta)));
    vec3 normalVec  = normalize(vec3(0.0,  cos(theta), sin(theta)));

    vec3 baseForCam = base * uViewRot.w;
    vec3 baseCamRot = rotateXYZ(baseForCam, uViewRot.xyz);
    float cameraFrontZ = baseCamRot.z;
    float localFrontZ  = base.z;

    float dsm = depthScaleMultiplier(localFrontZ, cameraFrontZ, radius, uViewRot.w);
    float hsm = heightStretchMultiplier(localFrontZ, cameraFrontZ, radius, uViewRot.w);

    float pulse = 1.0 + 0.035 * sin(phase * 2.0 + i * 0.71);
    float glyphScale = letterSize * pulse * dsm;

    float lx = P.x * glyphScale;
    float ly = P.y * glyphScale * hsm;
    float lz = P.z * glyphScale * uCurve1.x;

    float nx = N.x;
    float ny = N.y;
    float nz = N.z;

    if (letterMirrorX >= 0.5)
    {
        lx *= -1.0;
        nx *= -1.0;
    }

    bool doBackMirror = backMirrorState(localFrontZ, cameraFrontZ, radius, uViewRot.w);
    int backAxis = int(floor(uBack1.x + 0.5));

    if (doBackMirror)
    {
        if (backAxis == 0)
        {
            ly *= -1.0;
            ny *= -1.0;
        }
        else if (backAxis == 1)
        {
            lx *= -1.0;
            nx *= -1.0;
        }
        else
        {
            lx *= -1.0;
            ly *= -1.0;
            nx *= -1.0;
            ny *= -1.0;
        }
    }

    vec3 flatPos = base + axisVec * lx + tangentVec * ly + normalVec * (uCurve0.w + lz);

    float curveAmount   = (uCurve0.x < 0.5) ? 0.0 : clamp(uCurve0.y, 0.0, 1.0);
    float curvature     = uCurve0.z;
    float curveMode     = uCurve1.y;
    float curveFlip     = uCurve1.z;
    float maxAngle      = radians(max(0.001, uCurve1.w));

    float axialOffset;
    float angularSource;

    if (curveMode < 0.5)
    {
        axialOffset = lx;
        angularSource = ly;
    }
    else
    {
        axialOffset = ly;
        angularSource = lx;
    }

    if (curveFlip >= 0.5)
        angularSource *= -1.0;

    float angularOffset = clamp((angularSource / max(0.001, radius)) * curvature, -maxAngle, maxAngle);

    float thetaP = theta + angularOffset;
    float rP     = radius + uCurve0.w + lz;

    vec3 curvedPos = vec3(base.x + axialOffset, cos(thetaP) * rP, sin(thetaP) * rP);
    vec3 finalLocal = mix(flatPos, curvedPos, curveAmount);

    vec3 tangentP = normalize(vec3(0.0, -sin(thetaP), cos(thetaP)));
    vec3 normalP  = normalize(vec3(0.0,  cos(thetaP), sin(thetaP)));
    vec3 axisP    = axisVec;

    vec3 basisX;
    vec3 basisY;
    vec3 basisZ = normalP;

    if (curveMode < 0.5)
    {
        basisX = axisP;
        basisY = tangentP;
    }
    else
    {
        basisX = tangentP;
        basisY = axisP;
    }

    if (curveFlip >= 0.5)
        basisY *= -1.0;

    vec3 deformedNormal = normalize(nx * basisX + ny * basisY + nz * basisZ);

    if (uDebug0.x >= 0.5)
    {
        finalLocal = base + axisVec * lx + tangentVec * ly + normalVec * (uCurve0.w + lz);
        deformedNormal = normalize(nx * axisVec + ny * tangentVec + nz * normalVec);
    }

    vec3 worldPos = finalLocal * uViewRot.w;
    worldPos = rotateXYZ(worldPos, uViewRot.xyz);
    worldPos += uViewTr.xyz;

    vec3 worldNormal = rotateXYZ(deformedNormal, uViewRot.xyz);
    worldNormal = normalize(worldNormal);

    vsOut.worldPos = worldPos;
    vsOut.worldNormal = worldNormal;
    vsOut.baseColor = uBaseColor.rgb;
    vsOut.alpha = uBaseColor.a;

    gl_Position = uTDMats[0].worldCamProj * vec4(worldPos, 1.0);
}
'''

frag.text = '''
#version 330 core

in VS_OUT
{
    vec3 worldPos;
    vec3 worldNormal;
    vec3 baseColor;
    float alpha;
} fsIn;

layout(location = 0) out vec4 fragColor;

uniform vec4 uShade0; // specular, shininess, emission, ambient
uniform vec4 uDebug0; // flatDebug, specBoost, rimBoost, ambientOverride
uniform vec4 uLight0; // keyDir xyz (world-ish), intensity
uniform vec4 uLight1; // fillDir xyz, intensity
uniform vec4 uLight2; // rimDir xyz, intensity

void main()
{
    vec3 N = normalize(fsIn.worldNormal);
    vec3 V = normalize(vec3(0.0, 0.0, 8.0) - fsIn.worldPos);

    vec3 L0 = normalize(uLight0.xyz);
    vec3 L1 = normalize(uLight1.xyz);
    vec3 L2 = normalize(uLight2.xyz);

    float ambient   = max(0.0, uShade0.w) * max(0.0, uDebug0.w);
    float diff0     = max(dot(N, L0), 0.0) * uLight0.w;
    float diff1     = max(dot(N, L1), 0.0) * uLight1.w;

    vec3 H0         = normalize(L0 + V);
    vec3 H1         = normalize(L1 + V);
    float shininess = max(1.0, 4.0 + uShade0.y * 96.0);
    float spec0     = pow(max(dot(N, H0), 0.0), shininess) * uShade0.x * uDebug0.y;
    float spec1     = pow(max(dot(N, H1), 0.0), shininess) * (uShade0.x * 0.65) * uDebug0.y;

    float rim = pow(1.0 - max(dot(N, V), 0.0), 2.2) * uDebug0.z * uLight2.w;

    vec3 color = fsIn.baseColor * (ambient + diff0 + diff1)
               + vec3(spec0 + spec1)
               + fsIn.baseColor * (uShade0.z)
               + fsIn.baseColor * rim * 0.5;

    fragColor = vec4(color, fsIn.alpha);
}
'''

# -------------------------------------------------------------------------
# 3) Helper to configure GLSL MAT uniforms
# -------------------------------------------------------------------------
def configure_glsl_mat_uniforms(mat, letter_index, strand='A'):
    if mat is None:
        return

    set_val(mat, ['glslversion'], 'glsl330', verbose=False)
    set_val(mat, ['vdat'], vert.path)
    set_val(mat, ['pdat'], frag.path)

    set_val(mat, ['vec'], 21, verbose=False)

    def set_vec(i, name, exprx, expry='0', exprz='0', exprw='0'):
        set_val(mat, ['vec%dname' % i], name, verbose=False)
        set_expr(mat, 'vec%dvaluex' % i, exprx, verbose=False)
        set_expr(mat, 'vec%dvaluey' % i, expry, verbose=False)
        set_expr(mat, 'vec%dvaluez' % i, exprz, verbose=False)
        set_expr(mat, 'vec%dvaluew' % i, exprw, verbose=False)

    set_vec(0,  'uLetterIndex', str(float(letter_index)), '0', '0', '0')
    set_vec(1,  'uTimeVec', 'absTime.seconds', '0', '0', '0')

    set_vec(2,  'uHelix0', expr_par('Radius'), expr_par('Pitch'), expr_par('Turns'), expr_par('Speed'))
    set_vec(3,  'uHelix1', expr_par('Axisrollspeed'), expr_par('Axisrollangle'), expr_par('Globalspin'), str(float(len(WORD))))
    set_vec(4,  'uText0', expr_par('Lettersize'), expr_par('Mirrororder'), expr_par('Lettermirrorx'), '0')

    set_vec(5,  'uViewRot', expr_par('Viewrotx'), expr_par('Viewroty'), expr_par('Viewrotz'), expr_par('Viewscale'))
    set_vec(6,  'uViewTr', expr_par('Viewtx'), expr_par('Viewty'), expr_par('Viewtz'), '0')

    set_vec(7,  'uDepth0', expr_par('Depthscaleactive'), expr_par('Depthscaleamount'), expr_par('Depthscalemin'), expr_par('Depthscalemax'))
    set_vec(8,  'uDepth1', expr_par('Depthscalecurve'), expr_par('Depthscaleflip'), expr_par('Depthscalemode'), '0')

    set_vec(9,  'uHeight0', expr_par('Heightstretchactive'), expr_par('Heightstretchamount'), expr_par('Heightstretchminback'), expr_par('Heightstretchmaxfront'))
    set_vec(10, 'uHeight1', expr_par('Heightstretchcurve'), expr_par('Heightstretchflip'), expr_par('Heightstretchmode'), '0')

    set_vec(11, 'uBack0', expr_par('Backmirroractive'), expr_par('Backmirrorthreshold'), expr_par('Backmirrorinvert'), expr_par('Backmirrormode'))
    set_vec(12, 'uBack1', expr_par('Backmirroraxis'), '0', '0', '0')

    set_vec(13, 'uCurve0', expr_par('Curvedeformactive'), expr_par('Curvedeformamount'), expr_par('Curvecurvature'), expr_par('Curveoffset'))
    set_vec(14, 'uCurve1', expr_par('Curveextrudegain'), expr_par('Curvemode'), expr_par('Curveflip'), expr_par('Curvemaxangle'))

    if strand == 'A':
        set_vec(15, 'uBaseColor', expr_par('Strandar'), expr_par('Strandag'), expr_par('Strandab'), expr_par('Letteralpha'))
    else:
        set_vec(15, 'uBaseColor', expr_par('Strandbr'), expr_par('Strandbg'), expr_par('Strandbb'), expr_par('Letteralpha'))

    set_vec(16, 'uShade0', expr_par('Letterspecular'), expr_par('Lettershininess'), expr_par('Letteremission'), expr_par('V13gpuambient'))
    set_vec(17, 'uDebug0', expr_par('V13gpudebugflat'), expr_par('V13gpuspecboost'), expr_par('V13gpurimboost'), '1')

    set_vec(18, 'uLight0', '0.42', '0.70', '0.58', '1.0')
    set_vec(19, 'uLight1', '-0.35', '-0.15', '0.85', '0.45')
    set_vec(20, 'uLight2', '-0.25', '0.35', '-0.90', '1.15')

    set_val(mat, ['blending'], False, verbose=False)
    set_val(mat, ['depthwriting'], True, verbose=False)
    set_val(mat, ['cullface'], 'neither', verbose=False)

    p = get_par(mat, 'loaduniformnames')
    if p is not None:
        try:
            p.pulse()
        except Exception:
            pass

# -------------------------------------------------------------------------
# 4) Build static GPU geometry path for each letter
# -------------------------------------------------------------------------
letter_geo_paths = []

for i, ch in enumerate(WORD):
    geo = root.op('letter_%02d_%s' % (i, ch))
    if geo is None:
        print('WARNING missing letter geo', i, ch)
        continue

    set_flag(geo, 'display', True)
    set_flag(geo, 'render', True)

    for pname, val in [('tx',0),('ty',0),('tz',0),('rx',0),('ry',0),('rz',0),('sx',1),('sy',1),('sz',1)]:
        set_val(geo, [pname], val, verbose=False)

    text_sop = None
    for c in geo.children:
        if c.family == 'SOP' and c.name.startswith('text_'):
            text_sop = c
            break

    if text_sop is None:
        print('WARNING no text SOP in', geo.path)
        continue

    set_val(text_sop, ['text'], ch, verbose=False)
    set_val(text_sop, ['output'], 'closedpolys', verbose=False)
    set_expr_by_names(text_sop, ['levelofdetail'], expr_par('Extrude3dtextlod'), keywords=['lod', 'level of detail'], verbose=False)

    hole = create_or_get(geo, ['holeSOP'], 'hole_letter_v13_gpu', destroy=False)
    if hole is not None:
        hole.nodeX = text_sop.nodeX + 130
        hole.nodeY = text_sop.nodeY
        connect(text_sop, hole, 0)
        source = hole
    else:
        source = text_sop

    extrude = create_or_get(geo, ['extrudeSOP'], 'extrude_letter_v13_gpu', destroy=False)
    if extrude is not None:
        extrude.nodeX = text_sop.nodeX + 300
        extrude.nodeY = text_sop.nodeY
        connect(source, extrude, 0)

        set_expr_by_names(extrude, ['depthscale'], expr_par('Extrude3ddepth'), keywords=['depth scale'], verbose=False)
        set_expr_by_names(extrude, ['depthxlate'], '-0.5 * ' + expr_par('Extrude3ddepth'), keywords=['depth translate'], verbose=False)
        set_val(extrude, ['sharefaces'], True, verbose=False)
        set_val(extrude, ['removesharedsides'], True, verbose=False)
        set_val(extrude, ['dofuse'], 'all', verbose=False)
        set_val(extrude, ['docusp'], True, verbose=False)
        set_val(extrude, ['cuspangle'], 28, verbose=False)
        source2 = extrude
    else:
        source2 = source

    facet = create_or_get(geo, ['facetSOP'], 'facet_letter_v13_gpu', destroy=False)
    if facet is not None:
        facet.nodeX = text_sop.nodeX + 450
        facet.nodeY = text_sop.nodeY
        connect(source2, facet, 0)
        set_val(facet, ['docusp'], True, verbose=False)
        set_val(facet, ['cuspangle'], 30, verbose=False)
        set_val(facet, ['postnml'], True, verbose=False)
        set_val(facet, ['normals'], True, verbose=False)
        source3 = facet
    else:
        source3 = source2

    center = create_or_get(geo, ['xformSOP', 'transformSOP'], 'center_letter_v13_gpu', destroy=False)
    if center is not None:
        center.nodeX = text_sop.nodeX + 620
        center.nodeY = text_sop.nodeY
        connect(source3, center, 0)
        center_sop_with_bbox(source3, center)
        source4 = center
    else:
        source4 = source3

    outnull = create_or_get(geo, ['nullSOP'], 'OUT_LETTER_GPU_V13', destroy=False)
    if outnull is not None:
        outnull.nodeX = text_sop.nodeX + 790
        outnull.nodeY = text_sop.nodeY
        connect(source4, outnull, 0)
        final_sop = outnull
    else:
        final_sop = source4

    for c in geo.children:
        if c.family == 'SOP':
            set_flag(c, 'display', False)
            set_flag(c, 'render', False)
    set_flag(final_sop, 'display', True)
    set_flag(final_sop, 'render', True)

    glsl_mat = create_or_get(root, ['glslMAT'], 'mat_letter_gpu_v13_%02d_%s' % (i, ch), destroy=False)
    if glsl_mat is not None:
        glsl_mat.nodeX = 1020 + (i % 4) * 170
        glsl_mat.nodeY = -260 - (i // 4) * 110
        configure_glsl_mat_uniforms(glsl_mat, i, 'A' if i % 2 == 0 else 'B')
        set_val(geo, ['material', 'mat'], glsl_mat.path)

    old_deform = geo.op('bend_letter_v09')
    if old_deform is not None:
        set_flag(old_deform, 'display', False)
        set_flag(old_deform, 'render', False)

    try:
        final_sop.cook(force=True)
    except Exception:
        pass

    letter_geo_paths.append(geo.path)

# -------------------------------------------------------------------------
# 5) Render paths + output TOP
# -------------------------------------------------------------------------
tube_paths = []
for name in ['helix_tube_surface_v06', 'helix_tube_wire_v06']:
    tg = root.op(name)
    if tg is not None:
        set_flag(tg, 'display', True)
        set_flag(tg, 'render', True)
        tube_paths.append(tg.path)

render = root.op('render1')
cam = root.op('cam1')
if render is not None:
    if cam is not None:
        set_val(render, ['camera', 'cameras'], cam.path)
    set_val(render, ['geometry', 'geo', 'geometries'], ' '.join(letter_geo_paths + tube_paths))
    try:
        render.cook(force=True)
    except Exception:
        pass

out_top = root.op('OUT_RENDER_VIEW_THIS')
if out_top is not None and render is not None:
    try:
        out_top.inputConnectors[0].connect(render)
    except Exception:
        pass
    try:
        out_top.cook(force=True)
    except Exception:
        pass

# -------------------------------------------------------------------------
# 6) Debug report
# -------------------------------------------------------------------------
debug = create_or_get(root, ['tableDAT'], 'debug_v13_gpu_glsl', destroy=False)
if debug is not None:
    debug.nodeX = 780
    debug.nodeY = -1210
    try:
        debug.clear()
        debug.appendRow(['key', 'value'])
        debug.appendRow(['mode', 'GPU / GLSL'])
        debug.appendRow(['shader_vert', vert.path])
        debug.appendRow(['shader_frag', frag.path])
        debug.appendRow(['letters', len(letter_geo_paths)])
        debug.appendRow(['tube_paths', len(tube_paths)])
        debug.appendRow(['note_1', 'If letters disappear, inspect mat_letter_gpu_v13_XX info for shader compile errors.'])
        debug.appendRow(['note_2', 'Open OUT_RENDER_VIEW_THIS or render1, not the Base viewer, to judge final output.'])
        debug.appendRow(['note_3', 'Rerun V12D to restore CPU-deformed path if needed.'])
    except Exception as e:
        print('WARNING debug failed', e)

try:
    root.layout(root.children)
except Exception:
    pass

print('=' * 72)
print('MORPHOGENESIS DNA V13 GPU / GLSL OK')
print('Open:', ROOT_PATH + '/OUT_RENDER_VIEW_THIS')
print('or:', ROOT_PATH + '/render1')
print('Debug:', ROOT_PATH + '/debug_v13_gpu_glsl')
print('If a shader shows checkerboard:')
print('  open one of the mat_letter_gpu_v13_* materials and inspect Info DAT / shader compile status.')
print('To rollback to CPU deformation, rerun V12D.')
print('=' * 72)
