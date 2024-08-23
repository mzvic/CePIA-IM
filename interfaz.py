import sys
from PyQt6 import QtWidgets, uic, QtCore
import pyvisa
from pyvisa import constants
import os
import pyqtgraph as pg
from time import sleep
from datetime import datetime
import time

# Open RM
rm = pyvisa.ResourceManager()

#call device connected
#print("Connected VISA resources: ")
rm.list_resources()

dateFormat = "%H:%M:%S"
hourFormat = "%H%M%S"
filesDateFormat = "%d%m%y"


script_directory = os.path.dirname(os.path.abspath(__file__))
ui_folder = r"\HMI_RRL_3.ui"
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



class Interfaz(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(Interfaz,self).__init__(parent)
        self.ui=uic.loadUi(ui_dir, self)
        self.rig_dmm = None
        self.rig_sp = None
        self.ls = None
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


        #Valves definition
        self.V = 0


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
                print("1")
                self.write_command(self.rig_dmm, "*RST") # Reset the instrument
                sleep(2)
                print("2")
                self.write_command(self.rig_dmm, ":FUNC:CURR:DC") # Set current DC function
                self.write_command(self.rig_dmm, ":CURR:DC:RANG 1A") #Set 1A range
                print("3")
                sleep(2)
                self.write_command(self.rig_dmm, ":MEAS AUTO") # Set automatic measurameter
                print("4")
                sleep(2)
                print("5")
                command = ":MEASure:CURRent:DC?"
                print("6")
                self.query_thread_dmm = QueryThread(self.rig_dmm, command, interval=500)
                self.query_thread_dmm.response_received.connect(self.response_dm)
                self.query_thread_dmm.start()
                print("7")
            except Exception as err:
                print(f'error {err}')


            print("Digital MultiMeter Connected!")

        else:
            self.rig_dmm = rm.open_resource('USB0::0x1AB1::0x0588::DM3R153200585::INSTR')
            self.write_command(self.rig_dmm, "*RST")
            self.rig_dmm.close()
            if self.query_thread_dmm:
                self.query_thread_dmm.stop()
            print("Digital MultiMeter Disconnected!")

    def response_dm(self, response):
        if self.ui.c_dmm.isChecked():
            flt_response = (round(float(response), 2))
            dmm_response = str(flt_response)
            
            self.ui.curr_m.setText(dmm_response)



    def sp_connection(self):
        if self.ui.c_sp.isChecked():
            try:
                self.rig_sp = rm.open_resource('USB0::0x1AB1::0x0E11::DP8C170700397::INSTR')
                self.write_command(self.rig_sp, "*RST")
                sleep(1)
                self.write_command(self.rig_sp, ":INST CH1")
                self.write_command(self.rig_sp, ":VOLT:PROT 15")
                self.write_command(self.rig_sp, ':CURR:PROT 1')

                command = ":MEASure:VOLTage:DC?"
                self.query_thread_sp = QueryThread(self.rig_sp, command, interval=500)
                self.query_thread_sp.response_received.connect(self.response_sp)
                self.query_thread_sp.start()

                print("Supply Power Connected!")

            except Exception as e:
                print(f'error {e}')
        
        else:
            self.rig_sp = rm.open_resource('USB0::0x1AB1::0x0E11::DP8C170700397::INSTR')
            zero = '0'
            self.write_command(self.rig_sp, '*RST')
            self.write_command(self.rig_sp, f':VOLT {zero}')
            self.write_command(self.rig_sp, ':CURR 0')
            self.write_command(self.rig_sp, ':OUTP CH1,OFF')
            self.rig_sp.close()
            self.ui.volt_m.setText(f'{zero}')
            print("Supply Power Disconnected!")

    def response_sp(self, response):
        if self.ui.c_sp.isChecked():
            flt1_response = (round(float(response), 2))
            sp_response = str(flt1_response)
        
            self.ui.volt_m.setText(sp_response)



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

                # CREAR ARCHIVO DE DATOS CON NOMBRE DE FECHA Y HORA Y EN FORMATO (TIMESTAMP, TEMP)


                command = "CRDG? B" # creo que no esta reconociendo la RTD de forma automatica
                self.query_thread_ls = QueryThread(self.ls, command, interval=500)# tomar datos cada 0.5 seg para tener dos valores cada muestreo de 1 seg, y evitar error.
                self.query_thread_ls.response_received.connect(self.response_ls)
                self.query_thread_ls.start()
            
                print("LakeShore Model 336 Connected!")
            except Exception as e:
                print(f"erro {e}")
        else:

            self.ls = rm.open_resource("COM5", baud_rate=57600, parity=constants.Parity.odd, data_bits=7)
            self.ls.close()
            print("LakeShore Model 336 Disconnected!")

    def response_ls(self, response):
        if self.ui.c_ls.isChecked():
            try:
                a = response[1:8]
                b = a.replace(";",'')
                c = b.replace("+",'')
                d = float(c)
                e = str(d)

                if d > 100:
                    pass
                else:   

                    # getting the timestamp
                    current_time = time.time() - self.exec_time
                    self.ui.temp_m.setText(e)
                    self.y.append(d)
                    self.x.append(current_time)  # Add a new random value.

                    files = open("temp_files.txt", "a")
                    files.write(f"{current_time}-{d}\n")
                    files.close()

                    '''
                    folder_files = os.listdir(script_directory)
                    for files in folder_files:
                        name,extension = os.path.splitext(files)
                        if extension == ".csv":
                            #print(name, extension)
                            if name == self.nombreArchivo:
                                hour_ = datetime.now().strftime(hourFormat)
                                self.nombreArchivo = self.nombreArchivo +"_"+hour_
                    try:
                        self.adqfile = open(data_dir+self.nombreArchivo+'.csv', 'w')
                    except Exception as e:
                        print(f"Error creating file: {e}")
                        self.adqfile = open(self.nombreArchivo+'.csv', 'w')
                    '''

                    # AÑADIR current_time A ARCHIVO DE DATOS
                    # AÑADIR d A ARCHIVO DE DATOS
                    # AÑADIR "\n" A ARCHIVO DE DATOS

                    self.data_line =  self.PlotWidget1.plot(self.x, self.y)

                    min_temp = min(self.y)
                    max_temp = max(self.y)
                    if len(self.y) > 1:
                        self.PlotWidget1.setYRange(min_temp, max_temp)

                    self.data_line.setData(self.x, self.y)  # Update the data.
                    print(e)

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
            self.ui.temp_m.setText("no measuremeter")
            d = 0


        # Principal fuctions
    def voltage_set(self):
        if self.ui.c_sp.isChecked():
            self.V = round(float(self.ui.volt_c.text()), 2)

            self.write_command(self.rig_sp, f':VOLT {self.V}')
            self.write_command(self.rig_sp, ":OUTP CH1,ON")
            #time.sleep(1)

            if self.V == 0:
                pass

            elif self.V > 15:
                sleep(0.5)
                self.ui.volt_c.setText("EXCEEDS MAX. VOLTAGE")

            elif self.V < 0:
                self.ui.volt_c.setText("NEGATIVE VOLT. ERROR")
        else:
            if self.query_thread_ls:
                self.query_thread_sp.stop()
            self.rig_sp = rm.open_resource()
            self.write_command(self.rig_sp, "*RST")
            self.rig_sp.close()
            print("Supply Power Disconnected!")
    def close_all(self):
        self.rig_dmm.close()
        self.rig_sp.close()
        self.ls.close()



if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)
    window = Interfaz()
    window.show()
    sys.exit(app.exec())