import os
import shutil
import subprocess
import requests
import time
import stat
import psutil
import getpass
from pathlib import Path
from collections import defaultdict
import mimetypes
import sys
import tempfile

# Try to import beautiful output libraries
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.panel import Panel
    from rich.text import Text
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.align import Align
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

try:
    import colorama
    from colorama import Fore, Back, Style, init
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False

# Configuration for Server Dashboard Python/Tkinter
CONFIG = {
    'source_dir': r"e:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\2023\Topologie retea",
    'username': "TU-USERUL-TAU-GITHUB",  # ÎNLOCUIEȘTE cu username-ul tău GitHub
    'token': "TU-TOKEN-UL-TAU-GITHUB",   # ÎNLOCUIEȘTE cu token-ul tău GitHub
    'repo_name': "Server-Network-Topology-Monitor",
    'work_dir': r"D:\temp_github_upload_server_monitor",
    'ignore_files': [
        '.git', '__pycache__', 'venv', '.env', '*.pyc', '*.log', '*.tmp',
        'node_modules', '.vscode', '.idea', 'dist', 'build', '*.backup'
    ]
}

GIT_PATHS = [
    r"D:\Program Files\Git\bin\git.exe",
    r"C:\Program Files\Git\bin\git.exe",
    r"C:\Program Files (x86)\Git\bin\git.exe",
    "git"
]

