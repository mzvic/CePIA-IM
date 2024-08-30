

import sys
from PyQt6 import QtWidgets, uic, QtCore
from PyQt6.QtWidgets import QApplication, QMainWindow
import pyvisa
from pyvisa import constants
import os
import pyqtgraph as pg
from time import sleep
from datetime import datetime
import time
import threading
# Open RM
rm = pyvisa.ResourceManager()

#call device connected
#print("Connected VISA resources:")
print(rm.list_resources())

dateFormat = "%H:%M:%S"
hourFormat = "%H%M%S"
filesDateFormat = "%d%m%y"


script_directory = os.path.dirname(os.path.abspath(__file__))
ui_folder = r"/HMI_RRL_3.ui" if os.name == "posix" else r"\HMI_RRL_3.ui"
ui_dir = script_directory + ui_folder

data_dir = r"\\"

class QueryThread(QtCore.QThread):
    response_received = QtCore.pyqtSignal(str)  # Señal para emitir la respuesta

    def __init__(self, device, command, interval=500, parent=None):
        super().__init__(parent)
        self.device = device
        self.command = command
        self.interval = interval  # Intervalo de tiempo entre comandos
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            try:
    
                response = self.device.query(self.command)                
                self.response_received.emit(response)

            except Exception as e:
                print(f"Error querying device: {e}")
            self.msleep(self.interval)

    def stop(self):
        self.running = False
        self.wait()


class WriteDataThread(QtCore.QThread):
    sending_info = QtCore.pyqtSignal(str)
    def __init__(self, name_file, interface_inst,interval=500, parent=None):
        super().__init__(parent)
        self.name_file = name_file
        self.interval = interval
        self.running = False
        self. interface_inst = interface_inst
        self.dmm_data = ''
        self.sp_data = ''
        self.ls_data = ''

    def set_data(self, dmm, sp, ls):
        self.dmm_data = dmm
        self.sp_data = sp
        self.ls_data = ls


    def run(self):
        self.running = True
        script_directory = os.path.dirname(os.path.abspath(__file__))
        ui_dir = script_directory
        while self.running:
            with open(f"{ui_dir}\\{self.name_file}.csv", "a+") as files:

                    try:
                        self.ls_data = self.interface_inst.ls_data_resp()
                        self.sp_data = self.interface_inst.sp_data_resp()
                        self.dmm_data = self.interface_inst.dmm_data_resp()
                        self.set_data(self.dmm_data,self.sp_data,self.ls_data)
                        files.write(f"{self.dmm_data},{self.sp_data},{self.ls_data}\n")
                    except Exception as e:
                        print(f"Error al escribir datos: {e}")
                    sleep(self.interval / 1000)  # Convertir ms a s

    def stop(self):
            self.running = False
            self.wait()



