#!/usr/bin/env python3
"""
xml_updater_gui.py

Pequeña GUI para generar files.xml con CRC32 y enlaces basados en una carpeta.
Requiere Python 3.x (probado en 3.8+). Usa tkinter (viene con Python).
"""

import os
import zlib
import urllib.parse
import xml.etree.ElementTree as ET
from xml.dom import minidom
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ----- Config por defecto -----
DEFAULT_BASE_URL = "http://104.234.7.247/updater/"
DEFAULT_FILENAME = "files.xml"
# extensiones que inicialmente marcan restartRequired="true"
DEFAULT_RESTART_EXTS = {'.exe'}

# ----- Funciones auxiliares -----
def crc32_hex_of_file(path, block_size=65536):
    """Calcula CRC32 de un archivo, devuelve string de 8 hex en mayúsculas."""
    crc = 0
    with open(path, 'rb') as f:
        while True:
            data = f.read(block_size)
            if not data:
                break
            crc = zlib.crc32(data, crc)
    # zlib.crc32 returns signed on some platforms; mask to 32 bits
    crc = crc & 0xFFFFFFFF
    return f"{crc:08X}"

def quote_path_for_url(p):
    """Codifica nombre/ruta para URL, preservando '/' si existe."""
    return urllib.parse.quote(p)

