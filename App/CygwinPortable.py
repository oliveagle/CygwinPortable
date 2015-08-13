# -*- coding: utf-8 -*-
#########################################################################################################
# Set Path
#########################################################################################################
import os, sys

scriptpath = os.path.realpath(os.path.dirname(sys.argv[0])).replace('\\','/')
scriptpathWinSep = os.path.realpath(os.path.dirname(sys.argv[0]))

sys.path.insert(0, scriptpath)
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.join(scriptpath, 'lib'))

if sys.maxsize == 2147483647:
    sys.path.insert(0, os.path.join(scriptpath, 'libX86'))
    sys.path.insert(0, scriptpath + '/libX86/libraries.zip')
    x86x64 = 'X86'
    print ("Running x86")
else:
    sys.path.insert(0, os.path.join(scriptpath, 'libX64'))
    sys.path.insert(0, scriptpath + '/libX64/libraries.zip')
    x86x64 = 'X64'
    print ("Running x64")

import re, time, webbrowser

import logging 

#########################################################################################################
# Import Libs
#########################################################################################################
import dict4ini
import winshell
import shutil
import win32api
import glob
import functools

from PyQt5 import QtCore, QtGui, uic, QtWidgets, QtNetwork
from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog, QVBoxLayout, QTextEdit, QMainWindow, QSystemTrayIcon, QMenu, QAction, QDesktopWidget
QtCore.QString = str


os.environ['QT_API'] = 'pyqt'
if hasattr(sys, 'frozen'):
    if sys.maxsize == 2147483647:
        QtCore.QCoreApplication.setLibraryPaths(['libX86/plugins'])
    else:
        QtCore.QCoreApplication.setLibraryPaths(['libX64/plugins'])

#####################################################################################################
# Initialising
#####################################################################################################
if not os.path.isdir(scriptpath + '\\Runtime\\Cygwin'):
    print ("Cygwin Folder not found -> Creating")
    os.makedirs(scriptpath + '\\Runtime\\Cygwin')

def getOptions(base_path, args):
    import argparse
    parser = argparse.ArgumentParser(prog='CygwinPortable', conflict_handler='resolve')

    parser.add_argument('-path',
                        dest = 'path', help = '-path "C:\Windows" open Windows folder')
    parser.add_argument('-exit',
                        dest = 'exit', help = '-exit 0 let the cygwin window open, -exit 1 close the cygwin window after execution')
    parser.add_argument('-version', action='version', version='%(prog)s 2.0')

    return parser.parse_known_args(args)

def parseCommandLine():
    scriptpath = os.path.realpath(os.path.dirname(sys.argv[0]))
    options, unknown = getOptions(scriptpath, sys.argv[1:])
    #Unknown[0] -> Command without optional parameter -> CygwinPortable.exe C:\Windows -> Opens C:\Windows, this is needed to set CygwinPortable as e.g. default program for .sh
    if unknown:
        folder = unknown[0]
        cygwinOpen(folder)
        os._exit(1)     
    #options.path -> Command with path parameter -> CygwinPortable.exe -path C:\Windows -> Opens C:\Windows
    if options.path:
        folder = options.path
        cygwinOpen(folder)
        os._exit(1)        
    if options.exit:
        pass

#####################################################################################################
# Set Registry Keys
#####################################################################################################
import winreg
import win32api
import win32com
import platform

cybeSystemsRuntimeSettings = {}
cybeSystemsRuntimeSettings['globals'] = {}

if win32com.shell.shell.IsUserAnAdmin() == True:
    cybeSystemsRuntimeSettings['globals']['runningasadmin'] = True
else:
    cybeSystemsRuntimeSettings['globals']['runningasadmin'] = False
    
# Systems Keys need _winreg.KEY_WOW64_64KEY on x64 Systems
if platform.machine() == 'AMD64':
    systemKeyRead = winreg.KEY_WOW64_64KEY | winreg.KEY_ALL_ACCESS
else:
    systemKeyRead = winreg.KEY_ALL_ACCESS
# Use keyRead for Software (Wow6432Node)

keyRead = winreg.KEY_ALL_ACCESS    

def setInvokeContextMenu(option=0):
    if cybeSystemsRuntimeSettings['globals']['runningasadmin'] == True:
        if option == 0:
            try:
                winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "HKEY_CLASSES_ROOT\*\shell\Invoke", 0, systemKeyRead)
                return True
            except:
                return False
            
        if option == 1:
            #Icon
            key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, "*\shell\Run in Cygwin")
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_EXPAND_SZ, scriptpathWinSep + '\\AppInfo\\appicon.ico')
            #Command
            key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, "*\shell\Run in Cygwin\command")
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "\"" + scriptpathWinSep + "\CygwinPortable-" + x86x64 + ".exe" + "\" -path \"%1\"")
            
            #Icon
            key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, "Directory\shell\OpenDirectoryInCygwin")
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_EXPAND_SZ, scriptpathWinSep + '\\AppInfo\\appicon.ico')
            #Command
            key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, "Directory\shell\OpenDirectoryInCygwin\command")
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "\"" + scriptpathWinSep + "\CygwinPortable-" + x86x64 + ".exe" + "\" -path \"%L\"")
            
            #Icon
            key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, "Drive\shell\OpenDriveInCygwin")
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_EXPAND_SZ, scriptpathWinSep + '\\AppInfo\\appicon.ico')
            #Command
            key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, "Drive\shell\OpenDriveInCygwin\command")
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "\"" + scriptpathWinSep + "\CygwinPortable-" + x86x64 + ".exe" + "\" -path %1")                               
            
        if option == 2:
            #Option 2 deletes registry keys
            try:
                winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, '*\shell\Run in Cygwin\command')
                winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, '*\shell\Run in Cygwin')                
            except:
                pass
            try:            
                winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, 'Directory\shell\OpenDirectoryInCygwin\command')
                winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, 'Directory\shell\OpenDirectoryInCygwin')
            except:
                pass                
            try:                
                winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, 'Drive\shell\OpenDriveInCygwin\command')
                winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, 'Drive\shell\OpenDriveInCygwin')                
            except:
                pass                              

#####################################################################################################
# Helper functions
#####################################################################################################

