# Panda's Cool Timer for Friendly Friends :>
# Copyright (c) 2025 PandaHo Phinfoshly
#
# This software is released under the MIT License.
# See the LICENSE file for more details.


# Panda's Timer Desktop.

import sys
import configparser
import tkinter as tk
import random
import json
import math
from tkinter import messagebox, filedialog, colorchooser
from tkinter import font as tkFont
from tkinter.scrolledtext import ScrolledText
from just_playback import Playback
from datetime import datetime, timedelta
import os

class Tooltip:
    """
    Creates a tooltip (pop-up) for a given widget.
    """
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.text:
            return

        # Use the mouse's screen position from the event
        x = self.widget.winfo_pointerx() + 15
        y = self.widget.winfo_pointery() + 10

        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        label = tk.Label(self.tooltip_window, text=self.text, justify='left',
                         background="#2e2e2e", fg="white", relief='solid', borderwidth=1,
                         font=("tahoma", "8", "normal"), wraplength=164)
        label.pack(ipadx=1)

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None

class Note:
    """Represents a single note with its properties."""
    def __init__(self, title="Untitled", description="", completion_type="Plain Text", completion_data=None):
        self.id = datetime.now().strftime("%Y%m%d%H%M%S%f") # Unique ID based on creation time
        self.title = title
        # Description with font formatting
        self.description_text = description
        self.description_tags = []

        # Completion Type: "Plain Text", "Checkboxes", or "Digits/Full Digits"
        self.completion_type = completion_type

        if completion_data is not None:
            self.completion_data = completion_data
        else:
            if self.completion_type == "Checkboxes":
                self.completion_data = False
            elif self.completion_type == "Digits/Full Digits":
                self.completion_data = [0, 0, 10] # [current, min, max]
            else:
                self.completion_data = None

    def to_dict(self):
        """Converts the Note object to a dictionary for saving to a file."""
        return {
            'id': self.id,
            'title': self.title,
            'description_text': self.description_text,
            'description_tags': self.description_tags,
            'completion_type': self.completion_type,
            'completion_data': self.completion_data,
        }

    @classmethod
    def from_dict(cls, data):
        """Creates a Note object from a dictionary (loaded from a file)."""
        note = cls(
            title=data.get('title', 'Untitled'),
            description=data.get('description_text', ''),
            completion_type=data.get('completion_type', 'Plain Text'),
            completion_data=data.get('completion_data')
        )
        note.id = data.get('id', datetime.now().strftime("%Y%m%d%H%M%S%f"))
        note.description_tags = data.get('description_tags', [])
        return note

    def __repr__(self):
        return f"<Note: {self.title}>"




class TimerSwitcher(tk.Frame):
    def __init__(self, master, switch_callback):
        super().__init__(master, bg="#1e1e1e")
        self.switch_callback = switch_callback
        self.current_timer = 0
        self.timer_titles = [f"Timer {i + 1}" for i in range(8)]

        btn_style = {"bg": "#2e2e2e", "fg": "white", "activebackground": "#008B8B", "activeforeground": "white",
                     "relief": "flat"}
        self.left_btn = tk.Button(self, text="<", command=self.prev_timer, width=3, **btn_style)
        self.left_btn.grid(row=0, column=0, padx=(10, 5), pady=5)

        self.timer_id_label = tk.Label(self, text="Timer 1", font=("Helvetica", 12), fg="white", bg="#1e1e1e")
        self.timer_id_label.grid(row=0, column=1)

        self.right_btn = tk.Button(self, text=">", command=self.next_timer, width=3, **btn_style)
        self.right_btn.grid(row=0, column=2, padx=(5, 10), pady=5)

        self.title_var = tk.StringVar(value=self.timer_titles[self.current_timer])
        self.title_entry = tk.Entry(self, textvariable=self.title_var, font=("Helvetica", 12), width=25,
                                    justify="center",
                                    bg="#2e2e2e", fg="white", relief="flat", insertbackground="white",
                                    highlightthickness=1, highlightbackground="#00CED1", highlightcolor="#00CED1")
        self.title_entry.grid(row=1, column=0, columnspan=3, pady=(2, 8))

        self.title_var.trace_add("write", self.update_title)

    def prev_timer(self):
        self.current_timer = (self.current_timer - 1) % 8
        self.load_timer()

    def next_timer(self):
        self.current_timer = (self.current_timer + 1) % 8
        self.load_timer()

    def load_timer(self):
        self.timer_id_label.config(text=f"Timer {self.current_timer + 1}")
        self.title_var.set(self.timer_titles[self.current_timer])
        self.switch_callback(self.current_timer)

    def update_title(self, *args):
        self.timer_titles[self.current_timer] = self.title_var.get()


