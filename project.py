import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import pandas as pd
import os

# --- Configuration ---
FILE_NAME = 'student_data.csv'

# Globals
SUBJECTS = [] 
mark_entries = {} 

# --- Backend Logic ---
def load_data():
    if not os.path.exists(FILE_NAME):
        return pd.DataFrame()
    return pd.read_csv(FILE_NAME)

def save_data(df):
    df.to_csv(FILE_NAME, index=False)

def get_subjects_from_file():
    """Updates the global SUBJECTS list from the CSV headers."""
    global SUBJECTS
    if os.path.exists(FILE_NAME):
        df = pd.read_csv(FILE_NAME)
        all_cols = list(df.columns)
        standard_cols = ['Roll No', 'Name', 'Total', 'Percentage', 'Grade']
        SUBJECTS = [col for col in all_cols if col not in standard_cols]
    else:
        SUBJECTS = []

def calculate_grade(percentage):
    if percentage >= 90: return 'A'
    elif percentage >= 75: return 'B'
    elif percentage >= 60: return 'C'
    elif percentage >= 40: return 'D'
    else: return 'F'

def recalculate_all_scores(df):
    """Recalculates Total, Percentage, and Grade for the whole dataframe."""
    valid_subs = [s for s in SUBJECTS if s in df.columns]
    
    if not valid_subs:
        df['Total'] = 0
        df['Percentage'] = 0.0
        df['Grade'] = 'N/A'
    else:
        df['Total'] = df[valid_subs].sum(axis=1)
        max_score = len(valid_subs) * 100
        df['Percentage'] = round((df['Total'] / max_score) * 100, 2)
        df['Grade'] = df['Percentage'].apply(calculate_grade)
        
    return df

# --- HELPER: Case Insensitive Matcher ---
def find_subject_case_insensitive(user_input):
    """
    Returns the ACTUAL subject name from the global list 
    matching the user_input (ignoring case).
    Returns None if not found.
    """
    user_input_lower = user_input.lower().strip()
    for subject in SUBJECTS:
        if subject.lower() == user_input_lower:
            return subject # Return the existing formatted name
    return None

# --- Feature: Add Subject (Case Insensitive) ---
def add_new_subject_column():
    user_input = simpledialog.askstring("Add Subject", "Enter New Subject Name:")
    if not user_input: return 

    user_input = user_input.strip()
    
    # 1. Check if it exists (Ignoring Case)
    existing_name = find_subject_case_insensitive(user_input)
    
    if existing_name:
        messagebox.showerror("Error", f"Subject '{existing_name}' already exists!")
        return

    # 2. Format name to Title Case for better UI (e.g., "math" -> "Math")
    new_sub_name = user_input.title()

    df = load_data()
    
    if not df.empty:
        df[new_sub_name] = 0
        SUBJECTS.append(new_sub_name)
        df = recalculate_all_scores(df)
    else:
        SUBJECTS.append(new_sub_name)

    if not df.empty:
        cols = ['Roll No', 'Name'] + SUBJECTS + ['Total', 'Percentage', 'Grade']
        df = df[cols]
        save_data(df)
    
    setup_ui_inputs()
    refresh_treeview()
    messagebox.showinfo("Success", f"Subject '{new_sub_name}' added!")

# --- Feature: Remove Subject (Case Insensitive) ---
def remove_subject_column():
    if not SUBJECTS:
        messagebox.showwarning("Error", "No subjects to remove!")
        return

    sub_list_str = ", ".join(SUBJECTS)
    user_input = simpledialog.askstring("Remove Subject", f"Current Subjects: {sub_list_str}\n\nEnter name of subject to REMOVE:")

    if not user_input: return

    # 1. Find the ACTUAL name using the helper
    target_subject = find_subject_case_insensitive(user_input)

    if not target_subject:
        messagebox.showerror("Error", f"Subject '{user_input}' not found in list.")
        return

    confirm = messagebox.askyesno("Confirm", f"Are you sure you want to delete '{target_subject}'?\nThis will update all student records.")
    if not confirm: return

    # 2. Remove using the actual name
    SUBJECTS.remove(target_subject)

    df = load_data()
    if not df.empty:
        if target_subject in df.columns:
            df = df.drop(columns=[target_subject])
        
        df = recalculate_all_scores(df)
        save_data(df)

    setup_ui_inputs()
    refresh_treeview()
    messagebox.showinfo("Success", f"Subject '{target_subject}' removed.")

