from tkinter import filedialog
import csv


def moving_average(buffer, new_value):
    # Code to smooth data using a moving average. Need to set "BUFFER_SIZE"
    buffer.append(new_value)
    if len(buffer) > BUFFER_SIZE:
        buffer.pop(0)
    return sum(buffer) / len(buffer)

def send_reset_baseline():
    global ser
    # Write to serial to reset baseline values, need to define "ser"
    ser.write("RESET.BASELINE\n".encode())
    print("Baseline reset command sent.")

def save_data():
    # Function to save a .csv file when called
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if file_path:
        with open(file_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "Elapsed Time (s)", "Delta 1", "Object 1 Count", "Object 1 Timer", "Delta 2", "Object 2 Count", "Object 2 Timer"
                                , "Delta 3", "Object 3 Count", "Object 3 Timer", "Delta 4", "Object 4 Count", "Object 4 Timer"])
            while data_queue:
                writer.writerow(data_queue.popleft())
        print("Data saved successfully!")