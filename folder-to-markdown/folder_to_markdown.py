#!/usr/bin/env python3
import os
import sys
import time
import hashlib
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
from tkinter.font import Font
import markdown
from PIL import Image, ImageTk
import mimetypes
import json
import threading
from functools import partial
from pathlib import Path

class FolderToMarkdown:
    def __init__(self, root):
        self.root = root
        self.root.title("Folder to Markdown")
        self.root.geometry("1200x800")
        
        # Set application icon
        try:
            icon_path = self.resource_path("icon.png")
            self.root.iconphoto(True, tk.PhotoImage(file=icon_path))
        except:
            pass  # If icon not found, use default
        
        # Default excluded files and folders
        self.excluded_dirs = [
            'node_modules', '.git', '__pycache__', 'venv', 'env',
            'dist', 'build', '.vscode', '.webpack', '.idea', '.cache', '.idea', 'out'
        ]
        
        self.excluded_files = [
            'env.ts', 'secret.ts', '.env', '.gitignore', '.DS_Store', 'LICENSE', 'package-lock.json'
        ]
        
        self.excluded_extensions = [
            '.jpg', '.jpeg', '.png', '.gif', '.ico', '.svg', '.bmp',
            '.mp3', '.mp4', '.avi', '.mov', '.flv', '.zip', '.tar',
            '.gz', '.rar', '.7z', '.exe', '.dll', '.so', '.dylib', 
            '.pyc', '.o', '.obj', '.d.ts', '.webp', 'icns', 'ico'
        ]
        
        # Store file hashes for change detection
        self.file_hashes = {}
        
        # Store last selected folder
        self.selected_folder = None
        
        # Last markdown output
        self.last_markdown = ""
        
        # Default output filename
        self.output_filename = "README.md"
        
        # Create the main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create the control panel at the top
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Folder selection
        ttk.Label(self.control_frame, text="Folder:").pack(side=tk.LEFT, padx=(0, 5))
        self.folder_var = tk.StringVar()
        self.folder_entry = ttk.Entry(self.control_frame, textvariable=self.folder_var, width=40)
        self.folder_entry.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        
        self.browse_button = ttk.Button(self.control_frame, text="Browse", command=self.browse_folder)
        self.browse_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Output filename
        ttk.Label(self.control_frame, text="Output:").pack(side=tk.LEFT, padx=(0, 5))
        self.output_var = tk.StringVar(value=self.output_filename)
        self.output_entry = ttk.Entry(self.control_frame, textvariable=self.output_var, width=20)
        self.output_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        # Refresh button
        self.refresh_button = ttk.Button(self.control_frame, text="Refresh", command=self.refresh_markdown)
        self.refresh_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Save button
        self.save_button = ttk.Button(self.control_frame, text="Save", command=self.save_markdown)
        self.save_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Exclusion settings button
        self.settings_button = ttk.Button(self.control_frame, text="Exclusion Settings", command=self.show_exclusion_settings)
        self.settings_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Create paned window for the two main areas
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Left side - Tree structure
        self.tree_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.tree_frame, weight=1)
        
        ttk.Label(self.tree_frame, text="Folder Structure").pack(fill=tk.X)
        
        # Create treeview with scrollbar
        self.tree_scrollbar = ttk.Scrollbar(self.tree_frame)
        self.tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree = ttk.Treeview(self.tree_frame, yscrollcommand=self.tree_scrollbar.set)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree_scrollbar.config(command=self.tree.yview)
        
        # Configure tree columns
        self.tree["columns"] = ("status")
        self.tree.column("#0", width=300, minwidth=200)
        self.tree.column("status", width=50, minwidth=50, anchor=tk.CENTER)
        self.tree.heading("#0", text="Path")
        self.tree.heading("status", text="Status")
        
        # Right side - Markdown preview
        self.markdown_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.markdown_frame, weight=1)
        
        ttk.Label(self.markdown_frame, text="Markdown Preview").pack(fill=tk.X)
        
        # Create markdown preview with scrollbar
        self.preview_scrollbar = ttk.Scrollbar(self.markdown_frame)
        self.preview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # HTML preview widget
        self.preview = tk.Text(self.markdown_frame, wrap=tk.WORD, yscrollcommand=self.preview_scrollbar.set)
        self.preview.pack(fill=tk.BOTH, expand=True)
        self.preview_scrollbar.config(command=self.preview.yview)
        
        # Configure text tags for markdown rendering
        self.preview.tag_configure("h1", font=Font(family="Helvetica", size=18, weight="bold"))
        self.preview.tag_configure("h2", font=Font(family="Helvetica", size=16, weight="bold"))
        self.preview.tag_configure("h3", font=Font(family="Helvetica", size=14, weight="bold"))
        self.preview.tag_configure("code", font=Font(family="Courier", size=10), background="#f0f0f0")
        self.preview.tag_configure("bold", font=Font(family="Helvetica", weight="bold"))
        self.preview.tag_configure("italic", font=Font(family="Helvetica", slant="italic"))
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))
        
        # Load settings if they exist
        self.load_settings()
        
        # Auto-refresh thread
        self.stop_auto_refresh = threading.Event()
        self.auto_refresh_thread = threading.Thread(target=self.auto_refresh_loop, daemon=True)
        self.auto_refresh_thread.start()

    def resource_path(self, relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller"""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        
        return os.path.join(base_path, relative_path)
    
    def load_settings(self):
        """Load exclusion settings from config file"""
        config_path = os.path.join(os.path.expanduser("~"), ".folder_to_markdown_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self.excluded_dirs = config.get('excluded_dirs', self.excluded_dirs)
                    self.excluded_files = config.get('excluded_files', self.excluded_files)
                    self.excluded_extensions = config.get('excluded_extensions', self.excluded_extensions)
            except:
                # If loading fails, use defaults
                pass
    
    def save_settings(self):
        """Save exclusion settings to config file"""
        config_path = os.path.join(os.path.expanduser("~"), ".folder_to_markdown_config.json")
        config = {
            'excluded_dirs': self.excluded_dirs,
            'excluded_files': self.excluded_files,
            'excluded_extensions': self.excluded_extensions
        }
        
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except:
            self.show_error("Failed to save settings")
    
    def show_exclusion_settings(self):
        """Show a dialog for configuring exclusion settings"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Exclusion Settings")
        settings_window.geometry("600x500")
        settings_window.grab_set()  # Make window modal
        
        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Excluded directories tab
        dir_frame = ttk.Frame(notebook)
        notebook.add(dir_frame, text="Excluded Directories")
        
        dirs_text = scrolledtext.ScrolledText(dir_frame)
        dirs_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        dirs_text.insert(tk.END, "\n".join(self.excluded_dirs))
        
        # Excluded files tab
        file_frame = ttk.Frame(notebook)
        notebook.add(file_frame, text="Excluded Files")
        
        files_text = scrolledtext.ScrolledText(file_frame)
        files_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        files_text.insert(tk.END, "\n".join(self.excluded_files))
        
        # Excluded extensions tab
        ext_frame = ttk.Frame(notebook)
        notebook.add(ext_frame, text="Excluded Extensions")
        
        exts_text = scrolledtext.ScrolledText(ext_frame)
        exts_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        exts_text.insert(tk.END, "\n".join(self.excluded_extensions))
        
        # Buttons frame
        btn_frame = ttk.Frame(settings_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def save_and_close():
            # Update exclusion lists
            self.excluded_dirs = [d.strip() for d in dirs_text.get("1.0", tk.END).split("\n") if d.strip()]
            self.excluded_files = [f.strip() for f in files_text.get("1.0", tk.END).split("\n") if f.strip()]
            self.excluded_extensions = [e.strip() for e in exts_text.get("1.0", tk.END).split("\n") if e.strip()]
            
            # Save settings
            self.save_settings()
            
            # Refresh if a folder is selected
            if self.selected_folder:
                self.refresh_markdown()
            
            settings_window.destroy()
        
        save_btn = ttk.Button(btn_frame, text="Save", command=save_and_close)
        save_btn.pack(side=tk.RIGHT, padx=5)
        
        cancel_btn = ttk.Button(btn_frame, text="Cancel", command=settings_window.destroy)
        cancel_btn.pack(side=tk.RIGHT, padx=5)
    
    def browse_folder(self):
        """Open a folder picker dialog and select a folder"""
        folder = filedialog.askdirectory()
        if folder:
            self.folder_var.set(folder)
            self.selected_folder = folder
            self.generate_tree_and_markdown()
    
    def refresh_markdown(self):
        """Refresh the markdown based on the current folder"""
        if self.selected_folder:
            self.generate_tree_and_markdown()
        else:
            self.show_error("No folder selected")
    
    def auto_refresh_loop(self):
        """Background thread that checks for file changes every 5 seconds"""
        while not self.stop_auto_refresh.is_set():
            if self.selected_folder:
                # Check for file changes
                changes = self.check_for_changes()
                if changes:
                    # Update UI from the main thread
                    self.root.after(0, self.update_tree_status, changes)
            
            # Sleep for 5 seconds
            time.sleep(5)
    
    def check_for_changes(self):
        """Check for changes in the files and return a list of changed files"""
        changes = []
        
        if not self.selected_folder:
            return changes
        
        for root, dirs, files in os.walk(self.selected_folder):
            # Apply directory exclusions
            dirs[:] = [d for d in dirs if d not in self.excluded_dirs]
            
            for file in files:
                if self.should_exclude_file(file):
                    continue
                
                file_path = os.path.join(root, file)
                
                try:
                    current_hash = self.get_file_hash(file_path)
                    
                    if file_path in self.file_hashes:
                        if current_hash != self.file_hashes[file_path]:
                            changes.append(file_path)
                            self.file_hashes[file_path] = current_hash
                    else:
                        self.file_hashes[file_path] = current_hash
                except:
                    pass  # Ignore files that can't be read
        
        return changes
    
    def get_file_hash(self, file_path):
        """Generate a hash for a file to detect changes"""
        try:
            with open(file_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return ""
    
    def update_tree_status(self, changed_files):
        """Update the tree status icons for changed files"""
        if not changed_files:
            return
        
        for item_id in self.tree.get_children(""):
            self.update_item_status(item_id, changed_files)
    
    def update_item_status(self, item_id, changed_files):
        """Recursively update status for an item and its children"""
        item_path = self.tree.item(item_id, "text")
        full_path = os.path.join(self.selected_folder, item_path)
        
        # Check if this is a file that changed
        if os.path.isfile(full_path) and full_path in changed_files:
            self.tree.item(item_id, values=("⚠️"))
        
        # Process children
        for child_id in self.tree.get_children(item_id):
            self.update_item_status(child_id, changed_files)
    
    def should_exclude_file(self, filename):
        """Check if a file should be excluded based on filename or extension"""
        if filename in self.excluded_files:
            return True
        
        _, ext = os.path.splitext(filename)
        return ext.lower() in self.excluded_extensions
    
    def generate_tree_and_markdown(self):
        """Generate the tree view and markdown for the selected folder"""
        if not self.selected_folder or not os.path.exists(self.selected_folder):
            self.show_error("Invalid folder selected")
            return
        
        # Clear existing tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Reset file hashes
        self.file_hashes = {}
        
        # Update status
        self.status_var.set(f"Generating documentation for: {self.selected_folder}")
        self.root.update()
        
        # Start generating the markdown content
        markdown_content = f"# Project Documentation: {os.path.basename(self.selected_folder)}\n\n"
        markdown_content += "## Directory Structure\n\n```\n"
        
        # Add directory tree
        tree_content = self.generate_directory_tree(self.selected_folder)
        markdown_content += tree_content + "\n```\n\n"
        
        # Add file contents
        markdown_content += "## File Contents\n\n"
        
        # Populate the tree and generate file content
        file_content = self.populate_tree_and_get_content(self.selected_folder, "")
        markdown_content += file_content
        
        # Store the markdown
        self.last_markdown = markdown_content
        
        # Update the preview
        self.update_preview(markdown_content)
        
        # Update status
        self.status_var.set(f"Documentation generated for: {self.selected_folder}")
        
        # Auto-save if enabled
        self.save_markdown()
    
    def generate_directory_tree(self, folder_path):
        """Generate a text representation of the directory tree"""
        base_name = os.path.basename(folder_path)
        tree_content = base_name + "/\n"
        
        tree_content += self._generate_tree_recursive(folder_path, "", "")
        
        return tree_content
    
    def _generate_tree_recursive(self, folder_path, prefix, relative_path):
        """Recursively generate tree structure"""
        items = []
        
        try:
            items = sorted(os.listdir(folder_path))
        except:
            return ""
        
        tree_content = ""
        
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            item_path = os.path.join(folder_path, item)
            rel_path = os.path.join(relative_path, item)
            
            # Skip excluded directories and files
            if os.path.isdir(item_path) and item in self.excluded_dirs:
                continue
            
            if os.path.isfile(item_path) and self.should_exclude_file(item):
                continue
            
            # Add item to the tree
            if is_last:
                tree_content += f"{prefix}└── {item}"
                new_prefix = prefix + "    "
            else:
                tree_content += f"{prefix}├── {item}"
                new_prefix = prefix + "│   "
            
            if os.path.isdir(item_path):
                tree_content += "/\n"
                tree_content += self._generate_tree_recursive(item_path, new_prefix, rel_path)
            else:
                tree_content += "\n"
        
        return tree_content
    
    def populate_tree_and_get_content(self, folder_path, parent=""):
        """Populate the treeview and generate markdown content for files"""
        items = []
        
        try:
            items = sorted(os.listdir(folder_path))
        except:
            return ""
        
        file_content = ""
        
        for item in items:
            item_path = os.path.join(folder_path, item)
            rel_path = os.path.relpath(item_path, self.selected_folder)
            
            # Skip excluded directories and files
            if os.path.isdir(item_path) and item in self.excluded_dirs:
                continue
            
            if os.path.isfile(item_path) and self.should_exclude_file(item):
                continue
            
            # Add item to the tree
            if os.path.isdir(item_path):
                # Add directory to tree
                dir_id = self.tree.insert(parent, "end", text=rel_path, values=(""))
                
                # Process directory contents
                content = self.populate_tree_and_get_content(item_path, dir_id)
                if content:
                    file_content += content
            else:
                # Add file to tree
                self.tree.insert(parent, "end", text=rel_path, values=(""))
                
                # Get file content
                file_hash = self.get_file_hash(item_path)
                self.file_hashes[item_path] = file_hash
                
                try:
                    # Determine file type
                    file_ext = os.path.splitext(item)[1].lower()
                    
                    # Try to get language from extension for code highlighting
                    language = self.get_language_from_extension(file_ext)
                    
                    # Read file content
                    try:
                        with open(item_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Add file content to markdown
                        file_content += f"### {rel_path}\n\n"
                        file_content += f"```{language}\n{content}\n```\n\n"
                    except UnicodeDecodeError:
                        # For binary files
                        file_content += f"### {rel_path}\n\n"
                        file_content += "_Binary file, content not shown_\n\n"
                except:
                    file_content += f"### {rel_path}\n\n"
                    file_content += "_Error reading file_\n\n"
        
        return file_content
    
    def get_language_from_extension(self, ext):
        """Map file extension to language for syntax highlighting"""
        mapping = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'jsx',
            '.ts': 'typescript',
            '.tsx': 'tsx',
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.md': 'markdown',
            '.sql': 'sql',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cs': 'csharp',
            '.go': 'go',
            '.php': 'php',
            '.rb': 'ruby',
            '.rs': 'rust',
            '.sh': 'bash',
            '.swift': 'swift',
            '.yml': 'yaml',
            '.yaml': 'yaml',
            '.xml': 'xml',
            '.txt': 'text'
        }
        
        return mapping.get(ext, '')
    
    def update_preview(self, markdown_content):
        """Update the preview with rendered markdown"""
        # Clear the preview
        self.preview.config(state=tk.NORMAL)
        self.preview.delete("1.0", tk.END)
        
        # Very basic markdown rendering using tags
        # For a full-featured solution, consider using a web-based viewer
        
        lines = markdown_content.split('\n')
        code_block = False
        
        for line in lines:
            if line.startswith('```'):
                code_block = not code_block
                if code_block:
                    # Get language if specified
                    lang = line[3:].strip()
                    self.preview.insert(tk.END, f"Code Block ({lang}):\n", "bold")
                else:
                    self.preview.insert(tk.END, "\n")
                continue
            
            if code_block:
                self.preview.insert(tk.END, line + "\n", "code")
                continue
            
            # Headers
            if line.startswith('# '):
                self.preview.insert(tk.END, line[2:] + "\n\n", "h1")
            elif line.startswith('## '):
                self.preview.insert(tk.END, line[3:] + "\n\n", "h2")
            elif line.startswith('### '):
                self.preview.insert(tk.END, line[4:] + "\n\n", "h3")
            else:
                # Regular text
                self.preview.insert(tk.END, line + "\n")
        
        self.preview.config(state=tk.DISABLED)
    
    def save_markdown(self):
        """Save the markdown to a file"""
        if not self.last_markdown:
            self.show_error("No content to save")
            return
        
        output_filename = self.output_var.get().strip()
        if not output_filename:
            output_filename = "README.md"
        
        # Ensure it has .md extension
        if not output_filename.lower().endswith('.md'):
            output_filename += '.md'
        
        # Default to Documents folder
        docs_folder = os.path.join(os.path.expanduser("~"), "Documents")
        if not os.path.exists(docs_folder):
            docs_folder = os.path.expanduser("~")
        
        output_path = os.path.join(docs_folder, output_filename)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(self.last_markdown)
            
            self.status_var.set(f"Saved to: {output_path}")
        except Exception as e:
            self.show_error(f"Failed to save: {str(e)}")
    
    def show_error(self, message):
        """Show an error message"""
        self.status_var.set(f"Error: {message}")
        
        # Also show in a dialog for important errors
        tk.messagebox.showerror("Error", message)
    
    def on_closing(self):
        """Clean up before closing"""
        self.stop_auto_refresh.set()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = FolderToMarkdown(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
