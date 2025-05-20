import os
import json
from datetime import datetime
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import tkinter as tk
from tkinter import messagebox, ttk
import threading

def center_window(window):
    """Center popup on screen"""
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f'+{x}+{y}')


class CloudSaveManager:
    def __init__(self, root_ui):
        self.drive = None
        self.root_ui = root_ui  # Reference to main game window
        self._init_save_folder()
        self._init_cloud()


    def _init_save_folder(self):
        """Ensure saves directory exists"""
        self.save_dir = "save"
        os.makedirs(self.save_dir, exist_ok=True)


    def _init_cloud(self):
        """Initialize Google Drive connection with UI feedback"""
        try:
            gauth = GoogleAuth()
            
            full_path = os.path.dirname(__file__)
            token_file_path = os.path.join(full_path, "gdrive_token.json")
            # Step 1: Check for existing token
            if os.path.exists(token_file_path):
                try:
                    gauth.LoadCredentialsFile(token_file_path)
                    if gauth.access_token_expired:
                        gauth.Refresh()
                    self.drive = GoogleDrive(gauth)
                    return
                except Exception as e:
                    print(f"Existing token expired/invalid: {e}")

            # Step 2: Prepare proper client_secrets.json
            # Show auth popup if no credentials
            secrets_file_path = os.path.join(full_path, "client_secrets.json")
            ccred_file_path = os.path.join(full_path, "credentials.json")
            if not os.path.exists(secrets_file_path):
                if not os.path.exists(ccred_file_path):
                    self._show_error_popup(
                        f"Missing {ccred_file_path}\n"
                        "Please download from Google Cloud Console"
                    )
                    return
                self._create_client_secrets(ccred_file_path, secrets_file_path)

            # Step 3: Authenticate
            # Show auth progress popup
            auth_window = self._create_auth_popup()

            # Start authentication in a thread
            auth_thread = threading.Thread(
                target=self._authenticate_in_thread,
                args=(gauth, auth_window, token_file_path),
                daemon=True
            )
            auth_thread.start()
            
        except Exception as e:
            self._show_error_popup(f"Cloud saves disabled: {str(e)}")
            self.drive = None

    def _create_client_secrets(self, cred_file, sec_file):
        """Create PyDrive-compatible client_secrets.json from installed app credentials"""
        try:
            with open(cred_file) as f:
                creds = json.load(f)["installed"]  # Access the "installed" section

            # Create the EXACT format PyDrive expects
            proper_format = {
                "client_id": creds["client_id"],
                "client_secret": creds["client_secret"],
                "redirect_uris": creds["redirect_uris"],
                "auth_uri": creds["auth_uri"],
                "token_uri": creds["token_uri"]
            }

            with open(sec_file, "w") as f:
                json.dump({"web": proper_format}, f, indent=2)  # Note the "web" wrapper

        except Exception as e:
            raise ValueError(f"Credential conversion failed: {str(e)}")
        

    def _create_auth_popup(self):
        """Create properly animated auth window"""
        auth_window = tk.Toplevel(self.root_ui)
        auth_window.title("Cloud Connection Setup")
        auth_window.geometry("300x180")
        auth_window.attributes('-topmost', True)
        
        # Center window
        center_window(auth_window)
        
        # UI Elements
        tk.Label(
            auth_window,
            text="Connecting to Google Drive...",
            font=("Arial", 12)
        ).pack(pady=20)
        
        progress = ttk.Progressbar(
            auth_window,
            orient="horizontal",
            length=200,
            mode="indeterminate"
        )
        progress.pack()
        progress.start(10)
    
        # Keep animation running
        self._keep_animation_alive(auth_window, progress)
        
        return auth_window


    def _keep_animation_alive(self, window, progress):
        """Ensure progress bar keeps animating"""
        if window.winfo_exists():
            progress.step(1)  # Manually increment progress
            window.after(50, lambda: self._keep_animation_alive(window, progress))


    def _authenticate_in_thread(self, gauth, auth_window, token_file):
        """Run authentication in background thread"""
        try:
            # This will open browser for authentication
            gauth.LocalWebserverAuth()
            gauth.SaveCredentialsFile(token_file)
            
            # Close window from main thread
            self.root_ui.after(0, lambda: self._auth_complete(gauth, auth_window, True))

        except Exception as e:
            self.root_ui.after(0, lambda: self._auth_complete(gauth, auth_window, False, str(e)))


    def _auth_complete(self, gauth, auth_window, success, error_msg=None):
        """Clean up after authentication attempt"""
        if auth_window.winfo_exists():
            auth_window.destroy()
        
        if success:
            self.drive = GoogleDrive(gauth)
            self._show_success_popup("Cloud saves connected!")
        else:
            self._show_error_popup(f"Authentication failed:\n{error_msg}")
            self.drive = None


    def show_conflict_resolution(self, slot, local_time, cloud_time):
        """Game-themed conflict dialog"""
        conflict_window = tk.Toplevel(self.root_ui)
        conflict_window.title("Save Conflict Detected")
        conflict_window.geometry("400x300")
        
        # Styling to match game
        bg_color = "#2d2d2d"
        text_color = "#e0e0e0"
        button_style = {
            'bg': '#4a6ea9', 
            'fg': 'white',
            'activebackground': '#5d8aff',
            'borderwidth': 0,
            'padx': 15,
            'pady': 5
        }

        conflict_window.configure(bg=bg_color)
        
        # Header
        tk.Label(
            conflict_window,
            text="⚠️ Save Conflict",
            bg=bg_color,
            fg="#ffcc00",
            font=("Arial", 14, "bold")
        ).pack(pady=(10,5))

        # Explanation
        tk.Label(
            conflict_window,
            text=f"Slot {slot} has different versions:",
            bg=bg_color,
            fg=text_color,
            wraplength=380
        ).pack(pady=5)

        # Version info
        versions_frame = tk.Frame(conflict_window, bg=bg_color)
        versions_frame.pack(pady=10)
        
        tk.Label(
            versions_frame,
            text=f"LOCAL: {local_time}",
            bg="#1e3a6b",
            fg=text_color,
            padx=10
        ).grid(row=0, column=0, padx=5)
        
        tk.Label(
            versions_frame,
            text=f"CLOUD: {cloud_time}",
            bg="#3a1e6b",
            fg=text_color,
            padx=10
        ).grid(row=0, column=1, padx=5)

        # Buttons
        button_frame = tk.Frame(conflict_window, bg=bg_color)
        button_frame.pack(pady=15)
        
        def set_choice(choice):
            self.last_conflict_choice = choice
            conflict_window.destroy()

        tk.Button(
            button_frame,
            text="Keep Local Version",
            command=lambda: set_choice("local"),
            **button_style
        ).grid(row=0, column=0, padx=5)

        tk.Button(
            button_frame,
            text="Use Cloud Version",
            command=lambda: set_choice("cloud"),
            **button_style
        ).grid(row=0, column=1, padx=5)

        tk.Button(
            button_frame,
            text="Cancel (Keep Local)",
            command=lambda: set_choice("cancel"),
            bg="#6d6d6d",
            fg=text_color
        ).grid(row=1, columnspan=2, pady=(10,0))

        conflict_window.transient(self.root_ui)
        conflict_window.grab_set()
        self.root_ui.wait_window(conflict_window)
        
        return self.last_conflict_choice
    

    def _show_success_popup(self, message):
        """Show success notification"""
        messagebox.showinfo(
            "Success",
            message,
            parent=self.root_ui
        )

    def _show_error_popup(self, message):
        """Show error notification"""
        messagebox.showerror(
            "Error",
            message,
            parent=self.root_ui
        )


    # --- Save/Load Implementation ---
    def save_game(self, slot, game_data, immediate_upload=False):
        """Save game state with optional cloud sync"""
        save_path = os.path.join(self.save_dir, f"slot_{slot}.save")
        save_data = {
            "timestamp": datetime.now().isoformat(),
            "data": game_data
        }
        
        with open(save_path, 'w') as f:
            json.dump(save_data, f)
            
        if immediate_upload and self.drive:
            self._upload_to_cloud(slot, save_data)

    def load_game(self, slot):
        """Load with full conflict resolution"""
        local = self._load_local(slot)
        cloud = self._load_cloud(slot) if self.drive else None
        
        if not local and not cloud:
            return None
            
        if not cloud:
            return local["data"]
            
        if not local:
            self._save_local(slot, cloud)
            return cloud["data"]
            
        return self._resolve_save_conflict(slot, local, cloud)
    

    def _resolve_save_conflict(self, slot, local, cloud):
        """Handle all conflict scenarios"""
        local_time = datetime.fromisoformat(local["timestamp"])
        cloud_time = datetime.strptime(cloud["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ")
        
        # Auto-resolve if within 1 minute
        if abs((local_time - cloud_time).total_seconds()) < 60:
            return local["data"]
            
        # Significant difference - ask player
        choice = self.show_conflict_resolution(
            slot,
            local_time.strftime("%Y-%m-%d %H:%M"),
            cloud_time.strftime("%Y-%m-%d %H:%M")
        )
        
        if choice == "local":
            return local["data"]
        elif choice == "cloud":
            self._save_local(slot, cloud)
            return cloud["data"]
        else:
            return local["data"]  # On cancel
        
        
    def sync_all_saves(self):
        """Manual cloud sync (call on game exit)"""
        if not self.drive:
            return False
            
        for slot in range(1, 6):  # Assuming 5 save slots
            local = self._load_local(slot)
            if local:
                self._upload_to_cloud(slot, local)
                
        self._show_info_popup("All saves synced to cloud!")


    def show_reconnect_button(self):
        """Add a reconnect button to your settings menu"""
        if not self.drive:
            btn = ttk.Button(
                self.root_ui,
                text="Reconnect Cloud Saves",
                command=self._reconnect_cloud
            )
            btn.pack(pady=10)

    def _reconnect_cloud(self):
        """Manual reconnection flow"""
        self._init_cloud()
        if self.drive:
            self.sync_all_saves()