# Windows to Cygwin Folder
def Folder2CygFolder(fileOrFolder):
    winDrive,winPathAndFile = os.path.splitdrive(fileOrFolder)
    isFile = False

    if os.path.isfile(fileOrFolder):
        isFile = True
        filePath, fileNameComplete = os.path.split(fileOrFolder)
        fileName, fileExtension = os.path.splitext(fileNameComplete)
        if fileExtension.lower() == ".lnk":
            lnkFile = winshell.shortcut(fileOrFolder)
            lnkDrive, lnkPathAndFile = os.path.splitdrive(winshell.Shortcut._get_path(lnkFile))
            lnkFilepath, lnkFilenameExt = os.path.split(winshell.Shortcut._get_path(lnkFile))
            lnkFullPath = lnkDrive + lnkPathAndFile
            if os.path.isfile(lnkDrive + lnkPathAndFile):
                filePath, fileNameComplete = os.path.split(lnkDrive + lnkPathAndFile)
                fileName, fileExtension = os.path.splitext(fileNameComplete)
                cygPath = "/cygdrive/" + winDrive.replace(":", "").lower() + filePath.replace(winDrive + "\\", "/").replace("\\","/")
                cygPath = cygPath.replace(" ","\ ")
                cygFile = fileName + fileExtension
                cygFile = cygFile.replace(" ","\ ")
                cygDrive = "/cygdrive/" + winDrive.replace(":", "").lower() + winPathAndFile.replace("\\","/")
                return cygDrive, isFile, cygPath, cygFile, fileExtension
            else:
                isFile = False
                winDrive,winPathAndFile = os.path.splitdrive(lnkFullPath)
                cygPath = "/cygdrive/" + winDrive.replace(":", "").lower() + winPathAndFile.replace("\\","/")
                cygPath = cygPath.replace(" ","\ ")
                cygDrive = cygPath
                return cygDrive, isFile, None, None
        else:
            cygPath = "/cygdrive/" + winDrive.replace(":", "").lower() + filePath.replace(winDrive + "\\", "/").replace("\\","/")
            cygPath = cygPath.replace(" ","\ ")
            cygFile = fileName + fileExtension
            cygFile = cygFile.replace(" ","\ ")
            cygDrive = "/cygdrive/" + winDrive.replace(":", "").lower() + winPathAndFile.replace("\\","/")
            return cygDrive, isFile, cygPath, cygFile, fileExtension
    else:
        cygPath = "/cygdrive/" + winDrive.replace(":", "").lower() + winPathAndFile.replace("\\","/")
        cygPath = cygPath.replace(" ","\ ")
        cygDrive = cygPath
        return cygDrive, isFile, None, None

# Get windows drives
import string
from ctypes import windll

def get_drives():
    drives = []
    bitmask = windll.kernel32.GetLogicalDrives()
    for letter in string.ascii_uppercase:
        if bitmask & 1:
            drives.append(letter)
        bitmask >>= 1

    return drives

#####################################################################################################
# Load Settings
#####################################################################################################

scriptpathParentFolder = os.path.dirname(scriptpath)
scriptpathParentFolderDirName = os.path.basename(scriptpathParentFolder)

scriptpathParentParentFolder = os.path.dirname(scriptpathParentFolder)
scriptpathParentParentFolderDirName = os.path.basename(scriptpathParentParentFolder)

scriptpathParentParentParentFolder = os.path.dirname(scriptpathParentParentFolder)
scriptpathParentParentParentFolderDirName = os.path.basename(scriptpathParentParentParentFolder)

scriptpathWinSep = os.path.realpath(os.path.dirname(sys.argv[0]))
scriptpathParentFolder = os.path.dirname(scriptpathWinSep)
datapath = scriptpathParentFolder + "\\Data"

log_path = scriptpathParentFolder + "\\cygwin_portable.log"
# logging.basicConfig(filename=log_path, level=logging.DEBUG)

if not os.path.isdir(scriptpathParentFolder + '\\Data'):
    os.makedirs(scriptpathParentFolder + '\\Data')
if not os.path.isdir(scriptpathParentFolder + '\\Data\\ShellScript'):
    os.makedirs(scriptpathParentFolder + '\\Data\\ShellScript')
if not os.path.isdir(scriptpathParentFolder + '\\Data\\Shortcuts'):
    os.makedirs(scriptpathParentFolder + '\\Data\\Shortcuts')        

if not os.path.isfile(datapath + '\\config.ini'):
    QtCore.QFile.copy(scriptpathWinSep + '\\DefaultData\\config.ini', datapath + '\\config.ini')
    QtCore.QFile.copy(scriptpathWinSep + '\\DefaultData\\ShellScript\\Testscript.sh', datapath + '\\ShellScript\\Testscript.sh')
    QtCore.QFile.copy(scriptpathWinSep + '\\DefaultData\\Shortcuts\\C_Users.lnk', datapath + '\\Shortcuts\\C_Users.lnk')

if scriptpathParentParentFolderDirName == 'PortableApps':
    os.environ["PORTABLEAPPS"] = "true"
else:
    os.environ["PORTABLEAPPS"] = "false"

cybeSystemsMainSettings = {}
iniMainSettings = None

mainConfigFile = datapath + '\\config.ini'

cybeSystemsMainSettings = dict4ini.DictIni(mainConfigFile)
iniMainSettings = dict4ini.DictIni(mainConfigFile)

