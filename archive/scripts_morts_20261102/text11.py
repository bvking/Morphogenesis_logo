# archive du DAT /project1/text11 (purge du 2026-11-02)
# morphogenesis_dna_td_v13b_GLSL_COMPILE_FIX.py
# TouchDesigner 2025.32460 / Python 3.11
#
# Correctif V13B:
# - Supprime les lignes '#version 330 core' des DAT shaders.
#   Dans GLSL MAT, la version est déjà donnée par le paramètre glslversion.
# - Remplace les attributs explicites 'in vec3 P;' / 'in vec3 N;' par les fonctions TD:
#      vec3 P = TDPos();
#      vec3 N = TDNormal();
# - Remplace uTDMats[0].worldCamProj par TDWorldToProj(vec4(worldPos, 1.0)).
#
# À lancer après la V13 si tu as:
# '#version : must occur first in shader'
# ou
# '#version : bad profile name'
#
# Usage:
# 1) Colle ce script dans un Text DAT.
# 2) Run Script.
# 3) Ouvre /project1/MORPHOGENESIS_DNA_TD/OUT_RENDER_VIEW_THIS

ROOT_PATH = '/project1/MORPHOGENESIS_DNA_TD'
WORD = 'MORPHOGENESIS'

root = op(ROOT_PATH)
if root is None:
    raise Exception('Container introuvable: ' + ROOT_PATH)

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

def pulse(o, names):
    if o is None:
        return False
    for name in names:
        p = get_par(o, name)
        if p is not None:
            try:
                p.pulse()
                print('PULSE', o.path + '.par.' + p.name)
                return True
            except Exception:
                pass
    return False

def create_or_get(parent, type_names, name):
    existing = parent.op(name)
    if existing is not None:
        return existing
    for tn in type_names:
        try:
            o = parent.create(tn, name)
            print('CREATED', o.path)
            return o
        except Exception as e:
            print('try create failed', tn, e)
    return None

def set_flag(o, flag, value):
    try:
        setattr(o, flag, value)
        return True
    except Exception:
        return False

vert = create_or_get(root, ['textDAT'], 'v13_gpu_letter_vert')
frag = create_or_get(root, ['textDAT'], 'v13_gpu_letter_frag')

# No #version line here.
# TouchDesigner GLSL MAT injects/uses its own version handling from the MAT parameter.
vert.text = '''out VS_OUT
{
    vec3 worldPos;
    vec3 worldNormal;
    vec3 baseColor;
    float alpha;
} vsOut;

uniform vec4 uLetterIndex;
uniform vec4 uTimeVec;

uniform vec4 uHelix0;
uniform vec4 uHelix1;
uniform vec4 uText0;

uniform vec4 uViewRot;
uniform vec4 uViewTr;

uniform vec4 uDepth0;
uniform vec4 uDepth1;

uniform vec4 uHeight0;
uniform vec4 uHeight1;

uniform vec4 uBack0;
uniform vec4 uBack1;

uniform vec4 uCurve0;
uniform vec4 uCurve1;

uniform vec4 uBaseColor;
uniform vec4 uShade0;
uniform vec4 uDebug0;

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
    if (uDepth0.x < 0.5)
        return 1.0;

    float frontness = normalizedFrontness(localFrontZ, cameraFrontZ, radius, viewScale, uDepth1.z);
    if (uDepth1.y >= 0.5)
        frontness *= -1.0;

    float t = saturate(0.5 + 0.5 * frontness);
    t = pow(t, max(0.001, uDepth1.x));

    float target = mix(uDepth0.z, uDepth0.w, t);
    return mix(1.0, target, uDepth0.y);
}

float heightStretchMultiplier(float localFrontZ, float cameraFrontZ, float radius, float viewScale)
{
    if (uHeight0.x < 0.5)
        return 1.0;

    float frontness = normalizedFrontness(localFrontZ, cameraFrontZ, radius, viewScale, uHeight1.z);
    if (uHeight1.y >= 0.5)
        frontness *= -1.0;

    float t = saturate(0.5 + 0.5 * frontness);
    t = pow(t, max(0.001, uHeight1.x));

    float target = mix(uHeight0.z, uHeight0.w, t);
    return mix(1.0, target, uHeight0.y);
}

bool backMirrorState(float localFrontZ, float cameraFrontZ, float radius, float viewScale)
{
    if (uBack0.x < 0.5)
        return false;

    float frontness = normalizedFrontness(localFrontZ, cameraFrontZ, radius, viewScale, uBack0.w);
    bool back = frontness < uBack0.y;

    if (uBack0.z >= 0.5)
        back = !back;

    return back;
}

void main()
{
    vec3 P = TDPos();
    vec3 N = TDNormal();

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

    gl_Position = TDWorldToProj(vec4(worldPos, 1.0));
}
'''

