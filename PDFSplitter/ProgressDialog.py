import tkinter as tk
from tkinter import ttk


class ProgressDialog:
    """Enhanced progress dialog with better text display and cancel support"""
    
    def __init__(self, parent, title="Processing", message="Operation in progress..."):
        """Create a progress dialog with a progress bar and cancel button"""
        self.dialog = tk.Toplevel(parent)
        self.title = title
        self.dialog.title(title)
        self.dialog.geometry("500x250")  # Adjusted height to accommodate additional message
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Flag to track cancellation
        self.cancelled = False
        
        # Configure to be non-resizable
        self.dialog.resizable(False, False)
        
        # Center dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        # Create main frame with padding
        main_frame = ttk.Frame(self.dialog, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create message label
        self.message_var = tk.StringVar(value=message)
        self.message_label = ttk.Label(main_frame, textvariable=self.message_var, wraplength=420)
        self.message_label.pack(pady=(0, 15), anchor="w")
        
        # Create progress bar
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            main_frame, 
            orient=tk.HORIZONTAL, 
            length=420, 
            mode='determinate',
            variable=self.progress_var
        )
        self.progress_bar.pack(pady=5)
        
        # Create status label with fixed height to prevent layout changes
        status_frame = ttk.Frame(main_frame, height=40)
        status_frame.pack(fill=tk.X, pady=5)
        status_frame.pack_propagate(False)  # Maintain fixed height
        
        self.status_var = tk.StringVar(value="")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.pack(anchor="w")
        
        # Create secondary message label
        self.secondary_message_var = tk.StringVar(value="")
        self.secondary_message_label = ttk.Label(main_frame, textvariable=self.secondary_message_var, wraplength=420)
        self.secondary_message_label.pack(pady=(0, 15), anchor="w")
        
        # Create time remaining label with fixed height
        time_frame = ttk.Frame(main_frame, height=25)
        time_frame.pack(fill=tk.X)
        time_frame.pack_propagate(False)  # Maintain fixed height
        
        self.time_var = tk.StringVar(value="")
        self.time_label = ttk.Label(time_frame, textvariable=self.time_var)
        self.time_label.pack(anchor="w")
        
        # Create cancel button
        self.cancel_button = ttk.Button(main_frame, text="Cancel", command=self.cancel)
        self.cancel_button.pack(pady=(10, 0))
        
        # Update UI
        self.dialog.update()
        
        # Setup protocol for window close
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)

    def update_progress(self, value, maximum=100):
        """Update progress bar value and title"""
        if self.cancelled:
            return
        percentage = (value / maximum) * 100
        self.progress_var.set(percentage)
        self.dialog.title(self.title + f" - {percentage:.2f}% done")
        self.dialog.update()
        
    def update_message(self, message):
        """Update the message text"""
        if self.cancelled:
            return
        self.message_var.set(message)
        self.dialog.update()
        
    def update_secondary_message(self, message):
        """Update the secondary message text"""
        if self.cancelled:
            return
        print(f"Updating secondary message: {message}")  # Debug print
        self.secondary_message_var.set(message)
        self.dialog.update()
        
    def update_status(self, status):
        """Update the status text"""
        if self.cancelled:
            return
        self.status_var.set(status)
        self.dialog.update()
        
    def update_time_remaining(self, time_text):
        """Update the time remaining text"""
        if self.cancelled:
            return
        self.time_var.set(f"Estimated time remaining: {time_text}")
        self.dialog.update()
        
    def cancel(self):
        """Handle cancellation request"""
        self.cancelled = True
        self.status_var.set("Cancelling...")
        self.cancel_button.configure(state="disabled")
        self.dialog.update()
    
    def close(self):
        """Close the progress dialog"""
        self.dialog.destroy()
        
    def is_cancelled(self):
        """Check if operation was cancelled"""
        return self.cancelled
    
