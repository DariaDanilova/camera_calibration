import Settings
from PyQt5 import QtWidgets

class Setting(QtWidgets.QMainWindow):
    
    def __init__(self):
        # Это здесь нужно для доступа к переменным, методам
        super().__init__()
        self.ui = Settings.Ui_SettingsWindow()
        self.ui.setupUi(self) # Это нужно для инициализации нашего дизайна
        
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
    import sys  # sys нужен для передачи argv в QApplication
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = Setting()  # Создаём объект класса Setting
    window.show()  # Показываем окно
    app.exec_()  # и запускаем приложение

if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    main()  # то запускаем функцию main()