class Interfaz(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(Interfaz,self).__init__(parent)
        self.ui=uic.loadUi(ui_dir, self)
        self.rig_dmm = None
        self.rig_sp = None
        self.ls = None
        self.ls_response = "N/A"
        self.sp_response = "N/A"
        self.dmm_response = "N/A"
        self.query_thread_dmm = None
        self.query_thread_sp = None
        self.query_thread_ls = None
        self.x = []
        self.y = []

        # Set Window Title
        self.setWindowTitle("TEMPERATURE CONTROL - LAKESHORE MODEL 336")

        # Connection with GUI (.ui)
        self.ui.c_sp.clicked.connect(self.sp_connection)
        self.ui.c_dmm.clicked.connect(self.dmm_connection)
        self.ui.c_ls.clicked.connect(self.ls_connection)

        self.ui.volt_set.clicked.connect(self.voltage_set)
        self.ui.prot_volt_set.clicked.connect(self.volt_prot_set)

        self.ui.save_file.clicked.connect(self.save_files)


        #Valves definition
        self.V = 0
        self.protec_volt = 0
        self.file = None


        #Se crea gráfica
        self.layout1=self.ui.verticalLayout_3
        self.PlotWidget1=pg.PlotWidget(name="Plot1", title=u'Temperature vs Time')

        self.PlotWidget1.setLabel('bottom', 'Time', 's')
        self.PlotWidget1.setLabel('left', 'Temperature', '°C')
        self.PlotWidget1.setYRange(0,50)

        self.layout1.addWidget(self.PlotWidget1)

    # Auxiliar fuctions
    def write_command(self, device, command):
          device.write(command)


    # Device Comunication
    def dmm_connection(self):
        if self.ui.c_dmm.isChecked():
            try:
                self.rig_dmm = rm.open_resource('USB0::0x1AB1::0x0588::DM3R153200585::INSTR')
                self.write_command(self.rig_dmm, "*RST") # Reset the instrument
                sleep(1)
                self.write_command(self.rig_dmm, ":FUNC:CURR:DC") # Set current DC function
                self.write_command(self.rig_dmm, ":CURR:DC:RANG 1A") #Set 1A range
                sleep(1)
                self.write_command(self.rig_dmm, ":MEAS AUTO") # Set automatic measurameter
                sleep(2)

                command = ":MEASure:CURRent:DC?"
                self.query_thread_dmm = QueryThread(self.rig_dmm, command, interval=500)
                self.query_thread_dmm.response_received.connect(self.response_dm)
                self.query_thread_dmm.start()
            except Exception as err:
                print(f'error {err}')


            print("Digital MultiMeter Connected!")

        else:
            self.rig_dmm = rm.open_resource('USB0::0x1AB1::0x0588::DM3R153200585::INSTR')
            self.write_command(self.rig_dmm, "*RST")
            self.rig_dmm.close()
            self.ui.curr_m.setText("N/M")
            if self.query_thread_dmm:
                self.query_thread_dmm.stop()
            print("Digital MultiMeter Disconnected!")

    def response_dm(self, response):
        if self.ui.c_dmm.isChecked():
            flt_response = (round(float(response), 2))
            self.dmm_response = str(flt_response)
            
            self.ui.curr_m.setText(self.dmm_response)
            sleep(0.5)

    def dmm_data_resp(self):
        return self.dmm_response

    def sp_connection(self):
        if self.ui.c_sp.isChecked():
            try:
                self.rig_sp = rm.open_resource('USB0::0x1AB1::0x0E11::DP8C170700397::INSTR')
                self.write_command(self.rig_sp, "*RST")
                sleep(1)
                self.write_command(self.rig_sp, ":INST CH1")
                self.write_command(self.rig_sp, ':CURR:PROT 1')
                self.write_command(self.rig_sp, ":VOLT:PROT:STAT OFF")
                self.write_command(self.rig_sp, f":VOLT {self.V}")

                command = ":MEASure:VOLTage:DC?"
                self.query_thread_sp = QueryThread(self.rig_sp, command, interval=500)
                self.query_thread_sp.response_received.connect(self.response_sp)
                self.query_thread_sp.start()

                print("Supply Power Connected!")

            except Exception as e:
                print(f'Error Supply Power Connection: {e}')
        
        else:
            self.rig_sp = rm.open_resource('USB0::0x1AB1::0x0E11::DP8C170700397::INSTR')
            zero = 0
            self.write_command(self.rig_sp, '*RST')
            self.write_command(self.rig_sp, f':VOLT {zero}')
            self.write_command(self.rig_sp, f':CURR {zero}')
            self.write_command(self.rig_sp, ':OUTP CH1,OFF')
            self.write_command(self.rig_sp, "VOLT:PROT:STAT OFF")
            self.rig_sp.close()
            self.ui.volt_m.setText("N/M")
            if self.query_thread_sp:
                self.query_thread_sp.stop()
            print("Supply Power Disconnected!")

    def response_sp(self, response):
        if self.ui.c_sp.isChecked():
            flt1_response = (round(float(response), 2))
            self.sp_response = str(flt1_response)
            self.ui.volt_m.setText(self.sp_response)

    def sp_data_resp(self):
        return self.sp_response

    def ls_connection(self):
        if self.ui.c_ls.isChecked():
            try:
                self.ls = rm.open_resource("COM5", baud_rate=57600, parity=constants.Parity.odd, data_bits=7)
                self.exec_time = time.time()
                self.write_command(self.ls, "*RST") # Reset the instrument
                sleep(1)
                self.write_command(self.ls, ":INP:CHAN B") # Set current DC function
                self.write_command(self.ls, ":INP:RANG 1") #Set 1A range
                self.write_command(self.ls, "SENS:TEMP:RANG:AUTO ON")
                sleep(1)
                self.write_command(self.ls, ":UNIT:TEMP CEL") #Set 1A range
                self.write_command(self.ls, ":TEMP:SCAL 0.01") #Set 1A range
                self.write_command(self.ls, ":CONF:TEMP B")


                command = "CRDG? B"
                self.query_thread_ls = QueryThread(self.ls, command, interval=500)# tomar datos cada 0.5 seg para tener dos valores cada muestreo de 1 seg, y evitar error.
                self.query_thread_ls.response_received.connect(self.response_ls)
                self.query_thread_ls.start()

            
                print("LakeShore Model 336 Connected!")
            except Exception as e:
                print(f"Error LakeShore Connection: {e}")
        else:

            self.ls = rm.open_resource("COM5", baud_rate=57600, parity=constants.Parity.odd, data_bits=7)
            self.ls.close()

            if self.query_thread_ls:
                self.query_thread_ls.stop()
            self.ui.temp_m.setText("N/M")
            print("LakeShore Model 336 Disconnected!")

    def response_ls(self, response):
        if self.ui.c_ls.isChecked():
            try:
                a = response[1:8]
                b = a.replace(";",'')
                c = b.replace("+",'')
                d = float(c)
                self.ls_response = str(d)
                #print("1",self.ls_response)

                if d > 100:
                    pass
                else:   

                    # getting the timestamp
                    current_time = time.time() - self.exec_time
                    self.ui.temp_m.setText(self.ls_response)
                    self.y.append(d)
                    self.x.append(current_time)  # Add a new random value.


                    self.data_line =  self.PlotWidget1.plot(self.x, self.y)

                    min_temp = min(self.y)
                    max_temp = max(self.y)
                    if len(self.y) > 1:
                        self.PlotWidget1.setYRange(min_temp, max_temp)

                    self.data_line.setData(self.x, self.y)  # Update the data.
                    #print("2",self.ls_response)

            except Exception:
                pass
        else:
            if self.query_thread_ls:
                self.query_thread_ls.stop()
            self.ls = rm.open_resource("COM5", baud_rate=57600, parity=constants.Parity.odd, data_bits=7)
            self.write_command(self.ls, "*RST")
            self.ls.close()
            self.PlotWidget1.clear()
            self.x = []
            self.y = []
            #d = 0

    def ls_data_resp(self):
        #print("3",self.ls_response)
        return self.ls_response
    

        # Principal fuctions
    def voltage_set(self):
        if self.ui.c_sp.isChecked():
            try:
                self.V = round(float(self.ui.volt_c.text()), 2)
                self.protec_volt = round(float(self.ui.prot_volt.text()),2)
                self.write_command(self.rig_sp, ":INST CH1")

                if self.V >= self.protec_volt and self.protec_volt == 0:
                    self.write_command(self.rig_sp, ":VOLT:PROT:STAT OFF")
                    self.write_command(self.rig_sp, f':VOLT {self.V}')
                    self.write_command(self.rig_sp, ":OUTP CH1,ON")
                if self.V <= self.protec_volt and self.protec_volt != 0:
                    self.write_command(self.rig_sp, f':VOLT {self.V}')
                    self.write_command(self.rig_sp, ":OUTP CH1,ON")
                if self.V <= self.protec_volt and self.protec_volt == 0:
                    self.write_command(self.rig_sp, ":VOLT:PROT:STAT ON")
                    self.write_command(self.rig_sp, f':VOLT {self.V}')
                    self.write_command(self.rig_sp, ":OUTP CH1,ON")
            except Exception as e:
                print(f"Error in voltage set: {e}")

    def volt_prot_set(self):
        if self.ui.c_sp.isChecked():
            try:
                self.protec_volt = round(float(self.ui.prot_volt.text()), 2)

                if self.protec_volt != 0:
                    self.write_command(self.rig_sp, f":VOLT:PROT {self.protec_volt}")
                    self.write_command(self.rig_sp, ":VOLT:PROT:STAT ON")
                else:
                    self.V = self.protec_volt
                    self.write_command(self.rig_sp, f':VOLT {self.V}')
                    self.write_command(self.rig_sp, ":OUTP CH1,ON")
                
            except Exception as e:
                print(f"error in voltage protection set: {e}")
        else:
            self.ls = rm.open_resource('USB0::0x1AB1::0x0E11::DP8C170700397::INSTR')
            self.write_command(self.rig_sp, "*RST")
            self.rig_sp.close()
            if self.query_thread_sp:
                self.query_thread_sp.stop()

    def save_files(self):

        if self.ui.c_dmm.isChecked() and self.ui.c_sp.isChecked() and self.ui.c_ls.isChecked():
            self.date_time = datetime.now().strftime("%d-%m-%Y_%H:%M:%S")
            self.file = str(self.ui.set_file.text())
            self.startwriting = WriteDataThread(self.file, self, interval=500)
            self.startwriting.set_data(dmm=self.dmm_response, sp=self.sp_response, ls=self.ls_response)
            self.startwriting.start()
        if self.ui.c_dmm.isChecked() and self.ui.c_sp.isChecked() and not self.ui.c_ls.isChecked():
            self.date_time = datetime.now().strftime("%d-%m-%Y_%H:%M:%S")
            self.file = str(self.ui.set_file.text())
            self.startwriting = WriteDataThread(self.file, self, interval=500)
            self.startwriting.set_data(dmm=self.dmm_response, sp=self.sp_response, ls=0)
            self.startwriting.start()
        if self.ui.c_dmm.isChecked() and self.ui.c_ls.isChecked() and not self.ui.c_sp.isChecked():
            self.date_time = datetime.now().strftime("%d-%m-%Y_%H:%M:%S")
            self.file = str(self.ui.set_file.text())
            self.startwriting = WriteDataThread(self.file, self, interval=500)
            self.startwriting.set_data(dmm=self.dmm_response, sp=0, ls=self.ls_response)
            self.startwriting.start()
        if self.ui.c_sp.isChecked() and self.ui.c_ls.isChecked() and not self.ui.c_dmm.isChecked():
            self.date_time = datetime.now().strftime("%d-%m-%Y_%H:%M:%S")
            self.file = str(self.ui.set_file.text())
            self.startwriting = WriteDataThread(self.file, self, interval=500)
            self.startwriting.set_data(dmm=0, sp=self.sp_response, ls=self.ls_response)
            self.startwriting.start()
        if self.ui.c_dmm.isChecked() and not self.ui.c_sp.isChecked() and not self.ui.c_ls.isChecked():
            self.date_time = datetime.now().strftime("%d-%m-%Y_%H:%M:%S")
            self.file = str(self.ui.set_file.text())
            self.startwriting = WriteDataThread(self.file, self, interval=500)
            self.startwriting.set_data(dmm=self.dmm_response, sp=0, ls=0)
            self.startwriting.start()
        if self.ui.c_sp.isChecked() and not self.ui.c_ls.isChecked() and not self.ui.c_dmm.isChecked():
            self.date_time = datetime.now().strftime("%d-%m-%Y_%H:%M:%S")
            self.file = str(self.ui.set_file.text())
            self.startwriting = WriteDataThread(self.file, self, interval=500)
            self.startwriting.set_data(dmm=0, sp=self.sp_response, ls=0)
            self.startwriting.start()
        if self.ui.c_ls.isChecked() and not self.ui.c_dmm.isChecked() and not self.ui.c_sp.isChecked():
            self.date_time = datetime.now().strftime("%d-%m-%Y_%H:%M:%S")
            self.file = str(self.ui.set_file.text())
            self.startwriting = WriteDataThread(self.file,self, interval=500)
            self.startwriting.set_data(dmm=0, sp=0, ls=self.ls_response)
            self.startwriting.start()



    def closeEvent(self, event):
        
        if self.close():
            writing_data = WriteDataThread(self.file,self)
            writing_data.stop()

            if self.ui.c_dmm.isChecked():
                self.rig_dmm = rm.open_resource('USB0::0x1AB1::0x0588::DM3R153200585::INSTR')
                self.write_command(self.rig_dmm, "*RST")
                self.rig_dmm.close()
                if self.query_thread_dmm:
                        self.query_thread_dmm.stop()
            if self.ui.c_sp.isChecked():
                self.rig_sp = rm.open_resource('USB0::0x1AB1::0x0E11::DP8C170700397::INSTR')
                self.write_command(self.rig_sp, "*RST")
                self.rig_sp.close()
                if self.query_thread_sp:
                        self.query_thread_sp.stop()
            if self.ui.c_ls.isChecked():
                self.ls = rm.open_resource("COM5", baud_rate=57600, parity=constants.Parity.odd, data_bits=7)
                self.write_command(self.ls, "*RST")
                self.ls.close()
                if self.query_thread_ls:
                        self.query_thread_ls.stop()


if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)
    window = Interfaz()
    window.show()
    sys.exit(app.exec())