class DualProgressDialog:
    """Enhanced dual progress dialog with better text display and cancel support"""
    
    def __init__(self, parent, title="Processing", message="Operation in progress..."):
        """Create a progress dialog with two progress bars"""
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.title = title
        self.dialog.geometry("500x340")  # Adjusted height to accommodate additional message
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Flag to track cancellation
        self.cancelled = False
        
        # Configure to be non-resizable
        self.dialog.resizable(False, False)
        
        # Center dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        # Create main frame with padding
        main_frame = ttk.Frame(self.dialog, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create message label
        self.message_var = tk.StringVar(value=message)
        self.message_label = ttk.Label(main_frame, textvariable=self.message_var, wraplength=470)
        self.message_label.pack(pady=(0, 10), anchor="w")
        
        # Time remaining label with fixed height
        time_frame = ttk.Frame(main_frame, height=25)
        time_frame.pack(fill=tk.X)
        time_frame.pack_propagate(False)
        
        self.time_var = tk.StringVar(value="")
        self.time_label = ttk.Label(time_frame, textvariable=self.time_var)
        self.time_label.pack(anchor="w")
        
        # Create overall progress section
        overall_frame = ttk.LabelFrame(main_frame, text="Overall Progress")
        overall_frame.pack(fill=tk.X, pady=5)
        
        self.overall_progress_var = tk.DoubleVar(value=0)
        self.overall_progress_bar = ttk.Progressbar(
            overall_frame, 
            orient=tk.HORIZONTAL, 
            length=460, 
            mode='determinate',
            variable=self.overall_progress_var
        )
        self.overall_progress_bar.pack(pady=5, padx=5)
        
        # Overall status with fixed height
        overall_status_frame = ttk.Frame(overall_frame, height=25)
        overall_status_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        overall_status_frame.pack_propagate(False)
        
        self.overall_status_var = tk.StringVar(value="")
        self.overall_status_label = ttk.Label(overall_status_frame, textvariable=self.overall_status_var)
        self.overall_status_label.pack(anchor="w")
        
        # Create current item progress section
        current_frame = ttk.LabelFrame(main_frame, text="Current File Progress")
        current_frame.pack(fill=tk.X, pady=5)
        
        self.current_progress_var = tk.DoubleVar(value=0)
        self.current_progress_bar = ttk.Progressbar(
            current_frame, 
            orient=tk.HORIZONTAL, 
            length=460, 
            mode='determinate',
            variable=self.current_progress_var
        )
        self.current_progress_bar.pack(pady=5, padx=5)
        
        # Current status with fixed height
        current_status_frame = ttk.Frame(current_frame, height=25)
        current_status_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        current_status_frame.pack_propagate(False)
        
        self.current_status_var = tk.StringVar(value="")
        self.current_status_label = ttk.Label(current_status_frame, textvariable=self.current_status_var)
        self.current_status_label.pack(anchor="w")
        
        # Additional message spot
        self.additional_message_var = tk.StringVar(value="")
        self.additional_message_label = ttk.Label(main_frame, textvariable=self.additional_message_var, wraplength=470)
        self.additional_message_label.pack(pady=(10, 0), anchor="w")
        
        # Create cancel button
        self.cancel_button = ttk.Button(main_frame, text="Cancel", command=self.cancel)
        self.cancel_button.pack(pady=(10, 0))
        
        # Update UI
        self.dialog.update()
        
        # Setup protocol for window close
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)

    def update_overall_progress(self, value, maximum=100):
        """Update overall progress bar value and title"""
        if self.cancelled:
            return
        percentage = (value / maximum) * 100
        self.overall_progress_var.set(percentage)
        self.dialog.title(self.title + f" - {percentage:.2f}% done")
        self.dialog.update()
        
    def update_current_progress(self, value, maximum=100):
        """Update current item progress bar value"""
        if self.cancelled:
            return
        self.current_progress_var.set((value / maximum) * 100)
        self.dialog.update()
        
    def update_message(self, message):
        """Update the main message text"""
        if self.cancelled:
            return
        self.message_var.set(message)
        self.dialog.update()
        
    def update_time_remaining(self, time_text):
        """Update the time remaining text"""
        if self.cancelled:
            return
        self.time_var.set(f"Estimated time remaining: {time_text}")
        self.dialog.update()
        
    def update_overall_status(self, status):
        """Update the overall status text"""
        if self.cancelled:
            return
        self.overall_status_var.set(status)
        self.dialog.update()
        
    def update_current_status(self, status):
        """Update the current item status text"""
        if self.cancelled:
            return
        self.current_status_var.set(status)
        self.dialog.update()
        
    def update_additional_message(self, message):
        """Update the additional message text"""
        if self.cancelled:
            return
        self.additional_message_var.set(message)
        self.dialog.update()
        
    def reset_current_progress(self):
        """Reset the current progress bar to zero"""
        if self.cancelled:
            return
        self.current_progress_var.set(0)
        self.current_status_var.set("")
        self.dialog.update()
        
    def cancel(self):
        """Handle cancellation request"""
        self.cancelled = True
        self.overall_status_var.set("Cancelling...")
        self.cancel_button.configure(state="disabled")
        self.dialog.update()
    
    def close(self):
        """Close the progress dialog"""
        self.dialog.destroy()
        
    def is_cancelled(self):
        """Check if operation was cancelled"""
        return self.cancelled
    
