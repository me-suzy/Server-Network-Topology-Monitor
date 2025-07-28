import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import threading
import time
import random
import os
import math

class ServerDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("🖥️ Dashboard IT Professional - Server Monitoring System")
        self.root.geometry("1400x900")
        self.root.configure(bg='#2c3e50')

        # Configurare stil modern
        self.setup_styles()

        # Fișier Excel pentru baza de date
        self.excel_file = "server_database.xlsx"
        self.max_servers_per_tab = 6

        # Încărcare date
        self.initialize_database()
        self.load_data()

        # Setare variabile
        self.server_icons = {}
        self.alerts = []
        self.current_selected = None
        self.current_tab = 0
        self.tabs = []
        self.context_menu = None
        self.performance_metrics = {}

        # Inițializare metrici pentru a evita erori
        self.calculate_performance_metrics()

        # Creare interfață
        self.create_main_layout()

        # Start monitorizare în background
        self.monitor_thread = threading.Thread(target=self.monitor_servers, daemon=True)
        self.monitor_thread.start()

        print("🚀 Dashboard IT Professional inițializat cu succes")

    def setup_styles(self):
        """Configurează stilurile moderne pentru interfață"""
        try:
            style = ttk.Style()
            style.theme_use('clam')

            # Configurări de culori moderne
            style.configure('Title.TLabel',
                           font=('Segoe UI', 16, 'bold'),
                           foreground='#ecf0f1',
                           background='#2c3e50')

            style.configure('Header.TLabel',
                           font=('Segoe UI', 12, 'bold'),
                           foreground='#3498db',
                           background='#34495e')

            style.configure('Info.TLabel',
                           font=('Segoe UI', 10),
                           foreground='#ecf0f1',
                           background='#34495e')

            style.configure('Modern.TFrame',
                           background='#34495e',
                           borderwidth=1,
                           relief='solid')

            style.configure('Card.TFrame',
                           background='#34495e',
                           borderwidth=2,
                           relief='raised')

            # Configurare scrollbar mai gros
            style.configure('Custom.Vertical.TScrollbar',
                           gripcount=0,
                           background='#34495e',
                           darkcolor='#2c3e50',
                           lightcolor='#5a6c7d',
                           troughcolor='#2c3e50',
                           borderwidth=2,
                           arrowcolor='#ecf0f1',
                           width=20)  # Mai gros

        except Exception as e:
            print(f"⚠️ Warning: Nu s-au putut configura stilurile: {e}")

    def initialize_database(self):
        """Creează sau actualizează fișierul Excel cu structura completă"""
        if not os.path.exists(self.excel_file):
            print(f"📁 Creez fișierul {self.excel_file} cu structură avansată...")
            self.create_new_excel()
        else:
            print(f"🔄 Verific și actualizez structura Excel-ului existent...")
            self.update_existing_excel()

    def create_new_excel(self):
        """Creează un fișier Excel nou cu structura completă"""
        default_data = {
            'ID': ['SRV-001', 'SRV-002', 'SRV-003', 'SRV-004', 'SRV-005'],
            'Nume': ['Web Server', 'Database Server', 'File Server', 'Mail Server', 'Backup Server'],
            'IP': ['192.168.1.10', '192.168.1.20', '192.168.1.30', '192.168.1.40', '192.168.1.50'],
            'Locatie': ['Rack A1', 'Rack A2', 'Rack B1', 'Rack B2', 'Rack C1'],
            'Status': ['up', 'up', 'down', 'up', 'up'],
            'CPU_Usage': [45.2, 78.5, 0, 23.1, 12.8],
            'RAM_Usage': [62.3, 85.7, 0, 34.5, 28.9],
            'Disk_Usage': [78.9, 45.2, 95.1, 67.3, 23.4],
            'Network_In': [1024, 2048, 0, 512, 256],
            'Network_Out': [2048, 1024, 0, 768, 128],
            'Uptime_Hours': [720, 1440, 0, 168, 2160],
            'Performance_Score': [85, 72, 0, 92, 98],
            'UltimaVerificare': [datetime.now() - timedelta(minutes=random.randint(1, 30)) for _ in range(5)],
            'Loguri': [
                "System boot successful\nCPU temperature: 65°C\nRAM usage normal\nAll services running",
                "Database connections: 24\nQuery cache: 12MB\nBackup completed\nIndex optimization done",
                "Connection timeout\nLast backup failed\nDisk space critical\nService stopped",
                "Mail queue: 0 messages\nSpam blocked: 3 attempts\nSSL certificate valid\nRelay working",
                "Backup job completed\nData integrity check passed\nArchive compression: 85%\nRetention policy applied"
            ]
        }
        df = pd.DataFrame(default_data)
        df.to_excel(self.excel_file, index=False)
        print(f"✅ Fișierul {self.excel_file} creat cu structură completă")

    def update_existing_excel(self):
        """Actualizează Excel-ul existent cu coloanele noi"""
        try:
            # Încarcă Excel-ul existent
            existing_df = pd.read_excel(self.excel_file)
            print(f"📊 Excel existent încărcat cu {len(existing_df)} servere")

            # Lista coloanelor necesare cu valorile default
            required_columns = {
                'ID': 'SRV-000',
                'Nume': 'Unknown Server',
                'IP': '0.0.0.0',
                'Locatie': 'Unknown',
                'Status': 'down',
                'CPU_Usage': 0.0,
                'RAM_Usage': 0.0,
                'Disk_Usage': 0.0,
                'Network_In': 0,
                'Network_Out': 0,
                'Uptime_Hours': 0.0,
                'Performance_Score': 0.0,
                'UltimaVerificare': datetime.now(),
                'Loguri': 'No logs available'
            }

            # Verifică și adaugă coloanele lipsă
            columns_added = []
            for col, default_value in required_columns.items():
                if col not in existing_df.columns:
                    if col == 'UltimaVerificare':
                        existing_df[col] = [datetime.now()] * len(existing_df)
                    elif col in ['CPU_Usage', 'RAM_Usage', 'Disk_Usage', 'Uptime_Hours', 'Performance_Score']:
                        # Pentru servere existente, generează valori realiste
                        if col == 'CPU_Usage':
                            existing_df[col] = [random.uniform(10, 80) if status == 'up' else 0
                                              for status in existing_df.get('Status', ['down'] * len(existing_df))]
                        elif col == 'RAM_Usage':
                            existing_df[col] = [random.uniform(20, 70) if status == 'up' else 0
                                              for status in existing_df.get('Status', ['down'] * len(existing_df))]
                        elif col == 'Disk_Usage':
                            existing_df[col] = [random.uniform(30, 90) if status == 'up' else 0
                                              for status in existing_df.get('Status', ['down'] * len(existing_df))]
                        elif col == 'Uptime_Hours':
                            existing_df[col] = [random.uniform(1, 2000) if status == 'up' else 0
                                              for status in existing_df.get('Status', ['down'] * len(existing_df))]
                        elif col == 'Performance_Score':
                            existing_df[col] = [random.uniform(60, 95) if status == 'up' else 0
                                              for status in existing_df.get('Status', ['down'] * len(existing_df))]
                    elif col in ['Network_In', 'Network_Out']:
                        existing_df[col] = [random.randint(100, 2000) if status == 'up' else 0
                                          for status in existing_df.get('Status', ['down'] * len(existing_df))]
                    else:
                        existing_df[col] = [default_value] * len(existing_df)

                    columns_added.append(col)
                    print(f"  ➕ Adăugat coloana: {col}")

            if columns_added:
                # Salvează Excel-ul actualizat
                existing_df.to_excel(self.excel_file, index=False)
                print(f"✅ Excel actualizat cu {len(columns_added)} coloane noi")
            else:
                print("✅ Excel-ul are deja structura completă")

        except Exception as e:
            print(f"❌ Eroare la actualizarea Excel-ului: {e}")
            print("🔄 Creez structură nouă...")
            self.create_new_excel()

    def load_data(self):
        """Încarcă datele din fișierul Excel cu gestionarea erorilor"""
        try:
            print(f"📊 Încărcare date din {self.excel_file}...")
            self.servers = pd.read_excel(self.excel_file)

            # Conversie datetime pentru coloana UltimaVerificare
            if 'UltimaVerificare' in self.servers.columns:
                self.servers['UltimaVerificare'] = pd.to_datetime(self.servers['UltimaVerificare'])

            print(f"✅ Date încărcate cu succes - {len(self.servers)} servere")

            # Verifică dacă toate coloanele necesare există
            required_cols = ['CPU_Usage', 'RAM_Usage', 'Disk_Usage', 'Performance_Score']
            missing_cols = [col for col in required_cols if col not in self.servers.columns]

            if missing_cols:
                print(f"⚠️ Coloane lipsă detectate: {missing_cols}")
                print("🔄 Re-inițializez baza de date...")
                self.update_existing_excel()
                # Reîncarcă după actualizare
                self.servers = pd.read_excel(self.excel_file)
                self.servers['UltimaVerificare'] = pd.to_datetime(self.servers['UltimaVerificare'])
                print("✅ Date reîncărcate cu structura completă")

        except Exception as e:
            print(f"❌ Eroare critică la încărcarea datelor: {str(e)}")
            print("🔄 Creez bază de date nouă...")
            self.create_new_excel()
            try:
                self.servers = pd.read_excel(self.excel_file)
                self.servers['UltimaVerificare'] = pd.to_datetime(self.servers['UltimaVerificare'])
                print("✅ Bază de date nouă creată și încărcată")
            except Exception as e2:
                print(f"❌ Eroare fatală: {str(e2)}")
                messagebox.showerror("Eroare Fatală",
                                   f"Nu s-a putut crea baza de date:\n{str(e2)}\n\nAplicația se va închide.")
                exit(1)

    def save_data(self, silent=False):
        """Salvează datele în fișierul Excel cu auto-backup și gestionare erori"""
        try:
            # Verifică dacă fișierul este în uz (deschis în Excel)
            def is_file_in_use(filepath):
                try:
                    # Încearcă să deschidă fișierul pentru scriere
                    with open(filepath, 'r+b'):
                        pass
                    return False
                except (IOError, OSError):
                    return True

            # Verifică dacă Excel-ul este deschis
            if os.path.exists(self.excel_file) and is_file_in_use(self.excel_file):
                if not silent:
                    # Afișează mesaj informativ doar pentru salvări manuale
                    messagebox.showwarning("Fișier în uz",
                        f"Fișierul {self.excel_file} este deschis în Excel.\n\n"
                        f"✅ Datele sunt păstrate în memorie.\n"
                        f"💡 Închideți Excel pentru a salva pe disk.\n\n"
                        f"Aplicația va încerca din nou automat.")

                print(f"⚠️ Fișier în uz: {self.excel_file} - salvare amânată")
                return False  # Returnează False pentru a indica eșecul salvării

            # Backup precedent
            if os.path.exists(self.excel_file):
                backup_file = f"{self.excel_file}.backup"
                import shutil
                shutil.copy2(self.excel_file, backup_file)

            # Salvare principală
            self.servers.to_excel(self.excel_file, index=False)

            if not silent:
                print("💾 Date salvate cu succes în Excel")

            # Recalculare metrici
            self.calculate_performance_metrics()
            return True  # Returnează True pentru succes

        except PermissionError as e:
            if not silent:
                print(f"⚠️ Fișier blocat - salvare amânată: {str(e)}")
            else:
                print(f"⚠️ [Silent] Fișier blocat: {str(e)}")
            return False

        except Exception as e:
            if not silent:
                messagebox.showerror("Eroare", f"Eroare la salvarea datelor: {str(e)}")
                print(f"❌ Eroare la salvarea datelor: {str(e)}")
            else:
                print(f"❌ [Silent] Eroare la salvarea datelor: {str(e)}")
            return False

    def calculate_performance_metrics(self):
        """Calculează metrici avansate de performanță cu verificări de siguranță"""
        try:
            if self.servers is None or len(self.servers) == 0:
                # Metrici default dacă nu există servere
                self.performance_metrics = {
                    'total_servers': 0,
                    'online_servers': 0,
                    'offline_servers': 0,
                    'avg_cpu': 0,
                    'avg_ram': 0,
                    'avg_performance': 0,
                    'critical_servers': 0,
                    'total_uptime': 0
                }
                return

            # Verifică dacă coloanele necesare există
            required_columns = ['Status', 'CPU_Usage', 'RAM_Usage', 'Disk_Usage', 'Performance_Score', 'Uptime_Hours']
            for col in required_columns:
                if col not in self.servers.columns:
                    print(f"⚠️ Coloana {col} lipsește, folosesc valori default")
                    if col == 'Status':
                        self.servers[col] = 'down'
                    elif col in ['CPU_Usage', 'RAM_Usage', 'Disk_Usage', 'Performance_Score', 'Uptime_Hours']:
                        self.servers[col] = 0.0

            # Filtrează servere online/offline
            online_servers = self.servers[self.servers['Status'] == 'up']
            offline_servers = self.servers[self.servers['Status'] == 'down']

            # Calculare metrici
            self.performance_metrics = {
                'total_servers': len(self.servers),
                'online_servers': len(online_servers),
                'offline_servers': len(offline_servers),
                'avg_cpu': online_servers['CPU_Usage'].mean() if len(online_servers) > 0 else 0,
                'avg_ram': online_servers['RAM_Usage'].mean() if len(online_servers) > 0 else 0,
                'avg_performance': online_servers['Performance_Score'].mean() if len(online_servers) > 0 else 0,
                'critical_servers': len(self.servers[
                    (self.servers['CPU_Usage'] > 90) |
                    (self.servers['RAM_Usage'] > 90) |
                    (self.servers['Disk_Usage'] > 90)
                ]),
                'total_uptime': online_servers['Uptime_Hours'].sum() if len(online_servers) > 0 else 0
            }

            # Înlocuiește NaN cu 0
            for key, value in self.performance_metrics.items():
                if pd.isna(value):
                    self.performance_metrics[key] = 0

            print(f"📊 Metrici calculate: {self.performance_metrics['online_servers']}/{self.performance_metrics['total_servers']} servere online")

        except Exception as e:
            print(f"❌ Eroare la calcularea metricilor: {str(e)}")
            # Metrici default în caz de eroare
            self.performance_metrics = {
                'total_servers': 0,
                'online_servers': 0,
                'offline_servers': 0,
                'avg_cpu': 0,
                'avg_ram': 0,
                'avg_performance': 0,
                'critical_servers': 0,
                'total_uptime': 0
            }

    def create_main_layout(self):
        """Creează layout-ul principal cu orientare verticală"""
        # Frame principal
        main_container = tk.Frame(self.root, bg='#2c3e50')
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Header cu statistici
        self.create_header_panel(main_container)

        # Container pentru panouri principale
        content_frame = tk.Frame(main_container, bg='#2c3e50')
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        # Panou STÂNG - Schema serverelor (VERTICAL)
        left_frame = tk.Frame(content_frame, bg='#34495e', width=800)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        left_frame.pack_propagate(False)

        # Panou DREAPTA - Detalii și controale (VERTICAL)
        right_frame = tk.Frame(content_frame, bg='#34495e', width=400)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        right_frame.pack_propagate(False)

        # Creare conținut panouri
        self.create_topology_panel(left_frame)
        self.create_details_panel(right_frame)

        # Meniu contextual
        self.create_context_menu()

    def create_header_panel(self, parent):
        """Creează panoul header cu statistici"""
        header_frame = tk.Frame(parent, bg='#2c3e50', height=120)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.pack_propagate(False)

        # Titlu principal
        title_label = tk.Label(header_frame,
                              text="🖥️ Dashboard IT Professional",
                              font=('Segoe UI', 15, 'bold'),
                              fg='#ecf0f1', bg='#2c3e50')
        title_label.pack(pady=(10, 5))

        # Container pentru carduri statistici
        stats_frame = tk.Frame(header_frame, bg='#2c3e50')
        stats_frame.pack(fill=tk.X, pady=(5, 10))

        # Variabile pentru statistici
        self.stat_vars = {
            'total': tk.StringVar(value="0"),
            'online': tk.StringVar(value="0"),
            'offline': tk.StringVar(value="0"),
            'cpu_avg': tk.StringVar(value="0%"),
            'performance': tk.StringVar(value="0%"),
            'critical': tk.StringVar(value="0")
        }

        # Carduri statistici
        stats_data = [
            ("📊 Total Servere", self.stat_vars['total'], "#3498db"),
            ("✅ Online", self.stat_vars['online'], "#27ae60"),
            ("❌ Offline", self.stat_vars['offline'], "#e74c3c"),
            ("🔥 CPU Avg", self.stat_vars['cpu_avg'], "#f39c12"),
            ("⚡ Performance", self.stat_vars['performance'], "#9b59b6"),
            ("⚠️ Critical", self.stat_vars['critical'], "#e67e22")
        ]

        for i, (label, var, color) in enumerate(stats_data):
            card = tk.Frame(stats_frame, bg=color, relief='raised', bd=2)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)

            tk.Label(card, text=label, font=('Segoe UI', 9, 'bold'),
                    fg='white', bg=color).pack(pady=(5, 2))
            tk.Label(card, textvariable=var, font=('Segoe UI', 12, 'bold'),
                    fg='white', bg=color).pack(pady=(2, 5))

        # Update statistici
        self.update_header_stats()

    def update_header_stats(self):
        """Actualizează statisticile din header cu verificări de siguranță"""
        try:
            if hasattr(self, 'performance_metrics') and self.performance_metrics:
                self.stat_vars['total'].set(str(self.performance_metrics.get('total_servers', 0)))
                self.stat_vars['online'].set(str(self.performance_metrics.get('online_servers', 0)))
                self.stat_vars['offline'].set(str(self.performance_metrics.get('offline_servers', 0)))

                avg_cpu = self.performance_metrics.get('avg_cpu', 0)
                self.stat_vars['cpu_avg'].set(f"{avg_cpu:.1f}%" if not pd.isna(avg_cpu) else "0%")

                avg_perf = self.performance_metrics.get('avg_performance', 0)
                self.stat_vars['performance'].set(f"{avg_perf:.0f}%" if not pd.isna(avg_perf) else "0%")

                self.stat_vars['critical'].set(str(self.performance_metrics.get('critical_servers', 0)))
            else:
                # Valori default
                for var in self.stat_vars.values():
                    if var == self.stat_vars['cpu_avg'] or var == self.stat_vars['performance']:
                        var.set("0%")
                    else:
                        var.set("0")
        except Exception as e:
            print(f"❌ Eroare la actualizarea statisticilor: {e}")
            # Setează valori default în caz de eroare
            for var in self.stat_vars.values():
                if var == self.stat_vars['cpu_avg'] or var == self.stat_vars['performance']:
                    var.set("0%")
                else:
                    var.set("0")

    def create_topology_panel(self, parent):
        """Creează panoul pentru topologia serverelor"""
        # Header panou topologie
        topo_header = tk.Frame(parent, bg='#34495e', height=50)
        topo_header.pack(fill=tk.X, padx=10, pady=(10, 5))
        topo_header.pack_propagate(False)

        tk.Label(topo_header, text="🌐 Topologie Rețea",
                font=('Segoe UI', 14, 'bold'), fg='#ecf0f1', bg='#34495e').pack(side=tk.LEFT, pady=15)

        # Butoane control
        btn_frame = tk.Frame(topo_header, bg='#34495e')
        btn_frame.pack(side=tk.RIGHT, pady=10)

        tk.Button(btn_frame, text="➕ Adaugă Server", command=self.add_server,
                 font=('Segoe UI', 9), bg='#27ae60', fg='white',
                 relief='flat', padx=10).pack(side=tk.LEFT, padx=2)

        tk.Button(btn_frame, text="🔄 Refresh", command=self.refresh_topology,
                 font=('Segoe UI', 9), bg='#3498db', fg='white',
                 relief='flat', padx=10).pack(side=tk.LEFT, padx=2)

        # Notebook pentru tab-uri
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Creare tab-uri inițiale
        self.create_tabs()

        # Bind pentru schimbarea tab-ului
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def create_tabs(self):
        """Creează tab-urile cu maxim 6 servere fiecare - Layout VERTICAL (2x3)"""
        # Șterge tab-urile existente
        for tab in self.tabs:
            self.notebook.forget(tab['frame'])
        self.tabs = []

        # Calculează numărul de tab-uri necesare
        num_servers = len(self.servers)
        num_tabs = max(1, (num_servers + self.max_servers_per_tab - 1) // self.max_servers_per_tab)

        print(f"📋 Creez {num_tabs} tab-uri pentru {num_servers} servere")

        # Creează tab-urile
        for tab_idx in range(num_tabs):
            tab_frame = tk.Frame(self.notebook, bg='#34495e')
            tab_name = f"Rețea {tab_idx + 1}"
            self.notebook.add(tab_frame, text=tab_name)

            # Determină serverele pentru acest tab
            start_idx = tab_idx * self.max_servers_per_tab
            end_idx = min(start_idx + self.max_servers_per_tab, num_servers)
            tab_servers = self.servers.iloc[start_idx:end_idx]

            print(f"  📊 Tab {tab_idx + 1}: servere {start_idx}-{end_idx-1}")

            # Salvare informații tab
            self.tabs.append({
                'frame': tab_frame,
                'servers': tab_servers,
                'canvas': None
            })

            # Creează canvas pentru topologie
            self.create_tab_canvas(tab_idx)

        # Selectează primul tab
        if self.tabs:
            self.notebook.select(0)
            self.current_tab = 0

    def create_tab_canvas(self, tab_idx):
        """Creează canvas-ul pentru un tab specific cu layout VERTICAL (2x3)"""
        if tab_idx >= len(self.tabs):
            return

        tab = self.tabs[tab_idx]
        frame = tab['frame']

        # Canvas pentru desenarea topologiei
        canvas = tk.Canvas(frame, bg='#2c3e50', highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Actualizează informațiile tab-ului
        tab['canvas'] = canvas

        # Bind evenimente
        canvas.bind("<Button-1>", self.on_server_click)
        canvas.bind("<Button-3>", self.on_right_click)  # Click dreapta
        canvas.bind("<Configure>", lambda e: self.draw_tab_topology(tab_idx))

        # Desenare inițială după o scurtă întârziere
        self.root.after(100, lambda: self.draw_tab_topology(tab_idx))

    def draw_tab_topology(self, tab_idx):
        """Desenează topologia pentru un tab specific - Layout VERTICAL (2x3)"""
        if tab_idx >= len(self.tabs):
            return

        tab = self.tabs[tab_idx]
        canvas = tab['canvas']
        servers = tab['servers']

        if canvas is None:
            return

        canvas.delete("all")
        self.server_icons = {}

        # Obține dimensiunile canvas-ului
        canvas.update_idletasks()
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()

        if canvas_width < 50 or canvas_height < 50:
            return

        # Layout GRID VERTICAL: 2 coloane x 3 rânduri (maxim 6 servere)
        cols = 2
        rows = 3

        # Calculare dimensiuni celule
        cell_width = (canvas_width - 60) / cols  # 60px padding total
        cell_height = (canvas_height - 80) / rows  # 80px padding total

        start_x = 30
        start_y = 40

        # Desenare conexiuni între servere (linii conectoare)
        server_positions = []
        for idx, (_, server) in enumerate(servers.iterrows()):
            if idx >= 6:  # Maxim 6 servere per tab
                break

            row = idx // cols
            col = idx % cols

            center_x = start_x + col * cell_width + cell_width / 2
            center_y = start_y + row * cell_height + cell_height / 2
            server_positions.append((center_x, center_y, server))

        # Desenare linii de conectare
        for i in range(len(server_positions) - 1):
            x1, y1, _ = server_positions[i]
            x2, y2, _ = server_positions[i + 1]

            canvas.create_line(x1, y1, x2, y2,
                             fill="#7f8c8d", width=2, dash=(5, 5))

        # Desenare servere
        for idx, (_, server) in enumerate(servers.iterrows()):
            if idx >= 6:  # Maxim 6 servere per tab
                break

            row = idx // cols
            col = idx % cols

            # Calculare poziție
            x = start_x + col * cell_width
            y = start_y + row * cell_height
            center_x = x + cell_width / 2
            center_y = y + cell_height / 2

            # Dimensiuni server
            server_width = min(cell_width * 0.7, 120)
            server_height = min(cell_height * 0.6, 80)

            # Culori în funcție de status și performanță
            status = server.get('Status', 'down')
            performance = server.get('Performance_Score', 0)

            if status == 'up':
                if performance >= 90:
                    color = "#27ae60"  # Verde - Excelent
                elif performance >= 70:
                    color = "#f39c12"  # Portocaliu - Bun
                else:
                    color = "#e67e22"  # Portocaliu închis - Mediu
            else:
                color = "#e74c3c"  # Roșu - Offline

            # Desenare server (dreptunghi cu colțuri rotunjite)
            x1 = center_x - server_width/2
            y1 = center_y - server_height/2
            x2 = center_x + server_width/2
            y2 = center_y + server_height/2

            # Corp server
            server_id = canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=color, outline="#2c3e50", width=3,
                tags=("server", server['ID'])
            )

            # Icon server (reprezentare vizuală)
            icon_size = 20
            canvas.create_rectangle(
                center_x - icon_size/2, center_y - icon_size,
                center_x + icon_size/2, center_y - icon_size/2,
                fill="#2c3e50", outline="#ecf0f1", width=1
            )

            # LED status indicator
            led_size = 6
            led_color = "#27ae60" if status == 'up' else "#e74c3c"
            canvas.create_oval(
                center_x - led_size/2, center_y - icon_size - led_size - 5,
                center_x + led_size/2, center_y - icon_size + 5,
                fill=led_color, outline="#ecf0f1"
            )

            # Nume server
            nume = server.get('Nume', 'Unknown')
            display_name = nume[:12] + ("..." if len(nume) > 12 else "")
            canvas.create_text(
                center_x, center_y + 10,
                text=display_name,
                font=('Segoe UI', 9, 'bold'),
                fill="#ecf0f1"
            )

            # ID server
            canvas.create_text(
                center_x, center_y + 25,
                text=server['ID'],
                font=('Segoe UI', 8),
                fill="#bdc3c7"
            )

            # Metrici rapide (doar pentru servere online)
            if status == 'up':
                cpu_usage = server.get('CPU_Usage', 0)
                ram_usage = server.get('RAM_Usage', 0)
                metrics_text = f"CPU: {cpu_usage:.0f}% | RAM: {ram_usage:.0f}%"
                canvas.create_text(
                    center_x, y2 + 15,
                    text=metrics_text,
                    font=('Segoe UI', 7),
                    fill="#95a5a6"
                )
            else:
                canvas.create_text(
                    center_x, y2 + 15,
                    text="❌ OFFLINE",
                    font=('Segoe UI', 8, 'bold'),
                    fill="#e74c3c"
                )

            # Memorare poziție pentru click
            self.server_icons[server['ID']] = {
                'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                'tab_idx': tab_idx, 'canvas_id': server_id
            }

        print(f"✅ Topologie desenată pentru tab {tab_idx + 1}: {len(server_positions)} servere")

    def create_context_menu(self):
        """Creează meniul contextual pentru click dreapta"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="📊 Detalii Server", command=self.show_context_details)
        self.context_menu.add_command(label="🔄 Restart Server", command=self.restart_context_server)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="✏️ Editare Proprietăți", command=self.edit_context_server)
        self.context_menu.add_command(label="🗑️ Ștergere Server", command=self.delete_context_server)

        self.context_server_id = None

    def on_right_click(self, event):
        """Handle pentru click dreapta pe server"""
        canvas = self.tabs[self.current_tab]['canvas']
        x, y = event.x, event.y

        # Găsește serverul clickat
        for server_id, info in self.server_icons.items():
            if (info['tab_idx'] == self.current_tab and
                info['x1'] <= x <= info['x2'] and
                info['y1'] <= y <= info['y2']):

                self.context_server_id = server_id
                self.context_menu.post(event.x_root, event.y_root)
                print(f"🖱️ Context menu pentru server: {server_id}")
                return

# Găsește funcția show_context_details() și înlocuiește-o:

    def show_context_details(self):
        """Afișează detaliile serverului din context menu"""
        if self.context_server_id:
            print(f"🖱️ Context menu: Afișare detalii pentru {self.context_server_id}")

            # Setează serverul ca selectat
            self.current_selected = self.context_server_id

            # Afișează detaliile
            self.show_server_details(self.context_server_id)

            # IMPORTANT: Fă highlight vizual pe server
            self.highlight_selected_server(self.context_server_id)

            # Asigură-te că panoul de detalii este vizibil (scroll la început)
            try:
                self.details_canvas.yview_moveto(0)  # Scroll la începutul panoului
            except:
                pass

            # Feedback vizual suplimentar - flash effect pe panoul de detalii
            try:
                original_bg = self.scrollable_frame.cget('bg')
                self.scrollable_frame.configure(bg='#3498db')  # Flash albastru
                self.root.after(200, lambda: self.scrollable_frame.configure(bg=original_bg))
            except:
                pass

            print(f"✅ Context menu: Detalii afișate pentru {self.context_server_id}")
        else:
            print("⚠️ Context menu: Nu există server selectat în context")
            messagebox.showwarning("Avertisment", "Nu s-a putut identifica serverul selectat.")

    def restart_context_server(self):
        """Restart server din context menu"""
        if self.context_server_id:
            self.simulate_server_restart(self.context_server_id)

    def edit_context_server(self):
        """Editare server din context menu"""
        if self.context_server_id:
            self.edit_server_properties(self.context_server_id)

    def delete_context_server(self):
        """Ștergere server din context menu"""
        if self.context_server_id:
            self.current_selected = self.context_server_id
            self.delete_server()

    def create_details_panel(self, parent):
        """Creează panoul pentru detalii server și controale cu scroll îmbunătățit"""
        # Header panou detalii
        details_header = tk.Frame(parent, bg='#34495e', height=50)
        details_header.pack(fill=tk.X, padx=10, pady=(10, 5))
        details_header.pack_propagate(False)

        tk.Label(details_header, text="🔍 Detalii & Control",
                font=('Segoe UI', 14, 'bold'), fg='#ecf0f1', bg='#34495e').pack(pady=15)

        # Canvas și scrollbar container
        scroll_container = tk.Frame(parent, bg='#34495e')
        scroll_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Canvas pentru scroll
        self.details_canvas = tk.Canvas(scroll_container, bg='#34495e', highlightthickness=0)

        # Scrollbar vertical personalizat (mai gros) - folosind tk.Scrollbar
        details_scrollbar = tk.Scrollbar(scroll_container,
                                        orient="vertical",
                                        command=self.details_canvas.yview,
                                        bg='#34495e',           # Culoarea de fundal
                                        troughcolor='#2c3e50',  # Culoarea canalului
                                        activebackground='#5a6c7d',  # Culoarea când este activ
                                        width=25,               # Lățimea scrollbar-ului (mai gros)
                                        borderwidth=2,
                                        highlightthickness=0)

        # Frame pentru conținutul scrollabil
        self.scrollable_frame = tk.Frame(self.details_canvas, bg='#34495e')

        # Configurare scroll
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.details_canvas.configure(scrollregion=self.details_canvas.bbox("all"))
        )

        self.details_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.details_canvas.configure(yscrollcommand=details_scrollbar.set)

        # Pack canvas și scrollbar
        self.details_canvas.pack(side="left", fill="both", expand=True)
        details_scrollbar.pack(side="right", fill="y")

        # Bind mouse wheel pentru scroll - versiune îmbunătățită
        def _on_mousewheel(event):
            # Verifică dacă canvas-ul poate face scroll
            try:
                self.details_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except:
                # Pentru sisteme care nu au event.delta
                if event.num == 4:
                    self.details_canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    self.details_canvas.yview_scroll(1, "units")

        def bind_mousewheel_to_widget(widget):
            """Adaugă funcționalitatea de scroll cu rotița la un widget și la copiii săi"""
            widget.bind("<MouseWheel>", _on_mousewheel)
            widget.bind("<Button-4>", _on_mousewheel)  # Linux scroll up
            widget.bind("<Button-5>", _on_mousewheel)  # Linux scroll down

            # Aplică la toți copiii recursiv
            try:
                for child in widget.winfo_children():
                    bind_mousewheel_to_widget(child)
            except:
                pass

        # Aplică funcționalitatea de scroll la toate widget-urile
        bind_mousewheel_to_widget(scroll_container)
        bind_mousewheel_to_widget(self.details_canvas)
        bind_mousewheel_to_widget(self.scrollable_frame)

        # Creare secțiuni de conținut
        self.create_info_section(self.scrollable_frame)
        self.create_metrics_section(self.scrollable_frame)
        self.create_controls_section(self.scrollable_frame)
        self.create_logs_section(self.scrollable_frame)
        self.create_alerts_section(self.scrollable_frame)

        # Actualizează scroll region după crearea conținutului
        self.root.after(100, lambda: self.details_canvas.configure(scrollregion=self.details_canvas.bbox("all")))

        # Actualizează binding-urile pentru mouse wheel după crearea conținutului
        def update_mousewheel_bindings():
            """Actualizează binding-urile pentru toate widget-urile nou create"""
            bind_mousewheel_to_widget(self.scrollable_frame)

        # Apelează actualizarea binding-urilor după o scurtă întârziere
        self.root.after(200, update_mousewheel_bindings)

    def create_info_section(self, parent):
        """Secțiunea de informații de bază"""
        info_frame = tk.LabelFrame(parent, text="📋 Informații Server",
                                  bg='#34495e', fg='#ecf0f1',
                                  font=('Segoe UI', 10, 'bold'), bd=2)
        info_frame.pack(fill=tk.X, padx=5, pady=5)

        # Variabile pentru informații
        self.info_vars = {
            'id': tk.StringVar(value="Selectați un server"),
            'nume': tk.StringVar(value="-"),
            'ip': tk.StringVar(value="-"),
            'locatie': tk.StringVar(value="-"),
            'status': tk.StringVar(value="-"),
            'uptime': tk.StringVar(value="-"),
            'ultima_verificare': tk.StringVar(value="-")
        }

        # Labels pentru informații
        info_labels = [
            ("🆔 ID:", self.info_vars['id']),
            ("📛 Nume:", self.info_vars['nume']),
            ("🌐 IP:", self.info_vars['ip']),
            ("📍 Locație:", self.info_vars['locatie']),
            ("🔄 Status:", self.info_vars['status']),
            ("⏱️ Uptime:", self.info_vars['uptime']),
            ("🕐 Verificat:", self.info_vars['ultima_verificare'])
        ]

        for label_text, var in info_labels:
            frame = tk.Frame(info_frame, bg='#34495e')
            frame.pack(fill=tk.X, pady=2)

            tk.Label(frame, text=label_text, font=('Segoe UI', 9, 'bold'),
                    fg='#3498db', bg='#34495e', width=12, anchor='w').pack(side=tk.LEFT)
            tk.Label(frame, textvariable=var, font=('Segoe UI', 9),
                    fg='#ecf0f1', bg='#34495e', anchor='w').pack(side=tk.LEFT, fill=tk.X, expand=True)

    def create_metrics_section(self, parent):
        """Secțiunea pentru metrici de performanță"""
        metrics_frame = tk.LabelFrame(parent, text="📊 Metrici Performanță",
                                     bg='#34495e', fg='#ecf0f1',
                                     font=('Segoe UI', 10, 'bold'), bd=2)
        metrics_frame.pack(fill=tk.X, padx=5, pady=5)

        # Variables pentru metrici
        self.metrics_vars = {
            'cpu': tk.StringVar(value="0%"),
            'ram': tk.StringVar(value="0%"),
            'disk': tk.StringVar(value="0%"),
            'network_in': tk.StringVar(value="0 KB/s"),
            'network_out': tk.StringVar(value="0 KB/s"),
            'performance': tk.StringVar(value="0%")
        }

        # Progress bars pentru metrici
        self.progress_bars = {}
        metrics_config = [
            ("💻 CPU Usage:", self.metrics_vars['cpu'], 'cpu'),
            ("🧠 RAM Usage:", self.metrics_vars['ram'], 'ram'),
            ("💾 Disk Usage:", self.metrics_vars['disk'], 'disk'),
            ("🔻 Network In:", self.metrics_vars['network_in'], 'network_in'),
            ("🔺 Network Out:", self.metrics_vars['network_out'], 'network_out'),
            ("⚡ Performance:", self.metrics_vars['performance'], 'performance')
        ]

        for label_text, var, key in metrics_config:
            frame = tk.Frame(metrics_frame, bg='#34495e')
            frame.pack(fill=tk.X, pady=3)

            # Label
            tk.Label(frame, text=label_text, font=('Segoe UI', 9, 'bold'),
                    fg='#3498db', bg='#34495e', width=15, anchor='w').pack(side=tk.LEFT)

            # Progress bar (pentru CPU, RAM, Disk, Performance)
            if key in ['cpu', 'ram', 'disk', 'performance']:
                progress = ttk.Progressbar(frame, length=100, mode='determinate')
                progress.pack(side=tk.LEFT, padx=(5, 10))
                self.progress_bars[key] = progress

            # Value label
            tk.Label(frame, textvariable=var, font=('Segoe UI', 9),
                    fg='#ecf0f1', bg='#34495e', width=10, anchor='w').pack(side=tk.LEFT)

    def create_controls_section(self, parent):
        """Secțiunea pentru controale server"""
        controls_frame = tk.LabelFrame(parent, text="🎛️ Controale Server",
                                      bg='#34495e', fg='#ecf0f1',
                                      font=('Segoe UI', 10, 'bold'), bd=2)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)

        # Butoane de control
        btn_configs = [
            ("🔄 Refresh Status", self.refresh_status, "#3498db"),
            ("🔄 Restart Server", self.restart_selected_server, "#e67e22"),
            ("✏️ Edit Properties", self.edit_selected_server, "#9b59b6"),
            ("📊 Performance Test", self.run_performance_test, "#27ae60")
        ]

        for i, (text, command, color) in enumerate(btn_configs):
            if i % 2 == 0:
                btn_frame = tk.Frame(controls_frame, bg='#34495e')
                btn_frame.pack(fill=tk.X, pady=2)

            btn = tk.Button(btn_frame, text=text, command=command,
                           font=('Segoe UI', 8), bg=color, fg='white',  # Font mai mic
                           relief='flat',
                           width=26,        # Lățime fixă în caractere
                           pady=4)          # Padding vertical mai mic
            btn.pack(side=tk.LEFT, padx=2, pady=1)  # Fără fill și expand

    def create_logs_section(self, parent):
        """Secțiunea pentru loguri"""
        logs_frame = tk.LabelFrame(parent, text="📜 System Logs",
                                  bg='#34495e', fg='#ecf0f1',
                                  font=('Segoe UI', 10, 'bold'), bd=2)
        logs_frame.pack(fill=tk.X, padx=5, pady=5)

        # Text widget pentru loguri
        logs_container = tk.Frame(logs_frame, bg='#34495e')
        logs_container.pack(fill=tk.X, pady=5)

        self.log_text = tk.Text(logs_container, height=8, wrap=tk.WORD,
                               font=('Consolas', 9), bg='#2c3e50', fg='#ecf0f1',
                               selectbackground='#3498db')
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        log_scrollbar = ttk.Scrollbar(logs_container, command=self.log_text.yview,
                                     style='Custom.Vertical.TScrollbar')
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=log_scrollbar.set)

        # Butoane pentru loguri
        log_btn_frame = tk.Frame(logs_frame, bg='#34495e')
        log_btn_frame.pack(fill=tk.X, pady=(5, 0))

        tk.Button(log_btn_frame, text="✏️ Edit Logs", command=self.edit_logs,
                 font=('Segoe UI', 8), bg='#9b59b6', fg='white',
                 relief='flat', padx=10).pack(side=tk.LEFT, padx=2)

        tk.Button(log_btn_frame, text="🔄 Refresh Logs", command=self.refresh_logs,
                 font=('Segoe UI', 8), bg='#3498db', fg='white',
                 relief='flat', padx=10).pack(side=tk.LEFT, padx=2)

        tk.Button(log_btn_frame, text="🗑️ Clear Logs", command=self.clear_logs,
                 font=('Segoe UI', 8), bg='#e74c3c', fg='white',
                 relief='flat', padx=10).pack(side=tk.RIGHT, padx=2)

    def create_alerts_section(self, parent):
        """Secțiunea pentru alerte"""
        alerts_frame = tk.LabelFrame(parent, text="🚨 System Alerts",
                                    bg='#34495e', fg='#ecf0f1',
                                    font=('Segoe UI', 10, 'bold'), bd=2)
        alerts_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Lista pentru alerte
        alerts_container = tk.Frame(alerts_frame, bg='#34495e')
        alerts_container.pack(fill=tk.BOTH, expand=True, pady=5)

        self.alert_listbox = tk.Listbox(alerts_container, height=6,
                                       font=('Segoe UI', 9), bg='#2c3e50', fg='#ecf0f1',
                                       selectbackground='#e74c3c', selectmode=tk.SINGLE)
        self.alert_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        alert_scrollbar = ttk.Scrollbar(alerts_container, command=self.alert_listbox.yview,
                                       style='Custom.Vertical.TScrollbar')
        alert_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.alert_listbox.config(yscrollcommand=alert_scrollbar.set)

        # Buton pentru clear alerte
        tk.Button(alerts_frame, text="🗑️ Clear All Alerts", command=self.clear_alerts,
                 font=('Segoe UI', 9), bg='#e74c3c', fg='white',
                 relief='flat', padx=10, pady=3).pack(pady=(5, 0))

    def on_tab_changed(self, event):
        """Handle pentru schimbarea tab-ului"""
        try:
            selected = self.notebook.index(self.notebook.select())
            if 0 <= selected < len(self.tabs):
                self.current_tab = selected
                print(f"📑 Tab schimbat la {selected + 1}")

                # Clear selecția curentă
                self.current_selected = None
                self.clear_server_details()
        except Exception as e:
            print(f"❌ Eroare la schimbarea tab-ului: {e}")

    def on_server_click(self, event):
        """Handle pentru click pe server"""
        try:
            canvas = self.tabs[self.current_tab]['canvas']
            x, y = event.x, event.y

            # Găsește serverul clickat
            for server_id, info in self.server_icons.items():
                if (info['tab_idx'] == self.current_tab and
                    info['x1'] <= x <= info['x2'] and
                    info['y1'] <= y <= info['y2']):

                    print(f"🖱️ Server selectat: {server_id}")
                    self.current_selected = server_id
                    self.show_server_details(server_id)

                    # Highlight visual
                    self.highlight_selected_server(server_id)
                    return

            # Click pe zonă fără server
            print("🖱️ Click pe zonă fără server")
            self.current_selected = None
            self.clear_server_details()
        except Exception as e:
            print(f"❌ Eroare la click server: {e}")

    def highlight_selected_server(self, server_id):
        """Evidențiază serverul selectat"""
        try:
            if server_id in self.server_icons:
                info = self.server_icons[server_id]
                canvas = self.tabs[info['tab_idx']]['canvas']

                # Șterge highlight-urile anterioare
                canvas.delete("highlight")

                # Adaugă highlight pentru serverul selectat
                canvas.create_rectangle(
                    info['x1'] - 5, info['y1'] - 5,
                    info['x2'] + 5, info['y2'] + 5,
                    outline="#f1c40f", width=3, tags="highlight"
                )
        except Exception as e:
            print(f"❌ Eroare la highlight server: {e}")

    def show_server_details(self, server_id):
        """Afișează detaliile unui server cu verificări de siguranță"""
        try:
            server = self.servers[self.servers['ID'] == server_id]
            if server.empty:
                print(f"⚠️ Serverul {server_id} nu a fost găsit")
                return

            server = server.iloc[0]
            print(f"📊 Afișare detalii pentru {server_id}")

            # Actualizare informații de bază
            self.info_vars['id'].set(server['ID'])
            self.info_vars['nume'].set(server.get('Nume', 'Unknown'))
            self.info_vars['ip'].set(server.get('IP', '0.0.0.0'))
            self.info_vars['locatie'].set(server.get('Locatie', 'Unknown'))

            status = server.get('Status', 'down')
            status_text = f"{'🟢 ONLINE' if status == 'up' else '🔴 OFFLINE'}"
            self.info_vars['status'].set(status_text)

            uptime_hours = server.get('Uptime_Hours', 0)
            uptime_text = f"{uptime_hours:.0f}h ({uptime_hours/24:.1f} zile)"
            self.info_vars['uptime'].set(uptime_text)

            if 'UltimaVerificare' in server and pd.notna(server['UltimaVerificare']):
                ultima_verificare = server['UltimaVerificare'].strftime('%d/%m/%Y %H:%M')
            else:
                ultima_verificare = "Necunoscut"
            self.info_vars['ultima_verificare'].set(ultima_verificare)

            # Actualizare metrici
            if status == 'up':
                cpu_usage = server.get('CPU_Usage', 0)
                ram_usage = server.get('RAM_Usage', 0)
                disk_usage = server.get('Disk_Usage', 0)
                network_in = server.get('Network_In', 0)
                network_out = server.get('Network_Out', 0)
                performance = server.get('Performance_Score', 0)

                self.metrics_vars['cpu'].set(f"{cpu_usage:.1f}%")
                self.metrics_vars['ram'].set(f"{ram_usage:.1f}%")
                self.metrics_vars['disk'].set(f"{disk_usage:.1f}%")
                self.metrics_vars['network_in'].set(f"{network_in} KB/s")
                self.metrics_vars['network_out'].set(f"{network_out} KB/s")
                self.metrics_vars['performance'].set(f"{performance:.0f}%")

                # Actualizare progress bars
                if 'cpu' in self.progress_bars:
                    self.progress_bars['cpu']['value'] = cpu_usage
                if 'ram' in self.progress_bars:
                    self.progress_bars['ram']['value'] = ram_usage
                if 'disk' in self.progress_bars:
                    self.progress_bars['disk']['value'] = disk_usage
                if 'performance' in self.progress_bars:
                    self.progress_bars['performance']['value'] = performance
            else:
                # Server offline
                for key in ['cpu', 'ram', 'disk', 'performance']:
                    self.metrics_vars[key].set("0%")
                    if key in self.progress_bars:
                        self.progress_bars[key]['value'] = 0

                self.metrics_vars['network_in'].set("0 KB/s")
                self.metrics_vars['network_out'].set("0 KB/s")

            # Actualizare loguri
            logs = server.get('Loguri', 'No logs available')
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, logs)
            self.log_text.config(state=tk.DISABLED)

        except Exception as e:
            print(f"❌ Eroare la afișarea detaliilor: {e}")
            messagebox.showerror("Eroare", f"Eroare la afișarea detaliilor serverului: {str(e)}")

    def clear_server_details(self):
        """Șterge detaliile serverului"""
        try:
            print("🧹 Clear detalii server")

            # Clear informații
            self.info_vars['id'].set("Selectați un server")
            for key in ['nume', 'ip', 'locatie', 'status', 'uptime', 'ultima_verificare']:
                self.info_vars[key].set("-")

            # Clear metrici
            for key in ['cpu', 'ram', 'disk', 'performance']:
                self.metrics_vars[key].set("0%")
                if key in self.progress_bars:
                    self.progress_bars[key]['value'] = 0

            self.metrics_vars['network_in'].set("0 KB/s")
            self.metrics_vars['network_out'].set("0 KB/s")

            # Clear loguri
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)
            self.log_text.config(state=tk.DISABLED)

            # Remove highlight
            for tab in self.tabs:
                if tab['canvas']:
                    tab['canvas'].delete("highlight")
        except Exception as e:
            print(f"❌ Eroare la clear detalii: {e}")

    def generate_server_id(self):
        """Generează un ID unic pentru server"""
        existing_ids = set(self.servers['ID'].tolist())

        # Încercă cu format SRV-XXX
        for i in range(1, 1000):
            new_id = f"SRV-{i:03d}"
            if new_id not in existing_ids:
                return new_id

        # Fallback cu timestamp
        import time
        return f"SRV-{int(time.time() % 10000)}"



    def generate_server_id(self):
        """Generează un ID unic pentru server"""
        existing_ids = set(self.servers['ID'].tolist())

        # Încercă cu format SRV-XXX
        for i in range(1, 1000):
            new_id = f"SRV-{i:03d}"
            if new_id not in existing_ids:
                return new_id

        # Fallback cu timestamp
        import time
        return f"SRV-{int(time.time() % 10000)}"

    def add_server(self):
        """Adaugă un server nou cu interfață completă"""
        try:
            print("➕ Deschid fereastra pentru adăugare server")

            # Fereastră modală pentru adăugare server
            add_win = tk.Toplevel(self.root)
            add_win.title("➕ Adăugare Server Nou")
            add_win.geometry("500x600")  # Mărită puțin înălțimea
            add_win.configure(bg='#34495e')
            add_win.resizable(False, False)

            # Centrează fereastra
            add_win.transient(self.root)
            add_win.grab_set()

            # Variabile pentru form (definite mai devreme pentru a fi accesibile în save_server)
            form_vars = {
                'id': tk.StringVar(value=self.generate_server_id()),
                'nume': tk.StringVar(),
                'ip': tk.StringVar(),
                'locatie': tk.StringVar(),
                'status': tk.StringVar(value='up')
            }

            # Checkbox pentru configurări automate (definite mai devreme)
            auto_config = tk.BooleanVar(value=True)
            auto_logs = tk.BooleanVar(value=True)

            # Funcția save_server definită mai devreme pentru a fi accesibilă în header
            def save_server():
                try:
                    # Validare date
                    server_id = form_vars['id'].get().strip()
                    nume = form_vars['nume'].get().strip()
                    ip = form_vars['ip'].get().strip()
                    locatie = form_vars['locatie'].get().strip()
                    status = form_vars['status'].get()

                    # Verificări validare
                    if not server_id:
                        messagebox.showerror("Eroare", "ID-ul serverului este obligatoriu!", parent=add_win)
                        return

                    if server_id in self.servers['ID'].values:
                        messagebox.showerror("Eroare", f"ID-ul {server_id} există deja!", parent=add_win)
                        return

                    if not nume:
                        messagebox.showerror("Eroare", "Numele serverului este obligatoriu!", parent=add_win)
                        return

                    if not ip:
                        messagebox.showerror("Eroare", "Adresa IP este obligatorie!", parent=add_win)
                        return

                    # Validare IP simplă
                    ip_parts = ip.split('.')
                    if len(ip_parts) != 4 or not all(part.isdigit() and 0 <= int(part) <= 255 for part in ip_parts):
                        messagebox.showerror("Eroare", "Adresa IP nu este validă!", parent=add_win)
                        return

                    if not locatie:
                        locatie = "Unknown"

                    print(f"➕ Adaug server nou: {server_id} - {nume}")

                    # Pregătire date pentru noul server
                    new_server_data = {
                        'ID': server_id,
                        'Nume': nume,
                        'IP': ip,
                        'Locatie': locatie,
                        'Status': status,
                        'UltimaVerificare': datetime.now()
                    }

                    # Generare metrici automate
                    if auto_config.get() and status == 'up':
                        new_server_data.update({
                            'CPU_Usage': random.uniform(10, 60),
                            'RAM_Usage': random.uniform(20, 70),
                            'Disk_Usage': random.uniform(30, 80),
                            'Network_In': random.randint(100, 2000),
                            'Network_Out': random.randint(100, 2000),
                            'Uptime_Hours': random.uniform(1, 100),
                            'Performance_Score': random.uniform(70, 95)
                        })
                    else:
                        # Server offline sau fără configurare automată
                        new_server_data.update({
                            'CPU_Usage': 0,
                            'RAM_Usage': 0,
                            'Disk_Usage': 0,
                            'Network_In': 0,
                            'Network_Out': 0,
                            'Uptime_Hours': 0,
                            'Performance_Score': 0
                        })

                    # Generare loguri inițiale
                    if auto_logs.get():
                        if status == 'up':
                            initial_logs = f"""[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Server creat și adăugat în sistem
[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Configurare inițială completă
[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Servicii de bază activate
[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sistem operațional funcțional
[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Monitorizare activată"""
                        else:
                            initial_logs = f"""[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Server creat în sistem
[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Status: Offline
[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Așteptare pornire sistem"""
                    else:
                        initial_logs = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Server adăugat în sistem"

                    new_server_data['Loguri'] = initial_logs

                    # Adăugare în DataFrame
                    new_server_df = pd.DataFrame([new_server_data])
                    self.servers = pd.concat([self.servers, new_server_df], ignore_index=True)

                    # Salvare în Excel
                    self.save_data()
                    self.refresh_topology()

                    # Alertă succes
                    self.add_alert(f"➕ SERVER ADĂUGAT: {server_id} ({nume}) - Adăugat cu succes în sistem", "success")

                    # Închide fereastra
                    add_win.destroy()

                    # Mesaj succes
                    messagebox.showinfo("Succes", f"Serverul {server_id} ({nume}) a fost adăugat cu succes!\n\nStatusul inițial: {'Online' if status == 'up' else 'Offline'}", parent=self.root)

                    print(f"✅ Server adăugat cu succes: {server_id}")

                except Exception as e:
                    print(f"❌ Eroare la adăugarea serverului: {e}")
                    messagebox.showerror("Eroare", f"Eroare la adăugarea serverului:\n{str(e)}", parent=add_win)

            # Header CARE ESTE ȘI BUTON DE SALVARE
            header_frame = tk.Frame(add_win, bg='#2c3e50', height=70)
            header_frame.pack(fill=tk.X)
            header_frame.pack_propagate(False)

            # BUTONUL HEADER PRINCIPAL - Mare și vizibil
            save_header_btn = tk.Button(header_frame,
                                       text="💾 SALVEAZĂ SERVER NOU",
                                       command=save_server,
                                       font=('Segoe UI', 16, 'bold'),
                                       bg='#27ae60', fg='white',
                                       relief='flat',
                                       cursor='hand2',
                                       activebackground='#229954')
            save_header_btn.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

            # Form container
            form_frame = tk.Frame(add_win, bg='#34495e')
            form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

            # Câmpuri form
            form_fields = [
                ("🆔 ID Server:", form_vars['id'], "SRV-001"),
                ("📛 Nume Server:", form_vars['nume'], "Web Server"),
                ("🌐 Adresă IP:", form_vars['ip'], "192.168.1.100"),
                ("📍 Locație:", form_vars['locatie'], "Rack A1")
            ]

            entries = {}

            for label_text, var, placeholder in form_fields:
                # Label
                tk.Label(form_frame, text=label_text, font=('Segoe UI', 11, 'bold'),
                        fg='#3498db', bg='#34495e').pack(anchor='w', pady=(8, 3))

                # Entry
                entry = tk.Entry(form_frame, textvariable=var, font=('Segoe UI', 11),
                               bg='#2c3e50', fg='#ecf0f1', insertbackground='#3498db',
                               relief='solid', bd=1)
                entry.pack(fill=tk.X, pady=(0, 3), ipady=6)
                entries[label_text] = entry

                # Placeholder help - mai mic
                tk.Label(form_frame, text=f"Ex: {placeholder}",
                        font=('Segoe UI', 8), fg='#95a5a6', bg='#34495e').pack(anchor='w', pady=(0, 5))

            # Status selector
            tk.Label(form_frame, text="🔄 Status Inițial:", font=('Segoe UI', 11, 'bold'),
                    fg='#3498db', bg='#34495e').pack(anchor='w', pady=(8, 3))

            status_frame = tk.Frame(form_frame, bg='#34495e')
            status_frame.pack(fill=tk.X, pady=(0, 8))

            tk.Radiobutton(status_frame, text="🟢 Online", variable=form_vars['status'], value='up',
                          font=('Segoe UI', 10), fg='#27ae60', bg='#34495e',
                          selectcolor='#2c3e50').pack(side=tk.LEFT, padx=(0, 20))

            tk.Radiobutton(status_frame, text="🔴 Offline", variable=form_vars['status'], value='down',
                          font=('Segoe UI', 10), fg='#e74c3c', bg='#34495e',
                          selectcolor='#2c3e50').pack(side=tk.LEFT)

            # Separator mai mic
            tk.Frame(form_frame, height=1, bg='#2c3e50').pack(fill=tk.X, pady=10)

            # Configurări avansate - mai compacte
            tk.Label(form_frame, text="⚙️ Configurări Avansate",
                    font=('Segoe UI', 11, 'bold'), fg='#f39c12', bg='#34495e').pack(anchor='w', pady=(0, 5))

            # Checkbox pentru configurări automate
            tk.Checkbutton(form_frame, text="📊 Generare automată metrici performanță",
                          variable=auto_config, font=('Segoe UI', 9),
                          fg='#ecf0f1', bg='#34495e', selectcolor='#2c3e50').pack(anchor='w', pady=2)

            tk.Checkbutton(form_frame, text="📜 Creeare loguri inițiale",
                          variable=auto_logs, font=('Segoe UI', 9),
                          fg='#ecf0f1', bg='#34495e', selectcolor='#2c3e50').pack(anchor='w', pady=2)

            # Funcții helper
            def generate_new_id():
                """Generează un ID nou"""
                form_vars['id'].set(self.generate_server_id())

            def validate_ip(event):
                """Validează IP-ul în timp real"""
                ip = form_vars['ip'].get()
                if ip:
                    # Feedback vizual simplu
                    ip_parts = ip.split('.')
                    if len(ip_parts) == 4 and all(part.isdigit() and 0 <= int(part) <= 255 for part in ip_parts if part):
                        entries["🌐 Adresă IP:"].configure(bg='#27ae60')
                    else:
                        entries["🌐 Adresă IP:"].configure(bg='#2c3e50')

            # Bind validare IP
            entries["🌐 Adresă IP:"].bind('<KeyRelease>', validate_ip)

            # Footer frame cu butoane mici
            footer_frame = tk.Frame(add_win, bg='#34495e', height=50)
            footer_frame.pack(fill=tk.X, padx=20, pady=10)
            footer_frame.pack_propagate(False)

            # Butoane helper mai mici
            tk.Button(footer_frame, text="🎲 ID Nou", command=generate_new_id,
                     font=('Segoe UI', 9), bg='#f39c12', fg='white',
                     relief='flat', padx=10, pady=5).pack(side=tk.LEFT)

            tk.Button(footer_frame, text="❌ Anulează", command=add_win.destroy,
                     font=('Segoe UI', 9), bg='#e74c3c', fg='white',
                     relief='flat', padx=10, pady=5).pack(side=tk.RIGHT)

            # Info text pentru utilizator
            info_label = tk.Label(footer_frame,
                                 text="↑ Apasă butonul verde de sus pentru a salva serverul ↑",
                                 font=('Segoe UI', 9, 'italic'),
                                 fg='#95a5a6', bg='#34495e')
            info_label.pack(expand=True)

            # Auto-focus pe primul câmp
            entries["📛 Nume Server:"].focus_set()

            # Bind Enter pentru salvare rapidă
            def on_enter(event):
                save_server()

            add_win.bind('<Return>', on_enter)

        except Exception as e:
            print(f"❌ Eroare la deschiderea ferestrei de adăugare: {e}")
            messagebox.showerror("Eroare", f"Eroare la deschiderea ferestrei de adăugare server: {str(e)}")




    def edit_selected_server(self):
        """Editează serverul selectat"""
        if not self.current_selected:
            messagebox.showwarning("Avertisment", "Selectați un server pentru editare")
            return

        self.edit_server_properties(self.current_selected)

    def edit_server_properties(self, server_id):
        """Editează proprietățile unui server specific"""
        try:
            # Găsește serverul în DataFrame
            server_row = self.servers[self.servers['ID'] == server_id]
            if server_row.empty:
                messagebox.showerror("Eroare", f"Serverul {server_id} nu a fost găsit!")
                return

            server = server_row.iloc[0]
            server_idx = server_row.index[0]

            print(f"✏️ Editare proprietăți pentru {server_id}")

            # Fereastră modală pentru editare
            edit_win = tk.Toplevel(self.root)
            edit_win.title(f"✏️ Editare Server - {server_id}")
            edit_win.geometry("550x700")
            edit_win.configure(bg='#34495e')
            edit_win.resizable(False, False)

            # Centrează fereastra
            edit_win.transient(self.root)
            edit_win.grab_set()

            # Variabile pentru form (pre-populate cu datele existente)
            form_vars = {
                'id': tk.StringVar(value=server.get('ID', '')),
                'nume': tk.StringVar(value=server.get('Nume', '')),
                'ip': tk.StringVar(value=server.get('IP', '')),
                'locatie': tk.StringVar(value=server.get('Locatie', '')),
                'status': tk.StringVar(value=server.get('Status', 'down'))
            }

            # Opțiuni avansate
            reset_metrics = tk.BooleanVar(value=False)

            # Funcția save_changes definită mai devreme pentru a fi accesibilă în header
            def save_changes():
                try:
                    # Validare date
                    nume = form_vars['nume'].get().strip()
                    ip = form_vars['ip'].get().strip()
                    locatie = form_vars['locatie'].get().strip()
                    status = form_vars['status'].get()

                    # Verificări validare
                    if not nume:
                        messagebox.showerror("Eroare", "Numele serverului este obligatoriu!", parent=edit_win)
                        return

                    if not ip:
                        messagebox.showerror("Eroare", "Adresa IP este obligatorie!", parent=edit_win)
                        return

                    # Validare IP
                    ip_parts = ip.split('.')
                    if len(ip_parts) != 4 or not all(part.isdigit() and 0 <= int(part) <= 255 for part in ip_parts):
                        messagebox.showerror("Eroare", "Adresa IP nu este validă!", parent=edit_win)
                        return

                    if not locatie:
                        locatie = "Unknown"

                    print(f"💾 Salvez modificări pentru {server_id}")

                    # Detectează modificări
                    changes = []
                    if server.get('Nume') != nume:
                        changes.append(f"Nume: '{server.get('Nume')}' → '{nume}'")
                    if server.get('IP') != ip:
                        changes.append(f"IP: '{server.get('IP')}' → '{ip}'")
                    if server.get('Locatie') != locatie:
                        changes.append(f"Locație: '{server.get('Locatie')}' → '{locatie}'")
                    if server.get('Status') != status:
                        changes.append(f"Status: '{server.get('Status')}' → '{status}'")

                    if not changes and not reset_metrics.get():
                        messagebox.showinfo("Info", "Nu s-au detectat modificări pentru salvare.", parent=edit_win)
                        return

                    # Actualizare date
                    self.servers.at[server_idx, 'Nume'] = nume
                    self.servers.at[server_idx, 'IP'] = ip
                    self.servers.at[server_idx, 'Locatie'] = locatie

                    # Schimbare status
                    old_status = server.get('Status')
                    if old_status != status:
                        self.servers.at[server_idx, 'Status'] = status

                        # Dacă serverul a devenit online, generează metrici
                        if status == 'up' and old_status == 'down':
                            self.servers.at[server_idx, 'CPU_Usage'] = random.uniform(10, 50)
                            self.servers.at[server_idx, 'RAM_Usage'] = random.uniform(20, 60)
                            self.servers.at[server_idx, 'Disk_Usage'] = random.uniform(30, 70)
                            self.servers.at[server_idx, 'Network_In'] = random.randint(100, 1500)
                            self.servers.at[server_idx, 'Network_Out'] = random.randint(100, 1500)
                            self.servers.at[server_idx, 'Performance_Score'] = random.uniform(70, 95)
                            self.servers.at[server_idx, 'Uptime_Hours'] = 0
                        elif status == 'down':
                            # Server offline - resetează metrici
                            for metric in ['CPU_Usage', 'RAM_Usage', 'Disk_Usage', 'Network_In', 'Network_Out', 'Performance_Score', 'Uptime_Hours']:
                                if metric in self.servers.columns:
                                    self.servers.at[server_idx, metric] = 0

                    # Reset metrici dacă solicitat
                    if reset_metrics.get() and status == 'up':
                        self.servers.at[server_idx, 'CPU_Usage'] = random.uniform(10, 30)
                        self.servers.at[server_idx, 'RAM_Usage'] = random.uniform(15, 40)
                        self.servers.at[server_idx, 'Disk_Usage'] = random.uniform(20, 50)
                        self.servers.at[server_idx, 'Network_In'] = random.randint(100, 1000)
                        self.servers.at[server_idx, 'Network_Out'] = random.randint(100, 1000)
                        self.servers.at[server_idx, 'Performance_Score'] = random.uniform(80, 98)
                        self.servers.at[server_idx, 'Uptime_Hours'] = 0
                        changes.append("Metrici resetate")

                    # Update timestamp
                    self.servers.at[server_idx, 'UltimaVerificare'] = datetime.now()

                    # Update logs cu modificările
                    if 'Loguri' in self.servers.columns:
                        current_logs = self.servers.at[server_idx, 'Loguri']
                        change_log = f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Proprietăți modificate manual"
                        for change in changes:
                            change_log += f"\n  - {change}"
                        self.servers.at[server_idx, 'Loguri'] = current_logs + change_log

                    # Salvare și actualizare
                    self.save_data()

                    # Actualizare interfață
                    if self.current_selected == server_id:
                        self.show_server_details(server_id)
                    self.refresh_topology()

                    # Alertă modificare
                    changes_text = " | ".join(changes[:2])  # Primele 2 modificări
                    self.add_alert(f"✏️ SERVER MODIFICAT: {server_id} - {changes_text}", "info")

                    # Închide fereastra
                    edit_win.destroy()

                    # Mesaj succes
                    messagebox.showinfo("Succes",
                                      f"Serverul {server_id} a fost modificat cu succes!\n\nModificări:\n" +
                                      "\n".join(f"• {change}" for change in changes),
                                      parent=self.root)

                    print(f"✅ Server modificat cu succes: {server_id}")

                except Exception as e:
                    print(f"❌ Eroare la salvarea modificărilor: {e}")
                    messagebox.showerror("Eroare", f"Eroare la salvarea modificărilor:\n{str(e)}", parent=edit_win)

            # Header CARE ESTE ȘI BUTON DE SALVARE
            header_frame = tk.Frame(edit_win, bg='#2c3e50', height=80)
            header_frame.pack(fill=tk.X)
            header_frame.pack_propagate(False)

            # BUTONUL HEADER PRINCIPAL - Mare și vizibil
            save_header_btn = tk.Button(header_frame,
                                       text="💾 SALVEAZĂ MODIFICĂRI",
                                       command=save_changes,
                                       font=('Segoe UI', 16, 'bold'),
                                       bg='#3498db', fg='white',  # Albastru pentru modificare
                                       relief='flat',
                                       cursor='hand2',
                                       activebackground='#2980b9')
            save_header_btn.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

            # Subtitle în header
            subtitle_frame = tk.Frame(edit_win, bg='#34495e', height=25)
            subtitle_frame.pack(fill=tk.X)
            subtitle_frame.pack_propagate(False)

            tk.Label(subtitle_frame, text=f"Server: {server_id} | Modificați proprietățile și apăsați butonul albastru ↑",
                    font=('Segoe UI', 9, 'italic'), fg='#95a5a6', bg='#34495e').pack(pady=5)

            # Form container
            form_frame = tk.Frame(edit_win, bg='#34495e')
            form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

            # Informații de bază
            tk.Label(form_frame, text="📋 Informații de Bază",
                    font=('Segoe UI', 12, 'bold'), fg='#3498db', bg='#34495e').pack(anchor='w', pady=(0, 8))

            # Câmpuri form
            basic_fields = [
                ("🆔 ID Server:", form_vars['id'], False),  # ID nu poate fi modificat
                ("📛 Nume Server:", form_vars['nume'], True),
                ("🌐 Adresă IP:", form_vars['ip'], True),
                ("📍 Locație:", form_vars['locatie'], True)
            ]

            entries = {}

            for label_text, var, editable in basic_fields:
                # Label
                tk.Label(form_frame, text=label_text, font=('Segoe UI', 10, 'bold'),
                        fg='#ecf0f1', bg='#34495e').pack(anchor='w', pady=(6, 2))

                # Entry
                entry = tk.Entry(form_frame, textvariable=var, font=('Segoe UI', 10),
                               bg='#2c3e50' if editable else '#1a252f',
                               fg='#ecf0f1' if editable else '#7f8c8d',
                               insertbackground='#3498db',
                               relief='solid', bd=1, state='normal' if editable else 'readonly')
                entry.pack(fill=tk.X, pady=(0, 2), ipady=5)

                if not editable:
                    tk.Label(form_frame, text="(Nu poate fi modificat)",
                            font=('Segoe UI', 7), fg='#7f8c8d', bg='#34495e').pack(anchor='w', pady=(0, 4))
                else:
                    # Spațiu pentru uniformitate
                    tk.Label(form_frame, text=" ", font=('Segoe UI', 7), bg='#34495e').pack(anchor='w', pady=(0, 4))

                entries[label_text] = entry

            # Status selector
            tk.Label(form_frame, text="🔄 Status Server:", font=('Segoe UI', 10, 'bold'),
                    fg='#ecf0f1', bg='#34495e').pack(anchor='w', pady=(8, 2))

            status_frame = tk.Frame(form_frame, bg='#34495e')
            status_frame.pack(fill=tk.X, pady=(0, 8))

            tk.Radiobutton(status_frame, text="🟢 Online", variable=form_vars['status'], value='up',
                          font=('Segoe UI', 9), fg='#27ae60', bg='#34495e',
                          selectcolor='#2c3e50').pack(side=tk.LEFT, padx=(0, 20))

            tk.Radiobutton(status_frame, text="🔴 Offline", variable=form_vars['status'], value='down',
                          font=('Segoe UI', 9), fg='#e74c3c', bg='#34495e',
                          selectcolor='#2c3e50').pack(side=tk.LEFT)

            # Separator
            tk.Frame(form_frame, height=1, bg='#2c3e50').pack(fill=tk.X, pady=8)

            # Metrici actuale (doar informativ) - mai compact
            tk.Label(form_frame, text="📊 Metrici Actuale (Doar Informativ)",
                    font=('Segoe UI', 11, 'bold'), fg='#f39c12', bg='#34495e').pack(anchor='w', pady=(0, 5))

            metrics_frame = tk.Frame(form_frame, bg='#2c3e50', relief='solid', bd=1)
            metrics_frame.pack(fill=tk.X, pady=(0, 8), padx=5)

            # Afișare metrici actuale - mai compacte
            current_metrics = [
                ("💻 CPU:", f"{server.get('CPU_Usage', 0):.1f}%"),
                ("🧠 RAM:", f"{server.get('RAM_Usage', 0):.1f}%"),
                ("💾 Disk:", f"{server.get('Disk_Usage', 0):.1f}%"),
                ("⚡ Performance:", f"{server.get('Performance_Score', 0):.0f}%"),
                ("⏱️ Uptime:", f"{server.get('Uptime_Hours', 0):.0f}h")
            ]

            # Afișare în 3 rânduri x 2 coloane (prima cu un singur element centrat)
            for i in range(0, len(current_metrics), 2):
                row_frame = tk.Frame(metrics_frame, bg='#2c3e50')
                row_frame.pack(fill=tk.X, padx=8, pady=3)

                # Prima metrică
                metric1 = current_metrics[i]
                metric_container1 = tk.Frame(row_frame, bg='#2c3e50')
                metric_container1.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

                tk.Label(metric_container1, text=metric1[0], font=('Segoe UI', 8, 'bold'),
                        fg='#3498db', bg='#2c3e50').pack(side=tk.LEFT)
                tk.Label(metric_container1, text=metric1[1], font=('Segoe UI', 8),
                        fg='#ecf0f1', bg='#2c3e50').pack(side=tk.RIGHT)

                # A doua metrică (dacă există)
                if i + 1 < len(current_metrics):
                    metric2 = current_metrics[i + 1]
                    metric_container2 = tk.Frame(row_frame, bg='#2c3e50')
                    metric_container2.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)

                    tk.Label(metric_container2, text=metric2[0], font=('Segoe UI', 8, 'bold'),
                            fg='#3498db', bg='#2c3e50').pack(side=tk.LEFT)
                    tk.Label(metric_container2, text=metric2[1], font=('Segoe UI', 8),
                            fg='#ecf0f1', bg='#2c3e50').pack(side=tk.RIGHT)

            # Opțiuni avansate
            tk.Label(form_frame, text="⚙️ Opțiuni Avansate",
                    font=('Segoe UI', 11, 'bold'), fg='#e67e22', bg='#34495e').pack(anchor='w', pady=(8, 5))

            tk.Checkbutton(form_frame, text="🔄 Resetează metrici de performanță la salvare",
                          variable=reset_metrics, font=('Segoe UI', 9),
                          fg='#e67e22', bg='#34495e', selectcolor='#2c3e50').pack(anchor='w', pady=3)

            # Funcția reset form
            def reset_form():
                """Resetează formularul la valorile originale"""
                form_vars['nume'].set(server.get('Nume', ''))
                form_vars['ip'].set(server.get('IP', ''))
                form_vars['locatie'].set(server.get('Locatie', ''))
                form_vars['status'].set(server.get('Status', 'down'))
                reset_metrics.set(False)

            # Footer frame cu butoane helper
            footer_frame = tk.Frame(edit_win, bg='#34495e', height=45)
            footer_frame.pack(fill=tk.X, padx=20, pady=10)
            footer_frame.pack_propagate(False)

            # Butoane helper mai mici
            tk.Button(footer_frame, text="🔄 Reset", command=reset_form,
                     font=('Segoe UI', 9), bg='#f39c12', fg='white',
                     relief='flat', padx=12, pady=5).pack(side=tk.LEFT)

            tk.Button(footer_frame, text="❌ Anulează", command=edit_win.destroy,
                     font=('Segoe UI', 9), bg='#e74c3c', fg='white',
                     relief='flat', padx=12, pady=5).pack(side=tk.RIGHT)

            # Info text pentru utilizator
            info_label = tk.Label(footer_frame,
                                 text="↑ Modificați câmpurile și apăsați butonul albastru de sus ↑",
                                 font=('Segoe UI', 8, 'italic'),
                                 fg='#95a5a6', bg='#34495e')
            info_label.pack(expand=True)

            # Auto-focus pe primul câmp editabil
            entries["📛 Nume Server:"].focus_set()

            # Bind Enter pentru salvare rapidă
            def on_enter(event):
                save_changes()

            edit_win.bind('<Return>', on_enter)

        except Exception as e:
            print(f"❌ Eroare la editarea serverului: {e}")
            messagebox.showerror("Eroare", f"Eroare la editarea serverului: {str(e)}")

    def run_performance_test(self):
        """Rulează un test de performanță pentru serverul selectat"""
        if not self.current_selected:
            messagebox.showwarning("Avertisment", "Selectați un server pentru testul de performanță")
            return

        try:
            # Găsește serverul în DataFrame
            server_row = self.servers[self.servers['ID'] == self.current_selected]
            if server_row.empty:
                messagebox.showerror("Eroare", f"Serverul {self.current_selected} nu a fost găsit!")
                return

            server = server_row.iloc[0]
            server_idx = server_row.index[0]

            # Verifică dacă serverul este online
            if server.get('Status') != 'up':
                messagebox.showwarning("Avertisment", f"Nu se poate testa performanța serverului {self.current_selected} - serverul este offline!")
                return

            print(f"📊 Inițiez test de performanță pentru {self.current_selected}")

            # Fereastră pentru testul de performanță
            test_win = tk.Toplevel(self.root)
            test_win.title(f"📊 Test Performanță - {self.current_selected}")
            test_win.geometry("600x500")
            test_win.configure(bg='#34495e')
            test_win.resizable(False, False)

            # Centrează fereastra
            test_win.transient(self.root)
            test_win.grab_set()

            # Header
            header_frame = tk.Frame(test_win, bg='#2c3e50', height=80)
            header_frame.pack(fill=tk.X)
            header_frame.pack_propagate(False)

            tk.Label(header_frame, text=f"📊 Test Performanță - {self.current_selected}",
                    font=('Segoe UI', 16, 'bold'), fg='#ecf0f1', bg='#2c3e50').pack()
            tk.Label(header_frame, text=f"Server: {server.get('Nume', 'Unknown')} | IP: {server.get('IP', 'Unknown')}",
                    font=('Segoe UI', 10), fg='#95a5a6', bg='#2c3e50').pack()

            # Content frame
            content_frame = tk.Frame(test_win, bg='#34495e')
            content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

            # Progress section
            progress_frame = tk.LabelFrame(content_frame, text="🔄 Progres Test",
                                         bg='#34495e', fg='#ecf0f1',
                                         font=('Segoe UI', 12, 'bold'))
            progress_frame.pack(fill=tk.X, pady=(0, 10))

            # Progress bar și status
            progress_var = tk.IntVar()
            progress_bar = ttk.Progressbar(progress_frame, variable=progress_var,
                                         maximum=100, length=400)
            progress_bar.pack(pady=10)

            status_var = tk.StringVar(value="Inițializare test...")
            status_label = tk.Label(progress_frame, textvariable=status_var,
                                  font=('Segoe UI', 10), fg='#ecf0f1', bg='#34495e')
            status_label.pack(pady=5)

            # Results section
            results_frame = tk.LabelFrame(content_frame, text="📈 Rezultate Test",
                                        bg='#34495e', fg='#ecf0f1',
                                        font=('Segoe UI', 12, 'bold'))
            results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

            # Results text area
            results_text = tk.Text(results_frame, height=15, wrap=tk.WORD,
                                 font=('Consolas', 9), bg='#2c3e50', fg='#ecf0f1',
                                 state=tk.DISABLED)
            results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Test controls
            controls_frame = tk.Frame(content_frame, bg='#34495e')
            controls_frame.pack(fill=tk.X)

            # Variabile pentru test
            test_running = tk.BooleanVar(value=False)
            test_results = {}

            def update_results_display(text, color="#ecf0f1"):
                """Actualizează afișarea rezultatelor"""
                results_text.config(state=tk.NORMAL)
                results_text.insert(tk.END, text + "\n", color)
                results_text.see(tk.END)
                results_text.config(state=tk.DISABLED)
                test_win.update()

            def run_test_sequence():
                """Rulează secvența de teste de performanță"""
                try:
                    test_running.set(True)
                    start_button.config(state='disabled')

                    # Clear results
                    results_text.config(state=tk.NORMAL)
                    results_text.delete(1.0, tk.END)
                    results_text.config(state=tk.DISABLED)

                    # Test phases
                    test_phases = [
                        ("Inițializare test sistem...", 5),
                        ("Test CPU - Single Core...", 15),
                        ("Test CPU - Multi Core...", 25),
                        ("Test memorie RAM...", 40),
                        ("Test viteza disk I/O...", 55),
                        ("Test rețea - latență...", 70),
                        ("Test rețea - bandwidth...", 85),
                        ("Finalizare și analiză...", 100)
                    ]

                    update_results_display("=" * 50)
                    update_results_display(f"🚀 ÎNCEPERE TEST PERFORMANȚĂ - {self.current_selected}")
                    update_results_display(f"⏰ Timp start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    update_results_display("=" * 50)

                    for phase_name, progress_value in test_phases:
                        if not test_running.get():  # Check if test was cancelled
                            break

                        status_var.set(phase_name)
                        progress_var.set(progress_value)

                        # Simulate test phase
                        phase_duration = random.uniform(1, 2)  # 1-2 seconds per phase
                        time.sleep(phase_duration)

                        # Generate realistic test results
                        if "CPU - Single Core" in phase_name:
                            score = random.randint(2500, 4500)
                            test_results['cpu_single'] = score
                            update_results_display(f"💻 CPU Single Core: {score} points")

                        elif "CPU - Multi Core" in phase_name:
                            single_score = test_results.get('cpu_single', 3000)
                            multi_score = int(single_score * random.uniform(3.2, 6.8))
                            test_results['cpu_multi'] = multi_score
                            update_results_display(f"💻 CPU Multi Core: {multi_score} points")

                        elif "memorie RAM" in phase_name:
                            ram_speed = random.randint(12000, 25000)  # MB/s
                            ram_latency = random.uniform(45, 85)  # ns
                            test_results['ram_speed'] = ram_speed
                            test_results['ram_latency'] = ram_latency
                            update_results_display(f"🧠 RAM Speed: {ram_speed} MB/s")
                            update_results_display(f"🧠 RAM Latency: {ram_latency:.1f} ns")

                        elif "disk I/O" in phase_name:
                            read_speed = random.randint(450, 1200)  # MB/s
                            write_speed = random.randint(350, 900)  # MB/s
                            iops = random.randint(15000, 45000)
                            test_results['disk_read'] = read_speed
                            test_results['disk_write'] = write_speed
                            test_results['disk_iops'] = iops
                            update_results_display(f"💾 Disk Read: {read_speed} MB/s")
                            update_results_display(f"💾 Disk Write: {write_speed} MB/s")
                            update_results_display(f"💾 IOPS: {iops}")

                        elif "latență" in phase_name:
                            latency = random.uniform(0.5, 8.5)  # ms
                            packet_loss = random.uniform(0, 0.2)  # %
                            test_results['net_latency'] = latency
                            test_results['net_packet_loss'] = packet_loss
                            update_results_display(f"🌐 Network Latency: {latency:.2f} ms")
                            update_results_display(f"🌐 Packet Loss: {packet_loss:.2f}%")

                        elif "bandwidth" in phase_name:
                            download = random.randint(850, 1000)  # Mbps
                            upload = random.randint(350, 500)  # Mbps
                            test_results['net_download'] = download
                            test_results['net_upload'] = upload
                            update_results_display(f"🌐 Download: {download} Mbps")
                            update_results_display(f"🌐 Upload: {upload} Mbps")

                    if test_running.get():  # Only if test completed successfully
                        # Calculate overall performance score
                        cpu_score = (test_results.get('cpu_single', 0) + test_results.get('cpu_multi', 0) / 6) / 2
                        ram_score = test_results.get('ram_speed', 0) / 200
                        disk_score = (test_results.get('disk_read', 0) + test_results.get('disk_write', 0)) / 20
                        net_score = (test_results.get('net_download', 0) + test_results.get('net_upload', 0)) / 15

                        overall_score = (cpu_score * 0.3 + ram_score * 0.25 + disk_score * 0.25 + net_score * 0.2)
                        overall_score = min(100, max(0, overall_score))

                        update_results_display("\n" + "=" * 50)
                        update_results_display("📊 REZUMAT FINAL")
                        update_results_display("=" * 50)
                        update_results_display(f"⚡ Scor General Performanță: {overall_score:.1f}/100")

                        # Performance rating
                        if overall_score >= 85:
                            rating = "🥇 EXCELENT"
                            rating_color = "#27ae60"
                        elif overall_score >= 70:
                            rating = "🥈 FOARTE BUN"
                            rating_color = "#f39c12"
                        elif overall_score >= 55:
                            rating = "🥉 BUN"
                            rating_color = "#e67e22"
                        else:
                            rating = "⚠️ NECESITĂ ATENȚIE"
                            rating_color = "#e74c3c"

                        update_results_display(f"🏆 Rating: {rating}")

                        # Update server performance in database
                        new_performance = min(100, max(0, overall_score + random.uniform(-5, 5)))
                        self.servers.at[server_idx, 'Performance_Score'] = new_performance
                        self.servers.at[server_idx, 'UltimaVerificare'] = datetime.now()

                        # Add test log
                        if 'Loguri' in self.servers.columns:
                            current_logs = self.servers.at[server_idx, 'Loguri']
                            test_log = f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Test performanță completat - Scor: {overall_score:.1f}/100"
                            self.servers.at[server_idx, 'Loguri'] = current_logs + test_log

                        # Save and refresh
                        self.save_data()
                        if self.current_selected == self.current_selected:
                            self.show_server_details(self.current_selected)
                        self.draw_tab_topology(self.current_tab)

                        # Alert
                        self.add_alert(f"📊 TEST PERFORMANȚĂ: {self.current_selected} - Scor: {overall_score:.1f}/100 ({rating.split()[1]})", "info")

                        update_results_display(f"⏰ Timp finalizare: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        update_results_display("✅ Test completat cu succes!")

                        status_var.set("Test completat cu succes!")

                    test_running.set(False)
                    start_button.config(state='normal')
                    start_button.config(text="🔄 Rulează Test Din Nou")

                except Exception as e:
                    print(f"❌ Eroare în testul de performanță: {e}")
                    update_results_display(f"❌ EROARE: {str(e)}")
                    status_var.set("Test întrerupt din cauza unei erori")
                    test_running.set(False)
                    start_button.config(state='normal')

            def start_test():
                """Începe testul de performanță în thread separat"""
                test_thread = threading.Thread(target=run_test_sequence, daemon=True)
                test_thread.start()

            def cancel_test():
                """Anulează testul în desfășurare"""
                if test_running.get():
                    test_running.set(False)
                    status_var.set("Test anulat de utilizator")
                    progress_var.set(0)
                    start_button.config(state='normal')
                    update_results_display("\n❌ Test anulat de utilizator")
                else:
                    test_win.destroy()

            # Buttons
            start_button = tk.Button(controls_frame, text="🚀 Începe Test Performanță",
                                   command=start_test,
                                   font=('Segoe UI', 12, 'bold'), bg='#27ae60', fg='white',
                                   relief='flat', padx=20, pady=8)
            start_button.pack(side=tk.LEFT, padx=(0, 10))

            tk.Button(controls_frame, text="❌ Închide", command=cancel_test,
                     font=('Segoe UI', 11), bg='#e74c3c', fg='white',
                     relief='flat', padx=20, pady=8).pack(side=tk.RIGHT)

            # Info initial
            update_results_display("📊 Test de Performanță - Gata pentru început")
            update_results_display(f"🖥️ Server: {server.get('Nume')} ({self.current_selected})")
            update_results_display(f"🌐 IP: {server.get('IP')}")
            update_results_display(f"📍 Locație: {server.get('Locatie')}")
            update_results_display(f"⚡ Performanță actuală: {server.get('Performance_Score', 0):.1f}%")
            update_results_display("\n💡 Apăsați 'Începe Test Performanță' pentru a începe testarea.")

        except Exception as e:
            print(f"❌ Eroare la testul de performanță: {e}")
            messagebox.showerror("Eroare", f"Eroare la testul de performanță: {str(e)}")

    def refresh_status(self):
        """Refresh status pentru serverul selectat"""
        if not self.current_selected:
            messagebox.showwarning("Avertisment", "Selectați un server pentru refresh")
            return

        try:
            print(f"🔄 Refresh status pentru {self.current_selected}")
            server_idx = self.servers[self.servers['ID'] == self.current_selected].index[0]

            # Simulare verificare status
            old_status = self.servers.at[server_idx, 'Status']

            # 90% șansă să rămână online dacă era online
            if old_status == 'up':
                new_status = 'up' if random.random() < 0.9 else 'down'
            else:
                new_status = 'up' if random.random() < 0.3 else 'down'  # 30% șansă să revină online

            # Actualizare date
            self.servers.at[server_idx, 'Status'] = new_status
            self.servers.at[server_idx, 'UltimaVerificare'] = datetime.now()

            # Dacă serverul a revenit online, simulează metrici noi
            if new_status == 'up':
                self.servers.at[server_idx, 'CPU_Usage'] = random.uniform(10, 95)
                self.servers.at[server_idx, 'RAM_Usage'] = random.uniform(20, 90)
                if 'Disk_Usage' not in self.servers.columns:
                    self.servers['Disk_Usage'] = 0
                self.servers.at[server_idx, 'Disk_Usage'] = random.uniform(30, 95)
                self.servers.at[server_idx, 'Network_In'] = random.randint(100, 5000)
                self.servers.at[server_idx, 'Network_Out'] = random.randint(100, 5000)

                # Calculare performance score
                cpu = self.servers.at[server_idx, 'CPU_Usage']
                ram = self.servers.at[server_idx, 'RAM_Usage']
                disk = self.servers.at[server_idx, 'Disk_Usage']
                performance = 100 - ((cpu + ram + disk) / 3 * 0.5)  # Scor inversat
                self.servers.at[server_idx, 'Performance_Score'] = max(0, min(100, performance))
            else:
                # Server offline - resetează metrici
                for metric in ['CPU_Usage', 'RAM_Usage', 'Disk_Usage', 'Network_In', 'Network_Out', 'Performance_Score']:
                    if metric in self.servers.columns:
                        self.servers.at[server_idx, metric] = 0

            # Alertă dacă statusul s-a schimbat
            if new_status != old_status:
                server_name = self.servers.at[server_idx, 'Nume']
                if new_status == 'down':
                    alert_msg = f"🚨 ALERTĂ: {self.current_selected} ({server_name}) este OFFLINE!"
                    self.add_alert(alert_msg, "critical")
                else:
                    alert_msg = f"✅ RECUPERARE: {self.current_selected} ({server_name}) este ONLINE!"
                    self.add_alert(alert_msg, "info")

            # Salvare și actualizare
            self.save_data()
            self.show_server_details(self.current_selected)
            self.draw_tab_topology(self.current_tab)
            self.update_header_stats()

            print(f"✅ Status actualizat: {old_status} → {new_status}")

        except Exception as e:
            print(f"❌ Eroare la refresh status: {e}")
            messagebox.showerror("Eroare", f"Eroare la actualizarea statusului: {str(e)}")

    def restart_selected_server(self):
        """Restart serverul selectat"""
        if not self.current_selected:
            messagebox.showwarning("Avertisment", "Selectați un server pentru restart")
            return

        self.simulate_server_restart(self.current_selected)

    def simulate_server_restart(self, server_id):
        """Simulează restart-ul unui server"""
        try:
            server_idx = self.servers[self.servers['ID'] == server_id].index[0]
            server_name = self.servers.at[server_idx, 'Nume']

            # Confirmăre restart
            confirm = messagebox.askyesno(
                "Confirmare Restart",
                f"Sigur doriți să restartați serverul {server_id} ({server_name})?\n\nAcestă operațiune va întrerupe temporar serviciile.",
                icon='warning'
            )

            if not confirm:
                return

            print(f"🔄 Simulez restart pentru {server_id}")

            # Adaugă alertă restart
            self.add_alert(f"🔄 RESTART: {server_id} ({server_name}) - Restart inițiat", "warning")

            # Thread pentru simularea restart-ului
            def restart_process():
                # Faza 1: Server offline
                self.servers.at[server_idx, 'Status'] = 'down'
                self.servers.at[server_idx, 'UltimaVerificare'] = datetime.now()

                # Actualizare UI
                self.root.after(0, lambda: self.show_server_details(server_id))
                self.root.after(0, lambda: self.draw_tab_topology(self.current_tab))

                # Simulare timp restart (3-8 secunde)
                restart_time = random.uniform(3, 8)
                time.sleep(restart_time)

                # Faza 2: Server online cu metrici resetate
                self.servers.at[server_idx, 'Status'] = 'up'
                self.servers.at[server_idx, 'CPU_Usage'] = random.uniform(5, 30)  # CPU mai mic după restart
                self.servers.at[server_idx, 'RAM_Usage'] = random.uniform(15, 50)  # RAM mai mic după restart
                self.servers.at[server_idx, 'Network_In'] = random.randint(50, 1000)
                self.servers.at[server_idx, 'Network_Out'] = random.randint(50, 1000)
                if 'Uptime_Hours' in self.servers.columns:
                    self.servers.at[server_idx, 'Uptime_Hours'] = 0  # Reset uptime
                self.servers.at[server_idx, 'UltimaVerificare'] = datetime.now()

                # Recalculare performance score
                cpu = self.servers.at[server_idx, 'CPU_Usage']
                ram = self.servers.at[server_idx, 'RAM_Usage']
                if 'Disk_Usage' in self.servers.columns:
                    disk = self.servers.at[server_idx, 'Disk_Usage']
                else:
                    disk = random.uniform(30, 70)
                    self.servers.at[server_idx, 'Disk_Usage'] = disk

                performance = 100 - ((cpu + ram + disk) / 3 * 0.5)
                self.servers.at[server_idx, 'Performance_Score'] = max(70, min(100, performance))  # Minim 70% după restart

                # Update logs
                if 'Loguri' in self.servers.columns:
                    current_logs = self.servers.at[server_idx, 'Loguri']
                    restart_log = f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] System restart completed\nServices reloaded\nMemory cleared\nPerformance optimized"
                    self.servers.at[server_idx, 'Loguri'] = current_logs + restart_log

                # Salvare și actualizare UI
                self.root.after(0, self.save_data)
                self.root.after(0, lambda: self.show_server_details(server_id))
                self.root.after(0, lambda: self.draw_tab_topology(self.current_tab))
                self.root.after(0, self.update_header_stats)

                # Alertă finalizare
                self.root.after(0, lambda: self.add_alert(f"✅ RESTART COMPLET: {server_id} ({server_name}) - Online și optimizat", "success"))

                print(f"✅ Restart completat pentru {server_id}")

            # Start restart în thread separat
            restart_thread = threading.Thread(target=restart_process, daemon=True)
            restart_thread.start()

        except Exception as e:
            print(f"❌ Eroare la restart server: {e}")
            messagebox.showerror("Eroare", f"Eroare la restart server: {str(e)}")

    def edit_logs(self):
        """Editează logurile serverului selectat cu salvare în Excel"""
        if not self.current_selected:
            messagebox.showwarning("Avertisment", "Selectați un server pentru editarea logurilor")
            return

        try:
            server_idx = self.servers[self.servers['ID'] == self.current_selected].index[0]

            print(f"✏️ Editare loguri pentru {self.current_selected}")

            # Fereastră de editare loguri
            log_win = tk.Toplevel(self.root)
            log_win.title(f"📜 Editare Loguri - {self.current_selected}")
            log_win.geometry("700x500")
            log_win.configure(bg='#34495e')

            # Header
            header_frame = tk.Frame(log_win, bg='#2c3e50', height=60)
            header_frame.pack(fill=tk.X)
            header_frame.pack_propagate(False)

            tk.Label(header_frame, text=f"📜 Editare Loguri - {self.current_selected}",
                    font=('Segoe UI', 16, 'bold'), fg='#ecf0f1', bg='#2c3e50').pack(pady=20)

            # Text area pentru editare
            text_frame = tk.Frame(log_win, bg='#34495e')
            text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

            log_text = tk.Text(text_frame, wrap=tk.WORD, font=('Consolas', 10),
                              bg='#2c3e50', fg='#ecf0f1', insertbackground='#3498db',
                              selectbackground='#3498db')
            log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            log_scrollbar = ttk.Scrollbar(text_frame, command=log_text.yview,
                                        style='Custom.Vertical.TScrollbar')
            log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            log_text.config(yscrollcommand=log_scrollbar.set)

            # Încarcă logurile existente
            existing_logs = self.servers.at[server_idx, 'Loguri'] if 'Loguri' in self.servers.columns else "No logs available"
            log_text.insert(tk.END, existing_logs)

            # Buttons frame
            btn_frame = tk.Frame(log_win, bg='#34495e', height=60)
            btn_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=10)
            btn_frame.pack_propagate(False)

            def save_logs():
                try:
                    new_logs = log_text.get("1.0", tk.END).strip()

                    # Adaugă timestamp pentru modificare
                    timestamp_log = f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Loguri modificate manual"
                    final_logs = new_logs + timestamp_log

                    # Salvare în baza de date
                    if 'Loguri' not in self.servers.columns:
                        self.servers['Loguri'] = ""
                    self.servers.at[server_idx, 'Loguri'] = final_logs
                    self.servers.at[server_idx, 'UltimaVerificare'] = datetime.now()

                    # Salvare și actualizare
                    self.save_data()
                    self.show_server_details(self.current_selected)

                    # Alertă modificare
                    self.add_alert(f"📜 LOGURI MODIFICATE: {self.current_selected} - Loguri actualizate manual", "info")

                    log_win.destroy()
                    print(f"✅ Loguri salvate pentru {self.current_selected}")
                    messagebox.showinfo("Succes", f"Logurile pentru {self.current_selected} au fost actualizate în Excel!", parent=self.root)

                except Exception as e:
                    print(f"❌ Eroare la salvarea logurilor: {e}")
                    messagebox.showerror("Eroare", f"Eroare la salvarea logurilor: {str(e)}", parent=log_win)

            def add_timestamp():
                """Adaugă un timestamp nou în loguri"""
                current_pos = log_text.index(tk.INSERT)
                timestamp = f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                log_text.insert(current_pos, timestamp)

            def clear_logs():
                """Șterge toate logurile"""
                if messagebox.askyesno("Confirmare", "Sigur doriți să ștergeți toate logurile?", parent=log_win):
                    log_text.delete(1.0, tk.END)
                    log_text.insert(tk.END, f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Loguri șterse")

            # Buttons
            tk.Button(btn_frame, text="🕐 Adaugă Timestamp", command=add_timestamp,
                     font=('Segoe UI', 9), bg='#3498db', fg='white',
                     relief='flat', padx=10).pack(side=tk.LEFT, padx=(0, 5))

            tk.Button(btn_frame, text="🗑️ Clear Logs", command=clear_logs,
                     font=('Segoe UI', 9), bg='#e67e22', fg='white',
                     relief='flat', padx=10).pack(side=tk.LEFT, padx=5)

            tk.Button(btn_frame, text="💾 Salvează în Excel", command=save_logs,
                     font=('Segoe UI', 11, 'bold'), bg='#27ae60', fg='white',
                     relief='flat', padx=20, pady=5).pack(side=tk.RIGHT, padx=(10, 0))

            tk.Button(btn_frame, text="❌ Anulează", command=log_win.destroy,
                     font=('Segoe UI', 11), bg='#e74c3c', fg='white',
                     relief='flat', padx=20, pady=5).pack(side=tk.RIGHT, padx=(5, 10))

        except Exception as e:
            print(f"❌ Eroare la editarea logurilor: {e}")
            messagebox.showerror("Eroare", f"Eroare la editarea logurilor: {str(e)}")

    def refresh_logs(self):
        """Refresh logurile serverului selectat"""
        if not self.current_selected:
            messagebox.showwarning("Avertisment", "Selectați un server pentru refresh loguri")
            return

        try:
            print(f"🔄 Refresh loguri pentru {self.current_selected}")

            server_idx = self.servers[self.servers['ID'] == self.current_selected].index[0]

            # Generare loguri simulate
            log_entries = [
                "Service health check completed",
                "Memory usage optimized",
                "Network connectivity verified",
                "Security scan passed",
                "Backup integrity verified",
                "Performance metrics updated",
                "System temperature normal",
                "Database connection pool refreshed"
            ]

            # Adaugă log entries simulate
            if 'Loguri' in self.servers.columns:
                current_logs = self.servers.at[server_idx, 'Loguri']
            else:
                self.servers['Loguri'] = ""
                current_logs = ""

            new_log = f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {random.choice(log_entries)}"
            self.servers.at[server_idx, 'Loguri'] = current_logs + new_log
            self.servers.at[server_idx, 'UltimaVerificare'] = datetime.now()

            # Salvare și actualizare
            self.save_data()
            self.show_server_details(self.current_selected)

            print(f"✅ Loguri refresh pentru {self.current_selected}")

        except Exception as e:
            print(f"❌ Eroare la refresh loguri: {e}")
            messagebox.showerror("Eroare", f"Eroare la refresh loguri: {str(e)}")

    def clear_logs(self):
        """Șterge logurile serverului selectat"""
        if not self.current_selected:
            messagebox.showwarning("Avertisment", "Selectați un server pentru ștergerea logurilor")
            return

        try:
            confirm = messagebox.askyesno(
                "Confirmare",
                f"Sigur doriți să ștergeți toate logurile pentru {self.current_selected}?\n\nAceastă acțiune nu peut fi anulată.",
                icon='warning'
            )

            if not confirm:
                return

            print(f"🗑️ Șterg loguri pentru {self.current_selected}")

            server_idx = self.servers[self.servers['ID'] == self.current_selected].index[0]

            # Clear logs cu timestamp
            clear_log = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Loguri șterse - sistem resetat"

            if 'Loguri' not in self.servers.columns:
                self.servers['Loguri'] = ""
            self.servers.at[server_idx, 'Loguri'] = clear_log
            self.servers.at[server_idx, 'UltimaVerificare'] = datetime.now()

            # Salvare și actualizare
            self.save_data()
            self.show_server_details(self.current_selected)

            # Alertă
            self.add_alert(f"🗑️ LOGURI ȘTERSE: {self.current_selected} - Loguri resetate", "info")

            print(f"✅ Loguri șterse pentru {self.current_selected}")

        except Exception as e:
            print(f"❌ Eroare la ștergerea logurilor: {e}")
            messagebox.showerror("Eroare", f"Eroare la ștergerea logurilor: {str(e)}")

    def add_alert(self, message, alert_type="info"):
        """Adaugă o alertă în sistem"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")

            # Iconițe pentru tipuri de alerte
            icons = {
                "info": "ℹ️",
                "success": "✅",
                "warning": "⚠️",
                "critical": "🚨"
            }

            icon = icons.get(alert_type, "ℹ️")
            alert_text = f"[{timestamp}] {icon} {message}"

            # Adaugă la lista de alerte
            self.alerts.append({
                'timestamp': timestamp,
                'message': message,
                'type': alert_type,
                'full_text': alert_text
            })

            # Limitează la ultimele 50 de alerte
            if len(self.alerts) > 50:
                self.alerts = self.alerts[-50:]

            # Actualizare UI
            self.update_alerts_list()

            # Efecte vizuale pentru alerte critice
            if alert_type == "critical":
                try:
                    self.root.bell()  # Sunet sistem
                    # Flash effect
                    original_bg = self.root.cget('bg')
                    self.root.configure(bg='#e74c3c')
                    self.root.after(200, lambda: self.root.configure(bg=original_bg))
                except:
                    pass  # Ignore errors for visual effects

            print(f"🚨 Alertă {alert_type}: {message}")

        except Exception as e:
            print(f"❌ Eroare la adăugarea alertei: {e}")

    def update_alerts_list(self):
        """Actualizează lista de alerte"""
        try:
            self.alert_listbox.delete(0, tk.END)

            # Adaugă ultimele alerte (inversă pentru a avea cele mai noi sus)
            for alert in reversed(self.alerts[-20:]):  # Ultimele 20 alerte
                self.alert_listbox.insert(0, alert['full_text'])

                # Colorare în funcție de tip
                index = 0
                if alert['type'] == 'critical':
                    self.alert_listbox.itemconfig(index, {'fg': '#e74c3c', 'selectbackground': '#c0392b'})
                elif alert['type'] == 'warning':
                    self.alert_listbox.itemconfig(index, {'fg': '#f39c12', 'selectbackground': '#e67e22'})
                elif alert['type'] == 'success':
                    self.alert_listbox.itemconfig(index, {'fg': '#27ae60', 'selectbackground': '#229954'})
                else:
                    self.alert_listbox.itemconfig(index, {'fg': '#3498db', 'selectbackground': '#2980b9'})
        except Exception as e:
            print(f"❌ Eroare la actualizarea listei de alerte: {e}")

    def clear_alerts(self):
        """Șterge toate alertele"""
        try:
            confirm = messagebox.askyesno("Confirmare", "Sigur doriți să ștergeți toate alertele?")

            if confirm:
                print("🗑️ Șterg toate alertele")
                self.alerts = []
                self.update_alerts_list()

                # Adaugă alertă de confirmare
                self.add_alert("🗑️ Toate alertele au fost șterse", "info")
        except Exception as e:
            print(f"❌ Eroare la ștergerea alertelor: {e}")

    def delete_server(self):
        """Șterge serverul selectat"""
        if not self.current_selected:
            messagebox.showwarning("Avertisment", "Selectați un server pentru ștergere")
            return

        try:
            server = self.servers[self.servers['ID'] == self.current_selected].iloc[0]

            # Confirmare ștergere
            confirm = messagebox.askyesno(
                "Confirmare Ștergere",
                f"Sigur doriți să ștergeți serverul?\n\n"
                f"🆔 ID: {self.current_selected}\n"
                f"📛 Nume: {server.get('Nume', 'Unknown')}\n"
                f"🌐 IP: {server.get('IP', 'Unknown')}\n\n"
                f"⚠️ Această acțiune nu poate fi anulată!",
                icon='warning'
            )

            if not confirm:
                return

            print(f"🗑️ Șterg serverul {self.current_selected}")

            # Alertă ștergere
            self.add_alert(f"🗑️ SERVER ȘTERS: {self.current_selected} ({server.get('Nume', 'Unknown')}) - Eliminat din sistem", "warning")

            # Ștergere din DataFrame
            self.servers = self.servers[self.servers['ID'] != self.current_selected]

            # Salvare și actualizare
            self.save_data()
            self.current_selected = None
            self.clear_server_details()
            self.refresh_topology()

            print(f"✅ Server șters: {self.current_selected}")
            messagebox.showinfo("Succes", f"Serverul a fost șters cu succes!")

        except Exception as e:
            print(f"❌ Eroare la ștergerea serverului: {e}")
            messagebox.showerror("Eroare", f"Eroare la ștergerea serverului: {str(e)}")

    def refresh_topology(self):
        """Reîmprospătează topologia completă"""
        try:
            print("🔄 Reîmprospătare topologie completă...")

            # Reîncărcare date
            self.load_data()

            # Recreere tab-uri
            self.create_tabs()

            # Actualizare header
            self.update_header_stats()

            # Verifică dacă serverul selectat mai există
            if (self.current_selected and
                self.current_selected in self.servers['ID'].values):
                self.show_server_details(self.current_selected)
            else:
                self.current_selected = None
                self.clear_server_details()

            print("✅ Topologie actualizată")

        except Exception as e:
            print(f"❌ Eroare la actualizarea topologiei: {e}")
            messagebox.showerror("Eroare", f"Eroare la actualizarea topologiei: {str(e)}")

    def monitor_servers(self):
        """Monitor continuu pentru servere - rulează în background"""
        while True:
            try:
                print("🔍 Monitorizare servere în curs...")

                changes_made = False

                # Verificare fiecare server
                for idx, server in self.servers.iterrows():
                    status = server.get('Status', 'down')

                    if status == 'up':
                        # Simulare schimbări de metrici pentru servere online
                        if random.random() < 0.3:  # 30% șansă de schimbare
                            changes_made = True

                            # Verifică dacă coloanele există, dacă nu le creează
                            required_cols = ['CPU_Usage', 'RAM_Usage', 'Disk_Usage', 'Network_In', 'Network_Out', 'Performance_Score', 'Uptime_Hours']
                            for col in required_cols:
                                if col not in self.servers.columns:
                                    self.servers[col] = 0.0

                            # Schimbări graduale pentru realism
                            cpu_change = random.uniform(-5, 5)
                            ram_change = random.uniform(-3, 3)
                            disk_change = random.uniform(-1, 1)

                            current_cpu = server.get('CPU_Usage', 20)
                            current_ram = server.get('RAM_Usage', 30)
                            current_disk = server.get('Disk_Usage', 50)

                            new_cpu = max(5, min(98, current_cpu + cpu_change))
                            new_ram = max(10, min(95, current_ram + ram_change))
                            new_disk = max(20, min(99, current_disk + disk_change))

                            self.servers.at[idx, 'CPU_Usage'] = new_cpu
                            self.servers.at[idx, 'RAM_Usage'] = new_ram
                            self.servers.at[idx, 'Disk_Usage'] = new_disk

                            # Actualizare uptime
                            current_uptime = server.get('Uptime_Hours', 0)
                            self.servers.at[idx, 'Uptime_Hours'] = current_uptime + 0.167  # +10 minute

                            # Actualizare performance score
                            performance = 100 - ((new_cpu + new_ram + new_disk) / 3 * 0.5)
                            self.servers.at[idx, 'Performance_Score'] = max(0, min(100, performance))

                            # Network traffic simulation
                            self.servers.at[idx, 'Network_In'] = random.randint(100, 3000)
                            self.servers.at[idx, 'Network_Out'] = random.randint(100, 2500)

                            # Verificare threshold-uri pentru alerte
                            if new_cpu > 90:
                                alert_msg = f"🚨 CPU CRITIC: {server['ID']} ({server.get('Nume', 'Unknown')}) - CPU la {new_cpu:.1f}%"
                                self.root.after(0, lambda msg=alert_msg: self.add_alert(msg, "critical"))

                            if new_ram > 85:
                                alert_msg = f"⚠️ RAM RIDICAT: {server['ID']} ({server.get('Nume', 'Unknown')}) - RAM la {new_ram:.1f}%"
                                self.root.after(0, lambda msg=alert_msg: self.add_alert(msg, "warning"))

                            if new_disk > 90:
                                alert_msg = f"💾 DISK PLIN: {server['ID']} ({server.get('Nume', 'Unknown')}) - Disk la {new_disk:.1f}%"
                                self.root.after(0, lambda msg=alert_msg: self.add_alert(msg, "critical"))

                        # Mică șansă de cădere pentru servere online (1%)
                        if random.random() < 0.01:
                            changes_made = True
                            self.servers.at[idx, 'Status'] = 'down'

                            # Reset metrici
                            for metric in ['CPU_Usage', 'RAM_Usage', 'Network_In', 'Network_Out', 'Performance_Score']:
                                if metric in self.servers.columns:
                                    self.servers.at[idx, metric] = 0

                            alert_msg = f"🚨 SERVER DOWN: {server['ID']} ({server.get('Nume', 'Unknown')}) - A căzut neașteptat!"
                            self.root.after(0, lambda msg=alert_msg: self.add_alert(msg, "critical"))

                    else:  # Server offline
                        # Mică șansă de recuperare (5%)
                        if random.random() < 0.05:
                            changes_made = True
                            self.servers.at[idx, 'Status'] = 'up'

                            # Verifică și creează coloanele dacă nu există
                            required_cols = ['CPU_Usage', 'RAM_Usage', 'Disk_Usage', 'Network_In', 'Network_Out', 'Performance_Score', 'Uptime_Hours']
                            for col in required_cols:
                                if col not in self.servers.columns:
                                    self.servers[col] = 0.0

                            # Restore metrici
                            self.servers.at[idx, 'CPU_Usage'] = random.uniform(10, 40)
                            self.servers.at[idx, 'RAM_Usage'] = random.uniform(20, 60)
                            self.servers.at[idx, 'Network_In'] = random.randint(100, 1000)
                            self.servers.at[idx, 'Network_Out'] = random.randint(100, 800)
                            self.servers.at[idx, 'Performance_Score'] = random.uniform(70, 95)
                            self.servers.at[idx, 'Uptime_Hours'] = 0  # Reset uptime

                            alert_msg = f"✅ RECUPERARE: {server['ID']} ({server.get('Nume', 'Unknown')}) - Server revenit online!"
                            self.root.after(0, lambda msg=alert_msg: self.add_alert(msg, "success"))

                    # Actualizare timestamp verificare
                    self.servers.at[idx, 'UltimaVerificare'] = datetime.now()

                # Salvare și actualizare UI dacă au fost schimbări
                if changes_made:
                    self.root.after(0, lambda: self.save_data(silent=True))
                    self.root.after(0, self.update_header_stats)

                    # Actualizare detalii dacă un server este selectat
                    if (self.current_selected and
                        self.current_selected in self.servers['ID'].values):
                        self.root.after(0, lambda: self.show_server_details(self.current_selected))

                    # Redraw topologie pentru tab-ul curent
                    self.root.after(0, lambda: self.draw_tab_topology(self.current_tab))

                # Așteptare între verificări (15 secunde)
                time.sleep(15)

            except Exception as e:
                print(f"❌ Eroare în monitorizare: {str(e)}")
                time.sleep(30)  # Așteptare mai lungă în caz de eroare

if __name__ == "__main__":
    # Verificare dependințe
    try:
        import pandas as pd
        print("✅ Pandas disponibil")
    except ImportError:
        print("❌ Pandas nu este instalat!")
        print("Instalează cu: pip install pandas openpyxl")
        exit(1)

    # Start aplicație
    print("🚀 Inițializare Dashboard IT Professional...")

    root = tk.Tk()

    # Configurare pentru Windows (opțional)
    try:
        from tkinter import ttk
        root.tk.call('source', 'azure.tcl')
        root.tk.call('set_theme', 'dark')
    except:
        pass  # Continue cu tema default dacă nu e disponibilă

    # Start aplicație
    app = ServerDashboard(root)

    print("✅ Dashboard IT Professional gata!")
    print("🎯 Funcționalități disponibile:")
    print("   • ➕ Adăugare servere noi cu formular complet")
    print("   • ✏️ Editare proprietăți servere existente")
    print("   • 📊 Test performanță avansat cu rezultate detaliate")
    print("   • Layout vertical pentru topologie")
    print("   • Click dreapta pentru meniu contextual")
    print("   • Maxim 6 servere per tab")
    print("   • Editare și salvare în Excel")
    print("   • Monitorizare real-time")
    print("   • Sistem alerting avansat")
    print("   • Metrici de performanță")
    print("   • Design modern și intuitiv")
    print("   • Scroll îmbunătățit pentru panoul detalii")
    print("   • Compatibilitate cu Excel-uri existente")

    # Start main loop
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n👋 Dashboard închis de utilizator")
    except Exception as e:
        print(f"❌ Eroare fatală: {e}")
        messagebox.showerror("Eroare Fatală", f"Aplicația s-a închis din cauza unei erori:\n{str(e)}")

    print("👋 Dashboard IT Professional închis")