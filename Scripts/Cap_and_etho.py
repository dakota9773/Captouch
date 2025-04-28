"""
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

SERIAL_PORT = 'COM22'
BAUD_RATE = 9600
DELTA_THRESHOLD1 = 10
BUFFER_SIZE = 3
DATA_POINTS = 40

diff_data = [collections.deque(maxlen=DATA_POINTS) for _ in range(12)]
timestamps = collections.deque(maxlen=DATA_POINTS)

delta1_counter = 0
delta2_counter = 0
delta3_counter = 0
delta4_counter = 0
delta1_timer = 0
delta2_timer = 0
delta3_timer = 0
delta4_timer = 0
delta1_start_time = None
delta2_start_time = None
delta3_start_time = None
delta4_start_time = None
delta1_touch_detected = False
delta2_touch_detected = False
delta3_touch_detected = False
delta4_touch_detected = False
ethovision_flag_start = False
ethovision_flag_curr = False

# Variables to store the latest Delta values and timestamp
latest_delta1 = 0.0
latest_delta2 = 0.0
latest_delta3 = 0.0
latest_delta4 = 0.0
latest_timestamp = ""
saving = False
save_thread = None
ser = None
data_queue = collections.deque()



def read_from_serial(ser, canvas, delta1_text, delta2_text, delta3_text, delta4_text, circle1, circle2, circle3, circle4, ax, fig,
                     counter1_text, counter2_text, counter3_text, counter4_text, timer1_text, timer2_text, timer3_text, timer4_text,
                     delta1_index, delta2_index, delta3_index, delta4_index, graph_indices, ethovision_text, ethovision_circle, timer_label):
    global delta1_counter, delta2_counter, delta3_counter, delta4_counter, delta1_timer, delta2_timer, delta3_timer, delta4_timer, delta1_start_time, delta2_start_time, delta3_start_time, delta4_start_time, \
        delta1_touch_detected, delta2_touch_detected, delta3_touch_detected, delta4_touch_detected, latest_delta1, latest_delta2, latest_delta3, latest_delta4, latest_timestamp, ethovision_flag_start,\
        ethovision_flag_curr, data_queue
    buffers = [collections.deque(maxlen=BUFFER_SIZE) for _ in range(13)]  # Updated to 13 buffers for 25 values
    while True:
        try:
            line = ser.readline().decode('utf-8').strip()
            values = list(map(float, line.split(',')))
            if len(values) == 25:

                ethovision_flag_start = int(values[24])

                deltas = []
                for i in range(0, 24, 2):
                    deltas.append(values[i] - values[i + 1])
                smoothed_deltas = [moving_average(buffers[i], deltas[i]) for i in range(12)]

                # Keep delta1 and delta2 uncapped
                delta1 = smoothed_deltas[delta1_index]
                delta2 = smoothed_deltas[delta2_index]
                delta3 = smoothed_deltas[delta3_index]
                delta4 = smoothed_deltas[delta4_index]

                # Update canvas text for deltas (uncapped)
                canvas.itemconfig(delta1_text, text=f"O1 (E{delta1_index:02}): {delta1:.2f}")
                canvas.itemconfig(delta2_text, text=f"O2 (E{delta2_index:02}): {delta2:.2f}")
                canvas.itemconfig(delta3_text, text=f"O3 (E{delta3_index:02}): {delta3:.2f}")
                canvas.itemconfig(delta4_text, text=f"O4 (E{delta4_index:02}): {delta4:.2f}")

                # Update latest delta values and timestamp
                latest_delta1 = round(delta1, 2)
                latest_delta2 = round(delta2, 2)
                latest_delta3 = round(delta3, 2)
                latest_delta4 = round(delta4, 2)
                latest_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if ethovision_flag_start == 1:
                    canvas.itemconfig(ethovision_circle, state='normal', fill='red', outline='dark red')
                    canvas.itemconfig(ethovision_text, state='normal', text="Ethovision Recording", fill='red')
                else:
                    canvas.itemconfig(ethovision_circle, state='hidden')
                    canvas.itemconfig(ethovision_text, state='hidden')


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

                def update_timer(timer_start):
                    local_root = timer_label.winfo_toplevel()  # Renamed to avoid shadowing 'root'
                    if not ethovision_flag_curr:
                        timer_label.config(text="Trial Time: Not Started")
                        return
                    elapsed_time = int(time.time() - timer_start)
                    minutes = elapsed_time // 60
                    seconds = elapsed_time % 60
                    timer_label.config(text=f"Trial Time: {minutes:02d}:{seconds:02d}")
                    local_root.after(1000, lambda: update_timer(timer_start))


                if ethovision_flag_start == 1 and ethovision_flag_curr is False:
                    ethovision_flag_curr = True
                    start_time = time.time()

                if ethovision_flag_start == 1:
                    data_queue.append([
                        latest_timestamp,
                        (time.time() - start_time),
                        latest_delta1,
                        delta1_counter,
                        delta1_timer,
                        latest_delta2,
                        delta2_counter,
                        delta2_timer,
                        latest_delta3,
                        delta3_counter,
                        delta3_timer,
                        latest_delta4,
                        delta4_counter,
                        delta4_timer
                    ])
                    update_timer(start_time)

                if ethovision_flag_start == 0 and ethovision_flag_curr is True:
                    ethovision_flag_curr = False
                    save_data()

                # Update the graph (capped deltas)
                timestamps.append(time.time())
                for i in range(12):
                    diff_data[i].append(smoothed_deltas[i])
                ax.clear()
                full_colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray',
                               'olive', 'cyan', 'magenta', 'black']
                for i in graph_indices:
                    if i == delta1_index:
                        ax.plot(timestamps, [max(-5, min(5, value)) for value in diff_data[i]],
                                color='blue', label=f'E{i:02}')
                    elif i == delta2_index:
                        ax.plot(timestamps, [max(-5, min(5, value)) for value in diff_data[i]],
                                color='red', label=f'E{i:02}')
                    elif i == delta3_index:
                        ax.plot(timestamps, [max(-5, min(5, value)) for value in diff_data[i]],
                                color='green', label=f'E{i:02}')
                    elif i == delta4_index:
                        ax.plot(timestamps, [max(-5, min(5, value)) for value in diff_data[i]],
                                color='orange', label=f'E{i:02}')
                    else:
                        ax.plot(timestamps, diff_data[i], color=full_colors[i], label=f'E{i:02}')
                ax.legend(loc='upper right', bbox_to_anchor = (1.1,1))
                ax.spines['top'].set_visible(True)
                ax.spines['right'].set_visible(True)
                ax.spines['bottom'].set_visible(True)
                ax.spines['left'].set_visible(True)
                ax.tick_params(axis='both', which='both', length=0, labelbottom=False, labelleft=False)
                fig.autofmt_xdate()
                fig.canvas.draw()
            else:
                canvas.itemconfig(delta1_text, text="NA")
                canvas.itemconfig(delta2_text, text="NA")
                canvas.itemconfig(delta3_text, text="NA")
                canvas.itemconfig(delta4_text, text="NA")
        except serial.SerialException as e:
            canvas.itemconfig(delta1_text, text=f"Error: {e}")
            canvas.itemconfig(delta2_text, text=f"Error: {e}")
            canvas.itemconfig(delta3_text, text=f"Error: {e}")
            canvas.itemconfig(delta4_text, text=f"Error: {e}")
            break
        except ValueError:
            canvas.itemconfig(delta1_text, text="NA")
        except IndexError:
            canvas.itemconfig(delta1_text, text="NA")

def update_display(canvas, counter1_text, counter2_text, counter3_text, counter4_text,
                   timer1_text, timer2_text, timer3_text, timer4_text):
    global delta1_timer, delta2_timer, delta3_timer, delta4_timer
    global delta1_counter, delta2_counter, delta3_counter, delta4_counter

    # For Delta 1:
    if delta1_touch_detected:
        delta1_timer = time.time() - delta1_start_time
    else:
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

def ask_electrode_indices():
    # Create the main window
    window = tk.Tk()
    window.title("SELECT ELECTRODE")
    window.geometry("400x200")  # Adjusted size to fit additional elements

    # Electrode selection for Object 1
    tk.Label(window, text="Select electrode number for Object 1:").pack()
    delta1_var = tk.StringVar()
    delta1_menu = ttk.Combobox(window, textvariable=delta1_var)
    delta1_menu['values'] = [f"E{str(i).zfill(2)}" for i in range(12)]
    delta1_menu.pack()

    # Electrode selection for Object 2
    tk.Label(window, text="Select electrode number for Object 2:").pack()
    delta2_var = tk.StringVar()
    delta2_menu = ttk.Combobox(window, textvariable=delta2_var)
    delta2_menu['values'] = [f"E{str(i).zfill(2)}" for i in range(12)]
    delta2_menu.pack()

    # Electrode selection for Object 3
    tk.Label(window, text="Select electrode number for Object 3:").pack()
    delta3_var = tk.StringVar()
    delta3_menu = ttk.Combobox(window, textvariable=delta3_var)
    delta3_menu['values'] = [f"E{str(i).zfill(2)}" for i in range(12)]
    delta3_menu.pack()

    # Electrode selection for Object 4
    tk.Label(window, text="Select electrode number for Object 4:").pack()
    delta4_var = tk.StringVar()
    delta4_menu = ttk.Combobox(window, textvariable=delta4_var)
    delta4_menu['values'] = [f"E{str(i).zfill(2)}" for i in range(12)]
    delta4_menu.pack()

    # Submit button logic
    def on_submit():
        delta1_index = int(delta1_var.get()[1:])
        delta2_index = int(delta2_var.get()[1:])
        delta3_index = int(delta3_var.get()[1:])
        delta4_index = int(delta4_var.get()[1:])

        print(f"Electrode Object 1: E{str(delta1_index).zfill(2)}")
        print(f"Electrode Object 2: E{str(delta2_index).zfill(2)}")
        print(f"Electrode Object 3: E{str(delta3_index).zfill(2)}")
        print(f"Electrode Object 4: E{str(delta4_index).zfill(2)}")

        # Close the window
        window.destroy()
        main(delta1_index, delta2_index, delta3_index, delta4_index)

    # Submit button
    tk.Button(window, text="Submit", command=on_submit).pack()

    # Run the Tkinter event loop
    window.mainloop()


def initialize_gui(delta1_index, delta2_index, delta3_index, delta4_index):
    root = tk.Tk()
    root.title("Serial Data Reader")

    # Create canvas for visuals
    canvas = tk.Canvas(root, width=1000, height=450)
    canvas.pack(padx=10, pady=10)

    circle1 = canvas.create_oval(25, 50, 225, 250, fill="blue", outline="dark blue")
    circle2 = canvas.create_oval(275, 50, 475, 250, fill="red", outline="dark red")
    circle3 = canvas.create_oval(525, 50, 725, 250, fill="green", outline="dark green")
    circle4 = canvas.create_oval(775, 50, 975, 250, fill="orange", outline="dark orange")

    # Delta text displays (these will be drawn on top of the images)
    delta1_text = canvas.create_text(125, 150, text="Delta 1: ", font=("Helvetica", 16))
    delta2_text = canvas.create_text(375, 150, text="Delta 2: ", font=("Helvetica", 16))
    delta3_text = canvas.create_text(625, 150, text="Delta 3: ", font=("Helvetica", 16))
    delta4_text = canvas.create_text(875, 150, text="Delta 4: ", font=("Helvetica", 16))

    ethovision_circle = canvas.create_oval(820, 5, 840, 25, fill="red", state="hidden")
    ethovision_text = canvas.create_text(925, 15, text="Ethovision Recording", font=("Helvetica", 12), state="hidden")

    # Counter and timer displays moved higher
    counter1_text = canvas.create_text(125, 275, text="O1 Count: 0", font=("Helvetica", 16))
    counter2_text = canvas.create_text(375, 275, text="O2 Count: 0", font=("Helvetica", 16))
    counter3_text = canvas.create_text(625, 275, text="O3 Count: 0", font=("Helvetica", 16))
    counter4_text = canvas.create_text(875, 275, text="O4 Count: 0", font=("Helvetica", 16))
    timer1_text = canvas.create_text(125, 300, text="O1 Timer: 0.00 sec", font=("Helvetica", 16))
    timer2_text = canvas.create_text(375, 300, text="O2 Timer: 0.00 sec", font=("Helvetica", 16))
    timer3_text = canvas.create_text(625, 300, text="O3 Timer: 0.00 sec", font=("Helvetica", 16))
    timer4_text = canvas.create_text(875, 300, text="O4 Timer: 0.00 sec", font=("Helvetica", 16))

    # --- Insert Button Frame between canvas and trial timer ---
    button_frame = tk.Frame(root)
    button_frame.pack(pady=2)

    resetButton = tk.Button(button_frame, text="Reset Baseline", command=send_reset_baseline)
    resetButton.pack(side=tk.LEFT, padx=5)

    # --- End Button Frame ---

    # Trial timer display
    timer_label = tk.Label(root, text="Trial Time: Not started", font=("Helvetica", 14))
    timer_label.pack(pady=2)

    # Graph setup
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.legend(loc='upper right', bbox_to_anchor=(1.1, 1))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.tick_params(axis='both', which='both', length=0, labelbottom=False, labelleft=False)

    # Embed the graph in Tkinter
    canvas_plot = FigureCanvasTkAgg(fig, master=root)
    canvas_plot.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    # Start serial reading
    graph_indices = [delta1_index, delta2_index, delta3_index, delta4_index]

    # Clear the axes and plot the new data
    ax.clear()

    update_display(canvas, counter1_text, counter2_text, counter3_text, counter4_text,
                   timer1_text, timer2_text, timer3_text, timer4_text)

    # Start serial thread
    threading.Thread(
        target=read_from_serial,
        args=(
            ser, canvas, delta1_text, delta2_text, delta3_text, delta4_text,
            circle1, circle2, circle3, circle4, ax, fig,
            counter1_text, counter2_text, counter3_text, counter4_text,
            timer1_text, timer2_text, timer3_text, timer4_text,
            delta1_index, delta2_index, delta3_index, delta4_index, graph_indices,
            ethovision_text, ethovision_circle, timer_label
        )
    ).start()

    return root

def save_data():
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if file_path:
        with open(file_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "Elapsed Time (s)", "Delta 1", "Object 1 Count", "Object 1 Timer", "Delta 2", "Object 2 Count", "Object 2 Timer"
                                , "Delta 3", "Object 3 Count", "Object 3 Timer", "Delta 4", "Object 4 Count", "Object 4 Timer"])
            while data_queue:
                writer.writerow(data_queue.popleft())
        print("Data saved successfully!")

def send_reset_baseline():
    global ser
    # Send the reset command with a newline terminator.
    ser.write("RESET.BASELINE\n".encode())
    print("Baseline reset command sent.")

def moving_average(buffer, new_value):
    buffer.append(new_value)
    if len(buffer) > BUFFER_SIZE:
        buffer.pop(0)
    return sum(buffer) / len(buffer)

def main(delta1_index=None, delta2_index=None, delta3_index=None, delta4_index=None):
    if delta1_index is None or delta2_index is None or delta3_index is None or delta4_index is None:
        ask_electrode_indices()
    else:
        global ser
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE)
        root = initialize_gui(delta1_index, delta2_index, delta3_index, delta4_index)
        root.mainloop()

if __name__ == "__main__":
    main()
"""

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
import os