class NoteEditor(tk.Toplevel):
    """A dialog window when you want to create notes"""

    def __init__(self, parent_app, note_to_edit=None):
        super().__init__(parent_app.root)
        self.parent_app = parent_app
        self.note_to_edit = note_to_edit
        self._selection_change_active = True  # Flag to prevent update loops

        # --- Window Setup ---
        if self.note_to_edit:
            self.title("Edit Note")
        else:
            self.title("Add New Note")
        self.geometry("700x500")  # A bit wider for the new controls
        self.configure(bg="#2e2e2e")
        self.resizable(False, False)  # no resizing
        self.attributes("-toolwindow", True)  # no minimize/maximize
        self.transient(self.parent_app.root)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.cancel)

        # --- Main Layout Frames ---
        top_frame = tk.Frame(self, bg="#2e2e2e")
        top_frame.pack(fill="x", padx=10, pady=5)

        editor_frame = tk.Frame(self, bg="#2e2e2e")
        editor_frame.pack(fill="both", expand=True, padx=10)

        # --- Title Entry ---
        tk.Label(top_frame, text="Title:", font=("Helvetica", 12), bg="#2e2e2e", fg="white").pack(side="left",
                                                                                                  padx=(0, 5))
        self.title_var = tk.StringVar()
        title_entry = tk.Entry(top_frame, textvariable=self.title_var, font=("Helvetica", 12), bg="#3c3c3c", fg="white",
                               insertbackground="white")
        title_entry.pack(side="left", fill="x", expand=True)

        # --- Toolbar ---
        toolbar = tk.Frame(editor_frame, bg="#2e2e2e")
        toolbar.pack(fill="x", pady=(5, 2))

        # --- Font Dropdown (most used ones) ---
        self.font_families = sorted([
            "Arial", "Times New Roman", "Courier New", "Verdana", "Georgia", "Impact", "Tahoma", "Consolas", "Calibri"
        ])
        self.font_family_var = tk.StringVar(value="Arial")
        font_menu = tk.OptionMenu(toolbar, self.font_family_var, *self.font_families, command=self.apply_font_family)
        font_menu.config(bg="#3c3c3c", fg="white", activebackground="#4a4a9f", width=15)
        font_menu.pack(side="left", padx=(0, 5))

        # --- Font Size ---
        self.font_size_var = tk.IntVar(value=10)
        size_spinbox = tk.Spinbox(toolbar, from_=6, to=72, textvariable=self.font_size_var, width=4,
                                  command=self.apply_font_size,
                                  bg="#2e2e2e", fg="white", buttonbackground="#3c3c3c", relief="flat",
                                  highlightthickness=0, insertbackground="white")
        size_spinbox.pack(side="left", padx=(0, 5))
        size_spinbox.bind("<Return>", self.apply_font_size)

        # --- Style Buttons ---
        btn_style = {"bg": "#3c3c3c", "fg": "white", "activebackground": "#008B8B", "activeforeground": "white",
                     "relief": "flat"}
        self.bold_btn = tk.Button(toolbar, text="B", font=("Helvetica", 10, "bold"), width=3, **btn_style,
                                  command=lambda: self.toggle_tag("bold"))
        self.bold_btn.pack(side="left", padx=1)
        self.italic_btn = tk.Button(toolbar, text="I", font=("Helvetica", 10, "italic"), width=3, **btn_style,
                                    command=lambda: self.toggle_tag("italic"))
        self.italic_btn.pack(side="left", padx=1)
        self.underline_btn = tk.Button(toolbar, text="U", font=("Helvetica", 10, "underline"), width=3, **btn_style,
                                       command=lambda: self.toggle_tag("underline"))
        self.underline_btn.pack(side="left", padx=1)

        # --- Color Button ---
        tk.Button(toolbar, text="Color", **btn_style, command=self.apply_color).pack(side="left", padx=(5, 1))

        # --- Save/Cancel Buttons ---
        add_btn_text = "Save Changes" if self.note_to_edit else "Add Note"
        self.add_btn = tk.Button(toolbar, text=add_btn_text, command=self.save_note, bg="#4a4a9f", fg="white")
        self.add_btn.pack(side="right", padx=(5, 1))
        self.cancel_btn = tk.Button(toolbar, text="Cancel", command=self.cancel, bg="#555555", fg="white")
        self.cancel_btn.pack(side="right", padx=1)

        # --- Description Text Area ---
        self.desc_text = ScrolledText(editor_frame, wrap="word", bg="#1e1e1e", fg="white",
                                      insertbackground="white", undo=True, height=10, font=("Arial", 10))
        self.desc_text.pack(fill="both", expand=True)
        self.desc_text.bind("<<Selection>>", self._on_selection_change)

        # --- Bind focus out event ---
        self.desc_text.bind("<FocusOut>", lambda e: self.parent_app.root.focus_set())

        # --- Completion Type Options and their dynamic frames ---
        completion_options_container = tk.Frame(self, bg="#2e2e2e")
        completion_options_container.pack(fill="x", padx=10, pady=5)

        # --- Frame for Digits/Full Digits, it's hidden ---
        self.digits_frame = tk.Frame(self, bg="#2e2e2e")
        # (This frame will be packed/unpacked by the radio button command)
        tk.Label(self.digits_frame, text="Set Range:", bg="#2e2e2e", fg="white").grid(row=0, column=0, padx=5)
        self.min_digit_var = tk.IntVar(value=0)
        tk.Label(self.digits_frame, text="Min:", bg="#2e2e2e", fg="white").grid(row=0, column=1)
        min_digit_spinbox = tk.Spinbox(self.digits_frame, from_=0, to=9998, textvariable=self.min_digit_var, width=6)
        min_digit_spinbox.grid(row=0, column=2, padx=(0, 5))
        self.max_digit_var = tk.IntVar(value=10)
        tk.Label(self.digits_frame, text="Max:", bg="#2e2e2e", fg="white").grid(row=0, column=3)
        max_digit_spinbox = tk.Spinbox(self.digits_frame, from_=1, to=9999, textvariable=self.max_digit_var, width=6)
        max_digit_spinbox.grid(row=0, column=4)

        # --- Frame for Checkboxes ---
        self.checkbox_frame = tk.Frame(self, bg="#2e2e2e")

        # --- Radio buttons (choose completion type) ---
        completion_frame = tk.Frame(completion_options_container, bg="#2e2e2e")
        completion_frame.pack(fill="x")

        tk.Label(completion_frame, text="Completion Type:", bg="#2e2e2e", fg="white").pack(side="left")
        self.completion_type_var = tk.StringVar(value="Plain Text")

        options = ["Plain Text", "Checkboxes", "Digits/Full Digits"]
        for option in options:
            tk.Radiobutton(completion_frame, text=option, variable=self.completion_type_var,
                           value=option, bg="#2e2e2e", fg="white", selectcolor="#2e2e2e",
                           activebackground="#2e2e2e", activeforeground="white",
                           command=self._on_completion_type_change).pack(side="left", padx=5)

        # If editing, load the note's data
        if self.note_to_edit:
            self.load_note_data()

    def toggle_tag(self, tag_to_toggle):
        """Toggles a style tag (bold, italic, underline) on the selected text."""
        try:
            current_font = self.get_font_at_index("sel.first")

            if tag_to_toggle == "bold":
                new_weight = "normal" if current_font.actual("weight") == "bold" else "bold"
                new_slant = current_font.actual("slant")
                new_underline = current_font.actual("underline")
            elif tag_to_toggle == "italic":
                new_weight = current_font.actual("weight")
                new_slant = "roman" if current_font.actual("slant") == "italic" else "italic"
                new_underline = current_font.actual("underline")
            else:  # underline
                new_weight = current_font.actual("weight")
                new_slant = current_font.actual("slant")
                new_underline = 0 if current_font.actual("underline") else 1

            new_font = tkFont.Font(
                family=current_font.actual("family"),
                size=current_font.actual("size"),
                weight=new_weight,
                slant=new_slant,
                underline=new_underline
            )

            self.apply_font_to_selection(new_font)
        except tk.TclError:
            pass  # No text selected

    def get_font_at_index(self, index):
        """Correctly gets the tkFont.Font object at a given text index."""
        # Find the last-applied 'font_' tag at the index
        for tag in reversed(self.desc_text.tag_names(index)):
            if tag.startswith("font_"):
                font_config = self.desc_text.tag_cget(tag, "font")
                return tkFont.Font(font=font_config)

        # If no specific font tag is found, return the widget's default font
        return tkFont.Font(font=self.desc_text.cget("font"))

    def apply_font_to_selection(self, new_font):
        """Creates a unique tag for a font and applies it to the current selection."""
        # Create a unique tag name based on the font's properties
        family = new_font.actual('family').replace(' ', '_')
        size = new_font.actual('size')
        weight = new_font.actual('weight')
        slant = new_font.actual('slant')
        underline = new_font.actual('underline')
        font_tag = f"font_{family}_{size}_{weight}_{slant}_{underline}"

        self.desc_text.tag_configure(font_tag, font=new_font)

        # Remove all other font tags before applying the new one
        self.remove_all_font_tags("sel.first", "sel.last")
        self.desc_text.tag_add(font_tag, "sel.first", "sel.last")

    def apply_color(self):
        """Applies a selected color."""
        try:
            color = colorchooser.askcolor(parent=self)[1]
            if color:
                # Create a unique tag for this color
                color_tag = f"fg_{color.replace('#', '')}"
                self.desc_text.tag_config(color_tag, foreground=color)
                self.desc_text.tag_add(color_tag, "sel.first", "sel.last")
        except tk.TclError:
            pass  # No text selected

    def apply_font_family(self, selected_family):
        """Applies the font family from the dropdown to the selected text."""
        try:
            current_font = self.get_font_at_index("sel.first")
            new_font = tkFont.Font(
                family=selected_family,
                size=current_font.actual("size"),
                weight=current_font.actual("weight"),
                slant=current_font.actual("slant"),
                underline=current_font.actual("underline")
            )
            self.apply_font_to_selection(new_font)
        except tk.TclError:
            pass  # No text selected

    def remove_all_font_tags(self, start, end):
        """Helper to remove any conflicting font style tags from a range."""
        for tag in self.desc_text.tag_names():
            if tag.startswith("font_"):
                self.desc_text.tag_remove(tag, start, end)

    def apply_font_size(self, event=None):
        """Applies the font size from the spinbox to the selected text."""
        try:
            new_size = self.font_size_var.get()
            current_font = self.get_font_at_index("sel.first")

            new_font = tkFont.Font(
                family=current_font.actual("family"),
                size=new_size,
                weight=current_font.actual("weight"),
                slant=current_font.actual("slant"),
                underline=current_font.actual("underline")
            )
            self.apply_font_to_selection(new_font)
            self.desc_text.focus_set()
        except (tk.TclError, ValueError):
            pass  # No selection or invalid input

    def _on_selection_change(self, event=None):
        """Updates the entire toolbar state based on the selected text."""
        if not self._selection_change_active:
            return

        try:
            self._selection_change_active = False
            current_font = self.get_font_at_index("insert")

            self.font_family_var.set(current_font.actual("family"))
            self.font_size_var.set(current_font.actual("size"))

            if current_font.actual("weight") == "bold":
                self.bold_btn.config(relief="sunken", bg="#6a6ac0")
            else:
                self.bold_btn.config(relief="flat", bg="#3c3c3c")

            if current_font.actual("slant") == "italic":
                self.italic_btn.config(relief="sunken", bg="#6a6ac0")
            else:
                self.italic_btn.config(relief="flat", bg="#3c3c3c")

            if current_font.actual("underline"):
                self.underline_btn.config(relief="sunken", bg="#6a6ac0")
            else:
                self.underline_btn.config(relief="flat", bg="#3c3c3c")

        except tk.TclError:
            pass
        finally:
            self._selection_change_active = True

    def _on_completion_type_change(self):
        """Shows or hides the relevant frame based on radio button selection."""
        # Hide all dynamic frames first
        self.digits_frame.pack_forget()
        self.checkbox_frame.pack_forget()  # We still have this frame, so we hide it

        # Show the correct one
        ctype = self.completion_type_var.get()
        if ctype == "Digits/Full Digits":
            self.digits_frame.pack(fill="x", padx=10, pady=5)

    def save_note(self):
        """Saves the note data back to the main app."""
        title = self.title_var.get().strip()
        if not title:
            messagebox.showerror("Title Required", "The note must have a title.", parent=self)
            return

        description_text = self.desc_text.get("1.0", "end-1c")
        description_tags = []
        for tag in self.desc_text.tag_names():
            if tag == "sel": continue

            ranges = self.desc_text.tag_ranges(tag)
            if not ranges: continue

            config = {}
            if tag.startswith("font_"):
                font_obj = tkFont.Font(font=self.desc_text.tag_cget(tag, "font"))
                config["font"] = font_obj.actual()  # Save as a proper dictionary
            elif tag.startswith("fg_"):
                config["foreground"] = self.desc_text.tag_cget(tag, "foreground")

            if config:
                for start, end in zip(ranges[::2], ranges[1::2]):
                    description_tags.append((tag, str(start), str(end), config))

        completion_type = self.completion_type_var.get()
        completion_data = None
        if completion_type == "Digits/Full Digits":
            min_val = self.min_digit_var.get()
            max_val = self.max_digit_var.get()
            if min_val >= max_val:
                messagebox.showwarning("Invalid Range", "Minimum value must be less than the maximum value.",
                                       parent=self)
                return

            # If we are editing, keep the old current value, but clamp it to the new range
            current_val = min_val
            if self.note_to_edit and self.note_to_edit.completion_data:
                old_current = self.note_to_edit.completion_data[0]
                current_val = max(min_val, min(old_current, max_val))

            completion_data = [current_val, min_val, max_val]
        elif completion_type == "Checkboxes":
            # If editing, preserve the old checked state. Otherwise, default to False.
            if self.note_to_edit and self.note_to_edit.completion_type == "Checkboxes":
                completion_data = self.note_to_edit.completion_data
            else:
                completion_data = False  # Default to unmarked

        if self.note_to_edit:
            note = self.note_to_edit
            note.title = title
            note.description_text = description_text
            note.description_tags = description_tags
            note.completion_type = completion_type
            note.completion_data = completion_data
            self.parent_app.update_existing_note(note)
        else:
            # Create a new note with all the data
            new_note = Note(
                title=title,
                description=description_text,
                completion_type=completion_type,
                completion_data=completion_data
            )
            new_note.description_tags = description_tags
            self.parent_app.add_new_note_to_current_timer(new_note)

        self.destroy()

    def load_note_data(self):
        """Populates the editor with data from an existing note."""
        self.title_var.set(self.note_to_edit.title)
        self.desc_text.insert("1.0", self.note_to_edit.description_text)

        # Apply all saved tags
        for tag_name, start, end, config in self.note_to_edit.description_tags:
            if "font" in config:
                font_data = config["font"]
                # Handle both new dicts and old strings
                if isinstance(font_data, dict):
                    self.desc_text.tag_configure(tag_name, font=tkFont.Font(**font_data))
                else:  # Failsafe to old string format
                    self.desc_text.tag_configure(tag_name, font=font_data)
            elif "foreground" in config:
                self.desc_text.tag_configure(tag_name, foreground=config["foreground"])

            self.desc_text.tag_add(tag_name, start, end)

        self.completion_type_var.set(self.note_to_edit.completion_type)

        # Load completion-specific data
        if self.note_to_edit.completion_type == "Digits/Full Digits":
            data = self.note_to_edit.completion_data
            # Check for new [current, min, max] format
            if data and isinstance(data, list) and len(data) == 3:
                self.min_digit_var.set(data[1])
                self.max_digit_var.set(data[2])
            # Backwards compatibility for old [current, max] format
            elif data and isinstance(data, list) and len(data) == 2:
                self.min_digit_var.set(0)  # Default min to 0
                self.max_digit_var.set(data[1])

        # Don't forget to rechange UI after loading all data
        self._on_completion_type_change()

    def cancel(self):
        self.destroy()


