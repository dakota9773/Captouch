import tkinter as tk
from tkinter import ttk, filedialog
import serial
import threading
import collections
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time
import csv
import datetime

def update_display(canvas, counter1_text, counter2_text, counter3_text, counter4_text,
                   timer1_text, timer2_text, timer3_text, timer4_text):
    global delta1_timer, delta2_timer, delta3_timer, delta4_timer
    global delta1_counter, delta2_counter, delta3_counter, delta4_counter

    # For Delta 1:
    if delta1 >= DELTA_THRESHOLD1:
        if delta1_counter < 1
            delta1_start_time
        if not delta1_touch_detected:
            delta1_touch_detected = True
            delta1_counter += 1
        delta1_timer = time.time() - delta1_start_time
    elif delta1 < DELTA_THRESHOLD1:
        delta1_timer = delta1_timer

    # For Delta 2:
    if delta2_touch_detected:
        delta2_timer = time.time() - delta2_start_time
    else:
        delta2_timer = delta2_timer

    # For Delta 3:
    if delta3_touch_detected:
        delta3_timer = time.time() - delta3_start_time
    else:
        delta3_timer = delta3_timer

    # For Delta 4:
    if delta4_touch_detected:
        delta4_timer = time.time() - delta4_start_time
    else:
        delta4_timer = delta4_timer

    # Update timer displays
    canvas.itemconfig(timer1_text, text=f"O1 Timer: {delta1_timer:.2f} sec")
    canvas.itemconfig(timer2_text, text=f"O2 Timer: {delta2_timer:.2f} sec")
    canvas.itemconfig(timer3_text, text=f"O3 Timer: {delta3_timer:.2f} sec")
    canvas.itemconfig(timer4_text, text=f"O4 Timer: {delta4_timer:.2f} sec")

    # Update counter displays continuously
    canvas.itemconfig(counter1_text, text=f"O1 Count: {delta1_counter}")
    canvas.itemconfig(counter2_text, text=f"O2 Count: {delta2_counter}")
    canvas.itemconfig(counter3_text, text=f"O3 Count: {delta3_counter}")
    canvas.itemconfig(counter4_text, text=f"O4 Count: {delta4_counter}")

    # Schedule the next update (e.g. every 100 ms)
    canvas.after(100, lambda: update_display(canvas, counter1_text, counter2_text,
                                             counter3_text, counter4_text,
                                             timer1_text, timer2_text,
                                             timer3_text, timer4_text))




    # Touch detection for Delta 1
    if delta1 > DELTA_THRESHOLD1:
        canvas.itemconfig(circle1, fill='dark blue', outline='blue')
        canvas.itemconfig(delta1_text, text=f"O1 (E{delta1_index:02}): {delta1:.2f}")
        if not delta1_touch_detected:
            delta1_touch_detected = True
            delta1_counter += 1
            delta1_start_time = time.time()
    elif delta1 <= DELTA_THRESHOLD1:
        canvas.itemconfig(circle1, fill='blue', outline='dark blue')
        canvas.itemconfig(delta1_text, text=f"O1 (E{delta1_index:02}): {delta1:.2f}")
        if delta1_touch_detected:
            delta1_touch_detected = False
            delta1_timer += time.time() - delta1_start_time

    # Touch detection for Delta 2
    if delta2 > DELTA_THRESHOLD1:
        canvas.itemconfig(circle2, fill='dark red', outline='red')
        canvas.itemconfig(delta2_text, text=f"O2 (E{delta2_index:02}): {delta2:.2f}")
        if not delta2_touch_detected:
            delta2_touch_detected = True
            delta2_counter += 1
            delta2_start_time = time.time()
    elif delta2 <= DELTA_THRESHOLD1:
        canvas.itemconfig(circle2, fill='red', outline='dark red')  # Revert to blue
        canvas.itemconfig(delta2_text, text=f"O2 (E{delta2_index:02}): {delta2:.2f}")
        if delta2_touch_detected:
            delta2_touch_detected = False
            delta2_timer += time.time() - delta2_start_time

    # Touch detection for Delta 3
    if delta3 > DELTA_THRESHOLD1:
        canvas.itemconfig(circle3, fill='dark green', outline='green')
        canvas.itemconfig(delta3_text, text=f"O3 (E{delta3_index:02}): {delta3:.2f}")
        if not delta3_touch_detected:
            delta3_touch_detected = True
            delta3_counter += 1
            delta3_start_time = time.time()
    elif delta3 <= DELTA_THRESHOLD1:
        canvas.itemconfig(circle3, fill='green', outline='dark green')
        canvas.itemconfig(delta3_text, text=f"O3 (E{delta3_index:02}): {delta3:.2f}")
        if delta3_touch_detected:
            delta3_touch_detected = False
            delta3_timer += time.time() - delta3_start_time

    # Touch detection for Delta 4
    if delta4 > DELTA_THRESHOLD1:
        canvas.itemconfig(circle4, fill='dark orange', outline='orange')
        canvas.itemconfig(delta4_text, text=f"O4 (E{delta4_index:02}): {delta4:.2f}")
        if not delta4_touch_detected:
            delta4_touch_detected = True
            delta4_counter += 1
            delta4_start_time = time.time()
    elif delta4 <= DELTA_THRESHOLD1:
        canvas.itemconfig(circle4, fill='orange', outline='dark orange')  # Revert to blue
        canvas.itemconfig(delta4_text, text=f"O4 (E{delta4_index:02}): {delta4:.2f}")
        if delta4_touch_detected:
            delta4_touch_detected = False
            delta4_timer += time.time() - delta4_start_time