SERIAL_PORT = 'COM22'
BAUD_RATE = 9600
DELTA_THRESHOLD1 = 10
BUFFER_SIZE = 3
BATCH_THRESHOLD = 600
TEMP_FILE = 'temp_data.csv'
DATA_POINTS = 40

diff_data = [collections.deque(maxlen=DATA_POINTS) for _ in range(12)]
timestamps = collections.deque(maxlen=DATA_POINTS)

delta1_counter = 0
delta2_counter = 0
delta3_counter = 0
delta4_counter = 0
delta1_timer = 0
delta2_timer = 0
delta3_timer = 0
delta4_timer = 0
delta1_time_correct = 0
delta2_time_correct = 0
delta3_time_correct = 0
delta4_time_correct = 0
delta1_start_time = None
delta2_start_time = None
delta3_start_time = None
delta4_start_time = None
delta1_touch_detected = False
delta2_touch_detected = False
delta3_touch_detected = False
delta4_touch_detected = False
ethovision_flag_start = False
ethovision_flag_curr = False

# Variables to store the latest Delta values and timestamp
latest_delta1 = 0.0
latest_delta2 = 0.0
latest_delta3 = 0.0
latest_delta4 = 0.0
latest_timestamp = ""
saving = False
save_thread = None
ser = None
data_queue = collections.deque()



