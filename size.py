import tkinter as tk

def on_resize(event):
    width = event.width
    height = event.height
    print(f"Window size: {width}x{height}")

def main():
    root = tk.Tk()
    root.title("Window Size Example")
    root.geometry("600x400")  # starting size

    # Bind the resize event
    root.bind("<Configure>", on_resize)

    root.mainloop()

if __name__ == "__main__":
    main()
