# Sorting Visualizer

An interactive web application that visualizes how various sorting algorithms work step by step.

## Table of Contents

- [Overview](#overview)
- [Sorting Algorithms](#sorting-algorithms)
  - [Bubble Sort](#bubble-sort)
  - [Selection Sort](#selection-sort)
  - [Insertion Sort](#insertion-sort)
  - [Merge Sort](#merge-sort)
  - [Quick Sort](#quick-sort)
  - [Heap Sort](#heap-sort)
- [Complexity Comparison](#complexity-comparison)
- [Getting Started](#getting-started)
- [License](#license)

---

## Overview

Sorting Visualizer is a tool designed to help you understand how different sorting algorithms operate. Each algorithm is animated so you can observe comparisons, swaps, and the overall structure of the sort as it progresses.

---

## Sorting Algorithms

### Bubble Sort

Bubble Sort is the simplest comparison-based sorting algorithm. It repeatedly steps through the list, compares adjacent elements, and swaps them if they are in the wrong order. The largest unsorted element "bubbles up" to its correct position after each pass.

**How it works:**
1. Start from the first element and compare it with the next.
2. If the current element is greater than the next, swap them.
3. Repeat for every adjacent pair in the array.
4. After each full pass, the next largest element is in its final position.
5. Repeat until no swaps are needed.

**Time Complexity:**
| Case | Complexity |
|------|------------|
| Best | O(n) |
| Average | O(n²) |
| Worst | O(n²) |

**Space Complexity:** O(1) — in-place sorting

---

### Selection Sort

Selection Sort divides the array into a sorted and an unsorted region. On each iteration it finds the minimum element from the unsorted region and moves it to the end of the sorted region.

**How it works:**
1. Find the smallest element in the unsorted portion of the array.
2. Swap it with the first element of the unsorted portion.
3. Move the boundary between sorted and unsorted one position to the right.
4. Repeat until the entire array is sorted.

**Time Complexity:**
| Case | Complexity |
|------|------------|
| Best | O(n²) |
| Average | O(n²) |
| Worst | O(n²) |

**Space Complexity:** O(1) — in-place sorting

---

### Insertion Sort

Insertion Sort builds the sorted array one element at a time by taking each new element and inserting it into its correct position among the already-sorted elements. It is efficient for small or nearly-sorted datasets.

**How it works:**
1. Start with the second element (the first element is trivially sorted).
2. Compare the current element with the elements before it.
3. Shift larger elements one position to the right to make room.
4. Insert the current element into its correct position.
5. Repeat for all remaining elements.

**Time Complexity:**
| Case | Complexity |
|------|------------|
| Best | O(n) |
| Average | O(n²) |
| Worst | O(n²) |

**Space Complexity:** O(1) — in-place sorting

---

### Merge Sort

Merge Sort is a divide-and-conquer algorithm that recursively splits the array in half, sorts each half, and then merges the sorted halves back together. It guarantees O(n log n) performance for all cases.

**How it works:**
1. Divide the array into two halves.
2. Recursively sort each half.
3. Merge the two sorted halves into a single sorted array by comparing elements one at a time.
4. Repeat until the full array is sorted.

**Time Complexity:**
| Case | Complexity |
|------|------------|
| Best | O(n log n) |
| Average | O(n log n) |
| Worst | O(n log n) |

**Space Complexity:** O(n) — requires auxiliary space for merging

---

### Quick Sort

Quick Sort is another divide-and-conquer algorithm that selects a "pivot" element and partitions the array into elements less than the pivot and elements greater than the pivot, then recursively sorts each partition. It is one of the fastest general-purpose sorting algorithms in practice.

**How it works:**
1. Choose a pivot element from the array (commonly the last element).
2. Rearrange elements so that all elements less than the pivot come before it and all elements greater come after it (partitioning step).
3. Recursively apply the same process to the sub-arrays on either side of the pivot.
4. Base case: a sub-array of size 0 or 1 is already sorted.

**Time Complexity:**
| Case | Complexity |
|------|------------|
| Best | O(n log n) |
| Average | O(n log n) |
| Worst | O(n²) |

**Space Complexity:** O(log n) — due to recursive call stack

---

### Heap Sort

Heap Sort uses a binary heap data structure to sort elements. It first builds a max-heap from the array and then repeatedly extracts the maximum element from the heap and places it at the end of the array.

**How it works:**
1. Build a max-heap from the input array.
2. Swap the root (maximum value) with the last element of the heap.
3. Reduce the heap size by one and heapify the root to restore the max-heap property.
4. Repeat steps 2–3 until the heap is empty.

**Time Complexity:**
| Case | Complexity |
|------|------------|
| Best | O(n log n) |
| Average | O(n log n) |
| Worst | O(n log n) |

**Space Complexity:** O(1) — in-place sorting

---

## Complexity Comparison

| Algorithm | Best | Average | Worst | Space | Stable |
|-----------|------|---------|-------|-------|--------|
| Bubble Sort | O(n) | O(n²) | O(n²) | O(1) | ✅ Yes |
| Selection Sort | O(n²) | O(n²) | O(n²) | O(1) | ❌ No |
| Insertion Sort | O(n) | O(n²) | O(n²) | O(1) | ✅ Yes |
| Merge Sort | O(n log n) | O(n log n) | O(n log n) | O(n) | ✅ Yes |
| Quick Sort | O(n log n) | O(n log n) | O(n²) | O(log n) | ❌ No |
| Heap Sort | O(n log n) | O(n log n) | O(n log n) | O(1) | ❌ No |

> **Stable** means equal elements retain their original relative order after sorting.

---

## Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/Phatcharaphon-Hemnon/sorting-visualizer.git
   cd sorting-visualizer
   ```

2. **Open in your browser**
   Open `index.html` in your preferred browser to launch the visualizer.

3. **Use the visualizer**
   - Select a sorting algorithm from the menu.
   - Adjust the array size and animation speed as desired.
   - Click **Generate New Array** to create a random array.
   - Click the algorithm button to start the visualization.

---

## License

This project is open source and available under the [MIT License](LICENSE).