class TripleProgressDialog:
    """Enhanced triple progress dialog with better text display and cancel support"""
    
    def __init__(self, parent, title="Processing", message="Operation in progress..."):
        """Create a progress dialog with three progress bars"""
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.title = title
        self.dialog.geometry("500x400")  # Adjusted height to accommodate additional message
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Flag to track cancellation
        self.cancelled = False
        
        # Configure to be non-resizable
        self.dialog.resizable(False, False)
        
        # Center dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        # Create main frame with padding
        main_frame = ttk.Frame(self.dialog, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create message label
        self.message_var = tk.StringVar(value=message)
        self.message_label = ttk.Label(main_frame, textvariable=self.message_var, wraplength=470)
        self.message_label.pack(pady=(0, 10), anchor="w")
        
        # Time remaining label with fixed height
        time_frame = ttk.Frame(main_frame, height=25)
        time_frame.pack(fill=tk.X)
        time_frame.pack_propagate(False)
        
        self.time_var = tk.StringVar(value="")
        self.time_label = ttk.Label(time_frame, textvariable=self.time_var)
        self.time_label.pack(anchor="w")
        
        # Create overall progress section
        overall_frame = ttk.LabelFrame(main_frame, text="Overall Progress")
        overall_frame.pack(fill=tk.X, pady=5)
        
        self.overall_progress_var = tk.DoubleVar(value=0)
        self.overall_progress_bar = ttk.Progressbar(
            overall_frame, 
            orient=tk.HORIZONTAL, 
            length=460, 
            mode='determinate',
            variable=self.overall_progress_var
        )
        self.overall_progress_bar.pack(pady=5, padx=5)
        
        # Overall status with fixed height
        overall_status_frame = ttk.Frame(overall_frame, height=25)
        overall_status_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        overall_status_frame.pack_propagate(False)
        
        self.overall_status_var = tk.StringVar(value="")
        self.overall_status_label = ttk.Label(overall_status_frame, textvariable=self.overall_status_var)
        self.overall_status_label.pack(anchor="w")
        
        # Create current item progress section
        current_frame = ttk.LabelFrame(main_frame, text="Current File Progress")
        current_frame.pack(fill=tk.X, pady=5)
        
        self.current_progress_var = tk.DoubleVar(value=0)
        self.current_progress_bar = ttk.Progressbar(
            current_frame, 
            orient=tk.HORIZONTAL, 
            length=460, 
            mode='determinate',
            variable=self.current_progress_var
        )
        self.current_progress_bar.pack(pady=5, padx=5)
        
        # Current status with fixed height
        current_status_frame = ttk.Frame(current_frame, height=25)
        current_status_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        current_status_frame.pack_propagate(False)
        
        self.current_status_var = tk.StringVar(value="")
        self.current_status_label = ttk.Label(current_status_frame, textvariable=self.current_status_var)
        self.current_status_label.pack(anchor="w")
        
        # Create secondary progress section
        secondary_frame = ttk.LabelFrame(main_frame, text="Secondary Progress")
        secondary_frame.pack(fill=tk.X, pady=5)
        
        self.secondary_progress_var = tk.DoubleVar(value=0)
        self.secondary_progress_bar = ttk.Progressbar(
            secondary_frame, 
            orient=tk.HORIZONTAL, 
            length=460, 
            mode='determinate',
            variable=self.secondary_progress_var
        )
        self.secondary_progress_bar.pack(pady=5, padx=5)
        
        # Secondary status with fixed height
        secondary_status_frame = ttk.Frame(secondary_frame, height=25)
        secondary_status_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        secondary_status_frame.pack_propagate(False)
        
        self.secondary_status_var = tk.StringVar(value="")
        self.secondary_status_label = ttk.Label(secondary_status_frame, textvariable=self.secondary_status_var)
        self.secondary_status_label.pack(anchor="w")
        
        # Additional message spot
        self.additional_message_var = tk.StringVar(value="")
        self.additional_message_label = ttk.Label(main_frame, textvariable=self.additional_message_var, wraplength=470)
        self.additional_message_label.pack(pady=(10, 0), anchor="w")
        
        # Create cancel button
        self.cancel_button = ttk.Button(main_frame, text="Cancel", command=self.cancel)
        self.cancel_button.pack(pady=(10, 0))
        
        # Update UI
        self.dialog.update()
        
        # Setup protocol for window close
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)

    def update_overall_progress(self, value, maximum=100):
        """Update overall progress bar value and title"""
        if self.cancelled:
            return
        percentage = (value / maximum) * 100
        self.overall_progress_var.set(percentage)
        self.dialog.title(self.title + f" - {percentage:.2f}% done")
        self.dialog.update()
        
    def update_current_progress(self, value, maximum=100):
        """Update current item progress bar value"""
        if self.cancelled:
            return
        self.current_progress_var.set((value / maximum) * 100)
        self.dialog.update()
        
    def update_secondary_progress(self, value, maximum=100):
        """Update secondary progress bar value"""
        if self.cancelled:
            return
        self.secondary_progress_var.set((value / maximum) * 100)
        self.dialog.update()
        
    def update_message(self, message):
        """Update the main message text"""
        if self.cancelled:
            return
        self.message_var.set(message)
        self.dialog.update()
        
    def update_time_remaining(self, time_text):
        """Update the time remaining text"""
        if self.cancelled:
            return
        self.time_var.set(f"Estimated time remaining: {time_text}")
        self.dialog.update()
        
    def update_overall_status(self, status):
        """Update the overall status text"""
        if self.cancelled:
            return
        self.overall_status_var.set(status)
        self.dialog.update()
        
    def update_current_status(self, status):
        """Update the current item status text"""
        if self.cancelled:
            return
        self.current_status_var.set(status)
        self.dialog.update()
        
    def update_secondary_status(self, status):
        """Update the secondary status text"""
        if self.cancelled:
            return
        self.secondary_status_var.set(status)
        self.dialog.update()
        
    def update_additional_message(self, message):
        """Update the additional message text"""
        if self.cancelled:
            return
        self.additional_message_var.set(message)
        self.dialog.update()
        
    def reset_current_progress(self):
        """Reset the current progress bar to zero"""
        if self.cancelled:
            return
        self.current_progress_var.set(0)
        self.current_status_var.set("")
        self.dialog.update()
        
    def reset_secondary_progress(self):
        """Reset the secondary progress bar to zero"""
        if self.cancelled:
            return
        self.secondary_progress_var.set(0)
        self.secondary_status_var.set("")
        self.dialog.update()

    def close(self):
        """Close the progress dialog"""
        self.dialog.destroy()

    def is_cancelled(self):
        """Check if operation was cancelled"""
        return self.cancelled
       
    def cancel(self):
        """Handle cancellation request"""
        self.cancelled = True
        self.close()
       

