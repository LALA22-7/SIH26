# CycloneWatch — Pattern Taxonomy

> **Status:** Locked. Do not rename labels without coordinating with Backend Lead (DB migration required).
> **Source:** IBTrACS intensity thresholds + standard Dvorak technique structural descriptions.

---

## The 5 pattern labels

### 1. `eye`
**Wind threshold:** ≥ 120 knots (≥ 222 km/h) — IMD "Super Cyclonic Storm" or near-peak intensity

**What you see in IR:**
A dark, warm circular region at the centre (the eye) surrounded by a dense ring of very cold cloud tops (the eyewall). Tight, symmetric spiral bands radiate outward.

**Include:**
- Clear circular or near-circular warm core
- Dense overcast ring surrounding the centre
- Peak intensity phase of the storm

**Exclude:**
- An embedded centre without a clear warm eye (classify as `banding` instead)

**Example events:** Amphan 2020 at peak, Fani 2019 at peak

---

### 2. `banding`
**Wind threshold:** 64–119 knots (119–220 km/h) — "Severe" to "Very Severe" intensity

**What you see in IR:**
Multiple well-defined spiral bands of cold cloud wrapping around a visible but not always clear centre. Deep convection present. The storm looks organised and tightening.

**Include:**
- Organised spiral banding with a definable centre
- Active intensification or near-peak phase without clear eye
- Multiple distinct cloud bands

**Exclude:**
- Single, loose band (classify as `curved_band`)
- Clear warm-core eye present (classify as `eye`)

**Example events:** Biparjoy 2023 during intensification, Hudhud 2014 approach phase

---

### 3. `curved_band`
**Wind threshold:** 34–63 knots (63–116 km/h) — "Cyclonic Storm" intensity

**What you see in IR:**
A single curved band of cloud, loosely wrapped. The centre may be defined but not tightly organised. This is either an intensifying early-stage storm or a weakening remnant.

**Include:**
- Single primary cloud band with curvature
- Early development or post-peak weakening
- Centre identifiable but convection is asymmetric or loose

**Exclude:**
- Multiple organised bands (classify as `banding`)
- No coherent structure (classify as `disorganized`)

**Example events:** Ockhi 2017 early stage, Biparjoy 2023 early development

---

### 4. `shear_affected`
**Wind threshold:** ≥ 34 knots AND intensity drop ≥ 15 knots in 6 hours

**What you see in IR:**
The deep convection is displaced downshear — the coldest cloud tops are not centred over the circulation. The storm looks lopsided. This is caused by environmental wind shear tearing the vertical structure apart.

**Include:**
- Asymmetric convection clearly displaced from centre
- Rapid weakening rate (≥15 kt / 6h)
- Warm, exposed low-level circulation visible on one side

**Exclude:**
- Symmetric weakening without shear (classify as `curved_band`)

**Example events:** Biparjoy 2023 weakening phase after Gujarat landfall

---

### 5. `disorganized`
**Wind threshold:** < 34 knots — Depression or well-marked low

**What you see in IR:**
Scattered convection with no coherent structure. No identifiable centre in the cloud field. This is either a newly forming depression or a storm that has mostly dissipated.

**Include:**
- No clear spiral banding
- Scattered thunderstorm clusters
- Early depression stage before organisation
- Post-landfall remnant

**Exclude:**
- Any organised circulation with winds ≥ 34 knots

**Example events:** All 7 storms in their early depression and final weakening phases

---

## Label source and confidence

All 423 training labels were assigned algorithmically from IBTrACS WMO wind speed and 6-hour intensity change rates. They were **not manually verified against actual satellite imagery** — this is a known limitation.

For the demo: labels are presented as model outputs, not ground truth. The evidence panel shows the source satellite frame so a judge can verify visually.

**Label source string in data:** `ibtracs_intensity_rules`
