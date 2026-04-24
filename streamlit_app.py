import re
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

# ─── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Monte Carlo Integration",
    page_icon="🎲",
    layout="wide",
)

# ─── Styling ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;600&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

/* Dark background */
.stApp { background-color: #0d1117; color: #e6edf3; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #161b22;
    border-right: 1px solid #30363d;
}
[data-testid="stSidebar"] * { color: #e6edf3 !important; }

/* Inputs */
input, .stTextInput input, .stNumberInput input {
    background: #21262d !important;
    border: 1px solid #30363d !important;
    border-radius: 6px !important;
    color: #e6edf3 !important;
    font-family: 'Space Mono', monospace !important;
}
input:focus { border-color: #58a6ff !important; box-shadow: 0 0 0 3px rgba(88,166,255,.15) !important; }

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #1f6feb 0%, #388bfd 100%);
    color: #fff !important;
    border: none;
    border-radius: 8px;
    font-family: 'Space Mono', monospace;
    font-weight: 700;
    letter-spacing: .05em;
    padding: .55rem 1.4rem;
    transition: transform .15s, box-shadow .15s;
}
.stButton > button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(56,139,253,.45); }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { background: #161b22; border-bottom: 2px solid #30363d; gap: 0; }
.stTabs [data-baseweb="tab"] { color: #8b949e; font-family: 'Space Mono', monospace; font-size: .85rem; padding: .7rem 1.4rem; }
.stTabs [aria-selected="true"] { color: #58a6ff !important; border-bottom: 2px solid #58a6ff; background: transparent; }

/* Metrics */
[data-testid="stMetricValue"] { font-family: 'Space Mono', monospace; font-size: 1.4rem; color: #58a6ff !important; }
[data-testid="stMetricLabel"] { color: #8b949e !important; font-size: .75rem; text-transform: uppercase; letter-spacing: .1em; }

/* Code */
code { background: #21262d; padding: .1em .35em; border-radius: 4px; font-size: .85em; color: #f0883e; }

/* Header */
.mc-header {
    font-family: 'Space Mono', monospace;
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(90deg, #58a6ff, #79c0ff, #a5d6ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: .25rem;
}
.mc-sub { color: #8b949e; font-size: .9rem; margin-bottom: 2rem; }

/* Info box */
.info-box {
    background: #0d419d22;
    border: 1px solid #1f6feb55;
    border-left: 3px solid #58a6ff;
    border-radius: 6px;
    padding: .8rem 1rem;
    font-size: .85rem;
    color: #79c0ff;
    margin-bottom: 1.2rem;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  SHARED SAFE EVAL
# ══════════════════════════════════════════════════════════════════════
SAFE_FUNCTIONS = {
    "sin": np.sin, "cos": np.cos, "tan": np.tan,
    "exp": np.exp, "log": np.log, "ln": np.log,
    "sqrt": np.sqrt, "abs": np.abs,
    "pi": np.pi, "e": np.e, "np": np,
}
SAFE_BUILTINS = {"__import__": __import__}


# ══════════════════════════════════════════════════════════════════════
#  2-D HELPERS  (ported from script-1)
# ══════════════════════════════════════════════════════════════════════
def normalize_2d(expr: str) -> str:
    expr = expr.replace("^", "**")
    expr = re.sub(r"(\d)([A-Za-z])", r"\1*\2", expr)
    expr = re.sub(r"([xX])\(", r"\1*(", expr)
    expr = re.sub(r"\)([xX0-9])", r")*\1", expr)
    return expr


def build_2d_branches(eq: str) -> tuple[str, list[str]]:
    eq = normalize_2d(eq).strip()
    if not eq:
        raise ValueError("Equation cannot be empty")
    if "=" not in eq:
        return f"y = {eq}", [eq]

    lhs_raw, rhs_raw = eq.split("=", 1)
    lhs, rhs = lhs_raw.strip(), rhs_raw.strip()

    if lhs.lower() in {"y", "f(x)"}:
        return eq, [rhs]
    if rhs.lower() in {"y", "f(x)"}:
        return eq, [lhs]

    def parse_y2(side: str):
        c = side.replace(" ", "").lower()
        if c == "y**2":
            return 0.0
        m = re.fullmatch(r"\(y([+-]\d+(?:\.\d+)?)\)\*\*2", c)
        return -float(m.group(1)) if m else None

    for pivot, other in [(lhs, rhs), (rhs, lhs)]:
        shift = parse_y2(pivot)
        if shift is not None:
            sqrt_expr = f"sqrt(np.where(({other}) >= 0, ({other}), np.nan))"
            return eq, [f"({shift}) + {sqrt_expr}", f"({shift}) - {sqrt_expr}"]

    raise ValueError("2-D: use explicit y = f(x) or y² = g(x) form")


def eval_2d_branch(expr: str, x: np.ndarray) -> np.ndarray:
    return np.asarray(
        eval(expr, {"__builtins__": SAFE_BUILTINS}, {"x": x, **SAFE_FUNCTIONS}),
        dtype=float,
    )


def upper_envelope(branches: list[np.ndarray]) -> np.ndarray:
    upper = np.full_like(branches[0], np.nan, dtype=float)
    for b in branches:
        fin = np.isfinite(b)
        upper = np.where(fin & ~np.isfinite(upper), b, upper)
        both = fin & np.isfinite(upper)
        upper[both] = np.maximum(upper[both], b[both])
    return upper


def run_2d(eq: str, a: float, b: float, y_min: float, y_max: float, n: int):
    _, branches = build_2d_branches(eq)
    x_plot = np.linspace(a, b, 2000)
    y_branches_plot = [eval_2d_branch(br, x_plot) for br in branches]
    y_env = upper_envelope(y_branches_plot)

    sy_min = max(0.0, y_min)
    sy_max = y_max
    if sy_max <= sy_min:
        raise ValueError("y bounds must include a positive range")

    xr = np.random.uniform(a, b, n)
    yr = np.random.uniform(sy_min, sy_max, n)
    y_br = [eval_2d_branch(br, xr) for br in branches]
    fin_any = np.zeros(n, dtype=bool)
    below_any = np.zeros(n, dtype=bool)
    for bv in y_br:
        fin = np.isfinite(bv)
        fin_any |= fin
        below_any |= fin & (yr <= bv)
    inside = (yr >= 0.0) & fin_any & below_any

    rect = (b - a) * (sy_max - sy_min)
    estimate = float(np.mean(inside)) * rect

    fig, ax = plt.subplots(figsize=(10, 5.5), facecolor="#0d1117")
    ax.set_facecolor("#0d1117")
    for i, bv in enumerate(y_branches_plot):
        ax.plot(x_plot, bv, color="#58a6ff", lw=2.2,
                label=f"f(x): {eq}" if i == 0 else None)
    y_pos = np.where(np.isfinite(y_env), np.maximum(y_env, 0.0), np.nan)
    ax.fill_between(x_plot, 0.0, y_pos, alpha=0.15, color="#388bfd")
    ax.scatter(xr[inside], yr[inside], s=6, alpha=0.55, color="#388bfd", label=f"Inside ({inside.sum():,})")
    ax.scatter(xr[~inside], yr[~inside], s=6, alpha=0.40, color="#f85149", label=f"Outside ({(~inside).sum():,})")
    ax.set_xlim(a, b)
    ax.set_ylim(y_min, y_max)
    ax.tick_params(colors="#8b949e")
    for sp in ax.spines.values():
        sp.set_edgecolor("#30363d")
    ax.grid(alpha=0.15, color="#30363d")
    ax.legend(facecolor="#161b22", edgecolor="#30363d", labelcolor="#e6edf3", fontsize=9)
    ax.set_xlabel("x", color="#8b949e")
    ax.set_ylabel("y", color="#8b949e")
    ax.set_title(f"2-D Monte Carlo  |  n = {n:,}  |  estimate = {estimate:.6f}",
                 color="#e6edf3", fontsize=12, fontfamily="monospace")
    plt.tight_layout()
    return fig, estimate, int(inside.sum()), int((~inside).sum())


# ══════════════════════════════════════════════════════════════════════
#  3-D HELPERS  (ported from script-2)
# ══════════════════════════════════════════════════════════════════════
def normalize_3d(expr: str) -> str:
    return expr.replace("^", "**")


def eval_3d(expr: str, x, y, z) -> np.ndarray:
    expr = normalize_3d(expr)
    scope = {"x": x, "y": y, "z": z, **SAFE_FUNCTIONS}
    return np.asarray(eval(expr, {"__builtins__": SAFE_BUILTINS}, scope), dtype=float)


def build_3d_functions(eq: str):
    eq = normalize_3d(eq).strip()
    if not eq:
        raise ValueError("Equation cannot be empty")

    surface_fn = None

    if "=" in eq:
        lhs, rhs = [s.strip() for s in eq.split("=", 1)]

        def implicit(x, y, z):
            return eval_3d(lhs, x, y, z) - eval_3d(rhs, x, y, z)

        if lhs == "z":
            def surface_fn(x, y): return eval_3d(rhs, x, y, np.zeros_like(x))
        elif rhs == "z":
            def surface_fn(x, y): return eval_3d(lhs, x, y, np.zeros_like(x))
        elif lhs == "z**2":
            def surface_fn(x, y): return np.sqrt(np.maximum(eval_3d(rhs, x, y, np.zeros_like(x)), 0.0))
        elif rhs == "z**2":
            def surface_fn(x, y): return np.sqrt(np.maximum(eval_3d(lhs, x, y, np.zeros_like(x)), 0.0))

        return implicit, surface_fn

    def implicit(x, y, z):
        return z - eval_3d(eq, x, y, np.zeros_like(x))

    def surface_fn(x, y):
        return eval_3d(eq, x, y, np.zeros_like(x))

    return implicit, surface_fn


def run_3d(eq: str, xmin, xmax, ymin, ymax, zmin, zmax, n: int):
    implicit, surface_fn = build_3d_functions(eq)

    xd = np.linspace(xmin, xmax, 60)
    yd = np.linspace(ymin, ymax, 60)
    xx, yy = np.meshgrid(xd, yd)
    zz = surface_fn(xx, yy) if surface_fn else np.full_like(xx, np.nan)

    xr = np.random.uniform(xmin, xmax, n)
    yr = np.random.uniform(ymin, ymax, n)
    zr = np.random.uniform(zmin, zmax, n)
    inside = implicit(xr, yr, zr) <= 0.0

    hit = np.mean(inside)
    vol = (xmax - xmin) * (ymax - ymin) * (zmax - zmin)
    estimate = float(hit * vol)

    MAX_DISP = 10_000

    def downsample(arr, mask):
        sub = arr[mask]
        if len(sub) > MAX_DISP:
            idx = np.random.choice(len(sub), MAX_DISP, replace=False)
            sub = sub[idx]
        return sub

    xi = downsample(xr, inside); yi = downsample(yr, inside); zi = downsample(zr, inside)
    xo = downsample(xr, ~inside); yo = downsample(yr, ~inside); zo = downsample(zr, ~inside)

    fig = plt.figure(figsize=(10, 6.5), facecolor="#0d1117")
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor("#0d1117")

    if np.any(np.isfinite(zz)):
        ax.plot_surface(xx, yy, zz, cmap="Blues", alpha=0.45, linewidth=0, antialiased=True)

    ax.scatter(xi, yi, zi, s=6, alpha=0.55, color="#388bfd", label=f"Inside ({inside.sum():,})")
    ax.scatter(xo, yo, zo, s=6, alpha=0.30, color="#f85149", label=f"Outside ({(~inside).sum():,})")

    ax.set_xlabel("x", color="#8b949e"); ax.set_ylabel("y", color="#8b949e"); ax.set_zlabel("z", color="#8b949e")
    ax.tick_params(colors="#8b949e", labelsize=7)
    ax.xaxis.pane.fill = False; ax.yaxis.pane.fill = False; ax.zaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor("#30363d"); ax.yaxis.pane.set_edgecolor("#30363d"); ax.zaxis.pane.set_edgecolor("#30363d")
    ax.grid(True, color="#30363d", alpha=0.3)
    ax.legend(facecolor="#161b22", edgecolor="#30363d", labelcolor="#e6edf3", fontsize=8)
    ax.set_title(f"3-D Monte Carlo  |  n = {n:,}  |  estimate = {estimate:.6f}",
                 color="#e6edf3", fontsize=11, fontfamily="monospace")
    plt.tight_layout()
    return fig, estimate, int(inside.sum()), int((~inside).sum())


# ══════════════════════════════════════════════════════════════════════
#  UI
# ══════════════════════════════════════════════════════════════════════
st.markdown('<div class="mc-header">🎲 Monte Carlo Integration</div>', unsafe_allow_html=True)
st.markdown('<div class="mc-sub">Visualise numerical integration via random sampling — in 2-D and 3-D.</div>', unsafe_allow_html=True)

tab2d, tab3d = st.tabs(["📈  2-D Integration", "🧊  3-D Integration"])

# ─── 2-D TAB ────────────────────────────────────────────────────────────────────
with tab2d:
    st.markdown('<div class="info-box">Enter a function <code>y = f(x)</code>. You may also use <code>y^2 = g(x)</code> (both branches plotted). Supported: <code>sin cos tan exp log sqrt abs pi e ^</code></div>', unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### ⚙️ 2-D Settings")
        eq2 = st.text_input("Equation", value="y = sin(x) + 1", key="eq2")
        c1, c2 = st.columns(2)
        with c1:
            a2 = st.number_input("x min", value=0.0, key="a2")
            ylo2 = st.number_input("y min", value=0.0, key="ylo2")
        with c2:
            b2 = st.number_input("x max", value=float(np.pi), key="b2")
            yhi2 = st.number_input("y max", value=2.5, key="yhi2")
        n2 = st.slider("Random points", 500, 50_000, 8_000, 500, key="n2")
        run2 = st.button("▶  Run 2-D", use_container_width=True)

    if run2:
        try:
            with st.spinner("Sampling…"):
                fig2, est2, ins2, out2 = run_2d(eq2, a2, b2, ylo2, yhi2, n2)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Estimate", f"{est2:.6f}")
            m2.metric("Inside", f"{ins2:,}")
            m3.metric("Outside", f"{out2:,}")
            m4.metric("Hit rate", f"{ins2/n2*100:.1f}%")
            st.pyplot(fig2, use_container_width=True)
            plt.close(fig2)
        except Exception as err:
            st.error(f"Error: {err}")
    else:
        st.info("Configure the equation and bounds in the sidebar, then click **▶ Run 2-D**.")

# ─── 3-D TAB ────────────────────────────────────────────────────────────────────
with tab3d:
    st.markdown('<div class="info-box">Enter an implicit equation <code>f(x,y,z) = g(x,y,z)</code> or explicit <code>z = f(x,y)</code>. The Monte Carlo sampler counts points where <code>f − g ≤ 0</code>.</div>', unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("---")
        st.markdown("### ⚙️ 3-D Settings")
        eq3 = st.text_input("Equation", value="(x-1)^2 + (y-1)^2 + (z-1)^2 = 1", key="eq3")
        c3, c4 = st.columns(2)
        with c3:
            xlo3 = st.number_input("x min", value=0.0, key="xlo3")
            ylo3 = st.number_input("y min", value=0.0, key="ylo3")
            zlo3 = st.number_input("z min", value=0.0, key="zlo3")
        with c4:
            xhi3 = st.number_input("x max", value=2.0, key="xhi3")
            yhi3 = st.number_input("y max", value=2.0, key="yhi3")
            zhi3 = st.number_input("z max", value=2.0, key="zhi3")
        n3 = st.slider("Random points", 500, 80_000, 12_000, 500, key="n3")
        run3 = st.button("▶  Run 3-D", use_container_width=True)

    if run3:
        try:
            with st.spinner("Sampling 3-D space…"):
                fig3, est3, ins3, out3 = run_3d(eq3, xlo3, xhi3, ylo3, yhi3, zlo3, zhi3, n3)
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Volume estimate", f"{est3:.6f}")
            m2.metric("Inside", f"{ins3:,}")
            m3.metric("Outside", f"{out3:,}")
            m4.metric("Hit rate", f"{ins3/n3*100:.1f}%")
            st.pyplot(fig3, use_container_width=True)
            plt.close(fig3)
        except Exception as err:
            st.error(f"Error: {err}")
    else:
        st.info("Configure the equation and bounds in the sidebar, then click **▶ Run 3-D**.")

# ─── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<div style="text-align:center;color:#484f58;font-size:.78rem;font-family:monospace">'
    "Monte Carlo Integration · 2-D &amp; 3-D · Built with Streamlit + NumPy + Matplotlib"
    "</div>",
    unsafe_allow_html=True,
)
