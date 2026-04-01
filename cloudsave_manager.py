import os
import json
import io
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk
import threading

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaInMemoryUpload, MediaIoBaseDownload
except Exception:
    Credentials = None
    Request = None
    InstalledAppFlow = None
    build = None
    MediaInMemoryUpload = None
    MediaIoBaseDownload = None

SCOPES = ["https://www.googleapis.com/auth/drive.appdata"]

def center_window(window):
    """Center popup on screen"""
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f'+{x}+{y}')


class CloudSaveManager:
    def __init__(self, root_ui, status_callback=None):
        self.drive = None
        self.credentials = None
        self.token_file_path = None
        self.root_ui = root_ui  # Reference to main game window
        self.status_callback = status_callback
        self._init_save_folder()
        self._init_cloud()

    def _notify_status_change(self):
        if self.status_callback:
            self.root_ui.after(0, self.status_callback)


    def _init_save_folder(self):
        """Ensure saves directory exists next to the script"""
        self.save_dir = os.path.join(os.path.dirname(__file__), "save")
        os.makedirs(self.save_dir, exist_ok=True)


    def _init_cloud(self):
        """Initialize Google Drive connection with UI feedback"""
        try:
            if not all([Credentials, Request, InstalledAppFlow, build, MediaInMemoryUpload, MediaIoBaseDownload]):
                self._show_info_popup("Google Drive libraries are not installed. Cloud saves are disabled.")
                self.drive = None
                return

            full_path = os.path.dirname(__file__)
            sys_path = os.path.join(full_path, "sys")
            os.makedirs(sys_path, exist_ok=True)

            token_file_path = os.path.join(sys_path, "gdrive_token.json")
            self.token_file_path = token_file_path
            credentials_file_path = os.path.join(sys_path, "credentials.json")

            if not os.path.exists(credentials_file_path):
                self._show_error_popup(
                    f"Missing {credentials_file_path}\n"
                    "Please download from Google Cloud Console"
                )
                return

            # Step 1: Check for existing token
            if os.path.exists(token_file_path):
                try:
                    creds = self._load_token_credentials()
                    if creds and creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                        with open(token_file_path, "w", encoding="utf-8") as token_file:
                            token_file.write(creds.to_json())
                    if creds and creds.valid:
                        self.credentials = creds
                        self.drive = self._build_drive_service(creds)
                        self._notify_status_change()
                        return
                except Exception as e:
                    print(f"Existing token expired/invalid: {e}")

            # Step 2: Authenticate
            # Show auth progress popup
            auth_window = self._create_auth_popup()

            # Start authentication in a thread
            auth_thread = threading.Thread(
                target=self._authenticate_in_thread,
                args=(credentials_file_path, auth_window, token_file_path),
                daemon=True
            )
            auth_thread.start()
            
        except Exception as e:
            self._show_error_popup(f"Cloud saves disabled: {str(e)}")
            self.drive = None

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


    def _build_drive_service(self, creds):
        return build("drive", "v3", credentials=creds, cache_discovery=False)

    def _load_token_credentials(self):
        """Load OAuth credentials from token file when available."""
        if not self.token_file_path or not os.path.exists(self.token_file_path):
            return None
        try:
            return Credentials.from_authorized_user_file(self.token_file_path, SCOPES)
        except Exception:
            return None


    def _authenticate_in_thread(self, credentials_file, auth_window, token_file):
        """Run authentication in background thread"""
        try:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)

            with open(token_file, "w", encoding="utf-8") as token_out:
                token_out.write(creds.to_json())
            
            # Close window from main thread
            self.root_ui.after(0, lambda: self._auth_complete(creds, auth_window, True))

        except Exception as e:
            self.root_ui.after(0, lambda: self._auth_complete(None, auth_window, False, str(e)))


    def _auth_complete(self, creds, auth_window, success, error_msg=None):
        """Clean up after authentication attempt"""
        if auth_window.winfo_exists():
            auth_window.destroy()
        
        if success:
            self.credentials = creds
            self.drive = self._build_drive_service(creds)
            self._notify_status_change()
            self._show_success_popup("Cloud saves connected!")
        else:
            self._show_error_popup(f"Authentication failed:\n{error_msg}")
            self.drive = None
            self._notify_status_change()


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

    def _show_info_popup(self, message):
        """Show informational notification"""
        messagebox.showinfo(
            "Info",
            message,
            parent=self.root_ui
        )

    def _slot_path(self, slot):
        return os.path.join(self.save_dir, f"slot_{slot}.save")

    def _save_local(self, slot, save_blob):
        """Persist a full save blob to local disk."""
        with open(self._slot_path(slot), 'w', encoding='utf-8') as f:
            json.dump(save_blob, f)

    def _load_local(self, slot):
        """Load full local save blob for a slot."""
        path = self._slot_path(slot)
        if not os.path.exists(path):
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None

    def _cloud_filename(self, slot):
        return f"lk_slot_{slot}.save.json"

    def _find_cloud_file(self, slot):
        """Find an existing cloud save file for a slot, preferring latest modified."""
        if not self.drive:
            return None
        query = f"name='{self._cloud_filename(slot)}' and 'appDataFolder' in parents and trashed=false"
        response = self.drive.files().list(
            q=query,
            spaces="appDataFolder",
            fields="files(id,name,modifiedTime)",
            pageSize=10
        ).execute()
        files = response.get("files", [])
        if not files:
            return None
        files.sort(key=lambda f: f.get("modifiedTime", ""), reverse=True)
        return files[0]

    def _upload_to_cloud(self, slot, save_blob):
        """Upload a full save blob to Google Drive."""
        if not self.drive:
            return False
        try:
            file_obj = self._find_cloud_file(slot)
            media = MediaInMemoryUpload(
                json.dumps(save_blob).encode("utf-8"),
                mimetype="application/json",
                resumable=False
            )
            if file_obj is None:
                metadata = {
                    "name": self._cloud_filename(slot),
                    "parents": ["appDataFolder"]
                }
                self.drive.files().create(body=metadata, media_body=media, fields="id").execute()
            else:
                self.drive.files().update(fileId=file_obj["id"], media_body=media).execute()
            return True
        except Exception as e:
            self._show_error_popup(f"Cloud upload failed: {e}")
            return False

    def _load_cloud(self, slot):
        """Load full cloud save blob for a slot."""
        if not self.drive:
            return None
        try:
            file_obj = self._find_cloud_file(slot)
            if file_obj is None:
                return None
            request = self.drive.files().get_media(fileId=file_obj["id"])
            payload = io.BytesIO()
            downloader = MediaIoBaseDownload(payload, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            content = payload.getvalue().decode("utf-8")
            return json.loads(content)
        except Exception:
            return None

    def _parse_timestamp(self, value):
        """Parse multiple timestamp formats used by local/cloud saves."""
        if not value:
            return datetime.min
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            text = value.strip()
            # Handle trailing Z (UTC) used by Google metadata exports.
            if text.endswith("Z"):
                text = text[:-1] + "+00:00"
            try:
                parsed = datetime.fromisoformat(text)
                if parsed.tzinfo is not None:
                    return parsed.replace(tzinfo=None)
                return parsed
            except Exception:
                pass
        return datetime.min


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
        local_time = self._parse_timestamp(local.get("timestamp"))
        cloud_time = self._parse_timestamp(cloud.get("timestamp"))
        
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
        
        
    def _check_drive_connectivity(self):
        """Verify Drive is actually reachable; update status and drop drive handle if not."""
        if not self.drive:
            return False

        was_connected = self.drive is not None
        try:
            self.drive.files().list(spaces="appDataFolder", pageSize=1, fields="files(id)").execute()
            return True
        except Exception:
            pass

        # Recover from expired/stale sessions by reloading token credentials and rebuilding the service.
        creds = self._load_token_credentials() or self.credentials
        if creds:
            self.credentials = creds
            try:
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    if self.token_file_path:
                        with open(self.token_file_path, "w", encoding="utf-8") as token_file:
                            token_file.write(creds.to_json())

                if creds.valid:
                    self.drive = self._build_drive_service(creds)
                    self.drive.files().list(spaces="appDataFolder", pageSize=1, fields="files(id)").execute()
                    return True
            except Exception:
                pass

        self.drive = None
        if was_connected:
            self._notify_status_change()
        return False

    def is_cloud_connected(self, verify=False):
        """Report cloud connection state, with optional API reachability check."""
        if verify:
            return self._check_drive_connectivity()
        return self.drive is not None

    def refresh_connection_status(self):
        """Check reachability and try non-interactive reconnection using existing credentials."""
        was_connected = self.drive is not None

        if self._check_drive_connectivity():
            return True

        creds = self._load_token_credentials() or self.credentials
        if creds:
            self.credentials = creds

        if not creds:
            if was_connected:
                self._notify_status_change()
            return False

        try:
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                if self.token_file_path:
                    with open(self.token_file_path, "w", encoding="utf-8") as token_file:
                        token_file.write(creds.to_json())

            if creds.valid:
                test_drive = self._build_drive_service(creds)
                test_drive.files().list(spaces="appDataFolder", pageSize=1, fields="files(id)").execute()
                self.drive = test_drive
                if not was_connected:
                    self._notify_status_change()
                return True
        except Exception:
            pass

        self.drive = None
        if was_connected:
            self._notify_status_change()
        return False

    def sync_all_saves(self):
        """Manual cloud sync (call on game exit)"""
        if not self.refresh_connection_status():
            return False

        uploaded = 0
        for slot in range(1, 6):  # Assuming 5 save slots
            local = self._load_local(slot)
            if local:
                if self._upload_to_cloud(slot, local):
                    uploaded += 1

        if uploaded:
            self._show_info_popup(f"{uploaded} save(s) synced to cloud!")


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