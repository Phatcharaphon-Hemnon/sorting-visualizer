import streamlit as st
import random
import time

# --- Page Configuration ---
st.set_page_config(page_title="Sorting Visualizer by microsteatejeck", layout="wide")
st.title("Sorting Algorithm Visualizer")

# --- Sorting Algorithm Generators ---

def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            yield arr, [j, j + 1], "Comparing"
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                yield arr, [j, j + 1], "Swapping"

def selection_sort(arr):
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            yield arr, [min_idx, j], "Finding Minimum"
            if arr[j] < arr[min_idx]:
                min_idx = j
                yield arr, [min_idx], "New Minimum Found"
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
        yield arr, [i, min_idx], "Swapping"

def insertion_sort(arr):
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        yield arr, [i], "Selecting Element"
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            yield arr, [j, j + 1], "Moving Elements"
            j -= 1
        arr[j + 1] = key
        yield arr, [j + 1], "Inserting"

def quick_sort(arr, low, high):
    if low < high:
        pivot = arr[high]
        i = low - 1
        for j in range(low, high):
            yield arr, [j, high], "Comparing with Pivot"
            if arr[j] <= pivot:
                i += 1
                arr[i], arr[j] = arr[j], arr[i]
                yield arr, [i, j], "Swapping"
        arr[i + 1], arr[high] = arr[high], arr[i + 1]
        yield arr, [i + 1, high], "Placing Pivot"
        p = i + 1
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
            yield arr, [k], "Merging"
            k += 1
        while i < len(left_part):
            arr[k] = left_part[i]
            yield arr, [k], "Merging"
            i += 1
            k += 1
        while j < len(right_part):
            arr[k] = right_part[j]
            yield arr, [k], "Merging"
            j += 1
            k += 1

def heap_sort(arr):
    n = len(arr)
    for i in range(n // 2 - 1, -1, -1):
        curr, end = i, n
        while True:
            largest = curr
            l, r = 2*curr+1, 2*curr+2
            if l < end and arr[curr] < arr[l]: largest = l
            if r < end and arr[largest] < arr[r]: largest = r
            if largest != curr:
                arr[curr], arr[largest] = arr[largest], arr[curr]
                yield arr, [curr, largest], "Building Heap"
                curr = largest
            else: break
    for i in range(n-1, 0, -1):
        arr[i], arr[0] = arr[0], arr[i]
        yield arr, [0, i], "Extracting Max"
        curr, end = 0, i
        while True:
            largest = curr
            l, r = 2*curr+1, 2*curr+2
            if l < end and arr[curr] < arr[l]: largest = l
            if r < end and arr[largest] < arr[r]: largest = r
            if largest != curr:
                arr[curr], arr[largest] = arr[largest], arr[curr]
                yield arr, [curr, largest], "Heapifying"
                curr = largest
            else: break

def bucket_sort(arr):
    n = len(arr)
    if n <= 1: return
    # Creating n buckets
    buckets = [[] for _ in range(n)]
    for val in arr:
        # Assuming values are between 0 and 1 for Bucket Sort visualization
        index = int(n * val) if val < 1 else n - 1
        buckets[index].append(val)
        yield arr, [arr.index(val)], f"Putting {val} in bucket {index}"
    
    k = 0
    for i in range(n):
        buckets[i].sort()
        for val in buckets[i]:
            arr[k] = val
            yield arr, [k], f"Reconstructing from bucket {i}"
            k += 1

def counting_sort(arr):
    # This works for non-negative integers only. 
    # If floats are present, we temporarily convert for index mapping.
    if any(x < 0 for x in arr):
        yield arr, [], "Error: Counting Sort requires non-negative numbers"
        return
    
    max_val = int(max(arr))
    count = [0] * (max_val + 1)
    
    for i, x in enumerate(arr):
        count[int(x)] += 1
        yield arr, [i], f"Counting occurrences of {int(x)}"
    
    i = 0
    for a in range(len(count)):
        for _ in range(count[a]):
            arr[i] = float(a)
            yield arr, [i], f"Placing {a} back in array"
            i += 1

# --- Sidebar Controls ---
st.sidebar.header("Settings")

algo_name = st.sidebar.selectbox("Select Algorithm", 
    ["Bubble Sort", "Selection Sort", "Insertion Sort", "Quick Sort", "Merge Sort", "Heap Sort", "Bucket Sort", "Counting Sort"])

st.sidebar.subheader("Data Input")

# --- MODIFIED: Accepts Floats ---
manual_input = st.sidebar.text_input("Enter list (comma separated)", placeholder="e.g. 0.5, 0.2, 0.8, 0.1")
if st.sidebar.button("Load List"):
    try:
        # Changed to float() to handle decimals
        new_arr = [float(x.strip()) for x in manual_input.split(",") if x.strip()]
        if new_arr:
            st.session_state.arr = new_arr
            st.success("Loaded!")
    except ValueError:
        st.sidebar.error("Please use valid numbers (e.g., 0.5, 10, 2.5)")

# Single Number Input (Float)
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
data_size = st.sidebar.slider("Random Array Size", 5, 100, 30)
speed = st.sidebar.slider("Speed (s)", 0.0, 0.5, 0.05)

if "arr" not in st.session_state or st.sidebar.button("Randomize Data"):
    # Randomize with decimals if Bucket Sort is picked, otherwise integers
    if algo_name == "Bucket Sort":
        st.session_state.arr = [round(random.uniform(0, 1), 2) for _ in range(data_size)]
    else:
        st.session_state.arr = [float(random.randint(1, 100)) for _ in range(data_size)]

# --- Main Visualization Area ---
status_text = st.empty()
chart_placeholder = st.empty()

def run_visualization():
    if not st.session_state.arr:
        st.error("Please add some data first!")
        return

    arr_copy = st.session_state.arr.copy()
    
    if algo_name == "Bubble Sort": sorter = bubble_sort(arr_copy)
    elif algo_name == "Selection Sort": sorter = selection_sort(arr_copy)
    elif algo_name == "Insertion Sort": sorter = insertion_sort(arr_copy)
    elif algo_name == "Quick Sort": sorter = quick_sort(arr_copy, 0, len(arr_copy) - 1)
    elif algo_name == "Merge Sort": sorter = merge_sort(arr_copy, 0, len(arr_copy) - 1)
    elif algo_name == "Heap Sort": sorter = heap_sort(arr_copy)
    elif algo_name == "Bucket Sort": sorter = bucket_sort(arr_copy)
    elif algo_name == "Counting Sort": sorter = counting_sort(arr_copy)

    for current_arr, highlights, state in sorter:
        status_text.markdown(f"**Status:** `{state}` | **Indices:** `{highlights}`")
        chart_placeholder.bar_chart(current_arr)
        if speed > 0:
            time.sleep(speed)
    
    status_text.success(f"{algo_name} Complete!")
    chart_placeholder.bar_chart(arr_copy)

if st.session_state.arr:
    chart_placeholder.bar_chart(st.session_state.arr)
else:
    chart_placeholder.info("List is empty. Use the sidebar to add data.")

if st.sidebar.button("Start Sorting", use_container_width=True):
    run_visualization()
