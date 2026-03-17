import os
import binascii
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import xml.etree.ElementTree as ET


# ======================================================================================
# FUNCIÓN PARA CALCULAR CRC32
# ======================================================================================
def calcular_crc32(filepath):
    with open(filepath, "rb") as file:
        data = file.read()
        return format(binascii.crc32(data) & 0xFFFFFFFF, '08X')


# ======================================================================================
# ESCANEAR ARCHIVOS (con o sin subcarpetas)
# ======================================================================================
def obtener_archivos(carpeta_base, incluir_subcarpetas):
    archivos = []

    if incluir_subcarpetas:
        for root, _, files in os.walk(carpeta_base):
            for f in files:
                ruta_absoluta = os.path.join(root, f)
                ruta_relativa = os.path.relpath(ruta_absoluta, carpeta_base).replace("\\", "/")
                archivos.append((ruta_relativa, ruta_absoluta))
    else:
        for f in os.listdir(carpeta_base):
            ruta_absoluta = os.path.join(carpeta_base, f)
            if os.path.isfile(ruta_absoluta):
                archivos.append((f, ruta_absoluta))

    return archivos


# ======================================================================================
# CARGAR ARCHIVOS AL LISTADO
# ======================================================================================
def cargar_archivos():
    carpeta = filedialog.askdirectory()
    if not carpeta:
        return

    carpeta_seleccionada.set(carpeta)

    for row in lista_files.get_children():
        lista_files.delete(row)

    incluir_sub = incluir_subcarpetas.get()
    base_url = entry_url.get().rstrip("/") + "/"

    archivos = obtener_archivos(carpeta, incluir_sub)

    for ruta_rel, ruta_abs in archivos:
        crc = calcular_crc32(ruta_abs)
        lista_files.insert("", "end", values=(ruta_rel, crc, "false", base_url + ruta_rel))


# ======================================================================================
# GENERAR XML
# ======================================================================================
def generar_xml():
    if not carpeta_seleccionada.get():
        messagebox.showwarning("⚠️ Carpeta requerida", "Seleccione una carpeta primero.")
        return

    filelist = ET.Element("filelist")

    for item in lista_files.get_children():
        nombre = lista_files.item(item, "values")[0]
        crc = lista_files.item(item, "values")[1]
        restart = lista_files.item(item, "values")[2]
        link = lista_files.item(item, "values")[3]

        file_elem = ET.SubElement(filelist, "file", name=nombre, crc=crc)
        if restart.lower() == "true":
            file_elem.set("restartRequired", "true")

        link_elem = ET.SubElement(file_elem, "link")
        link_elem.text = link

    xml_path = os.path.join(carpeta_seleccionada.get(), "files.xml")
    tree = ET.ElementTree(filelist)
    tree.write(xml_path, encoding="UTF-8", xml_declaration=True)

    messagebox.showinfo("✅ XML Generado", f"Archivo creado:\n{xml_path}")


# ======================================================================================
# ELIMINAR ITEM
# ======================================================================================
def eliminar_item():
    seleccionado = lista_files.selection()
    if not seleccionado:
        messagebox.showwarning("⚠️ Nada seleccionado", "Debe seleccionar un archivo.")
        return

    for item in seleccionado:
        lista_files.delete(item)


# ======================================================================================
# ORDENAR COLUMNAS HACIENDO CLICK
# ======================================================================================
def ordenar_columna(tv, col, reverse):
    items = [(tv.set(k, col), k) for k in tv.get_children("")]
    items.sort(reverse=reverse)

    for index, (_, k) in enumerate(items):
        tv.move(k, "", index)

    tv.heading(col, command=lambda: ordenar_columna(tv, col, not reverse))


# ======================================================================================
# GUI
# ======================================================================================
root = tk.Tk()
root.title("🛠️ Generador de files.xml con subcarpetas")
root.geometry("950x550")
root.configure(bg="#1E1E1E")

style = ttk.Style()
style.theme_use("clam")

style.configure("Treeview",
                background="#FFFFFF",
                foreground="#000000",
                rowheight=25,
                fieldbackground="#FFFFFF")

style.configure("Treeview.Heading",
                background="#3A3A3A",
                foreground="white",
                font=("Segoe UI", 10, "bold"))

style.map("Treeview",
          background=[("selected", "#4A90E2")],
          foreground=[("selected", "white")])

carpeta_seleccionada = tk.StringVar()
entry_url_value = tk.StringVar(value="http://104.234.7.247/updater")
incluir_subcarpetas = tk.BooleanVar(value=False)


# ======================================================================================
# FRAME SUPERIOR
# ======================================================================================
frame_top = tk.Frame(root, bg="#1E1E1E")
frame_top.pack(fill="x", padx=10, pady=10)

tk.Label(frame_top, text="📁 Carpeta:", bg="#1E1E1E", fg="white", font=("Segoe UI", 10)).grid(row=0, column=0)
entry_carpeta = tk.Entry(frame_top, textvariable=carpeta_seleccionada, width=60, font=("Segoe UI", 10))
entry_carpeta.grid(row=0, column=1, padx=5)

tk.Checkbutton(frame_top, text="📂 Incluir subcarpetas", variable=incluir_subcarpetas,
               bg="#1E1E1E", fg="white", selectcolor="#1E1E1E",
               font=("Segoe UI", 10)).grid(row=0, column=3, padx=10)

tk.Button(frame_top, text="🔍 Buscar carpeta", command=cargar_archivos,
          bg="#4A90E2", fg="white", font=("Segoe UI", 10, "bold")).grid(row=0, column=2, padx=5)

tk.Label(frame_top, text="🌐 URL base:", bg="#1E1E1E", fg="white", font=("Segoe UI", 10)).grid(row=1, column=0, pady=5)
entry_url = tk.Entry(frame_top, textvariable=entry_url_value, width=60, font=("Segoe UI", 10))
entry_url.grid(row=1, column=1, padx=5)


# ======================================================================================
# TABLA
# ======================================================================================
columnas = ("Archivo", "CRC32", "Restart", "URL")
lista_files = ttk.Treeview(root, columns=columnas, show="headings")
lista_files.pack(fill="both", expand=True, padx=10, pady=10)

for col in columnas:
    lista_files.heading(col, text=col,
                        command=lambda _col=col: ordenar_columna(lista_files, _col, False))
    lista_files.column(col, width=180)


# ======================================================================================
# BOTONES
# ======================================================================================
frame_buttons = tk.Frame(root, bg="#1E1E1E")
frame_buttons.pack(pady=10)

tk.Button(frame_buttons, text="🗑️ Eliminar seleccionado", command=eliminar_item,
          bg="#D9534F", fg="white", font=("Segoe UI", 10, "bold"), width=25).grid(row=0, column=0, padx=10)

tk.Button(frame_buttons, text="📦 Generar files.xml", command=generar_xml,
          bg="#5CB85C", fg="white", font=("Segoe UI", 10, "bold"), width=25).grid(row=0, column=1, padx=10)

root.mainloop()