def read_from_serial(ser, canvas, delta1_text, delta2_text, delta3_text, delta4_text, circle1, circle2, circle3, circle4, ax, fig,
                     counter1_text, counter2_text, counter3_text, counter4_text, timer1_text, timer2_text, timer3_text, timer4_text,
                     delta1_index, delta2_index, delta3_index, delta4_index, graph_indices, ethovision_text, ethovision_circle, timer_label):
    global delta1_counter, delta2_counter, delta3_counter, delta4_counter, delta1_timer, delta2_timer, delta3_timer, delta4_timer, delta1_start_time, delta2_start_time, delta3_start_time, delta4_start_time, \
        delta1_touch_detected, delta2_touch_detected, delta3_touch_detected, delta4_touch_detected, latest_delta1, latest_delta2, latest_delta3, latest_delta4, latest_timestamp, ethovision_flag_start, \
        ethovision_flag_curr, data_queue
    buffers = [collections.deque(maxlen=BUFFER_SIZE) for _ in range(13)]  # Updated to 13 buffers for 25 values
    while True:
        try:
            line = ser.readline().decode('utf-8').strip()
            values = list(map(float, line.split(',')))
            if len(values) == 25:

                ethovision_flag_start = int(values[24])

                deltas = []
                for i in range(0, 24, 2):
                    deltas.append(values[i] - values[i + 1])
                smoothed_deltas = [moving_average(buffers[i], deltas[i]) for i in range(12)]

                # Keep delta1 and delta2 uncapped
                delta1 = smoothed_deltas[delta1_index]
                delta2 = smoothed_deltas[delta2_index]
                delta3 = smoothed_deltas[delta3_index]
                delta4 = smoothed_deltas[delta4_index]

                # Update canvas text for deltas (uncapped)
                canvas.itemconfig(delta1_text, text=f"O1 (E{delta1_index:02}): {delta1:.2f}")
                canvas.itemconfig(delta2_text, text=f"O2 (E{delta2_index:02}): {delta2:.2f}")
                canvas.itemconfig(delta3_text, text=f"O3 (E{delta3_index:02}): {delta3:.2f}")
                canvas.itemconfig(delta4_text, text=f"O4 (E{delta4_index:02}): {delta4:.2f}")

                # Update latest delta values and timestamp
                latest_delta1 = round(delta1, 2)
                latest_delta2 = round(delta2, 2)
                latest_delta3 = round(delta3, 2)
                latest_delta4 = round(delta4, 2)
                latest_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if ethovision_flag_start == 1:
                    canvas.itemconfig(ethovision_circle, state='normal', fill='red', outline='dark red')
                    canvas.itemconfig(ethovision_text, state='normal', text="Ethovision Recording", fill='red')
                else:
                    canvas.itemconfig(ethovision_circle, state='hidden')
                    canvas.itemconfig(ethovision_text, state='hidden')


                # Touch detection for Delta 1
                if delta1 > DELTA_THRESHOLD1:
                    canvas.itemconfig(circle1, fill='dark blue', outline='blue')
                    canvas.itemconfig(delta1_text, text=f"O1 (E{delta1_index:02}): {delta1:.2f}", fill="white")
                    if not delta1_touch_detected:
                        delta1_touch_detected = True
                        delta1_counter += 1
                        delta1_start_time = time.time()
                elif delta1 <= DELTA_THRESHOLD1:
                    canvas.itemconfig(circle1, fill='blue', outline='dark blue')
                    canvas.itemconfig(delta1_text, text=f"O1 (E{delta1_index:02}): {delta1:.2f}", fill="black")
                    if delta1_touch_detected:
                        delta1_touch_detected = False

                # Touch detection for Delta 2
                if delta2 > DELTA_THRESHOLD1:
                    canvas.itemconfig(circle2, fill='dark red', outline='red')
                    canvas.itemconfig(delta2_text, text=f"O2 (E{delta2_index:02}): {delta2:.2f}", fill="white")
                    if not delta2_touch_detected:
                        delta2_touch_detected = True
                        delta2_counter += 1
                        delta2_start_time = time.time()
                elif delta2 <= DELTA_THRESHOLD1:
                    canvas.itemconfig(circle2, fill='red', outline='dark red')  # Revert to blue
                    canvas.itemconfig(delta2_text, text=f"O2 (E{delta2_index:02}): {delta2:.2f}", fill="black")
                    if delta2_touch_detected:
                        delta2_touch_detected = False

                # Touch detection for Delta 3
                if delta3 > DELTA_THRESHOLD1:
                    canvas.itemconfig(circle3, fill='dark green', outline='green')
                    canvas.itemconfig(delta3_text, text=f"O3 (E{delta3_index:02}): {delta3:.2f}", fill="white")
                    if not delta3_touch_detected:
                        delta3_touch_detected = True
                        delta3_counter += 1
                        delta3_start_time = time.time()
                elif delta3 <= DELTA_THRESHOLD1:
                    canvas.itemconfig(circle3, fill='green', outline='dark green')
                    canvas.itemconfig(delta3_text, text=f"O3 (E{delta3_index:02}): {delta3:.2f}", fill="black")
                    if delta3_touch_detected:
                        delta3_touch_detected = False

                # Touch detection for Delta 4
                if delta4 > DELTA_THRESHOLD1:
                    canvas.itemconfig(circle4, fill='dark orange', outline='orange')
                    canvas.itemconfig(delta4_text, text=f"O4 (E{delta4_index:02}): {delta4:.2f}", fill="white")
                    if not delta4_touch_detected:
                        delta4_touch_detected = True
                        delta4_counter += 1
                        delta4_start_time = time.time()
                elif delta4 <= DELTA_THRESHOLD1:
                    canvas.itemconfig(circle4, fill='orange', outline='dark orange')  # Revert to blue
                    canvas.itemconfig(delta4_text, text=f"O4 (E{delta4_index:02}): {delta4:.2f}", fill="black")
                    if delta4_touch_detected:
                        delta4_touch_detected = False

                def update_timer(timer_start):
                    local_root = timer_label.winfo_toplevel()  # Renamed to avoid shadowing 'root'
                    if not ethovision_flag_curr:
                        timer_label.config(text="Trial Time: Not Started")
                        return
                    elapsed_time = int(time.time() - timer_start)
                    minutes = elapsed_time // 60
                    seconds = elapsed_time % 60
                    timer_label.config(text=f"Trial Time: {minutes:02d}:{seconds:02d}")
                    local_root.after(1000, lambda: update_timer(timer_start))


                if ethovision_flag_start == 1 and ethovision_flag_curr is False:
                    ethovision_flag_curr = True
                    start_time = time.time()

                if ethovision_flag_start == 1:
                    new_data = [
                        latest_timestamp,
                        (time.time() - start_time),
                        latest_delta1,
                        delta1_counter,
                        delta1_timer,
                        latest_delta2,
                        delta2_counter,
                        delta2_timer,
                        latest_delta3,
                        delta3_counter,
                        delta3_timer,
                        latest_delta4,
                        delta4_counter,
                        delta4_timer
                    ]
                    add_to_data_queue(new_data)
                    update_timer(start_time)

                if ethovision_flag_start == 0 and ethovision_flag_curr is True:
                    ethovision_flag_curr = False
                    save_data()

                # Update the graph (capped deltas)
                timestamps.append(time.time())
                for i in range(12):
                    diff_data[i].append(smoothed_deltas[i])
                ax.clear()
                full_colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray',
                               'olive', 'cyan', 'magenta', 'black']
                for i in graph_indices:
                    if i == delta1_index:
                        ax.plot(timestamps, [max(-5, min(5, value)) for value in diff_data[i]],
                                color='blue', label=f'E{i:02}')
                    elif i == delta2_index:
                        ax.plot(timestamps, [max(-5, min(5, value)) for value in diff_data[i]],
                                color='red', label=f'E{i:02}')
                    elif i == delta3_index:
                        ax.plot(timestamps, [max(-5, min(5, value)) for value in diff_data[i]],
                                color='green', label=f'E{i:02}')
                    elif i == delta4_index:
                        ax.plot(timestamps, [max(-5, min(5, value)) for value in diff_data[i]],
                                color='orange', label=f'E{i:02}')
                    else:
                        ax.plot(timestamps, diff_data[i], color=full_colors[i], label=f'E{i:02}')
                ax.legend(loc='upper right', bbox_to_anchor = (1.1,1))
                ax.spines['top'].set_visible(True)
                ax.spines['right'].set_visible(True)
                ax.spines['bottom'].set_visible(True)
                ax.spines['left'].set_visible(True)
                ax.tick_params(axis='both', which='both', length=0, labelbottom=False, labelleft=True)
                fig.autofmt_xdate()
                fig.canvas.draw()
            else:
                canvas.itemconfig(delta1_text, text="NA")
                canvas.itemconfig(delta2_text, text="NA")
                canvas.itemconfig(delta3_text, text="NA")
                canvas.itemconfig(delta4_text, text="NA")
        except serial.SerialException as e:
            canvas.itemconfig(delta1_text, text=f"Error: {e}")
            canvas.itemconfig(delta2_text, text=f"Error: {e}")
            canvas.itemconfig(delta3_text, text=f"Error: {e}")
            canvas.itemconfig(delta4_text, text=f"Error: {e}")
            break
        except ValueError:
            canvas.itemconfig(delta1_text, text="NA")
        except IndexError:
            canvas.itemconfig(delta1_text, text="NA")

