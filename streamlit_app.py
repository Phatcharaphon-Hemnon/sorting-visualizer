import re
import time
import random
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from mpl_toolkits.mplot3d import Axes3D

# --- PAGE CONFIG ---
st.set_page_config(page_title="Algorithm Visualizer", page_icon="🎲", layout="wide")

# ──────────────────────────────────────────────────────────────────────────────
# ── SECTION 1: MONTE CARLO INTEGRATION LOGIC ──────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────

FUNCS = {
    "sin": np.sin, "cos": np.cos, "tan": np.tan,
    "exp": np.exp, "log": np.log, "ln": np.log,
    "sqrt": np.sqrt, "abs": np.abs,
    "pi": np.pi, "e": np.e, "np": np,
}
BUILTINS = {"__import__": __import__}

def safe_eval(expr, scope):
    return np.asarray(eval(expr, {"__builtins__": BUILTINS}, {**FUNCS, **scope}), dtype=float)

def normalize(expr):
    expr = expr.replace("^", "**")
    expr = re.sub(r"(\d)([A-Za-z])", r"\1*\2", expr)
    expr = re.sub(r"([xX])\(", r"\1*(", expr)
    expr = re.sub(r"\)([xX0-9])", r")*\1", expr)
    return expr

def get_2d_branches(eq):
    eq = normalize(eq).strip()
    if not eq: raise ValueError("Equation is empty")
    if "=" not in eq: return [eq]
    lhs, rhs = [s.strip() for s in eq.split("=", 1)]
    if lhs.lower() in {"y", "f(x)"}: return [rhs]
    if rhs.lower() in {"y", "f(x)"}: return [lhs]
    
    def parse_y2(s):
        c = s.replace(" ", "").lower()
        if c == "y**2": return 0.0
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

def run_2d_mc(eq, a, b, ylo, yhi, n):
    branches = get_2d_branches(eq)
    x_line = np.linspace(a, b, 2000)
    y_lines = [safe_eval(br, {"x": x_line}) for br in branches]
    y_env = upper_envelope(y_lines)
    sy_min, sy_max = max(0.0, ylo), yhi
    xr = np.random.uniform(a, b, n); yr = np.random.uniform(sy_min, sy_max, n)
    fin_any = np.zeros(n, dtype=bool); below_any = np.zeros(n, dtype=bool)
    for br in branches:
        bv = safe_eval(br, {"x": xr})
        fin = np.isfinite(bv)
        fin_any |= fin
        below_any |= fin & (yr <= bv)
    inside = (yr >= 0.0) & fin_any & below_any
    estimate = float(np.mean(inside)) * (b - a) * (sy_max - sy_min)
    fig, ax = plt.subplots(figsize=(10, 5))
    for i, yl in enumerate(y_lines): ax.plot(x_line, yl, color="#4C9BE8", lw=2)
    ax.fill_between(x_line, 0, np.where(np.isfinite(y_env), np.maximum(y_env, 0.0), np.nan), alpha=0.12, color="#4C9BE8")
    ax.scatter(xr[inside], yr[inside], s=5, alpha=0.5, color="#4C9BE8")
    ax.scatter(xr[~inside], yr[~inside], s=5, alpha=0.35, color="#E85C5C")
    return fig, estimate, int(inside.sum()), int((~inside).sum())

def get_3d_functions(eq):
    eq = eq.replace("^", "**").strip()
    if "=" not in eq:
        return (lambda x,y,z: z - safe_eval(eq,{"x":x,"y":y,"z":z})), (lambda x,y: safe_eval(eq,{"x":x,"y":y,"z":np.zeros_like(x)}))
    lhs, rhs = [s.strip() for s in eq.split("=", 1)]
    implicit = lambda x,y,z: safe_eval(lhs,{"x":x,"y":y,"z":z}) - safe_eval(rhs,{"x":x,"y":y,"z":z})
    surface = None
    if lhs == "z": surface = lambda x,y: safe_eval(rhs,{"x":x,"y":y,"z":np.zeros_like(x)})
    return implicit, surface

def run_3d_mc(eq, xlo, xhi, ylo, yhi, zlo, zhi, n):
    implicit, surface = get_3d_functions(eq)
    xr, yr, zr = np.random.uniform(xlo, xhi, n), np.random.uniform(ylo, yhi, n), np.random.uniform(zlo, zhi, n)
    inside = implicit(xr, yr, zr) <= 0.0
    estimate = float(np.mean(inside)) * (xhi-xlo)*(yhi-ylo)*(zhi-zlo)
    fig = plt.figure(figsize=(10, 6)); ax = fig.add_subplot(111, projection="3d")
    ax.scatter(xr[inside][:5000], yr[inside][:5000], zr[inside][:5000], s=2, color="#4C9BE8", alpha=0.5)
    return fig, estimate, int(inside.sum()), int((~inside).sum())