class NoteViewer(tk.Toplevel):
    """A dialog for viewing and interacting with a single Note."""

    def __init__(self, parent_app, note_to_view, note_index):
        super().__init__(parent_app.root)
        self.parent_app = parent_app
        self.note = note_to_view
        self.note_index = note_index

        self.title("Note Viewer")
        self.geometry("700x450")
        self.configure(bg="#2e2e2e")
        self.resizable(False, False)  # no resizing
        self.attributes("-toolwindow", True)  # no minimize/maximize
        self.transient(parent_app.root)
        self.grab_set()

        # --- Main Layout ---
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # --- Title ---
        title_label = tk.Label(self, text=self.note.title, font=("Helvetica", 16, "bold"),
                               bg="#2e2e2e", fg="white", wraplength=680)
        title_label.grid(row=0, column=0, columnspan=3, pady=(10, 5), sticky="n")

        # --- Separator ---
        self.separator = tk.Frame(self, height=2, bg="#4a4a4f")
        self.separator.grid(row=2, column=1, padx=5, sticky="ns")

        # --- Description Panel (Right Side) ---
        self.build_description_panel()

        # --- Completion Panel (Left Side) ---
        self.build_completion_panel()

        # --- Bottom Control Buttons ---
        self.build_controls()

    def build_description_panel(self):
        self.desc_frame = tk.Frame(self, bg="#1e1e1e")
        self.desc_frame.grid(row=2, column=2, sticky="nsew", padx=(0, 10), pady=(0, 10))
        self.desc_frame.grid_rowconfigure(0, weight=1)
        self.desc_frame.grid_columnconfigure(0, weight=1)

        # --- ScrolledText ---
        desc_text = tk.Text(self.desc_frame, wrap="word", bg="#1e1e1e", fg="white",
                            highlightthickness=0, relief="flat", bd=0, insertbackground="white")
        desc_text.grid(row=0, column=0, sticky="nsew")

        # Create and style the scrollbar
        scrollbar = tk.Scrollbar(self.desc_frame, orient="vertical", command=desc_text.yview,
                                 bg="#2e2e2e", troughcolor="#1e1e1e", activebackground="#008B8B")
        scrollbar.grid(row=0, column=1, sticky="ns")
        desc_text.config(yscrollcommand=scrollbar.set)

        # Populate with text and apply formatting
        desc_text.config(state="normal")
        desc_text.insert("1.0", self.note.description_text)

        for tag_name, start, end, config in self.note.description_tags:
            if "font" in config:
                font_data = config["font"]
                if isinstance(font_data, dict):
                    desc_text.tag_configure(tag_name, font=tkFont.Font(**font_data))
                else:
                    desc_text.tag_configure(tag_name, font=font_data)
            elif "foreground" in config:
                desc_text.tag_configure(tag_name, foreground=config["foreground"])

            desc_text.tag_add(tag_name, start, end)

        desc_text.config(state="disabled")

    def build_completion_panel(self):
        self.completion_frame = tk.Frame(self, bg="#2e2e2e", width=200)
        self.completion_frame.grid(row=2, column=0, sticky="nsew", padx=(10, 0), pady=(0, 10))

        # Populate based on completion type
        if self.note.completion_type == "Plain Text":
            # Just plain text
            self.grid_columnconfigure(0, weight=0)  # Make sure first column doesn't expand
            self.completion_frame.grid_forget()
            self.desc_frame.grid_configure(column=0, columnspan=3)  # Span all 3 columns
            self.separator.grid_forget()  # Hide the separator


        elif self.note.completion_type == "Checkboxes":

            self.build_checkbox_completion()

        elif self.note.completion_type == "Digits/Full Digits":
            self.build_digits_completion()

    def build_checkbox_completion(self):
        """Creates a single large checkbox representing the note's status."""
        is_checked = self.note.completion_data if isinstance(self.note.completion_data, bool) else False
        self.checkbox_var = tk.BooleanVar(value=is_checked)

        container = tk.Frame(self.completion_frame, bg="#2e2e2e")
        container.pack(expand=True)

        cb = tk.Checkbutton(container, variable=self.checkbox_var, bg="#2e2e2e",
                            selectcolor="#1e1e1e",
                            command=self.update_checkbox_value)

        # Configure colors and font separately for reliability
        cb.config(
            font=("Helvetica", 20),
            fg="white",  # Color of the checkmark
            activebackground="#008B8B",  # Background color
            activeforeground="white"  # Checkmark color
        )

        cb.pack()

    def update_checkbox_value(self):
        """Saves the new state of the note's checkbox."""
        new_state = self.checkbox_var.get()
        self.note.completion_data = new_state
        self.parent_app.update_existing_note(self.note)

    def build_digits_completion(self):
        data = self.note.completion_data
        current_val, min_val, max_val = (data[0], data[1], data[2]) if data and len(data) == 3 else (0, 0, 10)

        self.current_digit_var = tk.IntVar(value=current_val)

        container = tk.Frame(self.completion_frame, bg="#2e2e2e")
        container.pack(expand=True)

        # Min/Max Spinbox
        spinbox = tk.Spinbox(container, from_=min_val, to=max_val, textvariable=self.current_digit_var,
                             width=5, font=("Helvetica", 16), justify="center",
                             command=self.update_digit_value,
                             bg="#2e2e2e", fg="white", buttonbackground="#3c3c3c", relief="flat",
                             highlightthickness=1, highlightbackground="#00CED1", insertbackground="white")
        spinbox.grid(row=0, column=0, padx=5)

        slash_label = tk.Label(container, text="/", font=("Helvetica", 16, "bold"), bg="#2e2e2e", fg="white")
        slash_label.grid(row=0, column=1)

        max_label = tk.Label(container, text=str(max_val), font=("Helvetica", 16), bg="#2e2e2e", fg="white")
        max_label.grid(row=0, column=2, padx=5)

        spinbox.bind("<Return>", lambda e: self.update_digit_value())

    def update_digit_value(self, event=None):
        """Callback to save the new digit value when the spinbox is changed."""
        min_val = self.note.completion_data[1]
        max_val = self.note.completion_data[2]

        try:
            new_value = self.current_digit_var.get()
            # Clamp the value just in case of manual entry
            clamped_value = max(min_val, min(new_value, max_val))

            if new_value != clamped_value:
                self.current_digit_var.set(clamped_value)

            self.note.completion_data[0] = clamped_value
            self.parent_app.update_existing_note(self.note)
        except tk.TclError:
            # Handle case where user enters non-integer
            self.current_digit_var.set(self.note.completion_data[0])

    def build_controls(self):
        controls_frame = tk.Frame(self, bg="#2e2e2e")
        controls_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(5, 10), padx=10)

        btn_style = {"bg": "#2e2e2e", "fg": "white", "activebackground": "#008B8B", "activeforeground": "white",
                     "relief": "flat", "font": ("Segoe UI Emoji", 10)} # Deprecated

        # --- Left Side Buttons ---
        tk.Button(controls_frame, text="\u25B2", command=self.move_note_up, **btn_style).pack(side="left")  # Up Arrow
        tk.Button(controls_frame, text="\u25BC", command=self.move_note_down, **btn_style).pack(side="left",
                                                                                                padx=5)  # Down Arrow
        tk.Button(controls_frame, text="Delete Note", bg="#a13d3d", fg="white", relief="flat",
                  command=self.delete_note).pack(
            side="left", padx=(10, 0))

        # --- Right Side Buttons ---
        tk.Button(controls_frame, text="Close", **btn_style, command=self.destroy).pack(side="right")

    def delete_note(self):
        if messagebox.askyesno("Confirm Deletion", "Are you sure you want to permanently delete this note?",
                               parent=self):
            self.parent_app.delete_note_at_index(self.note_index)
            self.destroy()

    def move_note_up(self):
        if self.parent_app.move_note(self.note_index, "up"):
            self.note_index -= 1  # Update our internal index up

    def move_note_down(self):
        if self.parent_app.move_note(self.note_index, "down"):
            self.note_index += 1  # Update our internal index down

