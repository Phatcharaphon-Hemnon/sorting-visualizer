import streamlit as st
import random
import time
import pandas as pd
import plotly.graph_objects as go

# --- Page Configuration ---
st.set_page_config(page_title="Sorting Visualizer by microsteatejeck", layout="wide")
st.title("Sorting Algorithm Visualizer")

# --- Color Helper ---
NORMAL_COLOR = "#4C9BE8"
HIGHLIGHT_COLOR = "#5dfc28"

def make_bar_chart(arr, highlight_indices=None):
    colors = []
    for i in range(len(arr)):
        if highlight_indices and i in highlight_indices:
            colors.append(HIGHLIGHT_COLOR)
        else:
            colors.append(NORMAL_COLOR)
    fig = go.Figure(
        data=[go.Bar(y=arr, marker_color=colors, showlegend=False)],
        layout=go.Layout(
            margin=dict(l=10, r=10, t=10, b=10),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(gridcolor="#333"),
            height=400,
        )
    )
    return fig

# --- Sorting Algorithm Generators ---

def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
        yield arr, f"Round {i + 1} Complete", list(range(n - i - 1, n))
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
        yield arr, f"Round {i + 1} Complete", [i]

def insertion_sort(arr):
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
        yield arr, f"Round {i} Complete", [j + 1]

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
    yield arr, "Round 1: Max Heap Built", [0]

    for i in range(n - 1, 0, -1):
        arr[i], arr[0] = arr[0], arr[i]
        heapify(i, 0)
        yield arr, f"Round {n - i + 1}: Extracted max to index {i}", [i]

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
        yield arr, f"Pivot {pivot} placed", [p]
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
        yield arr, f"Merged range {l} to {r}", list(range(l, r + 1))

def bucket_sort(arr):
    n = len(arr)
    if n <= 1:
        return
    buckets = [[] for _ in range(n)]
    for val in arr:
        index = int(n * val) if val < 1 else n - 1
        buckets[index].append(val)
    yield arr, "Elements distributed to buckets", []
    k = 0
    for i in range(n):
        buckets[i].sort()
        for val in buckets[i]:
            arr[k] = val
            k += 1
        yield arr, f"Bucket {i} sorted and merged", list(range(max(0, k - len(buckets[i])), k))

def counting_sort(arr):
    if any(x < 0 for x in arr):
        return
    max_val = int(max(arr))
    count = [0] * (max_val + 1)
    for x in arr:
        count[int(x)] += 1
    yield arr, "Occurrences counted", []
    i = 0
    for val, c in enumerate(count):
        if c > 0:
            start = i
            for _ in range(c):
                arr[i] = float(val)
                i += 1
            yield arr, f"Placed all of value {val}", list(range(start, i))

# --- Sidebar Controls ---
st.sidebar.header("Settings")
algo_name = st.sidebar.selectbox("Select Algorithm",
    ["Bubble Sort", "Selection Sort", "Insertion Sort", "Heap Sort", "Quick Sort", "Merge Sort", "Bucket Sort", "Counting Sort"])

st.sidebar.subheader("Data Input")
manual_input = st.sidebar.text_input("Enter list (comma separated)", placeholder="e.g. 0.5, 0.2, 0.8, 0.1")

if st.sidebar.button("Load List"):
    try:
        new_arr = [float(x.strip()) for x in manual_input.split(",") if x.strip()]
        if new_arr:
            st.session_state.arr = new_arr
            st.success("Loaded")
    except ValueError:
        st.sidebar.error("Please use valid numbers")

single_val = st.sidebar.number_input("Add a single number", min_value=0.0, max_value=200.0, value=0.5, step=0.1, format="%.2f")
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("Add"):
        if "arr" not in st.session_state: st.session_state.arr = []
        st.session_state.arr.append(single_val)
        st.rerun()
with col2:
    if st.button("Clear"):
        st.session_state.arr = []
        st.rerun()

st.sidebar.markdown("---")
data_size = st.sidebar.slider("Random Array Size", 5, 50, 10)
speed = st.sidebar.slider("Speed (s) per Round", 0.0, 2.0, 0.5)

if "arr" not in st.session_state or st.sidebar.button("Randomize Data"):
    if algo_name == "Bucket Sort":
        st.session_state.arr = [round(random.uniform(0, 1), 2) for _ in range(data_size)]
    else:
        st.session_state.arr = [float(random.randint(1, 100)) for _ in range(data_size)]

# --- Main Visualization Area ---
status_text = st.empty()
chart_placeholder = st.empty()
history_header = st.empty()
history_placeholder = st.empty()

def run_visualization():
    if not st.session_state.arr:
        st.error("Please add some data first")
        return

    arr_copy = st.session_state.arr.copy()
    history = []
    history.append({"Round": 0, "State": "{" + ", ".join(map(str, arr_copy)) + "}"})

    if algo_name == "Bubble Sort":       sorter = bubble_sort(arr_copy)
    elif algo_name == "Selection Sort":  sorter = selection_sort(arr_copy)
    elif algo_name == "Insertion Sort":  sorter = insertion_sort(arr_copy)
    elif algo_name == "Heap Sort":       sorter = heap_sort(arr_copy)
    elif algo_name == "Quick Sort":      sorter = quick_sort(arr_copy, 0, len(arr_copy) - 1)
    elif algo_name == "Merge Sort":      sorter = merge_sort(arr_copy, 0, len(arr_copy) - 1)
    elif algo_name == "Bucket Sort":     sorter = bucket_sort(arr_copy)
    elif algo_name == "Counting Sort":   sorter = counting_sort(arr_copy)

    round_count = 1
    for current_arr, state, highlights in sorter:
        status_text.markdown(f"**Current Status:** {state}")
        chart_placeholder.plotly_chart(
            make_bar_chart(current_arr, highlight_indices=highlights),
            use_container_width=True,
            key=f"chart_{round_count}"
        )

        history.append({"Round": round_count, "State": "{" + ", ".join(map(str, current_arr)) + "}"})
        round_count += 1

        history_header.subheader("Round History")
        history_placeholder.table(pd.DataFrame(history))

        if speed > 0:
            time.sleep(speed)

    status_text.success(f"{algo_name} Finished")
    chart_placeholder.plotly_chart(
        make_bar_chart(arr_copy, highlight_indices=list(range(len(arr_copy)))),
        use_container_width=True,
        key=f"chart_{round_count}_done"
    )

if st.session_state.arr:
    chart_placeholder.plotly_chart(
        make_bar_chart(st.session_state.arr),
        use_container_width=True,
        key="chart_initial"
    )
else:
    chart_placeholder.info("List is empty.")

if st.sidebar.button("Start Sorting", use_container_width=True):
    run_visualization()