def update_display(canvas, counter1_text, counter2_text, counter3_text, counter4_text,
                   timer1_text, timer2_text, timer3_text, timer4_text):
    global delta1_timer, delta2_timer, delta3_timer, delta4_timer, delta1_time_correct, delta2_time_correct, delta3_time_correct, delta4_time_correct, delta1_counter, delta2_counter, delta3_counter, delta4_counter

    # For Delta 1:
    if delta1_touch_detected:
        delta1_timer = time.time() - delta1_start_time + delta1_time_correct
    else:
        delta1_timer = delta1_timer
        delta1_time_correct = delta1_timer

    # For Delta 2:
    if delta2_touch_detected:
        delta2_timer = time.time() - delta2_start_time + delta2_time_correct
    else:
        delta2_timer = delta2_timer
        delta2_time_correct = delta2_timer

    # For Delta 3:
    if delta3_touch_detected:
        delta3_timer = time.time() - delta3_start_time + delta3_time_correct
    else:
        delta3_timer = delta3_timer
        delta3_time_correct = delta3_timer

    # For Delta 4:
    if delta4_touch_detected:
        delta4_timer = time.time() - delta4_start_time + delta4_time_correct
    else:
        delta4_timer = delta4_timer
        delta4_time_correct = delta4_timer

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

