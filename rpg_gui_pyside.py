import sys
import traceback
import os
import math
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QDialog, QLineEdit, QRadioButton, QListWidget, QListWidgetItem,
    QMessageBox, QStackedWidget, QTextEdit, QDialogButtonBox, QSlider, QGroupBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QFontDatabase, QPainter, QPen, QColor, QPixmap

# Importa a lógica do jogo do ficheiro original
import rpg_dinamico

# --- ESTILOS GLOBAIS (QSS - Quase como CSS) ---
STYLESHEET = """
    QWidget {
        background-color: #2d2d2d;
        color: #ffffff;
        font-family: Helvetica;
        font-size: 12px;
    }
    QMainWindow, QDialog {
        background-color: #2d2d2d;
    }
    QLabel#TitleLabel {
        font-family: "Courier New", Courier, monospace;
        font-size: 32px;
        font-weight: bold;
        color: #ffff00;
        text-shadow: 2px 2px #ff0000;
        border: 2px solid #5a5a5a;
        padding: 5px;
        background-color: #1e1e1e;
        border-radius: 5px;
    }
    QLabel#HeroInfoLabel {
        color: #aaffaa;
        font-size: 14px;
        font-weight: bold;
    }
    QPushButton {
        background-color: #4a4a4a;
        border: 1px solid #5a5a5a;
        padding: 8px;
        border-radius: 4px;
    }
    QPushButton:hover {
        background-color: #5a5a5a;
    }
    QPushButton:pressed {
        background-color: #6a6a6a;
    }
    QPushButton:disabled {
        background-color: #3a3a3a;
        color: #888888;
    }
    QPushButton#DungeonButton {
        background-color: #006400; /* Verde escuro */
    }
    QPushButton#DungeonButton:hover {
        background-color: #007800;
    }
    QPushButton#ExitButton {
        background-color: #8B0000; /* Vermelho escuro */
    }
    QPushButton#ExitButton:hover {
        background-color: #A52A2A;
    }
    QLineEdit, QTextEdit, QListWidget {
        background-color: #1e1e1e;
        border: 1px solid #5a5a5a;
        border-radius: 4px;
        padding: 5px;
    }
    QGroupBox {
        font-weight: bold;
        border: 1px solid #5a5a5a;
        border-radius: 4px;
        margin-top: 10px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 5px;
    }
    /* Estilo para a carta de classe */
    ClassCardWidget {
        background-color: #3d3d3d;
        border: 2px solid #5a5a5a;
        border-radius: 10px;
    }
"""

# --- ADAPTAÇÕES DA LÓGICA DO JOGO PARA A GUI ---
def patch_rpg_dinamico_para_gui():
    def patched_nome_formatado(self):
        icone = "✨" if self.raridade == "raro" else "🔹" if self.raridade == "incomum" else ""
        return f"{self.nome} [{self.raridade.capitalize()}] {icone}".strip()
    rpg_dinamico.Item.nome_formatado = patched_nome_formatado

    def get_status_com_itens(self):
        lines = [
            f"--- STATUS: {self.nome} - O {self.classe.capitalize()} (Nível {self.nivel}) ---",
            f"❤️ Vida: {self.vida_atual:.1f} / {self.vida_maxima:.1f}",
            f"🔮 Caos: {self.caos_atual:.1f} / {self.caos_maximo:.1f}",
            f"📊 XP: {self.xp_atual:.0f} / {self.xp_proximo_nivel}" if self.nivel < rpg_dinamico.MAX_NIVEL else "📊 XP: MÁXIMO",
            "\n--- Atributos Totais ---",
            f"💪 Força: {self.forca:.1f} | 🛡️ Defesa: {self.defesa:.1f} | 👟 Agilidade: {self.agilidade:.1f}",
            f"💥 Chance Crítico: {self.chance_critico_total:.1%} | 💥 Dano Crítico: x{self.dano_critico_total:.2f}",
            "\n--- Equipamentos ---"
        ]
        for slot, item in self.equipamentos.items():
            if item:
                lines.append(f"   - {slot.capitalize()}: {item.nome_formatado()} {item.get_bonus_texto()}")
            else:
                lines.append(f"   - {slot.capitalize()}: Vazio")

        lines.append("\n--- Inventário de Poções ---")
        if self.inventario_pocoes:
            lines.extend([f"   - {str(pocao)}" for pocao in self.inventario_pocoes])
        else:
            lines.append("   Vazio")
        if self.buffs_ativos:
            lines.append("\n--- Buffs Ativos ---")
            buff_str = ", ".join([f"{data['valor']:.1f} {tipo.upper()} ({data['turnos_restantes']}t)" for tipo, data in self.buffs_ativos.items()])
            lines.append(f"   {buff_str}")
        return "\n".join(lines)
    rpg_dinamico.Heroi.get_status_texto = get_status_com_itens

