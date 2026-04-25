import re
import random
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

# ── Unified Page Config ────────────────────────────────────────────────────────
st.set_page_config(page_title="Algorithm Visualizers", page_icon="🎲", layout="wide")

# ── CSS for N-Queens ───────────────────────────────────────────────────────────
st.markdown("""
    <style>
    .cell { width: 50px; height: 50px; display: flex; justify-content: center; align-items: center; border: 1px solid #ddd; font-weight: bold; }
    .q-cell { background-color: #ee6c4d; color: white; border-radius: 4px; }
    .safe-cell { background-color: #90e0ef; }
    .dead-cell { background-color: #ef476f; color: white; }
    .current-row { border: 2px solid #ffd166; }
    </style>
""", unsafe_allow_html=True)


# ===============================================================================
# ── APP 1 LOGIC: Monte Carlo Integration ───────────────────────────────────────
# ===============================================================================

# ── Safe eval ──
FUNCS = {
    "sin": np.sin, "cos": np.cos, "tan": np.tan,
    "exp": np.exp, "log": np.log, "ln": np.log,
    "sqrt": np.sqrt, "abs": np.abs,
    "pi": np.pi, "e": np.e, "np": np,
}
BUILTINS = {"__import__": __import__}

def safe_eval(expr, scope):
    return np.asarray(eval(expr, {"__builtins__": BUILTINS}, {**FUNCS, **scope}), dtype=float)

# ── 2-D ──
def normalize(expr):
    expr = expr.replace("^", "**")
    expr = re.sub(r"(\d)([A-Za-z])", r"\1*\2", expr)
    expr = re.sub(r"([xX])\(", r"\1*(", expr)
    expr = re.sub(r"\)([xX0-9])", r")*\1", expr)
    return expr

def get_2d_branches(eq):
    eq = normalize(eq).strip()
    if not eq:
        raise ValueError("Equation is empty")
    if "=" not in eq:
        return [eq]

    lhs, rhs = [s.strip() for s in eq.split("=", 1)]
    if lhs.lower() in {"y", "f(x)"}:
        return [rhs]
    if rhs.lower() in {"y", "f(x)"}:
        return [lhs]

    def parse_y2(s):
        c = s.replace(" ", "").lower()
        if c == "y**2":
            return 0.0
        m = re.fullmatch(r"\(y([+-]\d+(?:\.\d+)?)\)\*\*2", c)
        return -float(m.group(1)) if m else None

    for pivot, other in [(lhs, rhs), (rhs, lhs)]:
        sh = parse_y2(pivot)
        if sh is not None:
            sq = f"sqrt(np.where(({other})>=0,({other}),np.nan))"
            return [f"({sh})+{sq}", f"({sh})-{sq}"]

    raise ValueError("Use y = f(x) or y^2 = g(x)")

def upper_envelope(branches):
    upper = np.full_like(branches[0], np.nan)
    for b in branches:
        fin = np.isfinite(b)
        upper = np.where(fin & ~np.isfinite(upper), b, upper)
        both = fin & np.isfinite(upper)
        upper[both] = np.maximum(upper[both], b[both])
    return upper

def run_2d(eq, a, b, ylo, yhi, n):
    branches = get_2d_branches(eq)
    x_line = np.linspace(a, b, 2000)
    y_lines = [safe_eval(br, {"x": x_line}) for br in branches]
    y_env = upper_envelope(y_lines)

    sy_min, sy_max = max(0.0, ylo), yhi
    if sy_max <= sy_min:
        raise ValueError("y bounds must include a positive range")

    xr = np.random.uniform(a, b, n)
    yr = np.random.uniform(sy_min, sy_max, n)
    fin_any = np.zeros(n, dtype=bool)
    below_any = np.zeros(n, dtype=bool)
    for br in branches:
        bv = safe_eval(br, {"x": xr})
        fin = np.isfinite(bv)
        fin_any |= fin
        below_any |= fin & (yr <= bv)
    inside = (yr >= 0.0) & fin_any & below_any
    estimate = float(np.mean(inside)) * (b - a) * (sy_max - sy_min)

    fig, ax = plt.subplots(figsize=(10, 5))
    for i, yl in enumerate(y_lines):
        ax.plot(x_line, yl, color="#4C9BE8", lw=2, label=f"f(x) = {eq}" if i == 0 else None)
    y_pos = np.where(np.isfinite(y_env), np.maximum(y_env, 0.0), np.nan)
    ax.fill_between(x_line, 0, y_pos, alpha=0.12, color="#4C9BE8")
    ax.scatter(xr[inside], yr[inside], s=5, alpha=0.5, color="#4C9BE8", label=f"Inside ({inside.sum():,})")
    ax.scatter(xr[~inside], yr[~inside], s=5, alpha=0.35, color="#E85C5C", label=f"Outside ({(~inside).sum():,})")
    ax.set_xlim(a, b); ax.set_ylim(ylo, yhi)
    ax.set_xlabel("x"); ax.set_ylabel("y")
    ax.legend(fontsize=9); ax.grid(alpha=0.2)
    plt.tight_layout()
    return fig, estimate, int(inside.sum()), int((~inside).sum())