def ask_electrode_indices():
    # Create the main window
    window = tk.Tk()
    window.title("SELECT ELECTRODE")
    window.geometry("400x200")  # Adjusted size to fit additional elements

    # Electrode selection for Object 1
    tk.Label(window, text="Select electrode number for Object 1:").pack()
    delta1_var = tk.StringVar()
    delta1_menu = ttk.Combobox(window, textvariable=delta1_var)
    delta1_menu['values'] = [f"E{str(i).zfill(2)}" for i in range(12)]
    delta1_menu.pack()

    # Electrode selection for Object 2
    tk.Label(window, text="Select electrode number for Object 2:").pack()
    delta2_var = tk.StringVar()
    delta2_menu = ttk.Combobox(window, textvariable=delta2_var)
    delta2_menu['values'] = [f"E{str(i).zfill(2)}" for i in range(12)]
    delta2_menu.pack()

    # Electrode selection for Object 3
    tk.Label(window, text="Select electrode number for Object 3:").pack()
    delta3_var = tk.StringVar()
    delta3_menu = ttk.Combobox(window, textvariable=delta3_var)
    delta3_menu['values'] = [f"E{str(i).zfill(2)}" for i in range(12)]
    delta3_menu.pack()

    # Electrode selection for Object 4
    tk.Label(window, text="Select electrode number for Object 4:").pack()
    delta4_var = tk.StringVar()
    delta4_menu = ttk.Combobox(window, textvariable=delta4_var)
    delta4_menu['values'] = [f"E{str(i).zfill(2)}" for i in range(12)]
    delta4_menu.pack()

    # Submit button logic
    def on_submit():
        delta1_index = int(delta1_var.get()[1:])
        delta2_index = int(delta2_var.get()[1:])
        delta3_index = int(delta3_var.get()[1:])
        delta4_index = int(delta4_var.get()[1:])

        print(f"Electrode Object 1: E{str(delta1_index).zfill(2)}")
        print(f"Electrode Object 2: E{str(delta2_index).zfill(2)}")
        print(f"Electrode Object 3: E{str(delta3_index).zfill(2)}")
        print(f"Electrode Object 4: E{str(delta4_index).zfill(2)}")

        # Close the window
        window.destroy()
        main(delta1_index, delta2_index, delta3_index, delta4_index)

    # Submit button
    tk.Button(window, text="Submit", command=on_submit).pack()

    # Run the Tkinter event loop
    window.mainloop()


