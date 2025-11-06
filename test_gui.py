import tkinter as tk

root = tk.Tk()
root.title("Test")
root.geometry("300x200")
label = tk.Label(root, text="Hello!")
label.pack()
root.mainloop()
