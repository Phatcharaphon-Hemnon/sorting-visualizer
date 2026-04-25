import re
import random
import time
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

def run_2d(eq, a, b, ylo, yhi, n):
    branches = get_2d_branches(eq)
    x_line = np.linspace(a, b, 2000)
    y_lines = [safe_eval(br, {"x": x_line}) for br in branches]
    y_env = upper_envelope(y_lines)
    sy_min, sy_max = max(0.0, ylo), yhi
    if sy_max <= sy_min: raise ValueError("y bounds must include a positive range")

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
    if not eq: raise ValueError("Equation is empty")
    if "=" not in eq:
        def implicit(x, y, z): return z - safe_eval(eq, {"x": x, "y": y, "z": z})
        def surface(x, y):     return safe_eval(eq, {"x": x, "y": y, "z": np.zeros_like(x)})
        return implicit, surface

    lhs, rhs = [s.strip() for s in eq.split("=", 1)]
    def implicit(x, y, z): return safe_eval(lhs, {"x": x, "y": y, "z": z}) - safe_eval(rhs, {"x": x, "y": y, "z": z})

    surface = None
    if lhs == "z": def surface(x, y): return safe_eval(rhs, {"x": x, "y": y, "z": np.zeros_like(x)})
    elif rhs == "z": def surface(x, y): return safe_eval(lhs, {"x": x, "y": y, "z": np.zeros_like(x)})
    elif lhs == "z**2": def surface(x, y): return np.sqrt(np.maximum(safe_eval(rhs, {"x": x, "y": y, "z": np.zeros_like(x)}), 0))
    elif rhs == "z**2": def surface(x, y): return np.sqrt(np.maximum(safe_eval(lhs, {"x": x, "y": y, "z": np.zeros_like(x)}), 0))
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
        if len(s) > limit: s = s[np.random.choice(len(s), limit, replace=False)]
        return s

    xi, yi, zi = cap(xr, inside), cap(yr, inside), cap(zr, inside)
    xo, yo, zo = cap(xr, ~inside), cap(yr, ~inside), cap(zr, ~inside)

    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111, projection="3d")
    if np.any(np.isfinite(zz)): ax.plot_surface(xx, yy, zz, cmap="Blues", alpha=0.4, linewidth=0)
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
    if seed is not None: random.seed(seed)

    def push(etype, low, high, pivot_idx=None, pval=None, cmp_idx=None, swp_i=None, swp_j=None, msg=""):
        c_idx = [cmp_idx] if cmp_idx is not None else []
        s_idx = [swp_i, swp_j] if swp_i is not None and swp_j is not None else []
        out.append({
            "type": etype, "array": list(a), "sorted": set(sorted_set), "low": low, "high": high, 
            "pivotIndex": pivot_idx, "pivotValue": pval, "compareIndices": c_idx, "swapIndices": s_idx, "msg": msg
        })

    def partition(low, high):
        p_idx = random.randint(low, high)
        push("pivot-select", low, high, pivot_idx=p_idx, pval=a[p_idx], msg=f"Random pivot: idx {p_idx}, val {a[p_idx]}")
        
        if p_idx != high:
            a[p_idx], a[high] = a[high], a[p_idx]
            push("swap", low, high, swp_i=p_idx, swp_j=high, pivot_idx=high, msg="Move pivot to end")
            p_idx = high

        pivot = a[high]
        i = low - 1
        
        for j in range(low, high):
            push("compare", low, high, pivot_idx=high, pval=pivot, cmp_idx=j, msg=f"Compare idx {j} with pivot {pivot}")
            if a[j] <= pivot:
                i += 1
                if i != j:
                    a[i], a[j] = a[j], a[i]
                    push("swap", low, high, swp_i=i, swp_j=j, pivot_idx=high, msg="Partition swap")
        
        p = i + 1
        if p != high:
            a[p], a[high] = a[high], a[p]
            push("swap", low, high, swp_i=p, swp_j=high, pivot_idx=p, msg="Place pivot")

        sorted_set.add(p)
        push("pivot-fixed", low, high, pivot_idx=p, pval=a[p], msg=f"Pivot fixed at idx {p}")
        return p

    def qsort(low, high):
        if low > high: return
        if low == high:
            sorted_set.add(low)
            push("single", low, high, msg=f"Single element at idx {low} sorted")
            return
        p = partition(low, high)
        qsort(low, p - 1)
        qsort(p + 1, high)

    push("start", 0, len(a)-1, msg="Start sorting")
    qsort(0, len(a)-1)
    for k in range(len(a)): sorted_set.add(k)
    push("done", 0, len(a)-1, msg="Done")
    
    return out