def initialize_gui(delta1_index, delta2_index, delta3_index, delta4_index):
    root = tk.Tk()
    root.title("Serial Data Reader")

    # Create canvas for visuals
    canvas = tk.Canvas(root, width=1000, height=450)
    canvas.pack(padx=10, pady=10)

    circle1 = canvas.create_oval(25, 50, 225, 250, fill="blue", outline="dark blue")
    circle2 = canvas.create_oval(275, 50, 475, 250, fill="red", outline="dark red")
    circle3 = canvas.create_oval(525, 50, 725, 250, fill="green", outline="dark green")
    circle4 = canvas.create_oval(775, 50, 975, 250, fill="orange", outline="dark orange")

    # Delta text displays (these will be drawn on top of the images)
    delta1_text = canvas.create_text(125, 150, text="Delta 1: ", font=("Helvetica", 16))
    delta2_text = canvas.create_text(375, 150, text="Delta 2: ", font=("Helvetica", 16))
    delta3_text = canvas.create_text(625, 150, text="Delta 3: ", font=("Helvetica", 16))
    delta4_text = canvas.create_text(875, 150, text="Delta 4: ", font=("Helvetica", 16))

    ethovision_circle = canvas.create_oval(820, 5, 840, 25, fill="red", state="hidden")
    ethovision_text = canvas.create_text(925, 15, text="Ethovision Recording", font=("Helvetica", 12), state="hidden")

    # Counter and timer displays moved higher
    counter1_text = canvas.create_text(125, 275, text="O1 Count: 0", font=("Helvetica", 16))
    counter2_text = canvas.create_text(375, 275, text="O2 Count: 0", font=("Helvetica", 16))
    counter3_text = canvas.create_text(625, 275, text="O3 Count: 0", font=("Helvetica", 16))
    counter4_text = canvas.create_text(875, 275, text="O4 Count: 0", font=("Helvetica", 16))
    timer1_text = canvas.create_text(125, 300, text="O1 Timer: 0.00 sec", font=("Helvetica", 16))
    timer2_text = canvas.create_text(375, 300, text="O2 Timer: 0.00 sec", font=("Helvetica", 16))
    timer3_text = canvas.create_text(625, 300, text="O3 Timer: 0.00 sec", font=("Helvetica", 16))
    timer4_text = canvas.create_text(875, 300, text="O4 Timer: 0.00 sec", font=("Helvetica", 16))

    # --- Insert Button Frame between canvas and trial timer ---
    button_frame = tk.Frame(root)
    button_frame.pack(pady=2)

    resetButton = tk.Button(button_frame, text="Reset Baseline", command=send_reset_baseline)
    resetButton.pack(side=tk.LEFT, padx=5)

    # --- End Button Frame ---

    # Trial timer display
    timer_label = tk.Label(root, text="Trial Time: Not started", font=("Helvetica", 14))
    timer_label.pack(pady=2)

    # Graph setup
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.legend(loc='upper right', bbox_to_anchor=(1.1, 1))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.tick_params(axis='both', which='both', length=0, labelbottom=False, labelleft=True)

    # Embed the graph in Tkinter
    canvas_plot = FigureCanvasTkAgg(fig, master=root)
    canvas_plot.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    # Start serial reading
    graph_indices = [delta1_index, delta2_index, delta3_index, delta4_index]

    # Clear the axes and plot the new data
    ax.clear()

    update_display(canvas, counter1_text, counter2_text, counter3_text, counter4_text,
                   timer1_text, timer2_text, timer3_text, timer4_text)

    # Start serial thread
    threading.Thread(
        target=read_from_serial,
        args=(
            ser, canvas, delta1_text, delta2_text, delta3_text, delta4_text,
            circle1, circle2, circle3, circle4, ax, fig,
            counter1_text, counter2_text, counter3_text, counter4_text,
            timer1_text, timer2_text, timer3_text, timer4_text,
            delta1_index, delta2_index, delta3_index, delta4_index, graph_indices,
            ethovision_text, ethovision_circle, timer_label
        )
    ).start()

    return root
