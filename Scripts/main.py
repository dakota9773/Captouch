import tkinter as tk
from tkinter import Canvas, ttk, simpledialog, filedialog
import serial
import threading
import collections
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time
import csv
import datetime

# Your existing constants and global variables here

SERIAL_PORT = 'COM22'
BAUD_RATE = 9600
DELTA_THRESHOLD1 = 10
BUFFER_SIZE = 5
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

def read_from_serial(ser, canvas, delta1_text, delta2_text, circle1, circle2, ax, fig, counter1_text, counter2_text, timer1_text, timer2_text, delta1_index, delta2_index, graph_indices):
    global delta1_counter, delta2_counter, delta1_timer, delta2_timer, delta1_start_time, delta2_start_time
    global delta1_touch_detected, delta2_touch_detected, latest_delta1, latest_delta2, latest_timestamp

    buffers = [collections.deque(maxlen=BUFFER_SIZE) for _ in range(13)]  # Updated to 13 buffers for 25 values
    while True:
        try:
            line = ser.readline().decode('utf-8').strip()
            values = list(map(float, line.split(',')))
            if len(values) == 24:  # Check for 24 values (updated to remove Etho_recording)
                # Calculate deltas
                deltas = []
                for i in range(0, 24, 2):
                    deltas.append(values[i] - values[i + 1])
                smoothed_deltas = [moving_average(buffers[i], deltas[i]) for i in range(12)]

                # Keep delta1 and delta2 uncapped
                delta1 = smoothed_deltas[delta1_index]
                delta2 = smoothed_deltas[delta2_index]

                # Cap delta1 and delta2 values for graphing
                delta1cap = max(-25, min(25, delta1))
                delta2cap = max(-25, min(25, delta2))

                # Update canvas text for deltas (uncapped)
                canvas.itemconfig(delta1_text, text=f"O1 Delta (E{delta1_index:02}): {delta1:.2f}")
                canvas.itemconfig(delta2_text, text=f"O2 Delta (E{delta2_index:02}): {delta2:.2f}")

                # Update latest delta values and timestamp
                latest_delta1 = round(delta1, 2)
                latest_delta2 = round(delta2, 2)
                latest_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Touch detection for Delta 1 (uncapped)
                if delta1 > DELTA_THRESHOLD1:
                    canvas.itemconfig(circle1, fill='green', outline='dark green')
                    if not delta1_touch_detected:
                        delta1_touch_detected = True
                        delta1_counter += 1
                        delta1_start_time = time.time()
                elif delta1 <= DELTA_THRESHOLD1:
                    canvas.itemconfig(circle1, fill='blue', outline='dark blue')
                    if delta1_touch_detected:
                        delta1_touch_detected = False
                        delta1_timer += time.time() - delta1_start_time

                # Touch detection for Delta 2 (uncapped)
                if delta2 > DELTA_THRESHOLD1:
                    canvas.itemconfig(circle2, fill='green', outline='dark green')
                    if not delta2_touch_detected:
                        delta2_touch_detected = True
                        delta2_counter += 1
                        delta2_start_time = time.time()
                elif delta2 <= DELTA_THRESHOLD1:
                    canvas.itemconfig(circle2, fill='orange', outline='dark orange')
                    if delta2_touch_detected:
                        delta2_touch_detected = False
                        delta2_timer += time.time() - delta2_start_time

                # Update the counters and timers on the canvas
                canvas.itemconfig(counter1_text, text=f"Object 1 Count: {delta1_counter}")
                canvas.itemconfig(counter2_text, text=f"Object 2 Count: {delta2_counter}")
                canvas.itemconfig(timer1_text, text=f"Object 1 Timer: {delta1_timer:.2f} sec")
                canvas.itemconfig(timer2_text, text=f"Object 2 Timer: {delta2_timer:.2f} sec")

                # Update the graph (capped deltas)
                timestamps.append(time.time())
                for i in range(12):
                    diff_data[i].append(smoothed_deltas[i])
                ax.clear()
                full_colors = ['blue', 'orange', 'green', 'red', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan', 'magenta', 'black']
                color_map = {delta1_index: 'blue', delta2_index: 'orange'}
                for i in graph_indices:
                    if i == delta1_index:
                        ax.plot(timestamps, [max(-25, min(25, value)) for value in diff_data[i]], color='blue', label=f'E{i:02}')
                    elif i == delta2_index:
                        ax.plot(timestamps, [max(-25, min(25, value)) for value in diff_data[i]], color='orange', label=f'E{i:02}')
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
    canvas = Canvas(root, width=1000, height=450)
    canvas.pack(padx=10, pady=10)

    # Circles for touch indicators
    circle1 = canvas.create_oval(200, 50, 450, 300, outline="dark blue", width=2, fill="blue")
    circle2 = canvas.create_oval(550, 50, 800, 300, outline="dark orange", width=2, fill="orange")

    # Delta text displays
    delta1_text = canvas.create_text(325, 175, text="Delta 1: ", font=("Helvetica", 16))
    delta2_text = canvas.create_text(675, 175, text="Delta 2: ", font=("Helvetica", 16))

    # Counter and timer displays moved higher
    counter1_text = canvas.create_text(325, 325, text="Object 1 Count: 0", font=("Helvetica", 16))
    counter2_text = canvas.create_text(675, 325, text="Object 2 Count: 0", font=("Helvetica", 16))
    timer1_text = canvas.create_text(325, 375, text="Object 1 Timer: 0.00 sec", font=("Helvetica", 16))
    timer2_text = canvas.create_text(675, 375, text="Object 2 Timer: 0.00 sec", font=("Helvetica", 16))

    # Trial time input
    tk.Label(root, text="Enter Trial Time (Minutes):").pack(pady=5)
    trial_time_var = tk.StringVar()
    trial_time_entry = tk.Entry(root, textvariable=trial_time_var, width=10)
    trial_time_entry.pack()

    # Start trial button logic
    def start_trial():
        try:
            trial_time = int(trial_time_var.get()) * 60  # Convert minutes to seconds
        except ValueError:
            tk.messagebox.showerror("Input Error", "Please enter a valid number for trial time!")
            return

        def countdown_timer():
            nonlocal trial_time
            while trial_time > 0:
                timer_label.config(text=f"Time Remaining: {trial_time // 60}:{trial_time % 60:02d}")
                root.update()
                time.sleep(1)
                trial_time -= 1

            timer_label.config(text="Trial Completed!")
            save_data()

        threading.Thread(target=countdown_timer).start()

    # Trial timer display
    timer_label = tk.Label(root, text="Time Remaining: Not started", font=("Helvetica", 14))
    timer_label.pack(pady=5)

    # Start trial button
    tk.Button(root, text="Start Trial", command=start_trial, font=("Helvetica", 12), bg="green", fg="white").pack(pady=5)

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