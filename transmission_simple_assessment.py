import math
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

def classify_magnitude(value):
    """
    Classify a cell-count value:
      1–7   => Very low
      8–14  => Low
      15–25 => Moderate
      26–36 => High
      37+   => Very high
    """
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

def compute_sums(tower_height_m, span_between_towers_m, tower_angle_deg):
    """
    Computes the unique occupied 10° horizontal cells based on the tower
    geometry. For each x in -4000 to +4000 (step=span_between_towers_m),
    the horizontal angle (phi) is computed and binned into 10° cells.
    Towers with a raw angle > 3° count as "main"; the function returns
    the unique cell count for main (and side) towers.
    """
    angle_radians = math.radians(tower_angle_deg)
    if abs(math.tan(angle_radians)) < 1e-12:
        return (0, 0, 0.0), (0, 0, 0.0)
    
    d = tower_height_m / math.tan(angle_radians)
    main_cells = set()
    side_cells = set()
    
    for x in range(-4000, 4001, int(span_between_towers_m)):
        r = math.hypot(d, x)
        if r <= 0:
            continue
        raw_angle = math.degrees(math.atan(tower_height_m / r))
        if raw_angle < 0.1:
            continue
        
        # Compute horizontal angle phi
        if x == 0:
            phi = 95.0  # central tower pinned at 95°
        else:
            phi_calc = math.degrees(math.atan(abs(x)/d))
            phi = 95 + phi_calc if x > 0 else 95 - phi_calc
            phi = max(0, min(180, phi))
        
        cell = int(phi // 10)
        if raw_angle > 3.0:
            main_cells.add(cell)
        else:
            side_cells.add(cell)
    
    main_count = len(main_cells)
    side_count = len(side_cells)
    return (main_count, main_count, float(main_count)), (side_count, side_count, float(side_count))

def visualize_towers(tower_height_m, span_between_towers_m, tower_angle_deg, f3, c3, d3, classification, triggers_intermediate):
    """
    Creates an alignment chart using a simple rectangle for each tower.
    The rectangle's height exactly equals the computed top angle (capped at 40°).
    The horizontal position is determined by the computed phi.
    """
    angle_radians = math.radians(tower_angle_deg)
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
        
        # Compute horizontal angle phi.
        if x == 0:
            phi = 95.0
        else:
            phi_calc = math.degrees(math.atan(abs(x)/d))
            phi = 95 + phi_calc if x > 0 else 95 - phi_calc
            phi = max(0, min(180, phi))
        
        color = 'red' if raw_angle > 3.0 else 'blue'
        # Use the full raw_angle up to a maximum of 40° as the tower's height.
        top_deg = min(raw_angle, 40.0)
        towers_data.append((phi, top_deg, color))

    # Create a high-resolution figure.
    fig, ax = plt.subplots(figsize=(12, 3), dpi=300)
    
    # Draw vertical grid lines at every 10° on the horizontal axis.
    for xv in range(0, 181, 10):
        ax.axvline(x=xv, color='gray', lw=0.5, alpha=0.5)
    # Draw horizontal grid lines for every degree on the vertical axis.
    for yv in range(0, 41):
        ax.axhline(y=yv, color='gray', lw=0.5, alpha=0.5)

    ax.set_xticks(range(0, 181, 10))
    ax.set_yticks(range(0, 41, 5))
    
    ax.set_xlim(0, 180)
    ax.set_ylim(0, 40)
    ax.set_xlabel("Horizontal angle (°)")
    ax.set_ylabel("Vertical angle (°)")
    ax.set_title("Transmission Simple Assessment Tool")
    
    # Ensure the plot is drawn to scale.
    ax.set_aspect('equal', adjustable='box')

    # Draw each tower as a simple rectangle.
    for (phi, top_deg, color) in towers_data:
        width = 2.0  # fixed width for simplicity
        lower_left = (phi - width/2, 0)
        rect = Rectangle(lower_left, width, top_deg, facecolor=color, edgecolor=color, alpha=0.6)
        ax.add_patch(rect)

    main_text = (f"Towers >3° => Occupied Cells: {f3} | "
                 f"Classification: {classification} | "
                 f"Intermediate: {'YES' if triggers_intermediate else 'NO'}")
    
    # Increase bottom margin and position the summary text well below the x-axis.
    fig.subplots_adjust(bottom=0.7)
    fig.text(0.5, 0.0, main_text, ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    return fig

# --- Streamlit App Interface ---
st.title("Simple Tower Assessment Tool")
st.write("Enter the following values:")

tower_height = st.number_input("Tower Height (m):", value=50.0, step=1.0)
span = st.number_input("Span Between Towers (m):", value=100.0, step=1.0)
tower_angle = st.number_input("Tower Height Angle (°):", min_value=1.0, max_value=20.0, value=5.0, step=0.1)

if st.button("Calculate"):
    (f3, c3, d3), (f_sub3, c_sub3, dec_sub3) = compute_sums(tower_height, span, tower_angle)
    # f3 now represents the count of occupied 10° cells for towers > 3°.
    classification = classify_magnitude(f3)
    triggers_intermediate = (f3 >= 16)

    st.subheader("RESULTS:")
    st.write(f"**Tower Height (m):** {tower_height}")
    st.write(f"**Span Between Towers (m):** {span}")
    st.write(f"**Tower Height Angle (°):** {tower_angle:.1f}")
    st.write("---")
    st.write("**MAIN CALCULATIONS (Towers >3°):**")
    st.write(f"Occupied 1×10° Cells: {f3}")
    st.write(f"Classification: {classification}")
    if triggers_intermediate:
        st.write("NOTE: Occupied cell count >=16, triggering intermediate assessment.")
    st.write("")
    st.write("**SIDE CALCULATION (Towers ≤3):**")
    st.write(f"Occupied 1×10° Cells: {f_sub3}")
    
    # Display the alignment chart.
    fig = visualize_towers(tower_height, span, tower_angle, f3, c3, d3, classification, triggers_intermediate)
    if fig is not None:
        st.pyplot(fig)