class ConflictResolver:
    """Handles conflicts and permission issues"""

    def __init__(self, output_handler):
        self.output = output_handler
        self.console = Console() if RICH_AVAILABLE else None

    def check_repository_exists(self, username, repo_name, headers):
        """Check if repository already exists on GitHub"""
        url = f"https://api.github.com/repos/{username}/{repo_name}"
        try:
            response = requests.get(url, headers=headers)
            return response.status_code == 200
        except:
            return False

    def resolve_repository_conflict(self, username, repo_name, headers):
        """Handle existing repository conflict"""
        self.output.print_warning(f"Repository '{repo_name}' already exists on GitHub!")

        if RICH_AVAILABLE:
            choice = Prompt.ask(
                "🤔 What would you like to do?",
                choices=["update", "rename", "delete", "abort"],
                default="update"
            )
        else:
            print("\n🤔 What would you like to do?")
            print("1. update - Push to existing repository")
            print("2. rename - Create with different name")
            print("3. delete - Delete existing and recreate")
            print("4. abort - Cancel upload")
            choice = input("Choose (1-4, default: 1): ").strip()
            choice_map = {"1": "update", "2": "rename", "3": "delete", "4": "abort", "": "update"}
            choice = choice_map.get(choice, "update")

        if choice == "update":
            self.output.print_info("📤 Will push to existing repository")
            return "update", repo_name
        elif choice == "rename":
            return self._handle_rename(repo_name)
        elif choice == "delete":
            return self._handle_delete(username, repo_name, headers)
        else:
            self.output.print_info("❌ Upload cancelled by user")
            sys.exit(0)

    def _handle_rename(self, original_name):
        """Handle repository rename with validation"""
        timestamp = int(time.time())
        suggestions = [
            f"{original_name}-Pro",
            f"{original_name}-Advanced",
            f"{original_name}-{timestamp}",
            f"Python-Server-Monitor",
            f"IT-Network-Dashboard",
            f"Tkinter-Server-Monitor"
        ]

        while True:
            if RICH_AVAILABLE:
                self.output.console.print("💡 Suggested names:")
                for i, name in enumerate(suggestions, 1):
                    self.output.console.print(f"  {i}. {name}")

                new_name = Prompt.ask("✏️ Enter new repository name", default=suggestions[0])
            else:
                print("💡 Suggested names:")
                for i, name in enumerate(suggestions, 1):
                    print(f"  {i}. {name}")
                new_name = input(f"✏️ Enter new repository name (default: {suggestions[0]}): ").strip()
                if not new_name:
                    new_name = suggestions[0]

            if self._validate_repo_name(new_name):
                return "create", new_name
            else:
                self.output.print_error(f"❌ Invalid name '{new_name}'. Please choose another.")

    def _validate_repo_name(self, name):
        """Validate GitHub repository name"""
        if not name or len(name) > 100:
            return False
        
        import re
        if not re.match(r'^[a-zA-Z0-9._-]+$', name):
            return False
            
        if name.startswith('.') or name.endswith('.') or name.startswith('-') or name.endswith('-'):
            return False
            
        return True

    def _handle_delete(self, username, repo_name, headers):
        """Handle repository deletion"""
        if RICH_AVAILABLE:
            confirm = Confirm.ask(f"⚠️ Delete repository '{repo_name}'? This cannot be undone!")
        else:
            confirm = input(f"⚠️ Delete repository '{repo_name}'? (y/N): ").lower() == 'y'

        if not confirm:
            self.output.print_info("❌ Deletion cancelled")
            return self._handle_rename(repo_name)

        url = f"https://api.github.com/repos/{username}/{repo_name}"
        response = requests.delete(url, headers=headers)

        if response.status_code == 204:
            self.output.print_success(f"🗑️ Repository '{repo_name}' deleted successfully")
            time.sleep(2)
            return "create", repo_name
        else:
            self.output.print_error(f"Failed to delete repository: {response.text}")
            return self._handle_rename(repo_name)

    def kill_git_processes(self):
        """Kill any running Git processes that might lock files"""
        killed_processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'git' in proc.info['name'].lower():
                        proc.kill()
                        killed_processes.append(proc.info['name'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except:
            pass

        if killed_processes:
            self.output.print_success(f"🔄 Killed {len(killed_processes)} Git processes")
        return len(killed_processes)

    def force_remove_directory(self, path):
        """Force remove directory with advanced techniques"""
        if not os.path.exists(path):
            return True

        methods = [
            self._method_normal_removal,
            self._method_chmod_removal,
            self._method_process_kill_removal,
            self._method_temp_move_removal
        ]

        for i, method in enumerate(methods, 1):
            try:
                self.output.print_info(f"🔄 Attempting cleanup method {i}/{len(methods)}")
                if method(path):
                    self.output.print_success(f"✅ Directory cleaned with method {i}")
                    return True
                time.sleep(1)
            except Exception as e:
                self.output.print_warning(f"⚠️ Method {i} failed: {str(e)}")
                continue

        self.output.print_error(f"❌ Could not remove directory: {path}")
        return False

    def _method_normal_removal(self, path):
        shutil.rmtree(path)
        return not os.path.exists(path)

    def _method_chmod_removal(self, path):
        def handle_remove_readonly(func, path, exc):
            if os.path.exists(path):
                os.chmod(path, stat.S_IWRITE)
                func(path)
        shutil.rmtree(path, onerror=handle_remove_readonly)
        return not os.path.exists(path)

    def _method_process_kill_removal(self, path):
        self.kill_git_processes()
        time.sleep(2)
        shutil.rmtree(path)
        return not os.path.exists(path)

    def _method_temp_move_removal(self, path):
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, "to_delete")
        shutil.move(path, temp_path)
        try:
            shutil.rmtree(temp_path)
        except:
            pass
        return not os.path.exists(path)

class BeautifulOutput:
    """Enhanced output handler"""

    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None

    def print_banner(self):
        """Print enhanced banner"""
        if RICH_AVAILABLE:
            banner = """
    🖥️ SERVER NETWORK TOPOLOGY MONITOR 🖥️
    ═════════════════════════════════════════
    🐍 Python/Tkinter Desktop Application
    📊 Advanced Excel Database Integration
    🎯 Professional Network Monitoring
    🔄 Real-time Server Status Updates
    ⚡ Multi-threaded Background Monitoring
    🛠️ Complete CRUD Operations
    📈 Performance Testing & Analytics
    """
            panel = Panel(
                Align.center(Text(banner, style="bold blue")),
                border_style="bright_green",
                title="[bold yellow]🏆 PYTHON SERVER MONITOR UPLOADER 🏆[/bold yellow]",
                subtitle="[italic]v3.0 - Professional IT Infrastructure Management![/italic]"
            )
            self.console.print(panel)
        else:
            print("\n" + "="*70)
            print("🖥️ SERVER NETWORK TOPOLOGY MONITOR 🖥️")
            print("🐍 Python/Tkinter Desktop Application")
            print("📊 Advanced Excel Database Integration")  
            print("🎯 Professional Network Monitoring")
            print("🔄 Real-time Server Status Updates")
            print("="*70 + "\n")

    def print_step(self, step_num, total_steps, title, description=""):
        if RICH_AVAILABLE:
            progress_text = f"[bold cyan]Step {step_num}/{total_steps}[/bold cyan]"
            title_text = f"[bold green]{title}[/bold green]"
            if description:
                desc_text = f"[dim]{description}[/dim]"
                content = f"{progress_text} - {title_text}\n{desc_text}"
            else:
                content = f"{progress_text} - {title_text}"
            self.console.print(Panel(content, border_style="blue", padding=(0, 1)))
        else:
            print(f"\n📋 Step {step_num}/{total_steps} - {title}")
            if description:
                print(f"   💡 {description}")

    def print_success(self, message):
        if RICH_AVAILABLE:
            self.console.print(f"[bold green]✅ {message}[/bold green]")
        else:
            print(f"✅ {message}")

    def print_error(self, message):
        if RICH_AVAILABLE:
            self.console.print(f"[bold red]❌ {message}[/bold red]")
        else:
            print(f"❌ {message}")

    def print_info(self, message):
        if RICH_AVAILABLE:
            self.console.print(f"[bold blue]ℹ️  {message}[/bold blue]")
        else:
            print(f"ℹ️  {message}")

    def print_warning(self, message):
        if RICH_AVAILABLE:
            self.console.print(f"[bold yellow]⚠️  {message}[/bold yellow]")
        else:
            print(f"⚠️  {message}")

    def create_progress_bar(self, description):
        if RICH_AVAILABLE:
            return Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=self.console
            )
        else:
            return self._FallbackProgress(description)

    class _FallbackProgress:
        def __init__(self, description):
            self.description = description

        def __enter__(self):
            print(f"🔄 {self.description}...")
            return self

        def __exit__(self, *args):
            print(f"✅ {self.description} completed!")

        def add_task(self, description, total=100):
            return 0

        def update(self, task_id, advance=1):
            print(".", end="", flush=True)

