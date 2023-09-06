from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
import sys
import os
import platform

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.filelist_path = ""
        self.textbox = QTextEdit(self)
        self.title_label = QLabel("DeepDRP server", self)
        self.input_label = QLabel(">Fasta Input", self)
        self.select_file_label = QLabel("OR upload your input filelist:", self)
        self.filepath_label = QLabel("No file selected", self)
        self.example_button = QPushButton("Example", self)
        self.reset_button = QPushButton("Reset", self)
        self.submit_button = QPushButton("Submit", self)
        self.select_button = QPushButton("选择文件", self)

        self.file_selected_status = 0

        self.initUI()

    def initUI(self):
        self.setGeometry(300, 300, 860, 550)

        self.title_label.move(340, 15)
        self.title_label.setStyleSheet('font-size:25px')

        self.input_label.move(40, 35)
        self.input_label.setStyleSheet('font-size:18px')

        self.textbox.setGeometry(40, 65, 780, 320)

        self.select_file_label.move(45, 400)
        self.select_file_label.setStyleSheet('font-size:18px')

        self.select_button.move(280, 397) #####
        self.select_button.clicked.connect(self.select_file)

        self.filepath_label.resize(1000, 20)
        self.filepath_label.move(370, 400)
        self.filepath_label.setStyleSheet('font-size:18px')

        self.example_button.setGeometry(85, 450, 160, 60)
        self.example_button.setStyleSheet('font-size:18px')
        self.example_button.clicked.connect(self.example)

        self.reset_button.setGeometry(345, 450, 160, 60)
        self.reset_button.setStyleSheet('font-size:18px')
        self.reset_button.clicked.connect(self.reset)

        self.submit_button.setGeometry(605, 450, 160, 60)
        self.submit_button.setStyleSheet('font-size:18px')
        self.submit_button.clicked.connect(self.submit)

        self.setWindowTitle('DeepDRP')
        self.center()
        self.show()

    def center(self):
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def select_file(self):
        path = QFileDialog.getOpenFileName(self, "选择文件", "/", "All Files (*);;Text Files (*.txt)")[0]
        self.filepath_label.setText(path)
        self.filelist_path = path
        self.file_selected_status = 1

    def example(self):
        example_data = ">4RBXA\nATCYCRTGRCATRESLSGVCRISGRLYRLCCR"
        self.textbox.setPlainText(example_data)

    def reset(self):
        self.textbox.setPlainText("")
        self.filelist_path = ""
        self.filepath_label.setText("No file selected")
        self.file_selected_status = 0

    def submit(self):

        reply = QMessageBox.question(self, 'Message',
                                     "Are you sure to submit?", QMessageBox.StandardButton.Yes |
                                     QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

        if reply != QMessageBox.StandardButton.Yes:
            return

        if self.file_selected_status == 1:  # 选中文件
            cmd = "nohup python predict.py -i {} -o ./results > prediction.log 2>&1 &".format(self.filelist_path)
            os.system(cmd)
            QMessageBox.information(
                self,
                'Submit',
                'Submit Successfully\nResults saved in the results folder\nCheck the process in the predicton.log file',
                QMessageBox.StandardButton.Ok
            )

        elif self.file_selected_status == 0:  # 使用输入框
            input_fasta = self.textbox.toPlainText()

            if input_fasta == '':
                QMessageBox.warning(
                    self,
                    'Warning',
                    "No fasta submit",
                    QMessageBox.StandardButton.Ok)
                return

            input_list = input_fasta.split('\n')

            with open("./tmp/filelist_GUI", "w") as filelist:
                for i in range(len(input_list)):
                    if input_list[i].startswith('>'):
                        seq_id = input_list[i].replace('>', '')
                        with open("./tmp/{}.fasta".format(seq_id), "w") as f:
                            f.write(input_list[i] + '\n')
                            f.write(input_list[i + 1] + '\n')
                        filelist.write('./tmp/{}.fasta'.format(seq_id) + "\n")
	
	    
            if platform.system().lower()!= 'windows':
                cmd = "nohup python predict.py -i {} -o ./results > prediction.log 2>&1 &".format("./tmp/filelist_GUI")
             
            else:
                cmd = "pythonw predict.py -i {} -o ./results >prediction.log".format("./tmp/filelist_GUI")
             
            os.system(cmd)

            QMessageBox.information(
                self,
                'Submit',
                'Submit Successfully\nResults are saved in the results folder\nCheck the process in the predicton.log file',
                QMessageBox.StandardButton.Ok
            )


def main():
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