frag.text = '''in VS_OUT
{
    vec3 worldPos;
    vec3 worldNormal;
    vec3 baseColor;
    float alpha;
} fsIn;

out vec4 fragColor;

uniform vec4 uShade0;
uniform vec4 uDebug0;
uniform vec4 uLight0;
uniform vec4 uLight1;
uniform vec4 uLight2;

void main()
{
    TDCheckDiscard();

    vec3 N = normalize(fsIn.worldNormal);
    vec3 V = normalize(vec3(0.0, 0.0, 8.0) - fsIn.worldPos);

    vec3 L0 = normalize(uLight0.xyz);
    vec3 L1 = normalize(uLight1.xyz);

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

# Reconfigure all existing V13 GLSL materials.
fixed = 0
for i, ch in enumerate(WORD):
    mat = root.op('mat_letter_gpu_v13_%02d_%s' % (i, ch))
    if mat is None:
        print('WARNING missing V13 mat for', i, ch)
        continue

    set_val(mat, ['glslversion'], 'glsl330', verbose=False)
    set_val(mat, ['vdat'], vert.path, verbose=False)
    set_val(mat, ['pdat'], frag.path, verbose=False)
    set_val(mat, ['blending'], False, verbose=False)
    set_val(mat, ['depthwriting'], True, verbose=False)
    set_val(mat, ['cullface'], 'neither', verbose=False)

    pulse(mat, ['loaduniformnames'])

    try:
        mat.cook(force=True)
    except Exception as e:
        print('WARNING could not cook', mat.path, e)

    fixed += 1

# Re-render.
render = root.op('render1')
if render is not None:
    try:
        render.cook(force=True)
    except Exception:
        pass

out_top = root.op('OUT_RENDER_VIEW_THIS')
if out_top is not None:
    try:
        out_top.cook(force=True)
    except Exception:
        pass

debug = create_or_get(root, ['tableDAT'], 'debug_v13b_glsl_compile_fix')
if debug is not None:
    try:
        debug.clear()
        debug.appendRow(['key', 'value'])
        debug.appendRow(['fixed_mats', fixed])
        debug.appendRow(['vertex_dat', vert.path])
        debug.appendRow(['fragment_dat', frag.path])
        debug.appendRow(['fix_1', 'No #version line in DAT text'])
        debug.appendRow(['fix_2', 'Use TDPos()/TDNormal() instead of declaring in vec3 P/N'])
        debug.appendRow(['fix_3', 'Use TDWorldToProj(vec4(worldPos, 1.0))'])
        debug.appendRow(['open', ROOT_PATH + '/OUT_RENDER_VIEW_THIS'])
    except Exception:
        pass

print('=' * 72)
print('V13B GLSL COMPILE FIX DONE')
print('Fixed GLSL MAT count:', fixed)
print('Open:', ROOT_PATH + '/OUT_RENDER_VIEW_THIS')
print('Debug:', ROOT_PATH + '/debug_v13b_glsl_compile_fix')
print('If there is a new shader error, send the new compile log.')
print('=' * 72)