class TimerApp:
    def __init__(self, root):
        self.alarm_playing = None
        self.loop_count = 1
        self.config_busy = False
        self.present_path = None
        self.pause_flash_state = False
        # --- Default Sound Paths ---
        self.default_sound1 = self.resource_path("alarmA.ogg")
        self.default_sound2 = self.resource_path(
            "alarmB.mp3")

        # --- Current Timer's Sound Paths ---
        # These will be updated when switching timers or setting new sounds.
        self.sound_path1 = self.default_sound1
        self.sound_path2 = self.default_sound2

        self.root = root
        self.root.title("Panda's Cool Clock for Friendly Friends :>  _--_  v0.7")
        self.root.geometry("620x510")
        self.root.resizable(False, False)  # no resizing
        self.root.minsize(620, 510)
        self.root.configure(bg="#1e1e1e")  # dark background

        try:
            # Icon
            icon_path = self.resource_path("timer_icon.ico")
            self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Error setting application icon: {e}")

        self.timer_switcher = TimerSwitcher(self.root, self.switch_timer)
        self.timer_switcher.pack(pady=(10, 0))



        # Initialize timer data placeholders
        # Each timer has a 'notes' list associated with it
        self.all_timers_data = [{"notes": []} for _ in range(8)]
        self.timer_fired_flags = [False for _ in range(8)]
        self.current_timer_id = 0

        # This will hold the notes for the CURRENTLY active timer
        self.notes = []

        self.audio_player = Playback()
        self.alarm_loop_counter = 0

        self.week_seconds = 7 * 24 * 3600

        self.day_var = tk.IntVar()
        self.hour_var = tk.IntVar()
        self.min_var = tk.IntVar()
        self.sec_var = tk.IntVar()
        self.update_timer_var = tk.BooleanVar()

        self.end_time = None
        self.paused = False
        self.pause_time = None
        self.remaining_duration = None
        self.timer_running = False

        self.timer_file = "CurrentTimer.ini"

        self.build_ui()
        self.load_timer_from_memory()
        self.try_restore_timer()

        self.check_all_timers()
        self.setup_listbox_tooltip()

    @staticmethod
    def resource_path(relative_path):
        """ Get absolute path to resource """
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)

    def on_note_selection_change(self, event=None):
        """Called when listbox selection changes. Enables/disables all relevant buttons."""
        selected_indices = self.notes_listbox.curselection()
        if not selected_indices:
            # No selection, disable all buttons
            self.edit_note_btn.config(state="disabled")
            self.delete_note_btn.config(state="disabled")
            self.mark_btn.config(state="disabled")
            self.unmark_btn.config(state="disabled")
            return

        # An item is selected, so Edit and Delete are always possible
        self.edit_note_btn.config(state="normal")
        self.delete_note_btn.config(state="normal")

        note_index = selected_indices[0]
        note = self.notes[note_index]

        # Enable/disable Mark/Unmark based on note type
        if note.completion_type == "Plain Text":
            self.mark_btn.config(state="disabled")
            self.unmark_btn.config(state="disabled")
        else:
            self.mark_btn.config(state="normal")
            self.unmark_btn.config(state="normal")

    def mark_selected_note(self, increment=True):
        """
        Handles the 'Mark' and 'Unmark' buttons.
        - For Checkboxes: Marks or unmarks the note.
        - For Digits: Increments or decrements the current value.
        - For Plain Text: Does nothing. What? You want them to grow or shrink? Nah.
        """
        selected_indices = self.notes_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please select a note to modify.")
            return

        note_index = selected_indices[0]
        note = self.notes[note_index]

        if note.completion_type == "Checkboxes":
            note.completion_data = increment # True for Mark, False for Unmark

        elif note.completion_type == "Digits/Full Digits":
            current, min_val, max_val = note.completion_data
            if increment: # Mark Note = Increment
                if current < max_val:
                    note.completion_data[0] += 1
            else: # Unmark Note = Decrement
                if current > min_val:
                    note.completion_data[0] -= 1
        else:
            return

        self.update_existing_note(note)
        self.notes_listbox.selection_set(note_index)
        self.notes_listbox.activate(note_index)

    def draw_stopwatch(self, canvas):
        """Draws a vector stopwatch on the provided canvas."""
        width = int(canvas['width'])
        height = int(canvas['height'])

        # Center coordinates, shifted down to make room for top buttons
        cx = width / 2
        cy = height / 2 + 15

        # --- Draw Layers from Back to Front ---

        # 1. Main silver body
        main_radius = 100
        canvas.create_oval(cx - main_radius, cy - main_radius, cx + main_radius, cy + main_radius,
                           fill="#a0a0a0", outline="#555555", width=2)

        # Angled Side Plungers
        plunger_w_radius = 6
        plunger_h_radius = 14
        for angle_deg in [-36, 36]:  # Angle from the top vertical axis
            # Calculate the center of the plunger on the edge of the main body
            center_angle_rad = math.radians(270 + angle_deg)
            plunger_cx = cx + (main_radius - 5) * math.cos(center_angle_rad)
            plunger_cy = cy + (main_radius - 5) * math.sin(center_angle_rad) - 16

            # Rotation angle for the plunger itself
            rotation_rad = math.radians(angle_deg)
            cos_rot = math.cos(rotation_rad)
            sin_rot = math.sin(rotation_rad)

            points = []
            # Create a smooth oval shape with 20 points
            for i in range(21):
                point_angle_rad = (i / 20) * 2 * math.pi
                # Un-rotated point
                px = plunger_w_radius * math.cos(point_angle_rad)
                py = plunger_h_radius * math.sin(point_angle_rad)

                # Rotated point
                rotated_x = px * cos_rot - py * sin_rot
                rotated_y = px * sin_rot + py * cos_rot

                # Translate to final position and add to list
                points.extend([plunger_cx + rotated_x, plunger_cy + rotated_y])

            canvas.create_polygon(points, fill="#a0a0a0", outline="#555555", width=2)

        # 2. Bezel highlight (a slightly smaller, lighter circle on top)
        bezel_radius = 106
        canvas.create_oval(cx - bezel_radius, cy - bezel_radius, cx + bezel_radius, cy + bezel_radius,
                           fill="#cccccc", outline="#a0a0a0", width=1)

        # Top Buttons and Connectors
        btn_y = cy - main_radius - 2
        # 3. Hollow
        canvas.create_oval(cx - 12, btn_y - 43, cx + 11, btn_y - 16,
                           fill="#cfb1db", outline="#1b7897", width=2)
        # Top plunger part
        canvas.create_rectangle(cx - 5, btn_y - 18, cx + 5, btn_y - 4,
                                fill="#a0a0a0", outline="#555555", width=2)
        # Center square button
        canvas.create_rectangle(cx - 8, btn_y - 28, cx + 8, btn_y - 13,
                                fill="#a0a0a0", outline="#555555", width=2)


        # 4. Inner black face background
        face_radius = 85
        canvas.create_oval(cx - face_radius, cy - face_radius, cx + face_radius, cy + face_radius,
                           fill="black", outline="")

        # 5. Dashed Blue Outer Ring
        dash_radius_outer = 78
        dash_radius_inner = 72
        for i in range(60):
            angle = math.radians(i * 6)  # 360 degrees / 60 ticks
            x1 = cx + dash_radius_outer * math.cos(angle)
            y1 = cy + dash_radius_outer * math.sin(angle)
            x2 = cx + dash_radius_inner * math.cos(angle)
            y2 = cy + dash_radius_inner * math.sin(angle)
            canvas.create_line(x1, y1, x2, y2, fill="#00aaff", width=3)

        # 6. Inner "Stitching" Dashed Ring
        stitch_radius_outer = 68
        stitch_radius_inner = 65
        for i in range(120):  # More ticks for a finer look
            angle = math.radians(i * 3)  # 360 / 120
            x1 = cx + stitch_radius_outer * math.cos(angle)
            y1 = cy + stitch_radius_outer * math.sin(angle)
            x2 = cx + stitch_radius_inner * math.cos(angle)
            y2 = cy + stitch_radius_inner * math.sin(angle)
            canvas.create_line(x1, y1, x2, y2, fill="#333333", width=2)

        # 7. Final black display circle to cover the center
        display_radius = 62
        canvas.create_oval(cx - display_radius, cy - display_radius, cx + display_radius, cy + display_radius,
                           fill="black", outline="")

    def build_ui(self):
        # The main container
        main_panels_frame = tk.Frame(self.root, bg="#1e1e1e")
        main_panels_frame.pack(expand=True, fill="both", padx=10, pady=5)

        # Notes Section
        self.notes_panel = tk.Frame(main_panels_frame, bg="#2a2a2a")
        self.notes_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.notes_panel.grid_columnconfigure(0, weight=1)
        self.notes_panel.grid_rowconfigure(1, weight=1)

        # --- Notes Panel Header with Add Button ---
        notes_header_frame = tk.Frame(self.notes_panel, bg="#2a2a2a")
        notes_header_frame.grid(row=0, column=0, pady=(5, 10), sticky="ew")

        self.add_note_btn = tk.Button(notes_header_frame, text="+", font=("Helvetica", 16, "bold"),
                                      bg="#2e2e2e", fg="#4CAF50",  # Dark BG, Green text
                                      activebackground="#008B8B", activeforeground="white",
                                      command=self.open_add_note_dialog,
                                      width=2, relief="flat", highlightthickness=1,
                                      highlightbackground="#00CED1")
        self.add_note_btn.pack(side="left", padx=(10, 5))

        notes_label = tk.Label(notes_header_frame, text="Notes Library", font=("Helvetica", 14, "bold"), bg="#2a2a2a",
                               fg="white")
        notes_label.pack(side="left", padx=(0, 10))  # Added padding

        # Frame for the listbox and its scrollbar
        list_frame = tk.Frame(self.notes_panel, bg="#2a2a2a")
        list_frame.grid(row=1, column=0, sticky="nsew", padx=5)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        self.notes_listbox = tk.Listbox(list_frame, bg="#1e1e1e", fg="white", selectbackground="#4a4a9f",
                                        highlightthickness=0, borderwidth=1, relief="solid",
                                        font=("Consolas", 15))
        self.notes_listbox.grid(row=0, column=0, sticky="nsew")
        self.notes_listbox.bind("<Double-1>", self.open_note_viewer)
        self.notes_listbox.bind("<<ListboxSelect>>", self.on_note_selection_change)

        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=self.notes_listbox.yview,
                                 bg="#2e2e2e", troughcolor="#1e1e1e", activebackground="#008B8B")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.notes_listbox.config(yscrollcommand=scrollbar.set)

        # Frame for the control buttons below the list
        notes_button_frame = tk.Frame(self.notes_panel, bg="#2a2a2a")
        notes_button_frame.grid(row=2, column=0, pady=5)

        btn_style = {"bg": "#3c3c3c", "fg": "white", "width": 10}

        # Delete Note Button
        self.delete_note_btn = tk.Button(notes_button_frame, text="Delete Note", bg="#a13d3d", fg="white", width=10,
                                         state="normal", command=self.delete_selected_note)
        self.delete_note_btn.grid(row=0, column=0, padx=3, pady=2)

        # Edit Note Button
        self.edit_note_btn = tk.Button(notes_button_frame, text="Edit Note...", **btn_style, state="normal",
                                       command=self.open_edit_note_dialog)
        self.edit_note_btn.grid(row=0, column=1, padx=3, pady=2)

        # Mark Note Button
        self.mark_btn = tk.Button(notes_button_frame, text="Mark Note", **btn_style, state="disabled",
                                  command=self.mark_selected_note)
        self.mark_btn.grid(row=1, column=0, padx=3, pady=2)

        # Unmark Note Button
        self.unmark_btn = tk.Button(notes_button_frame, text="Unmark Note", **btn_style, state="disabled",
                                    command=lambda: self.mark_selected_note(False))
        self.unmark_btn.grid(row=1, column=1, padx=3, pady=2)

        # Time Controls on the right side. Basically where the timer is at
        self.right_panel = tk.Frame(main_panels_frame, bg="#1e1e1e")
        self.right_panel.pack(side="right", fill="both", expand=True)

        # This frame will hold the time inputs (Days, Hours, etc.)
        spinbox_frame = tk.Frame(self.right_panel, bg="#1e1e1e")
        spinbox_frame.pack(side="top", fill="x", pady=(0, 10))

        label_font = ("Helvetica", 12)
        spinbox_font = ("Helvetica", 12)

        #Create two sub-frames for top-left and top-right inputs
        left_inputs = tk.Frame(spinbox_frame, bg="#1e1e1e")
        left_inputs.pack(side="left", padx=(10, 20))

        right_inputs = tk.Frame(spinbox_frame, bg="#1e1e1e")
        right_inputs.pack(side="right", padx=(20, 10))

        # Minutes
        tk.Label(left_inputs, text="Minutes:", font=label_font, bg="#1e1e1e", fg="white").grid(row=0, column=0, padx=5,
                                                                                               pady=2, sticky="w")
        spinbox_style = {"bg": "#2e2e2e", "fg": "white", "insertbackground": "white", "relief": "flat",
                         "highlightthickness": 0, "buttonbackground": "#3c3c3c"}
        self.min_spin = tk.Spinbox(left_inputs, from_=0, to=999, textvariable=self.min_var, width=5, font=spinbox_font,
                                   **spinbox_style)
        self.min_spin.grid(row=0, column=1, padx=5, pady=2)
        self.min_spin.bind("<Return>", self.normalize_time_event)

        # Seconds
        tk.Label(left_inputs, text="Seconds:", font=label_font, bg="#1e1e1e", fg="white").grid(row=1, column=0, padx=5,
                                                                                               pady=2, sticky="w")
        self.sec_spin = tk.Spinbox(left_inputs, from_=0, to=999, textvariable=self.sec_var, width=5, font=spinbox_font,
                                   **spinbox_style)
        self.sec_spin.grid(row=1, column=1, padx=5, pady=2)
        self.sec_spin.bind("<Return>", self.normalize_time_event)

        # Days
        tk.Label(right_inputs, text="Days:", font=label_font, bg="#1e1e1e", fg="white").grid(row=0, column=0, padx=5,
                                                                                             pady=2, sticky="w")
        self.day_spin = tk.Spinbox(right_inputs, from_=0, to=35, textvariable=self.day_var, width=5, font=spinbox_font,
                                   **spinbox_style)
        self.day_spin.grid(row=0, column=1, padx=5, pady=2)
        self.day_spin.bind("<Return>", self.normalize_time_event)

        # Hours
        tk.Label(right_inputs, text="Hours:", font=label_font, bg="#1e1e1e", fg="white").grid(row=1, column=0, padx=5,
                                                                                              pady=2, sticky="w")
        self.hour_spin = tk.Spinbox(right_inputs, from_=0, to=999, textvariable=self.hour_var, width=5,
                                    font=spinbox_font, **spinbox_style)
        self.hour_spin.grid(row=1, column=1, padx=5, pady=2)
        self.hour_spin.bind("<Return>", self.normalize_time_event)

        # The timer display canvas
        self.image_canvas = tk.Canvas(self.right_panel, width=341, height=256, bg="#1e1e1e", highlightthickness=0)
        self.image_canvas.pack(side="top", anchor="e", padx=(0, 5))

        # Draw the stopwatch
        self.draw_stopwatch(self.image_canvas)

        text_cx = 341 / 2
        text_cy = 256 / 2 + 0
        main_font = ("Consolas", 21, "bold")
        extra_font = ("Consolas", 16, "bold")
        main_color = "white"

        # Create main text item
        self.timer_text_main = self.image_canvas.create_text(text_cx, text_cy - 5, text="00:00:00", font=main_font,
                                                             fill=main_color)

        # Create extra text item (initially off-screen)
        self.timer_text_extra = self.image_canvas.create_text(1000, 1000, text="", font=extra_font, fill=main_color)

        # This frame will hold the control buttons (Start, Pause)
        controls_frame = tk.Frame(self.right_panel, bg="#1e1e1e")
        controls_frame.pack(side="bottom", fill="x", pady=5)

        # Create a sub-frame for the buttons on the bottom-right
        button_group_frame = tk.Frame(controls_frame, bg="#1e1e1e")
        button_group_frame.pack(side="right", padx=10)

        self.update_check = tk.Checkbutton(
            button_group_frame, text="Update Timer", font=("Helvetica", 12),
            variable=self.update_timer_var, state='disabled',
            bg="#1e1e1e", fg="white", selectcolor="#1e1e1e", activebackground="#1e1e1e", activeforeground="white"
        )
        self.update_check.grid(row=0, column=0, columnspan=2, sticky="e", pady=(0, 5))

        self.start_btn = tk.Button(button_group_frame, text="Start", font=label_font,
                                   command=self.start_timer, bg="#211c90", fg="white", width=8)
        self.start_btn.grid(row=1, column=0, padx=5)

        self.pause_btn = tk.Button(button_group_frame, text="Pause", font=label_font, state='disabled',
                                   command=self.toggle_pause, bg="#211c90", fg="white", width=8)
        self.pause_btn.grid(row=1, column=1, padx=5)

        self.update_timer_canvas("00:00:00", color_main="white")

        # --- Menus ---
        self.menu = tk.Menu(self.root)
        self.root.config(menu=self.menu)
        file_menu = tk.Menu(self.menu, tearoff=0, bg="#2e2e2e", fg="white")
        self.menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Present...", command=self.new_present)
        file_menu.add_command(label="Import Present...", command=self.import_present)
        file_menu.add_command(label="Save Present", command=self.save_present)
        file_menu.add_command(label="Delete Present...", command=self.delete_present)
        options_menu = tk.Menu(self.menu, tearoff=0, bg="#2e2e2e", fg="white")
        self.menu.add_cascade(label="Options", menu=options_menu)
        options_menu.add_command(label="Loop...", command=self.set_loop)
        options_menu.add_command(label="Change Sound...", command=self.choose_sound)

    def normalize_time_event(self, event=None):
        self.normalize_time()

    def normalize_time(self):
        # The maximum of time a timer can hold is 35 days
        total_seconds = min(self.get_input_seconds(), 35 * 86400)

        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        self.day_var.set(days)
        self.hour_var.set(hours)
        self.min_var.set(minutes)
        self.sec_var.set(seconds)

    def start_timer(self):
        if self.config_busy:
            return

        if self.start_btn.cget("text") == "Stop":
            # 1. Reset the current state variables for the current timer.
            # The duration values (days, hours, etc.) are kept as they are.
            self.timer_running = False
            self.paused = False
            self.end_time = None
            self.pause_time = None
            self.remaining_duration = None
            self.timer_fired_flags[self.current_timer_id] = False

            # 2. Update the UI to reflect the "stopped" state.
            self.start_btn.config(text='Start')
            self.pause_btn.config(text='Pause', state='disabled')
            self.update_check.config(state='disabled')
            self.enable_spinboxes()
            self.update_timer_canvas("00:00:00", color_main="white")

            # 3. Save the new state of ALL timers.
            # This will update the now-stopped timer in the CurrentTimer.ini file
            # while preserving the state of all other timers.
            # I suck at programming. I know.
            self.save_current_timer_state()

            return

        # Starting a new timer
        self.normalize_time()
        total_seconds = self.get_input_seconds()

        if total_seconds <= 0:
            messagebox.showwarning("Invalid Time", "Please set a duration greater than 0.")
            return

        self.end_time = datetime.now() + timedelta(seconds=total_seconds)
        self.remaining_duration = timedelta(seconds=total_seconds)
        self.paused = False
        self.timer_running = True

        # Save the initial running state for all timers to the file
        # Ignore the "current" word.
        self.save_current_timer_state()

        self.start_btn.config(text='Stop', state='normal')
        self.pause_btn.config(state='normal', text='Pause')

        self.disable_spinboxes()
        self.update_check.config(state='disabled')
        self.update_timer_var.set(False)

        self.update_timer()

    def toggle_pause(self):
        if self.config_busy:
            return
        if not self.timer_running:
            return

        if not self.paused:
            # --- Pausing the timer ---
            self.paused = True
            self.start_btn.config(text='Stop', state='normal')
            self.pause_time = datetime.now()

            # --- Sync memory with the new "paused" state ---
            self.save_current_timer_to_memory()

            self.save_current_timer_state()
            self.pause_btn.config(text='Resume')
            self.enable_spinboxes()
            self.save_config()
            self.update_check.config(state='normal')
        else:
            # --- Resuming the timer ---
            if self.update_timer_var.get():
                self.normalize_time()
                new_total = self.get_input_seconds()
                if new_total <= 0:
                    messagebox.showwarning("Invalid Time", "Please set a duration greater than 0.")
                    return
                self.end_time = datetime.now() + timedelta(seconds=new_total)
                self.remaining_duration = timedelta(seconds=new_total)
                self.save_current_timer_state()
                self.update_timer_var.set(False)
            else:
                pause_duration = datetime.now() - self.pause_time
                self.end_time += pause_duration

            self.save_config()
            self.update_check.config(state='disabled')
            self.paused = False
            self.start_btn.config(text='Stop', state='normal')
            self.pause_btn.config(text='Pause')

            # --- Sync memory with the new "resumed" state ---
            self.save_current_timer_to_memory()

            self.save_current_timer_state()
            self.disable_spinboxes()
            self.update_timer()

    def update_timer(self):
        if not self.timer_running:
            return

        if self.paused:
            self.handle_pause_flash()
            self.root.after(500, self.update_timer)
            return

        now = datetime.now()
        remaining = self.end_time - now

        if remaining.total_seconds() <= 0:
            self.timer_running = False
            self.start_btn.config(state='normal', text='Start')
            self.pause_btn.config(state='disabled')
            self.enable_spinboxes()
            self.update_check.config(state='disabled')

            self.update_timer_canvas("00:00:00", color_main="#ff3c3c")

            self.play_alarm(self.sound_path1, self.sound_path2, self.loop_count)
            self.save_current_timer_state()
            self.show_timer_finished_popup()
            return

        self.remaining_duration = remaining
        self.display_remaining_time(remaining)
        self.root.after(500, self.update_timer)

    def show_timer_finished_popup(self, timer_id=None, title=None):
        popup = tk.Toplevel(self.root)
        popup.title("Timer Finished!")
        popup.geometry("300x150")
        popup.configure(bg="#1e1e1e")
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()

        label_text = "Timer has finished!"
        if timer_id is not None and title:
            label_text = f"Timer {timer_id + 1} \"{title}\" has finished!"

        label = tk.Label(popup, text=label_text, font=("Helvetica", 13),
                         bg="#1e1e1e", fg="white", wraplength=280, justify="center")
        label.pack(pady=(30, 10))

        def stop_alarm_and_close():
            if self.audio_player.playing:
                self.audio_player.stop()
            popup.destroy()

        ok_btn = tk.Button(popup, text="OK", command=stop_alarm_and_close,
                           bg="#333399", fg="white", font=("Helvetica", 11))
        ok_btn.pack()

        # Also handle window close button
        popup.protocol("WM_DELETE_WINDOW", stop_alarm_and_close)

    def show_background_timer_popup(self, timer_id):
        title = self.timer_switcher.timer_titles[timer_id]
        self.show_timer_finished_popup(timer_id=timer_id, title=title)

    def handle_pause_flash(self):
        if not self.pause_time:
            return

        elapsed = int((datetime.now() - self.pause_time).total_seconds())
        # I like to make UI cool
        if elapsed % 4 == 0:
            color = "#f14f8c"  # Red (once every 4 seconds)
        else:
            color = "#00c650"  # Green for the other 3 seconds

        self.image_canvas.itemconfig(self.timer_text_main, fill=color)
        self.image_canvas.itemconfig(self.timer_text_extra, fill=color)

    def update_timer_canvas(self, time_text, extra_text="", color_main="white", color_extra="white"):
        text_cx = 341 / 2
        text_cy = 256 / 2

        # Update text content for the main items
        self.image_canvas.itemconfig(self.timer_text_main, text=time_text, fill=color_main)
        self.image_canvas.itemconfig(self.timer_text_extra, text=extra_text, fill=color_extra)

        if extra_text:
            # Position for main text with extra text below
            main_y = text_cy + 2
            extra_y = text_cy + 35
            self.image_canvas.coords(self.timer_text_main, text_cx, main_y)
            self.image_canvas.coords(self.timer_text_extra, text_cx, extra_y)
        else:
            # Position for centered main text, extra text off-screen
            main_y = text_cy + 2
            self.image_canvas.coords(self.timer_text_main, text_cx, main_y)
            self.image_canvas.coords(self.timer_text_extra, 1000, 1000)

    def get_input_seconds(self):
        try:
            d = int(self.day_var.get())
            h = int(self.hour_var.get())
            m = int(self.min_var.get())
            s = int(self.sec_var.get())
            total = max(0, d * 86400 + h * 3600 + m * 60 + s)
            return min(total, 35 * 86400)
        except:
            return 0

    def disable_spinboxes(self):
        self.day_spin.config(state='disabled')
        self.hour_spin.config(state='disabled')
        self.min_spin.config(state='disabled')
        self.sec_spin.config(state='disabled')

    def enable_spinboxes(self):
        self.day_spin.config(state='normal')
        self.hour_spin.config(state='normal')
        self.min_spin.config(state='normal')
        self.sec_spin.config(state='normal')

    def check_all_timers(self):
        for i in range(8):
            if i == self.current_timer_id:
                continue  # Move to the next timer in the loop

            data = self.all_timers_data[i]
            if data.get("running") and not data.get("paused"):
                end_time = data.get("end_time")
                if end_time and isinstance(end_time, datetime):
                    remaining = end_time - datetime.now()
                    if remaining.total_seconds() <= 0 and not self.timer_fired_flags[i]:
                        self.timer_fired_flags[i] = True
                        data["running"] = False
                        data["paused"] = False
                        data["remaining_duration"] = timedelta(seconds=0)
                        data["end_time"] = None

                        self.play_alarm(
                            sound1=data.get("sound_path1"),
                            sound2=data.get("sound_path2"),
                            loop_count=data.get("loop_count")
                        )

                        title = self.timer_switcher.timer_titles[i]
                        self.show_timer_finished_popup(timer_id=i, title=title)

                        # --- Save the updated state ---
                        self.save_current_timer_state()

        self.root.after(1000, self.check_all_timers)

    def play_alarm(self, sound1, sound2, loop_count):
        if self.audio_player.playing:
            self.audio_player.stop()

        if not sound1: sound1 = self.default_sound1
        if not sound2: sound2 = self.default_sound2
        if sound1 and not sound2: sound2 = sound1

        if not os.path.exists(sound1) or not os.path.exists(sound2):
            print(f"Alarm sound file(s) missing or invalid.\nPath1: {sound1}\nPath2: {sound2}")
            messagebox.showerror("Alarm Error", "Could not find the alarm sound file(s).")
            return

        try:
            chosen_sound = random.choice([sound1, sound2])
            self.audio_player.load_file(chosen_sound)

            # Set up the loop counter. 0 means infinite, so we set a high number.
            # Otherwise, use the user's count (1 means play once, so loops=0).
            self.alarm_loop_counter = 9999 if loop_count == 0 else loop_count - 1

            self.audio_player.play()
            print(f"[Alarm] Playing: {os.path.basename(chosen_sound)}")

        except Exception as e:
            print("Error playing alarm:", e)
            messagebox.showerror("Alarm Error", f"Could not play the alarm sound:\n{e}")

    def stop_alarm(self):
        if self.audio_player.playing:
            self.audio_player.stop()

    def change_sound(self):
        filetypes = [("Audio Files", "*.mp3 *.wav *.ogg")]
        initial_dir = os.path.dirname(self.sound_path1) if self.sound_path1 else os.getcwd()

        path1 = filedialog.askopenfilename(title="Select Primary Alarm Sound", filetypes=filetypes,
                                           initialdir=initial_dir)
        if not path1 or not os.path.isfile(path1):
            return

        try:
            # Use a temporary player instance to check duration
            temp_player = Playback()
            temp_player.load_file(path1)
            duration = temp_player.duration
            temp_player.stop()  # Release the file handle

            if duration > 12:
                messagebox.showwarning("Too Long", "Primary sound must be 12 seconds or shorter.")
                return
            self.sound_path1 = path1
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load primary sound:\n{e}")
            return

        # Ask for secondary
        if messagebox.askyesno("Secondary Alarm", "Do you need a secondary alarm to be played randomly?"):
            path2 = filedialog.askopenfilename(title="Select Secondary Alarm Sound", filetypes=filetypes,
                                               initialdir=initial_dir)
            if path2 and os.path.isfile(path2):
                try:
                    temp_player.load_file(path2)
                    duration = temp_player.duration
                    temp_player.stop()

                    if duration > 12:
                        messagebox.showwarning("Too Long", "Secondary sound must be 12 seconds or shorter.")
                        self.sound_path2 = ""
                    else:
                        self.sound_path2 = path2
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to load secondary sound:\n{e}")
                    self.sound_path2 = ""
            else:
                self.sound_path2 = ""
        else:
            self.sound_path2 = ""

        self.save_current_timer_state()
        self.show_overlay("Alarm sound(s) set!")

    def choose_sound(self):
        """
        Prompts the user to set alarm sounds with specific logic.
        1. Asks for a primary sound.
        2. Asks if a secondary sound is needed.
        3. If no, the primary sound is used for both slots.
        4. If yes, prompts for the secondary sound.
        """
        filetypes = [("Audio Files", "*.wav *.mp3 *.ogg")]
        # Determine initial directory based on current sound path, if it exists
        initial_dir = os.getcwd()
        if self.sound_path1 and os.path.exists(os.path.dirname(self.sound_path1)):
            initial_dir = os.path.dirname(self.sound_path1)

        # 1. Always ask for the primary sound first
        primary_path = filedialog.askopenfilename(
            title="Select PRIMARY Alarm Sound",
            filetypes=filetypes,
            initialdir=initial_dir
        )

        if not primary_path:
            # User cancelled the primary sound selection
            return

        # 2. Ask if the user wants a secondary sound
        use_secondary = messagebox.askyesno(
            "Secondary Sound",
            "Do you need a secondary alarm to be played randomly?"
        )

        if use_secondary:
            # 3. If so, prompt for the secondary sound
            secondary_path = filedialog.askopenfilename(
                title="Select SECONDARY Alarm Sound",
                filetypes=filetypes,
                initialdir=os.path.dirname(primary_path)  # Start in the same folder as the primary
            )

            if not secondary_path:
                messagebox.showwarning(
                    "Selection Cancelled",
                    "You chose to add a secondary sound but didn't select one. The alarm sounds have not been changed."
                )
                return

            # Both paths are valid, assign them
            self.sound_path1 = primary_path
            self.sound_path2 = secondary_path
            message = "Primary & secondary sounds set!"

        else:
            # 4. If No, use the primary sound for both slots
            self.sound_path1 = primary_path
            self.sound_path2 = primary_path  # Set secondary to be the same as primary
            message = "Custom sound set!"

        # Persist the changes for the current timer
        self.save_current_timer_to_memory()
        self.save_current_timer_state()
        self.show_overlay(message)

    def on_note_selection_change(self, event=None):
        """Called when listbox selection changes. Enables/disables buttons."""
        selected_indices = self.notes_listbox.curselection()
        if not selected_indices:
            self.mark_btn.config(state="disabled")
            self.unmark_btn.config(state="disabled")
            return

        note_index = selected_indices[0]
        note = self.notes[note_index]

        if note.completion_type == "Plain Text":
            self.mark_btn.config(state="disabled")
            self.unmark_btn.config(state="disabled")
        else:
            self.mark_btn.config(state="normal")
            self.unmark_btn.config(state="normal")

    def refresh_notes_listbox(self):
        """
        Clears and re-populates the notes listbox.
        Long titles are truncated for display. Tooltips will display long titles.
        """
        self.notes_listbox.delete(0, tk.END)
        for note in self.notes:
            prefix = ""
            suffix = ""
            display_title = note.title

            if note.completion_type == "Checkboxes" and note.completion_data is True:
                prefix = "✓ "
            elif note.completion_type == "Digits/Full Digits":
                if note.completion_data and len(note.completion_data) == 3:
                    current, _, maximum = note.completion_data
                    suffix = f"  [{current}/{maximum}]"

            # Truncate title for display if it's too long
            if len(note.title) > 13:
                display_title = note.title[:13] + "..."

            display_text = f"  {prefix}{display_title}{suffix}"
            self.notes_listbox.insert(tk.END, display_text)

        self.on_note_selection_change()

    def setup_listbox_tooltip(self):
        """Sets up a dynamic tooltip for the notes listbox."""
        self.tooltip = Tooltip(self.notes_listbox, "")  # Creates a tooltip
        self.tooltip.hide_tooltip()  # Hide it initially
        self.notes_listbox.bind("<Motion>", self.update_listbox_tooltip)

    def update_listbox_tooltip(self, event):
        """Shows a tooltip only if the mouse is over a truncated item."""
        # Find the listbox item under the mouse cursor
        index = self.notes_listbox.nearest(event.y)

        # Check if the index is valid and corresponds to a note
        if 0 <= index < len(self.notes):
            note = self.notes[index]
            # Show tooltip if the title is long
            if len(note.title) > 26:
                prefix = "✓ " if note.completion_type == "Checkboxes" and note.completion_data else ""
                suffix = ""
                if note.completion_type == "Digits/Full Digits" and note.completion_data and len(
                        note.completion_data) == 3:
                    suffix = f"  [{note.completion_data[0]}/{note.completion_data[2]}]"

                full_text = f"{prefix}{note.title}{suffix}"

                # If the tooltip text is different, update and show it
                if self.tooltip.text != full_text:
                    self.tooltip.text = full_text
                    self.tooltip.show_tooltip(event)
                return

        # If we are not over a truncated item, hide the tooltip
        self.tooltip.hide_tooltip()
        self.tooltip.text = ""  # Clear the text

    def open_add_note_dialog(self):
        """Opens the NoteEditor window to create a new note."""
        NoteEditor(self)

    def open_edit_note_dialog(self):
        """Opens the NoteEditor to edit the selected note."""
        selected_indices = self.notes_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please select a note from the list to edit.")
            return

        note_index = selected_indices[0]
        note_to_edit = self.notes[note_index]
        NoteEditor(self, note_to_edit=note_to_edit)  # Pass the actual note object

    def delete_selected_note(self):
        """Deletes the currently selected note from the listbox after confirmation."""
        selected_indices = self.notes_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please select a note to delete.")
            return

        note_index = selected_indices[0]
        note_title = self.notes[note_index].title

        if messagebox.askyesno("Confirm Deletion",
                               f"Are you sure you want to permanently delete the note '{note_title}'?"):
            self.delete_note_at_index(note_index)

    def update_existing_note(self, updated_note):
        """Finds an existing note by ID and updates it, also refreshes the UI."""
        for i, note in enumerate(self.notes):
            if note.id == updated_note.id:
                self.notes[i] = updated_note
                break

        self.refresh_notes_listbox()
        self.save_current_timer_to_memory()
        self.save_current_timer_state()

    def add_new_note_to_current_timer(self, note_object):
        """Adds a new note to the current timer's note list and updates the UI."""
        self.notes.append(note_object)
        self.refresh_notes_listbox()
        # Save the change to memory immediately
        self.save_current_timer_to_memory()
        # Also persist to the file
        self.save_current_timer_state()

    def save_config(self):
        if not self.present_path:
            return

        self.config_busy = True
        self.start_btn.config(state='disabled')
        self.pause_btn.config(state='disabled')

        config = configparser.ConfigParser()
        config["TIMER"] = {
            "days": str(self.day_var.get()),
            "hours": str(self.hour_var.get()),
            "minutes": str(self.min_var.get()),
            "seconds": str(self.sec_var.get()),

            "sound1": self.sound_path1 or "",
            "sound2": self.sound_path2 or "",

            "loop": str(self.loop_count if self.loop_count is not None else 1)
        }

        try:
            with open(self.present_path, "w") as f:
                config.write(f)
        except Exception as e:
            print("Failed to save config:", e)

        self.start_btn.config(state='normal')
        self.pause_btn.config(state='normal' if self.timer_running else 'disabled')
        self.config_busy = False

    def load_present_from_file(self, path):
        """Loads the complete state of all 8 timers from a present file."""
        config = configparser.ConfigParser()
        try:
            config.read(path)

            # --- Loop Through and Load All 8 Timers ---
            for i in range(8):
                section = f"TIMER_{i}"
                if not config.has_section(section):
                    continue  # Skip if this timer isn't in the file

                timer_config = config[section]

                # Load basic settings
                title = timer_config.get("title", f"Timer {i + 1}")
                self.timer_switcher.timer_titles[i] = title

                # Load notes by deserializing from JSON
                notes_json = timer_config.get("notes", "[]")
                notes_data = json.loads(notes_json)
                notes_list = [Note.from_dict(data) for data in notes_data]

                # Update the main data store for this timer
                self.all_timers_data[i] = {
                    "days": timer_config.getint("days", 0),
                    "hours": timer_config.getint("hours", 0),
                    "minutes": timer_config.getint("minutes", 0),
                    "seconds": timer_config.getint("seconds", 0),
                    "sound_path1": timer_config.get("sound_path1", ""),
                    "sound_path2": timer_config.get("sound_path2", ""),
                    "loop_count": timer_config.getint("loop_count", 1),
                    "notes": notes_list,
                    # Reset live state variables (might need to remove this)
                    "paused": False,
                    "running": False,
                    "remaining_duration": 0,
                    "pause_time": None,
                    "end_time": None,
                }

            # After loading all data, refresh the UI to show the current timer's state
            self.load_timer_from_memory()
            self.present_path = path
            self.show_overlay("Present loaded!")

        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load present file:\n{e}")

    def new_present(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("New Present")
        dialog.geometry("400x150")
        dialog.configure(bg="#1e1e1e")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        label = tk.Label(dialog, text="Enter name for new present:", font=("Helvetica", 12),
                         bg="#1e1e1e", fg="white")
        label.pack(pady=(20, 5))

        entry = tk.Entry(dialog, font=("Helvetica", 14), bg="#2e2e2e", fg="white", justify="center")
        entry.pack(pady=(0, 10), ipadx=6, ipady=3)

        def create():
            name = entry.get().strip()
            if not name:
                messagebox.showwarning("Name Required", "Please enter a present name.")
                return
            path = filedialog.asksaveasfilename(defaultextension=".ini", initialfile=name,
                                                filetypes=[("INI Files", "*.ini")])
            if path:
                self.present_path = path
                self.save_config()
            dialog.destroy()

        btn = tk.Button(dialog, text="Create", command=create, bg="#211c90", fg="white", font=("Helvetica", 12))
        btn.pack()

    def import_present(self):
        path = filedialog.askopenfilename(
            filetypes=[("INI files", "*.ini")],
            title="Import Present"
        )
        if path:
            self.load_present_from_file(path)

    def save_present(self):
        """Saves the complete state of all 8 timers to a present file."""
        path = self.present_path
        if not path:
            path = filedialog.asksaveasfilename(
                title="Save Present As...",
                defaultextension=".ini",
                filetypes=[("Present Files", "*.ini")]
            )
            if not path:
                return  # User cancelled

        # Before saving, make sure the currently displayed data is synced to memory
        self.save_current_timer_to_memory()

        config = configparser.ConfigParser()

        # --- Save Global Settings (to be continued) ---
        # config["GLOBAL"] = {"version": "1.0"}

        # --- Loop Through and Save All 8 Timers ---
        for i in range(8):
            section = f"TIMER_{i}"
            config[section] = {}
            timer_data = self.all_timers_data[i]

            # Save basic settings
            config[section]["title"] = self.timer_switcher.timer_titles[i]
            config[section]["days"] = str(timer_data.get("days", 0))
            config[section]["hours"] = str(timer_data.get("hours", 0))
            config[section]["minutes"] = str(timer_data.get("minutes", 0))
            config[section]["seconds"] = str(timer_data.get("seconds", 0))
            config[section]["sound_path1"] = timer_data.get("sound_path1", "") or ""
            config[section]["sound_path2"] = timer_data.get("sound_path2", "") or ""
            config[section]["loop_count"] = str(timer_data.get("loop_count", 1))

            # Save notes by serializing to JSON
            notes_list = timer_data.get("notes", [])
            notes_as_dicts = [note.to_dict() for note in notes_list]
            config[section]["notes"] = json.dumps(notes_as_dicts)

        try:
            with open(path, "w") as f:
                config.write(f)
            self.present_path = path
            self.show_overlay("Present saved!")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save present file:\n{e}")

    def delete_present(self):
        path = self.present_path
        if not path:
            path = filedialog.askopenfilename(
                filetypes=[("INI files", "*.ini")],
                title="Delete Present"
            )
            if not path:
                return

        if not os.path.exists(path):
            messagebox.showerror("Error", "File does not exist.")
            return

        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete this present?\n{path}")
        if confirm:
            try:
                os.remove(path)
                if path == self.present_path:
                    self.present_path = None
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete:\n{e}")

    def open_note_viewer(self, event=None):
        """Opens the NoteViewer to the double-clicked selected note."""
        selected_indices = self.notes_listbox.curselection()
        if not selected_indices:
            return

        note_index = selected_indices[0]
        note_to_view = self.notes[note_index]
        NoteViewer(self, note_to_view, note_index)

    def delete_note_at_index(self, index):
        """Deletes a note from the list by its index."""
        if 0 <= index < len(self.notes):
            del self.notes[index]
            self.refresh_notes_listbox()
            self.save_current_timer_to_memory()
            self.save_current_timer_state()

    def move_note(self, index, direction):
        """Moves a note up or down in the list."""
        if direction == "up" and index > 0:
            # Swap with the element above
            self.notes[index], self.notes[index - 1] = self.notes[index - 1], self.notes[index]
            new_index = index - 1
        elif direction == "down" and index < len(self.notes) - 1:
            # Swap with the element below
            self.notes[index], self.notes[index + 1] = self.notes[index + 1], self.notes[index]
            new_index = index + 1
        else:
            return False  # Move was not possible

        self.refresh_notes_listbox()
        # Reselect the moved item for a better user experience
        self.notes_listbox.selection_clear(0, tk.END)
        self.notes_listbox.selection_set(new_index)
        self.notes_listbox.activate(new_index)

        # Save changes
        self.save_current_timer_to_memory()
        self.save_current_timer_state()
        return True  # Move was successful

    def set_loop(self):
        loop_win = tk.Toplevel(self.root)
        loop_win.title("Set Loop Count")
        loop_win.geometry("300x160")
        loop_win.resizable(False, False)  # no resizing
        loop_win.attributes("-toolwindow", True)  # no minimize/maximize

        label = tk.Label(loop_win, text="How many times should the alarm loop?\n(0 = Infinite)", font=("Helvetica", 11),
                         justify="center")
        label.pack(pady=(15, 5))

        loop_var = tk.IntVar(value=self.loop_count if self.loop_count is not None else 1)
        entry = tk.Entry(loop_win, textvariable=loop_var, font=("Helvetica", 12), justify="center", width=10)
        entry.pack(pady=5)
        entry.focus_set()

        def apply():
            try:
                count = int(loop_var.get())
                if count < 0:
                    raise ValueError
                self.loop_count = count
                self.save_config()
                loop_win.destroy()
                # save loops
                self.save_current_timer_to_memory()
                self.save_current_timer_state()
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter a non-negative number.")

        btn_frame = tk.Frame(loop_win)
        btn_frame.pack(pady=10)

        set_btn = tk.Button(btn_frame, text="Set", width=10, command=apply)
        set_btn.grid(row=0, column=0, padx=5)

        exit_btn = tk.Button(btn_frame, text="Exit", width=10, command=loop_win.destroy)
        exit_btn.grid(row=0, column=1, padx=5)

        entry.bind("<Return>", lambda e: apply())
        entry.bind("<Escape>", lambda e: loop_win.destroy())

    def show_overlay(self, message):
        if hasattr(self, 'overlay_frame') and self.overlay_frame:
            self.overlay_frame.destroy()

        self.overlay_frame = tk.Frame(self.root, bg="#222222", bd=2, relief="ridge")
        self.overlay_frame.place(relx=0.5, rely=0.5, anchor="center", width=280, height=80)

        label = tk.Label(self.overlay_frame, text=message, bg="#222222", fg="white", font=("Helvetica", 14))
        label.place(relx=0.5, rely=0.5, anchor="center")

        self.root.after(2000, self.overlay_frame.destroy)

    def try_restore_timer(self):
        # Initialize flags before loop, so we can set them correctly for expired timers.
        self.timer_fired_flags = [False for _ in range(8)]

        if not os.path.exists(self.timer_file):
            return

        config = configparser.ConfigParser()
        try:
            config.read(self.timer_file)

            for timer_id in range(8):
                section_name = f"TIMER {timer_id}"
                if section_name not in config:
                    continue

                timer = config[section_name]

                # Extract state
                running = timer.get("running", "no").lower() == "yes"
                paused = timer.get("paused", "no").lower() == "yes"
                end_time_str = timer.get("end_time", "")
                pause_time_str = timer.get("pause_time", "")
                remaining_seconds = int(timer.get("remaining_seconds", "0"))

                # Convert time strings to datetime objects
                end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S") if end_time_str else None
                pause_time = datetime.strptime(pause_time_str, "%Y-%m-%d %H:%M:%S") if pause_time_str else None

                # Check if a running timer expired while the app was closed.
                if running and end_time and end_time <= datetime.now():
                    running = False
                    paused = False
                    end_time = None
                    pause_time = None
                    remaining_seconds = 0
                    self.timer_fired_flags[timer_id] = True  # Mark as fired to prevent popup on launch.

                # Deserialize notes from JSON
                notes_json = timer.get("notes", "[]")
                notes_data = json.loads(notes_json)
                notes_list = [Note.from_dict(data) for data in notes_data]

                # Store the fully parsed state into our in-memory list.
                self.all_timers_data[timer_id] = {
                    "days": int(timer.get("days", "0")),
                    "hours": int(timer.get("hours", "0")),
                    "minutes": int(timer.get("minutes", "0")),
                    "seconds": int(timer.get("seconds", "0")),
                    "sound_path1": timer.get("sound1", ""),
                    "sound_path2": timer.get("sound2", ""),
                    "loop_count": int(timer.get("loop", "1")),
                    "paused": paused,
                    "running": running,
                    "end_time": end_time,
                    "pause_time": pause_time,
                    "remaining_duration": remaining_seconds,  # Stored as seconds
                    "notes": notes_list,
                }

                self.timer_switcher.timer_titles[timer_id] = timer.get("title", f"Timer {timer_id + 1}")

            # After restoring all timers into memory, reset UI.
            self.load_timer_from_memory()

        except Exception as e:
            print(f"Failed to restore timers from '{self.timer_file}': {e}")

    def display_remaining_time(self, remaining=None):
        if remaining is None:
            if self.paused:
                remaining = self.remaining_duration
            else:
                remaining = self.end_time - datetime.now()

        total_seconds = int(remaining.total_seconds())
        weeks, seconds = divmod(total_seconds, 7 * 86400)
        days, seconds = divmod(seconds, 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)

        if weeks > 0:
            main_text = f"{hours:02}:{minutes:02}:{seconds:02}"
            extra_text = f"{weeks:02}:{days:02}"
            self.update_timer_canvas(main_text, extra_text, color_main="#43e97a", color_extra="#57b4e5")
        elif days > 0:
            main_text = f"{hours:02}:{minutes:02}:{seconds:02}"
            extra_text = f"{days:02}"
            self.update_timer_canvas(main_text, extra_text, color_main="#43e97a", color_extra="#6457e5")
        else:
            time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
            self.update_timer_canvas(time_str, color_main="#43e97a")

    def save_current_timer_state(self):
        # First, ensure the data for the currently active UI is synced to our in-memory.
        self.save_current_timer_to_memory()

        # Block UI to prevent changes during the save operation. Yes I hear you Son Of a Glitch.
        self.config_busy = True
        self.start_btn.config(state='disabled')
        self.pause_btn.config(state='disabled')

        config = configparser.ConfigParser()

        # Iterate through all 8 timers' data stored in memory and build the config.
        for i in range(8):
            timer_data = self.all_timers_data[i]
            section_name = f"TIMER {i}"
            config[section_name] = {}

            # Save the base duration settings
            config[section_name]["days"] = str(timer_data.get("days", 0))
            config[section_name]["hours"] = str(timer_data.get("hours", 0))
            config[section_name]["minutes"] = str(timer_data.get("minutes", 0))
            config[section_name]["seconds"] = str(timer_data.get("seconds", 0))

            # Save metadata and sounds
            config[section_name]["title"] = self.timer_switcher.timer_titles[i]
            config[section_name]["sound1"] = timer_data.get("sound_path1", "") or ""
            config[section_name]["sound2"] = timer_data.get("sound_path2", "") or ""
            config[section_name]["loop"] = str(timer_data.get("loop_count", 1))

            # Serialize the notes list into a JSON string
            notes_list = timer_data.get("notes", [])
            notes_as_dicts = [note.to_dict() for note in notes_list]
            config[section_name]["notes"] = json.dumps(notes_as_dicts)

            # Save the dynamic running/paused state
            is_running = timer_data.get("running", False)
            is_paused = timer_data.get("paused", False)
            config[section_name]["running"] = "yes" if is_running else "no"
            config[section_name]["paused"] = "yes" if is_paused else "no"

            if is_running:
                end_time = timer_data.get("end_time")
                pause_time = timer_data.get("pause_time")

                if end_time:
                    config[section_name]["end_time"] = end_time.strftime("%Y-%m-%d %H:%M:%S")

                if is_paused and pause_time:
                    config[section_name]["pause_time"] = pause_time.strftime("%Y-%m-%d %H:%M:%S")

                # Accurately determine the remaining seconds to save
                remaining_secs = 0
                if is_paused:
                    # When paused, the saved duration (in seconds) is authoritative.
                    remaining_secs = timer_data.get("remaining_duration", 0)
                elif end_time:
                    # When actively running, calculate remaining time from now.
                    remaining_secs = max(0, (end_time - datetime.now()).total_seconds())

                config[section_name]["remaining_seconds"] = str(int(remaining_secs))

        try:
            # Write the complete configuration for all 8 timers to the file.
            with open(self.timer_file, "w") as f:
                config.write(f)
        except Exception as e:
            print(f"Failed to save state for all timers to '{self.timer_file}': {e}")
        finally:
            # Restore UI button states based on the currently displayed timer.
            self.start_btn.config(state='normal')
            self.pause_btn.config(state='normal' if self.timer_running else 'disabled')
            self.config_busy = False

    def switch_timer(self, timer_id):
        self.save_current_timer_to_memory()  # Save current one first
        self.current_timer_id = timer_id  # Switch ID
        self.load_timer_from_memory()  # Load new one

    def save_current_timer_to_memory(self):
        self.all_timers_data[self.current_timer_id] = {
            "days": self.day_var.get(),
            "hours": self.hour_var.get(),
            "minutes": self.min_var.get(),
            "seconds": self.sec_var.get(),
            "paused": self.paused,
            "running": self.timer_running,
            "remaining_duration": self.remaining_duration.total_seconds() if self.remaining_duration else 0,
            "pause_time": self.pause_time,
            "end_time": self.end_time,
            "sound_path1": self.sound_path1,
            "sound_path2": self.sound_path2,
            "loop_count": self.loop_count,
            "notes": self.notes,
        }

    def load_timer_from_memory(self):
        data = self.all_timers_data[self.current_timer_id]

        self.day_var.set(data.get("days", 0))
        self.hour_var.set(data.get("hours", 0))
        self.min_var.set(data.get("minutes", 0))
        self.sec_var.set(data.get("seconds", 0))

        self.paused = data.get("paused", False)
        self.timer_running = data.get("running", False)
        remaining_secs = data.get("remaining_duration", 0)
        self.remaining_duration = timedelta(seconds=remaining_secs) if remaining_secs else None

        self.pause_time = data.get("pause_time", None)
        self.end_time = data.get("end_time", None)

        self.sound_path1 = data.get("sound_path1", "")
        self.sound_path2 = data.get("sound_path2", "")
        self.loop_count = data.get("loop_count", 1)

        self.notes = data.get("notes", [])
        self.refresh_notes_listbox()

        # Re-sync title entry
        self.timer_switcher.title_var.set(self.timer_switcher.timer_titles[self.current_timer_id])

        self.update_timer_canvas("00:00:00", color_main="white")
        self.start_btn.config(text="Start", state="normal")
        self.pause_btn.config(state='disabled')
        self.update_check.config(state='disabled')
        self.update_timer_var.set(False)
        self.enable_spinboxes()

        if self.timer_running:
            if self.paused:
                self.start_btn.config(text='Stop', state='normal')
                self.pause_btn.config(text='Resume', state='normal')
                self.update_check.config(state='normal')
                self.display_remaining_time()
                self.handle_pause_flash()
            else:
                self.start_btn.config(text='Stop', state='normal')
                self.pause_btn.config(text='Pause', state='normal')
                self.disable_spinboxes()
                self.update_check.config(state='disabled')
                self.update_timer_var.set(False)
                self.display_remaining_time()
                self.update_timer()

        self.timer_fired_flags[self.current_timer_id] = False

    def store_timer_to_memory(self):
        self.all_timers_data[self.current_timer_id] = {
            "days": self.day_var.get(),
            "hours": self.hour_var.get(),
            "minutes": self.min_var.get(),
            "seconds": self.sec_var.get(),
            "paused": self.paused,
            "running": self.timer_running,
            "remaining_duration": int(self.remaining_duration.total_seconds()) if self.remaining_duration else 0,
            "pause_time": self.pause_time,
            "end_time": self.end_time,
            "sound_path1": self.sound_path1,
            "sound_path2": self.sound_path2,
            "loop_count": self.loop_count,
        }


if __name__ == "__main__":
    root = tk.Tk()
    app = TimerApp(root)

    def on_closing():
        app.save_current_timer_state()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()