def defaultMainSettingsIni():
    cybeSystemsMainSettings['Main'] = {}
    cybeSystemsMainSettings['Main']['ExecutableExtension'] = "exe,bat,sh,pl,bat,py"
    cybeSystemsMainSettings['Main']['ExitAfterExec'] = False
    cybeSystemsMainSettings['Main']['SetContextMenu'] = True
    cybeSystemsMainSettings['Main']['TrayMenu'] = True
    # cybeSystemsMainSettings['Main']['Shell'] = "ConEmu"
    # cybeSystemsMainSettings['Main']['Shell'] = "mintty"
    cybeSystemsMainSettings['Main']['Shell'] = "mintty-zsh"
    cybeSystemsMainSettings['Main']['NoMsgBox'] = False
    # cybeSystemsMainSettings['Main']['CygwinMirror'] = "http://lug.mtu.edu/cygwin"
    cybeSystemsMainSettings['Main']['CygwinMirror'] = "http://mirrors.163.com/cygwin/"
    cybeSystemsMainSettings['Main']['CygwinPortsMirror'] = "ftp://ftp.cygwinports.org/pub/cygwinports"
    cybeSystemsMainSettings['Main']['CygwinFirstInstallAdditions'] = "vim,X11,xinit,wget,tar,gawk,bzip2,curl,zsh,git,tig"
    #cybeSystemsMainSettings['Main']['CygwinFirstInstallAdditions'] = "gawk,tar,bzip2,wget,subversion,mail,sSMTP,util-linux,ncurses,openSSH,cygrunsrv,apache2,MySQL "
    cybeSystemsMainSettings['Main']['CygwinFirstInstallDeleteUnneeded'] = True
    cybeSystemsMainSettings['Main']['InstallUnofficial'] = True
    cybeSystemsMainSettings['Main']['WindowsPathToCygwin'] = True
    cybeSystemsMainSettings['Main']['WindowsAdditionalPath'] = "/cygdrive/c/python27;/cygdrive/c/windows;/cygdrive/c/windows/system32;/cygdrive/c/windows/SysWOW64"
    cybeSystemsMainSettings['Main']['WindowsPythonPath'] = "/cygdrive/c/python27"
    cybeSystemsMainSettings['Main']['uiTemplate'] = "default"
    cybeSystemsMainSettings['Static']['Username'] = "cygwin"
    cybeSystemsMainSettings['Expert']['CygwinDeleteInstallation'] = False
    cybeSystemsMainSettings['Expert']['CygwinDeleteInstallationFolders'] = "xbin,cygdrive,dev,etc,home,lib,packages,tmp,usr,var"

def replaceSetting():
    defaultMainSettingsIni()
    mainConfigFile = datapath + '\\config.ini'
    iniMainSettings = dict4ini.DictIni(mainConfigFile)    
    
    for section in list(iniMainSettings.keys()):
        #print (iniMainSettings[section].keys())
        for opt in list(iniMainSettings[section].keys()):
            value = iniMainSettings[section][opt]
            #print (str(value))
            if isinstance(value, list):
                cybeSystemsMainSettings[section][opt] = value
            else:
                cybeSystemsMainSettings[section][opt] = str(value)
            if value == 'true' or value == 'True':
                cybeSystemsMainSettings[section][opt] = True
            if value == 'false' or value == 'False':
                cybeSystemsMainSettings[section][opt] = False
            if str(value).isdigit() == True:
                cybeSystemsMainSettings[section][opt] = int(value)

def writeMainSettings():
    cybeSystemsMainSettings.save()
    #Trigger replace Settings again to convert comma strings to array
    replaceSetting()

#Get Values from ini file -> If not found use default values
replaceSetting()

#Set Registry Keys if enabled
if cybeSystemsMainSettings['Main']['SetContextMenu'] == True:
    setInvokeContextMenu(2)
    setInvokeContextMenu(1)

if cybeSystemsMainSettings['Main']['Shell'] == "ConEmu" and not os.path.isfile(scriptpath + '/Runtime/ConEmu/ConEmu.exe'):
    print ("ConEmu not found -> Fallback to mintty")
    cybeSystemsMainSettings['Main']['Shell'] = "mintty"

if cybeSystemsMainSettings['Static']['Username'] == "" and not os.path.isfile(scriptpath + '/Runtime/ConEmu/ConEmu.exe'):
    print ("No Username -> Fallback to cygwin")
    cybeSystemsMainSettings['Static']['Username'] = "cygwin"

#Set Environment
portableAppsDrive,portableAppsPathAndFile = os.path.splitdrive(scriptpath)
if cybeSystemsMainSettings['Main']['WindowsPathToCygwin'] == True:
    os.environ["PATH"] += cybeSystemsMainSettings['Main']['WindowsAdditionalPath']
    os.environ["PATH"] += ";" + scriptpath + "\\Runtime\\cygwin\\bin"
else:
    os.environ["PATH"] += ";" + scriptpath + "\\Runtime\\cygwin\\bin"

os.environ["ALLUSERSPROFILE"] = "C:\ProgramData"
os.environ["ProgramData"] = "C:\ProgramData"
os.environ["CYGWIN"] = "nodosfilewarning1"
os.environ["USERNAME"] = cybeSystemsMainSettings['Static']['Username']
os.environ["HOME"] = "/home/" + cybeSystemsMainSettings['Static']['Username']
os.environ["USBDRV"] = portableAppsDrive
os.environ["USBDRVPATH"] = portableAppsDrive
if cybeSystemsMainSettings['Main']['WindowsPythonPath'] != "":
    os.environ["PYTHONPATH"] = cybeSystemsMainSettings['Main']['WindowsPythonPath']

if not os.path.isdir(scriptpath + '\\Runtime\\cygwin\\home\\' + cybeSystemsMainSettings['Static']['Username']):
    if os.path.isfile(scriptpath + '\\Runtime\\cygwin\\bin\\bash.exe'):
        os.makedirs(scriptpath + '\\Runtime\\cygwin\\home\\' + cybeSystemsMainSettings['Static']['Username'])

if cybeSystemsMainSettings['Expert']['CygwinDeleteInstallation'] == True:
    result = win32api.MessageBox(None,"Do you REALLY want to delete and reinstall your Cygwin installation ?", "Delete/Reinstall Cygwin",1)
    if result == 1:
        print ('Delete Cygwin Installation')
        for folder in cybeSystemsMainSettings['Expert']['CygwinDeleteInstallationFolders']:
            try:
                shutil.rmtree(scriptpath + "\\Runtime\\Cygwin\\" + folder)
            except:
                pass
    elif result == 2:
        print ('Cancel delete of Cygwin Installation')
        os._exit(1)

cygwinSetupFound = True
if not os.path.isfile(scriptpath + '\\Runtime\\cygwin\\CygwinConfig.exe'):
    cygwinSetupFound = False
    print("Cygwin setup not found -> Downloading on GUI start")

if not os.path.isfile(scriptpath + '\\Runtime\\cygwin\\CygwinPortableConfig.bat'):
    for batchFile in glob.glob(os.path.join(scriptpathParentFolder + '\\other\\batch\\*.bat')):
        shutil.copy(batchFile, scriptpath + '\\Runtime\\cygwin')

#####################################################################################################
# Config Dialog
#####################################################################################################

def loadUi(uifile, parent=None):
    from PyQt5 import uic
    return uic.loadUi(uifile, parent)

