import Settings
from PyQt5 import QtWidgets

class Setting(QtWidgets.QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.ui = Settings.Ui_SettingsWindow()
        self.ui.setupUi(self)
        
        self.ui.squareSize.textEdited.connect(self.get_square_size)
    
    def get_square_size(self):
        square_size = self.ui.squareSize.text()
        if square_size != '':
            square_size = int(square_size)
            print(square_size)
        else:
            pass #заглушка
            #print('-')
        return square_size
        
def main():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = Setting()
    window.show()
    app.exec_()

if __name__ == '__main__':
    main()
