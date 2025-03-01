import tkinter as tk
from tkinter import ttk
import pyautogui
import win32gui
import win32api
import win32con


class LaptopKeyboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Professional Laptop Keyboard")
        self.root.geometry("1200x450")
        self.root.attributes('-topmost', True)  # Keep the keyboard on top
        self.root.configure(bg='#1e1e1e')
        self.root.resizable(False, False)

        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Color scheme
        self.bg_color = '#1e1e1e'
        self.button_bg = '#2d2d2d'
        self.button_fg = '#ffffff'
        self.button_en = '#008000'
        self.special_button_bg = '#007acc'
        self.function_button_bg = '#444444'
        self.danger_button_bg = '#d9534f'  # Red color for backspace
        self.hover_color = '#696969'
        self.display_bg = '#252526'
        self.display_fg = '#00ff00'

        # Configure styles
        self.style.configure('TButton',
                             font=('Arial', 12, 'bold'),
                             borderwidth=2,
                             relief='flat',
                             background=self.button_bg,
                             foreground=self.button_fg)

        self.style.map('TButton',
                       background=[('active', self.hover_color)],
                       foreground=[('active', self.button_fg)])

        self.style.configure('Special.TButton',
                             background=self.special_button_bg,
                             foreground='white')

        self.style.configure('Function.TButton',
                             background=self.function_button_bg,
                             foreground='white',
                             font=('Arial', 10, 'bold'))

        self.style.configure('Entry.TButton',
                             background=self.special_button_bg,
                             foreground='white')

        self.style.configure('Enter.TButton',
                             background=self.button_en,
                             foreground='white')

        self.style.configure('Danger.TButton',  # Style for backspace
                             background=self.danger_button_bg,
                             foreground='white')

        self.style.configure('Display.TEntry',
                             font=('Arial', 20),
                             fieldbackground=self.display_bg,
                             foreground=self.display_fg,
                             padding=10,
                             borderwidth=3,
                             relief='sunken')

        # Variables to track keyboard state
        self.last_caret_pos = pyautogui.position()
        self.previous_window = win32gui.GetForegroundWindow()
        self.caps_lock_on = False
        self.num_lock_on = True
        self.fn_mode = False
        self.shift_pressed = False
        self.is_dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0

        # Create UI components
        self.create_display()
        self.create_keyboard()

        # Bind mouse events to track clicks and update caret position
        self.root.bind("<Button-1>", self.start_drag)
        self.root.bind("<B1-Motion>", self.drag_window)

        # Periodically track mouse clicks outside the keyboard
        self.root.after(100, self.track_mouse_clicks)

    def track_mouse_clicks(self):
        """
        Dynamically track the most recent mouse click position
        and store it as the current caret position.
        """
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd != self.get_hwnd():  # Ensure the click is outside the keyboard
                self.last_caret_pos = pyautogui.position()  # Update the caret position
                self.previous_window = hwnd  # Update the active window
        except Exception as e:
            print(f"Error tracking mouse clicks: {e}")
        finally:
            # Continue tracking
            self.root.after(100, self.track_mouse_clicks)

    def get_hwnd(self):
        """Get the window handle for the on-screen keyboard."""
        return win32gui.FindWindow(None, self.root.title())

    def create_display(self):
        """Create the display area for the keyboard."""
        display_frame = ttk.Frame(self.root)
        display_frame.pack(fill="x", pady=(10, 10), padx=20)

        self.display_var = tk.StringVar()

        self.display = ttk.Entry(
            display_frame,
            textvariable=self.display_var,
            style='Display.TEntry',
            justify="center",
            state="readonly"
        )
        self.display.pack(fill="x")

    def create_keyboard(self):
        """Create the laptop-style on-screen keyboard."""
        keyboard_frame = ttk.Frame(self.root)
        keyboard_frame.pack(expand=True, fill="both", padx=10, pady=5)

        # Function keys row
        function_row = ttk.Frame(keyboard_frame)
        function_row.pack(expand=True, fill="both", pady=2)

        # Escape key
        esc_button = ttk.Button(
            function_row,
            text='Esc',
            style='Function.TButton',
            width=3,
            command=lambda: self.handle_key('escape')
        )
        esc_button.pack(side="left", expand=True, fill="both", padx=1)

        # Function keys F1-F12
        for i in range(1, 13):
            function_key = ttk.Button(
                function_row,
                text=f'F{i}',
                style='Function.TButton',
                width=3,
                command=lambda k=i: self.handle_key(f'f{k}')
            )
            function_key.pack(side="left", expand=True, fill="both", padx=1)

        # Add extra function keys typically found on laptops
        special_function_keys = [
            ('Print\nScreen', 'print_screen'),
            ('Scroll\nLock', 'scroll_lock'),
            ('Pause\nBreak', 'pause')
        ]
        for label, key in special_function_keys:
            btn = ttk.Button(
                function_row,
                text=label,
                style='Function.TButton',
                width=3,
                command=lambda k=key: self.handle_key(k)
            )
            btn.pack(side="left", expand=True, fill="both", padx=1)

        # Number row with symbols
        number_row_frame = ttk.Frame(keyboard_frame)
        number_row_frame.pack(expand=True, fill="both", pady=2)

        # Add the backtick/tilde key
        tilde_button = ttk.Button(
            number_row_frame,
            text='`\n~',
            style='TButton',
            width=3,
            command=lambda: self.handle_key('`' if not self.shift_pressed else '~')
        )
        tilde_button.pack(side="left", expand=True, fill="both", padx=1)

        # Number row with symbols
        number_symbols = [
            ('1', '!'), ('2', '@'), ('3', '#'), ('4', '$'),
            ('5', '%'), ('6', '^'), ('7', '&'), ('8', '*'),
            ('9', '('), ('0', ')'), ('-', '_'), ('=', '+')
        ]

        for num, symbol in number_symbols:
            btn = ttk.Button(
                number_row_frame,
                text=f'{num}\n{symbol}',
                style='TButton',
                width=3,
                command=lambda n=num, s=symbol: self.handle_key(s if self.shift_pressed else n)
            )
            btn.pack(side="left", expand=True, fill="both", padx=1)

        # Add the Backspace button
        backspace_button = ttk.Button(
            number_row_frame,
            text='Backspace',
            style='Danger.TButton',
            width=8,
            command=lambda: self.handle_key('⌫')
        )
        backspace_button.pack(side="left", expand=True, fill="both", padx=1)

        # Add Insert, Home, Page Up
        for key, text in [('insert', 'Insert'), ('home', 'Home'), ('page_up', 'Page\nUp')]:
            btn = ttk.Button(
                number_row_frame,
                text=text,
                style='Special.TButton',
                width=3,
                command=lambda k=key: self.handle_key(k)
            )
            btn.pack(side="left", expand=True, fill="both", padx=1)

        # QWERTY row
        qwerty_row_frame = ttk.Frame(keyboard_frame)
        qwerty_row_frame.pack(expand=True, fill="both", pady=2)

        # Tab key
        tab_button = ttk.Button(
            qwerty_row_frame,
            text='Tab',
            style='Special.TButton',
            width=4,
            command=lambda: self.handle_key('tab')
        )
        tab_button.pack(side="left", expand=True, fill="both", padx=1)

        # QWERTY keys
        qwerty_keys = ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P']
        for key in qwerty_keys:
            btn = ttk.Button(
                qwerty_row_frame,
                text=key,
                style='TButton',
                width=3,
                command=lambda k=key: self.handle_key(k)
            )
            btn.pack(side="left", expand=True, fill="both", padx=1)

        # Bracket keys
        bracket_keys = [
            ('[', '{'), (']', '}'), ('\\', '|')
        ]
        for key, shift_key in bracket_keys:
            btn = ttk.Button(
                qwerty_row_frame,
                text=f'{key}\n{shift_key}',
                style='TButton',
                width=3,
                command=lambda k=key, sk=shift_key: self.handle_key(sk if self.shift_pressed else k)
            )
            btn.pack(side="left", expand=True, fill="both", padx=1)

        # Add Delete, End, Page Down
        for key, text in [('delete', 'Delete'), ('end', 'End'), ('page_down', 'Page\nDown')]:
            btn = ttk.Button(
                qwerty_row_frame,
                text=text,
                style='Special.TButton',
                width=3,
                command=lambda k=key: self.handle_key(k)
            )
            btn.pack(side="left", expand=True, fill="both", padx=1)

        # ASDF row
        asdf_row_frame = ttk.Frame(keyboard_frame)
        asdf_row_frame.pack(expand=True, fill="both", pady=2)

        # Caps Lock key
        caps_button = ttk.Button(
            asdf_row_frame,
            text='Caps Lock',
            style='Special.TButton',
            width=6,
            command=lambda: self.handle_key('Caps')
        )
        caps_button.pack(side="left", expand=True, fill="both", padx=1)

        # ASDF keys
        asdf_keys = ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L']
        for key in asdf_keys:
            btn = ttk.Button(
                asdf_row_frame,
                text=key,
                style='TButton',
                width=3,
                command=lambda k=key: self.handle_key(k)
            )
            btn.pack(side="left", expand=True, fill="both", padx=1)

        # Semicolon and quotes
        semicolon_button = ttk.Button(
            asdf_row_frame,
            text=';\n:',
            style='TButton',
            width=3,
            command=lambda: self.handle_key(':' if self.shift_pressed else ';')
        )
        semicolon_button.pack(side="left", expand=True, fill="both", padx=1)

        quotes_button = ttk.Button(
            asdf_row_frame,
            text="'\n\"",
            style='TButton',
            width=3,
            command=lambda: self.handle_key('"' if self.shift_pressed else "'")
        )
        quotes_button.pack(side="left", expand=True, fill="both", padx=1)

        # Enter key
        enter_button = ttk.Button(
            asdf_row_frame,
            text='Enter',
            style='Enter.TButton',
            width=5,
            command=lambda: self.handle_key('Enter')
        )
        enter_button.pack(side="left", expand=True, fill="both", padx=1)

        # ZXCV row
        zxcv_row_frame = ttk.Frame(keyboard_frame)
        zxcv_row_frame.pack(expand=True, fill="both", pady=2)

        # Shift keys
        left_shift_button = ttk.Button(
            zxcv_row_frame,
            text='Shift',
            style='Special.TButton',
            width=7,
            command=lambda: self.toggle_shift()
        )
        left_shift_button.pack(side="left", expand=True, fill="both", padx=1)

        # ZXCV keys
        zxcv_keys = ['Z', 'X', 'C', 'V', 'B', 'N', 'M']
        for key in zxcv_keys:
            btn = ttk.Button(
                zxcv_row_frame,
                text=key,
                style='TButton',
                width=3,
                command=lambda k=key: self.handle_key(k)
            )
            btn.pack(side="left", expand=True, fill="both", padx=1)

        # Comma, period, slash
        punctuation_keys = [
            (',', '<'), ('.', '>'), ('/', '?')
        ]
        for key, shift_key in punctuation_keys:
            btn = ttk.Button(
                zxcv_row_frame,
                text=f'{key}\n{shift_key}',
                style='TButton',
                width=3,
                command=lambda k=key, sk=shift_key: self.handle_key(sk if self.shift_pressed else k)
            )
            btn.pack(side="left", expand=True, fill="both", padx=1)

        right_shift_button = ttk.Button(
            zxcv_row_frame,
            text='Shift',
            style='Special.TButton',
            width=7,
            command=lambda: self.toggle_shift()
        )
        right_shift_button.pack(side="left", expand=True, fill="both", padx=1)

        # Arrow up button
        up_button = ttk.Button(
            zxcv_row_frame,
            text='↑',
            style='Special.TButton',
            width=3,
            command=lambda: self.handle_key('Up')
        )
        up_button.pack(side="left", expand=True, fill="both", padx=1)

        # Bottom row (CTRL, ALT, Space, etc.)
        bottom_row_frame = ttk.Frame(keyboard_frame)
        bottom_row_frame.pack(expand=True, fill="both", pady=2)

        # Modifier keys
        modifier_keys = [
            ('Ctrl', 'ctrl'), ('Win', 'win'), ('Alt', 'alt')
        ]
        for text, key in modifier_keys:
            btn = ttk.Button(
                bottom_row_frame,
                text=text,
                style='Special.TButton',
                width=3,
                command=lambda k=key: self.handle_key(k)
            )
            btn.pack(side="left", expand=True, fill="both", padx=1)

        # Space bar
        space_button = ttk.Button(
            bottom_row_frame,
            text='Space',
            style='TButton',
            width=25,
            command=lambda: self.handle_key('Space')
        )
        space_button.pack(side="left", expand=True, fill="both", padx=1)

        # Right modifier keys
        right_modifier_keys = [
            ('Alt', 'alt'), ('Fn', 'fn'), ('Menu', 'apps'), ('Ctrl', 'ctrl')
        ]
        for text, key in right_modifier_keys:
            btn = ttk.Button(
                bottom_row_frame,
                text=text,
                style='Special.TButton',
                width=3,
                command=lambda k=key: self.handle_key(k)
            )
            btn.pack(side="left", expand=True, fill="both", padx=1)

        # Arrow keys
        arrow_keys = [
            ('←', 'Left'), ('↓', 'Down'), ('→', 'Right')
        ]
        for symbol, key in arrow_keys:
            btn = ttk.Button(
                bottom_row_frame,
                text=symbol,
                style='Special.TButton',
                width=3,
                command=lambda k=key: self.handle_key(k)
            )
            btn.pack(side="left", expand=True, fill="both", padx=1)

    def toggle_shift(self):
        """Toggle the shift key state."""
        self.shift_pressed = not self.shift_pressed
        # Update the display to show shift is active/inactive
        if self.shift_pressed:
            self.display_var.set("Shift: ON")
        else:
            self.display_var.set("Shift: OFF")

    def handle_key(self, key):
        """Handle keypresses and simulate typing at the caret position."""
        current = self.display_var.get()

        # Restore focus to the last clicked window
        win32gui.SetForegroundWindow(self.previous_window)

        if key == '⌫':
            self.display_var.set(current[:-1] if current else "")  # Remove last character
            pyautogui.press('backspace')  # Simulate backspace
        elif key == 'Enter':
            pyautogui.press('enter')  # Simulate Enter key
            self.display_var.set('')  # Clear display
        elif key == 'Caps':
            self.caps_lock_on = not self.caps_lock_on  # Toggle Caps Lock
            self.display_var.set(f"Caps Lock: {'ON' if self.caps_lock_on else 'OFF'}")
        elif key == 'Space':
            self.display_var.set(current + ' ')  # Add space to display
            pyautogui.press('space')  # Simulate space
        elif key == 'tab':
            pyautogui.press('tab')  # Simulate tab key
            self.display_var.set(current + '    ')  # Visual representation of tab
        elif key in ['escape', 'print_screen', 'scroll_lock', 'pause', 'insert',
                     'home', 'page_up', 'delete', 'end', 'page_down']:
            pyautogui.press(key)  # Simulate the key press
            self.display_var.set(f"Pressed: {key}")
        elif key.startswith('f') and key[1:].isdigit():
            # Handle function keys F1-F12
            pyautogui.press(key)
            self.display_var.set(f"Pressed: {key.upper()}")
        elif key in ['ctrl', 'alt', 'win', 'apps', 'fn']:
            # For modifier keys, just show status
            self.display_var.set(f"Pressed: {key}")
            if key != 'fn':  # fn is not a real key in pyautogui
                pyautogui.keyDown(key)
                pyautogui.keyUp(key)
        elif key in ['Up', 'Down', 'Left', 'Right']:
            pyautogui.press(key.lower())  # Simulate arrow key
            self.display_var.set(f"Pressed: {key} Arrow")
        else:
            # Handle regular keys
            if self.caps_lock_on and key.isalpha():
                char = key.upper()
            elif self.shift_pressed and key.isalpha():
                char = key.upper() if key.islower() else key.lower()
            else:
                char = key.lower() if key.isalpha() else key

            self.display_var.set(current + char)  # Add character to display
            pyautogui.write(char)  # Simulate typing

            # Turn off shift after a single key press
            if self.shift_pressed:
                self.shift_pressed = False
                self.display_var.set(f"Shift: OFF")

    def start_drag(self, event):
        """Initiates dragging."""
        self.is_dragging = True
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def drag_window(self, event):
        """Moves the window while dragging."""
        if self.is_dragging:
            x = self.root.winfo_x() - self.drag_start_x + event.x
            y = self.root.winfo_y() - self.drag_start_y + event.y
            self.root.geometry(f"+{x}+{y}")


if __name__ == "__main__":
    root = tk.Tk()
    app = LaptopKeyboard(root)
    root.mainloop()