# ──────────────────────────────────────────────────────────────────────────────
# ── SECTION 2: LAS VEGAS N-QUEENS LOGIC ───────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────

def get_safe_cols(n, row, queens):
    safe = []
    for col in range(n):
        if all(c != col and abs(r - row) != abs(c - col) for r, c in enumerate(queens)):
            safe.append(col)
    return safe

def generate_nqueens_steps(n, max_restarts, seed):
    if seed: random.seed(seed)
    steps = []
    for attempt in range(1, max_restarts + 1):
        queens = []
        steps.append({"type": "start", "attempt": attempt, "queens": []})
        failed = False
        for row in range(n):
            safe_cols = get_safe_cols(n, row, queens)
            steps.append({"type": "scan", "attempt": attempt, "row": row, "safe": safe_cols, "queens": queens.copy()})
            if not safe_cols:
                steps.append({"type": "dead", "attempt": attempt, "row": row, "queens": queens.copy()})
                failed = True; break
            col = random.choice(safe_cols); queens.append(col)
            steps.append({"type": "place", "attempt": attempt, "row": row, "col": col, "queens": queens.copy()})
        if not failed:
            steps.append({"type": "success", "attempt": attempt, "queens": queens})
            return steps
    return steps

def render_board(n, queens, row=None, safe=None, dead=False):
    html = "<div style='display: grid; grid-template-columns: repeat("+str(n)+", 40px); gap: 2px;'>"
    for r in range(n):
        for c in range(n):
            color = "#f8f9fa" if (r+c)%2==0 else "#e5e7eb"
            content = ""
            if r < len(queens) and queens[r] == c:
                color = "#ee6c4d"; content = "Q"
            elif r == row:
                if dead: color = "#ef476f"
                elif safe and c in safe: color = "#90e0ef"; content = "+"
                else: color = "#ffd166"
            html += f"<div style='width:40px;height:40px;background:{color};display:grid;place-items:center;font-weight:bold;border-radius:4px;'>{content}</div>"
    return html + "</div>"

# ──────────────────────────────────────────────────────────────────────────────
# ── MAIN UI ROUTING ───────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────

st.sidebar.title("🛠️ Global Algorithm Menu")
mode = st.sidebar.radio("Select Application", ["Monte Carlo Integration", "Las Vegas N-Queens"])

if mode == "Monte Carlo Integration":
    st.title("🎲 Monte Carlo Integration")
    tab2, tab3 = st.tabs(["2-D Area", "3-D Volume"])
    
    with tab2:
        eq2 = st.text_input("Equation", "y = sin(x) + 1")
        col1, col2 = st.columns(2)
        a2 = col1.number_input("x min", value=0.0)
        b2 = col2.number_input("x max", value=float(np.pi))
        n2 = st.slider("Points", 500, 50000, 10000)
        if st.button("Calculate Area"):
            fig, est, ins, out = run_2d_mc(eq2, a2, b2, 0, 3, n2)
            st.metric("Estimated Area", f"{est:.5f}")
            st.pyplot(fig)

    with tab3:
        eq3 = st.text_input("3D Equation", "x^2 + y^2 + z^2 = 1")
        n3 = st.slider("3D Points", 500, 50000, 10000)
        if st.button("Calculate Volume"):
            fig, est, ins, out = run_3d_mc(eq3, -1, 1, -1, 1, -1, 1, n3)
            st.metric("Estimated Volume", f"{est:.5f}")
            st.pyplot(fig)

else:
    st.title("👸 Las Vegas N-Queens Visualizer")
    n = st.sidebar.slider("Board Size", 4, 16, 8)
    restarts = st.sidebar.number_input("Max Restarts", 1, 1000, 100)
    delay = st.sidebar.slider("Delay (s)", 0.01, 1.0, 0.1)
    
    if st.button("🚀 Start Simulation"):
        steps = generate_nqueens_steps(n, restarts, None)
        status = st.empty()
        board_container = st.empty()
        
        for step in steps:
            if step["type"] == "start": msg = f"Attempt {step['attempt']}: Resetting board..."
            elif step["type"] == "scan": msg = f"Row {step['row']+1}: Finding safe spots..."
            elif step["type"] == "place": msg = f"Placed Queen at Row {step['row']+1}"
            elif step["type"] == "dead": msg = f"❌ Dead-end at Row {step['row']+1}! Restarting..."
            elif step["type"] == "success": msg = f"✅ Success on Attempt {step['attempt']}!"
            
            status.info(msg)
            board_container.markdown(render_board(
                n, step["queens"], 
                row=step.get("row"), 
                safe=step.get("safe"), 
                dead=(step["type"]=="dead")
            ), unsafe_allow_html=True)
            
            time.sleep(delay)
            if step["type"] == "success": 
                st.balloons()
                break