# ── 3-D ──
def get_3d_functions(eq):
    eq = eq.replace("^", "**").strip()
    if not eq:
        raise ValueError("Equation is empty")

    if "=" not in eq:
        def implicit(x, y, z): return z - safe_eval(eq, {"x": x, "y": y, "z": z})
        def surface(x, y):     return safe_eval(eq, {"x": x, "y": y, "z": np.zeros_like(x)})
        return implicit, surface

    lhs, rhs = [s.strip() for s in eq.split("=", 1)]

    def implicit(x, y, z):
        return safe_eval(lhs, {"x": x, "y": y, "z": z}) - safe_eval(rhs, {"x": x, "y": y, "z": z})

    surface = None
    if lhs == "z":
        def surface(x, y): return safe_eval(rhs, {"x": x, "y": y, "z": np.zeros_like(x)})
    elif rhs == "z":
        def surface(x, y): return safe_eval(lhs, {"x": x, "y": y, "z": np.zeros_like(x)})
    elif lhs == "z**2":
        def surface(x, y): return np.sqrt(np.maximum(safe_eval(rhs, {"x": x, "y": y, "z": np.zeros_like(x)}), 0))
    elif rhs == "z**2":
        def surface(x, y): return np.sqrt(np.maximum(safe_eval(lhs, {"x": x, "y": y, "z": np.zeros_like(x)}), 0))

    return implicit, surface

def run_3d(eq, xlo, xhi, ylo, yhi, zlo, zhi, n):
    implicit, surface = get_3d_functions(eq)

    xd, yd = np.linspace(xlo, xhi, 60), np.linspace(ylo, yhi, 60)
    xx, yy = np.meshgrid(xd, yd)
    zz = surface(xx, yy) if surface else np.full_like(xx, np.nan)

    xr = np.random.uniform(xlo, xhi, n)
    yr = np.random.uniform(ylo, yhi, n)
    zr = np.random.uniform(zlo, zhi, n)
    inside = implicit(xr, yr, zr) <= 0.0
    estimate = float(np.mean(inside)) * (xhi - xlo) * (yhi - ylo) * (zhi - zlo)

    def cap(arr, mask, limit=8000):
        s = arr[mask]
        if len(s) > limit:
            s = s[np.random.choice(len(s), limit, replace=False)]
        return s

    xi, yi, zi = cap(xr, inside), cap(yr, inside), cap(zr, inside)
    xo, yo, zo = cap(xr, ~inside), cap(yr, ~inside), cap(zr, ~inside)

    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111, projection="3d")
    if np.any(np.isfinite(zz)):
        ax.plot_surface(xx, yy, zz, cmap="Blues", alpha=0.4, linewidth=0)
    ax.scatter(xi, yi, zi, s=5, alpha=0.5, color="#4C9BE8", label=f"Inside ({inside.sum():,})")
    ax.scatter(xo, yo, zo, s=5, alpha=0.3, color="#E85C5C", label=f"Outside ({(~inside).sum():,})")
    ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_zlabel("z")
    ax.legend(fontsize=9)
    plt.tight_layout()
    return fig, estimate, int(inside.sum()), int((~inside).sum())


# ===============================================================================
# ── APP 2 LOGIC: Las Vegas N-Queens ────────────────────────────────────────────
# ===============================================================================

