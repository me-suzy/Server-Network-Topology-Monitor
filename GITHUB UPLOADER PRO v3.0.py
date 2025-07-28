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

# Configuration for Server Dashboard IT
CONFIG = {
    'source_dir': r"d:\Server-Dashboard-IT",
    'username': "me-suzy",
    'token': "ghp_YOUR-TOKEN",
    'repo_name': "Server-Dashboard-IT-Monitoring",
    'work_dir': r"D:\temp_github_upload_dashboard",
    'ignore_files': [
        '.git', '__pycache__', 'venv', '.env', '*.pyc', '*.log', '*.tmp',
        'node_modules', '.vscode', '.idea', 'dist', 'build'
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
            f"{original_name}-v2",
            f"{original_name}-{timestamp}",
            f"{original_name}-Advanced",
            f"IT-Dashboard-Monitoring",
            f"Server-Monitor-Dashboard"
        ]

        # Reserved/invalid names on GitHub
        reserved_names = [
            'update', 'delete', 'create', 'new', 'edit', 'settings', 'admin',
            'api', 'www', 'mail', 'ftp', 'blog', 'docs', 'help', 'support',
            'git', 'github', 'gitlab', 'bitbucket', 'master', 'main'
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

            # Validate name
            if self._validate_repo_name(new_name, reserved_names):
                return "create", new_name
            else:
                self.output.print_error(f"❌ Invalid name '{new_name}'. Please choose another.")

    def _validate_repo_name(self, name, reserved_names):
        """Validate GitHub repository name"""
        if not name:
            self.output.print_error("Repository name cannot be empty")
            return False

        if len(name) > 100:
            self.output.print_error("Repository name too long (max 100 characters)")
            return False

        if name.lower() in reserved_names:
            self.output.print_error(f"'{name}' is a reserved name on GitHub")
            return False

        # Check for invalid characters
        import re
        if not re.match(r'^[a-zA-Z0-9._-]+$', name):
            self.output.print_error("Repository name can only contain letters, numbers, dots, hyphens, and underscores")
            return False

        if name.startswith('.') or name.endswith('.'):
            self.output.print_error("Repository name cannot start or end with a dot")
            return False

        if name.startswith('-') or name.endswith('-'):
            self.output.print_error("Repository name cannot start or end with a hyphen")
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

        # Delete repository
        url = f"https://api.github.com/repos/{username}/{repo_name}"
        response = requests.delete(url, headers=headers)

        if response.status_code == 204:
            self.output.print_success(f"🗑️ Repository '{repo_name}' deleted successfully")
            time.sleep(2)  # Wait for GitHub to process
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
            self._method_git_clean,
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
        """Normal directory removal"""
        shutil.rmtree(path)
        return not os.path.exists(path)

    def _method_chmod_removal(self, path):
        """Remove with chmod modification"""
        def handle_remove_readonly(func, path, exc):
            if os.path.exists(path):
                os.chmod(path, stat.S_IWRITE)
                func(path)

        shutil.rmtree(path, onerror=handle_remove_readonly)
        return not os.path.exists(path)

    def _method_git_clean(self, path):
        """Use git clean to remove files"""
        try:
            os.chdir(path)
            subprocess.run(["git", "clean", "-fdx"], capture_output=True)
            os.chdir("..")
            shutil.rmtree(path)
            return not os.path.exists(path)
        except:
            return False

    def _method_process_kill_removal(self, path):
        """Kill processes and then remove"""
        self.kill_git_processes()
        time.sleep(2)
        shutil.rmtree(path)
        return not os.path.exists(path)

    def _method_temp_move_removal(self, path):
        """Move to temp and schedule for deletion"""
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, "to_delete")
        shutil.move(path, temp_path)

        # Try to remove from temp
        try:
            shutil.rmtree(temp_path)
        except:
            # If fails, it will be cleaned by system temp cleanup
            pass

        return not os.path.exists(path)

class BeautifulOutput:
    """Enhanced output handler with conflict resolution"""

    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None

    def print_banner(self):
        """Print enhanced banner"""
        if RICH_AVAILABLE:
            banner = """
    🖥️ SERVER DASHBOARD IT UPLOADER 🖥️
    ════════════════════════════════════════
    🚀 Automated GitHub Repository Creator
    📁 Smart File Management System
    🎯 Professional Git Workflow
    🛠️ ADVANCED CONFLICT RESOLUTION
    🔧 PERMISSION ISSUE RESOLVER
    ⚡ REACT + VITE + TAILWIND READY
    """
            panel = Panel(
                Align.center(Text(banner, style="bold blue")),
                border_style="bright_green",
                title="[bold yellow]🏆 IT DASHBOARD GITHUB UPLOADER PRO 🏆[/bold yellow]",
                subtitle="[italic]v3.0 - Server Monitoring Dashboard Ready![/italic]"
            )
            self.console.print(panel)
        else:
            self._fallback_banner()

    def _fallback_banner(self):
        """Enhanced fallback banner"""
        if COLORAMA_AVAILABLE:
            print(f"\n{Fore.CYAN}{'='*70}")
            print(f"{Fore.YELLOW}🖥️ SERVER DASHBOARD IT UPLOADER 🖥️")
            print(f"{Fore.GREEN}🚀 Automated GitHub Repository Creator")
            print(f"{Fore.BLUE}📁 Smart File Management System")
            print(f"{Fore.MAGENTA}🎯 Professional Git Workflow")
            print(f"{Fore.RED}🛠️ ADVANCED CONFLICT RESOLUTION")
            print(f"{Fore.YELLOW}🔧 PERMISSION ISSUE RESOLVER")
            print(f"{Fore.CYAN}⚡ REACT + VITE + TAILWIND READY")
            print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
        else:
            print("\n" + "="*70)
            print("🖥️ SERVER DASHBOARD IT UPLOADER 🖥️")
            print("🚀 Automated GitHub Repository Creator")
            print("📁 Smart File Management System")
            print("🎯 Professional Git Workflow")
            print("🛠️ ADVANCED CONFLICT RESOLUTION")
            print("🔧 PERMISSION ISSUE RESOLVER")
            print("⚡ REACT + VITE + TAILWIND READY")
            print("="*70 + "\n")

    def print_step(self, step_num, total_steps, title, description=""):
        """Print step with enhanced formatting"""
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
            self._fallback_step(step_num, total_steps, title, description)

    def _fallback_step(self, step_num, total_steps, title, description=""):
        if COLORAMA_AVAILABLE:
            print(f"\n{Fore.CYAN}📋 Step {step_num}/{total_steps} - {Fore.GREEN}{title}")
            if description:
                print(f"{Fore.YELLOW}   💡 {description}")
        else:
            print(f"\n📋 Step {step_num}/{total_steps} - {title}")
            if description:
                print(f"   💡 {description}")

    def print_success(self, message):
        if RICH_AVAILABLE:
            self.console.print(f"[bold green]✅ {message}[/bold green]")
        elif COLORAMA_AVAILABLE:
            print(f"{Fore.GREEN}✅ {message}")
        else:
            print(f"✅ {message}")

    def print_error(self, message):
        if RICH_AVAILABLE:
            self.console.print(f"[bold red]❌ {message}[/bold red]")
        elif COLORAMA_AVAILABLE:
            print(f"{Fore.RED}❌ {message}")
        else:
            print(f"❌ {message}")

    def print_info(self, message):
        if RICH_AVAILABLE:
            self.console.print(f"[bold blue]ℹ️  {message}[/bold blue]")
        elif COLORAMA_AVAILABLE:
            print(f"{Fore.BLUE}ℹ️  {message}")
        else:
            print(f"ℹ️  {message}")

    def print_warning(self, message):
        if RICH_AVAILABLE:
            self.console.print(f"[bold yellow]⚠️  {message}[/bold yellow]")
        elif COLORAMA_AVAILABLE:
            print(f"{Fore.YELLOW}⚠️  {message}")
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

class GitHubDashboardUploader:
    """Advanced GitHub uploader for Server Dashboard IT"""

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
        # Basic validation - ensure directory exists
        if not os.path.exists(self.config['source_dir']):
            self.output.print_error(f"❌ Source directory not found: {self.config['source_dir']}")
            self.output.print_info("🔧 Please check the source directory path")
            sys.exit(1)

        # Validate GitHub credentials are present
        if not self.config['username'] or not self.config['token']:
            self.output.print_error("❌ GitHub credentials missing!")
            self.output.print_info("🔑 Please check username and token configuration")
            sys.exit(1)

    def run(self):
        """Enhanced execution flow with conflict resolution"""
        try:
            self.output.print_banner()

            # Step 0: Pre-check and conflict resolution
            self.output.print_step(0, 7, "🔍 Pre-flight Checks",
                                 "Checking for conflicts and preparing environment")
            self._preflight_checks()

            # Step 1: Initialize
            self.output.print_step(1, 7, "🔧 Initializing Environment",
                                 "Setting up tools and checking requirements")
            self._initialize()

            # Step 2: Cleanup and prepare workspace
            self.output.print_step(2, 7, "🧹 Preparing Workspace",
                                 "Cleaning previous attempts and preparing directory")
            self._prepare_workspace()

            # Step 3: Handle repository creation/conflict
            self.output.print_step(3, 7, "🏗️  Managing GitHub Repository",
                                 "Creating or updating remote repository")
            self._handle_repository()

            # Step 4: Prepare files
            self.output.print_step(4, 7, "📁 Preparing Dashboard Files",
                                 "Copying React app, Python scripts, and documentation")
            self._prepare_files_with_progress()

            # Step 5: Initialize Git
            self.output.print_step(5, 7, "🔄 Initializing Git Repository",
                                 "Setting up local Git repository")
            self._initialize_repo()

            # Step 6: Push to GitHub
            self.output.print_step(6, 7, "🚀 Uploading to GitHub",
                                 "Pushing Server Dashboard to remote repository")
            self._push_to_github()

            # Step 7: Finalize
            self.output.print_step(7, 7, "🧹 Final Cleanup",
                                 "Removing temporary files and finalizing")
            self._cleanup()

            # Success summary
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

            # Check source directory
            progress.update(task, advance=20)
            if not os.path.exists(self.config['source_dir']):
                raise FileNotFoundError(f"Source directory not found: {self.config['source_dir']}")

            # Check if user is admin
            progress.update(task, advance=20)
            try:
                is_admin = os.getuid() == 0
            except AttributeError:
                is_admin = subprocess.run(["net", "session"], capture_output=True).returncode == 0

            if not is_admin:
                self.output.print_warning("⚠️ Not running as administrator - some cleanup operations may fail")

            # Check for running Git processes
            progress.update(task, advance=20)
            killed = self.resolver.kill_git_processes()
            self.stats['processes_killed'] = killed

            # Check repository conflict
            progress.update(task, advance=20)
            repo_exists = self.resolver.check_repository_exists(
                self.config['username'],
                self.config['repo_name'],
                self.headers
            )

            if repo_exists:
                self.stats['conflicts_resolved'] += 1
                action, new_name = self.resolver.resolve_repository_conflict(
                    self.config['username'],
                    self.config['repo_name'],
                    self.headers
                )

                if new_name != self.config['repo_name']:
                    self.config['repo_name'] = new_name
                    self.repo_url = f"https://github.com/{self.config['username']}/{new_name}.git"
                    self.output.print_info(f"📝 Repository name updated to: {new_name}")

            progress.update(task, advance=20)
            self.output.print_success("Pre-flight checks completed")

    def _prepare_workspace(self):
        """Enhanced workspace preparation"""
        with self.output.create_progress_bar("🧹 Preparing workspace") as progress:
            task = progress.add_task("Cleaning workspace...", total=100)

            # Force remove existing directory
            progress.update(task, advance=30)
            if os.path.exists(self.config['work_dir']):
                success = self.resolver.force_remove_directory(self.config['work_dir'])
                if not success:
                    # Try alternative directory
                    timestamp = int(time.time())
                    self.config['work_dir'] = f"{self.config['work_dir']}_{timestamp}"
                    self.output.print_warning(f"Using alternative directory: {self.config['work_dir']}")

            # Create fresh directory
            progress.update(task, advance=40)
            os.makedirs(self.config['work_dir'], exist_ok=True)

            # Set proper permissions
            progress.update(task, advance=30)
            try:
                os.chmod(self.config['work_dir'], 0o777)
            except:
                pass

            self.output.print_success("Workspace prepared successfully")

    def _initialize(self):
        """Initialize with enhanced error handling"""
        with self.output.create_progress_bar("🔧 Initializing") as progress:
            task = progress.add_task("Setting up environment...", total=100)

            # Find Git
            progress.update(task, advance=30)
            self.git_path = self._find_git()
            self.output.print_success(f"Git found: {self.git_path}")

            # Validate paths
            progress.update(task, advance=30)
            if not os.path.exists(self.config['source_dir']):
                raise FileNotFoundError(f"Source directory not found: {self.config['source_dir']}")

            # Check available space
            progress.update(task, advance=40)
            self._check_disk_space()

            self.output.print_success("Environment initialized successfully")

    def _check_disk_space(self):
        """Check available disk space"""
        try:
            import shutil
            free_space = shutil.disk_usage(os.path.dirname(self.config['work_dir'])).free
            source_size = sum(f.stat().st_size for f in Path(self.config['source_dir']).rglob('*') if f.is_file())

            if free_space < source_size * 2:  # Need 2x space for safety
                self.output.print_warning(f"⚠️ Low disk space. Available: {self._format_size(free_space)}, Need: {self._format_size(source_size * 2)}")
        except:
            pass

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
                self.output.print_warning(f"Git found at {path} but failed: {e}")
                continue

        self.output.print_error("Git not found. Please install Git:")
        self.output.print_info("📥 Download from: https://git-scm.com/download/windows")
        raise Exception("Git not found")

    def _handle_repository(self):
        """Handle repository creation with proper validation"""
        with self.output.create_progress_bar("🏗️ Managing repository") as progress:
            task = progress.add_task("Creating repository...", total=100)

            # Create the repository on GitHub
            url = "https://api.github.com/user/repos"
            data = {
                "name": self.config['repo_name'],
                "description": f"🖥️ Server Dashboard IT - Aplicație React profesională pentru monitorizarea serverelor cu interfață modernă, grid 5×3, alerting sistem, și management complet al infrastructurii IT - Uploaded {time.strftime('%Y-%m-%d %H:%M')}",
                "private": False,
                "auto_init": False
            }

            progress.update(task, advance=30)

            try:
                response = requests.post(url, json=data, headers=self.headers)
                progress.update(task, advance=40)

                if response.status_code not in [200, 201]:
                    if response.status_code == 422:
                        error_data = response.json()
                        if "already exists" in str(error_data):
                            self.output.print_warning(f"Repository '{self.config['repo_name']}' already exists - will update it")
                        else:
                            raise Exception(f"Repository creation failed: {error_data.get('message', 'Unknown error')}")
                    else:
                        raise Exception(f"GitHub API error {response.status_code}: {response.text}")
                else:
                    self.output.print_success(f"Repository '{self.config['repo_name']}' created successfully")

                progress.update(task, advance=30)

                # Wait for GitHub to fully initialize the repository
                time.sleep(3)

                # Verify repository exists
                verify_url = f"https://api.github.com/repos/{self.config['username']}/{self.config['repo_name']}"
                verify_response = requests.get(verify_url, headers=self.headers)

                if verify_response.status_code != 200:
                    raise Exception(f"Repository verification failed - repository may not exist: {verify_response.text}")

                self.output.print_success(f"Repository verified and ready: {self.config['repo_name']}")

            except Exception as e:
                raise Exception(f"Repository management failed: {str(e)}")

        # Update the repository URL
        self.repo_url = f"https://github.com/{self.config['username']}/{self.config['repo_name']}.git"

    def _prepare_files_with_progress(self):
        """Prepare files with enhanced progress tracking for Dashboard"""
        # Count total files first
        total_files = 0
        try:
            total_files = sum(1 for _ in Path(self.config['source_dir']).rglob('*') if _.is_file())
        except:
            total_files = 100  # Fallback estimate

        with self.output.create_progress_bar("📁 Copying Dashboard files") as progress:
            task = progress.add_task("Copying files...", total=total_files)

            for root, dirs, files in os.walk(self.config['source_dir']):
                # Filter ignored directories (more specific for React/Node projects)
                dirs[:] = [d for d in dirs if not any(ignore in d for ignore in self.config['ignore_files'])]

                rel_path = os.path.relpath(root, self.config['source_dir'])
                dest_dir = os.path.join(self.config['work_dir'], rel_path)

                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
                    self.stats['directories_created'] += 1

                for file in files:
                    # More specific filtering for web projects
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
        """Initialize repository with enhanced error handling"""
        os.chdir(self.config['work_dir'])

        with self.output.create_progress_bar("🔄 Initializing Git") as progress:
            task = progress.add_task("Setting up Git...", total=100)

            try:
                # Initialize git
                subprocess.run([self.git_path, "init"], check=True, capture_output=True)
                progress.update(task, advance=20)

                subprocess.run([self.git_path, "branch", "-M", "main"], check=True, capture_output=True)
                progress.update(task, advance=20)

                # Create enhanced README and files
                progress.update(task, advance=20)
                self._create_enhanced_readme()

                progress.update(task, advance=20)
                self._create_comprehensive_gitignore()

                # Initial commit
                subprocess.run([self.git_path, "add", "."], check=True, capture_output=True)
                subprocess.run([self.git_path, "commit", "-m", "🚀 Initial commit - Server Dashboard IT Monitoring System"],
                             check=True, capture_output=True)
                progress.update(task, advance=20)

            except subprocess.CalledProcessError as e:
                raise Exception(f"Git initialization failed: {e.stderr.decode() if e.stderr else 'Unknown error'}")

        self.output.print_success("Git repository initialized successfully")

    def _push_to_github(self):
        """Push with enhanced error handling and repository verification"""
        os.chdir(self.config['work_dir'])

        with self.output.create_progress_bar("🚀 Uploading to GitHub") as progress:
            task = progress.add_task("Pushing to remote...", total=100)

            try:
                # Double-check repository exists before pushing
                verify_url = f"https://api.github.com/repos/{self.config['username']}/{self.config['repo_name']}"
                verify_response = requests.get(verify_url, headers=self.headers)

                if verify_response.status_code != 200:
                    self.output.print_error(f"❌ Repository doesn't exist on GitHub: {self.config['repo_name']}")
                    self.output.print_info("🔄 Attempting to create repository...")

                    # Try to create repository again
                    create_url = "https://api.github.com/user/repos"
                    create_data = {
                        "name": self.config['repo_name'],
                        "description": f"🖥️ Server Dashboard IT - Professional monitoring system - Uploaded {time.strftime('%Y-%m-%d %H:%M')}",
                        "private": False,
                        "auto_init": False
                    }

                    create_response = requests.post(create_url, json=create_data, headers=self.headers)
                    if create_response.status_code not in [200, 201]:
                        raise Exception(f"Failed to create repository: {create_response.text}")

                    self.output.print_success("✅ Repository created successfully")
                    time.sleep(3)  # Wait for GitHub

                progress.update(task, advance=20)

                # Construct authenticated repository URL
                auth_repo_url = f"https://{self.config['username']}:{self.config['token']}@github.com/{self.config['username']}/{self.config['repo_name']}.git"

                # Remove existing remote if exists
                subprocess.run([self.git_path, "remote", "remove", "origin"],
                             capture_output=True)  # Ignore errors

                # Add remote
                subprocess.run([self.git_path, "remote", "add", "origin", auth_repo_url],
                             check=True, capture_output=True)
                progress.update(task, advance=20)

                # Try normal push first
                self.output.print_info("📤 Attempting normal push...")
                push_result = subprocess.run([self.git_path, "push", "-u", "origin", "main"],
                                           capture_output=True)

                if push_result.returncode != 0:
                    # If normal push fails, try force push
                    self.output.print_warning("⚠️ Normal push failed, trying force push...")
                    push_result = subprocess.run([self.git_path, "push", "-f", "-u", "origin", "main"],
                                               check=True, capture_output=True)

                progress.update(task, advance=60)

                # Verify push was successful
                final_verify = requests.get(verify_url, headers=self.headers)
                if final_verify.status_code == 200:
                    repo_data = final_verify.json()
                    if repo_data.get('size', 0) > 0:
                        self.output.print_success("✅ Push verified - Server Dashboard is now on GitHub!")
                    else:
                        self.output.print_warning("⚠️ Push completed but repository appears empty")

            except subprocess.CalledProcessError as e:
                error_msg = e.stderr.decode('utf-8', errors='ignore') if e.stderr else 'Unknown Git error'

                # Provide specific error messages for common issues
                if "repository not found" in error_msg.lower():
                    raise Exception(f"Repository '{self.config['repo_name']}' not found on GitHub. Please check the name and permissions.")
                elif "authentication failed" in error_msg.lower():
                    raise Exception("GitHub authentication failed. Please check your token permissions.")
                elif "permission denied" in error_msg.lower():
                    raise Exception("Permission denied. Make sure your token has 'repo' permissions.")
                else:
                    raise Exception(f"Git push failed: {error_msg}")

            except Exception as e:
                raise Exception(f"Push operation failed: {str(e)}")

        self.output.print_success(f"🎉 Successfully uploaded Server Dashboard to {self.repo_url}")

        # Final verification message
        self.output.print_info(f"🔗 Access your repository at: https://github.com/{self.config['username']}/{self.config['repo_name']}")

    def _cleanup(self):
        """Enhanced cleanup with multiple attempts"""
        success = self.resolver.force_remove_directory(self.config['work_dir'])
        if success:
            self.output.print_success("Temporary files cleaned up")
        else:
            self.output.print_warning(f"⚠️ Could not fully clean: {self.config['work_dir']}")
            self.output.print_info("💡 You can manually delete this folder later")

    def _emergency_cleanup(self):
        """Emergency cleanup on failure"""
        try:
            self.resolver.force_remove_directory(self.config['work_dir'])
        except:
            pass

    def _create_enhanced_readme(self):
        """Create comprehensive README for Server Dashboard IT"""
        readme_content = f"""# 🖥️ Server Dashboard IT - Professional Monitoring System

[![React](https://img.shields.io/badge/React-18.3+-blue.svg)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-5.3+-green.svg)](https://vitejs.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.3+-cyan.svg)](https://tailwindcss.com/)
[![Node.js](https://img.shields.io/badge/Node.js-22.17+-orange.svg)](https://nodejs.org/)
[![GitHub](https://img.shields.io/badge/GitHub-{self.config['username']}-black.svg)](https://github.com/{self.config['username']})

> 🏆 **Aplicație profesională React pentru monitorizarea serverelor IT cu interfață modernă, sistem de alerting avansat și management complet al infrastructurii.**
>
> 📅 **Uploaded:** {time.strftime('%Y-%m-%d %H:%M:%S')}
>
> 🚀 **Auto-uploaded** with GitHub Dashboard Uploader Pro v3.0

## 🌟 Caracteristici Principale

### 🎛️ **Dashboard Modern**
- **Grid 5×3** pentru topologia rețelei cu vizualizare intuitivă
- **Status real-time** cu codificare color (🟢 Online, 🟡 Warning, 🔴 Offline)
- **Interfață responsivă** optimizată pentru toate device-urile
- **Animații fluide** și tranziții profesionale

### 📊 **Sistem Monitorizare Avansat**
- **8 Servere pre-configurate** (Web, Database, API, Cache, Load Balancer, Monitoring, Backup, Firewall)
- **Metrici în timp real**: CPU, RAM, Disk usage cu progress bars colorate
- **Uptime tracking** și monitorizare continuă
- **Actualizări automate** la fiecare 10 secunde

### 🚨 **Sistem Alerting Inteligent**
- **Alerting automat** pentru probleme critice
- **Threshold-uri configurabile** (CPU >90%, RAM >85%, Disk >90%)
- **Istoric alerte** cu timestamp și categorii
- **Notificări vizuale** și sonore

### 🔧 **Management Servere**
- **Restart servere** cu animație loading
- **View Full Logs** cu modal dedicat
- **Server details modal** cu informații complete
- **Network topology** cu click-to-detail

### ⚡ **Tehnologii Moderne**
- **React 18** cu Hooks și functional components
- **Vite** pentru build ultra-rapid
- **Tailwind CSS** pentru styling modern
- **Lucide React** pentru iconițe vectoriale
- **Loading sistem** în 2 etape (HTML + React)

## 🚀 Setup Rapid

### 📋 **Cerințe Sistem**
```bash
Node.js 22.17+ (inclus în proiect: node-v22.17.1-win-x64)
npm 10.9+
Python 3.8+ (pentru scripturi setup)
```

### ⚡ **Instalare în 3 Pași**

1️⃣ **Clonează repository-ul**
```bash
git clone {self.repo_url}
cd {self.config['repo_name']}
```

2️⃣ **Setup automat cu script**
```bash
python setup-dashboard.py
```

3️⃣ **Sau pornește direct**
```bash
python START.py
```

### 🔧 **Setup Manual (Alternativ)**
```bash
cd react-app
npm install
npm run dev
```

## 📁 Structura Proiect

```
{self.config['repo_name']}/
├── react-app/                    # Aplicația React principală
│   ├── src/
│   │   ├── App.jsx              # Dashboard principal cu toate funcționalitățile
│   │   ├── main.jsx             # Entry point React
│   │   └── index.css            # Tailwind CSS setup
│   ├── package.json             # Dependențe React
│   ├── vite.config.js           # Configurare Vite
│   ├── tailwind.config.js       # Configurare Tailwind
│   └── index.html               # HTML cu loader sistem
├── INSTALAT node-v22.17.1-win-x64/  # Node.js portable
├── setup-dashboard.py           # Script setup automat
├── START.py                     # Script pornire aplicație
├── update-app.py               # Script actualizare funcționalități
├── fix-templates.py            # Script reparare template literals
├── Instructiuni.txt            # Ghid utilizare
└── README.md                   # Documentație completă
```

## 🎯 Funcționalități Detaliate

### 🖥️ **Server Grid (5×3)**
- **15 sloturi** pentru servere cu organizare logică
- **8 servere active** pre-configurate cu date realiste
- **Click pe server** → Modal detalii complete
- **Hover effects** și animații scale

### 📈 **Sistem Metrici**
- **CPU Usage** cu threshold-uri colorate
- **Memory Usage** cu progress bars animate
- **Disk Usage** cu alerting automat
- **Network Status** cu ping simulation

### 🔄 **Auto-refresh & Real-time**
- **Simulare date live** cu variații realiste
- **Refresh manual** cu buton și loading state
- **Websocket ready** pentru implementare production
- **Performance optimizat** pentru fluiditate

### 🎨 **Design System**
- **Dark theme** professional cu accent colors
- **Gradient backgrounds** și glassmorphism effects
- **Micro-animations** pentru feedback utilizator
- **Responsive design** pentru toate screen sizes

## 🚀 Development Workflow

### 📦 **Scripts Disponibile**
```bash
# Setup complet automat
python setup-dashboard.py

# Pornire rapidă
python START.py

# Update funcționalități noi
python update-app.py

# Reparare template issues
python fix-templates.py

# Development server
cd react-app && npm run dev

# Build pentru production
cd react-app && npm run build
```

### 🔧 **Configurare Development**
- **Hot reload** activat pentru development rapid
- **Source maps** pentru debugging
- **Error boundaries** pentru handling errors
- **Performance monitoring** integrat

## 📊 Upload Statistics

- 📁 **Files:** {self.stats['files_copied']}
- 📂 **Directories:** {self.stats['directories_created']}
- 💾 **Size:** {self._format_size(self.stats['total_size'])}
- 🛠️ **Conflicts Resolved:** {self.stats['conflicts_resolved']}
- 🔄 **Processes Killed:** {self.stats['processes_killed']}

## 🎯 Roadmap Viitor

### v2.0 Features
- [ ] **WebSocket integration** pentru date real-time
- [ ] **User authentication** și role management
- [ ] **Historical data** cu charts și trends
- [ ] **Email notifications** pentru alerte critice
- [ ] **Custom dashboards** configurabile

### v3.0 Enterprise
- [ ] **Multi-tenant** support
- [ ] **API REST** pentru integrări externe
- [ ] **Docker deployment** cu orchestration
- [ ] **Mobile app** companion
- [ ] **AI-powered** predictive maintenance

## 🤝 Contributing

Contribuțiile sunt binevenite! Pentru bug reports, feature requests sau pull requests:

1. **Fork** repository-ul
2. **Create feature branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit changes** (`git commit -m 'Add AmazingFeature'`)
4. **Push to branch** (`git push origin feature/AmazingFeature`)
5. **Open Pull Request**

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.

## 📞 Contact & Support

- **GitHub Issues**: Pentru bug reports și feature requests
- **Documentation**: Vezi `Instructiuni.txt` pentru ghid detaliat
- **Development**: Script-uri Python pentru automatizare completă

---

<div align="center">

**🖥️ Dezvoltat cu pasiune pentru infrastructura IT și tehnologiile moderne! 🖥️**

🤖 **Auto-uploaded** with [GitHub Dashboard Uploader Pro](https://github.com/{self.config['username']})

⭐ **Dacă îți place proiectul, oferă o stea!** ⭐

🚀 **Ready for production deployment!** 🚀

</div>
"""

        with open("README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)

    def _create_comprehensive_gitignore(self):
        """Create comprehensive .gitignore for React/Node project"""
        gitignore_content = """# 🖥️ Server Dashboard IT - GitIgnore

# 📦 Dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
lerna-debug.log*

# 🔨 Build outputs
dist/
dist-ssr/
build/
.vite/
*.local

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
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg

# 🔒 Environment & Config
.env
.env.local
.env.development.local
.env.test.local
.env.production.local
.venv
env/
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
*.sublime-session

# 🔍 Testing
coverage/
*.lcov
.nyc_output

# 📊 Logs
logs/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
lerna-debug.log*

# 💾 Temporary files
*.tmp
*.temp
*.bak
*.swp
*.swo
*~

# 🔄 Runtime data
pids/
*.pid
*.seed
*.pid.lock

# 📁 Directory for instrumented libs generated by jscoverage/JSCover
lib-cov/

# 🔍 Coverage directory used by tools like istanbul
coverage/
*.lcov

# 📊 nyc test coverage
.nyc_output/

# 🎯 Dependency directories
jspm_packages/

# 🔧 TypeScript cache
*.tsbuildinfo

# 📦 Optional npm cache directory
.npm

# 📝 Optional eslint cache
.eslintcache

# 📊 Microbundle cache
.rpt2_cache/
.rts2_cache_cjs/
.rts2_cache_es/
.rts2_cache_umd/

# 🔍 Optional REPL history
.node_repl_history

# 📤 Output of 'npm pack'
*.tgz

# 📦 Yarn Integrity file
.yarn-integrity

# 🔧 parcel-bundler cache (https://parceljs.org/)
.cache
.parcel-cache

# 🎯 Next.js build output
.next

# 📊 Nuxt.js build / generate output
.nuxt
dist

# 🔍 Gatsby files
.cache/
public

# 📱 Storybook build outputs
.out
.storybook-out

# 🔧 Temporary folders
tmp/
temp/

# 🎯 Project specific
backup/
cache/
uploads/

# 🔄 Server Dashboard specific
*.xlsx
*.xls
*.csv
server-logs/
monitoring-data/
"""
        with open(".gitignore", "w", encoding="utf-8") as f:
            f.write(gitignore_content)

    def _print_success_summary(self):
        """Enhanced success summary for Dashboard"""
        elapsed_time = time.time() - self.stats['start_time']

        if RICH_AVAILABLE:
            stats_data = [
                ("📁 Files Uploaded", self.stats['files_copied'], "React app + Python scripts"),
                ("📂 Directories Created", self.stats['directories_created'], "Project structure"),
                ("💾 Total Size", self._format_size(self.stats['total_size']), "Dashboard data transferred"),
                ("🛠️ Conflicts Resolved", self.stats['conflicts_resolved'], "Repository conflicts"),
                ("🔄 Processes Killed", self.stats['processes_killed'], "Git cleanup operations"),
                ("⏱️ Time Elapsed", f"{elapsed_time:.1f}s", "Upload duration"),
                ("🔗 Repository URL", self.repo_url, "Access your dashboard")
            ]

            table = self._create_stats_table(stats_data)
            self.output.console.print(table)

            success_text = f"""
🎉 SERVER DASHBOARD IT SUCCESSFULLY UPLOADED! 🎉

✅ Your professional monitoring system is now live on GitHub!
🔗 Access it at: {self.repo_url}

🚀 Quick Start Commands:
  git clone {self.repo_url}
  cd {self.config['repo_name']}
  python START.py

⚡ What's included:
  • 🖥️ React Dashboard with 5×3 server grid
  • 📊 Real-time monitoring with 8 pre-configured servers
  • 🚨 Advanced alerting system
  • 🔧 Server management tools (restart, logs, details)
  • ⚡ Modern loading system and animations
  • 🎨 Professional dark theme with Tailwind CSS
  • 📱 Fully responsive design
  • 🔄 Auto-refresh and real-time updates

💡 Next steps:
  • 👀 Clone and test the dashboard locally
  • 📝 Customize server configurations
  • 🌟 Star the repository
  • 🔄 Set up CI/CD pipeline
  • 📊 Monitor your real infrastructure

🛠️ Professional upload with advanced features:
  • 🔍 Pre-flight conflict detection and resolution
  • 🧹 Multi-method force cleanup system
  • 🔄 Git process management and optimization
  • 📝 Intelligent repository name handling
  • 📊 Comprehensive upload statistics
            """

            success_panel = Panel(
                Align.center(Text(success_text, style="bold green")),
                border_style="bright_green",
                title="[bold yellow]🏆 SERVER DASHBOARD UPLOAD SUCCESS! 🏆[/bold yellow]",
                subtitle="[italic]Professional IT Monitoring System Ready for Production[/italic]"
            )

            self.output.console.print(success_panel)
        else:
            self.output.print_success("SERVER DASHBOARD IT UPLOAD COMPLETED SUCCESSFULLY!")
            print(f"\n📊 Upload Statistics:")
            print(f"   📁 Files: {self.stats['files_copied']}")
            print(f"   💾 Size: {self._format_size(self.stats['total_size'])}")
            print(f"   🛠️ Conflicts: {self.stats['conflicts_resolved']}")
            print(f"   ⏱️ Time: {elapsed_time:.1f}s")
            print(f"\n🔗 Repository: {self.repo_url}")
            print(f"\n🚀 Quick start: git clone {self.repo_url}")

    def _create_stats_table(self, stats_data):
        """Create beautiful stats table"""
        if RICH_AVAILABLE:
            table = Table(title="📊 Server Dashboard Upload Statistics", show_header=True, header_style="bold magenta")
            table.add_column("📈 Metric", style="cyan", no_wrap=True)
            table.add_column("📋 Value", style="green")
            table.add_column("📝 Description", style="yellow")

            for metric, value, description in stats_data:
                table.add_row(metric, str(value), description)

            return table
        return None

    def _print_troubleshooting_guide(self):
        """Print comprehensive troubleshooting guide for Dashboard"""
        if RICH_AVAILABLE:
            guide = """
🔧 SERVER DASHBOARD TROUBLESHOOTING GUIDE

Common issues and solutions for dashboard upload:

1️⃣ **Configuration Issues**
   • Edit script and replace 'TU-USERUL-TAU-GITHUB' with your username
   • Replace 'TU-TOKEN-UL-TAU-GITHUB' with your GitHub token
   • Ensure token has 'repo' permissions

2️⃣ **Repository Not Found Error**
   • Check repository name (avoid: update, delete, new, etc.)
   • Try suggested names: Server-Dashboard-IT-Pro, IT-Dashboard-Monitoring
   • Verify GitHub token permissions

3️⃣ **Source Directory Issues**
   • Verify d:\\Server-Dashboard-IT\\ exists
   • Check folder contains react-app/ directory
   • Ensure all files are accessible

4️⃣ **Node.js / React Issues**
   • Verify Node.js is in d:\\INSTALAT node-v22.17.1-win-x64\\
   • Check react-app/package.json exists
   • Ensure npm dependencies are available

5️⃣ **Permission Issues**
   • Run as Administrator (Right-click → Run as administrator)
   • Close VS Code, GitHub Desktop, or any Git tools
   • Kill Node.js processes if running

6️⃣ **Git Repository Issues**
   • Delete existing .git folder in source if exists
   • Clear git cache: git config --global credential.helper ""
   • Try different work directory

7️⃣ **GitHub Token Setup**
   Settings → Developer Settings → Personal Access Tokens
   Generate new token → Select 'repo' scope

8️⃣ **Manual Cleanup**
   Delete: D:\\temp_github_upload_dashboard
   Clear: C:\\Users\\[user]\\AppData\\Local\\npm-cache

💡 If upload fails but repository exists:
   Choose "update" option to push to existing repo

🔗 Complete Dashboard Setup:
   1. Upload successful → git clone [repo-url]
   2. cd [repo-folder] → python START.py
   3. Dashboard opens at http://localhost:5173

🎯 Dashboard Features to Test:
   • React app loads with loading screen
   • 5×3 server grid displays correctly
   • Click servers → modal opens with details
   • Restart server → animation works
   • View Full Logs → extended modal
   • Auto-refresh every 10 seconds
            """

            panel = Panel(
                Text(guide, style="yellow"),
                border_style="red",
                title="[bold red]🛠️ DASHBOARD TROUBLESHOOTING GUIDE[/bold red]"
            )
            self.output.console.print(panel)
        else:
            print("\n🔧 SERVER DASHBOARD TROUBLESHOOTING GUIDE:")
            print("1. Configuration - Replace username and token in script")
            print("2. Repository Not Found - Check name and token permissions")
            print("3. Source Directory - Verify d:\\Server-Dashboard-IT\\ exists")
            print("4. Run as Administrator")
            print("5. Close all Git applications and Node.js processes")
            print("6. Check GitHub token has 'repo' permissions")
            print("7. Delete temp directory manually if needed")
            print("8. Try different repository name if conflicts")
            print("9. For existing repos, choose 'update' option")

    def _format_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"

def main():
    """Main entry point with enhanced dashboard-specific setup"""

    print("🖥️ SERVER DASHBOARD IT - GITHUB UPLOADER PRO v3.0 🖥️")
    print("=" * 70)

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
        print("⚠️  For full functionality, install required libraries:")
        print(f"   pip install {' '.join(missing_libs)}")
        print("   🎨 This adds beautiful output and process management!")
        print("\n🚀 Continuing with basic functionality...\n")

    # Run the uploader
    try:
        uploader = GitHubDashboardUploader()
        uploader.run()
    except KeyboardInterrupt:
        print("\n🛑 Dashboard upload cancelled by user")
        sys.exit(0)

if __name__ == "__main__":
    main()