# ===============================================================================
# ── UNIFIED UI NAVIGATION & ROUTING ────────────────────────────────────────────
# ===============================================================================

st.sidebar.title("Navigation")
app_selection = st.sidebar.selectbox("Choose Application:", [
    "Monte Carlo Integration", 
    "Las Vegas N-Queens (Basic)", 
    "8-Queens Compare (LV vs BT)", 
    "Randomized Quick Sort"
])


# ── Route 1: Monte Carlo ───────────────────────────────────────────────────────
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

# ── Route 2: Basic Las Vegas N-Queens ──────────────────────────────────────────
elif app_selection == "Las Vegas N-Queens (Basic)":
    with st.sidebar:
        st.divider()
        st.header("⚙️ LV Controls")
        n = st.slider("Board Size (n)", 4, 16, 8, key="lv_basic_n")
        max_restarts = st.number_input("Max Restarts", 1, 20000, 500, key="lv_basic_r")
        delay = st.slider("Delay (sec)", 0.0, 1.0, 0.2, key="lv_basic_d")
        seed_val = st.text_input("Random Seed (optional)", key="lv_basic_s")
        seed = int(seed_val) if seed_val.isdigit() else None
        run_btn = st.button("🚀 Run Visualization", use_container_width=True)

    st.title("🎰 Las Vegas N-Queens Visualizer")
    st.caption("Randomly placing queens row-by-row. If it hits a dead-end, it restarts.")

    status_box = st.empty()
    board_box = st.empty()
    log_box = st.empty()

    if run_btn:
        all_steps = generate_lv_steps(n, max_restarts, seed)
        logs = []
        
        for step in all_steps:
            st_type = step["type"]
            msg = f"Event: {st_type}"
            if st_type == "attempt_start": msg = f"Attempt {step['attempt']}: Starting new..."
            elif st_type == "row_scan": msg = f"Attempt {step['attempt']} | Row {step['row']+1}: Scanning safe."
            elif st_type == "place": msg = f"Attempt {step['attempt']} | Placed Q at ({step['row']+1}, {step['col']+1})"
            elif st_type == "dead_end": msg = f"❌ Dead-end at Row {step['row']+1}!"
            elif st_type == "restart": msg = "Restarting..."
            elif st_type == "success": msg = f"✅ SUCCESS on attempt {step['attempt']}."
            elif st_type == "failed": msg = f"Failed after {step['attempt']} restarts."
            
            status_box.info(msg)
            logs.append(msg)
            
            board_html = render_board(n, step.get("queens", []), row=step.get("row"), safe=step.get("safe_cols"), dead=(st_type == "dead_end"))
            board_box.markdown(board_html, unsafe_allow_html=True)
            log_box.code("\n".join(logs[-5:]))
            
            time.sleep(delay)
            if st_type == "success":
                st.balloons()
                break
    else:
        st.info("Adjust the settings in the sidebar and click 'Run Visualization'.")