"""
def save_data_troubleshoot():
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if file_path:
        with open(file_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "Elapsed Time (s)", "Delta 1", "Object 1 Count", "Object 1 Timer", "Delta 2", "Object 2 Count", "Object 2 Timer"
                                , "Delta 3", "Object 3 Count", "Object 3 Timer", "Delta 4", "Object 4 Count", "Object 4 Timer"])
            while data_queue:
                writer.writerow(data_queue.popleft())
        print("Data saved successfully!")

        from tkinter import filedialog
"""
def save_data():
    # First, flush any residual data from memory to the temporary file.
    while data_queue:
        flush_data_batch_to_temp_file()  # This writes in batches until data_queue is empty

    # Ask the user where they’d like to save the final CSV:
    file_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv")]
    )
    if file_path:
        with open(file_path, mode="w", newline="") as out_file:
            writer = csv.writer(out_file)
            # Write CSV header:
            writer.writerow([
                "Timestamp", "Elapsed Time (s)", "Delta 1", "Object 1 Count", "Object 1 Timer",
                "Delta 2", "Object 2 Count", "Object 2 Timer", "Delta 3", "Object 3 Count",
                "Object 3 Timer", "Delta 4", "Object 4 Count", "Object 4 Timer"
            ])
            # Merge the temporary file’s data into the final file:
            if os.path.exists(TEMP_FILE):
                with open(TEMP_FILE, "r", newline="") as temp_file:
                    reader = csv.reader(temp_file)
                    for row in reader:
                        writer.writerow(row)
                # Optionally, remove the temporary file after merging.
                os.remove(TEMP_FILE)
        print("Data saved successfully!")

