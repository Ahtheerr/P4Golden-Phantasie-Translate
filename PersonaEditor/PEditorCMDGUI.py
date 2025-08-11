import sys
import os
import subprocess
import xml.etree.ElementTree as ET
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
    QLineEdit, QGroupBox, QComboBox, QCheckBox, QLabel, QTextEdit, QListWidget,
    QSpinBox, QListWidgetItem, QFrame
)
from PyQt6.QtCore import QSettings, Qt

APP_NAME = "PersonaEditorGUI"
APP_AUTHOR = "SeuNomeOuEmpresa"

class PersonaEditorGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings(APP_AUTHOR, APP_NAME)
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        self.setWindowTitle("PersonaEditorCMD GUI")
        self.setGeometry(100, 100, 850, 850)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        main_layout.addLayout(self.create_exe_path_group())
        self.font_settings_group = self.create_font_settings_group()
        main_layout.addWidget(self.font_settings_group)
        main_layout.addWidget(self.create_file_selection_group())
        main_layout.addWidget(self.create_commands_group())
        main_layout.addWidget(self.create_output_group())
        
        self.execute_button = QPushButton("🚀 Executar Comando")
        self.execute_button.setStyleSheet("font-size: 14px; padding: 10px;")
        self.execute_button.clicked.connect(self.run_command)
        main_layout.addWidget(self.execute_button)

    # ==================================================================
    # Funções de criação dos widgets da UI
    # ==================================================================
    
    def build_argument_list(self):
        """Constrói a lista de argumentos respeitando a ordem correta."""
        args = []
        selected_command_text = self.command_combo.currentText()
        command = self.command_map.get(selected_command_text, "")

        # 1. Comando principal
        if command == "-exp":
            args.append(f"-exp{self.exp_type_combo.currentText()}")
        else:
            args.append(command)
        
        # --- ALTERAÇÃO PRINCIPAL AQUI: REORDENANDO OS ARGUMENTOS ---
        if self.sub_check.isChecked():
            args.append("/sub")
            
        if self.save_check.isChecked() and self.save_check.isVisible():
            args.append("-save")

        # 3. Outros modificadores gerais (/ovrw, /sub)
        #    /ovrw agora virá depois de -save, se ambos estiverem marcados.
        if self.ovrw_check.isChecked():
            args.append("/ovrw")
        

        # 4. Argumentos específicos do comando com parâmetros
        if command == "-imptext":
            if self.map_pattern_edit.text(): args.extend(["/map", self.map_pattern_edit.text()])
            if self.lbl_check.isChecked(): args.append("/lbl")
            if self.auto_check.isChecked(): args.extend(["/auto", str(self.auto_width_spin.value())])
            if self.skipempty_check.isChecked(): args.append("/skipempty")
            args.extend(["/enc", self.enc_combo.currentText()])
        if command == "-exptext":
            if self.rmvspl_check.isChecked(): args.append("/rmvspl")
        if command == "-expptp":
            if self.co2n_check.isChecked(): args.append("/co2n")
        if command == "-impimage":
            if self.size_check.isChecked(): args.extend(["/size", str(self.size_spin.value())])
        
        return args

    # O resto do código permanece o mesmo. Colei abaixo para garantir a integridade.
    
    def create_exe_path_group(self):
        layout = QHBoxLayout()
        label = QLabel("Caminho do PersonaEditorCMD.exe:")
        self.exe_path_edit = QLineEdit()
        self.exe_path_edit.setPlaceholderText("Selecione o local do executável...")
        self.exe_path_edit.editingFinished.connect(self.load_font_settings)
        browse_button = QPushButton("Procurar...")
        browse_button.clicked.connect(self.select_exe_path)
        layout.addWidget(label); layout.addWidget(self.exe_path_edit); layout.addWidget(browse_button)
        return layout

    def create_font_settings_group(self):
        group = QGroupBox("Configurações de Fonte (PersonaEditor.xml)")
        layout = QVBoxLayout()
        grid_layout = QHBoxLayout()
        font_selectors_layout = QVBoxLayout()
        old_font_layout = QHBoxLayout()
        old_font_layout.addWidget(QLabel("Fonte Original (OldFont):"))
        self.old_font_combo = QComboBox()
        old_font_layout.addWidget(self.old_font_combo)
        new_font_layout = QHBoxLayout()
        new_font_layout.addWidget(QLabel("Nova Fonte (NewFont):"))
        self.new_font_combo = QComboBox()
        new_font_layout.addWidget(self.new_font_combo)
        font_selectors_layout.addLayout(old_font_layout); font_selectors_layout.addLayout(new_font_layout)
        actions_layout = QVBoxLayout()
        self.save_fonts_button = QPushButton("Salvar Alterações no XML")
        self.save_fonts_button.clicked.connect(self.save_font_settings)
        self.font_status_label = QLabel("Defina o caminho do executável para carregar as fontes.")
        self.font_status_label.setStyleSheet("color: gray;")
        actions_layout.addWidget(self.save_fonts_button); actions_layout.addWidget(self.font_status_label)
        grid_layout.addLayout(font_selectors_layout, 2); grid_layout.addLayout(actions_layout, 1)
        layout.addLayout(grid_layout)
        group.setLayout(layout)
        group.setEnabled(False)
        return group
    
    def create_file_selection_group(self):
        group = QGroupBox("Arquivos de Entrada (Processamento em Lote)")
        layout = QVBoxLayout()
        self.file_list_widget = QListWidget()
        self.file_list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        button_layout = QHBoxLayout()
        select_files_button = QPushButton("Selecionar Arquivos..."); select_files_button.clicked.connect(self.select_files)
        select_folder_button = QPushButton("Selecionar Pasta..."); select_folder_button.clicked.connect(self.select_folder)
        clear_button = QPushButton("Limpar Seleção"); clear_button.clicked.connect(self.file_list_widget.clear)
        button_layout.addWidget(select_files_button); button_layout.addWidget(select_folder_button); button_layout.addWidget(clear_button)
        layout.addWidget(self.file_list_widget); layout.addLayout(button_layout)
        group.setLayout(layout)
        return group

    def create_commands_group(self):
        group = QGroupBox("Configuração do Comando")
        group.setToolTip(
            "Selecione a operação a ser realizada.\n"
            "-exptext e -imptext agora suportam arquivos BF, BMD e contêineres (BIN, PAC, etc.) diretamente."
        )
        main_layout = QVBoxLayout()
        cmd_layout = QHBoxLayout()
        cmd_label = QLabel("Comando Principal:")
        self.command_combo = QComboBox()
        self.command_map = {
            "Exportar Imagem (-expimage)": "-expimage", 
            "Importar Imagem (-impimage)": "-impimage", 
            "Exportar Tabela de Largura (-exptable)": "-exptable", 
            "Importar Tabela de Largura (-imptable)": "-imptable",
            "Exportar PTP (-expptp)": "-expptp", 
            "Importar PTP (-impptp)": "-impptp",
            "Exportar Texto (-exptext)": "-exptext",
            "Importar Texto (-imptext)": "-imptext",
            "Exportar Todos os Sub-arquivos (-expall)": "-expall", 
            "Importar Todos os Sub-arquivos (-impall)": "-impall",
            "Exportar por Tipo (-exp[Tipo])": "-exp"
        }
        self.command_combo.addItems(self.command_map.keys())
        self.command_combo.currentIndexChanged.connect(self.update_argument_visibility)
        self.exp_type_combo = QComboBox()
        self.exp_type_combo.addItems(["BIN", "SPR", "TMX", "BF", "PM1", "BMD", "FNT", "BVP", "HEX"])
        self.exp_type_combo.setVisible(False)
        cmd_layout.addWidget(cmd_label); cmd_layout.addWidget(self.command_combo, 1); cmd_layout.addWidget(self.exp_type_combo)
        main_layout.addLayout(cmd_layout)
        line1 = QFrame(); line1.setFrameShape(QFrame.Shape.HLine); line1.setFrameShadow(QFrame.Shadow.Sunken); main_layout.addWidget(line1)
        args_layout = QHBoxLayout()
        col1_layout = QVBoxLayout()
        col1_layout.addWidget(self.create_general_args_group())
        self.imptext_group = self.create_imptext_args_group()
        col1_layout.addWidget(self.imptext_group)
        self.exptext_group = self.create_exptext_args_group()
        col1_layout.addWidget(self.exptext_group)
        col1_layout.addStretch()
        col2_layout = QVBoxLayout()
        self.expptp_group = self.create_expptp_args_group()
        col2_layout.addWidget(self.expptp_group)
        self.impimage_group = self.create_impimage_args_group()
        col2_layout.addWidget(self.impimage_group)
        col2_layout.addStretch()
        args_layout.addLayout(col1_layout, 1); args_layout.addLayout(col2_layout, 1)
        main_layout.addLayout(args_layout)
        group.setLayout(main_layout)
        self.update_argument_visibility()
        return group

    def create_general_args_group(self):
        group = QGroupBox("Argumentos Gerais")
        layout = QVBoxLayout()
        self.sub_check = QCheckBox("/sub (Processar recursivamente)")
        self.ovrw_check = QCheckBox("/ovrw (Sobrescrever arquivo original)")
        self.save_check = QCheckBox("-save (Salvar alterações na importação)")
        self.save_check.setToolTip("Necessário para que os comandos de importação salvem o resultado.")
        layout.addWidget(self.sub_check)
        layout.addWidget(self.ovrw_check)
        layout.addWidget(self.save_check)
        group.setLayout(layout)
        return group

    def create_imptext_args_group(self):
        group = QGroupBox("Argumentos de Importação de Texto (-imptext)")
        group.setToolTip("Use com arquivos BF, BMD ou contêineres (com /sub).\nO programa encontrará e importará o texto para os PTPs internos.")
        layout = QVBoxLayout()
        self.imptext_single_file_check = QCheckBox("Usar um único arquivo de texto para importação")
        self.imptext_single_file_widget = QWidget()
        single_file_layout = QHBoxLayout(self.imptext_single_file_widget)
        single_file_layout.setContentsMargins(0, 5, 0, 0)
        self.imptext_single_file_edit = QLineEdit()
        self.imptext_single_file_edit.setPlaceholderText("Caminho para o arquivo .txt/.tsv...")
        browse_btn = QPushButton("Procurar...")
        browse_btn.clicked.connect(self.select_single_import_file)
        single_file_layout.addWidget(self.imptext_single_file_edit); single_file_layout.addWidget(browse_btn)
        layout.addWidget(self.imptext_single_file_check); layout.addWidget(self.imptext_single_file_widget)
        self.imptext_single_file_check.toggled.connect(self.imptext_single_file_widget.setVisible)
        self.imptext_single_file_widget.setVisible(False)
        layout.addWidget(QFrame(frameShape=QFrame.Shape.HLine, frameShadow=QFrame.Shadow.Sunken))
        map_layout = QHBoxLayout()
        self.map_pattern_edit = QLineEdit()
        map_layout.addWidget(QLabel("/map:")); map_layout.addWidget(self.map_pattern_edit)
        layout.addLayout(map_layout)
        self.lbl_check = QCheckBox("/lbl (Importar linha por linha)")
        layout.addWidget(self.lbl_check)
        auto_layout = QHBoxLayout()
        self.auto_check = QCheckBox("/auto (Hifenização automática)")
        self.auto_width_spin = QSpinBox()
        self.auto_width_spin.setRange(1, 9999); self.auto_width_spin.setEnabled(False)
        self.auto_check.toggled.connect(self.auto_width_spin.setEnabled)
        auto_layout.addWidget(self.auto_check); auto_layout.addWidget(self.auto_width_spin); auto_layout.addStretch()
        layout.addLayout(auto_layout)
        self.skipempty_check = QCheckBox("/skipempty (Pular textos vazios)")
        layout.addWidget(self.skipempty_check)
        enc_layout = QHBoxLayout()
        self.enc_combo = QComboBox()
        self.enc_combo.addItems(["UTF-8", "UTF-7", "UTF-16", "UTF-32"])
        enc_layout.addWidget(QLabel("/enc:")); enc_layout.addWidget(self.enc_combo); enc_layout.addStretch()
        layout.addLayout(enc_layout)
        group.setLayout(layout)
        return group

    def create_exptext_args_group(self):
        group = QGroupBox("Argumentos de Exportação de Texto (-exptext)")
        group.setToolTip("Use com arquivos BF, BMD ou contêineres (com /sub).\nO programa encontrará e exportará o texto dos PTPs internos.")
        layout = QVBoxLayout()
        self.rmvspl_check = QCheckBox('/rmvspl (Substituir "\\n" por espaço)')
        layout.addWidget(self.rmvspl_check)
        layout.addWidget(QFrame(frameShape=QFrame.Shape.HLine, frameShadow=QFrame.Shadow.Sunken))
        self.exptext_unify_check = QCheckBox("Unificar textos exportados em um único arquivo")
        self.exptext_unify_widget = QWidget()
        unify_layout = QHBoxLayout(self.exptext_unify_widget)
        unify_layout.setContentsMargins(0, 5, 0, 0)
        self.exptext_unify_path_edit = QLineEdit()
        self.exptext_unify_path_edit.setPlaceholderText("Caminho para o arquivo unificado...")
        save_as_btn = QPushButton("Salvar Como...")
        save_as_btn.clicked.connect(self.select_unify_output_file)
        unify_layout.addWidget(self.exptext_unify_path_edit); unify_layout.addWidget(save_as_btn)
        layout.addWidget(self.exptext_unify_check); layout.addWidget(self.exptext_unify_widget)
        self.exptext_unify_check.toggled.connect(self.exptext_unify_widget.setVisible)
        self.exptext_unify_widget.setVisible(False)
        group.setLayout(layout)
        return group
    
    def create_expptp_args_group(self):
        group = QGroupBox("Argumentos de Exportação de PTP (-expptp)")
        layout = QVBoxLayout()
        self.co2n_check = QCheckBox("/co2n (Copiar texto original para o novo)")
        layout.addWidget(self.co2n_check)
        group.setLayout(layout)
        return group
        
    def create_impimage_args_group(self):
        group = QGroupBox("Argumentos de Importação de Imagem (-impimage)")
        layout = QVBoxLayout()
        size_layout = QHBoxLayout()
        self.size_check = QCheckBox("/size (Definir novo tamanho da fonte)")
        self.size_spin = QSpinBox(); self.size_spin.setRange(1, 99999); self.size_spin.setValue(13842); self.size_spin.setEnabled(False)
        self.size_check.toggled.connect(self.size_spin.setEnabled)
        size_layout.addWidget(self.size_check); size_layout.addWidget(self.size_spin); size_layout.addStretch()
        layout.addLayout(size_layout)
        group.setLayout(layout)
        return group

    def create_output_group(self):
        group = QGroupBox("Saída do Comando")
        layout = QVBoxLayout()
        self.output_console = QTextEdit()
        self.output_console.setReadOnly(True)
        self.output_console.setFontFamily("Courier New")
        layout.addWidget(self.output_console)
        group.setLayout(layout)
        return group
    
    def log(self, message):
        self.output_console.append(message)
        QApplication.processEvents()

    def select_exe_path(self):
        path, _ = QFileDialog.getOpenFileName(self, "Selecione o PersonaEditorCMD.exe", "", "Executables (*.exe)")
        if path:
            self.exe_path_edit.setText(path); self.save_settings(); self.load_font_settings()

    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Selecione os Arquivos", "", "All Files (*)")
        if files:
            for file in files:
                self.file_list_widget.addItem(QListWidgetItem(file))

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Selecione a Pasta")
        if folder:
            self.log(f"Adicionando todos os arquivos da pasta: {folder}")
            for filename in os.listdir(folder):
                full_path = os.path.join(folder, filename)
                if os.path.isfile(full_path):
                    self.file_list_widget.addItem(QListWidgetItem(full_path))

    def update_argument_visibility(self):
        selected_command_text = self.command_combo.currentText()
        command = self.command_map.get(selected_command_text, "")
        import_commands = ['-impimage', '-imptable', '-impptp', '-imptext', '-impall']
        is_import = command in import_commands
        self.save_check.setVisible(is_import)
        self.exp_type_combo.setVisible(command == "-exp")
        self.imptext_group.setVisible(command == "-imptext")
        self.exptext_group.setVisible(command == "-exptext")
        self.expptp_group.setVisible(command == "-expptp")
        self.impimage_group.setVisible(command == "-impimage")

    def run_command(self):
        exe_path = self.exe_path_edit.text()
        if not exe_path or not os.path.exists(exe_path):
            self.log("ERRO: O caminho para o PersonaEditorCMD.exe não é válido ou não foi definido."); return
        if self.file_list_widget.count() == 0:
            self.log("ERRO: Nenhum arquivo de entrada selecionado."); return
        selected_command_text = self.command_combo.currentText()
        main_command = self.command_map.get(selected_command_text, "")
        if main_command == "-imptext" and self.imptext_single_file_check.isChecked():
            if not self.imptext_single_file_edit.text():
                self.log("ERRO: A opção de importar de arquivo único está habilitada, mas nenhum arquivo foi selecionado."); return
        if main_command == "-exptext" and self.exptext_unify_check.isChecked():
            if not self.exptext_unify_path_edit.text():
                self.log("ERRO: A opção de unificar arquivos está habilitada, mas nenhum arquivo de saída foi definido."); return
        self.output_console.clear()
        self.execute_button.setEnabled(False)
        self.log("--- INICIANDO PROCESSO ---")
        base_command_args = self.build_argument_list()
        processed_files = []
        for i in range(self.file_list_widget.count()):
            file_item = self.file_list_widget.item(i)
            full_file_path = file_item.text()
            processed_files.append(full_file_path)
            file_dir = os.path.dirname(full_file_path)
            file_name_only = os.path.basename(full_file_path)
            final_command = [exe_path, file_name_only]
            command_and_args = list(base_command_args)
            main_cmd = command_and_args.pop(0)
            final_command.append(main_cmd)
            if main_cmd == "-imptext" and self.imptext_single_file_check.isChecked():
                single_import_file = self.imptext_single_file_edit.text()
                final_command.append(single_import_file)
            final_command.extend(command_and_args)
            self.log(f"\n> Processando: {file_name_only}")
            self.log(f"  Diretório de Trabalho: {file_dir}")
            self.log(f"  Comando: {' '.join(f'\"{c}\"' if ' ' in c else c for c in final_command)}")
            try:
                startupinfo = None
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO(); startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                result = subprocess.run(final_command, cwd=file_dir, capture_output=True, text=True, encoding='utf-8', errors='replace', startupinfo=startupinfo)
                if result.stdout: self.log(f"  Saída:\n{result.stdout.strip()}")
                if result.stderr: self.log(f"  ERROS:\n{result.stderr.strip()}")
                if result.returncode == 0: self.log("  Status: Sucesso!")
                else: self.log(f"  Status: Falha com código de saída {result.returncode}")
            except Exception as e:
                self.log(f"ERRO CRÍTICO ao executar o processo: {e}"); break
        if main_command == "-exptext" and self.exptext_unify_check.isChecked():
            self.unify_exported_files(processed_files)
        self.log("\n--- PROCESSO CONCLUÍDO ---")
        self.execute_button.setEnabled(True)

    def unify_exported_files(self, processed_files):
        self.log("\n--- INICIANDO UNIFICAÇÃO DE ARQUIVOS DE TEXTO ---")
        target_file = self.exptext_unify_path_edit.text()
        source_extension = ".txt" 
        found_files = 0
        try:
            with open(target_file, 'w', encoding='utf-8') as outfile:
                for file_path in processed_files:
                    predicted_output_path = file_path + source_extension
                    if os.path.exists(predicted_output_path):
                        found_files += 1
                        self.log(f"  Adicionando: {os.path.basename(predicted_output_path)}")
                        outfile.write(f"--- START: {os.path.basename(predicted_output_path)} ---\n\n")
                        with open(predicted_output_path, 'r', encoding='utf-8', errors='replace') as infile:
                            outfile.write(infile.read())
                        outfile.write("\n\n")
                    else:
                        self.log(f"  AVISO: Arquivo exportado não encontrado: {os.path.basename(predicted_output_path)}")
            self.log(f"\nUnificação concluída. {found_files} arquivos foram juntados em '{os.path.basename(target_file)}'.")
        except Exception as e:
            self.log(f"\nERRO CRÍTICO durante a unificação: {e}")

    def select_single_import_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Selecione o arquivo de texto para importação", "", "Text Files (*.txt *.tsv);;All Files (*)")
        if path:
            self.imptext_single_file_edit.setText(path)

    def select_unify_output_file(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salvar arquivo unificado como...", "", "Text Files (*.txt);;Tab-Separated Values (*.tsv);;All Files (*)")
        if path:
            self.exptext_unify_path_edit.setText(path)

    def load_font_settings(self):
        font_group = self.font_settings_group
        exe_path = self.exe_path_edit.text()
        if not exe_path or not os.path.isdir(os.path.dirname(exe_path)):
            font_group.setEnabled(False); self.font_status_label.setText("Caminho do executável inválido."); self.font_status_label.setStyleSheet("color: red;"); return
        exe_dir = os.path.dirname(exe_path); font_dir = os.path.join(exe_dir, "font"); xml_path = os.path.join(exe_dir, "PersonaEditor.xml")
        self.old_font_combo.clear(); self.new_font_combo.clear()
        available_fonts = []
        if os.path.isdir(font_dir):
            for filename in os.listdir(font_dir):
                if filename.upper().endswith(".FNTMAP"):
                    available_fonts.append(os.path.splitext(filename)[0])
            if available_fonts:
                self.old_font_combo.addItems(available_fonts); self.new_font_combo.addItems(available_fonts)
            else:
                self.font_status_label.setText("Pasta 'font' encontrada, mas sem arquivos .FNTMAP."); self.font_status_label.setStyleSheet("color: orange;")
        else:
            self.font_status_label.setText("ERRO: Pasta 'font' não encontrada no diretório do executável."); self.font_status_label.setStyleSheet("color: red;"); font_group.setEnabled(False); return
        if os.path.isfile(xml_path):
            try:
                tree = ET.parse(xml_path); root = tree.getroot()
                old_font_node = root.find("OldFont"); new_font_node = root.find("NewFont")
                if old_font_node is not None and new_font_node is not None:
                    self.old_font_combo.setCurrentText(old_font_node.text); self.new_font_combo.setCurrentText(new_font_node.text)
                    self.font_status_label.setText("Configurações do XML carregadas com sucesso."); self.font_status_label.setStyleSheet("color: green;"); font_group.setEnabled(True)
                else:
                    self.font_status_label.setText("ERRO: Tags <OldFont>/<NewFont> não encontradas no XML."); self.font_status_label.setStyleSheet("color: red;"); font_group.setEnabled(False)
            except ET.ParseError:
                self.font_status_label.setText("ERRO: Falha ao ler o arquivo PersonaEditor.xml (malformado)."); self.font_status_label.setStyleSheet("color: red;"); font_group.setEnabled(False)
        else:
            self.font_status_label.setText("ERRO: Arquivo PersonaEditor.xml não encontrado."); self.font_status_label.setStyleSheet("color: red;"); font_group.setEnabled(False)

    def save_font_settings(self):
        exe_path = self.exe_path_edit.text(); exe_dir = os.path.dirname(exe_path); xml_path = os.path.join(exe_dir, "PersonaEditor.xml")
        if not os.path.isfile(xml_path):
            self.font_status_label.setText("ERRO: Não é possível salvar, PersonaEditor.xml não encontrado."); self.font_status_label.setStyleSheet("color: red;"); return
        try:
            tree = ET.parse(xml_path); root = tree.getroot()
            old_font_node = root.find("OldFont"); new_font_node = root.find("NewFont")
            if old_font_node is not None and new_font_node is not None:
                old_font_node.text = self.old_font_combo.currentText(); new_font_node.text = self.new_font_combo.currentText()
                tree.write(xml_path, encoding='utf-8', xml_declaration=True)
                self.font_status_label.setText("Alterações salvas com sucesso no XML!"); self.font_status_label.setStyleSheet("color: blue;")
            else:
                self.font_status_label.setText("ERRO: Tags não encontradas no XML para salvar."); self.font_status_label.setStyleSheet("color: red;")
        except Exception as e:
            self.font_status_label.setText(f"ERRO ao salvar o XML: {e}"); self.font_status_label.setStyleSheet("color: red;")

    def save_settings(self):
        self.settings.setValue("exe_path", self.exe_path_edit.text())

    def load_settings(self):
        exe_path = self.settings.value("exe_path", "")
        self.exe_path_edit.setText(exe_path)
        if exe_path:
            self.load_font_settings()

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = PersonaEditorGUI()
    window.show()
    sys.exit(app.exec())