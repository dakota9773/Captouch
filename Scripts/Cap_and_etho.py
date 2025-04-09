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
delta1_timer = 0
delta2_timer = 0
delta1_start_time = None
delta2_start_time = None
delta1_touch_detected = False
delta2_touch_detected = False
ethovision_flag_start = False
ethovision_flag_curr = False

# Variables to store the latest Delta values and timestamp
latest_delta1 = 0.0
latest_delta2 = 0.0
latest_timestamp = ""
saving = False
save_thread = None
data_queue = collections.deque()

def moving_average(buffer, new_value):
    buffer.append(new_value)
    if len(buffer) > BUFFER_SIZE:
        buffer.pop(0)
    return sum(buffer) / len(buffer)

def read_from_serial(ser, canvas, delta1_text, delta2_text, circle1, circle2,
                     ax, fig, counter1_text, counter2_text, timer1_text,
                     timer2_text, delta1_index, delta2_index, graph_indices,
                     ethovision_text, ethovision_circle, timer_label):
    global delta1_counter, delta2_counter, delta1_timer, delta2_timer, delta1_start_time, delta2_start_time, \
        delta1_touch_detected, delta2_touch_detected, latest_delta1, latest_delta2, latest_timestamp, ethovision_flag_start,\
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

                # Update canvas text for deltas (uncapped)
                canvas.itemconfig(delta1_text, text=f"O1 Delta (E{delta1_index:02}): {delta1:.2f}")
                canvas.itemconfig(delta2_text, text=f"O2 Delta (E{delta2_index:02}): {delta2:.2f}")

                # Update latest delta values and timestamp
                latest_delta1 = round(delta1, 2)
                latest_delta2 = round(delta2, 2)
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
                    canvas.itemconfig(delta1_text, text=f"O1 Delta (E{delta1_index:02}): {delta1:.2f}")
                    if not delta1_touch_detected:
                        delta1_touch_detected = True
                        delta1_counter += 1
                        delta1_start_time = time.time()
                elif delta1 <= DELTA_THRESHOLD1:
                    canvas.itemconfig(circle1, fill='blue', outline='dark blue')
                    canvas.itemconfig(delta1_text, text=f"O1 Delta (E{delta1_index:02}): {delta1:.2f}")
                    if delta1_touch_detected:
                        delta1_touch_detected = False
                        delta1_timer += time.time() - delta1_start_time

                # Touch detection for Delta 2
                if delta2 > DELTA_THRESHOLD1:
                    canvas.itemconfig(circle2, fill='dark red', outline='red')
                    canvas.itemconfig(delta2_text, text=f"O2 Delta (E{delta2_index:02}): {delta2:.2f}")
                    if not delta2_touch_detected:
                        delta2_touch_detected = True
                        delta2_counter += 1
                        delta2_start_time = time.time()
                elif delta2 <= DELTA_THRESHOLD1:
                    canvas.itemconfig(circle2, fill='red', outline='dark red')  # Revert to blue
                    canvas.itemconfig(delta2_text, text=f"O2 Delta (E{delta2_index:02}): {delta2:.2f}")
                    if delta2_touch_detected:
                        delta2_touch_detected = False
                        delta2_timer += time.time() - delta2_start_time

                def update_timer(timer_start):
                    root = timer_label.winfo_toplevel()
                    if not ethovision_flag_curr:
                        timer_label.config(text="Trial Time: Not Started")
                        return
                    elapsed_time = int(time.time() - timer_start)  # Calculate elapsed time
                    minutes = elapsed_time // 60
                    seconds = elapsed_time % 60
                    timer_label.config(text=f"Trial Time: {minutes:02d}:{seconds:02d}")
                    root.after(1000, lambda: update_timer(timer_start))


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
                        delta2_timer
                    ])
                    update_timer(start_time)

                if ethovision_flag_start == 0 and ethovision_flag_curr is True:
                    ethovision_flag_curr = False
                    save_data()

                # Update the counters and timers on the canvas
                canvas.itemconfig(counter1_text, text=f"O1 Count: {delta1_counter}")
                canvas.itemconfig(counter2_text, text=f"O2 Count: {delta2_counter}")
                canvas.itemconfig(timer1_text, text=f"O1 Timer: {delta1_timer:.2f} sec")
                canvas.itemconfig(timer2_text, text=f"O2 Timer: {delta2_timer:.2f} sec")

                # Update the graph (capped deltas)
                timestamps.append(time.time())
                for i in range(12):
                    diff_data[i].append(smoothed_deltas[i])
                ax.clear()
                full_colors = ['blue', 'red', 'green', 'red', 'purple', 'brown', 'pink', 'gray',
                               'olive', 'cyan', 'magenta', 'black']
                for i in graph_indices:
                    if i == delta1_index:
                        ax.plot(timestamps, [max(-25, min(25, value)) for value in diff_data[i]],
                                color='blue', label=f'E{i:02}')
                    elif i == delta2_index:
                        ax.plot(timestamps, [max(-25, min(25, value)) for value in diff_data[i]],
                                color='red', label=f'E{i:02}')
                    else:
                        ax.plot(timestamps, diff_data[i], color=full_colors[i], label=f'E{i:02}')
                ax.legend(loc='upper right')
                ax.set_title("Deltas over Time")
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['bottom'].set_visible(False)
                ax.spines['left'].set_visible(True)
                ax.tick_params(axis='both', which='both', length=0, labelbottom=False, labelleft=False)
                fig.autofmt_xdate()
                fig.canvas.draw()
            else:
                canvas.itemconfig(delta1_text, text="Invalid data format")
                canvas.itemconfig(delta2_text, text="Invalid data format")
        except serial.SerialException as e:
            canvas.itemconfig(delta1_text, text=f"Error: {e}")
            canvas.itemconfig(delta2_text, text=f"Error: {e}")
            break
        except ValueError:
            canvas.itemconfig(delta1_text, text="Invalid data values")
        except IndexError:
            canvas.itemconfig(delta1_text, text="Index error occurred")

