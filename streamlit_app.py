import re
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(page_title="Monte Carlo Integration", page_icon="🎲", layout="wide")

# ── Safe eval ──────────────────────────────────────────────────────────────────
FUNCS = {
    "sin": np.sin, "cos": np.cos, "tan": np.tan,
    "exp": np.exp, "log": np.log, "ln": np.log,
    "sqrt": np.sqrt, "abs": np.abs,
    "pi": np.pi, "e": np.e, "np": np,
}
BUILTINS = {"__import__": __import__}


def safe_eval(expr, scope):
    return np.asarray(eval(expr, {"__builtins__": BUILTINS}, {**FUNCS, **scope}), dtype=float)


# ── 2-D ────────────────────────────────────────────────────────────────────────
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
    ax.scatter(xr[inside],  yr[inside],  s=5, alpha=0.5,  color="#4C9BE8", label=f"Inside  ({inside.sum():,})")
    ax.scatter(xr[~inside], yr[~inside], s=5, alpha=0.35, color="#E85C5C", label=f"Outside ({(~inside).sum():,})")
    ax.set_xlim(a, b); ax.set_ylim(ylo, yhi)
    ax.set_xlabel("x"); ax.set_ylabel("y")
    ax.legend(fontsize=9); ax.grid(alpha=0.2)
    plt.tight_layout()
    return fig, estimate, int(inside.sum()), int((~inside).sum())


# ── 3-D ────────────────────────────────────────────────────────────────────────
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
    ax.scatter(xi, yi, zi, s=5, alpha=0.5, color="#4C9BE8", label=f"Inside  ({inside.sum():,})")
    ax.scatter(xo, yo, zo, s=5, alpha=0.3, color="#E85C5C", label=f"Outside ({(~inside).sum():,})")
    ax.set_xlabel("x"); ax.set_ylabel("y"); ax.set_zlabel("z")
    ax.legend(fontsize=9)
    plt.tight_layout()
    return fig, estimate, int(inside.sum()), int((~inside).sum())


# ── UI ─────────────────────────────────────────────────────────────────────────
st.title("🎲 Monte Carlo Integration")

tab2, tab3 = st.tabs(["2-D", "3-D"])

with tab2:
    with st.sidebar:
        st.header("2-D Settings")
        eq2  = st.text_input("Equation", "y = sin(x) + 1", key="eq2")
        c1, c2 = st.columns(2)
        a2   = c1.number_input("x min", value=0.0,           key="a2")
        b2   = c2.number_input("x max", value=float(np.pi),  key="b2")
        ylo2 = c1.number_input("y min", value=0.0,           key="ylo2")
        yhi2 = c2.number_input("y max", value=2.5,           key="yhi2")
        n2   = st.slider("Points", 500, 50_000, 8_000, 500,  key="n2")
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
