import cv2
from datetime import datetime
from PyQt5 import QtGui, QtCore, QtWidgets

#import existing files
import Interface
from AppIMGc_ver3 import App #import base class
import DetermineValueBlur as dvb
import chessboard_map as ch_m

#inheriting from base class
class AppInterface(App):

    __iatObj = None    
    flag = False
    i = 1
    row = ''
    
    def __init__(self):
        super().__init__()
        self.ui = Interface.Ui_MainWindow()
        self.ui.setupUi(self)
                  
        # button click events
        self.ui.Pattern_Button.clicked.connect(self.pattern_onClicked)
        self.ui.Start_Button.clicked.connect(self.thread_onclicked)
        self.ui.Stop_Button.clicked.connect(self.stop_acq)       
        self.ui.Add_Button.clicked.connect(self.add) 
        self.ui.Edit_Button.clicked.connect(self.edit) 

    def onClicked(self):
        startTime = datetime.now()
        
        self.__iatObj = ImgAcq()
        self.row = self.ui.listWidget.currentItem().text().split('x')
        self.__iatObj.setImageW(int(self.row[0]))
        self.__iatObj.setImageH(int(self.row[1]))
        
        #from row 40 to 90 is not mine
        patternSize=(9,6)
        CM=ch_m.chess_map(self.__iatObj.getImageH(),self.__iatObj.getImageW(),40,patternSize)
        CF=ch_m.chessboardFinder(patternSize)
         
        while self.flag==False:          

            self.__iatObj.prepare()
            
            while (self.i < 100):  
                self.__iatObj.image=self.__iatObj.getImage() 
                #print(self.__iatObj.image.shape)
                work_image=self.__iatObj.image.copy()
                #focus analize
                self.__obj = dvb.DetermineValueBlur()                    
                analize_blur_of_image, chiselka = self.__obj.determineValueBlur(work_image) 
                #find chessboard
                
                #print(work_image.shape)
                found, corners=CF.findBoard(analize_blur_of_image)
                
                if(found):
                    #print(cv2.resize(analize_blur_of_image, (640, 480),interpolation = cv2.INTER_AREA).shape[1])                    
                    #analize_blur_of_image=cv2.resize(analize_blur_of_image, (640,480),interpolation = cv2.INTER_AREA) 
                    map1=CM.add_chessboard(corners)
                    
                    for a in range(0,map1.shape[0]):
                        for b in range (0,map1.shape[1]):
                            
                            if(map1[a,b,1]<255):
                                analize_blur_of_image[a,b,1]=map1[a,b,1]
                            else:
                                analize_blur_of_image[a,b,1]=255                            
                     
                self.__iatObj.image = analize_blur_of_image 
                
                if self.ui.checkBoxSaveImage.isChecked():  
                    cv2.imwrite('./ImgAcq/img/img'+str(self.__iatObj.num_images)+'.jpg', self.__iatObj.image)  
                 
                if self.ui.checkBoxImageOutput.isChecked():        
                              
                    image1 = QImage(self.__iatObj.image, self.__iatObj.image.shape[1], self.__iatObj.image.shape[0], 0, QImage.Format_RGB888)
                    #self.__iatObj.image.strides[0]
                    pixmap = QtGui.QPixmap.fromImage(image1)
                    image_resized = pixmap.scaled(640, 480, QtCore.Qt.KeepAspectRatio)
                    self.ui.frame.setPixmap(image_resized)  
                self.i += 1      

            self.i=1
            self.__iatObj.kill()
            endTime = datetime.now() 
            print("Execution time: ", endTime - startTime)
         
    def add(self):
        self.row = self.ui.listWidget.currentRow()
        self.msg, self.status = QtWidgets.QInputDialog.getText(self, "Add", "Add Image Size")
        
        if self.status and self.msg:
            self.ui.listWidget.insertItem(self.row, self.msg) 
            self.ui.listWidget.setCurrentItem(self.ui.listWidget.item(0))
    
    def edit(self):
        self.row = self.ui.listWidget.currentRow()
        self.item = self.ui.listWidget.item(self.row)
        
        if self.item is not None:
            self.msg, self.status = QtWidgets.QInputDialog.getText(self, "Edit", "Edit Image Size",
                                                                   QtWidgets.QLineEdit.Normal, self.item.text())
            if self.status and self.msg is not None:
                self.item.setText(self.msg)
    
def main():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = AppInterface()  # create an object of the AppInterface class 
    window.show()
    app.exec_()  # execute the app

if __name__ == '__main__':
    main()