# --- WIDGET DA CARTA DE CLASSE ---
class ClassCardWidget(QWidget):
    def __init__(self, class_name, class_data, image_path, parent=None):
        super().__init__(parent)
        self.class_name = class_name
        self.is_selected = False
        self.setFixedSize(240, 420) 

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        image_label = QLabel()
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            print(f"Aviso: Não foi possível carregar a imagem em {image_path}")
            image_label.setText("Imagem\nNão\nEncontrada")
            image_label.setStyleSheet("color: red; border: 1px dashed red;")
        
        image_label.setPixmap(pixmap.scaledToWidth(230, Qt.SmoothTransformation))
        image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(image_label)
        
        desc_label = QLabel(class_data['desc'])
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-style: italic; color: #cccccc;")
        layout.addWidget(desc_label)

        stats_group = QGroupBox("Atributos Base")
        stats_layout = QVBoxLayout()
        stats_data = class_data['stats']
        stats_layout.addWidget(QLabel(f"❤️ Vida: {stats_data['vida_base']}"))
        stats_layout.addWidget(QLabel(f"💪 Força: {stats_data['forca_base']}"))
        stats_layout.addWidget(QLabel(f"🛡️ Defesa: {stats_data['defesa_base']}"))
        stats_layout.addWidget(QLabel(f"👟 Agilidade: {stats_data['agilidade_base']}"))
        stats_layout.addWidget(QLabel(f"🔮 Caos: {stats_data['caos_base']}"))
        
        crit_chance = class_data.get('chance_critico_base', 0)
        crit_multi = class_data.get('multiplicador_critico_base', 1.5)
        stats_layout.addWidget(QLabel(f"💥 Chance Crítico: {crit_chance:.0%}"))
        stats_layout.addWidget(QLabel(f"💥 Dano Crítico: x{crit_multi:.2f}"))
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        layout.addStretch()

    def setSelected(self, selected):
        if self.is_selected != selected:
            self.is_selected = selected
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.is_selected:
            painter = QPainter(self)
            pen = QPen(QColor("#ffff00"), 4)
            painter.setPen(pen)
            painter.drawRoundedRect(2, 2, self.width() - 4, self.height() - 4, 8, 8)

# --- JANELAS E DIÁLOGOS DA APLICAÇÃO ---

