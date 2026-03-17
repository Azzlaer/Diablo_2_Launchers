import os, configparser, webbrowser
from PySide6.QtWidgets import (
    QWidget, QPushButton, QListWidget, QProgressBar, QLabel, QVBoxLayout,
    QGroupBox, QRadioButton, QHBoxLayout
)
from PySide6.QtGui import QPixmap, QPalette, QBrush, QColor
from PySide6.QtCore import Qt

RESOURCE_FOLDER = "launcher"


class Ui_MainWindow(object):

    def setupUi(self, MainWindow):

        # ================================
        # 📄 Cargar config.ini
        # ================================
        config = configparser.ConfigParser()
        config.read("config.ini")

        # Tamaño del launcher editable
        width  = int(config["LAUNCHER"].get("window_width", 520))
        height = int(config["LAUNCHER"].get("window_height", 700))

        MainWindow.setWindowTitle("Launcher XML Updater")
        MainWindow.resize(width, height)


        # ================================
        # 🎮 Parámetros para ejecutar el juego
        # ================================
        self.game_path   = config["UPDATE"].get("download_path","./")
        self.exe_name    = config["GAME"].get("exe_name","Game.exe")
        self.arg_default = config["GAME"].get("arg_default","-skiptobnet")
        self.arg_classic = config["GAME"].get("arg_classic","-w")
        self.arg_hd      = config["GAME"].get("arg_hd","-3dfx")


        # ================================
        # 🌄 Fondo gráfico
        # ================================
        def parseInt(v, default):
            try: return int(str(v).split(";")[0].strip())
            except: return default

        bg = config["BACKGROUND"]
        bg_file = bg.get("image","")
        bg_mode = bg.get("mode","cover").lower()
        bg_opacity = parseInt(bg.get("opacity",100),100)

        bg_path = os.path.join(RESOURCE_FOLDER, bg_file)

        if os.path.exists(bg_path):
            pix = QPixmap(bg_path)

            if bg_mode == "stretch": pix = pix.scaled(width,height,Qt.IgnoreAspectRatio)
            elif bg_mode == "cover": pix = pix.scaled(width,height,Qt.KeepAspectRatioByExpanding)
            elif bg_mode == "contain": pix = pix.scaled(width,height,Qt.KeepAspectRatio)
            elif bg_mode == "tile":
                pal = QPalette(); pal.setBrush(QPalette.Window,QBrush(pix)); MainWindow.setPalette(pal)

            if bg_mode!="tile":
                pal = QPalette()
                b = QBrush(pix)
                b.setColor(QColor(255,255,255,bg_opacity))
                pal.setBrush(QPalette.Window,b)
                MainWindow.setPalette(pal)


        # ================================
        # 📌 Base UI
        # ================================
        self.centralwidget = QWidget(MainWindow)
        MainWindow.setCentralWidget(self.centralwidget)
        self.layout = QVBoxLayout(self.centralwidget)


        # ================================
        # 🔥 Título principal
        # ================================
        self.lblTitulo = QLabel("Launcher XML Updater")
        self.lblTitulo.setAlignment(Qt.AlignCenter)
        self.lblTitulo.setStyleSheet("""
            font-size:22px;font-weight:bold;color:white;margin:8px;
        """)
        self.layout.addWidget(self.lblTitulo)


        # ================================
        # 📄 Consola / Logs
        # ================================
        self.listWidget = QListWidget()
        self.listWidget.setStyleSheet("""
            font-size:14px;background:rgba(0,0,0,0.58);
            color:white;border-radius:6px;padding:4px;
        """)
        self.layout.addWidget(self.listWidget)


        # ================================
        # 🔁 Progress Bar
        # ================================
        self.progressBar = QProgressBar()
        self.progressBar.setValue(0)
        self.progressBar.setStyleSheet("""
            QProgressBar{background:#222;height:26px;color:white;border-radius:6px;}
            QProgressBar::chunk{background:#0077ff;border-radius:6px;}
        """)
        self.layout.addWidget(self.progressBar)


        # ================================
        # 🔓 Botones Update Manual
        # ================================
        self.btnActualizar = QPushButton("Actualizar Archivos")
        self.btnActualizar.setStyleSheet(
            "background:#0066ff;color:white;font-size:16px;padding:10px;border-radius:6px;"
        )
        self.layout.addWidget(self.btnActualizar)

        self.btnCancelar = QPushButton("Cancelar")
        self.btnCancelar.setStyleSheet(
            "background:#bb0000;color:white;font-size:16px;padding:10px;border-radius:6px;"
        )
        self.layout.addWidget(self.btnCancelar)


        # ================================
        # 🎮 Modo de Video
        # ================================
        self.grpModo = QGroupBox("Modo de Video del Juego")
        self.grpModo.setStyleSheet("color:white;font-size:16px;")
        box = QHBoxLayout()

        self.rClassic = QRadioButton("Clásico (-w)")
        self.rHD      = QRadioButton("HD (-3dfx)")
        self.rClassic.setStyleSheet("color:white;font-size:14px;")
        self.rHD.setStyleSheet("color:white;font-size:14px;")

        box.addWidget(self.rClassic); box.addWidget(self.rHD)
        self.grpModo.setLayout(box)
        self.layout.addWidget(self.grpModo)


        # ================================
        # ⭐ Botón PLAY
        # ================================
        self.btnJugar = QPushButton("⭐ JUGAR ⭐")
        self.btnJugar.setStyleSheet("""
            QPushButton{
                background:#1fd51a;color:white;font-size:22px;
                font-weight:bold;padding:13px;border-radius:8px;
            }
            QPushButton:hover{background:#0a9c08;}
        """)
        self.layout.addWidget(self.btnJugar)


        # ================================
        # 🌐 WEB Panel Button
        # ================================
        self.btnWeb = QPushButton("🌐 Página Web Oficial")
        self.btnWeb.setStyleSheet("""
            QPushButton{
                background:#0c71d4;color:white;font-size:17px;
                border-radius:6px;padding:10px;
            }
            QPushButton:hover{background:#09559e;}
        """)
        self.layout.addWidget(self.btnWeb)


        # ================================
        # 🔗 Redes / Social Links
        # ================================
        self.grpLinks = QGroupBox("Comunidad & Redes")
        self.grpLinks.setStyleSheet("color:white;font-size:16px;")
        links = QHBoxLayout()

        for name,url in config["LINKS"].items():
            b = QPushButton(name.capitalize())
            b.setStyleSheet("background:#444;color:white;padding:7px;border-radius:6px;")
            b.clicked.connect(lambda _,link=url:webbrowser.open(link))
            links.addWidget(b)

        self.grpLinks.setLayout(links)
        self.layout.addWidget(self.grpLinks)