class ShowMainConfigDialog(QtWidgets.QMainWindow):
    def __init__(self, parent=None):

        super(ShowMainConfigDialog, self).__init__(parent)
        if os.path.isfile(scriptpath + "/Ressource/ui/mainConfigDialog.ui"):
            loadUi(scriptpath + "/Ressource/ui/mainConfigDialog.ui", self)
        else:
            loadUi(scriptpath + "/Ressource/ui/mainConfigDialog.ui", self)      
        

        #self.setWindowFlags(QtCore.Qt.FramelessWindowHint)  # Enable Frameless Mode
        #Load Stylesheet
        if cybeSystemsMainSettings['Main']['uiTemplate'].lower() != 'default':
            if os.path.isfile(scriptpath + "/Ressource/ui/" + cybeSystemsMainSettings['Main']['uiTemplate']):
                stylesheetFile = open(scriptpath + "/Ressource/ui/" + cybeSystemsMainSettings['Main']['uiTemplate'], "r")
            else:
                stylesheetFile = open(scriptpath + "/Ressource/ui/" + cybeSystemsMainSettings['Main']['uiTemplate'], "r")
            stylesheet = stylesheetFile.read()
            self.setStyleSheet(stylesheet)
            stylesheetFile.close()
        QtCore.QMetaObject.connectSlotsByName(self)
        self.show()

        #mainConfig
        if cybeSystemsMainSettings['Main']['SetContextMenu']:
            self.checkBox_set_windows_context_menu.setCheckState(QtCore.Qt.Checked)
        if cybeSystemsMainSettings['Main']['ExitAfterExec']:
            self.checkBox_exit_after_execution.setCheckState(QtCore.Qt.Checked)
        if cybeSystemsMainSettings['Main']['NoMsgBox']:
            self.checkBox_disable_message_boxes.setCheckState(QtCore.Qt.Checked)
        if cybeSystemsMainSettings['Main']['WindowsPathToCygwin']:
            self.checkBox_add_windows_path_variables_to_cygwin.setCheckState(QtCore.Qt.Checked)
        if cybeSystemsMainSettings['Main']['CygwinFirstInstallDeleteUnneeded']:
            self.checkBox_delete_unneeded_files.setCheckState(QtCore.Qt.Checked)
        if cybeSystemsMainSettings['Main']['InstallUnofficial']:
            self.checkBox_install_unofficial_cygwin_tools.setCheckState(QtCore.Qt.Checked)
        if cybeSystemsMainSettings['Expert']['CygwinDeleteInstallation']:
            self.checkBox_delete_complete_installation.setCheckState(QtCore.Qt.Checked)
        
        indexComboBox_shell = self.comboBox_shell.findText(cybeSystemsMainSettings['Main']['Shell'])
        print (indexComboBox_shell)
        self.comboBox_shell.setCurrentIndex(indexComboBox_shell)

        #self.lineEdit_executable_file_extensions.setText(cybeSystemsMainSettings['Main']['ExecutableExtension'])
        self.lineEdit_executable_file_extensions.setText(', '.join(cybeSystemsMainSettings['Main']['ExecutableExtension']))
        self.lineEdit_cygwin_mirror.setText(cybeSystemsMainSettings['Main']['CygwinMirror'])
        self.lineEdit_cygwin_ports_mirror.setText(cybeSystemsMainSettings['Main']['CygwinPortsMirror'])
        #self.lineEdit_first_install_additions.setText(cybeSystemsMainSettings['Main']['CygwinFirstInstallAdditions'])
        self.lineEdit_first_install_additions.setText(', '.join(cybeSystemsMainSettings['Main']['CygwinFirstInstallAdditions']))
        #self.lineEdit_drop_these_folders_on_reinstall.setText(cybeSystemsMainSettings['Expert']['CygwinDeleteInstallationFolders'])
        self.lineEdit_drop_these_folders_on_reinstall.setText(', '.join(cybeSystemsMainSettings['Expert']['CygwinDeleteInstallationFolders']))
        self.lineEdit_username.setText(cybeSystemsMainSettings['Static']['Username'])

    """def resizeEvent(self, event):
        #Top right buttons -> Fixed size
        self.btn_close.setGeometry((self.width() - 60), -3, 60, 30)
        self.btn_restore.setGeometry((self.width() - 88), -3, 40, 30)
        self.btn_minimize.setGeometry((self.width() - 118), -3, 42, 30)

        self.btn_cybesystems.setGeometry(10, 3, 30, 32)"""

    def mousePressEvent(self, event):
        self.last_pos = QtGui.QCursor.pos()

    def mouseMoveEvent(self, event):
        buttons = event.buttons()
        new_pos = QtGui.QCursor.pos()
        offset = new_pos - self.last_pos
        if buttons & QtCore.Qt.LeftButton:
            self.move(self.pos() + offset)
            self.update()
        elif buttons & QtCore.Qt.RightButton:
            size = self.size()
            self.resize(size.width() + offset.x(),
                        size.height() + offset.y())
            self.update()
        self.last_pos = QtCore.QPoint(new_pos)

    def checkCheckboxState(self, checkbox):
        if checkbox.checkState() == QtCore.Qt.Checked:
                return True
        else:
                return False

    @QtCore.pyqtSlot()
    def on_button_save_clicked(self):
        cybeSystemsMainSettings['Main']['SetContextMenu'] = self.checkCheckboxState(self.checkBox_set_windows_context_menu)
        cybeSystemsMainSettings['Main']['ExitAfterExec'] = self.checkCheckboxState(self.checkBox_exit_after_execution)
        cybeSystemsMainSettings['Main']['NoMsgBox'] = self.checkCheckboxState(self.checkBox_disable_message_boxes)
        cybeSystemsMainSettings['Main']['SetCoWindowsPathToCygwinntextMenu'] = self.checkCheckboxState(self.checkBox_add_windows_path_variables_to_cygwin)
        cybeSystemsMainSettings['Main']['CygwinFirstInstallDeleteUnneeded'] = self.checkCheckboxState(self.checkBox_delete_unneeded_files)
        cybeSystemsMainSettings['Main']['InstallUnofficial'] = self.checkCheckboxState(self.checkBox_install_unofficial_cygwin_tools)
        cybeSystemsMainSettings['Expert']['CygwinDeleteInstallation'] = self.checkCheckboxState(self.checkBox_delete_complete_installation)

        cybeSystemsMainSettings['Main']['ExecutableExtension'] = self.lineEdit_executable_file_extensions.text()
        cybeSystemsMainSettings['Main']['CygwinMirror'] = self.lineEdit_cygwin_mirror.text()
        cybeSystemsMainSettings['Main']['CygwinPortsMirror'] = self.lineEdit_cygwin_ports_mirror.text()
        cybeSystemsMainSettings['Main']['CygwinFirstInstallAdditions'] = self.lineEdit_first_install_additions.text()
        cybeSystemsMainSettings['Main']['Shell'] = self.comboBox_shell.currentText()
        cybeSystemsMainSettings['Expert']['CygwinDeleteInstallationFolders'] = self.lineEdit_drop_these_folders_on_reinstall.text()
        cybeSystemsMainSettings['Static']['Username'] = self.lineEdit_username.text()

        writeMainSettings()
        self.close()

    @QtCore.pyqtSlot()
    def on_button_cancel_clicked(self):
        self.close()

    @QtCore.pyqtSlot()
    def on_btn_close_clicked(self):
        self.close()

    @QtCore.pyqtSlot()
    def on_btn_minimize_clicked(self):
        self.showMinimized()

    @QtCore.pyqtSlot()
    def on_btn_restore_clicked(self):
        print(self.windowState())
        if self.windowState() != QtCore.Qt.WindowMaximized:
            self.showMaximized()
        else:
            self.showNormal()


