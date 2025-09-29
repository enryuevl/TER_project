import customtkinter as ctk

# Create the main window
root = ctk.CTk()
root.title("Tabview Test - Tabs on Upper Left")
root.geometry("500x300")

# Create a Tabview with tabs aligned top-left
tabview = ctk.CTkTabview(
    master=root,
    width=400,
    height=250,
    anchor="w"   # "w" = west (left side) alignment
)
tabview.pack(padx=20, pady=20, fill="both", expand=True)

# Add tabs
tabview.add("Home")
tabview.add("Settings")
tabview.add("About")

# Place widgets inside tabs
ctk.CTkLabel(tabview.tab("Home"), text="Welcome to the Home Tab!", font=("Arial", 14)).pack(pady=20)
ctk.CTkLabel(tabview.tab("Settings"), text="Adjust your preferences here.", font=("Arial", 14)).pack(pady=20)
ctk.CTkLabel(tabview.tab("About"), text="TabView Demo\nTabs aligned to the left.", font=("Arial", 14)).pack(pady=20)

# Run the app
root.mainloop()
