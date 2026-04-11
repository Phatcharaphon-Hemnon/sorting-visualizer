import streamlit as st
import random
import time
import pandas as pd
import plotly.graph_objects as go

# --- Page Configuration ---
st.set_page_config(page_title="Sorting Visualizer by microsteatejeck", layout="wide")
st.title("Sorting Algorithm Visualizer")

# --- Sorting Algorithm Generators (Yielding array, highlights, and status) ---

def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
        yield arr, list(range(n - i - 1, n)), f"Round {i + 1} Complete"
        if not swapped:
            break

def selection_sort(arr):
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
        yield arr, [i, min_idx], f"Round {i + 1} Complete"

def insertion_sort(arr):
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
        yield arr, [j + 1, i], f"Round {i} Complete"

def heap_sort(arr):
    n = len(arr)
    def heapify(n, i):
        largest = i
        l = 2 * i + 1
        r = 2 * i + 2
        if l < n and arr[i] < arr[l]: largest = l
        if r < n and arr[largest] < arr[r]: largest = r
        if largest != i:
            arr[i], arr[largest] = arr[largest], arr[i]
            heapify(n, largest)

    for i in range(n // 2 - 1, -1, -1):
        heapify(n, i)
    yield arr, list(range(n // 2)), "Max Heap Built"

    for i in range(n - 1, 0, -1):
        arr[i], arr[0] = arr[0], arr[i]
        heapify(i, 0)
        yield arr, [0, i], f"Round {n - i + 1}: Max Extracted"

def quick_sort(arr, low, high):
    if low < high:
        pivot = arr[high]
        i = low - 1
        for j in range(low, high):
            if arr[j] <= pivot:
                i += 1
                arr[i], arr[j] = arr[j], arr[i]
        arr[i + 1], arr[high] = arr[high], arr[i + 1]
        p = i + 1
        yield arr, [p, high], f"Pivot {pivot} placed"
        yield from quick_sort(arr, low, p - 1)
        yield from quick_sort(arr, p + 1, high)

def merge_sort(arr, l, r):
    if l < r:
        m = (l + r) // 2
        yield from merge_sort(arr, l, m)
        yield from merge_sort(arr, m + 1, r)
        left_part = arr[l:m+1]
        right_part = arr[m+1:r+1]
        i = j = 0
        k = l
        while i < len(left_part) and j < len(right_part):
            if left_part[i] <= right_part[j]:
                arr[k] = left_part[i]
                i += 1
            else:
                arr[k] = right_part[j]
                j += 1
            k += 1
        while i < len(left_part):
            arr[k] = left_part[i]
            i += 1
            k += 1
        while j < len(right_part):
            arr[k] = right_part[j]
            j += 1
            k += 1
        yield arr, list(range(l, r + 1)), f"Merged range {l} to {r}"

def bucket_sort(arr):
    n = len(arr)
    if n <= 1: return
    buckets = [[] for _ in range(n)]
    for val in arr:
        index = int(n * val) if val < 1 else n - 1
        buckets[index].append(val)
    yield arr, [], "Elements distributed"
    k = 0
    for i in range(n):
        buckets[i].sort()
        start_idx = k
        for val in buckets[i]:
            arr[k] = val
            k += 1
        yield arr, list(range(start_idx, k)), f"Bucket {i} merged"

def counting_sort(arr):
    if any(x < 0 for x in arr): return
    max_val = int(max(arr))
    count = [0] * (max_val + 1)
    for x in arr:
        count[int(x)] += 1
    yield arr, [], "Occurrences counted"
    i = 0
    for val, c in enumerate(count):
        if c > 0:
            start_idx = i
            for _ in range(c):
                arr[i] = float(val)
                i += 1
            yield arr, list(range(start_idx, i)), f"Placed value {val}"

# --- Sidebar Controls ---
st.sidebar.header("Settings")
algo_name = st.sidebar.selectbox("Select Algorithm", 
    ["Bubble Sort", "Selection Sort", "Insertion Sort", "Heap Sort", "Quick Sort", "Merge Sort", "Bucket Sort", "Counting Sort"])

st.sidebar.subheader("Data Input")
manual_input = st.sidebar.text_input("Enter list (comma separated)", placeholder="e.g. 0.5, 0.2, 0.8, 0.1")

if st.sidebar.button("Load List"):
    try:
        st.session_state.arr = [float(x.strip()) for x in manual_input.split(",") if x.strip()]
        st.success("Loaded")
    except ValueError:
        st.sidebar.error("Invalid numbers")

st.sidebar.markdown("---")
data_size = st.sidebar.slider("Random Array Size", 5, 50, 10)
speed = st.sidebar.slider("Speed (s) per Round", 0.0, 2.0, 0.5)

if "arr" not in st.session_state or st.sidebar.button("Randomize Data"):
    if algo_name == "Bucket Sort":
        st.session_state.arr = [round(random.uniform(0, 1), 2) for _ in range(data_size)]
    else:
        st.session_state.arr = [float(random.randint(1, 100)) for _ in range(data_size)]

# --- Helper Function for Colored Plotly Chart ---
def display_chart(arr, highlights=[]):
    colors = ['#636EFA'] * len(arr) # Default Blue
    for idx in highlights:
        if 0 <= idx < len(arr):
            colors[idx] = '#EF553B' # Highlight Red
    
    fig = go.Figure(data=[
        go.Bar(x=list(range(len(arr))), y=arr, marker_color=colors)
    ])
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        height=400,
        xaxis=dict(visible=False),
        yaxis=dict(title="Value")
    )
    chart_placeholder.plotly_chart(fig, use_container_width=True)

# --- Main Visualization Area ---
status_text = st.empty()
chart_placeholder = st.empty()
history_header = st.empty()
history_placeholder = st.empty()

def run_visualization():
    if not st.session_state.arr:
        st.error("Add data first")
        return

    arr_copy = st.session_state.arr.copy()
    history = []
    history.append({"Round": 0, "State": "{" + ", ".join(map(str, arr_copy)) + "}"})
    
    # Selection logic
    if algo_name == "Bubble Sort": sorter = bubble_sort(arr_copy)
    elif algo_name == "Selection Sort": sorter = selection_sort(arr_copy)
    elif algo_name == "Insertion Sort": sorter = insertion_sort(arr_copy)
    elif algo_name == "Heap Sort": sorter = heap_sort(arr_copy)
    elif algo_name == "Quick Sort": sorter = quick_sort(arr_copy, 0, len(arr_copy) - 1)
    elif algo_name == "Merge Sort": sorter = merge_sort(arr_copy, 0, len(arr_copy) - 1)
    elif algo_name == "Bucket Sort": sorter = bucket_sort(arr_copy)
    elif algo_name == "Counting Sort": sorter = counting_sort(arr_copy)

    round_count = 1
    for current_arr, highlights, state in sorter:
        status_text.markdown(f"**Current Status:** {state}")
        display_chart(current_arr, highlights)
        
        history.append({"Round": round_count, "State": "{" + ", ".join(map(str, current_arr)) + "}"})
        round_count += 1
        
        history_header.subheader("Round History")
        history_placeholder.table(pd.DataFrame(history))
        
        if speed > 0:
            time.sleep(speed)
    
    display_chart(arr_copy, []) # Final state (all blue)
    status_text.success(f"{algo_name} Finished")

# Initial Render
if st.session_state.arr:
    display_chart(st.session_state.arr)

if st.sidebar.button("Start Sorting", use_container_width=True):
    run_visualization()