#####################################################################################################
#
# Cygwin open
#
# Folder2CygFolder returns:
# Folder2CygFolder(cygwinPath)[0] -> Complete path (e.g. /cygdrive/c/windows/system32/cmd.exe)
# Folder2CygFolder(cygwinPath)[1] -> If request is a file (True) or a folder (False)
# Folder2CygFolder(cygwinPath)[2] -> Path only (e.g. /cygdrive/c/windows/system32)
# Folder2CygFolder(cygwinPath)[3] -> File only (e.g. cmd.exe)
# Folder2CygFolder(cygwinPath)[4] -> Extension only (e.g. .exe)
#
#####################################################################################################

def cygwinOpen(cygwinPath=""):
    logging.debug("cygwinOpen started")
    cygFolder = Folder2CygFolder(cygwinPath)

    logging.debug("cygFolder: %s", cygFolder)

    if cybeSystemsMainSettings['Main']['ExitAfterExec'] == False:
        shellStayOpen = ";exec /bin/bash.exe'"
        if cybeSystemsMainSettings['Main']['Shell'] == "mintty-zsh":
            shellStayOpen = ";exec /bin/zsh.exe'"
    else:
        shellStayOpen = "'"

    if cygFolder[1] == True:
        if cygFolder[4].replace(".","") in cybeSystemsMainSettings['Main']['ExecutableExtension']:
            print ("Extension is valid -> Executing")
            executeCommand = ";./" + cygFolder[3]
            if cybeSystemsMainSettings['Main']['Shell'] == "ConEmu":
                path = scriptpath + "\\Runtime\\ConEmu\\ConEmu.exe"
                parameter = " /cmd " + scriptpath + "\\Runtime\\cygwin\\bin\\bash.exe --login -i -c 'cd " + cygFolder[2] + executeCommand + shellStayOpen
            elif cybeSystemsMainSettings['Main']['Shell'] == "mintty-zsh":
                path = scriptpath + "\\Runtime\\cygwin\\bin\\mintty.exe"
                parameter = " --config /home/" + cybeSystemsMainSettings['Static']['Username'] + "/.minttyrc -e /bin/bash.exe -c 'cd " + cygFolder[2] + executeCommand + shellStayOpen
            else:
                path = scriptpath + "\\Runtime\\cygwin\\bin\\mintty.exe"
                parameter = " --config /home/" + cybeSystemsMainSettings['Static']['Username'] + "/.minttyrc -e /bin/bash.exe -c 'cd " + cygFolder[2] + executeCommand + shellStayOpen
            pathname = scriptpath
            flag = 1
            logging.debug("%s %s %s", path, parameter, pathname)
            win32api.ShellExecute(0, "open", path, parameter, pathname, flag)
    else:
        if cybeSystemsMainSettings['Main']['Shell'] == "ConEmu":
            path = scriptpath + "\\Runtime\\ConEmu\\ConEmu.exe"
            parameter = " /cmd " + scriptpath + "\\Runtime\\cygwin\\bin\\bash.exe --login -i -c 'cd " + cygFolder[0] + shellStayOpen
        elif cybeSystemsMainSettings['Main']['Shell'] == "mintty-zsh":
            path = scriptpath + "\\Runtime\\cygwin\\bin\\mintty.exe"
            parameter = " --config /home/" + cybeSystemsMainSettings['Static']['Username'] + "/.minttyrc -e /bin/bash.exe -c 'cd " + cygFolder[0] + shellStayOpen
        else:
            path = scriptpath + "\\Runtime\\cygwin\\bin\\mintty.exe"
            parameter = " --config /home/" + cybeSystemsMainSettings['Static']['Username'] + "/.minttyrc -e /bin/bash.exe -c 'cd " + cygFolder[0] + shellStayOpen
        pathname = scriptpath
        flag = 1
        logging.debug("%s %s %s", path, parameter, pathname)
        win32api.ShellExecute(0, "open", path, parameter, pathname, flag)

