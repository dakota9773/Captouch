import tkinter as tk
from tkinter import ttk

def ask_electrode_indices():
    # Create the main window
    window = tk.Tk()
    window.title("SELECT ELECTRODE")
    window.geometry("400x200")

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