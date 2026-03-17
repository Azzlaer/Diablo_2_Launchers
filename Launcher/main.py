import sys, os, subprocess, traceback, zlib
from datetime import datetime
from PySide6.QtWidgets import QApplication, QMainWindow, QListWidgetItem
from PySide6.QtCore import QThread, Signal

import downloader
from ui_launcher import Ui_MainWindow


# ======================================================
# LOG GENERAL
# ======================================================
def write_log(msg):
    with open("update_log.txt","a",encoding="utf-8") as f:
        f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}\n")


def registrar_error(contexto, error):
    with open("crash.log","a",encoding="utf-8") as f:
        f.write("\n==============================================\n")
        f.write(f"{datetime.now()}  -  {contexto}\n")
        f.write(traceback.format_exc())
    write_log(f"[CRASH] {contexto}: {error}")
    print("\n⚠ ERROR — revisar crash.log\n")


# ======================================================
# HILO DE DESCARGA MANUAL
# ======================================================
class Worker(QThread):

    progreso = Signal(int)
    archivo_actual = Signal(str)
    archivo_finalizado = Signal(str)

    def __init__(self):
        super().__init__()
        self.cancel_requested = False

    def cancelar(self):
        self.cancel_requested = True

    def run(self):
        try:
            write_log("=== Inicio descarga manual ===")

            xml = downloader.descargar_xml()
            archivos = downloader.leer_xml(xml)

            total = len(archivos)
            procesados = 0
            write_log(f"Archivos XML detectados: {total}")

            for nombre, url, crc in archivos:

                if self.cancel_requested:
                    self.archivo_finalizado.emit("⛔ Cancelado")
                    write_log("Cancelado por usuario")
                    return

                self.archivo_actual.emit(f"⬇ Descargando: {nombre}")

                for descargado,totalb,estado in downloader.descargar_archivo(nombre,url,crc):

                    if self.cancel_requested:
                        self.archivo_finalizado.emit(f"⛔ Cancelado en {nombre}")
                        return

                    if estado=="descargando" and totalb>0:
                        self.progreso.emit(int((descargado/totalb)*100))

                    elif estado=="ok":
                        procesados+=1
                        msg=f"✔ {nombre} ({procesados}/{total})"
                        self.archivo_finalizado.emit(msg)
                        write_log(msg)

                    elif estado=="error":
                        msg=f"❌ Error CRC → {nombre}"
                        self.archivo_finalizado.emit(msg)
                        write_log(msg)
                        break

            write_log("=== Descarga manual finalizada ===\n")

        except Exception as e:
            registrar_error("EXCEPCIÓN EN WORKER DESCARGA", e)



