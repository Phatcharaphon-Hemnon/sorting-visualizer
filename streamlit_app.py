import streamlit as st
import random
import time
import pandas as pd

# --- Page Configuration ---
st.set_page_config(page_title="Sorting Visualizer", layout="wide")
st.title("📊 Sorting Algorithm Visualizer")

# --- Sorting Algorithm Generators ---
# (Keeping your existing logic for bubble_sort, selection_sort, etc.)
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            yield arr, [j, j + 1], "Comparing", "comparison"
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                yield arr, [j, j + 1], "Swapping", "swap"

def selection_sort(arr):
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            yield arr, [min_idx, j], "Finding Minimum", "comparison"
            if arr[j] < arr[min_idx]:
                min_idx = j
                yield arr, [min_idx], "New Minimum Found", "assignment"
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
        yield arr, [i, min_idx], "Swapping to Position", "swap"

def insertion_sort(arr):
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        yield arr, [i], "Selecting Element", "assignment"
        while j >= 0 and arr[j] > key:
            yield arr, [j, j+1], "Comparing & Moving", "comparison"
            arr[j + 1] = arr[j]
            yield arr, [j, j + 1], "Moving Elements", "swap"
            j -= 1
        arr[j + 1] = key
        yield arr, [j + 1], "Inserting", "assignment"

def quick_sort(arr, low, high):
    if low < high:
        pivot = arr[high]
        i = low - 1
        for j in range(low, high):
            yield arr, [j, high], "Comparing with Pivot", "comparison"
            if arr[j] <= pivot:
                i += 1
                arr[i], arr[j] = arr[j], arr[i]
                yield arr, [i, j], "Swapping", "swap"
        arr[i + 1], arr[high] = arr[high], arr[i + 1]
        yield arr, [i + 1, high], "Placing Pivot", "swap"
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
            yield arr, [k], "Comparing sub-elements", "comparison"
            if left_part[i] <= right_part[j]:
                arr[k] = left_part[i]
                i += 1
            else:
                arr[k] = right_part[j]
                j += 1
            yield arr, [k], "Merging", "assignment"
            k += 1
        while i < len(left_part):
            arr[k] = left_part[i]
            yield arr, [k], "Merging Leftover", "assignment"
            i += 1
            k += 1
        while j < len(right_part):
            arr[k] = right_part[j]
            yield arr, [k], "Merging Leftover", "assignment"
            j += 1
            k += 1

def bucket_sort(arr):
    n = len(arr)
    if n <= 1: return
    buckets = [[] for _ in range(n)]
    for val in arr:
        index = int(n * val) if val < 1 else n - 1
        buckets[index].append(val)
        yield arr, [arr.index(val)], f"Putting {val} in bucket {index}", "assignment"
    k = 0
    for i in range(n):
        buckets[i].sort()
        for val in buckets[i]:
            arr[k] = val
            yield arr, [k], f"Reconstructing from bucket {i}", "assignment"
            k += 1

def counting_sort(arr):
    max_val = int(max(arr))
    count = [0] * (max_val + 1)
    for i, x in enumerate(arr):
        count[int(x)] += 1
        yield arr, [i], f"Counting {int(x)}", "comparison"
    i = 0
    for a in range(len(count)):
        for _ in range(count[a]):
            arr[i] = float(a)
            yield arr, [i], f"Placing {a}", "assignment"
            i += 1

# --- Sidebar Controls ---
st.sidebar.header("⚙️ Settings")
algo_name = st.sidebar.selectbox("Select Algorithm", 
    ["Bubble Sort", "Selection Sort", "Insertion Sort", "Quick Sort", "Merge Sort", "Bucket Sort", "Counting Sort"])

data_size = st.sidebar.slider("Random Size", 5, 50, 20)
speed = st.sidebar.slider("Speed (s)", 0.0, 0.5, 0.05)

if "arr" not in st.session_state or st.sidebar.button("Randomize"):
    st.session_state.arr = [round(random.uniform(0, 1), 2) for _ in range(data_size)]

# --- Main Layout ---
# Stats displayed at the top for better visibility
m1, m2, m3, m4 = st.columns(4)
comp_stat = m1.metric("Comparisons", 0)
swap_stat = m2.metric("Swaps", 0)
assign_stat = m3.metric("Assignments", 0)
total_stat = m4.metric("Total Operations", 0)

status_text = st.empty()
chart_placeholder = st.empty()
chart_placeholder.bar_chart(st.session_state.arr)

def run_visualization():
    arr_copy = st.session_state.arr.copy()
    comp, swap, assign = 0, 0, 0
    
    if algo_name == "Bubble Sort": sorter = bubble_sort(arr_copy)
    elif algo_name == "Selection Sort": sorter = selection_sort(arr_copy)
    elif algo_name == "Insertion Sort": sorter = insertion_sort(arr_copy)
    elif algo_name == "Quick Sort": sorter = quick_sort(arr_copy, 0, len(arr_copy)-1)
    elif algo_name == "Merge Sort": sorter = merge_sort(arr_copy, 0, len(arr_copy)-1)
    elif algo_name == "Bucket Sort": sorter = bucket_sort(arr_copy)
    elif algo_name == "Counting Sort": sorter = counting_sort(arr_copy)

    for current_arr, highlights, state, work_type in sorter:
        if work_type == "comparison": comp += 1
        elif work_type == "swap": swap += 1
        elif work_type == "assignment": assign += 1
        
        # Update metrics in place
        comp_stat.metric("Comparisons", comp)
        swap_stat.metric("Swaps", swap)
        assign_stat.metric("Assignments", assign)
        total_stat.metric("Total Operations", comp + swap + assign)
        
        status_text.markdown(f"**Current Status:** `{state}`")
        chart_placeholder.bar_chart(current_arr)
        
        if speed > 0:
            time.sleep(speed)

    st.balloons()

if st.sidebar.button("🚀 Start Sorting", use_container_width=True):
    run_visualization()