def prettify_xml(elem):
    """Devuelve string bonito UTF-8 de ElementTree Element."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="    ", encoding='utf-8')

# ----- Lógica de generación XML -----
def build_filelist_xml(entries, base_url):
    """
    entries: lista de dicts { 'name': <str relativ/path>, 'crc': <str>, 'restart': <bool> }
    base_url: URL base (terminar con / preferiblemente)
    Retorna bytes (utf-8) del XML.
    """
    root = ET.Element('filelist')
    for e in entries:
        file_attrib = {'name': e['name'], 'crc': e['crc']}
        if e.get('restart'):
            file_attrib['restartRequired'] = "true"
        file_elem = ET.SubElement(root, 'file', file_attrib)
        link_text = base_url.rstrip('/') + '/' + quote_path_for_url(e['name'])
        link_elem = ET.SubElement(file_elem, 'link')
        link_elem.text = link_text
    return prettify_xml(root)

# ----- GUI -----
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Generador files.xml (Updater)")
        self.geometry("900x600")
        self.minsize(700, 400)

        self.folder_path = tk.StringVar()
        self.base_url = tk.StringVar(value=DEFAULT_BASE_URL)
        self.output_name = tk.StringVar(value=DEFAULT_FILENAME)
        self.include_subdirs = tk.BooleanVar(value=False)

        # Frame superior -> controles
        ctrl = ttk.Frame(self, padding=8)
        ctrl.pack(fill='x')

        ttk.Label(ctrl, text="Carpeta:").grid(row=0, column=0, sticky='w')
        entry_folder = ttk.Entry(ctrl, textvariable=self.folder_path, width=60)
        entry_folder.grid(row=0, column=1, padx=6, sticky='w')
        ttk.Button(ctrl, text="Seleccionar...", command=self.select_folder).grid(row=0, column=2, padx=6)

        ttk.Checkbutton(ctrl, text="Incluir subcarpetas", variable=self.include_subdirs).grid(row=1, column=1, sticky='w', pady=(6,0))

        ttk.Label(ctrl, text="Base URL:").grid(row=2, column=0, sticky='w', pady=(10,0))
        ttk.Entry(ctrl, textvariable=self.base_url, width=60).grid(row=2, column=1, sticky='w', pady=(10,0))
        ttk.Label(ctrl, text="Nombre de salida:").grid(row=2, column=2, sticky='w', padx=(6,0))
        ttk.Entry(ctrl, textvariable=self.output_name, width=20).grid(row=2, column=3, sticky='w', pady=(10,0))

        ttk.Button(ctrl, text="Escanear carpeta", command=self.scan_folder).grid(row=0, column=3, padx=6)

        # Frame central -> Treeview con archivos
        mid = ttk.Frame(self, padding=8)
        mid.pack(fill='both', expand=True)

        columns = ("name", "crc", "restart")
        self.tree = ttk.Treeview(mid, columns=columns, show='headings', selectmode='browse')
        self.tree.heading('name', text='Nombre (relativo)')
        self.tree.column('name', width=420, anchor='w')
        self.tree.heading('crc', text='CRC32')
        self.tree.column('crc', width=120, anchor='center')
        self.tree.heading('restart', text='restartRequired')
        self.tree.column('restart', width=120, anchor='center')
        self.tree.pack(fill='both', expand=True, side='left')

        # Scrollbar
        sb = ttk.Scrollbar(mid, orient='vertical', command=self.tree.yview)
        sb.pack(side='left', fill='y')
        self.tree.configure(yscrollcommand=sb.set)

        # Bind doble click en columna restart para alternar
        self.tree.bind('<Double-1>', self.on_double_click)

        # Frame inferior -> botones
        bottom = ttk.Frame(self, padding=8)
        bottom.pack(fill='x')

        ttk.Button(bottom, text="Marcar todos restart", command=lambda: self.set_all_restart(True)).pack(side='left')
        ttk.Button(bottom, text="Desmarcar todos", command=lambda: self.set_all_restart(False)).pack(side='left', padx=(6,0))
        ttk.Button(bottom, text="Generar files.xml", command=self.generate_xml).pack(side='right')

        # status
        self.status_var = tk.StringVar(value="Listo")
        ttk.Label(self, textvariable=self.status_var, relief='sunken', anchor='w').pack(fill='x', side='bottom')

        # datos en memoria
        self.entries = []  # lista de dicts con name, fullpath, crc, restart

    def select_folder(self):
        d = filedialog.askdirectory()
        if d:
            self.folder_path.set(d)

    def scan_folder(self):
        folder = self.folder_path.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Selecciona una carpeta válida primero.")
            return

        self.status_var.set("Escaneando archivos...")
        self.update_idletasks()

        entries = []
        root_len = len(folder.rstrip(os.sep)) + 1
        if self.include_subdirs.get():
            for dirpath, _, filenames in os.walk(folder):
                for fn in filenames:
                    full = os.path.join(dirpath, fn)
                    rel = full[root_len:].replace(os.sep, '/')
                    entries.append((rel, full))
        else:
            for fn in os.listdir(folder):
                full = os.path.join(folder, fn)
                if os.path.isfile(full):
                    rel = fn  # solo nombre
                    entries.append((rel, full))

        # limpiar tree
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.entries = []

        # calcular CRCs (puede tardar dependiendo de la carpeta)
        for rel, full in sorted(entries, key=lambda x: x[0].lower()):
            try:
                crc = crc32_hex_of_file(full)
            except Exception as ex:
                crc = "ERROR"
            _, ext = os.path.splitext(rel)
            restart_flag = ext.lower() in DEFAULT_RESTART_EXTS
            entry = {'name': rel, 'fullpath': full, 'crc': crc, 'restart': restart_flag}
            self.entries.append(entry)
            self.tree.insert('', 'end', values=(entry['name'], entry['crc'], "true" if entry['restart'] else "false"))

        self.status_var.set(f"Escaneo completado: {len(self.entries)} archivos.")
        self.update_idletasks()

    def on_double_click(self, event):
        # Determinar fila y columna; si columna restart => alternar
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        col = self.tree.identify_column(event.x)  # e.g. '#3'
        item = self.tree.identify_row(event.y)
        if not item:
            return
        col_index = int(col.replace('#',''))
        if col_index == 3:  # restart column (name=1,crc=2,restart=3)
            vals = list(self.tree.item(item, 'values'))
            new = "false" if vals[2] == "true" else "true"
            self.tree.set(item, 'restart', new)
            # actualizar entries (encontrar por name)
            name = vals[0]
            for e in self.entries:
                if e['name'] == name:
                    e['restart'] = (new == "true")
                    break

    def set_all_restart(self, val: bool):
        for iid in self.tree.get_children():
            self.tree.set(iid, 'restart', "true" if val else "false")
        for e in self.entries:
            e['restart'] = val

    def generate_xml(self):
        if not self.entries:
            messagebox.showwarning("Atención", "Primero escanea una carpeta.")
            return
        base_url = self.base_url.get().strip()
        if not base_url:
            messagebox.showwarning("Atención", "Especifica la base URL.")
            return
        outfile = self.output_name.get().strip() or DEFAULT_FILENAME

        # Construir lista de entries serializables (name relativo, crc, restart)
        simple_entries = []
        for e in self.entries:
            if e['crc'] == "ERROR":
                # omitir o preguntar? aquí lo incluimos con crc vacío
                crc_val = ""
            else:
                crc_val = e['crc']
            simple_entries.append({'name': e['name'], 'crc': crc_val, 'restart': e['restart']})

        xml_bytes = build_filelist_xml(simple_entries, base_url)

        # Preguntar donde guardar
        folder = self.folder_path.get().strip()
        default_save = os.path.join(folder if folder else os.getcwd(), outfile)
        save_path = filedialog.asksaveasfilename(defaultextension=".xml",
                                                 initialfile=outfile,
                                                 initialdir=(folder if folder else None),
                                                 filetypes=[("XML files","*.xml"),("All files","*.*")])
        if not save_path:
            self.status_var.set("Guardado cancelado.")
            return
        try:
            with open(save_path, 'wb') as f:
                f.write(xml_bytes)
            messagebox.showinfo("Hecho", f"Archivo guardado:\n{save_path}")
            self.status_var.set(f"XML generado: {save_path}")
        except Exception as ex:
            messagebox.showerror("Error al guardar", str(ex))
            self.status_var.set("Error guardando XML.")

if __name__ == "__main__":
    app = App()
    app.mainloop()