# ======================================================
# MAIN UI + AUTOUPDATE
# ======================================================
class Main(QMainWindow):

    def __init__(self):
        super().__init__()

        try:
            self.ui = Ui_MainWindow()
            self.ui.setupUi(self)

            # Worker conexiones
            self.worker = Worker()
            self.worker.progreso.connect(self.update_progress)
            self.worker.archivo_actual.connect(self.add_list)
            self.worker.archivo_finalizado.connect(self.add_list)

            # Botones UI
            self.ui.btnActualizar.clicked.connect(self.start_update)
            self.ui.btnCancelar.clicked.connect(self.cancelar)
            self.ui.btnJugar.clicked.connect(self.launch_game)
            self.ui.btnWeb.clicked.connect(self.open_web)


            # ============================
            # 🔥 AUTOUPDATE CONFIG LOGIC
            # ============================
            import configparser
            cfg = configparser.ConfigParser()
            cfg.read("config.ini")

            auto = cfg["AUTOUPDATE"].get("enable","false").lower()

            if auto == "true":
                self.add_list("🔍 Autoupdate ACTIVADO — Comprobando archivos...")
                self.ui.btnActualizar.hide()
                self.ui.btnCancelar.hide()
                self.auto_check_files()

            else:
                self.add_list("🟡 Autoupdate DESACTIVADO — Modo Manual")
                self.ui.btnActualizar.show()
                self.ui.btnCancelar.show()


        except Exception as e:
            registrar_error("ERROR AL INICIAR INTERFAZ", e)



    # ======================================================
    # AUTO-CHECK + CRC VALIDATION
    # ======================================================
    def auto_check_files(self):
        self.add_list("📡 Leyendo XML remoto...")

        try:
            xml = downloader.descargar_xml()
            archivos = downloader.leer_xml(xml)  # (name,url,crc)
        except Exception as e:
            self.add_list("❌ No se pudo descargar XML remoto")
            write_log("ERROR XML: "+str(e))
            return

        self.add_list(f"📄 {len(archivos)} archivos detectados")

        for nombre,url,crc in archivos:

            ruta = os.path.join(self.ui.game_path,nombre)

            # Archivo faltante → descargar
            if not os.path.exists(ruta):
                self.add_list(f"⬇ Faltante → {nombre}")
                downloader.descargar_archivo(nombre,url,crc)
                continue

            # Archivo existe → comparar CRC
            with open(ruta,"rb") as f:
                local_crc = zlib.crc32(f.read()) & 0xFFFFFFFF

            if local_crc != int(crc,16):
                self.add_list(f"⚠ CRC distinto → {nombre} (Actualizando)")
                downloader.descargar_archivo(nombre,url,crc)
            else:
                self.add_list(f"✔ {nombre} OK ✓")
                continue

        self.add_list("🟢 Comprobación automática finalizada")
        write_log("Autoupdate completo")


    # ======================================================
    # ACTUALIZACIÓN MANUAL
    # ======================================================
    def start_update(self):
        self.add_list("▶ Descarga manual iniciada\n")
        write_log("Descarga manual iniciada")
        self.worker.cancel_requested=False
        self.worker.start()

    def cancelar(self):
        self.worker.cancelar()
        self.add_list("⛔ Cancelando...")
        write_log("Cancelación solicitada")

    def update_progress(self,val):
        self.ui.progressBar.setValue(val)

    def add_list(self,txt):
        self.ui.listWidget.addItem(QListWidgetItem(txt))


    # ======================================================
    # EJECUTAR GAME.EXE COMO ADMIN + ARGUMENTOS
    # ======================================================
    def launch_game(self):
        try:
            exe = os.path.join(self.ui.game_path,self.ui.exe_name)

            if not os.path.exists(exe):
                self.add_list("❌ Game.exe no encontrado")
                return

            args = self.ui.arg_default

            if self.ui.rClassic.isChecked(): args+=f" {self.ui.arg_classic}"
            if self.ui.rHD.isChecked():      args+=f" {self.ui.arg_hd}"

            import ctypes
            ctypes.windll.shell32.ShellExecuteW(
                None,"runas",exe,args,os.path.dirname(exe),1
            )

            msg=f"🚀 Ejecutando como Admin → {exe} {args}"
            self.add_list(msg)
            write_log(msg)

        except Exception as e:
            registrar_error("ERROR EJECUTANDO GAME",e)
            self.add_list("❌ Falló ejecución")


    # ======================================================
    # WEBVIEW — Vista Web con persistencia
    # ======================================================
    def open_web(self):
        try:
            from PySide6.QtWebEngineWidgets import QWebEngineView
            from PySide6.QtCore import QUrl
        except:
            import webbrowser
            webbrowser.open("http://104.234.7.247/d2revenge/index.php")
            self.add_list("⚠ WebEngine faltante → Navegador externo usado")
            return

        self.webview = QWebEngineView()
        self.webview.setWindowTitle("Página Oficial Diablo II Revenge")
        self.webview.resize(1100,750)
        self.webview.load(QUrl("http://104.234.7.247/d2revenge/index.php"))
        self.webview.show()

        self.add_list("🌐 Web abierta correctamente")
        write_log("WEBVIEW abierto")


# ======================================================
# EJECUCIÓN SEGURA
# ======================================================
if __name__=="__main__":
    try:
        app = QApplication(sys.argv)
        win = Main()
        win.show()
        app.exec()
    except Exception as e:
        registrar_error("CRASH GENERAL",e)
