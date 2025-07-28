import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import threading
import time
import random

class ServerDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Dashboard de Monitorizare IT")
        self.root.geometry("1200x800")

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

        # Creare interfață
        self.create_widgets()

        # Start monitorizare în background
        self.monitor_thread = threading.Thread(target=self.monitor_servers, daemon=True)
        self.monitor_thread.start()

        print("Aplicația a fost inițializată cu succes")

    def initialize_database(self):
        """Creează fișierul Excel dacă nu există"""
        if not os.path.exists(self.excel_file):
            print(f"Fișierul {self.excel_file} nu există, se creează...")
            default_data = {
                'ID': ['SRV-001', 'SRV-002', 'SRV-003', 'SRV-004'],
                'Nume': ['Web Server', 'Database', 'File Server', 'Mail Server'],
                'IP': ['192.168.1.10', '192.168.1.20', '192.168.1.30', '192.168.1.40'],
                'Locatie': ['Rack A1', 'Rack A2', 'Rack B1', 'Rack B2'],
                'Status': ['up', 'up', 'down', 'up'],
                'UltimaVerificare': [datetime.now()] * 4,
                'Loguri': [
                    "System boot\nCPU normal\nRAM 45%",
                    "DB connections: 24\nQuery cache: 12MB",
                    "Connection timeout\nLast backup failed",
                    "Mail queue: 0\nSpam blocked: 3"
                ]
            }
            df = pd.DataFrame(default_data)
            df.to_excel(self.excel_file, index=False)
            print(f"Fișierul {self.excel_file} a fost creat cu date implicite")

    def load_data(self):
        """Încarcă datele din fișierul Excel"""
        try:
            print(f"Încărcare date din {self.excel_file}...")
            self.servers = pd.read_excel(self.excel_file)
            self.servers['UltimaVerificare'] = pd.to_datetime(self.servers['UltimaVerificare'])
            print("Date încărcate cu succes")

        except Exception as e:
            messagebox.showerror("Eroare", f"Eroare la încărcarea datelor: {str(e)}")
            print(f"Eroare la încărcarea datelor: {str(e)}")

    def save_data(self):
        """Salvează datele în fișierul Excel"""
        try:
            self.servers.to_excel(self.excel_file, index=False)
            print("Date salvate cu succes în fișierul Excel")
        except Exception as e:
            messagebox.showerror("Eroare", f"Eroare la salvarea datelor: {str(e)}")
            print(f"Eroare la salvarea datelor: {str(e)}")

    def create_widgets(self):
        # Meniu principal
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Meniu File
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Adăugare Server", command=self.add_server)
        file_menu.add_command(label="Ștergere Server", command=self.delete_server)
        file_menu.add_separator()
        file_menu.add_command(label="Salvare", command=self.save_data)
        file_menu.add_command(label="Ieșire", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Notebook pentru tab-uri
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Creare tab-uri inițiale
        self.create_tabs()

        # Panou dreapta - Informații și alerte
        right_frame = ttk.Frame(main_frame, width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self.create_info_panel(right_frame)
        self.create_alerts_panel(right_frame)

    def create_tabs(self):
        """Creează tab-urile necesare în funcție de numărul de servere"""
        # Șterge tab-urile existente
        for tab in self.tabs:
            self.notebook.forget(tab['frame'])
        self.tabs = []

        # Calculează numărul de tab-uri necesare
        num_servers = len(self.servers)
        num_tabs = (num_servers + self.max_servers_per_tab - 1) // self.max_servers_per_tab

        if num_tabs == 0:
            num_tabs = 1  # Cel puțin un tab chiar dacă nu sunt servere

        # Creează tab-urile
        for tab_idx in range(num_tabs):
            tab_frame = ttk.Frame(self.notebook)
            tab_name = f"Rețea {tab_idx + 1}"
            self.notebook.add(tab_frame, text=tab_name)

            # Determină serverele pentru acest tab
            start_idx = tab_idx * self.max_servers_per_tab
            end_idx = start_idx + self.max_servers_per_tab
            tab_servers = self.servers.iloc[start_idx:end_idx]

            # Generează layout pentru acest tab
            layout, connections = self.generate_topology_layout(tab_servers)

            # Salvare informații tab
            self.tabs.append({
                'frame': tab_frame,
                'servers': tab_servers,
                'layout': layout,
                'connections': connections,
                'canvas': None
            })

            # Creează canvas pentru topologie
            self.create_tab_topology(tab_idx)

        # Selectează primul tab
        if self.tabs:
            self.notebook.select(0)
            self.current_tab = 0

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def generate_topology_layout(self, servers):
        """Generează un layout pentru serverele date"""
        server_ids = servers['ID'].tolist()
        num_servers = len(server_ids)

        # Determină dimensiunile grid-ului
        if num_servers <= 2:
            rows, cols = 1, num_servers
        elif num_servers <= 4:
            rows, cols = 2, (num_servers + 1) // 2
        else:
            rows, cols = 2, 3

        # Creează layout-ul
        layout = []
        for i in range(rows):
            row = []
            for j in range(cols):
                idx = i * cols + j
                if idx < num_servers:
                    row.append(server_ids[idx])
                else:
                    row.append('')
            layout.append(row)

        # Creează conexiuni simple (doar pentru demo)
        connections = []
        for i in range(len(server_ids) - 1):
            connections.append((server_ids[i], server_ids[i + 1]))

        return layout, connections

    def create_tab_topology(self, tab_idx):
        """Creează panoul de topologie pentru un tab specific"""
        if tab_idx >= len(self.tabs):
            return

        tab = self.tabs[tab_idx]
        frame = tab['frame']

        # Frame pentru titlu și butoane
        title_frame = ttk.Frame(frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(title_frame, text="Topologie Rețea", font=('Helvetica', 14, 'bold')).pack(side=tk.LEFT)

        # Buton pentru reîmprospătare topologie
        ttk.Button(title_frame, text="Refresh", command=self.refresh_topology).pack(side=tk.RIGHT)

        # Canvas pentru desenarea topologiei
        canvas = tk.Canvas(frame, bg='white', borderwidth=0, highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)

        # Actualizează informațiile tab-ului
        tab['canvas'] = canvas

        # Desenare topologie
        self.draw_tab_topology(tab_idx)

        # Legare eveniment click
        canvas.bind("<Button-1>", self.on_server_click)

    def draw_tab_topology(self, tab_idx):
        """Desenează topologia pentru un tab specific"""
        if tab_idx >= len(self.tabs):
            return

        tab = self.tabs[tab_idx]
        canvas = tab['canvas']
        layout = tab['layout']
        connections = tab['connections']

        canvas.delete("all")
        self.server_icons = {}

        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()

        if canvas_width < 10 or canvas_height < 10:
            return

        # Calculare dimensiuni grid
        rows = len(layout)
        cols = max(len(row) for row in layout)

        cell_width = canvas_width / cols
        cell_height = canvas_height / rows

        # Desenare conexiuni
        for (src, dst) in connections:
            src_row, src_col = self.find_server_position(layout, src)
            dst_row, dst_col = self.find_server_position(layout, dst)

            if src_row is not None and dst_row is not None:
                x1 = (src_col + 0.5) * cell_width
                y1 = (src_row + 0.5) * cell_height
                x2 = (dst_col + 0.5) * cell_width
                y2 = (dst_row + 0.5) * cell_height

                canvas.create_line(x1, y1, x2, y2, fill="gray", width=2)

        # Desenare servere
        for row_idx, row in enumerate(layout):
            for col_idx, server_id in enumerate(row):
                if server_id:
                    server = self.servers[self.servers['ID'] == server_id]
                    if not server.empty:
                        server = server.iloc[0]
                        status = server['Status']

                        x = (col_idx + 0.5) * cell_width
                        y = (row_idx + 0.5) * cell_height
                        radius = min(cell_width, cell_height) * 0.3

                        # Culoare în funcție de status
                        color = "green" if status == "up" else "red"

                        # Desenare icon server
                        canvas.create_oval(
                            x - radius, y - radius,
                            x + radius, y + radius,
                            fill=color, outline="black", width=2,
                            tags=("server", server_id)
                        )

                        # Adăugare text
                        canvas.create_text(
                            x, y + radius + 15,
                            text=server['Nume'],
                            font=('Helvetica', 10),
                            tags=("server_text", server_id)
                        )

                        # Memorare poziție pentru click
                        self.server_icons[server_id] = (x, y, radius, tab_idx)
                    else:
                        print(f"Avertisment: Serverul {server_id} din topologie nu a fost găsit în baza de date")

    def find_server_position(self, layout, server_id):
        """Găsește poziția unui server în layout"""
        for row_idx, row in enumerate(layout):
            for col_idx, s_id in enumerate(row):
                if s_id == server_id:
                    return (row_idx, col_idx)
        return (None, None)

    def on_tab_changed(self, event):
        """Handle la schimbarea tab-ului"""
        selected = self.notebook.index(self.notebook.select())
        if 0 <= selected < len(self.tabs):
            self.current_tab = selected
            print(f"Tab schimbat la {selected}")

    def on_server_click(self, event):
        """Handle la click pe un server"""
        x, y = event.x, event.y
        canvas = self.tabs[self.current_tab]['canvas']

        for server_id, (sx, sy, radius, tab_idx) in self.server_icons.items():
            if tab_idx == self.current_tab and ((x - sx) ** 2 + (y - sy) ** 2) <= radius ** 2:
                print(f"Server selectat: {server_id}")
                self.show_server_details(server_id)
                self.current_selected = server_id
                return

        print("Click pe zonă fără server")
        self.current_selected = None
        self.clear_server_details()

    def create_info_panel(self, parent):
        # Frame pentru detalii server
        self.info_frame = ttk.LabelFrame(parent, text="Detalii Server", padding=10)
        self.info_frame.pack(fill=tk.X, pady=(0, 10))

        # Elemente vor fi populate dinamic
        self.server_details = {
            'nume': ttk.Label(self.info_frame, text="Nume: ", font=('Helvetica', 10)),
            'ip': ttk.Label(self.info_frame, text="IP: ", font=('Helvetica', 10)),
            'locatie': ttk.Label(self.info_frame, text="Locatie: ", font=('Helvetica', 10)),
            'status': ttk.Label(self.info_frame, text="Status: ", font=('Helvetica', 10)),
            'ultima_verificare': ttk.Label(self.info_frame, text="Ultima verificare: ", font=('Helvetica', 10))
        }

        for label in self.server_details.values():
            label.pack(anchor=tk.W, pady=2)

        # Frame pentru loguri
        log_frame = ttk.LabelFrame(self.info_frame, text="Loguri", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD, font=('Helvetica', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

        # Butoane
        btn_frame = ttk.Frame(self.info_frame)
        btn_frame.pack(pady=(10, 0))

        ttk.Button(btn_frame, text="Refresh Status", command=self.refresh_status).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Editare Loguri", command=self.edit_logs).pack(side=tk.RIGHT, padx=5)

    def create_alerts_panel(self, parent):
        # Frame pentru alerte
        alert_frame = ttk.LabelFrame(parent, text="Alert System", padding=10)
        alert_frame.pack(fill=tk.BOTH, expand=True)

        # Listă alerte
        self.alert_listbox = tk.Listbox(
            alert_frame,
            height=10,
            font=('Helvetica', 9),
            selectbackground="#ffcccc",
            selectmode=tk.SINGLE
        )
        self.alert_listbox.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(alert_frame, command=self.alert_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.alert_listbox.config(yscrollcommand=scrollbar.set)

        # Buton clear alerte
        ttk.Button(alert_frame, text="Clear Alerts", command=self.clear_alerts).pack(pady=(5, 0))

    def show_server_details(self, server_id):
        server = self.servers[self.servers['ID'] == server_id].iloc[0]

        print(f"Afisare detalii pentru serverul {server_id}")

        # Actualizare detalii
        self.server_details['nume'].config(text=f"Nume: {server['Nume']}")
        self.server_details['ip'].config(text=f"IP: {server['IP']}")
        self.server_details['locatie'].config(text=f"Locatie: {server['Locatie']}")

        status_text = f"Status: {'✅ UP' if server['Status'] == 'up' else '❌ DOWN'}"
        self.server_details['status'].config(text=status_text)

        self.server_details['ultima_verificare'].config(
            text=f"Ultima verificare: {server['UltimaVerificare'].strftime('%Y-%m-%d %H:%M:%S')}"
        )

        # Actualizare loguri
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, server['Loguri'])
        self.log_text.config(state=tk.DISABLED)

    def clear_server_details(self):
        print("Clear detalii server")
        for label in self.server_details.values():
            label.config(text=label.cget('text').split(':')[0] + ": ")

        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def refresh_status(self):
        if self.current_selected:
            print(f"Refresh status pentru serverul {self.current_selected}")
            server_idx = self.servers[self.servers['ID'] == self.current_selected].index[0]

            # Simulare verificare status
            new_status = random.choice(['up', 'down'])

            old_status = self.servers.at[server_idx, 'Status']
            self.servers.at[server_idx, 'Status'] = new_status
            self.servers.at[server_idx, 'UltimaVerificare'] = datetime.now()

            # Adăugare alertă dacă statusul s-a schimbat
            if new_status == 'down' and old_status != 'down':
                alert_msg = f"ALERTĂ: Server {self.current_selected} ({self.servers.at[server_idx, 'Nume']}) este DOWN!"
                self.add_alert(alert_msg)
                print(alert_msg)

            # Reafișare detalii și topologie
            self.show_server_details(self.current_selected)
            self.refresh_topology()
            self.save_data()
        else:
            print("Niciun server selectat pentru refresh")
            messagebox.showwarning("Avertisment", "Selectați un server pentru a actualiza statusul")

    def edit_logs(self):
        if self.current_selected:
            print(f"Editare loguri pentru serverul {self.current_selected}")
            server_idx = self.servers[self.servers['ID'] == self.current_selected].index[0]

            # Creează fereastra de editare
            edit_win = tk.Toplevel(self.root)
            edit_win.title(f"Editare Loguri - {self.current_selected}")

            # Text area pentru editare
            log_text = tk.Text(edit_win, width=50, height=15, wrap=tk.WORD)
            log_text.pack(padx=10, pady=10)
            log_text.insert(tk.END, self.servers.at[server_idx, 'Loguri'])

            # Butoane
            btn_frame = ttk.Frame(edit_win)
            btn_frame.pack(pady=5)

            def save_changes():
                new_logs = log_text.get("1.0", tk.END).strip()
                self.servers.at[server_idx, 'Loguri'] = new_logs
                self.show_server_details(self.current_selected)
                self.save_data()
                edit_win.destroy()
                print("Loguri actualizate")

            ttk.Button(btn_frame, text="Salvare", command=save_changes).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Anulare", command=edit_win.destroy).pack(side=tk.RIGHT, padx=5)
        else:
            print("Niciun server selectat pentru editare loguri")
            messagebox.showwarning("Avertisment", "Selectați un server pentru a edita logurile")

    def add_alert(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.alerts.append(f"[{timestamp}] {message}")
        self.update_alerts_list()

        # Alertă vizuală
        self.root.bell()

        # Dacă fereastra nu e activă, facem flash
        if not self.root.focus_displayof():
            self.root.attributes('-alpha', 0.8)
            self.root.after(200, lambda: self.root.attributes('-alpha', 1.0))

        print(f"Alertă adăugată: {message}")

    def update_alerts_list(self):
        self.alert_listbox.delete(0, tk.END)
        for alert in self.alerts[-20:]:  # Limita la ultimele 20 alerte
            self.alert_listbox.insert(tk.END, alert)

        # Colorare alerte recente
        for i, alert in enumerate(self.alerts[-20:]):
            if "DOWN" in alert:
                self.alert_listbox.itemconfig(i, {'fg': 'red'})
            else:
                self.alert_listbox.itemconfig(i, {'fg': 'black'})

    def clear_alerts(self):
        print("Ștergere alerte")
        self.alerts = []
        self.update_alerts_list()

    def add_server(self):
        print("Inițiere proces adăugare server nou")
        add_win = tk.Toplevel(self.root)
        add_win.title("Adăugare Server Nou")

        # Variabile pentru formular
        var_id = tk.StringVar()
        var_nume = tk.StringVar()
        var_ip = tk.StringVar()
        var_locatie = tk.StringVar()
        var_status = tk.StringVar(value="up")
        var_loguri = tk.StringVar(value="No logs yet")

        # Frame formular
        form_frame = ttk.Frame(add_win, padding=10)
        form_frame.pack()

        # Câmpuri formular
        ttk.Label(form_frame, text="ID Server:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form_frame, textvariable=var_id).grid(row=0, column=1, pady=2)

        ttk.Label(form_frame, text="Nume:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form_frame, textvariable=var_nume).grid(row=1, column=1, pady=2)

        ttk.Label(form_frame, text="IP:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form_frame, textvariable=var_ip).grid(row=2, column=1, pady=2)

        ttk.Label(form_frame, text="Locație:").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form_frame, textvariable=var_locatie).grid(row=3, column=1, pady=2)

        ttk.Label(form_frame, text="Status:").grid(row=4, column=0, sticky=tk.W, pady=2)
        ttk.Combobox(form_frame, textvariable=var_status, values=["up", "down"]).grid(row=4, column=1, pady=2)

        ttk.Label(form_frame, text="Loguri:").grid(row=5, column=0, sticky=tk.W, pady=2)
        ttk.Entry(form_frame, textvariable=var_loguri).grid(row=5, column=1, pady=2)

        # Butoane
        btn_frame = ttk.Frame(add_win)
        btn_frame.pack(pady=10)

        def save_server():
            new_server = {
                'ID': var_id.get(),
                'Nume': var_nume.get(),
                'IP': var_ip.get(),
                'Locatie': var_locatie.get(),
                'Status': var_status.get(),
                'UltimaVerificare': datetime.now(),
                'Loguri': var_loguri.get()
            }

            # Verificare ID unic
            if new_server['ID'] in self.servers['ID'].values:
                messagebox.showerror("Eroare", "ID-ul serverului există deja!")
                return

            # Adăugare server nou
            self.servers = pd.concat([self.servers, pd.DataFrame([new_server])], ignore_index=True)
            self.save_data()
            self.refresh_topology()
            add_win.destroy()

            # Selectează noul server
            self.current_selected = new_server['ID']
            self.show_server_details(self.current_selected)

            print(f"Server nou adăugat: {new_server['ID']}")
            messagebox.showinfo("Succes", "Serverul a fost adăugat cu succes!")

        ttk.Button(btn_frame, text="Salvare", command=save_server).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Anulare", command=add_win.destroy).pack(side=tk.RIGHT, padx=5)

    def delete_server(self):
        if self.current_selected:
            confirm = messagebox.askyesno(
                "Confirmare",
                f"Sigur doriți să ștergeți serverul {self.current_selected}?",
                parent=self.root
            )

            if confirm:
                print(f"Ștergere server {self.current_selected}")
                self.servers = self.servers[self.servers['ID'] != self.current_selected]
                self.save_data()
                self.current_selected = None
                self.clear_server_details()
                self.refresh_topology()
        else:
            print("Niciun server selectat pentru ștergere")
            messagebox.showwarning("Avertisment", "Selectați un server pentru a șterge")

    def refresh_topology(self):
        print("Reîmprospătare topologie...")
        self.load_data()
        self.create_tabs()

        if self.current_selected and self.current_selected in self.servers['ID'].values:
            self.show_server_details(self.current_selected)
        else:
            self.current_selected = None
            self.clear_server_details()

    def monitor_servers(self):
        """Thread pentru monitorizare continuă a serverelor"""
        while True:
            print("Monitorizare servere în curs...")

            # Verificare periodică a statusului (simulată)
            for _, server in self.servers.iterrows():
                # În practică, ați face un ping sau alt check aici
                if random.random() < 0.1:  # 10% șansă de schimbare status pentru demo
                    new_status = 'down' if server['Status'] == 'up' else 'up'
                    old_status = server['Status']

                    if new_status != old_status:
                        self.servers.at[server.name, 'Status'] = new_status
                        self.servers.at[server.name, 'UltimaVerificare'] = datetime.now()

                        if new_status == 'down':
                            alert_msg = f"ALERTĂ: Server {server['ID']} ({server['Nume']}) este DOWN!"
                            self.root.after(0, lambda: self.add_alert(alert_msg))
                            print(alert_msg)

            # Actualizare interfață
            self.root.after(0, self.update_ui)

            # Așteptare între verificări
            time.sleep(10)

    def update_ui(self):
        """Actualizează interfața utilizator"""
        if self.current_selected and self.current_selected in self.servers['ID'].values:
            self.show_server_details(self.current_selected)

        # Recreăm doar canvas-ul curent pentru performanță
        if self.tabs:
            self.draw_tab_topology(self.current_tab)

if __name__ == "__main__":
    import os
    root = tk.Tk()
    app = ServerDashboard(root)
    root.mainloop()