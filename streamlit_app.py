import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- Logic Configuration ---
SAFE_FUNCTIONS = {
    "sin": np.sin,
    "cos": np.cos,
    "tan": np.tan,
    "exp": np.exp,
    "log": np.log,
    "sqrt": np.sqrt,
    "abs": np.abs,
    "pi": np.pi,
    "e": np.e,
}

def normalize_expression(expr: str) -> str:
    return expr.replace("^", "**")

def evaluate_1d(expr: str, x: np.ndarray) -> np.ndarray:
    expr = normalize_expression(expr)
    local_scope = {"x": x, **SAFE_FUNCTIONS}
    return eval(expr, {"__builtins__": {}}, local_scope)

def evaluate_2d(expr: str, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    expr = normalize_expression(expr)
    local_scope = {"x": x, "y": y, **SAFE_FUNCTIONS}
    return eval(expr, {"__builtins__": {}}, local_scope)

# --- Streamlit UI Setup ---
st.set_page_config(page_title="Monte Carlo Visualizer", layout="wide")
st.title("🎯 Monte Carlo Integration Visualizer")

mode = st.sidebar.selectbox("Select Dimension", ["2D (Single Integral)", "3D (Double Integral)"])

# --- Sidebar Inputs ---
st.sidebar.header("Parameters")
func_input = st.sidebar.text_input("Function f(x)" if mode == "2D (Single Integral)" else "Function f(x, y)", 
                                   "sin(x) + 2" if mode == "2D (Single Integral)" else "x^2 + y^2 + 1")

num_points = st.sidebar.slider("Number of Points", 100, 50000, 5000, step=100)

col1, col2 = st.sidebar.columns(2)
x_min = col1.number_input("X Min", value=0.0)
x_max = col2.number_input("X Max", value=float(np.pi))

if mode == "3D (Double Integral)":
    col3, col4 = st.sidebar.columns(2)
    y_min = col3.number_input("Y Min", value=0.0)
    y_max = col4.number_input("Y Max", value=float(np.pi))

# --- Visualization Logic ---
try:
    if mode == "2D (Single Integral)":
        # Data Generation
        x_plot = np.linspace(x_min, x_max, 1000)
        y_plot = evaluate_1d(func_input, x_plot)
        
        y_min_val, y_max_val = np.min(y_plot), np.max(y_plot)
        y_range = y_max_val - y_min_val
        y_sample_min, y_sample_max = y_min_val - 0.1 * y_range, y_max_val + 0.1 * y_range

        # Monte Carlo Sampling
        x_rand = np.random.uniform(x_min, x_max, num_points)
        y_rand = np.random.uniform(y_sample_min, y_sample_max, num_points)
        y_curve = evaluate_1d(func_input, x_rand)
        inside = y_rand <= y_curve

        # Calculation
        hit_ratio = np.mean(inside)
        estimate = (x_max - x_min) * (y_sample_min + hit_ratio * (y_sample_max - y_sample_min))

        # Plotting
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(x_plot, y_plot, color="#2E7D32", lw=2, label=f"f(x)={func_input}")
        ax.fill_between(x_plot, 0, y_plot, alpha=0.2, color="#66BB6A")
        ax.scatter(x_rand[inside], y_rand[inside], s=1, color="#1E88E5", alpha=0.5, label="Inside")
        ax.scatter(x_rand[~inside], y_rand[~inside], s=1, color="#E53935", alpha=0.3, label="Outside")
        ax.set_ylim(y_sample_min, y_sample_max)
        ax.legend()
        
        st.pyplot(fig)
        st.success(f"Estimated Integral: **{estimate:.6f}**")

    else:
        # 3D Data Generation
        res = 50
        x_line = np.linspace(x_min, x_max, res)
        y_line = np.linspace(y_min, y_max, res)
        X, Y = np.meshgrid(x_line, y_line)
        Z = evaluate_2d(func_input, X, Y)

        z_min_val, z_max_val = np.min(Z), np.max(Z)
        z_range = z_max_val - z_min_val
        z_sample_min, z_sample_max = z_min_val - 0.1 * z_range, z_max_val + 0.1 * z_range

        # Monte Carlo Sampling
        x_rand = np.random.uniform(x_min, x_max, num_points)
        y_rand = np.random.uniform(y_min, y_max, num_points)
        z_rand = np.random.uniform(z_sample_min, z_sample_max, num_points)
        z_surface = evaluate_2d(func_input, x_rand, y_rand)
        inside = z_rand <= z_surface

        # Calculation
        hit_ratio = np.mean(inside)
        domain_area = (x_max - x_min) * (y_max - y_min)
        estimate = domain_area * (z_sample_min + hit_ratio * (z_sample_max - z_sample_min))

        # Plotting
        fig = plt.figure(figsize=(10, 7))
        ax = fig.add_subplot(111, projection='3d')
        ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.4)
        
        # Limit display points for performance
        display_n = 5000
        ax.scatter(x_rand[inside][:display_n], y_rand[inside][:display_n], z_rand[inside][:display_n], 
                   s=1, color="#1E88E5", alpha=0.4)
        ax.scatter(x_rand[~inside][:display_n], y_rand[~inside][:display_n], z_rand[~inside][:display_n], 
                   s=1, color="#E53935", alpha=0.2)
        
        st.pyplot(fig)
        st.success(f"Estimated Double Integral (Volume): **{estimate:.6f}**")

except Exception as e:
    st.error(f"Error in expression: {e}")

st.info("Note: The visualizer calculates the area/volume between the curve and the horizontal axis/plane. Adjust bounds to fit the function shape.")