class GitHubServerMonitorUploader:
    """Advanced GitHub uploader for Server Network Topology Monitor"""

    def __init__(self):
        self.output = BeautifulOutput()
        self.resolver = ConflictResolver(self.output)
        self.config = CONFIG.copy()
        self.git_path = None

        # Validate configuration
        self._validate_config()

        self.repo_url = f"https://github.com/{self.config['username']}/{self.config['repo_name']}.git"

        # Statistics
        self.stats = {
            'files_copied': 0,
            'directories_created': 0,
            'total_size': 0,
            'conflicts_resolved': 0,
            'processes_killed': 0,
            'start_time': time.time()
        }

        # Headers for GitHub API
        self.headers = {
            "Authorization": f"token {self.config['token']}",
            "Accept": "application/vnd.github.v3+json"
        }

    def _validate_config(self):
        """Validate configuration"""
        if not os.path.exists(self.config['source_dir']):
            self.output.print_error(f"❌ Source directory not found: {self.config['source_dir']}")
            self.output.print_info("🔧 Please check the source directory path")
            sys.exit(1)

        if not self.config['username'] or not self.config['token'] or "TU-" in self.config['username'] or "TU-" in self.config['token']:
            self.output.print_error("❌ GitHub credentials missing!")
            self.output.print_info("🔑 Please edit the script and replace 'TU-USERUL-TAU-GITHUB' and 'TU-TOKEN-UL-TAU-GITHUB'")
            sys.exit(1)

    def run(self):
        """Enhanced execution flow with conflict resolution"""
        try:
            self.output.print_banner()

            steps = [
                ("🔍 Pre-flight Checks", "Checking for conflicts and preparing environment"),
                ("🔧 Initializing Environment", "Setting up tools and checking requirements"),
                ("🧹 Preparing Workspace", "Cleaning previous attempts and preparing directory"),
                ("🏗️ Managing GitHub Repository", "Creating or updating remote repository"),
                ("📁 Preparing Python Files", "Copying application files and database"),
                ("🔄 Initializing Git Repository", "Setting up local Git repository"),
                ("🚀 Uploading to GitHub", "Pushing Server Monitor to remote repository"),
                ("🧹 Final Cleanup", "Removing temporary files and finalizing")
            ]

            for i, (title, description) in enumerate(steps, 1):
                self.output.print_step(i, len(steps), title, description)
                
                if i == 1:
                    self._preflight_checks()
                elif i == 2:
                    self._initialize()
                elif i == 3:
                    self._prepare_workspace()
                elif i == 4:
                    self._handle_repository()
                elif i == 5:
                    self._prepare_files_with_progress()
                elif i == 6:
                    self._initialize_repo()
                elif i == 7:
                    self._push_to_github()
                elif i == 8:
                    self._cleanup()

            self._print_success_summary()

        except KeyboardInterrupt:
            self.output.print_warning("🛑 Upload cancelled by user")
            self._emergency_cleanup()
            sys.exit(0)
        except Exception as e:
            self.output.print_error(f"Upload failed: {str(e)}")
            self._emergency_cleanup()
            self._print_troubleshooting_guide()
            sys.exit(1)

    def _preflight_checks(self):
        """Enhanced preflight checks"""
        with self.output.create_progress_bar("🔍 Running pre-flight checks") as progress:
            task = progress.add_task("Checking system...", total=100)

            progress.update(task, advance=25)
            if not os.path.exists(self.config['source_dir']):
                raise FileNotFoundError(f"Source directory not found: {self.config['source_dir']}")

            progress.update(task, advance=25)
            killed = self.resolver.kill_git_processes()
            self.stats['processes_killed'] = killed

            progress.update(task, advance=25)
            repo_exists = self.resolver.check_repository_exists(
                self.config['username'], self.config['repo_name'], self.headers
            )

            if repo_exists:
                self.stats['conflicts_resolved'] += 1
                action, new_name = self.resolver.resolve_repository_conflict(
                    self.config['username'], self.config['repo_name'], self.headers
                )
                if new_name != self.config['repo_name']:
                    self.config['repo_name'] = new_name
                    self.repo_url = f"https://github.com/{self.config['username']}/{new_name}.git"
                    self.output.print_info(f"📝 Repository name updated to: {new_name}")

            progress.update(task, advance=25)

    def _prepare_workspace(self):
        """Enhanced workspace preparation"""
        with self.output.create_progress_bar("🧹 Preparing workspace") as progress:
            task = progress.add_task("Cleaning workspace...", total=100)

            progress.update(task, advance=50)
            if os.path.exists(self.config['work_dir']):
                success = self.resolver.force_remove_directory(self.config['work_dir'])
                if not success:
                    timestamp = int(time.time())
                    self.config['work_dir'] = f"{self.config['work_dir']}_{timestamp}"

            progress.update(task, advance=50)
            os.makedirs(self.config['work_dir'], exist_ok=True)

    def _initialize(self):
        """Initialize with enhanced error handling"""
        with self.output.create_progress_bar("🔧 Initializing") as progress:
            task = progress.add_task("Setting up environment...", total=100)

            progress.update(task, advance=50)
            self.git_path = self._find_git()
            self.output.print_success(f"Git found: {self.git_path}")

            progress.update(task, advance=50)
            if not os.path.exists(self.config['source_dir']):
                raise FileNotFoundError(f"Source directory not found: {self.config['source_dir']}")

    def _find_git(self):
        """Find Git with enhanced error reporting"""
        for path in GIT_PATHS:
            try:
                result = subprocess.run([path, "--version"], check=True,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return path
            except FileNotFoundError:
                continue
            except Exception as e:
                continue

        self.output.print_error("Git not found. Please install Git:")
        self.output.print_info("📥 Download from: https://git-scm.com/download/windows")
        raise Exception("Git not found")

    def _handle_repository(self):
        """Handle repository creation"""
        with self.output.create_progress_bar("🏗️ Managing repository") as progress:
            task = progress.add_task("Creating repository...", total=100)

            url = "https://api.github.com/user/repos"
            data = {
                "name": self.config['repo_name'],
                "description": f"🖥️ Server Network Topology Monitor - Aplicație Python/Tkinter profesională pentru monitorizarea infrastructurii IT cu interfață modernă, bază de date Excel, sistem alerting avansat și management complet al serverelor - Uploaded {time.strftime('%Y-%m-%d %H:%M')}",
                "private": False,
                "auto_init": False
            }

            progress.update(task, advance=50)

            try:
                response = requests.post(url, json=data, headers=self.headers)
                if response.status_code not in [200, 201]:
                    if response.status_code == 422:
                        self.output.print_warning(f"Repository '{self.config['repo_name']}' already exists - will update it")
                    else:
                        raise Exception(f"GitHub API error {response.status_code}: {response.text}")
                else:
                    self.output.print_success(f"Repository '{self.config['repo_name']}' created successfully")

                progress.update(task, advance=50)
                time.sleep(3)

            except Exception as e:
                raise Exception(f"Repository management failed: {str(e)}")

    def _prepare_files_with_progress(self):
        """Prepare files with enhanced progress tracking"""
        total_files = sum(1 for f in Path(self.config['source_dir']).rglob('*') if f.is_file())

        with self.output.create_progress_bar("📁 Copying Server Monitor files") as progress:
            task = progress.add_task("Copying files...", total=total_files)

            for root, dirs, files in os.walk(self.config['source_dir']):
                dirs[:] = [d for d in dirs if not any(ignore in d for ignore in self.config['ignore_files'])]

                rel_path = os.path.relpath(root, self.config['source_dir'])
                dest_dir = os.path.join(self.config['work_dir'], rel_path)

                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
                    self.stats['directories_created'] += 1

                for file in files:
                    if not any(file.endswith(ext.replace('*', '')) for ext in self.config['ignore_files'] if ext.startswith('*')):
                        try:
                            src_file = os.path.join(root, file)
                            dest_file = os.path.join(dest_dir, file)

                            shutil.copy2(src_file, dest_file)
                            self.stats['files_copied'] += 1
                            self.stats['total_size'] += os.path.getsize(src_file)

                            progress.update(task, advance=1)
                        except Exception as e:
                            self.output.print_warning(f"⚠️ Skipped file {file}: {e}")
                            continue

        self.output.print_success(f"Copied {self.stats['files_copied']} files ({self._format_size(self.stats['total_size'])})")

    def _initialize_repo(self):
        """Initialize repository"""
        os.chdir(self.config['work_dir'])

        with self.output.create_progress_bar("🔄 Initializing Git") as progress:
            task = progress.add_task("Setting up Git...", total=100)

            try:
                subprocess.run([self.git_path, "init"], check=True, capture_output=True)
                progress.update(task, advance=20)

                subprocess.run([self.git_path, "branch", "-M", "main"], check=True, capture_output=True)
                progress.update(task, advance=20)

                progress.update(task, advance=20)
                self._create_enhanced_readme()

                progress.update(task, advance=20)
                self._create_gitignore()

                subprocess.run([self.git_path, "add", "."], check=True, capture_output=True)
                subprocess.run([self.git_path, "commit", "-m", "🚀 Initial commit - Server Network Topology Monitor"],
                             check=True, capture_output=True)
                progress.update(task, advance=20)

            except subprocess.CalledProcessError as e:
                raise Exception(f"Git initialization failed: {e.stderr.decode() if e.stderr else 'Unknown error'}")

    def _push_to_github(self):
        """Push to GitHub"""
        os.chdir(self.config['work_dir'])

        with self.output.create_progress_bar("🚀 Uploading to GitHub") as progress:
            task = progress.add_task("Pushing to remote...", total=100)

            try:
                auth_repo_url = f"https://{self.config['username']}:{self.config['token']}@github.com/{self.config['username']}/{self.config['repo_name']}.git"

                subprocess.run([self.git_path, "remote", "remove", "origin"], capture_output=True)
                subprocess.run([self.git_path, "remote", "add", "origin", auth_repo_url], check=True, capture_output=True)
                progress.update(task, advance=30)

                push_result = subprocess.run([self.git_path, "push", "-u", "origin", "main"], capture_output=True)
                if push_result.returncode != 0:
                    push_result = subprocess.run([self.git_path, "push", "-f", "-u", "origin", "main"], check=True, capture_output=True)

                progress.update(task, advance=70)

            except subprocess.CalledProcessError as e:
                error_msg = e.stderr.decode('utf-8', errors='ignore') if e.stderr else 'Unknown Git error'
                raise Exception(f"Git push failed: {error_msg}")

    def _cleanup(self):
        """Enhanced cleanup"""
        success = self.resolver.force_remove_directory(self.config['work_dir'])
        if success:
            self.output.print_success("Temporary files cleaned up")
        else:
            self.output.print_warning(f"⚠️ Could not fully clean: {self.config['work_dir']}")

    def _emergency_cleanup(self):
        """Emergency cleanup on failure"""
        try:
            self.resolver.force_remove_directory(self.config['work_dir'])
        except:
            pass

    def _create_enhanced_readme(self):
        """Create comprehensive README for Server Monitor"""
        readme_content = f"""# 🖥️ Server Network Topology Monitor - Professional IT Infrastructure Management

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org/)
[![Tkinter](https://img.shields.io/badge/GUI-Tkinter-green.svg)](https://docs.python.org/3/library/tkinter.html)
[![Pandas](https://img.shields.io/badge/Data-Pandas-orange.svg)](https://pandas.pydata.org/)
[![Excel](https://img.shields.io/badge/Database-Excel-brightgreen.svg)](https://openpyxl.readthedocs.io/)
[![GitHub](https://img.shields.io/badge/GitHub-{self.config['username']}-black.svg)](https://github.com/{self.config['username']})

> 🏆 **Aplicație desktop Python/Tkinter profesională pentru monitorizarea și managementul infrastructurii IT cu interfață modernă, sistem de alerting avansat și integrare completă cu baza de date Excel.**
>
> 📅 **Uploaded:** {time.strftime('%Y-%m-%d %H:%M:%S')}
>
> 🚀 **Auto-uploaded** with GitHub Server Monitor Uploader Pro v3.0

## 🌟 Caracteristici Principale

### 🎛️ **Dashboard Modern & Intuitiv**
- **Layout vertical** cu topologie de rețea în grid 2×3 (maxim 6 servere per tab)
- **Tabs multiple** pentru organizarea serverelor (scalabilitate nelimitată)
- **Interfață dark theme** profesională cu accent colors moderne
- **Context menu** cu click dreapta pentru acțiuni rapide
- **Highlight vizual** pentru servere selectate cu feedback instant

### 📊 **Sistem Monitorizare în Timp Real**
- **Monitorizare continuă** în background cu thread dedicat (actualizare la 15 secunde)
- **Metrici complete**: CPU Usage, RAM Usage, Disk Usage, Network I/O, Performance Score
- **Progress bars animate** cu codificare color pentru threshold-uri
- **Uptime tracking** precis cu conversie ore/zile
- **Status real-time** cu detectare automată a schimbărilor

### 🚨 **Sistem Alerting Inteligent**
- **Threshold-uri configurabile**: CPU >90% (critic), RAM >85% (warning), Disk >90% (critic)
- **Alerting automat** pentru probleme critice cu nivele de severitate
- **Istoric alerte** cu timestamp și categorii (info, success, warning, critical)
- **Feedback vizual** cu flash effects și sunet sistem pentru alerte critice
- **Management alerte** cu posibilitate de clear și filtrare

### 🔧 **Management Complet Servere**
- **CRUD complet**: Create, Read, Update, Delete cu validări avansate
- **Formuri interactive** cu header-buttons pentru salvare rapidă
- **Editare proprietăți** cu detectare automată a modificărilor
- **Restart simulat** cu animații și feedback vizual
- **Test performanță** comprehensive cu rezultate detaliate
- **Management loguri** cu editare și salvare în Excel

### 📈 **Bază de Date Excel Avansată**
- **Auto-backup** înainte de fiecare salvare cu versioning
- **Structură auto-repair** pentru compatibilitate cu Excel-uri existente
- **Gestionare conflicte** când Excel-ul este deschis
- **Export/Import** seamless cu păstrarea formatului
- **Validări de integritate** și reparare automată a structurii

### ⚡ **Arhitectură Tehnică Modernă**
- **Multi-threading** pentru UI responsive și monitorizare background
- **Memory management** optimizat pentru performanță
- **Error handling** robust cu recovery automat
- **Scroll îmbunătățit** cu mouse wheel support
- **Layout responsive** cu dimensiuni dinamice

## 🚀 Setup și Utilizare

### 📋 **Cerințe Sistem**
```bash
Python 3.8+ (recomandat 3.9+)
pandas >= 1.3.0
openpyxl >= 3.0.0
tkinter (inclus în Python standard)
```

### ⚡ **Instalare în 2 Pași**

1️⃣ **Clonează repository-ul**
```bash
git clone {self.repo_url}
cd {self.config['repo_name']}
```

2️⃣ **Instalează dependențele și pornește**
```bash
pip install pandas openpyxl
python "Aplicatie Complexa FINAL.py"
```

### 🔧 **Instalare Dependențe**
```bash
# Instalare completă cu toate extensiile
pip install pandas openpyxl xlsxwriter

# Pentru output îmbunătățit (opțional)
pip install rich colorama

# Pentru monitorizare procese (opțional)
pip install psutil
```

## 📁 Structura Proiect

```
{self.config['repo_name']}/
├── 📄 Aplicatie Complexa FINAL.py    # 🏆 Aplicația principală (131.7KB)
├── 📊 server_database.xlsx           # Baza de date servere (cu backup)
├── 📋 Idei de imbunatatire.txt      # Ghid îmbunătățiri și features viitoare
├── 🚀 GITHUB UPLOADER PRO v3.0.py   # Script auto-upload GitHub
├── 📜 Topologie retea 0.py          # Versiune simplă (pentru studiu)
├── 📜 Topologie retea 1.py          # Versiune intermediară
├── 📜 Topologie retea 2.py          # Versiune avansată
└── 📖 README.md                     # Documentație completă
```

## 🎯 Funcționalități Detaliate

### 🖥️ **Interfață Utilizator Avansată**
- **Multi-tab system** pentru organizarea serverelor în grupuri logice
- **Server grid 2×3** cu vizualizare intuitivă și click-to-detail
- **Context menu** complet cu toate opțiunile (Detalii, Restart, Edit, Delete)
- **Panels layout** cu topologie + detalii & control cu scroll optimizat
- **Theme modern** dark cu accente de culoare și animații fluide

### 📈 **Monitorizare și Metrici**
- **8 tipuri de metrici** monitorizate în continuu
- **Performance score** calculat dinamic pe baza tuturor metricilor
- **Network monitoring** cu traffic in/out simulation
- **Uptime calculation** precis cu conversii automate
- **Threshold detection** cu alerting automat

### 🔄 **Background Processing**
- **Thread separat** pentru monitorizare non-blocking
- **Auto-refresh** la 15 secunde cu simulare date realiste
- **Status changes** detectate automat cu recovery logic
- **Memory cleanup** și resource management optimizat
- **Error recovery** automat pentru situații neprevăzute

### 🎨 **Design System Professional**
- **Color coding** pentru statusuri (🟢 Online, 🟡 Warning, 🔴 Offline)
- **Progress bars** animate cu threshold colors
- **Micro-animations** pentru feedback utilizator
- **Flash effects** pentru acțiuni importante
- **Responsive design** pentru diferite rezoluții

## 🔧 Configurare și Personalizare

### ⚙️ **Configurări Avansate**
```python
# În fișierul principal, secțiunea de configurare:
CONFIG = {{
    'max_servers_per_tab': 6,          # Servere per tab
    'monitoring_interval': 15,          # Secunde între verificări
    'alert_thresholds': {{
        'cpu_critical': 90,             # CPU critic %
        'ram_warning': 85,              # RAM warning %
        'disk_critical': 90             # Disk critic %
    }},
    'backup_retention': 5               # Număr backup-uri păstrate
}}
```

### 🎛️ **Personalizare Interfață**
- **Tema de culori** modificabilă în secțiunea `setup_styles()`
- **Dimensiuni layout** configurabile pentru diferite ecrane
- **Font customization** pentru accessibility
- **Animation timing** ajustabil pentru performanță

## 📊 Upload Statistics

- 📁 **Files Uploaded:** {self.stats['files_copied']}
- 📂 **Directories Created:** {self.stats['directories_created']}
- 💾 **Total Size:** {self._format_size(self.stats['total_size'])}
- 🛠️ **Conflicts Resolved:** {self.stats['conflicts_resolved']}
- 🔄 **Processes Cleaned:** {self.stats['processes_killed']}

## 🎯 Roadmap și Dezvoltare Viitoare

### v2.0 Enterprise Features
- [ ] **Database integration** cu SQL Server/PostgreSQL
- [ ] **Web dashboard** complementar cu API REST
- [ ] **Email notifications** pentru alerte critice
- [ ] **Historical data** cu charts și trends analysis
- [ ] **User authentication** și role-based access

### v3.0 Advanced Monitoring
- [ ] **SNMP integration** pentru monitoring real de echipamente
- [ ] **Network discovery** automat pentru servere noi
- [ ] **Custom metrics** configurabile de utilizator
- [ ] **Docker/container** monitoring support
- [ ] **Cloud integration** (AWS, Azure, GCP)

### v4.0 AI & Automation
- [ ] **Predictive maintenance** cu machine learning
- [ ] **Anomaly detection** automat
- [ ] **Auto-scaling** recommendations
- [ ] **Chatbot integration** pentru support
- [ ] **Mobile app** companion

## 💡 Utilizare și Best Practices

### 🚀 **Quick Start Guide**
1. **Lansează aplicația** - dublu-click pe `Aplicatie Complexa FINAL.py`
2. **Explorează serverele** - click pe orice server din grid pentru detalii
3. **Adaugă servere noi** - buton "➕ Adaugă Server" cu formular complet
4. **Monitorizează în timp real** - aplicația se actualizează automat
5. **Gestionează alertele** - panoul de alerte afișează problemele detectate

### 🔧 **Sfaturi de Administrare**
- **Backup regulat** - Excel-ul se salvează automat cu backup
- **Monitorizare threshold-uri** - ajustează valorile pentru infrastructura ta
- **Organizare în tabs** - grupează serverele logic (de ex: Production, Staging, Development)
- **Review periodic** al logurilor pentru detectarea pattern-urilor
- **Testare performanță** regulată pentru optimizare

### ⚠️ **Troubleshooting Common Issues**
- **Excel locked error** - închide Excel înainte de modificări majore
- **Performance issues** - reduce numărul de servere monitorizate simultan
- **Memory usage** - restartează aplicația periodic pentru cleanup
- **Thread conflicts** - evită modificările simultane din multiple instanțe

## 🤝 Contributing & Support

### 🛠️ **Development Setup**
```bash
# Clone repository
git clone {self.repo_url}
cd {self.config['repo_name']}

# Install development dependencies
pip install pandas openpyxl rich colorama psutil

# Run application
python "Aplicatie Complexa FINAL.py"
```

### 📝 **Contribution Guidelines**
1. **Fork** repository-ul
2. **Create feature branch** (`git checkout -b feature/AmazingFeature`)
3. **Test thoroughly** - aplicația gestionează date critice
4. **Document changes** - update README și comentarii cod
5. **Submit Pull Request** cu descriere detaliată

### 🐛 **Bug Reports**
Pentru raportarea bug-urilor, include:
- **Python version** și OS details
- **Stack trace** complet pentru erori
- **Steps to reproduce** cu date de test
- **Expected vs actual behavior**
- **Screenshots** pentru probleme UI

## 📜 License & Acknowledgments

Distributed under the MIT License. See `LICENSE` for more information.

### 🙏 **Special Thanks**
- **pandas** team pentru data management excelent
- **tkinter** pentru GUI framework robust și cross-platform
- **openpyxl** pentru integrare Excel seamless
- **Python community** pentru ecosystem bogat

---

<div align="center">

**🖥️ Dezvoltat cu pasiune pentru administrarea infrastructurii IT și tehnologii Python moderne! 🖥️**

🤖 **Auto-uploaded** with [GitHub Server Monitor Uploader Pro](https://github.com/{self.config['username']})

⭐ **Dacă îți place proiectul, oferă o stea!** ⭐

🚀 **Ready for production deployment in enterprise environments!** 🚀

**🎯 Perfect pentru administratorii IT care au nevoie de monitoring rapid și eficient! 🎯**

</div>

---

### 📞 Contact & Professional Use

Această aplicație a fost dezvoltată pentru administrarea profesională a infrastructurii IT. 
Pentru consultanță sau customizări enterprise, contactați dezvoltatorul prin GitHub Issues.

**🏢 Enterprise features available upon request!**
"""

        with open("README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)

    def _create_gitignore(self):
        """Create gitignore for Python project"""
        gitignore_content = """# 🖥️ Server Network Topology Monitor - GitIgnore

# 🐍 Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
develop-eggs/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# 🔒 Environment & Config
.env
.venv
venv/
ENV/
env.bak/
venv.bak/

# 🖥️ OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
desktop.ini

# 🔧 IDEs and editors
.vscode/
.idea/
*.swp
*.swo
*~
.sublime-project
.sublime-workspace

# 📊 Logs and temporary files
*.log
*.tmp
*.temp
*.bak
*.swp
*.swo
*~

# 📁 Project specific
backup/
temp/
cache/
uploads/

# 🔄 Server Monitor specific
*.xlsx.backup
server-logs/
monitoring-data/
performance-reports/
"""
        with open(".gitignore", "w", encoding="utf-8") as f:
            f.write(gitignore_content)

    def _print_success_summary(self):
        """Enhanced success summary"""
        elapsed_time = time.time() - self.stats['start_time']

        if RICH_AVAILABLE:
            success_text = f"""
🎉 SERVER NETWORK TOPOLOGY MONITOR UPLOADED SUCCESSFULLY! 🎉

✅ Your professional Python/Tkinter monitoring system is now live on GitHub!
🔗 Access it at: {self.repo_url}

🚀 Quick Start Commands:
  git clone {self.repo_url}
  cd {self.config['repo_name']}
  pip install pandas openpyxl
  python "Aplicatie Complexa FINAL.py"

⚡ What's included:
  • 🖥️ Professional Python/Tkinter Desktop Application (131.7KB)
  • 📊 Advanced Excel database integration with auto-backup
  • 🚨 Real-time monitoring system with multi-threading
  • 🔧 Complete CRUD operations for server management  
  • 📈 Performance testing and analytics tools
  • 🎨 Modern dark theme with responsive design
  • 🔄 Background monitoring with smart alerting system
  • 📱 Context menus and advanced UI interactions

💡 Key Features:
  • 👀 Multi-tab server organization (6 servers per tab)
  • 📝 Excel integration with conflict resolution
  • 🌟 Professional IT infrastructure management
  • 🔄 Real-time status updates and performance metrics
  • 📊 Advanced reporting and alert system

🛠️ Professional upload completed with:
  • 🔍 Advanced conflict detection and resolution
  • 🧹 Multi-method cleanup system for robust deployment
  • 🔄 Git process management and optimization
  • 📝 Intelligent repository handling
  • 📊 Comprehensive upload statistics and reporting
            """

            success_panel = Panel(
                Align.center(Text(success_text, style="bold green")),
                border_style="bright_green",
                title="[bold yellow]🏆 PYTHON SERVER MONITOR UPLOAD SUCCESS! 🏆[/bold yellow]",
                subtitle="[italic]Professional IT Infrastructure Management System Ready![/italic]"
            )

            self.output.console.print(success_panel)
        else:
            self.output.print_success("SERVER NETWORK TOPOLOGY MONITOR UPLOAD COMPLETED!")
            print(f"\n📊 Upload Statistics:")
            print(f"   📁 Files: {self.stats['files_copied']}")
            print(f"   💾 Size: {self._format_size(self.stats['total_size'])}")
            print(f"   ⏱️ Time: {elapsed_time:.1f}s")
            print(f"\n🔗 Repository: {self.repo_url}")

    def _print_troubleshooting_guide(self):
        """Print troubleshooting guide"""
        if RICH_AVAILABLE:
            guide = """
🔧 SERVER MONITOR TROUBLESHOOTING GUIDE

Common issues and solutions:

1️⃣ **Configuration Issues**
   • Edit script and replace 'TU-USERUL-TAU-GITHUB' with your GitHub username
   • Replace 'TU-TOKEN-UL-TAU-GITHUB' with your GitHub personal access token
   • Ensure token has 'repo' permissions for public repositories

2️⃣ **Source Directory Issues**
   • Verify the path exists: e:\\Carte\\BB\\17 - Site Leadership\\...\\Topologie retea\\
   • Check that 'Aplicatie Complexa FINAL.py' is present
   • Ensure all files are accessible (not locked by other programs)

3️⃣ **Python Dependencies**
   • Install required packages: pip install pandas openpyxl
   • For enhanced output: pip install rich colorama psutil
   • Verify Python 3.8+ is installed

4️⃣ **Repository Conflicts**
   • Choose 'update' to push to existing repository
   • Choose 'rename' for alternative repository name
   • Suggested names: Python-Server-Monitor, IT-Network-Dashboard

5️⃣ **File Access Issues**
   • Close Excel if server_database.xlsx is open
   • Run as Administrator for file permission issues
   • Kill any running Git processes blocking files

6️⃣ **GitHub Token Setup**
   • Go to GitHub Settings → Developer Settings → Personal Access Tokens
   • Generate new token → Select 'repo' scope for full repository access
   • Copy token and replace in script configuration

💡 After successful upload:
   1. Clone repository: git clone [repo-url]
   2. Install dependencies: pip install pandas openpyxl  
   3. Run application: python "Aplicatie Complexa FINAL.py"
   4. Test all features: server monitoring, alerts, Excel integration

🎯 Application Features to Test:
   • Desktop GUI loads with modern dark theme
   • Server grid displays with status indicators
   • Click servers → details panel updates
   • Add/Edit server → forms work correctly
   • Excel database → saves and loads properly
   • Background monitoring → updates every 15 seconds
            """

            panel = Panel(
                Text(guide, style="yellow"),
                border_style="red",
                title="[bold red]🛠️ SERVER MONITOR TROUBLESHOOTING[/bold red]"
            )
            self.output.console.print(panel)

    def _format_size(self, size_bytes):
        """Format file size"""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"

def main():
    """Main entry point"""
    print("🖥️ SERVER NETWORK TOPOLOGY MONITOR - GITHUB UPLOADER PRO v3.0 🖥️")
    print("=" * 80)

    # Check for required libraries
    missing_libs = []
    if not RICH_AVAILABLE:
        missing_libs.append("rich")
    if not COLORAMA_AVAILABLE:
        missing_libs.append("colorama")

    try:
        import psutil
    except ImportError:
        missing_libs.append("psutil")

    if missing_libs:
        print("⚠️  For enhanced functionality, install optional libraries:")
        print(f"   pip install {' '.join(missing_libs)}")
        print("   🎨 This adds beautiful output and advanced process management!")
        print("\n🚀 Continuing with basic functionality...\n")

    # Run the uploader
    try:
        uploader = GitHubServerMonitorUploader()
        uploader.run()
    except KeyboardInterrupt:
        print("\n🛑 Server Monitor upload cancelled by user")
        sys.exit(0)

if __name__ == "__main__":
    main()
