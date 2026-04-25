import re
import random
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

# ── Unified Page Config ────────────────────────────────────────────────────────
st.set_page_config(page_title="Algorithm Visualizers", page_icon="🎲", layout="wide")

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
    <style>
    .cell { width: 45px; height: 45px; display: flex; justify-content: center; align-items: center; border: 1px solid rgba(15, 23, 42, 0.08); font-weight: bold; border-radius:4px; font-size: 1.2rem; color: #1f2937;}
    </style>
""", unsafe_allow_html=True)


# ===============================================================================
# ── COMMON FUNCTIONS ───────────────────────────────────────────────────────────
# ===============================================================================

def render_board(n, queens, row=None, safe=None, dead=False, try_col=None, try_safe=None):
    cell_size = 45 
    grid_width = n * (cell_size + 2) 
    
    html = f"<div style='display: grid; grid-template-columns: repeat({n}, {cell_size}px); grid-template-rows: repeat({n}, {cell_size}px); gap: 2px; width: {grid_width}px; margin: 10px 0;'>"
    
    safe_set = set(safe if safe else [])

    for r in range(n):
        for c in range(n):
            base_color = "#f8f9fa" if (r + c) % 2 == 0 else "#e5e7eb"
            content = ""
            
            # 1. Placed Queens
            if r < len(queens) and queens[r] == c:
                base_color = "#ee6c4d"
                content = "Q"
            
            # 2. Current Row processing
            elif r == row:
                if dead:
                    base_color = "#ef476f" # Dead end
                elif c in safe_set:
                    base_color = "#90e0ef" # Safe candidate
                    content = "+"
                else:
                    base_color = "#ffd166" # Current row (active)
                
                # 3. Backtracking explicit tries
                if try_col is not None and c == try_col:
                    base_color = "#90e0ef" if try_safe else "#f9a8a8"
                    content = "?"
            
            html += f"<div class='cell' style='background:{base_color};'>{content}</div>"
    
    html += "</div>"
    return html

def render_bars(step_data):
    arr = step_data.get("array", [])
    low = step_data.get("low", -1)
    high = step_data.get("high", -1)
    sorted_set = step_data.get("sorted", set())
    p_idx = step_data.get("pivotIndex", -1)
    cmp_indices = step_data.get("compareIndices", [])
    swp_indices = step_data.get("swapIndices", [])

    max_val = max(arr) if arr else 1
    show_numbers = len(arr) <= 30

    html = "<div style='display: flex; align-items: flex-end; gap: 3px; height: 380px; background: linear-gradient(to top, rgba(15, 118, 110, 0.08), rgba(15, 118, 110, 0.02)); padding: 12px; border-radius: 12px; border: 1px solid #d1d5db; margin-top: 10px;'>"
    
    for i, val in enumerate(arr):
        color = "#2a9d8f" 
        scale = 1.0

        if low <= i <= high: color = "#94a3b8"
        if i in sorted_set: color = "#118ab2"
        if i == p_idx: 
            color = "#ef476f"
            scale = 1.05
        if i in cmp_indices: 
            color = "#ffd166"
            scale = 1.06
        if i in swp_indices: 
            color = "#f4a261"
            scale = 1.1

        h_pct = (val / max_val) * 100
        
        num_div = f"<div style='font-size: 11px; margin-top: 4px; color: #374151; font-weight: bold;'>{val}</div>" if show_numbers else ""
        
        html += f"""
        <div style='flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 100%;'>
            <div style='width: 100%; height: {h_pct}%; background: {color}; border-radius: 5px 5px 0 0; transform: scaleY({scale}); transform-origin: bottom; transition: all 0.1s ease;'></div>
            {num_div}
        </div>
        """
    html += "</div>"
    return html


# ===============================================================================
# ── APP 1 LOGIC: Monte Carlo Integration ───────────────────────────────────────
# ===============================================================================
FUNCS = {
    "sin": np.sin, "cos": np.cos, "tan": np.tan, "exp": np.exp, "log": np.log, "ln": np.log,
    "sqrt": np.sqrt, "abs": np.abs, "pi": np.pi, "e": np.e, "np": np,
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
    if not eq: 
        raise ValueError("Equation is empty")
    if "=" not in eq: 
        return [eq]
    
    lhs, rhs = [s.strip() for s in eq.split("=", 1)]
    if lhs.lower() in {"y", "f(x)"}: return [rhs]
    if rhs.lower() in {"y", "f(x)"}: return [lhs]

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

def get_3d_functions(eq):
    eq = eq.replace("^", "**").strip()
    if not eq: 
        raise ValueError("Equation is empty")
        
    if "=" not in eq:
        def implicit(x, y, z): 
            return z - safe_eval(eq, {"x": x, "y": y, "z": z})
        def surface(x, y):     
            return safe_eval(eq, {"x": x, "y": y, "z": np.zeros_like(x)})
        return implicit, surface

    lhs, rhs = [s.strip() for s in eq.split("=", 1)]
    def implicit(x, y, z): 
        return safe_eval(lhs, {"x": x, "y": y, "z": z}) - safe_eval(rhs, {"x": x, "y": y, "z": z})

    surface = None
    if lhs == "z": 
        def surface(x, y): 
            return safe_eval(rhs, {"x": x, "y": y, "z": np.zeros_like(x)})
    elif rhs == "z": 
        def surface(x, y): 
            return safe_eval(lhs, {"x": x, "y": y, "z": np.zeros_like(x)})
    elif lhs == "z**2": 
        def surface(x, y): 
            return np.sqrt(np.maximum(safe_eval(rhs, {"x": x, "y": y, "z": np.zeros_like(x)}), 0))
    elif rhs == "z**2": 
        def surface(x, y): 
            return np.sqrt(np.maximum(safe_eval(lhs, {"x": x, "y": y, "z": np.zeros_like(x)}), 0))
            
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
# ── APP 2 & 3 LOGIC: Las Vegas & Backtracking Generators ───────────────────────
# ===============================================================================

def is_safe_queen(row, col, used_cols, used_diag1, used_diag2):
    return (col not in used_cols) and ((row - col) not in used_diag1) and ((row + col) not in used_diag2)

def generate_lv_steps(n, max_restarts, seed):
    if seed is not None: random.seed(seed)
    steps = []
    
    for attempt in range(1, max_restarts + 1):
        queens = []
        used_cols, used_diag1, used_diag2 = set(), set(), set()
        steps.append({"type": "attempt_start", "attempt": attempt, "queens": list(queens)})
        failed = False

        for row in range(n):
            safe_cols = [c for c in range(n) if is_safe_queen(row, c, used_cols, used_diag1, used_diag2)]
            steps.append({"type": "row_scan", "attempt": attempt, "row": row, "safe_cols": list(safe_cols), "queens": list(queens)})

            if not safe_cols:
                steps.append({"type": "dead_end", "attempt": attempt, "row": row, "queens": list(queens)})
                failed = True
                break

            col = random.choice(safe_cols)
            queens.append(col)
            used_cols.add(col); used_diag1.add(row - col); used_diag2.add(row + col)
            steps.append({"type": "place", "attempt": attempt, "row": row, "col": col, "queens": list(queens)})

        if not failed and len(queens) == n:
            steps.append({"type": "success", "attempt": attempt, "queens": list(queens)})
            return steps
        steps.append({"type": "restart", "attempt": attempt})
    
    steps.append({"type": "failed", "attempt": max_restarts})
    return steps

def generate_bt_steps(n):
    out = []
    queens = []
    used_cols, used_diag1, used_diag2 = set(), set(), set()

    def push(evt_type, row=None, col=None, safe=None):
        out.append({"type": evt_type, "queens": list(queens), "row": row, "col": col, "safe_col": safe})

    push("start")

    def solve(row):
        if row == n:
            push("success")
            return True
        
        push("row_start", row=row)
        has_safe = False

        for col in range(n):
            safe = is_safe_queen(row, col, used_cols, used_diag1, used_diag2)
            push("try_col", row=row, col=col, safe=safe)
            if not safe:
                continue
            
            has_safe = True
            queens.append(col)
            used_cols.add(col); used_diag1.add(row - col); used_diag2.add(row + col)
            push("place", row=row, col=col)
            
            if solve(row + 1):
                return True
            
            popped = queens.pop()
            used_cols.remove(popped); used_diag1.remove(row - popped); used_diag2.remove(row + popped)
            push("backtrack", row=row, col=popped)

        if not has_safe:
            push("dead_end", row=row)
        return False

    if not solve(0):
        push("failed")
    return out


# ===============================================================================
# ── APP 4 LOGIC: Randomized Quick Sort ─────────────────────────────────────────
# ===============================================================================

def generate_qsort_steps(arr, seed):
    out = []
    a = list(arr)
    sorted_set = set()
    if seed is not
