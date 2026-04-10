import streamlit as st
import random
import pandas as pd

# --- Page Configuration ---
st.set_page_config(page_title="Sorting Visualizer by microsteatejeck", layout="wide")
st.title("Sorting Algorithm Visualizer")

# --- Sorting Algorithm Generators (Updated for Round-by-Round) ---

def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                swapped = True
        # Yield only after one full pass (Round)
        yield arr, f"Round {i + 1} complete"
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
        yield arr, f"Round {i + 1}: Found minimum and swapped"

def insertion_sort(arr):
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
        yield arr, f"Round {i}: Inserted element {key}"

def bucket_sort(arr):
    n = len(arr)
    if n <= 1: return
    buckets = [[] for _ in range(n)]
    for val in arr:
        index = int(n * val) if val < 1 else n - 1
        buckets[index].append(val)
    yield arr, "Round 1: Distributed all elements into buckets"
    
    k = 0
    for i in range(n):
        buckets[i].sort()
        for val in buckets[i]:
            arr[k] = val
            k += 1
        yield arr, f"Round {i + 2}: Reconstructed from bucket {i}"

# --- Session State Initialization ---
if "arr" not in st.session_state:
    st.session_state.arr = [0.42, 0.89, 0.63, 0.12, 0.94, 0.27, 0.78, 0.03, 0.50, 0.36]

if "sorter_iterator" not in st.session_state:
    st.session_state.sorter_iterator = None

if "history" not in st.session_state:
    st.session_state.history = []

if "current_status" not in st.session_state:
    st.session_state.current_status = "Waiting to start"

# --- Sidebar Controls ---
st.sidebar.header("Settings")
algo_name = st.sidebar.selectbox("Select Algorithm", 
    ["Bubble Sort", "Selection Sort", "Insertion Sort", "Bucket Sort"])

st.sidebar.subheader("Data Input")
manual_input = st.sidebar.text_input("Enter list (comma separated)", placeholder="0.5, 0.8, 0.2")

if st.sidebar.button("Load List"):
    try:
        st.session_state.arr = [float(x.strip()) for x in manual_input.split(",") if x.strip()]
        st.session_state.history = []
        st.session_state.sorter_iterator = None
        st.success("Loaded")
    except ValueError:
        st.sidebar.error("Use valid numbers")

if st.sidebar.button("Randomize Data"):
    st.session_state.arr = [round(random.uniform(0, 1), 2) for _ in range(10)]
    st.session_state.history = []
    st.session_state.sorter_iterator = None
    st.rerun()

# --- Main Logic ---

# Initialize the Generator when "Start" is clicked
if st.sidebar.button("Start Step-by-Step", use_container_width=True):
    arr_copy = st.session_state.arr.copy()
    if algo_name == "Bubble Sort": st.session_state.sorter_iterator = bubble_sort(arr_copy)
    elif algo_name == "Selection Sort": st.session_state.sorter_iterator = selection_sort(arr_copy)
    elif algo_name == "Insertion Sort": st.session_state.sorter_iterator = insertion_sort(arr_copy)
    elif algo_name == "Bucket Sort": st.session_state.sorter_iterator = bucket_sort(arr_copy)
    
    st.session_state.history = [{"Round": "Initial", "State": "{" + ", ".join(map(str, st.session_state.arr)) + "}"}]
    st.session_state.current_status = "Sorting initialized"
    st.rerun()

# Display Visuals
st.subheader(f"Current State: {algo_name}")
st.bar_chart(st.session_state.arr)
st.write(f"Status: {st.session_state.current_status}")

# The "Next Round" Button
if st.session_state.sorter_iterator is not None:
    if st.button("Next Round"):
        try:
            # Get the next round from the generator
            current_arr, status = next(st.session_state.sorter_iterator)
            
            # Update the main array for the chart
            st.session_state.arr = current_arr.copy()
            st.session_state.current_status = status
            
            # Add to history table
            round_num = len(st.session_state.history)
            st.session_state.history.append({
                "Round": round_num, 
                "State": "{" + ", ".join(map(str, current_arr)) + "}"
            })
            st.rerun()
        except StopIteration:
            st.session_state.current_status = "Sorting completed"
            st.session_state.sorter_iterator = None
            st.rerun()

# --- History Grid ---
if st.session_state.history:
    st.subheader("Round Results")
    df = pd.DataFrame(st.session_state.history)
    st.table(df)