#####################################################################################################
# Download Dialog
#####################################################################################################
class HttpWindow(QtWidgets.QDialog):

    def center_widget(self, w):
        desktop = QtWidgets.QApplication.desktop()
        screenRect = desktop.screenGeometry(desktop.primaryScreen())
        screen_w = screenRect.width()
        screen_h = screenRect.height()
        widget_w = w.width()
        widget_h = w.height()
        x = (screen_w - widget_w) / 2
        y = (screen_h - widget_h) /2
        w.move(x, y)

    def __init__(self, url=None, showURL = False, parent=None):
        super(HttpWindow, self).__init__(parent)

        self.url = QtCore.QUrl()
        self.qnam = QtNetwork.QNetworkAccessManager()
        self.reply = None
        self.outFile = None
        self.httpGetId = 0
        self.httpRequestAborted = False

        self.urlLineEdit = QtWidgets.QLineEdit(url)
        if showURL == True:
            urlLabel = QtWidgets.QLabel("&URL:")
            urlLabel.setBuddy(self.urlLineEdit)
            self.statusLabel = QtWidgets.QLabel("Please enter the URL of a file you want to download.")
            self.statusLabel.setWordWrap(True)

            self.downloadButton = QtWidgets.QPushButton("Download")
            self.downloadButton.setDefault(True)
            self.quitButton = QtWidgets.QPushButton("Quit")
            self.quitButton.setAutoDefault(False)

            buttonBox = QtWidgets.QDialogButtonBox()
            buttonBox.addButton(self.downloadButton, QtWidgets.QDialogButtonBox.ActionRole)
            buttonBox.addButton(self.quitButton, QtWidgets.QDialogButtonBox.RejectRole)

            self.progressDialog = QtWidgets.QProgressDialog(self)
            self.urlLineEdit.textChanged.connect(self.enableDownloadButton)
            self.qnam.authenticationRequired.connect(
                    self.slotAuthenticationRequired)
            self.qnam.sslErrors.connect(self.sslErrors)
            self.progressDialog.canceled.connect(self.cancelDownload)
            self.downloadButton.clicked.connect(self.downloadFile)
            self.quitButton.clicked.connect(self.close)

            topLayout = QtWidgets.QHBoxLayout()
            topLayout.addWidget(urlLabel)
            topLayout.addWidget(self.urlLineEdit)

            mainLayout = QtWidgets.QVBoxLayout()
            mainLayout.addLayout(topLayout)
            mainLayout.addWidget(self.statusLabel)
            mainLayout.addWidget(buttonBox)
            self.setLayout(mainLayout)

            self.setWindowTitle("HTTP")
            self.urlLineEdit.setFocus()
        else:
            urlLabel = QtWidgets.QLabel("&URL:")
            urlLabel.setBuddy(self.urlLineEdit)
            self.statusLabel = QtWidgets.QLabel("Cygwin setup not found - Please click on download")
            self.statusLabel.setWordWrap(True)

            self.downloadButton = QtWidgets.QPushButton("Download")
            self.downloadButton.setDefault(True)
            self.quitButton = QtWidgets.QPushButton("Quit")
            self.quitButton.setAutoDefault(False)

            buttonBox = QtWidgets.QDialogButtonBox()
            buttonBox.addButton(self.downloadButton, QtWidgets.QDialogButtonBox.ActionRole)
            buttonBox.addButton(self.quitButton, QtWidgets.QDialogButtonBox.RejectRole)

            self.progressDialog = QtWidgets.QProgressDialog(self)
            self.urlLineEdit.textChanged.connect(self.enableDownloadButton)
            self.qnam.authenticationRequired.connect(
                    self.slotAuthenticationRequired)
            self.qnam.sslErrors.connect(self.sslErrors)
            self.progressDialog.canceled.connect(self.cancelDownload)
            self.downloadButton.clicked.connect(self.downloadFile)
            self.quitButton.clicked.connect(self.close)

            topLayout = QtWidgets.QHBoxLayout()
            topLayout.addWidget(urlLabel)
            topLayout.addWidget(self.urlLineEdit)

            mainLayout = QtWidgets.QVBoxLayout()
            mainLayout.addLayout(topLayout)
            mainLayout.addWidget(self.statusLabel)
            mainLayout.addWidget(buttonBox)
            self.setLayout(mainLayout)

            self.setWindowTitle("Download Cygwin Setup")
            self.setGeometry(0,0,500,100)
            self.center_widget(self)
            self.urlLineEdit.setFocus()

    def startRequest(self, url):
        self.reply = self.qnam.get(QtNetwork.QNetworkRequest(url))
        self.reply.finished.connect(self.httpFinished)
        self.reply.readyRead.connect(self.httpReadyRead)
        self.reply.downloadProgress.connect(self.updateDataReadProgress)

    def downloadFile(self):
        self.url = QtCore.QUrl(self.urlLineEdit.text())
        fileInfo = QtCore.QFileInfo(self.url.path())
        fileName = fileInfo.fileName()

        if not fileName:
            fileName = 'index.html'

        if QtCore.QFile.exists(fileName):
            ret = QtWidgets.QMessageBox.question(self, "HTTP","There already exists a file called %s in the current directory. Overwrite?" % fileName, QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

            if ret == QtWidgets.QMessageBox.No:
                return

            QtCore.QFile.remove(fileName)

        self.outFile = QtCore.QFile(fileName)
        if not self.outFile.open(QtCore.QIODevice.WriteOnly):
            QtWidgets.QMessageBox.information(self, "HTTP",
                    "Unable to save the file %s: %s." % (fileName, self.outFile.errorString()))
            self.outFile = None
            return

        self.progressDialog.setWindowTitle("HTTP")
        self.progressDialog.setLabelText("Downloading %s." % fileName)
        self.downloadButton.setEnabled(False)

        self.httpRequestAborted = False
        self.startRequest(self.url)

    def cancelDownload(self):
        self.statusLabel.setText("Download canceled.")
        self.httpRequestAborted = True
        self.reply.abort()
        self.downloadButton.setEnabled(True)

    def httpFinished(self):
        if self.httpRequestAborted:
            if self.outFile is not None:
                self.outFile.close()
                self.outFile.remove()
                self.outFile = None

            self.reply.deleteLater()
            self.reply = None
            self.progressDialog.hide()
            return

        self.progressDialog.hide()
        self.outFile.flush()
        self.outFile.close()

        redirectionTarget = self.reply.attribute(QtNetwork.QNetworkRequest.RedirectionTargetAttribute)

        if self.reply.error():
            self.outFile.remove()
            QtWidgets.QMessageBox.information(self, "HTTP", "Download failed: %s." % self.reply.errorString())
            self.downloadButton.setEnabled(True)
        elif redirectionTarget is not None:
            newUrl = self.url.resolved(redirectionTarget.toUrl())

            ret = QtWidgets.QMessageBox.question(self, "HTTP",
                    "Redirect to %s?" % newUrl.toString(),
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)

            if ret == QtWidgets.QMessageBox.Yes:
                self.url = newUrl
                self.reply.deleteLater()
                self.reply = None
                self.outFile.open(QtCore.QIODevice.WriteOnly)
                self.outFile.resize(0)
                self.startRequest(self.url)
                return
        else:
            fileName = QtCore.QFileInfo(QtCore.QUrl(self.urlLineEdit.text()).path()).fileName()
            self.statusLabel.setText("Downloaded %s to %s." % (fileName, QtCore.QDir.currentPath()))

            self.downloadButton.setEnabled(True)

        self.reply.deleteLater()
        self.reply = None
        self.outFile = None

    def httpReadyRead(self):
        if self.outFile is not None:
            self.outFile.write(self.reply.readAll())

    def updateDataReadProgress(self, bytesRead, totalBytes):
        if self.httpRequestAborted:
            return

        self.progressDialog.setMaximum(totalBytes)
        self.progressDialog.setValue(bytesRead)

    def enableDownloadButton(self):
        self.downloadButton.setEnabled(self.urlLineEdit.text() != '')

    def slotAuthenticationRequired(self, authenticator):
        import os
        from PyQt5 import uic

        ui = os.path.join(os.path.dirname(__file__), 'authenticationdialog.ui')
        dlg = uic.loadUi(ui)
        dlg.adjustSize()
        dlg.siteDescription.setText("%s at %s" % (authenticator.realm(), self.url.host()))

        dlg.userEdit.setText(self.url.userName())
        dlg.passwordEdit.setText(self.url.password())

        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            authenticator.setUser(dlg.userEdit.text())
            authenticator.setPassword(dlg.passwordEdit.text())

    def sslErrors(self, reply, errors):
        errorString = ", ".join([str(error.errorString()) for error in errors])

        ret = QtWidgets.QMessageBox.warning(self, "HTTP Example",
                "One or more SSL errors has occurred: %s" % errorString,
                QtWidgets.QMessageBox.Ignore | QtWidgets.QMessageBox.Abort)

        if ret == QtWidgets.QMessageBox.Ignore:
            self.reply.ignoreSslErrors()

#####################################################################################################
# Main Window (Tray and Config)
#####################################################################################################

#Parse Commandine First
parseCommandLine()

import subprocess

def firstCygwinInstall():
    cygwinFirstInstallAdditions2String =  ", ".join(cybeSystemsMainSettings['Main']['CygwinFirstInstallAdditions'])
    cmd = scriptpath + "\\Runtime\\Cygwin\\CygwinConfig.exe -R " + scriptpath + "\\Runtime\\Cygwin\\" + " -l " + scriptpath + "\\Runtime\\Cygwin\\packages -n -d -N -s " + cybeSystemsMainSettings['Main']['CygwinMirror'] + " -q -P " + cygwinFirstInstallAdditions2String
    firstCygwinInstallProcess = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    firstCygwinInstallProcessOut = firstCygwinInstallProcess.communicate()
    if cybeSystemsMainSettings['Main']['CygwinFirstInstallDeleteUnneeded'] == True:
        try:
            os.remove(scriptpath + '\\Runtime\\Cygwin\\Cygwin.ico')
            os.remove(scriptpath + '\\Runtime\\Cygwin\\Cygwin.bat')
            os.remove(scriptpath + '\\Runtime\\Cygwin\\setup.log')
            os.remove(scriptpath + '\\Runtime\\Cygwin\\setup.log.full')
        except:
            pass
    # TODO: create userhome
    print ("Cygwin Download finished")

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        if cygwinSetupFound == False:
            self.downloadFileWorker("http://cygwin.com/setup-x86.exe")
            if os.path.isfile(scriptpath + '\\setup-x86.exe'):
                shutil.copy(scriptpath + '\\setup-x86.exe', scriptpath + '\\Runtime\\cygwin\\CygwinConfig.exe')
                firstCygwinInstall()
        if os.path.isfile(scriptpath + '\\setup-x86.exe'):
            os.remove(scriptpath + '\\setup-x86.exe')

        self.startCybeSystemsApplication()

    def downloadFileWorker(self,url):
        self.httpWin = HttpWindow(url)
        self.httpWin.show()

    def center_widget(self, w):
        desktop = QtWidgets.QApplication.desktop()
        screenRect = desktop.screenGeometry(desktop.primaryScreen())
        screen_w = screenRect.width()
        screen_h = screenRect.height()
        widget_w = w.width()
        widget_h = w.height()
        x = (screen_w - widget_w) / 2
        y = (screen_h - widget_h) /2
        w.move(x, y)

    def onTrayIconActivated(self,reason):
        if reason == QtWidgets.QSystemTrayIcon.DoubleClick:
            pass

        if reason == QtWidgets.QSystemTrayIcon.Trigger:
            pass

        if reason == QtWidgets.QSystemTrayIcon.Context:
            self.scripts.clear()
            self.shortcuts.clear()
            self.drives.clear()
            for script in glob.glob(os.path.join(datapath + '\\ShellScript\\*.*')):
                img = QtGui.QImage()
                img.load(scriptpath + '/AppInfo/appicon_16.png')
                pixmap = QtGui.QPixmap.fromImage(img)
                icon = QtGui.QIcon()
                icon.addPixmap(pixmap)
                entry = QtWidgets.QAction(QtGui.QIcon(icon), script, self)
                entry.triggered.connect(functools.partial(cygwinOpen, script))
                self.scripts.addAction(entry)
            for shortcut in glob.glob(os.path.join(datapath + '\\Shortcuts\\*.*')):
                img = QtGui.QImage()
                img.load(scriptpath + '/AppInfo/appicon_16.png')
                pixmap = QtGui.QPixmap.fromImage(img)
                icon = QtGui.QIcon()
                icon.addPixmap(pixmap)
                entry = QtWidgets.QAction(QtGui.QIcon(icon), shortcut, self)
                entry.triggered.connect(functools.partial(cygwinOpen, shortcut))
                self.shortcuts.addAction(entry)
            for drive in get_drives():
                img = QtGui.QImage()
                img.load(scriptpath + '/AppInfo/drive.png')
                pixmap = QtGui.QPixmap.fromImage(img)
                icon = QtGui.QIcon()
                icon.addPixmap(pixmap)
                entry = QtWidgets.QAction(QtGui.QIcon(icon), drive, self)
                entry.triggered.connect(functools.partial(cygwinOpen, drive))
                self.drives.addAction(entry)

    def trayOptionExit(self,msgbox=True):
        app = QtWidgets.QApplication.instance()
        app.closeAllWindows()
        self.tray.hide()
        os._exit(1)

    def showQuickConfig(self):
        self.ShowMainConfigDialog=ShowMainConfigDialog()
        self.center_widget(self.ShowMainConfigDialog)
        self.ShowMainConfigDialog.setWindowIcon(QtGui.QIcon(scriptpath + '/AppInfo/appicon.ico'))
        
    def showCygwinConfig(self):
        path = scriptpath + "\\Runtime\\Cygwin\\CygwinConfig.exe"
        parameter = "-R " + scriptpath + "\\Runtime\\cygwin\\ -l " + scriptpath + "\\Runtime\\cygwin\\packages -n -d -N -s " + cybeSystemsMainSettings['Main']['CygwinMirror']
        pathname = scriptpath
        flag = 1
        win32api.ShellExecute(0, "open", path, parameter, pathname, flag)    
        
    def showCygwinPortsConfig(self):
        path = scriptpath + "\\Runtime\\Cygwin\\CygwinConfig.exe"
        parameter = " -K http://cygwinports.org/ports.gpg -R " + scriptpath + "\\Runtime\\cygwin\\ -l " + scriptpath + "\\Runtime\\cygwin\\packages -n -d -N -s " + cybeSystemsMainSettings['Main']['CygwinPortsMirror']
        pathname = scriptpath
        flag = 1
        win32api.ShellExecute(0, "open", path, parameter, pathname, flag)            
        
    def showCygwinXServer(self):
        path = scriptpath + "\\Runtime\\Cygwin\\bin\\run.exe"
        parameter = "/bin/bash.exe -c '/usr/bin/startxwin.exe -- -nolock -unixkill"
        pathname = scriptpath
        flag = 1
        win32api.ShellExecute(0, "open", path, parameter, pathname, flag)           

    def startCybeSystemsApplication(self):
        #Set Loading TrayIcon
        self.setWindowIcon(QtGui.QIcon(scriptpath + '/AppInfo/appicon_16.png'))
        traymenu = QtWidgets.QMenu()
        img = QtGui.QImage()
        img.load(scriptpath + '/AppInfo/appicon_16.png')
        self.pixmap = QtGui.QPixmap.fromImage(img)
        self.icon = QtGui.QIcon()
        self.icon.addPixmap(self.pixmap)
        self.tray = QtWidgets.QSystemTrayIcon(self.icon, self)
        self.tray.activated.connect(self.onTrayIconActivated)
        self.tray.setContextMenu(traymenu)
        self.tray.show()

        #Load Stylesheet
        if cybeSystemsMainSettings['Main']['uiTemplate'].lower() != 'default':
            if os.path.isfile(scriptpath + "/Ressource/ui/" + cybeSystemsMainSettings['Main']['uiTemplate']):
                stylesheetFile = open(scriptpath + "/Ressource/ui/" + cybeSystemsMainSettings['Main']['uiTemplate'], "r")
            else:
                stylesheetFile = open(scriptpath + "/App/PythonLib/ui/" + cybeSystemsMainSettings['Main']['uiTemplate'], "r")            
            stylesheet = stylesheetFile.read()
            traymenu.setStyleSheet(stylesheet)
            stylesheetFile.close()

        self.scripts = traymenu.addMenu('&Scripts')
        self.scripts.setIcon(QtGui.QIcon(scriptpath + '/AppInfo/appicon_16.png'))
        self.shortcuts = traymenu.addMenu('&Shortcuts')
        self.shortcuts.setIcon(QtGui.QIcon(scriptpath + '/AppInfo/shortcuts.png'))
        self.drives = traymenu.addMenu('&Drives')
        self.drives.setIcon(QtGui.QIcon(scriptpath + '/AppInfo/drive.png'))
        traymenu.addSeparator()

        # trayoption_openbash = QtWidgets.QAction(QtGui.QIcon(self.icon), "Open Terminal (C:\)", self)
        trayoption_openbash = QtWidgets.QAction(QtGui.QIcon(self.icon), "Open Terminal", self)
        trayoption_openbash.triggered.connect(lambda: cygwinOpen("C:\\"))
        traymenu.addAction(trayoption_openbash)
        trayoption_openbash.setIcon(QtGui.QIcon(scriptpath + '/AppInfo/appicon2_16.png'))

        trayoption_openxserver = QtWidgets.QAction(QtGui.QIcon(self.icon), "Open XServer", self)
        trayoption_openxserver.triggered.connect(lambda: self.showCygwinXServer())
        traymenu.addAction(trayoption_openxserver)
        trayoption_openxserver.setIcon(QtGui.QIcon(scriptpath + '/AppInfo/appicon3_16.png'))

        trayoption_opencygwinsetup = QtWidgets.QAction(QtGui.QIcon(self.icon), "Open Cygwin Setup", self)
        trayoption_opencygwinsetup.triggered.connect(lambda: self.showCygwinConfig())
        traymenu.addAction(trayoption_opencygwinsetup)
        trayoption_opencygwinsetup.setIcon(QtGui.QIcon(scriptpath + '/AppInfo/wand.png'))

        trayoption_opencygwinportssetup = QtWidgets.QAction(QtGui.QIcon(self.icon), "Open Cygwin Setup (Cygwin ports)", self)
        trayoption_opencygwinportssetup.triggered.connect(lambda: self.showCygwinPortsConfig())
        traymenu.addAction(trayoption_opencygwinportssetup)
        trayoption_opencygwinportssetup.setIcon(QtGui.QIcon(scriptpath + '/AppInfo/wand.png'))

        trayoption_quickconfig = QtWidgets.QAction(QtGui.QIcon(self.icon), "QuickConfig", self)
        trayoption_quickconfig.triggered.connect(lambda: self.showQuickConfig())
        traymenu.addAction(trayoption_quickconfig)
        trayoption_quickconfig.setIcon(QtGui.QIcon(scriptpath + '/AppInfo/cog.png'))

        traymenu.addSeparator()

        trayoption_exit_entry = QtWidgets.QAction(QtGui.QIcon(self.icon), "Exit", self)
        trayoption_exit_entry.triggered.connect(lambda: self.trayOptionExit())
        traymenu.addAction(trayoption_exit_entry)
        trayoption_exit_entry.setIcon(QtGui.QIcon(scriptpath + '/AppInfo/cancel.png'))
        
        self.tray.showMessage('CygwinPortable is running','\nRight click to open Traymenu')


#####################################################################################################
# Run TrayMenu
#####################################################################################################

if __name__ == '__main__':
    #parseCommandLine()

    app = QtWidgets.QApplication.instance()
    if app == None:
        app = QtWidgets.QApplication(sys.argv)

    app.setQuitOnLastWindowClosed(False)
    w = MainWindow()
    w.setWindowFlags(QtCore.Qt.Tool)


    sys.exit(app.exec_())