class TelaBatalha(QDialog):
    def __init__(self, jogador, inimigo, parent=None):
        super().__init__(parent)
        self.jogador = jogador
        self.inimigo = inimigo
        self.parent = parent

        self.setWindowTitle(f"Batalha contra {self.inimigo.nome}")
        self.setMinimumSize(800, 600)
        self.setModal(True)

        self.layout = QVBoxLayout(self)
        self.stats_layout = QHBoxLayout()
        self.botoes_layout = QHBoxLayout()

        self.heroi_stats_label = QLabel()
        self.inimigo_stats_label = QLabel()
        self.log_batalha = QTextEdit()
        self.log_batalha.setReadOnly(True)

        self.heroi_stats_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.inimigo_stats_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        heroi_group = QGroupBox(f"Herói: {self.jogador.nome} ({self.jogador.classe})")
        heroi_layout = QVBoxLayout()
        heroi_layout.addWidget(self.heroi_stats_label)
        heroi_group.setLayout(heroi_layout)

        inimigo_group = QGroupBox(f"Inimigo: {self.inimigo.nome}")
        inimigo_layout = QVBoxLayout()
        inimigo_layout.addWidget(self.inimigo_stats_label)
        inimigo_group.setLayout(inimigo_layout)

        self.stats_layout.addWidget(heroi_group)
        self.stats_layout.addWidget(inimigo_group)

        self.layout.addLayout(self.stats_layout)
        self.layout.addWidget(self.log_batalha)
        self.layout.addLayout(self.botoes_layout)

        self.criar_botoes_acao()
        self.atualizar_status_batalha()
        self.log(f"⚔️ A batalha contra {self.inimigo.nome} começa!")

    def criar_botoes_acao(self):
        self.botoes = {}
        acoes = {
            "Atacar": self.acao_ataque,
            "Habilidades": self.acao_habilidade,
            "Poção": self.acao_pocao,
            "Status": self.acao_status,
            "Fugir": self.acao_fugir
        }
        for nome, func in acoes.items():
            btn = QPushButton(nome)
            btn.clicked.connect(func)
            self.botoes[nome] = btn
            self.botoes_layout.addWidget(btn)
        self.atualizar_botoes()

    def log(self, mensagem):
        self.log_batalha.append(mensagem)
        self.log_batalha.verticalScrollBar().setValue(self.log_batalha.verticalScrollBar().maximum())


    def atualizar_status_batalha(self):
        self.heroi_stats_label.setText(self.jogador.get_battle_stats_texto())
        self.inimigo_stats_label.setText(self.inimigo.get_battle_stats_texto())

    def atualizar_botoes(self, enable=True):
        self.botoes["Habilidades"].setEnabled(enable)
        self.botoes["Poção"].setEnabled(enable and bool(self.jogador.inventario_pocoes))
        self.botoes["Atacar"].setEnabled(enable)
        self.botoes["Fugir"].setEnabled(enable)
        self.botoes["Status"].setEnabled(enable)

    def turno_jogador(self, acao_func):
        self.atualizar_botoes(enable=False)
        acao_func()
        self.atualizar_status_batalha()
        if self.verificar_fim_batalha():
            return
        QTimer.singleShot(1200, self.turno_inimigo)

    def turno_inimigo(self):
        if self.inimigo.esta_vivo():
            self.log("-" * 20)
            self.inimigo.processar_debuffs()
            self.atualizar_status_batalha()
            if not self.inimigo.esta_vivo():
                self.verificar_fim_batalha()
                return

            self.inimigo.atacar(self.jogador, logger=self.log)
            self.jogador.processar_buffs()
            self.atualizar_status_batalha()
            if self.verificar_fim_batalha():
                return
            self.atualizar_botoes(enable=True)
            self.log("\nSua vez de agir!")
        else:
            self.atualizar_botoes(enable=True)

    def verificar_fim_batalha(self):
        if not self.inimigo.esta_vivo():
            self.log(f"🎉 Você venceu a batalha contra {self.inimigo.nome}!")
            self.atualizar_botoes(enable=False)
            QTimer.singleShot(1500, lambda: self.done(QDialog.DialogCode.Accepted))
            return True
        if not self.jogador.esta_vivo():
            self.log("❌ Você foi derrotado!")
            self.atualizar_botoes(enable=False)
            QTimer.singleShot(1500, lambda: self.done(QDialog.DialogCode.Rejected))
            return True
        return False

    def acao_ataque(self):
        self.turno_jogador(lambda: self.jogador.atacar(self.inimigo, logger=self.log))

    def acao_habilidade(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Escolher Habilidade")
        layout = QVBoxLayout(dialog)
        
        list_widget = QListWidget()
        habilidades = rpg_dinamico.CLASSES_BASE[self.jogador.classe]['habilidades']
        for i, hab in enumerate(habilidades):
            texto_item = f"{hab['nome']} (Custo: {hab['custo']}) - {hab['desc']}"
            item = QListWidgetItem(texto_item)
            item.setData(Qt.UserRole, i)
            if self.jogador.caos_atual < hab['custo']:
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            list_widget.addItem(item)
        layout.addWidget(list_widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec():
            selected_item = list_widget.currentItem()
            if selected_item:
                habilidade_index = selected_item.data(Qt.UserRole)
                self.turno_jogador(lambda: self.jogador.usar_habilidade(habilidade_index, self.inimigo))
    
    def acao_pocao(self):
        if not self.jogador.inventario_pocoes: return
        dialog = QDialog(self)
        dialog.setWindowTitle("Usar Poção")
        layout = QVBoxLayout(dialog)
        list_widget = QListWidget()
        for i, pocao in enumerate(self.jogador.inventario_pocoes):
            item = QListWidgetItem(str(pocao))
            item.setData(Qt.UserRole, i)
            list_widget.addItem(item)
        layout.addWidget(list_widget)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec():
            selected_item = list_widget.currentItem()
            if selected_item:
                pocao_index = selected_item.data(Qt.UserRole)
                self.turno_jogador(lambda: self.jogador.usar_pocao(pocao_index))
    
    def acao_status(self):
        QMessageBox.information(self, f"Status de {self.jogador.nome}", self.jogador.get_status_texto())

    def acao_fugir(self):
        chance = max(10, min(90, 50 + (self.jogador.agilidade - self.inimigo.agilidade)))
        self.log(f"Tentando fugir... (Chance: {chance:.1f}%)")
        if rpg_dinamico.random.randint(1, 100) <= chance:
            self.log("...Você conseguiu escapar!")
            QTimer.singleShot(1500, lambda: self.done(10)) # Código 10 para Fuga
        else:
            self.log("...A fuga falhou!")
            self.turno_jogador(lambda: self.log(""))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RPG de Masmorra Dinâmica - PySide6 Edition")
        self.setMinimumSize(800, 600)
        self.heroi_selecionado = None
        self.vidas_heroi = 3
        self.inimigo_atual = None
        self.andar_atual = 0
        self.total_andares = 0
        self.masmorra_ativa = False
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        self.tela_inicial = QWidget()
        self.criar_tela_inicial()
        self.stacked_widget.addWidget(self.tela_inicial)

    def criar_tela_inicial(self):
        layout = QVBoxLayout(self.tela_inicial)
        layout.setAlignment(Qt.AlignCenter)
        self.title_label = QLabel("RPG DE MASMORRA")
        self.title_label.setObjectName("TitleLabel")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.vidas_label = QLabel()
        self.vidas_label.setAlignment(Qt.AlignCenter)
        self.hero_info_label = QLabel("Nenhum herói ativo")
        self.hero_info_label.setObjectName("HeroInfoLabel")
        self.hero_info_label.setAlignment(Qt.AlignCenter)
        botoes_layout = QVBoxLayout()
        botoes_layout.setSpacing(10)
        self.btn_criar = QPushButton("Criar Novo Herói")
        self.btn_selecionar = QPushButton("Selecionar Herói")
        self.btn_masmorra = QPushButton("Entrar na Masmorra")
        self.btn_masmorra.setObjectName("DungeonButton")
        self.btn_sair = QPushButton("Sair do Jogo")
        self.btn_sair.setObjectName("ExitButton")
        self.btn_criar.clicked.connect(self.abrir_tela_criar_heroi)
        self.btn_selecionar.clicked.connect(self.abrir_tela_selecionar_heroi)
        self.btn_masmorra.clicked.connect(self.iniciar_masmorra)
        self.btn_sair.clicked.connect(self.close)
        botoes_layout.addWidget(self.btn_criar)
        botoes_layout.addWidget(self.btn_selecionar)
        botoes_layout.addWidget(self.btn_masmorra)
        botoes_layout.addWidget(self.btn_sair)
        layout.addWidget(self.title_label)
        layout.addSpacing(20)
        layout.addWidget(self.vidas_label)
        layout.addWidget(self.hero_info_label)
        layout.addSpacing(20)
        layout.addLayout(botoes_layout)
        self.atualizar_tela_inicial()

    def atualizar_tela_inicial(self):
        vidas_texto = "❤️ " * self.vidas_heroi if self.vidas_heroi > 0 else "☠️ GAME OVER"
        self.vidas_label.setText(f"Vidas restantes: {vidas_texto}")
        if self.heroi_selecionado:
            self.hero_info_label.setText(f"Herói Ativo: {self.heroi_selecionado.nome} - {self.heroi_selecionado.classe} (Nível {self.heroi_selecionado.nivel})")
            self.btn_masmorra.setEnabled(self.vidas_heroi > 0)
        else:
            self.hero_info_label.setText("Nenhum herói ativo")
            self.btn_masmorra.setEnabled(False)
        self.btn_selecionar.setEnabled(bool(rpg_dinamico.HEROIS_CRIADOS))
        if self.vidas_heroi <= 0:
            self.btn_criar.setEnabled(False)
            self.btn_selecionar.setEnabled(False)

    def abrir_tela_criar_heroi(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Criação de Herói")
        dialog.setMinimumWidth(800)
        layout = QVBoxLayout(dialog)

        nome_layout = QHBoxLayout()
        nome_layout.addWidget(QLabel("Nome do Herói:"))
        nome_entry = QLineEdit()
        nome_layout.addWidget(nome_entry)
        layout.addLayout(nome_layout)
        
        layout.addWidget(QLabel("Escolha sua Classe:"))

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)
        
        image_map = {
            "Feral": "FERAL.png",
            "Sombra": "SOMBRA.png",
            "Moldador de Essência": "MOLDADOR DE ESSENCIA.png"
        }
        
        card_widgets = []
        selected_card = {"widget": None}

        def create_card_click_handler(card):
            def handler():
                if selected_card["widget"]:
                    selected_card["widget"].setSelected(False)
                selected_card["widget"] = card
                card.setSelected(True)
            return handler

        for name, data in rpg_dinamico.CLASSES_BASE.items():
            image_path = image_map.get(name, "")
            card = ClassCardWidget(name, data, image_path)
            card.mousePressEvent = lambda event, c=card: create_card_click_handler(c)()
            cards_layout.addWidget(card)
            card_widgets.append(card)

        if card_widgets:
            create_card_click_handler(card_widgets[0])()

        layout.addLayout(cards_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec():
            nome = nome_entry.text().strip()
            if not nome:
                QMessageBox.critical(self, "Erro", "O nome do herói não pode ser vazio.")
                return
            if nome in rpg_dinamico.HEROIS_CRIADOS:
                QMessageBox.critical(self, "Erro", "Já existe um herói com esse nome.")
                return
            if not selected_card["widget"]:
                QMessageBox.critical(self, "Erro", "Nenhuma classe selecionada.")
                return
            
            classe_selecionada = selected_card["widget"].class_name
            stats_iniciais = rpg_dinamico.CLASSES_BASE[classe_selecionada]["stats"]
            novo_heroi = rpg_dinamico.Heroi(nome, classe_selecionada, **stats_iniciais)
            
            if self.abrir_tela_distribuir_pontos(novo_heroi, rpg_dinamico.PONTOS_DISTRIBUICAO_INICIAL, is_creation=True):
                rpg_dinamico.HEROIS_CRIADOS[nome] = novo_heroi
                self.heroi_selecionado = novo_heroi
                QMessageBox.information(self, "Sucesso", f"Herói {nome} criado com sucesso!")
                self.atualizar_tela_inicial()

    def abrir_tela_distribuir_pontos(self, heroi, pontos, is_creation=False):
        dialog = QDialog(self)
        dialog.setWindowTitle("Distribuir Pontos")
        layout = QVBoxLayout(dialog)
        pontos_restantes = {"value": pontos}
        pontos_label = QLabel(f"Pontos restantes: {pontos}")
        layout.addWidget(pontos_label)
        sliders = {}
        
        def update_label():
            gastos = sum(s.value() for s in sliders.values())
            pontos_restantes["value"] = pontos - gastos
            pontos_label.setText(f"Pontos restantes: {pontos_restantes['value']}")
            for s in sliders.values():
                s.setMaximum(s.value() + pontos_restantes["value"])

        for stat in ["forca_base", "defesa_base", "agilidade_base"]:
            layout.addWidget(QLabel(stat.replace('_base', '').capitalize()))
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, pontos)
            slider.valueChanged.connect(update_label)
            sliders[stat] = slider
            layout.addWidget(slider)
            
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec():
            if pontos_restantes["value"] < 0:
                QMessageBox.critical(self, "Erro", "Você gastou pontos demais!")
                return False
            
            pontos_gastos = {
                "forca_base": sliders["forca_base"].value(),
                "defesa_base": sliders["defesa_base"].value(),
                "agilidade_base": sliders["agilidade_base"].value()
            }

            heroi.forca_base += pontos_gastos["forca_base"]
            heroi.defesa_base += pontos_gastos["defesa_base"]
            heroi.agilidade_base += pontos_gastos["agilidade_base"]
            
            if not is_creation:
                heroi.pontos_distribuidos_por_nivel[heroi.nivel] = pontos_gastos

            heroi.vida_atual = heroi.vida_maxima
            heroi.caos_atual = heroi.caos_maximo
            return True
        return False

    def abrir_tela_selecionar_heroi(self):
        if not rpg_dinamico.HEROIS_CRIADOS:
            QMessageBox.information(self, "Aviso", "Nenhum herói criado ainda.")
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle("Selecionar Herói")
        dialog.setMinimumSize(700, 450)
        
        dialog_layout = QVBoxLayout(dialog)
        content_layout = QHBoxLayout()
        dialog_layout.addLayout(content_layout)

        list_widget = QListWidget()
        list_widget.setMaximumWidth(220)
        nomes_herois = list(rpg_dinamico.HEROIS_CRIADOS.keys())
        for nome in nomes_herois:
            heroi = rpg_dinamico.HEROIS_CRIADOS[nome]
            list_widget.addItem(f"{heroi.nome} - {heroi.classe} (Nível {heroi.nivel})")
        content_layout.addWidget(list_widget)

        stats_display = QTextEdit()
        stats_display.setReadOnly(True)
        content_layout.addWidget(stats_display)

        def update_stats_display():
            if list_widget.currentItem():
                index = list_widget.currentRow()
                nome_selecionado = nomes_herois[index]
                heroi = rpg_dinamico.HEROIS_CRIADOS[nome_selecionado]
                stats_display.setText(heroi.get_status_texto())
            else:
                stats_display.clear()

        list_widget.currentItemChanged.connect(update_stats_display)
        if list_widget.count() > 0:
            list_widget.setCurrentRow(0)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        dialog_layout.addWidget(buttons)

        if dialog.exec():
            if list_widget.currentItem():
                index = list_widget.currentRow()
                nome_selecionado = nomes_herois[index]
                self.heroi_selecionado = rpg_dinamico.HEROIS_CRIADOS[nome_selecionado]
                self.atualizar_tela_inicial()

    def iniciar_masmorra(self):
        if self.masmorra_ativa:
            QMessageBox.warning(self, "Aviso", "Você já está em uma masmorra.")
            return

        jogador = self.heroi_selecionado
        jogador.vida_atual = jogador.vida_maxima
        jogador.caos_atual = jogador.caos_maximo
        jogador.buffs_ativos = {}
        self.andar_atual = 1
        self.total_andares = 2 + jogador.nivel
        self.masmorra_ativa = True
        QMessageBox.information(self, "Masmorra", f"Você entra na masmorra. Ela tem {self.total_andares} andares.")
        self.proximo_andar()

    def proximo_andar(self):
        if not self.masmorra_ativa: return

        jogador = self.heroi_selecionado
        if self.andar_atual <= self.total_andares:
            self.inimigo_atual = rpg_dinamico.gerar_inimigo(jogador.nivel)
            QMessageBox.information(self, "Novo Andar", f"Andar {self.andar_atual}/{self.total_andares}\nUm {self.inimigo_atual.nome} apareceu!")
        else:
            self.inimigo_atual = rpg_dinamico.gerar_chefe(jogador.nivel)
            QMessageBox.information(self, "Chefe!", f"Você chegou ao andar final e encontra o chefe: {self.inimigo_atual.nome}!")
        
        batalha_dialog = TelaBatalha(jogador, self.inimigo_atual, self)
        resultado = batalha_dialog.exec()
        
        if resultado == QDialog.DialogCode.Accepted: # Vitória
            self.vitoria_batalha()
        elif resultado == QDialog.DialogCode.Rejected: # Derrota
            self.lidar_com_derrota()
        elif resultado == 10: # Fuga
            self.lidar_com_fuga()
    
    def vitoria_batalha(self):
        jogador = self.heroi_selecionado
        xp_ganho = self.inimigo_atual.nivel * 5 + rpg_dinamico.random.randint(1, 5)
        
        log_temp = []
        teve_level_up = jogador.ganhar_xp(xp_ganho, logger=log_temp.append)
        
        QMessageBox.information(self, "Vitória!", "\n".join(log_temp))
        
        if teve_level_up:
            QMessageBox.information(self, "Level Up!", f"{jogador.nome} alcançou o nível {jogador.nivel}!")
            self.abrir_tela_distribuir_pontos(jogador, rpg_dinamico.PONTOS_POR_NIVEL)
            
        if self.andar_atual > self.total_andares:
             QMessageBox.information(self, "Vitória na Masmorra!", "🏆 Você conquistou a masmorra! �")
             self.masmorra_ativa = False
             self.atualizar_tela_inicial()
             return
             
        self.mostrar_recompensa()
        self.andar_atual += 1
        self.proximo_andar()

    def lidar_com_derrota(self):
        self.vidas_heroi -= 1
        jogador = self.heroi_selecionado
        
        log_temp = []
        jogador.perder_xp(rpg_dinamico.PENALIDADE_XP_DERROTA, logger=log_temp.append)
        
        msg = f"Você foi derrotado!\nPerdeu uma vida e sofreu penalidades de XP.\n\n" + "\n".join(log_temp)
        QMessageBox.warning(self, "Fim da Jornada", msg)
        
        self.masmorra_ativa = False
        self.atualizar_tela_inicial()

        if self.vidas_heroi <= 0:
            QMessageBox.critical(self, "Game Over", "GAME OVER. Suas vidas acabaram. Obrigado por jogar!")
            self.close()

    def lidar_com_fuga(self):
        jogador = self.heroi_selecionado
        log_temp = []
        jogador.perder_xp(rpg_dinamico.PENALIDADE_XP_FUGA, logger=log_temp.append)
        
        msg = "Você fugiu da batalha e perdeu o progresso na masmorra.\nVocê sofreu uma pequena penalidade de XP.\n\n" + "\n".join(log_temp)
        QMessageBox.warning(self, "Fuga", msg)
        
        self.masmorra_ativa = False
        self.atualizar_tela_inicial()

    def mostrar_recompensa(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Recompensa da Batalha")
        dialog.setMinimumWidth(700)
        main_layout = QHBoxLayout(dialog)

        rewards_group = QGroupBox("Escolha sua recompensa:")
        rewards_layout = QVBoxLayout()
        recompensas = [rpg_dinamico.gerar_recompensa_aleatoria(self.heroi_selecionado) for _ in range(3)]
        for item in recompensas:
            btn = QPushButton(str(item))
            btn.clicked.connect(lambda checked=False, i=item, d=dialog: self.selecionar_recompensa(i, d))
            rewards_layout.addWidget(btn)
        btn_nenhum = QPushButton("Não quero nenhum item.")
        btn_nenhum.clicked.connect(dialog.accept)
        rewards_layout.addWidget(btn_nenhum)
        rewards_group.setLayout(rewards_layout)
        main_layout.addWidget(rewards_group)
        
        stats_group = QGroupBox("Seu Status Atual")
        stats_layout = QVBoxLayout()
        stats_label = QTextEdit()
        stats_label.setReadOnly(True)
        stats_label.setText(self.heroi_selecionado.get_status_texto())
        stats_layout.addWidget(stats_label)
        stats_group.setLayout(stats_layout)
        main_layout.addWidget(stats_group, 1)

        dialog.exec()

    def selecionar_recompensa(self, item, dialog):
        jogador = self.heroi_selecionado
        if isinstance(item, rpg_dinamico.Equipamento):
            msg_box = QMessageBox(QMessageBox.Question, "Equipar Item?", 
                                  f"Deseja equipar o novo item?\n\nNOVO: {item}\nATUAL: {jogador.equipamentos.get(item.slot) or 'Nada'}",
                                  QMessageBox.Yes | QMessageBox.No, self)
            if msg_box.exec() == QMessageBox.Yes:
                log_temp = []
                jogador.avaliar_e_equipar_item(item, logger=log_temp.append)
                QMessageBox.information(self, "Equipado", "\n".join(log_temp))
        elif isinstance(item, rpg_dinamico.Pocao):
            if len(jogador.inventario_pocoes) < rpg_dinamico.MAX_POCOES_INVENTARIO:
                jogador.inventario_pocoes.append(item)
                QMessageBox.information(self, "Poção", f"{item.nome_formatado()} adicionada ao inventário.")
            else:
                QMessageBox.warning(self, "Inventário cheio", "Seu inventário de poções está cheio!")
        dialog.accept()


if __name__ == "__main__":
    try:
        patch_rpg_dinamico_para_gui()
        app = QApplication(sys.argv)
        app.setStyleSheet(STYLESHEET)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        with open("error_log.txt", "w") as f:
            f.write(traceback.format_exc())
        print(f"Ocorreu um erro crítico. Detalhes salvos em 'error_log.txt'.\nErro: {e}")
