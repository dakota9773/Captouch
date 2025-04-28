import tkinter as tk
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def initialize_gui(delta1_index, delta2_index, delta3_index, delta4_index):
    root = tk.Tk()
    root.title("CapTouch 3.0")

# Create canvas for visuals
    canvas = tk.Canvas(root, width=1000, height=450)
    canvas.pack(padx=10, pady=10)

    circle1 = canvas.create_oval(25, 50, 225, 250, fill="blue", outline="dark blue")
    circle2 = canvas.create_oval(275, 50, 475, 250, fill="red", outline="dark red")
    circle3 = canvas.create_oval(525, 50, 725, 250, fill="green", outline="dark green")
    circle4 = canvas.create_oval(775, 50, 975, 250, fill="orange", outline="dark orange")


    delta1_text = canvas.create_text(125, 150, text="Delta 1: ", font=("Helvetica", 16))
    delta2_text = canvas.create_text(375, 150, text="Delta 2: ", font=("Helvetica", 16))
    delta3_text = canvas.create_text(625, 150, text="Delta 3: ", font=("Helvetica", 16))
    delta4_text = canvas.create_text(875, 150, text="Delta 4: ", font=("Helvetica", 16))

    ethovision_circle = canvas.create_oval(820, 5, 840, 25, fill="red", state="hidden")
    ethovision_text = canvas.create_text(925, 15, text="Ethovision Recording", font=("Helvetica", 12), state="hidden")

    counter1_text = canvas.create_text(125, 275, text="O1 Count: 0", font=("Helvetica", 16))
    counter2_text = canvas.create_text(375, 275, text="O2 Count: 0", font=("Helvetica", 16))
    counter3_text = canvas.create_text(625, 275, text="O3 Count: 0", font=("Helvetica", 16))
    counter4_text = canvas.create_text(875, 275, text="O4 Count: 0", font=("Helvetica", 16))
    timer1_text = canvas.create_text(125, 300, text="O1 Timer: 0.00 sec", font=("Helvetica", 16))
    timer2_text = canvas.create_text(375, 300, text="O2 Timer: 0.00 sec", font=("Helvetica", 16))
    timer3_text = canvas.create_text(625, 300, text="O3 Timer: 0.00 sec", font=("Helvetica", 16))
    timer4_text = canvas.create_text(875, 300, text="O4 Timer: 0.00 sec", font=("Helvetica", 16))

# Frame for buttons
    button_frame = tk.Frame(root)
    button_frame.pack(pady=2)

    resetButton = tk.Button(button_frame, text="Reset Baseline", command=send_reset_baseline)
    resetButton.pack(side=tk.LEFT, padx=5)

# Frame for timer display

    timer_label = tk.Label(root, text="Trial Time: Not started", font=("Helvetica", 14))
    timer_label.pack(pady=2)

# Graph setup
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.legend(loc='upper right', bbox_to_anchor=(1.1, 1))
    ax.spines['top'].set_visible(True)
    ax.spines['right'].set_visible(True)
    ax.spines['bottom'].set_visible(True)
    ax.spines['left'].set_visible(True)
    ax.tick_params(axis='both', which='both', length=0, labelbottom=False, labelleft=False)

    canvas_plot = FigureCanvasTkAgg(fig, master=root)
    canvas_plot.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

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