def start_serial_reading(canvas, delta1_text, delta2_text, circle1, circle2, ax, fig, counter1_text, counter2_text, timer1_text, timer2_text, delta1_index, delta2_index, graph_indices):
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE)
        thread = threading.Thread(target=read_from_serial, args=(ser, canvas, delta1_text, delta2_text, circle1, circle2, ax, fig, counter1_text, counter2_text, timer1_text, timer2_text, delta1_index, delta2_index, graph_indices))
        thread.daemon = True
        thread.start()
    except serial.SerialException as e:
        canvas.itemconfig(delta1_text, text=f"Error: {e}")
        canvas.itemconfig(delta2_text, text=f"Error: {e}")

def ask_electrode_indices():
    # Create the main window
    window = tk.Tk()
    window.title("SELECT ELECTRODE")
    window.geometry("400x150")

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

    # Submit button logic
    def on_submit():
        delta1_index = int(delta1_var.get()[1:])
        delta2_index = int(delta2_var.get()[1:])

        print(f"Electrode Object 1: E{str(delta1_index).zfill(2)}")
        print(f"Electrode Object 2: E{str(delta2_index).zfill(2)}")

        # Close the window
        window.destroy()
        main(delta1_index, delta2_index)

    # Submit button
    tk.Button(window, text="Submit", command=on_submit).pack()

    # Run the Tkinter event loop
    window.mainloop()

def initialize_gui(delta1_index, delta2_index):
    root = tk.Tk()
    root.title("Serial Data Reader")

    # Create canvas for visuals
    canvas = tk.Canvas(root, width=1000, height=450)
    canvas.pack(padx=10, pady=10)

    circle1 = canvas.create_oval(200, 50, 450, 300, fill="blue", outline="dark blue")
    circle2 = canvas.create_oval(550, 50, 800, 300, fill="red", outline="dark red")


    # Delta text displays (these will be drawn on top of the images)
    delta1_text = canvas.create_text(325, 175, text="Delta 1: ", font=("Helvetica", 16))
    delta2_text = canvas.create_text(675, 175, text="Delta 2: ", font=("Helvetica", 16))

    ethovision_circle = canvas.create_oval(820, 5, 840, 25, fill="red", state = "hidden")
    ethovision_text = canvas.create_text(925, 15, text="Ethovision Recording", font=("Helvetica", 12), state = "hidden")


    # Counter and timer displays moved higher
    counter1_text = canvas.create_text(325, 325, text="O1 Count: 0", font=("Helvetica", 16))
    counter2_text = canvas.create_text(675, 325, text="O2 Count: 0", font=("Helvetica", 16))
    timer1_text = canvas.create_text(325, 375, text="O1 Timer: 0.00 sec", font=("Helvetica", 16))
    timer2_text = canvas.create_text(675, 375, text="O2 Timer: 0.00 sec", font=("Helvetica", 16))

    # Trial timer display
    timer_label = tk.Label(root, text="Trial Time: Not started", font=("Helvetica", 14))
    timer_label.pack(pady=5)

    # Graph setup
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.set_title("Deltas over Time")
    ax.legend(loc='upper right')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.tick_params(axis='both', which='both', length=0, labelbottom=False, labelleft=False)

    # Embed the graph in Tkinter
    canvas_plot = FigureCanvasTkAgg(fig, master=root)
    canvas_plot.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    # Start serial reading
    graph_indices = [delta1_index, delta2_index]

    # Clear the axes and plot the new data
    ax.clear()
    for i in graph_indices:
        # Clamp data before plotting
        clamped_data = [min(100, max(-100, value)) for value in diff_data[i]]
        ax.plot(timestamps, clamped_data, label=f'E{i:02}')

    # Keep the graph clean and readable
    ax.set_title("Deltas over Time")
    ax.legend(loc='upper right')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.tick_params(axis='both', which='both', length=0, labelbottom=False, labelleft=False)

    fig.canvas.draw()

    # Start serial thread
    threading.Thread(
        target=read_from_serial,
        args=(
            serial.Serial(SERIAL_PORT, BAUD_RATE),
            canvas, delta1_text, delta2_text, circle1, circle2, ax, fig,
            counter1_text, counter2_text, timer1_text, timer2_text,
            delta1_index, delta2_index, graph_indices,
            ethovision_text, ethovision_circle, timer_label
        )
    ).start()

    return root

def save_data():
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if file_path:
        with open(file_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "Elapsed Time (s)", "Delta 1", "Object 1 Count", "Object 1 Timer", "Delta 2", "Object 2 Count", "Object 2 Timer"])
            while data_queue:
                writer.writerow(data_queue.popleft())
        print("Data saved successfully!")

def main(delta1_index=None, delta2_index=None):
    if delta1_index is None or delta2_index is None:
        ask_electrode_indices()
    else:
        root = initialize_gui(delta1_index, delta2_index)
        root.mainloop()

if __name__ == "__main__":
    main()