# ── Route 3: 8-Queens Compare (LV vs BT) ───────────────────────────────────────
elif app_selection == "8-Queens Compare (LV vs BT)":
    with st.sidebar:
        st.divider()
        st.header("⚙️ Compare Controls")
        n = st.slider("Board Size (n)", 4, 12, 8, key="cmp_n")
        max_restarts = st.number_input("Max LV Restarts", 1, 20000, 500, key="cmp_r")
        delay = st.slider("Delay (sec)", 0.0, 1.0, 0.15, key="cmp_d")
        seed_val = st.text_input("LV Random Seed", key="cmp_s")
        seed = int(seed_val) if seed_val.isdigit() else None
        run_btn = st.button("🚀 Auto Compare", use_container_width=True)

    st.title("⚔️ 8-Queens: Las Vegas vs Backtracking")
    st.caption("Synchronized step-by-step trace comparison.")

    global_status = st.empty()
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎰 Las Vegas")
        lv_status = st.empty()
        lv_board = st.empty()
        lv_metrics = st.empty()
        
    with col2:
        st.subheader("🔙 Backtracking")
        bt_status = st.empty()
        bt_board = st.empty()
        bt_metrics = st.empty()

    if run_btn:
        lv_steps = generate_lv_steps(n, max_restarts, seed)
        bt_steps = generate_bt_steps(n)
        
        total_steps = max(len(lv_steps), len(bt_steps))
        
        lv_restarts = 0
        bt_calls = 0
        bt_backs = 0
        
        for idx in range(total_steps):
            # LV Update
            lv_evt = lv_steps[idx] if idx < len(lv_steps) else lv_steps[-1]
            if lv_evt["type"] == "restart": lv_restarts += 1
            lv_msg = f"{lv_evt['type']} (Att: {lv_evt.get('attempt','')})"
            lv_status.info(f"LV Event: **{lv_msg}**")
            
            lv_board_html = render_board(n, lv_evt.get("queens", []), row=lv_evt.get("row"), safe=lv_evt.get("safe_cols"), dead=(lv_evt["type"] == "dead_end"))
            lv_board.markdown(lv_board_html, unsafe_allow_html=True)
            lv_metrics.markdown(f"**Step:** {min(idx+1, len(lv_steps))}/{len(lv_steps)} | **Restarts:** {lv_restarts}")

            # BT Update
            bt_evt = bt_steps[idx] if idx < len(bt_steps) else bt_steps[-1]
            if bt_evt["type"] == "row_start": bt_calls += 1
            if bt_evt["type"] == "backtrack": bt_backs += 1
            bt_msg = f"{bt_evt['type']} "
            if "row" in bt_evt and bt_evt["row"] is not None: bt_msg += f"R:{bt_evt['row']+1}"
            if "col" in bt_evt and bt_evt["col"] is not None: bt_msg += f" C:{bt_evt['col']+1}"
            bt_status.info(f"BT Event: **{bt_msg}**")
            
            bt_board_html = render_board(
                n, bt_evt.get("queens", []), row=bt_evt.get("row"), 
                dead=(bt_evt["type"] == "dead_end"), 
                try_col=bt_evt.get("col") if bt_evt["type"]=="try_col" else None,
                try_safe=bt_evt.get("safe_col")
            )
            bt_board.markdown(bt_board_html, unsafe_allow_html=True)
            bt_metrics.markdown(f"**Step:** {min(idx+1, len(bt_steps))}/{len(bt_steps)} | **Calls:** {bt_calls} | **Backtracks:** {bt_backs}")

            # Global
            global_status.markdown(f"### Compare Step: {idx+1} / {total_steps}")
            time.sleep(delay)
            
        st.success(f"Comparison Complete! Las Vegas took {len(lv_steps)} steps. Backtracking took {len(bt_steps)} steps.")
    else:
        # Initial empty state rendering
        empty_board = render_board(n, [])
        with col1: lv_board.markdown(empty_board, unsafe_allow_html=True)
        with col2: bt_board.markdown(empty_board, unsafe_allow_html=True)
        st.info("Adjust the settings in the sidebar and click 'Auto Compare'.")


# ── Route 4: Randomized Quick Sort ─────────────────────────────────────────────
elif app_selection == "Randomized Quick Sort":
    with st.sidebar:
        st.divider()
        st.header("⚙️ Array Controls")
        arr_size = st.slider("Array Size", 8, 100, 28, key="qs_size")
        delay = st.slider("Delay (sec)", 0.0, 1.0, 0.1, key="qs_d")
        seed_val = st.text_input("Seed (optional)", key="qs_s")
        seed = int(seed_val) if seed_val.isdigit() else None
        
        c1, c2 = st.columns(2)
        run_btn = c1.button("🚀 Auto Play", use_container_width=True)

    st.title("📊 Randomized Quick Sort Visualizer")
    st.caption("Selects a random pivot for each partition. Visualizing compare/swap step by step.")

    status_box = st.empty()
    metrics_box = st.empty()
    bar_box = st.empty()

    if run_btn:
        if seed is not None: random.seed(seed)
        arr = [random.randint(5, 99) for _ in range(arr_size)]
        
        all_steps = generate_qsort_steps(arr, seed)
        
        cmps = 0
        swps = 0
        pvts = 0
        
        for idx, step in enumerate(all_steps):
            if step["type"] == "compare": cmps += 1
            if step["type"] == "swap": swps += 1
            if step["type"] == "pivot-select": pvts += 1
            
            status_box.info(f"**Action:** {step['msg']}")
            
            cols = metrics_box.columns(4)
            cols[0].metric("Comparisons", cmps)
            cols[1].metric("Swaps", swps)
            cols[2].metric("Pivot Picks", pvts)
            cols[3].metric("Step", f"{idx+1}/{len(all_steps)}")
            
            bar_html = render_bars(step)
            bar_box.markdown(bar_html, unsafe_allow_html=True)
            
            time.sleep(delay)
            
        st.success("Array sorted completely!")
        st.balloons()
    else:
        # Initial View
        st.info("Adjust settings in the sidebar and click 'Auto Play'.")
        dummy_arr = [random.randint(5, 99) for _ in range(arr_size)]
        bar_box.markdown(render_bars({"array": dummy_arr}), unsafe_allow_html=True)