# --- Standard Functions ---
def add_student():
    roll = roll_entry.get()
    name = name_entry.get()
    
    if not roll or not name:
        messagebox.showerror("Input Error", "Roll No and Name are required.")
        return

    current_marks = {}
    
    try:
        for sub_name, entry_widget in mark_entries.items():
            val = int(entry_widget.get())
            current_marks[sub_name] = val
    except ValueError:
        messagebox.showerror("Input Error", "All subject marks must be numbers.")
        return

    df = load_data()
    if not df.empty and str(roll) in df['Roll No'].astype(str).values:
        messagebox.showerror("Error", "Roll Number already exists!")
        return

    new_data = {'Roll No': roll, 'Name': name}
    new_data.update(current_marks)
    
    new_row_df = pd.DataFrame([new_data])
    df = pd.concat([df, new_row_df], ignore_index=True)
    df = recalculate_all_scores(df)
    
    save_data(df)
    refresh_treeview()
    clear_inputs()
    messagebox.showinfo("Success", "Student Added Successfully")

def delete_student():
    selected = tree.focus()
    if not selected: return
    val = tree.item(selected, 'values')
    roll = val[0]
    df = load_data()
    df = df[df['Roll No'].astype(str) != str(roll)]
    save_data(df)
    refresh_treeview()

def clear_inputs():
    roll_entry.delete(0, tk.END)
    name_entry.delete(0, tk.END)
    for entry in mark_entries.values():
        entry.delete(0, tk.END)

def setup_ui_inputs():
    for widget in frame_dynamic.winfo_children():
        widget.destroy()
    mark_entries.clear()
    row_val = 0
    col_val = 0
    for subject in SUBJECTS:
        tk.Label(frame_dynamic, text=f"{subject}:", fg="blue").grid(row=row_val, column=col_val, padx=5, pady=5)
        ent = tk.Entry(frame_dynamic, width=10)
        ent.grid(row=row_val, column=col_val+1, padx=5, pady=5)
        mark_entries[subject] = ent
        col_val += 2
        if col_val >= 8:
            col_val = 0
            row_val += 1

def refresh_treeview():
    tree.delete(*tree.get_children())
    cols = ['Roll No', 'Name'] + SUBJECTS + ['Total', 'Percentage', 'Grade']
    tree['columns'] = cols
    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=80, anchor='center')
    df = load_data()
    if df.empty: return
    for sub in SUBJECTS:
        if sub not in df.columns: df[sub] = 0
    if 'Total' not in df.columns: df['Total'] = 0
    if 'Percentage' not in df.columns: df['Percentage'] = 0
    if 'Grade' not in df.columns: df['Grade'] = 'N/A'
    df = df[cols] 
    for _, row in df.iterrows():
        tree.insert("", tk.END, values=list(row))

def initial_check():
    if not os.path.exists(FILE_NAME):
        df = pd.DataFrame(columns=['Roll No', 'Name', 'Total', 'Percentage', 'Grade'])
        df.to_csv(FILE_NAME, index=False)
    get_subjects_from_file()

# --- Main Application ---
root = tk.Tk()
root.title("Student Record (Smart Case Handling)")
root.geometry("950x600")

initial_check() 

frame_top = tk.Frame(root, bd=2, relief=tk.GROOVE)
frame_top.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

tk.Label(frame_top, text="Roll No:").pack(side=tk.LEFT, padx=5)
roll_entry = tk.Entry(frame_top, width=15)
roll_entry.pack(side=tk.LEFT, padx=5)

tk.Label(frame_top, text="Name:").pack(side=tk.LEFT, padx=5)
name_entry = tk.Entry(frame_top, width=20)
name_entry.pack(side=tk.LEFT, padx=5)

tk.Button(frame_top, text="- Remove Subject", command=remove_subject_column, bg="#E91E63", fg="white").pack(side=tk.RIGHT, padx=5)
tk.Button(frame_top, text="+ Add Subject", command=add_new_subject_column, bg="#FF9800", fg="white").pack(side=tk.RIGHT, padx=5)

frame_dynamic = tk.Frame(root, bd=2, relief=tk.SUNKEN, bg="#f9f9f9")
frame_dynamic.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

frame_btn = tk.Frame(root)
frame_btn.pack(pady=5)
tk.Button(frame_btn, text="Save Record", command=add_student, bg="green", fg="white", width=15).grid(row=0, column=0, padx=5)
tk.Button(frame_btn, text="Delete Student", command=delete_student, bg="red", fg="white", width=15).grid(row=0, column=1, padx=5)
tk.Button(frame_btn, text="Clear Fields", command=clear_inputs, width=15).grid(row=0, column=2, padx=5)

tree_frame = tk.Frame(root)
tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
tree_scroll = ttk.Scrollbar(tree_frame)
tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
tree = ttk.Treeview(tree_frame, show='headings', yscrollcommand=tree_scroll.set)
tree_scroll.config(command=tree.yview)
tree.pack(fill=tk.BOTH, expand=True)

setup_ui_inputs() 
refresh_treeview() 

root.mainloop()