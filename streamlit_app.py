import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import re

# --- Logic Configuration ---
SAFE_FUNCTIONS = {
    "sin": np.sin, "cos": np.cos, "tan": np.tan,
    "exp": np.exp, "log": np.log, "ln": np.log,
    "sqrt": np.sqrt, "abs": np.abs, "pi": np.pi,
    "e": np.e, "np": np,
}

def normalize_expression(expression: str) -> str:
    expression = expression.replace("^", "**")
    expression = re.sub(r"(\d)([A-Za-z])", r"\1*\2", expression)
    expression = re.sub(r"([xXyYzZ])\(", r"\1*(", expression)
    expression = re.sub(r"\)([xXyYzZ0-9])", r")*\1", expression)
    return expression

# --- 2D Logic ---
def build_2d_branches(equation_text: str):
    expr = normalize_expression(equation_text).strip()
    if "=" not in expr: return [expr]
    
    lhs, rhs = expr.split("=", 1)
    lhs, rhs = lhs.strip().lower(), rhs.strip()
    
    if lhs in {"y", "f(x)"}: return [rhs]
    if rhs.lower() in {"y", "f(x)"}: return [lhs]
    
    if "y**2" in lhs:
        return [f"sqrt(np.where(({rhs}) >= 0, ({rhs}), np.nan))", 
                f"-sqrt(np.where(({rhs}) >= 0, ({rhs}), np.nan))"]
    return [rhs]

# --- 3D Logic ---
def build_3d_logic(equation_text: str):
    expr = normalize_expression(equation_text).strip()
    if "=" in expr:
        lhs_raw, rhs_raw = expr.split("=", 1)
        def implicit_fn(x, y, z):
            l_val = eval(lhs_raw, {"__builtins__": {}}, {"x": x, "y": y, "z": z, **SAFE_FUNCTIONS})
            r_val = eval(rhs_raw, {"__builtins__": {}}, {"x": x, "y": y, "z": z, **SAFE_FUNCTIONS})
            return l_val - r_val
        return implicit_fn
    else:
        return lambda x, y, z: z - eval(expr, {"__builtins__": {}}, {"x": x, "y": y, **SAFE_FUNCTIONS})

# --- Streamlit UI ---
st.set_page_config(page_title="Monte Carlo Integration", layout="wide")
st.title("🎲 Monte Carlo Integration Visualizer")

mode = st.sidebar.radio("Dimensions", ["2D Integration", "3D Volume"])
st.sidebar.markdown("---")

# Common Inputs
eq_input = st.sidebar.text_input("Equation", "y = x^2 + 1" if mode == "2D Integration" else "x^2 + y^2 + z^2 = 1")
num_points = st.sidebar.number_input("Random Points", 100, 200000, 10000, step=1000)

col1, col2 = st.sidebar.columns(2)
x_min = col1.number_input("X Min", value=-2.0)
x_max = col2.number_input("X Max", value=2.0)

if mode == "3D Volume":
    col3, col4 = st.sidebar.columns(2)
    y_min = col3.number_input("Y Min", value=-2.0)
    y_max = col4.number_input("Y Max", value=2.0)
    col5, col6 = st.sidebar.columns(2)
    z_min = col5.number_input("Z Min", value=-2.0)
    z_max = col6.number_input("Z Max", value=2.0)
else:
    col3, col4 = st.sidebar.columns(2)
    y_min_bound = col3.number_input("Y Min", value=0.0)
    y_max_bound = col4.number_input("Y Max", value=5.0)

# --- Execution ---
try:
    if mode == "2D Integration":
        branches = build_2d_branches(eq_input)
        x_rand = np.random.uniform(x_min, x_max, num_points)
        y_rand = np.random.uniform(y_min_bound, y_max_bound, num_points)
        
        inside_mask = np.zeros(num_points, dtype=bool)
        for b in branches:
            y_curve = eval(b, {"__builtins__": {}}, {"x": x_rand, **SAFE_FUNCTIONS})
            # Standard MC: point is between 0 and the curve
            inside_mask |= (y_rand >= 0) & (y_rand <= y_curve)
        
        estimate = (x_max - x_min) * (y_max_bound - y_min_bound) * np.mean(inside_mask)
        
        fig, ax = plt.subplots(figsize=(10, 5))
        x_plot = np.linspace(x_min, x_max, 1000)
        for b in branches:
            y_plot = eval(b, {"__builtins__": {}}, {"x": x_plot, **SAFE_FUNCTIONS})
            ax.plot(x_plot, y_plot, color="#2E7D32", lw=2)
        
        ax.scatter(x_rand[inside_mask], y_rand[inside