def get_safe_cols(n, row, queens):
    safe = []
    for col in range(n):
        is_safe = True
        for r_idx, c_idx in enumerate(queens):
            # Check column, and both diagonals
            if c_idx == col or \
               abs(r_idx - row) == abs(c_idx - col):
                is_safe = False
                break
        if is_safe:
            safe.append(col)
    return safe

def generate_steps(n, max_restarts, seed):
    if seed is not None:
        random.seed(seed)
    
    steps = []
    restarts = 0
    
    for attempt in range(1, max_restarts + 1):
        queens = []
        steps.append({"type": "attempt_start", "attempt": attempt, "queens": []})
        failed = False

        for row in range(n):
            safe_cols = get_safe_cols(n, row, queens)
            
            steps.append({
                "type": "row_scan", 
                "attempt": attempt, 
                "row": row, 
                "safe_cols": safe_cols.copy(), 
                "queens": queens.copy()
            })

            if not safe_cols:
                steps.append({"type": "dead_end", "attempt": attempt, "row": row, "queens": queens.copy()})
                failed = True
                break

            col = random.choice(safe_cols)
            queens.append(col)
            steps.append({
                "type": "place", 
                "attempt": attempt, 
                "row": row, 
                "col": col, 
                "queens": queens.copy()
            })

        if not failed and len(queens) == n:
            steps.append({"type": "success", "attempt": attempt, "queens": queens})
            return steps, attempt - 1

        steps.append({"type": "restart", "attempt": attempt})
    
    return steps, max_restarts

def render_board(n, queens, row=None, safe=None, dead=False):
    # Set the size of each square
    cell_size = 45 
    grid_width = n * (cell_size + 2) # Adding 2 for the gap
    
    # Grid container with explicit column repeats
    html = f"""
    <div style='
        display: grid; 
        grid-template-columns: repeat({n}, {cell_size}px); 
        grid-template-rows: repeat({n}, {cell_size}px); 
        gap: 2px; 
        width: {grid_width}px;
        margin: 10px 0;
    '>"""
    
    for r in range(n):
        for c in range(n):
            # Chessboard pattern logic
            base_color = "#f8f9fa" if (r + c) % 2 == 0 else "#e5e7eb"
            content = ""
            border = "none"
            
            # 1. Check if there is a Queen here
            if r < len(queens) and queens[r] == c:
                base_color = "#ee6c4d"
                content = "Q"
            
            # 2. Highlight current row being processed
            elif r == row:
                if dead:
                    base_color = "#ef476f" # Red for dead-end
                elif safe and c in safe:
                    base_color = "#90e0ef" # Light blue for safe spots
                    content = "+"
                else:
                    base_color = "#ffd166" # Yellow for current processing row
            
            html += f"""
                <div style='
                    width:{cell_size}px; 
                    height:{cell_size}px; 
                    background:{base_color}; 
                    display:flex; 
                    justify-content:center; 
                    align-items:center; 
                    font-weight:bold; 
                    color:#1f2937;
                    border-radius:4px;
                    font-size: 1.2rem;
                '>{content}</div>
            """
    
    html += "</div>"
    return html


# ===============================================================================
# ── UNIFIED UI NAVIGATION & ROUTING ────────────────────────────────────────────
# ===============================================================================

st.sidebar.title("Navigation")
app_selection = st.sidebar.selectbox("Choose Application:", ["Monte Carlo Integration", "Las Vegas N-Queens"])

