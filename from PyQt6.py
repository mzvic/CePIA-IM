import sys
from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import Qt
import pyqtgraph as pg
import time
import pyvisa
import os

'''
# Open RM
rm = pyvisa.ResourceManager()

#call device connected
print("Connected VISA resources: ")
rm.list_resources()

'''

script_directory = os.path.dirname(os.path.abspath(__file__))
ui_folder = r"/HMI_RRL_3.ui"
ui_dir = script_directory + ui_folder


class Interfaz(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(Interfaz,self).__init__(parent)
        self.ui=uic.loadUi(ui_dir, self)

        # Set Window Title
        self.setWindowTitle("TEMPERATURE CONTROL - LAKESHORE MODEL 336")

        # Connection with GUI (.ui)
        self.ui.c_sp.clicked.connect(self.sp_connection)
        self.ui.c_dmm.clicked.connect(self.dmm_connection)
        self.ui.c_ls.clicked.connect(self.ls_connection)
        
        self.ui.volt_set.clicked.connect(self.voltage_set)


        #Valves definition
        self.V = 0


        
        #Se crea gráfica
        self.layout1=self.ui.verticalLayout_3
        self.PlotWidget1=pg.PlotWidget(name="Plot1", title=u'Temperature vs Time')
        
        self.PlotWidget1.setLabel('bottom', 'Time', 'minutes')
        self.PlotWidget1.setLabel('left', 'Temperature', '°C')
        self.PlotWidget1.setYRange(0,50)

        self.layout1.addWidget(self.PlotWidget1)
    
    # Auxiliar fuctions
    def query_command(self, device, command):
            query = device.query(command)
            print(query)

    def write_command(self, device, command):
          device.write(command)

    # Device Comunication
    def dmm_connection(self):
        if self.ui.c_dmm.isChecked():
            
            #rig_dmm = rm.open_resource('USB0::0x1AB1::0x0588::DM3R153200585::INSTR')
            #self.write_command(rig_dmm, "*RST") # Reset the instrument
            #time.sleep(1)
            #self.write_command(rig_dmm, ":FUNC:CURR:DC") # Set current DC function
            #self.write_command(rig_dmm, ":CURR:DC:RANG 1A") #Set 1A range
            #self.write_command(rig_dmm, ":MEAS AUTO") # Set automatic measurameter
            #time.sleep(1)

            #while True:
                #meas_dmm = self.query_command(rig_dmm, ":MEAS?")
                #self.ui.curr_m.setText(meas_dmm)
                #time.sleep(0.5)

            print("Digital MultiMeter Connected!")
        else:

            #rig_dmm.close()
            print("Digital MultiMeter Disconnected!")

    def sp_connection(self):
        if self.ui.c_sp.isChecked():

            #rig_sp  = rm.open_resource('USB0::0x1AB1::0x0E11::DP8C170700397::INSTR')
            print("Supply Power Connected!")
        else:

            #rig_sp.close()
            print("Supply Power Disconnected!")

    def ls_connection(self):
        if self.ui.c_ls.isChecked():

            #ls = rm.open_resource("COM5", baud_rate=57600, parity=constants.Parity.odd, data_bits=7)
            #self.write_command(ls, "*RST") # Reset the instrument
            #time.sleep(1)
            #self.write_command(ls, ":INP:CHAN 3") # Set current DC function
            #self.write_command(ls, ":INP:RANG 1") #Set 1A range
            #self.write_command(ls, ":UNIT:TEMP CEL") #Set 1A range
            #self.write_command(ls, ":TEMP:SCAL 0.01") #Set 1A range
            #time.sleep(1)
        
            #while True:
                #meas_ls = self.query_command(ls, ":MEAS:TEMP?")
                #self.ui.temp_m.setText(meas_ls)
                #time.sleep(0.5)

            print("LakeShore Model 336 Connected!")
        else:

            #ls.close()
            print("LakeShore Model 336 Disconnected!")


        # Principal fuctions
    def voltage_set(self):
        
        self.V = round(float(self.ui.volt_c.text()), 2)
        #self.write_command(rig_sp, "*RST")
        #time.sleep(1)
        #self.write_command(rig_sp, ":INST CH1")
        #self.write_command(rig_sp, ":VOLT:PROT 15")
        #self.write_command(rig_sp, f':VOLT {V}')
        #self.write_command(rig_sp, ":OUTP CH1 ON")
        #time.sleep(1)

        if self.V == 0:
            pass

        elif self.V > 15:
            time.sleep(0.5)
            self.ui.volt_c.setText("EXCEEDS MAX. VOLTAGE")

        elif self.V < 0:
            self.ui.volt_c.setText("NEGATIVE VOLT. ERROR")

        else:
            while self.V <= 15:
                #meas_sp = self.query_command(rig_sp, ":MEAS:VOLT:DC? CH1")
                #self.ui.volt_m.setText(str(meas_sp))
                time.sleep(1)
                print()
                time.sleep(1)




if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)
    window = Interfaz()
    window.show()
    sys.exit(app.exec())