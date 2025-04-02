import math
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

def classify_magnitude(value):
    if value <= 7:
        return "Very low"
    elif value <= 14:
        return "Low"
    elif value <= 25:
        return "Moderate"
    elif value <= 36:
        return "High"
    else:
        return "Very high"

def compute_sums(tower_height_m, span_between_towers_m, turbine_height_deg):
    angle_radians = math.radians(turbine_height_deg)
    if abs(math.tan(angle_radians)) < 1e-12:
        return (0, 0, 0.0), (0, 0, 0.0)
    d = tower_height_m / math.tan(angle_radians)
    floor_3p = 0
    ceil_3p  = 0
    dec_3p   = 0.0
    floor_sub3 = 0
    ceil_sub3  = 0
    dec_sub3   = 0.0

    for x in range(-4000, 4001, int(span_between_towers_m)):
        r = math.hypot(d, x)
        if r <= 0:
            continue
        raw_angle = math.degrees(math.atan(tower_height_m / r))
        if raw_angle < 0.1:
            continue
        if raw_angle > 3.0:
            floor_3p += math.floor(raw_angle)
            ceil_3p  += math.ceil(raw_angle)
            dec_3p   += raw_angle
        else:
            floor_sub3 += math.floor(raw_angle)
            ceil_sub3  += math.ceil(raw_angle)
            dec_sub3   += raw_angle

    return (floor_3p, ceil_3p, dec_3p), (floor_sub3, ceil_sub3, dec_sub3)

def visualize_towers(tower_height_m, span_between_towers_m, turbine_height_deg, f3, c3, d3, classification, triggers_intermediate):
    angle_radians = math.radians(turbine_height_deg)
    if abs(math.tan(angle_radians)) < 1e-12:
        st.write("Angle too small.")
        return None

    d = tower_height_m / math.tan(angle_radians)
    towers_data = []
    for x in range(-4000, 4001, int(span_between_towers_m)):
        r = math.hypot(d, x)
        if r <= 0:
            continue
        raw_angle = math.degrees(math.atan(tower_height_m / r))
        if raw_angle < 0.1:
            continue
        if x == 0:
            phi = 95.0  # central tower pinned at 95°
        else:
            phi_calc = math.degrees(math.atan(abs(x)/d))
            phi = 95 + phi_calc if x > 0 else 95 - phi_calc
            phi = max(0, min(180, phi))
        color = 'red' if raw_angle > 3.0 else 'blue'
        top_deg = min(raw_angle, 40.0)
        towers_data.append((phi, top_deg, color))

    fig, ax = plt.subplots(figsize=(8,6))
    # grid lines
    for xv in range(0, 181, 10):
        ax.axvline(x=xv, color='gray', lw=0.5, alpha=0.5)
    for yv in range(0, 41):
        ax.axhline(y=yv, color='gray', lw=0.5, alpha=0.5)
    ax.set_xticks(range(0, 181, 10))
    ax.set_yticks(range(0, 41, 1))
    ax.set_xlim(0, 180)
    ax.set_ylim(0, 40)
    ax.set_xlabel("Horizontal angle (°)")
    ax.set_ylabel("Vertical angle (°)")
    ax.set_title("Transmission Simple Assessment Tool")

    # draw polygons
    for (phi, top_angle, color) in towers_data:
        if top_angle <= 0:
            continue
        arm1_y = 0.33 * top_angle
        arm2_y = 0.66 * top_angle
        base_half = 1.0
        verts = [
            (phi - base_half, 0),
            (phi + base_half, 0),
            (phi + 0.6 * base_half, arm1_y),
            (phi + 0.15 * base_half, arm1_y),
            (phi + 0.4 * base_half, arm2_y),
            (phi + 0.05 * base_half, top_angle),
            (phi - 0.05 * base_half, top_angle),
            (phi - 0.4 * base_half, arm2_y),
            (phi - 0.15 * base_half, arm1_y),
            (phi - 0.6 * base_half, arm1_y),
            (phi - base_half, 0)
        ]
        tower_poly = Polygon(verts, closed=True, facecolor=color, edgecolor=color, alpha=0.6)
        ax.add_patch(tower_poly)

    main_text = (f"Towers >3° => Lower={f3}, Upper={c3}, Decimal={d3:.2f}, "
                 f"Classification={classification}, "
                 f"Intermediate={'YES' if triggers_intermediate else 'NO'}")
    fig.text(0.5, 0.01, main_text, ha='center', va='bottom', fontsize=9)
    plt.tight_layout()
    return fig

# --- Streamlit App Interface ---
st.title("Simple Tower Assessment Tool")
st.write("Enter the following values:")

tower_height = st.number_input("Tower Height (m):", value=50.0, step=1.0)
span = st.number_input("Span Between Towers (m):", value=100.0, step=1.0)
turbine_height = st.number_input("Turbine Height (°) [1..20]:", min_value=1.0, max_value=20.0, value=5.0, step=0.1)

if st.button("Calculate"):
    (f3, c3, d3), (f_sub3, c_sub3, dec_sub3) = compute_sums(tower_height, span, turbine_height)
    classification = classify_magnitude(c3)
    triggers_intermediate = (c3 >= 16)

    st.subheader("RESULTS:")
    st.write(f"**Tower Height (m):** {tower_height}")
    st.write(f"**Span Between Towers (m):** {span}")
    st.write(f"**Turbine Height (°):** {turbine_height:.1f}")
    st.write("---")
    st.write("**MAIN CALCULATIONS (Towers >3°):**")
    st.write(f"Lower Range: {f3}, Upper Range: {c3}, Decimal: {d3:.2f}")
    st.write(f"Classification: {classification}")
    if triggers_intermediate:
        st.write("NOTE: sum(ceil) >3° >=16, triggering intermediate assessment.")
    st.write("")
    st.write("**SIDE NOTE (Towers 0.1°..3°):**")
    st.write(f"Lower Range: {f_sub3}, Upper Range: {c_sub3}, Decimal: {dec_sub3:.2f}")
    
    # Directly display the alignment chart after calculations
    fig = visualize_towers(tower_height, span, turbine_height, f3, c3, d3, classification, triggers_intermediate)
    if fig is not None:
        st.pyplot(fig)