if app_selection == "Monte Carlo Integration":
    st.title("🎲 Monte Carlo Integration")
    tab2, tab3 = st.tabs(["2-D", "3-D"])

    with tab2:
        with st.sidebar:
            st.divider()
            st.header("2-D Settings")
            eq2  = st.text_input("Equation", "y = sin(x) + 1", key="eq2")
            c1, c2 = st.columns(2)
            a2   = c1.number_input("x min", value=0.0, key="a2")
            b2   = c2.number_input("x max", value=float(np.pi), key="b2")
            ylo2 = c1.number_input("y min", value=0.0, key="ylo2")
            yhi2 = c2.number_input("y max", value=2.5, key="yhi2")
            n2   = st.slider("Points", 500, 50_000, 8_000, 500, key="n2")
            run2 = st.button("Run", key="btn2", use_container_width=True)

        if run2:
            try:
                fig2, est2, ins2, out2 = run_2d(eq2, a2, b2, ylo2, yhi2, n2)
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Area estimate", f"{est2:.5f}")
                c2.metric("Inside",  f"{ins2:,}")
                c3.metric("Outside", f"{out2:,}")
                c4.metric("Hit rate", f"{ins2/n2*100:.1f}%")
                st.pyplot(fig2, use_container_width=True)
                plt.close(fig2)
            except Exception as e:
                st.error(str(e))
        else:
            st.info("Set equation and bounds in the sidebar, then click **Run**.")

    with tab3:
        with st.sidebar:
            st.divider()
            st.header("3-D Settings")
            eq3  = st.text_input("Equation", "(x-1)^2 + (y-1)^2 + (z-1)^2 = 1", key="eq3")
            c1, c2 = st.columns(2)
            xlo3 = c1.number_input("x min", value=0.0, key="xlo3")
            xhi3 = c2.number_input("x max", value=2.0, key="xhi3")
            ylo3 = c1.number_input("y min", value=0.0, key="ylo3")
            yhi3 = c2.number_input("y max", value=2.0, key="yhi3")
            zlo3 = c1.number_input("z min", value=0.0, key="zlo3")
            zhi3 = c2.number_input("z max", value=2.0, key="zhi3")
            n3   = st.slider("Points", 500, 80_000, 12_000, 500, key="n3")
            run3 = st.button("Run", key="btn3", use_container_width=True)

        if run3:
            try:
                fig3, est3, ins3, out3 = run_3d(eq3, xlo3, xhi3, ylo3, yhi3, zlo3, zhi3, n3)
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Volume estimate", f"{est3:.5f}")
                c2.metric("Inside",  f"{ins3:,}")
                c3.metric("Outside", f"{out3:,}")
                c4.metric("Hit rate", f"{ins3/n3*100:.1f}%")
                st.pyplot(fig3, use_container_width=True)
                plt.close(fig3)
            except Exception as e:
                st.error(str(e))
        else:
            st.info("Set equation and bounds in the sidebar, then click **Run**.")

elif app_selection == "Las Vegas N-Queens":
    with st.sidebar:
        st.divider()
        st.header("⚙️ N-Queens Controls")
        n = st.slider("Board Size (n)", 4, 16, 8)
        max_restarts = st.number_input("Max Restarts", 1, 20000, 500)
        delay = st.slider("Delay (sec)", 0.0, 1.0, 0.2)
        seed_val = st.text_input("Random Seed (optional)", "")
        seed = int(seed_val) if seed_val.isdigit() else None
        
        run_btn = st.button("🚀 Run Visualization", use_container_width=True)

    st.title("🎰 Las Vegas N-Queens Visualizer")
    st.caption("Randomly placing queens row-by-row. If it hits a dead-end, it restarts.")

    status_box = st.empty()
    board_box = st.empty()
    log_box = st.empty()

    if run_btn:
        all_steps, total_restarts = generate_steps(n, max_restarts, seed)
        logs = []
        
        current_restarts = 0
        for i, step in enumerate(all_steps):
            st_type = step["type"]
            
            if st_type == "attempt_start":
                msg = f"Attempt {step['attempt']}: Starting new random placement..."
            elif st_type == "row_scan":
                msg = f"Attempt {step['attempt']} | Row {step['row']+1}: Scanning for safe spots."
            elif st_type == "place":
                msg = f"Attempt {step['attempt']} | Placed Queen at (Row {step['row']+1}, Col {step['col']+1})"
            elif st_type == "dead_end":
                msg = f"❌ Dead-end at Row {step['row']+1}!"
            elif st_type == "restart":
                current_restarts += 1
                msg = "Restarting..."
            elif st_type == "success":
                msg = f"✅ SUCCESS! Found solution on attempt {step['attempt']}."
            
            status_box.info(msg)
            logs.append(msg)
            
            # THE FIX: Updated keyword arguments to match the render_board definition
            board_html = render_board(
                n, 
                step.get("queens", []), 
                row=step.get("row"), 
                safe=step.get("safe_cols"),
                dead=(st_type == "dead_end")
            )
            board_box.markdown(board_html, unsafe_allow_html=True)
            
            log_box.code("\n".join(logs[-5:]))
            
            time.sleep(delay)
            
            if st_type == "success":
                st.balloons()
                break
    else:
        st.info("Adjust the settings in the sidebar and click 'Run Visualization' to start.")