class QuadrupleProgressDialog:
    """Enhanced quadruple progress dialog with better text display and cancel support"""
    
    def __init__(self, parent, title="Processing", message="Operation in progress..."):
        """Create a progress dialog with four progress bars"""
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.title = title
        self.dialog.geometry("500x500")  # Adjusted height to accommodate additional message
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Flag to track cancellation
        self.cancelled = False
        
        # Configure to be non-resizable
        self.dialog.resizable(False, False)
        
        # Center dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        # Create main frame with padding
        main_frame = ttk.Frame(self.dialog, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create message label
        self.message_var = tk.StringVar(value=message)
        self.message_label = ttk.Label(main_frame, textvariable=self.message_var, wraplength=470)
        self.message_label.pack(pady=(0, 10), anchor="w")
        
        # Time remaining label with fixed height
        time_frame = ttk.Frame(main_frame, height=25)
        time_frame.pack(fill=tk.X)
        time_frame.pack_propagate(False)
        
        self.time_var = tk.StringVar(value="")
        self.time_label = ttk.Label(time_frame, textvariable=self.time_var)
        self.time_label.pack(anchor="w")
        
        # Create overall progress section
        overall_frame = ttk.LabelFrame(main_frame, text="Overall Progress")
        overall_frame.pack(fill=tk.X, pady=5)
        
        self.overall_progress_var = tk.DoubleVar(value=0)
        self.overall_progress_bar = ttk.Progressbar(
            overall_frame, 
            orient=tk.HORIZONTAL, 
            length=460, 
            mode='determinate',
            variable=self.overall_progress_var
        )
        self.overall_progress_bar.pack(pady=5, padx=5)
        
        # Overall status with fixed height
        overall_status_frame = ttk.Frame(overall_frame, height=25)
        overall_status_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        overall_status_frame.pack_propagate(False)
        
        self.overall_status_var = tk.StringVar(value="")
        self.overall_status_label = ttk.Label(overall_status_frame, textvariable=self.overall_status_var)
        self.overall_status_label.pack(anchor="w")
        
        # Create current item progress section
        current_frame = ttk.LabelFrame(main_frame, text="Current File Progress")
        current_frame.pack(fill=tk.X, pady=5)
        
        self.current_progress_var = tk.DoubleVar(value=0)
        self.current_progress_bar = ttk.Progressbar(
            current_frame, 
            orient=tk.HORIZONTAL, 
            length=460, 
            mode='determinate',
            variable=self.current_progress_var
        )
        self.current_progress_bar.pack(pady=5, padx=5)
        
        # Current status with fixed height
        current_status_frame = ttk.Frame(current_frame, height=25)
        current_status_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        current_status_frame.pack_propagate(False)
        
        self.current_status_var = tk.StringVar(value="")
        self.current_status_label = ttk.Label(current_status_frame, textvariable=self.current_status_var)
        self.current_status_label.pack(anchor="w")
        
        # Create additional progress section
        additional_frame = ttk.LabelFrame(main_frame, text="Additional Progress")
        additional_frame.pack(fill=tk.X, pady=5)
        
        self.additional_progress_var = tk.DoubleVar(value=0)
        self.additional_progress_bar = ttk.Progressbar(
            additional_frame, 
            orient=tk.HORIZONTAL, 
            length=460, 
            mode='determinate',
            variable=self.additional_progress_var
        )
        self.additional_progress_bar.pack(pady=5, padx=5)
        
        # Additional status with fixed height
        additional_status_frame = ttk.Frame(additional_frame, height=25)
        additional_status_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        additional_status_frame.pack_propagate(False)
        
        self.additional_status_var = tk.StringVar(value="")
        self.additional_status_label = ttk.Label(additional_status_frame, textvariable=self.additional_status_var)
        self.additional_status_label.pack(anchor="w")
        
        # Create extra progress section
        extra_frame = ttk.LabelFrame(main_frame, text="Extra Progress")
        extra_frame.pack(fill=tk.X, pady=5)
        
        self.extra_progress_var = tk.DoubleVar(value=0)
        self.extra_progress_bar = ttk.Progressbar(
            extra_frame, 
            orient=tk.HORIZONTAL, 
            length=460, 
            mode='determinate',
            variable=self.extra_progress_var
        )
        self.extra_progress_bar.pack(pady=5, padx=5)
        
        # Extra status with fixed height
        extra_status_frame = ttk.Frame(extra_frame, height=25)
        extra_status_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        extra_status_frame.pack_propagate(False)
        
        self.extra_status_var = tk.StringVar(value="")
        self.extra_status_label = ttk.Label(extra_status_frame, textvariable=self.extra_status_var)
        self.extra_status_label.pack(anchor="w")
        
        # Create cancel button
        self.cancel_button = ttk.Button(main_frame, text="Cancel", command=self.cancel)
        self.cancel_button.pack(pady=(10, 0))
        
        # Update UI
        self.dialog.update()
        
        # Setup protocol for window close
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)

    def reset_current_progress(self):
        """Reset the current progress bar to zero"""
        if self.cancelled:
            return
        self.current_progress_var.set(0)
        self.current_status_var.set("")
        self.dialog.update()

    def update_overall_progress(self, value, maximum=100):
        """Update overall progress bar value and title"""
        if self.cancelled:
            return
        percentage = (value / maximum) * 100
        self.overall_progress_var.set(percentage)
        self.dialog.title(self.title + f" - {percentage:.2f}% done")
        self.dialog.update()
        
    def update_current_progress(self, value, maximum=100):
        """Update current item progress bar value"""
        if self.cancelled:
            return
        self.current_progress_var.set((value / maximum) * 100)
        self.dialog.update()
        
    def update_additional_progress(self, value, maximum=100):
        """Update additional progress bar value"""
        if self.cancelled:
            return
        self.additional_progress_var.set((value / maximum) * 100)
        self.dialog.update()
        
    def update_extra_progress(self, value, maximum=100):
        """Update extra progress bar value"""
        if self.cancelled:
            return
        self.extra_progress_var.set((value / maximum) * 100)
        self.dialog.update()
        
    def update_message(self, message):
        """Update the main message text"""
        if self.cancelled:
            return
        self.message_var.set(message)
        self.dialog.update()
        
    def update_time_remaining(self, time_text):
        """Update the time remaining text"""
        if self.cancelled:
            return
        self.time_var.set(f"Estimated time remaining: {time_text}")
        self.dialog.update()
        
    def update_overall_status(self, status):
        """Update the overall status text"""
        if self.cancelled:
            return
        self.overall_status_var.set(status)
        self.dialog.update()
        
    def update_current_status(self, status):
        """Update the current item status text"""
        if self.cancelled:
            return
        self.current_status_var.set(status)
        self.dialog.update()
        
    def update_additional_status(self, status):
        """Update the additional status text"""
        if self.cancelled:
            return
        self.additional_status_var.set(status)
        self.dialog.update()
        
    def update_extra_status(self, status):
        """Update the extra status text"""
        if self.cancelled:
            return
        self.extra_status_var.set(status)
        self.dialog.update()
        
    def cancel(self):
        """Handle cancellation request"""
        self.cancelled = True
        self.overall_status_var.set("Cancelling...")
        self.cancel_button.configure(state="disabled")
        self.dialog.update()
    
    def close(self):
        """Close the progress dialog"""
        self.dialog.destroy()
        
    def is_cancelled(self):
        """Check if operation was cancelled"""
        return self.cancelled