def send_reset_baseline():
    global ser
    # Send the reset command with a newline terminator.
    ser.write("RESET.BASELINE\n".encode())
    print("Baseline reset command sent.")

def moving_average(buffer, new_value):
    buffer.append(new_value)
    if len(buffer) > BUFFER_SIZE:
        buffer.pop(0)
    return sum(buffer) / len(buffer)

def flush_data_batch_to_temp_file():
    """Flush one batch worth of data from in-memory data_queue to a temporary file."""
    global data_queue
    with open(TEMP_FILE, "a", newline="") as temp_file:
        writer = csv.writer(temp_file)
        count = 0
        # Write out one batch (or flush everything, if fewer than threshold)
        while data_queue and count < BATCH_THRESHOLD:
            row = data_queue.popleft()
            writer.writerow(row)
            count += 1
    print("Flushed batch remaining data_queue length:", len(data_queue))
def add_to_data_queue(row):
    """Add a row to the data_queue, and flush to TEMP_FILE if the size exceeds threshold."""
    global data_queue
    data_queue.append(row)
    if len(data_queue) >= BATCH_THRESHOLD:
        flush_data_batch_to_temp_file()

def main(delta1_index=None, delta2_index=None, delta3_index=None, delta4_index=None):
    if delta1_index is None or delta2_index is None or delta3_index is None or delta4_index is None:
        ask_electrode_indices()
    else:
        global ser
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE)
        root = initialize_gui(delta1_index, delta2_index, delta3_index, delta4_index)
        root.mainloop()

if __name__ == "__main__":
    main()