# Copyright (C) 2018 Silicon Laboratories, Inc.
# http://developer.silabs.com/legal/version/v11/Silicon_Labs_Software_License_Agreement.txt
#
# This file is part of Bluetooth Mesh Provisioner.
#
# Bluetooth Mesh Provisioner is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Bluetooth Mesh Provisioner is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Ble Mesh Provision Tool.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-

import sys
import os
from PySide.QtGui import *
from PySide import QtCore, QtGui

from PySide import QtCore, QtGui
from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtGui import QItemSelection
from enum import Enum, IntEnum

from _ctypes import sizeof
from fileinput import filename
from os import path, access, R_OK  # W_OK for write permission.
from os import path, access, W_OK  # W_OK for write permission.
import os
import sys
import logging

import serial
import serial.tools.list_ports

from ui_newDialog import UiNewGroupDialog
from ui_newDialog import UiAddToGroup
from pyblemesh import MeshNCPThread

import binascii
from _sqlite3 import connect
from Tkconstants import OFF
from symbol import argument


logger = logging.getLogger(__name__)


class NodeStatusEnum(IntEnum):
    Unprovision = 0     # Public address
    provisioning = 1    # Random address
    provisioned = 2     # Public identity address resolved by stack
    grouped = 3         # Random identity address resolved by stack


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.centralWidget = QtGui.QWidget()
        self.centralWidget.setObjectName("centralWidget")
        self.setCentralWidget(self.centralWidget)

        self.groupListTableWidget = QtGui.QTableWidget(self.centralWidget)
        self.groupListTableWidget.setObjectName("groupListTableWidget")

        self.unGroupedNodesWidget = QtGui.QTableWidget(self.centralWidget)
        self.unGroupedNodesWidget.setObjectName("unGroupedNodesWidget")

        self.groupedNodesWidget = QtGui.QTableWidget()
        self.groupedNodesWidget.setObjectName("groupedNodesWidget")

        self.scan_button = QtGui.QPushButton(self.centralWidget)
        self.scan_button.setMaximumHeight(50)
        # self.scan_button.setGeometry(QtCore.QRect(460, 80, 75, 23))
        self.scan_button.setObjectName("scanButton")
        self.scan_button.setText('Scan')
        self.scan_button.clicked.connect(self.scan_devices)

        self.showDevices_button = QtGui.QPushButton(self.centralWidget)
        self.showDevices_button.setMaximumHeight(50)
        self.showDevices_button.setObjectName("showDevicesButton")
        self.showDevices_button.setText('Devices')
        self.showDevices_button.clicked.connect(self.show_devices)

        self.provision_button = QtGui.QPushButton(self.centralWidget)
        self.provision_button.setMaximumHeight(50)
        # self.provision_button.setGeometry(QtCore.QRect(460, 80, 75, 23))
        self.provision_button.setObjectName("provision_button")
        self.provision_button.setText('Provision')
        self.provision_button.clicked.connect(self.provision_devices)

        self.addToGroupButton = QtGui.QPushButton(self.centralWidget)
        self.addToGroupButton.setMaximumHeight(50)
        # self.scan_button.setGeometry(QtCore.QRect(460, 80, 75, 23))
        self.addToGroupButton.setObjectName("addToGroupButton")
        self.addToGroupButton.setText('Add to Group')
        self.addToGroupButton.clicked.connect(self.add_to_group)

        self.groupListComboBox = QtGui.QComboBox(self.centralWidget)
        self.groupListComboBox.setMaximumHeight(50)
        # self.groupListComboBox.setGeometry(QtCore.QRect(110, 60, 151, 21))
        self.groupListComboBox.setAutoFillBackground(True)
        self.groupListComboBox.setEditable(False)
        self.groupListComboBox.setMaxVisibleItems(20)
        self.groupListComboBox.setInsertPolicy(QtGui.QComboBox.InsertAtBottom)
        self.groupListComboBox.setSizeAdjustPolicy(
            QtGui.QComboBox.AdjustToContents)
        self.groupListComboBox.setObjectName("groupListComboBox")

        self.delFromGroupButton = QtGui.QPushButton(self.centralWidget)
        self.delFromGroupButton.setMaximumHeight(50)
        self.delFromGroupButton.setObjectName("delFromGroupButton")
        self.delFromGroupButton.setText('Delete nodes')
        self.delFromGroupButton.clicked.connect(self.del_from_group)        

        self.groupedNodesWidget.setMaximumHeight(self.height() * 0.5)

        self.splitterHor = QtGui.QSplitter(self.centralWidget)
        self.splitterHor.setOrientation(QtCore.Qt.Horizontal)
        self.splitterHor.setObjectName("splitterHor")

        self.subSplitterHor1 = QtGui.QSplitter(self.centralWidget)
        self.subSplitterHor1.setOrientation(QtCore.Qt.Horizontal)
        self.subSplitterHor1.setObjectName("subSplitterHor1")
        self.subSplitterHor1.addWidget(self.scan_button)
        self.subSplitterHor1.addWidget(self.provision_button)
        self.subSplitterHor1.addWidget(self.showDevices_button)

        self.subSplitterHor2 = QtGui.QSplitter(self.centralWidget)
        self.subSplitterHor2.setOrientation(QtCore.Qt.Horizontal)
        self.subSplitterHor2.setObjectName("subSplitterHor2")
        self.subSplitterHor2.addWidget(self.addToGroupButton)
        self.subSplitterHor2.addWidget(self.groupListComboBox)
        self.subSplitterHor2.addWidget(self.delFromGroupButton)

        self.splitterVer = QtGui.QSplitter(self.centralWidget)
        self.splitterVer.setOrientation(QtCore.Qt.Vertical)
        self.splitterVer.setObjectName("splitterVer")

        self.splitterVer.addWidget(self.subSplitterHor1)
        self.splitterVer.addWidget(self.unGroupedNodesWidget)
        self.splitterVer.addWidget(self.subSplitterHor2)
        self.splitterVer.addWidget(self.groupedNodesWidget)

        self.splitterHor.addWidget(self.groupListTableWidget)
        self.splitterHor.addWidget(self.splitterVer)
        self.splitterHor.setStretchFactor(1, 8)

        self.horizontalLayout = QtGui.QHBoxLayout(self.centralWidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalLayout.addWidget(self.splitterHor)
        self.centralWidget.setLayout(self.horizontalLayout)

        self.setWindowIcon(QtGui.QIcon("./icon/smarthome.png"))
        self.centralWidget.show()

        self.groupListTableWidget.verticalHeader().setVisible(False)
        self.groupListTableWidget.horizontalHeader().setVisible(False)

        self.groupListTableWidget.setSelectionMode(
            QtGui.QTableView.SingleSelection)
        self.groupListTableWidget.setSelectionBehavior(
            QtGui.QTableView.SelectRows)

        self.groupListTableWidget.setDragDropMode(
            QtGui.QAbstractItemView.NoDragDrop)

        self.groupListTableWidget.setAlternatingRowColors(False)
        self.groupListTableWidget.setIconSize(QtCore.QSize(80, 80))
        self.groupListTableWidget.setShowGrid(False)
#         self.groupListTableWidget.setRowCount(1)
        self.groupListTableWidget.setColumnCount(1)

        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(203, 226, 253))
        palette.setBrush(QtGui.QPalette.Active,
                         QtGui.QPalette.Highlight, brush)
        self.groupListTableWidget.setPalette(palette)

        self.groupListTableWidget.setEditTriggers(
            QtGui.QAbstractItemView.SelectedClicked)
        self.groupListTableWidget.clicked.connect(self.group_selected)

        self.unGroupedNodesWidget.setAcceptDrops(True)
        self.unGroupedNodesWidget.setDragEnabled(True)
        self.unGroupedNodesWidget.setSortingEnabled(True)
        self.unGroupedNodesWidget.setDropIndicatorShown(True)
        self.unGroupedNodesWidget.setDragDropMode(
            QtGui.QAbstractItemView.InternalMove)

        self.unGroupedNodesWidget.setSelectionMode(
            QtGui.QTableView.SingleSelection)

        self.unGroupedNodesWidget.setSelectionBehavior(
            QtGui.QTableView.SelectItems)

        self.unGroupedNodesWidget.verticalHeader().setVisible(False)
        self.unGroupedNodesWidget.horizontalHeader().setVisible(False)

        self.unGroupedNodesWidget.setAlternatingRowColors(False)
        self.unGroupedNodesWidget.setIconSize(QtCore.QSize(80, 80))
        self.unGroupedNodesWidget.setShowGrid(False)
        self.unGroupedNodesWidget.setRowCount(1)
        self.unGroupedNodesWidget.setColumnCount(3)

        self.unGroupedNodesWidget.setEditTriggers(
            QtGui.QAbstractItemView.SelectedClicked)
        self.unGroupedNodesWidget.clicked.connect(
            self.un_grouped_nodes_selected)

        self.groupedNodesWidget.setAcceptDrops(True)
        self.groupedNodesWidget.setDragEnabled(True)
        self.groupedNodesWidget.setSortingEnabled(True)
        self.groupedNodesWidget.setDropIndicatorShown(True)
        self.groupedNodesWidget.setDragDropMode(
            QtGui.QAbstractItemView.InternalMove)

        self.groupedNodesWidget.setSelectionMode(
            QtGui.QTableView.SingleSelection)
        self.groupedNodesWidget.setSelectionBehavior(
            QtGui.QTableView.SelectItems)

        self.groupedNodesWidget.verticalHeader().setVisible(False)
        self.groupedNodesWidget.horizontalHeader().setVisible(False)

        self.groupedNodesWidget.setAlternatingRowColors(False)
        self.groupedNodesWidget.setIconSize(QtCore.QSize(80, 80))
        self.groupedNodesWidget.setShowGrid(False)
        self.groupedNodesWidget.setRowCount(1)
        self.groupedNodesWidget.setColumnCount(3)

        self.groupedNodesWidget.setEditTriggers(
            QtGui.QAbstractItemView.SelectedClicked)
        self.groupedNodesWidget.clicked.connect(self.grouped_nodes_selected)

        self.menuBar = QtGui.QMenuBar()
        self.menuBar.setObjectName("menuBar")
        self.menuAction = QtGui.QMenu(self.menuBar)
        self.menuAction.setObjectName("menuAction")
        self.menuAbout = QtGui.QMenu(self.menuBar)
        self.menuAbout.setObjectName("menuAbout")
        self.setMenuBar(self.menuBar)

        self.actionNewGroup = QtGui.QAction(self.centralWidget)
        self.actionNewGroup.setObjectName("actionNewGroup")

        self.actionAboutBleProvisioner = QtGui.QAction(self.centralWidget)
        self.actionAboutBleProvisioner.setObjectName(
            "actionAboutBleProvisioner")

        self.menuAction.addAction(self.actionNewGroup)
        self.menuAbout.addAction(self.actionAboutBleProvisioner)
        self.menuBar.addAction(self.menuAction.menuAction())
        self.menuBar.addAction(self.menuAbout.menuAction())

        self.actionNewGroup.setShortcut('Ctrl+N')
        self.actionNewGroup.setIcon(QtGui.QIcon(
            self.resource_path('./icon/new_group.png')))
        self.actionNewGroup.triggered.connect(self.action_new_group)

        self.actionAboutBleProvisioner.setIcon(
            QtGui.QIcon(self.resource_path('./icon/about.png')))
        self.actionAboutBleProvisioner.triggered.connect(
            self.action_about)

        self.setWindowTitle(
            QtGui.QApplication.translate("MainWindow", "Bluetooth Mesh Provisioner",
                                         None, QtGui.QApplication.UnicodeUTF8))
        self.menuAction.setTitle(
            QtGui.QApplication.translate("MainWindow", "Action", None, QtGui.QApplication.UnicodeUTF8))
        self.menuAbout.setTitle(
            QtGui.QApplication.translate("MainWindow", "Help", None, QtGui.QApplication.UnicodeUTF8))
        self.actionNewGroup.setText(
            QtGui.QApplication.translate("MainWindow", "New Group", None, QtGui.QApplication.UnicodeUTF8))
        self.actionAboutBleProvisioner.setText(
            QtGui.QApplication.translate("MainWindow", "About Bluetooth Mesh Provisioner",
                                         None, QtGui.QApplication.UnicodeUTF8))

        self.toolBar = QtGui.QToolBar()
        self.toolBar.setObjectName("toolBar")
        
        self.comboxNCP = QtGui.QComboBox(self.centralWidget)
        self.toolBar.addWidget(self.comboxNCP)
        
        self.selectNCP = QtGui.QAction(self.centralWidget)
        self.selectNCP.setIcon(QtGui.QIcon(
            self.resource_path('./icon/disconnect.png')))
        self.selectNCP.triggered.connect(self.action_connect_ncp)
        self.toolBar.addAction(self.selectNCP)
        
        self.toolBar.addSeparator()
        
        self.rssiLabel = QtGui.QLabel(' RSSI > ')
        self.toolBar.addWidget(self.rssiLabel)
        
        self.rssiFilter = QtGui.QComboBox(self.centralWidget)
        for idx in range(0, 15):
            self.rssiFilter.addItem(str((-5)*idx + (-20))+' dbm')
        self.rssiFilter.setCurrentIndex(8)
        self.rssiFilter.setDisabled(True)   # disable temporally, the beacon has no RSSI information
        self.toolBar.addWidget(self.rssiFilter)

        self.toolBar.addSeparator()
        
        self.factoryResetButton = QtGui.QPushButton(self.centralWidget)
        self.factoryResetButton.setMaximumHeight(50)
        self.factoryResetButton.setObjectName("factoryResetButton")
        self.factoryResetButton.setText('Reset Nodes')
        self.factoryResetButton.clicked.connect(self.factory_reset_nodes)
        self.toolBar.addWidget(self.factoryResetButton)

        self.addToolBar(self.toolBar)        

        self.resize(960, 800)
        
        # Variable to control the GUI display
        self.scan_state = 0

        self.totalItemInProvisionedList = 0
        self.totalItemInGroupedList = 0
        self.newGroupDialog_x = None
        self.addToGroupDialog_x = None

        self.grp_addr = 0xC000
        self.unprov_nodes = []  # mac address, uuid, need_prov
        self.prov_nodes = []
        self.mesh_group = []
        self.add_to_group_list = []
        
        self.scan_ncp_port()

        self.ncp = None
        self.remote_set_state = 0

        logger.setLevel(logging.DEBUG)
#         logger.setLevel(logging.ERROR)

    def resizeEvent(self, *args, **kwargs):
        self.action_resize_widget()
        return QMainWindow.resizeEvent(self, *args, **kwargs)
    
    def action_resize_widget(self):
        logger.debug("%d %d %d %d" % (self.splitterVer.geometry().x(),
                                      self.splitterVer.geometry().y(),
                                      self.splitterVer.geometry().width(),
                                      self.splitterVer.geometry().height()))

        #         self.scan_button.setGeometry(self.splitterVer.geometry().x, self.splitterVer.geometry().x, 80, 30)
        for index_row in range(0, self.groupListTableWidget.rowCount()):
            group_list_table_widget_w = self.groupListTableWidget.width()
            group_list_table_widget_h = self.groupListTableWidget.height()

            width_setting = (group_list_table_widget_w *
                             0.9) if (group_list_table_widget_w * 0.9) >= 80 else 80
            self.groupListTableWidget.setColumnWidth(0, width_setting)
            self.groupListTableWidget.setRowHeight(
                index_row, group_list_table_widget_h * 0.15)

        un_grouped_widget_w = self.unGroupedNodesWidget.width()
        for index_column in range(0, self.unGroupedNodesWidget.columnCount()):
            self.unGroupedNodesWidget.setColumnWidth(
                index_column, un_grouped_widget_w * (0.99 / self.unGroupedNodesWidget.columnCount()))
        for index_row in range(0, self.unGroupedNodesWidget.rowCount()):
            self.unGroupedNodesWidget.setRowHeight(index_row, 100)

        grouped_widget_w = self.groupedNodesWidget.width()
        for index_column in range(0, self.groupedNodesWidget.columnCount()):
            self.groupedNodesWidget.setColumnWidth(
                index_column, grouped_widget_w * (0.99 / self.groupedNodesWidget.columnCount()))
        for index_row in range(0, self.groupedNodesWidget.rowCount()):
            self.groupedNodesWidget.setRowHeight(index_row, 100)    

    def scan_ncp_port(self):
        port_list = list(serial.tools.list_ports.grep("JLink CDC UART Port"))
        if len(port_list) <= 0:
            QtGui.QMessageBox.warning(self, 'Select NCP', 'No NCP connected')
        else:
            for idx in range(0, len(port_list)):
                self.comboxNCP.addItem(port_list[idx][0])

    def action_connect_ncp(self):
        if not self.ncp:
            self.ble_mesh_routine_init()
            self.selectNCP.setIcon(QtGui.QIcon(self.resource_path('./icon/connected.png')))
        else:
            self.ncp.stop()
            self.ncp = None
            self.selectNCP.setIcon(QtGui.QIcon(self.resource_path('./icon/disconnect.png')))

    @staticmethod
    def resource_path(relative_path):
        if hasattr(sys, "_MEIPASS"):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def action_new_group(self):
        self.newGroupDialog_x = UiNewGroupDialog()
        new_group_dialog = QtGui.QDialog(self)
        self.newGroupDialog_x.setup_ui(new_group_dialog)
        self.newGroupDialog_x.buttonBox.accepted.connect(
            self.action_new_group_done)
        new_group_dialog.exec_()

    # Start to create the group
    def action_new_group_done(self):
        new_group_name = self.newGroupDialog_x.editBox.toPlainText()
        logger.debug("new group name is: " + new_group_name)

        if new_group_name == "":
            QtGui.QMessageBox.warning(
                self, 'Warning', 'You didnt input any group name.')

        else:

            for val in self.mesh_group:
                if val[0] == new_group_name:
                    QtGui.QMessageBox.warning(
                        self, 'Warning', 'The group exist.')
                    return

            row_count = self.groupListTableWidget.rowCount()
            self.groupListTableWidget.setRowCount(row_count + 1)

            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap("./icon/smarthome.png"),
                           QtGui.QIcon.Normal, QtGui.QIcon.Off)
            icon.addPixmap(QtGui.QPixmap("./icon/smarthome.png"),
                           QtGui.QIcon.Normal, QtGui.QIcon.On)

            item = QtGui.QTableWidgetItem()
            item.setIcon(icon)
            # item.setCheckState(QtCore.Qt.Checked)

            brush = QtGui.QBrush(QtGui.QColor(170, 170, 127))
            brush.setStyle(QtCore.Qt.NoBrush)
            item.setBackground(brush)
            item.setText(new_group_name)
#             item.setFlags(~QtCore.Qt.ItemIsEditable)
            item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

            self.groupListTableWidget.setItem(
                self.groupListTableWidget.rowCount() - 1, 0, item)

            # update the group list comboBox
            self.groupListComboBox.addItem(new_group_name)

            # Add the group to the list
            grp = [new_group_name, self.grp_addr, self.grp_addr + 1]
            self.grp_addr += 2
            self.mesh_group.append(grp)  # group name, ctrl addr, status addr

            self.action_resize_widget()

    def action_about(self):
        QtGui.QMessageBox.about(self, 'About Bluetooth Mesh Provisioner',
                                'Copyright 2018 Silicon Laboratories, Inc. http://www.silabs.com')

    def group_selected(self, index):
        group_name = index.data()

        logger.debug("Select the group %s row %d colum %d" %
                     (index.data(), index.row(), index.column()))
        idx = self.groupListComboBox.findText(group_name)
        self.groupListComboBox.setCurrentIndex(idx)

        self.show_grouped_nodes()

    def un_grouped_nodes_selected(self, index):
        mac_address = index.data()
        logger.debug("Select the device %s row %d colum %d" %
                     (mac_address, index.row(), index.column()))

    def grouped_nodes_selected(self, index):
        mac_address_info = index.data()
        if len(mac_address_info) >= 18:
            mac_address_info = mac_address_info[:17]
                   
        logger.debug("Select the node %s row %d colum %d" %
                     (mac_address_info, index.row(), index.column()))

    @staticmethod
    def get_icon(models):
        logger.debug(models)
        ico_path = "./icon/unknown.png"

        for val in models:
            if val == 0x1302:
                ico_path = "./icon/switch.png"
                break
            elif val == 0x1300:
                ico_path = "./icon/light.png"
                break
        return ico_path

    def show_un_provisioned_devices(self):
        logger.info("Show the un-provisioned devices, total number is %d" %
                    len(self.unprov_nodes))
        for idx in range(len(self.unprov_nodes)):
            index_row = idx / 3
            index_column = idx % 3

            item = QtGui.QTableWidgetItem()
            self.groupListTableWidget.setHorizontalHeaderItem(0, item)
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap("./icon/unknown.png"),
                           QtGui.QIcon.Normal, QtGui.QIcon.Off)
            icon.addPixmap(QtGui.QPixmap("./icon/unknown.png"),
                           QtGui.QIcon.Normal, QtGui.QIcon.On)

            item = QtGui.QTableWidgetItem()
            item.setIcon(icon)
            item.setCheckState(QtCore.Qt.Unchecked)

            item.setText(self.unprov_nodes[idx]['Mac_address'])
            self.unGroupedNodesWidget.setRowCount(index_row + 1)
            self.unGroupedNodesWidget.setItem(index_row, index_column, item)

        self.action_resize_widget()
        
    def show_provisioned_nodes(self):
        logger.info("Show the provisioned devices")
        self.unGroupedNodesWidget.clear()

        logger.debug("number of provisioned nodes %d " % len(self.prov_nodes))
        for idx in range(len(self.prov_nodes)):
            logger.debug("Mac address " +
                         str(self.prov_nodes[idx]['Mac_address']))
            logger.debug("node address " +
                         str(self.prov_nodes[idx]['Node_address']))
            # logger.debug("node UUID " + str(self.prov_nodes[idx]['UUID']))
            
            logger.debug(self.prov_nodes[idx]['element_data'])

        self.totalItemInProvisionedList = 0

        for idx in range(len(self.prov_nodes)):
            # Show the provisioned nodes
            if (self.prov_nodes[idx]['status'] == NodeStatusEnum.provisioned) \
                    or (self.prov_nodes[idx]['status'] == NodeStatusEnum.grouped):
                index_row = self.totalItemInProvisionedList / 3
                index_column = self.totalItemInProvisionedList % 3
                self.totalItemInProvisionedList = self.totalItemInProvisionedList + 1
                
                # extract all of the sig models
                sig_models = []
                for element_idx in range(self.prov_nodes[idx]['element_data'][0]):
                    sig_models.extend(self.prov_nodes[idx]['element_data'][element_idx+1][3])
                icon_path = self.get_icon(sig_models)

                icon = QtGui.QIcon()
                icon.addPixmap(QtGui.QPixmap(icon_path),
                               QtGui.QIcon.Normal, QtGui.QIcon.Off)
                icon.addPixmap(QtGui.QPixmap(icon_path),
                               QtGui.QIcon.Normal, QtGui.QIcon.On)

                item = QtGui.QTableWidgetItem()
                item.setIcon(icon)
                item.setCheckState(QtCore.Qt.Unchecked)

                item_info = str(self.prov_nodes[idx]['Mac_address'])
                
                for item_group in self.prov_nodes[idx]['group']:
                    item_info = item_info + '\n' + item_group[0]

                item.setText(item_info)

                self.unGroupedNodesWidget.setRowCount(index_row + 1)
                self.unGroupedNodesWidget.setItem(
                    index_row, index_column, item)

        self.action_resize_widget()

    def show_grouped_nodes(self):
        logger.info("Show the grouped devices")
        self.groupedNodesWidget.clear()
        self.totalItemInGroupedList = 0
        for idx in range(len(self.prov_nodes)):
            if self.prov_nodes[idx]['status'] == NodeStatusEnum.grouped:
                for node_item in self.prov_nodes[idx]['group']:
                    if self.groupListComboBox.currentText() in node_item:
                        index_row = self.totalItemInGroupedList / 3
                        index_column = self.totalItemInGroupedList % 3
                        self.totalItemInGroupedList = self.totalItemInGroupedList + 1

                        sig_models = []
                        for element_idx in range(self.prov_nodes[idx]['element_data'][0]):
                            sig_models.extend(self.prov_nodes[idx]['element_data'][element_idx+1][3])
                        icon_path = self.get_icon(sig_models)

                        icon = QtGui.QIcon()
                        icon.addPixmap(QtGui.QPixmap(icon_path),
                                       QtGui.QIcon.Normal, QtGui.QIcon.Off)
                        icon.addPixmap(QtGui.QPixmap(icon_path),
                                       QtGui.QIcon.Normal, QtGui.QIcon.On)

                        item = QtGui.QTableWidgetItem()
                        item.setIcon(icon)
                        item.setCheckState(QtCore.Qt.Unchecked)

                        item.setText(self.prov_nodes[idx]['Mac_address'])
                        self.groupedNodesWidget.setRowCount(index_row + 1)
                        self.groupedNodesWidget.setItem(
                            index_row, index_column, item)

        self.action_resize_widget()

    def add_to_group_routine(self):
        
        functionality_idx = self.addToGroupDialog_x.functionalityListComboBox.currentIndex()
        if functionality_idx == -1:
            logger.info("Invalid functionality Index")
            return
        
        find_group = False
        group_index = 0
        
        for group_item in self.mesh_group:
            if group_item[0] == self.groupListComboBox.currentText():
                group_index = self.mesh_group.index(group_item)
                find_group = True
                break
        if not find_group:
            return        
        
        # mesh_group [group name, ctrl addr, status addr, [mac_address, UUID, node_address, [sig_models of elementX,.]]]
        list_len = len(self.mesh_group[group_index])
        node_num = list_len - 3
        if node_num == 0:
            # There is no node in the list need to add to group
            return
        
        # node format "Mac_address, UUID, node_address, element_address, [sig_model]]
        node = []
        
        for node_idx in range(0, node_num):
            for ele_idx in range(0, len(self.mesh_group[group_index][node_idx + 3][3])):
                if functionality_idx == 0:  # Generic OnOFF
                    if 0x1001 in self.mesh_group[group_index][node_idx + 3][3][ele_idx]:
                        logger.info("Find Generic OnOff Client")
                        node = [self.mesh_group[group_index][node_idx + 3][0],
                                self.mesh_group[group_index][node_idx + 3][1],
                                self.mesh_group[group_index][node_idx + 3][2],
                                self.mesh_group[group_index][node_idx + 3][2] + ele_idx,
                                [0x1001]]
                    elif 0x1000 in self.mesh_group[group_index][node_idx + 3][3][ele_idx]:
                        logger.info("Add Generic OnOff Server to Group")
                        node = [self.mesh_group[group_index][node_idx + 3][0],
                                self.mesh_group[group_index][node_idx + 3][1],
                                self.mesh_group[group_index][node_idx + 3][2],
                                self.mesh_group[group_index][node_idx + 3][2] + ele_idx,
                                [0x1000]]
                            
                elif functionality_idx == 1:  # Light Lightness
                    if 0x1302 in self.mesh_group[group_index][node_idx + 3][3][ele_idx]:
                        node = [self.mesh_group[group_index][node_idx + 3][0],
                                self.mesh_group[group_index][node_idx + 3][1],
                                self.mesh_group[group_index][node_idx + 3][2],
                                self.mesh_group[group_index][node_idx + 3][2] + ele_idx,
                                [0x1302]]
                    elif 0x1300 in self.mesh_group[group_index][node_idx + 3][3][ele_idx]:
                        node = [self.mesh_group[group_index][node_idx + 3][0],
                                self.mesh_group[group_index][node_idx + 3][1],
                                self.mesh_group[group_index][node_idx + 3][2],
                                self.mesh_group[group_index][node_idx + 3][2] + ele_idx,
                                [0x1300]]
                        logger.info("Find Light Lightness Client")
                        
                elif functionality_idx == 2:  # Light CTL Temperature
                    if 0x1305 in self.mesh_group[group_index][node_idx + 3][3][ele_idx]:
                        node = [self.mesh_group[group_index][node_idx + 3][0],
                                self.mesh_group[group_index][node_idx + 3][1],
                                self.mesh_group[group_index][node_idx + 3][2],
                                self.mesh_group[group_index][node_idx + 3][2] + ele_idx,
                                [0x1305]]
                    elif 0x1303 in self.mesh_group[group_index][node_idx + 3][3][ele_idx]:
                        node = [self.mesh_group[group_index][node_idx + 3][0],
                                self.mesh_group[group_index][node_idx + 3][1],
                                self.mesh_group[group_index][node_idx + 3][2],
                                self.mesh_group[group_index][node_idx + 3][2] + ele_idx,
                                [0x1303]]
                        logger.info("Find Light Lightness Client")
                else:
                    logger.info("Invalid functionality index")

            self.mesh_group[group_index].pop(node_idx + 3)

            if node:
                logger.info("start to add node %s to group %s, group address %s %s" %
                    (str(node[0]),
                     self.mesh_group[group_index][0],
                     str(hex(self.mesh_group[group_index][1])),
                     str(hex(self.mesh_group[group_index][2]))))
                self.ncp.send_command("cmd_add_node_to_group",
                                      [self.mesh_group[group_index][1],     # control group address
                                       self.mesh_group[group_index][2],     # status group address
                                       node])
            return

    def add_to_group(self):
        comb_box_index = self.groupListComboBox.currentIndex()
        if comb_box_index == -1:
            QtGui.QMessageBox.about(self, 'Warning',
                                    'Please select the Group for the operation')
        else:
            # Store the node Mac info to the list add_to_group_list[]
            row_count = self.unGroupedNodesWidget.rowCount()
            column_count = self.unGroupedNodesWidget.columnCount()
            
            for index_row in range(0, row_count):
                for index_column in range(0, column_count):
    
                    table_item = self.unGroupedNodesWidget.item(
                        index_row, index_column)
                    if table_item:
                        if self.unGroupedNodesWidget.item(index_row, index_column).checkState() == QtCore.Qt.Checked:
                            mac_address_info = self.unGroupedNodesWidget.item(
                                index_row, index_column).text()
                            if len(mac_address_info) >= 18:
                                mac_address_info = mac_address_info[:17]
                            if self.add_to_group_list.count(mac_address_info) == 0:
                                self.add_to_group_list.append(mac_address_info)
                            logger.info("Add the node to the list for adding to group %s" % mac_address_info)
                    else:
                        logger.info("None item")            

            find_group = False
            group_index = 0
            
            for group_item in self.mesh_group:
                if group_item[0] == self.groupListComboBox.currentText():
                    group_index = self.mesh_group.index(group_item)
                    find_group = True
                    break
            if not find_group:
                return
    
            # Get the UUID of the selected devices, need to search
            # the dict
            next_step = True
    
            for mac_address_info in self.add_to_group_list:
                for node_item in self.prov_nodes:
                    if (node_item['Mac_address'] == mac_address_info) \
                            and ((node_item['status'] == NodeStatusEnum.provisioned)
                                 or (node_item['status'] == NodeStatusEnum.grouped)):
                        for grp_item in node_item['group']:
                            if self.mesh_group[group_index][0] in grp_item:
                                # return if the node has been in the
                                # group now.
                                logger.info(
                                    "the node %s has been in the group now" % node_item['Mac_address'])
                                next_step = False
                                break
        
                        if next_step:
                            
                            sig_models = []
                            for element_idx in range(node_item['element_data'][0]):
                                # Currently, do not support vendor models, so just extract the SIG models. 
                                # sig_models.extend(node_item['element_data'][element_idx+1][3])
                                sig_models.append(node_item['element_data'][element_idx+1][3])
                            
                            node = [node_item['Mac_address'], node_item['UUID'],
                                    node_item['Node_address'], sig_models]
                            # mesh_group [group name, ctrl addr, status addr, [mac_address, UUID, node_address, [sig_models of elementX,...]]]
                            self.mesh_group[group_index].append(node)
                        break
                    
            # Remove the add_to_group_list
            self.add_to_group_list = []
            list_len = len(self.mesh_group[group_index])
            node_num = list_len - 3
            
            generic_onoff_cnt = 0
            lightness_cnt = 0
            ctl_temp_cnt = 0
            
            for node_idx in range(0, node_num):
                for ele_idx in range(0, len(self.mesh_group[group_index][node_idx + 3][3])):
                    if 0x1001 in self.mesh_group[group_index][node_idx + 3][3][ele_idx]:
                        generic_onoff_cnt = generic_onoff_cnt+1
                        logger.info("Find Generic OnOff Client")
                    if 0x1302 in self.mesh_group[group_index][node_idx + 3][3][ele_idx]:
                        lightness_cnt = lightness_cnt+1
                        logger.info("Find Light Lightness Client")
                    if 0x1305 in self.mesh_group[group_index][node_idx + 3][3][ele_idx]:
                        ctl_temp_cnt = ctl_temp_cnt+1
                        logger.info("Find Light CTL Client")
                    if 0x1000 in self.mesh_group[group_index][node_idx + 3][3][ele_idx]:
                        generic_onoff_cnt = generic_onoff_cnt+1
                        logger.info("Find Generic OnOff Server")
                    if 0x1300 in self.mesh_group[group_index][node_idx + 3][3][ele_idx]:
                        lightness_cnt = lightness_cnt+1
                        logger.info("Find Light Lightness Server")
                    if 0x1303 in self.mesh_group[group_index][node_idx + 3][3][ele_idx]:
                        ctl_temp_cnt = ctl_temp_cnt+1
                        logger.info("Find Light CTL Server")

            self.addToGroupDialog_x = UiAddToGroup()
            add_to_group_dialog = QtGui.QDialog(self)
            self.addToGroupDialog_x.setup_ui(add_to_group_dialog)
            
            if generic_onoff_cnt == node_num:
                self.addToGroupDialog_x.functionalityListComboBox.addItem("Generic OnOff")
            if lightness_cnt == node_num:
                self.addToGroupDialog_x.functionalityListComboBox.addItem("Light Lightness")            
            if ctl_temp_cnt == node_num:
                self.addToGroupDialog_x.functionalityListComboBox.addItem("Light CTL Temperature")            
            
            self.addToGroupDialog_x.buttonBox.accepted.connect(
                self.action_add_to_group_done)
            add_to_group_dialog.exec_()

    def action_add_to_group_done(self):
        self.add_to_group_routine()

    def del_from_group_routine(self):
        row_count = self.groupedNodesWidget.rowCount()
        column_count = self.groupedNodesWidget.columnCount()

        for index_row in range(0, row_count):
            for index_column in range(0, column_count):

                table_item = self.groupedNodesWidget.item(
                    index_row, index_column)
                if table_item:

                    if self.groupedNodesWidget.item(index_row, index_column).checkState() == QtCore.Qt.Checked:

                        # Check if the device be provisioned, only provisioned
                        # device (node) can be added to group
                        mac_address_info = self.groupedNodesWidget.item(
                            index_row, index_column).text()
                        if len(mac_address_info) >= 18:
                            mac_address_info = mac_address_info[:17]
                        # Get the UUID of the selected devices, need to search
                        # the dict

                        for node_item in self.prov_nodes:
                            if (node_item['Mac_address'] == mac_address_info) \
                                    and (node_item['status'] == NodeStatusEnum.grouped):
                                for grp_item in node_item['group']:
                                    if self.groupListComboBox.currentText() in grp_item:
                                        logger.info("start to delete node %s from groups" %
                                                    str(node_item['Mac_address']))

                                        self.ncp.send_command("cmd_del_node_from_group", 
                                                              node_item['Node_address'])  # node address to delete
                                        return
                else:
                    logger.info("None item")

    def del_from_group(self):
        comb_box_index = self.groupListComboBox.currentIndex()
        if comb_box_index == -1:
            QtGui.QMessageBox.about(self, 'Warning',
                                    'Please select the Group for the operation')
        else:
            self.del_from_group_routine()

    def provision_devices_routine(self):
        logger.info("Start provisioning routine")
        if len(self.unprov_nodes) == 0:
            return
        for item in self.unprov_nodes:
            if item['Need_Prov']:
                logger.info("provision device %s" % item['Mac_address'])
                self.ncp.send_command("cmd_provision_device", item)
                # return, and waiting for prov_node_info to trigger next provision
                return

    def provision_devices(self):
        logger.info(
            "Provision button be clicked, start provisioning the selected devices")
#         if self.scan_state == 1:
#             QtGui.QMessageBox.warning(self, 'Warning',
#                                       'Please stop the scanning before provisioning')
#         else:
        row_count = self.unGroupedNodesWidget.rowCount()
        column_count = self.unGroupedNodesWidget.columnCount()

        for index_row in range(0, row_count):
            for index_column in range(0, column_count):

                table_item = self.unGroupedNodesWidget.item(
                    index_row, index_column)
                if table_item:
                    if self.unGroupedNodesWidget.item(index_row, index_column).checkState() == QtCore.Qt.Checked:
                        mac_address_info = self.unGroupedNodesWidget.item(
                            index_row, index_column).text()
                        for item in self.unprov_nodes:
                            if item['Mac_address'] == mac_address_info:
                                item['Need_Prov'] = True
                else:
                    logger.info("None item")

        self.provision_devices_routine()

    def scan_devices(self):
        if self.ncp:
            # start to scan the unprovisioned devices.
            if self.scan_state == 0:
                self.scan_state = 1
                self.scan_button.setText("Stop")
                self.showDevices_button.setDisabled(True)
                self.provision_button.setDisabled(True)
                
                self.unGroupedNodesWidget.clear()
                # Clear the unprov_nodes list
                self.unprov_nodes = []
                self.ncp.send_command("cmd_start_scan", [])
                logger.info("Scan button be clicked, start to scan the devices")                
            else:
                self.scan_state = 0
                self.scan_button.setText("Scan")
                self.ncp.send_command("cmd_stop_scan", [])
                self.showDevices_button.setEnabled(True)
                self.provision_button.setEnabled(True)
                # Show all of the scanned devices.
                self.unGroupedNodesWidget.clear()
                self.show_un_provisioned_devices()
                logger.info("Stop button be clicked, stop to scan the devices")
        else:
            QtGui.QMessageBox.warning(self, 'Scan devices', 'Connect the NCP firstly')

    def show_devices(self):
        logger.info("Show devices button be clicked, show the provisioned nodes")
        # Show the provisioned nodes
        self.show_provisioned_nodes()

    def factory_reset_nodes_route(self):
        logger.info("Start factory reset nodes route")
        
        row_count = self.unGroupedNodesWidget.rowCount()
        column_count = self.unGroupedNodesWidget.columnCount()

        for index_row in range(0, row_count):
            for index_column in range(0, column_count):

                table_item = self.unGroupedNodesWidget.item(
                    index_row, index_column)
                if table_item:
                    if self.unGroupedNodesWidget.item(index_row, index_column).checkState() == QtCore.Qt.Checked:
                        # Check if the device be provisioned, only provisioned and grouped nodes can be reset
                        # with the node address
                        mac_address_info = self.unGroupedNodesWidget.item(
                            index_row, index_column).text()
                        if len(mac_address_info) >= 18:
                            mac_address_info = mac_address_info[:17]

                        for node_item in self.prov_nodes:
                            if (node_item['Mac_address'] == mac_address_info) \
                                    and ((node_item['status'] == NodeStatusEnum.provisioned)
                                         or (node_item['status'] == NodeStatusEnum.grouped)):
                                logger.info("start to reset node %s" %
                                            str(node_item['Mac_address']))
                                # node address to delete
                                self.ncp.send_command("cmd_factory_reset",
                                                      [node_item['Node_address'], node_item['UUID']])
                                return
                else:
                    logger.info("None item")
        
    def factory_reset_nodes(self):
        logger.info(
            "Factory reset button be clicked, start factory reset the selected nodes")
        self.factory_reset_nodes_route()

#     def node_status_switch(self, arg):
#         switcher = {
#             0: 'Unprovision',
#             1: 'provisioning',
#             2: 'provisioned',
#             3: 'grouped',
#         }
#         return switcher.get(arg, "no")

    def update_gui(self, message, data):
        if message == 'unprov_node_info':  # mac address, UUID, rssi
            logger.debug("unprov devices information: " +
                         data[0] + ', ' + data[1].encode('hex') + ', ' + str(data[2]))
            for item in self.unprov_nodes:
                if data[0] == item['Mac_address']:  # Check if the device in the unprovisioning list
                    return
            self.unprov_nodes.append({'Mac_address': data[0], 'UUID': data[1], 'Need_Prov': False})
            self.show_un_provisioned_devices()

        elif message == 'prov_node_info':  # ]mac addr, uuid, node addr], models
            logger.info("Provisioned nodes information: " + str(data[0]) + '  ' + str(
                data[1]) + '  ' + str(data[2]) + '  ' + str(data[3]))
            uuid = data[1]

            for item in self.unprov_nodes:
                if item['UUID'] == uuid:
                    # delete the node from the unprov list
                    self.unprov_nodes.pop(self.unprov_nodes.index(item))

            # prov_nodes format
            # [Mac_address, UUID, Node_address, netkeyIdx, appkeyIdx, element_data, status, group]
            # element_data [elements_cnt, [location, sig_cnt, vendor_cnt, [sig models], [vendor models]], [.], [.], ]
            # data format [Mac Address, UUID, Node Address, netkeyIdx, appkeyIdx, element_data]
            self.prov_nodes.append({'Mac_address': data[0], 
                                    'UUID': data[1],
                                    'Node_address': data[2], 
                                    'netkeyIdx': data[3],
                                    'appkeyIdx': data[4], 
                                    'element_data': data[5],
                                    'status': NodeStatusEnum.provisioned,
                                    'group': [],
                                    'relay': False,
                                    'proxy': False,
                                    'friendship': False})

            self.provision_devices_routine()
            # Show the provisioned nodes
            self.show_provisioned_nodes()

        elif message == 'add_node_to_group_done':  # node address
            group_item = []
            for item in self.mesh_group:
                if data[1] in item:     # sub_address in the mesh_group list item
                    group_item = item

            if group_item:
                for item in self.prov_nodes:
                    if data[0] == item['Node_address']:
                        item['group'].append(group_item)
                        # change the status to grouped
                        item['status'] = NodeStatusEnum.grouped
            else:
                return

            logger.info(str(data) + "Joined the group")
            self.show_grouped_nodes()
            self.show_provisioned_nodes()
            self.add_to_group_routine()
        
        elif message == 'del_node_from_group_done':
            for item in self.prov_nodes:
                if data[0] == item['Node_address']:
                    assert(item['status'] == NodeStatusEnum.grouped)
                    item['group'] = []
                    # change the status to grouped
                    item['status'] = NodeStatusEnum.provisioned            
            
            self.show_grouped_nodes()
            self.show_provisioned_nodes()
            self.del_from_group_routine()
        elif message == 'factory_reset_done':
            for item in self.prov_nodes:
                if data[0] == item['Node_address']:
                    self.prov_nodes.pop(self.prov_nodes.index(item))
                    break
            
            self.show_grouped_nodes()
            self.show_provisioned_nodes()
            self.factory_reset_nodes_route()
        elif message == 'set_relay_info':
            # returned data format [evt.address, evt.netkey_index, evt.value, evt.count, evt.interval]
            logger.debug('set relay event')
            
            for node_item in self.prov_nodes:
                if node_item['Node_address'] == data[0]:
                    self.prov_nodes[(self.prov_nodes.index(node_item))]['relay'] = True
                    break

        elif message == 'set_proxy_done':
            # returned data format [evt.address, evt.id, evt.status, evt.data]
            logger.debug('set proxy')

            for item in self.prov_nodes:
                if data[0] == item['Node_address']:
                    string_x = data[3]
                    for i in range(len(string_x)):
                        logger.debug(ord(string_x[i]))
                    if ord(string_x[0]):
                        item['proxy'] = True
                    else:
                        item['proxy'] = False
                    break

        elif message == 'set_friendship_done':
            # returned data format [evt.address, evt.id, evt.status, evt.data]
            logger.debug('set friendship')
            for item in self.prov_nodes:
                if data[0] == item['Node_address']:
                    string_x = data[3]
                    for i in range(len(string_x)):
                        logger.info(ord(string_x[i]))
                    if ord(string_x[0]):
                        item['friendship'] = True
                    else:
                        item['friendship'] = False
                    break
        elif message == "unexpected_error_message":
            logger.debug('unexpected error message 0x%x' % data)
            QtGui.QMessageBox.warning(self, 'Warning', 'Error' + str(hex(data)) + ', please try it again!')

    def ble_mesh_routine_init(self):
        # self.ncp = MeshNCPThread(self, self.comboxNCP.currentText())
        self.ncp = MeshNCPThread(self.comboxNCP.currentText())
        self.ncp.trigger.connect(self.update_gui)
        self.ncp.start()

    def contextMenuEvent(self, event):
        ungrouped_rect = QRect(self.unGroupedNodesWidget.mapToGlobal(self.unGroupedNodesWidget.pos()),
                           self.unGroupedNodesWidget.size())
        ungrouped_rect.setY(ungrouped_rect.y() - self.unGroupedNodesWidget.pos().y())
        ungrouped_rect.setSize(self.unGroupedNodesWidget.size())
        
        grouped_rect = QRect(self.groupedNodesWidget.mapToGlobal(self.groupedNodesWidget.pos()),
                           self.groupedNodesWidget.size())
        grouped_rect.setY(grouped_rect.y() - self.groupedNodesWidget.pos().y())
        grouped_rect.setSize(self.groupedNodesWidget.size())        

        if ungrouped_rect.contains(event.globalPos()):
            if self.unGroupedNodesWidget.currentItem():
                logger.info( self.unGroupedNodesWidget.currentItem().text())
            else:
                logger.info('none item')

            menu_s = QtGui.QMenu(self)
            select_all_action = QtGui.QAction('Select All', self)
            select_all_action.triggered.connect(lambda: self.select_all_slot())
            deselect_all_action = QtGui.QAction('Deselect All', self)
            deselect_all_action.triggered.connect(lambda: self.deselect_all_slot())
            menu_s.addAction(select_all_action)
            menu_s.addAction(deselect_all_action)
            menu_s.popup(QtGui.QCursor.pos())
        elif grouped_rect.contains(event.globalPos()):
            
            if self.groupedNodesWidget.currentItem():
                logger.info(self.groupedNodesWidget.currentItem().text())

                # Check the models of the selected node
                mac_address_info = self.groupedNodesWidget.currentItem().text()
                if len(mac_address_info) >= 18:
                    mac_address_info = mac_address_info[:17]

                node = []
                node_item = []
                for node_item in self.prov_nodes:
                    if (node_item['Mac_address'] == mac_address_info) \
                            and (node_item['status'] == NodeStatusEnum.grouped):

                            sig_models = []
                            for element_idx in range(node_item['element_data'][0]):
                                sig_models.extend(node_item['element_data'][element_idx+1][3])
                            
                            node = [node_item['Mac_address'], 
                                    node_item['UUID'],
                                    node_item['Node_address'], 
                                    node_item['netkeyIdx'],
                                    node_item['relay'],
                                    node_item['proxy'],
                                    node_item['friendship'],
                                    sig_models]

                            logger.info("The information of the selected node mac = %s, \
                                        UUID = %s address = %d netkeyIdx = %d" %
                                        (str(node_item['Mac_address']),
                                         str(node_item['UUID']),
                                          node_item['Node_address'],
                                          node_item['netkeyIdx']))
                            break

                menu_s = QtGui.QMenu(self)
                
                # Need to check if the node support relay
                set_relay_action = QtGui.QAction('Enable Relay', self)
                set_relay_action.triggered.connect(lambda: self.set_relay_slot(node))

                if node_item['relay']:
                    set_relay_action.setText('Disable Relay')
                
                # Need to check if the node support proxy
                set_proxy_action = QtGui.QAction('Enable Proxy', self)
                set_proxy_action.triggered.connect(lambda: self.set_proxy_slot(node))
                
                if node_item['proxy']:
                    set_proxy_action.setText('Disable Proxy')
                
                # Need to check if the node support friendship
                set_friendship_action = QtGui.QAction('Enable Friendship', self)
                set_friendship_action.triggered.connect(lambda: self.set_friendship_slot(node))
                
                if node_item['friendship']:
                    set_friendship_action.setText('Disable Friendship')                
                
                # Need to check if the node support on off
                set_onoff_action = QtGui.QAction('Toggle Light', self)
                set_onoff_action.triggered.connect(lambda: self.set_onoff_slot(node))
                
                menu_s.addAction(set_relay_action)
                menu_s.addAction(set_proxy_action)
                menu_s.addAction(set_friendship_action)
                menu_s.addAction(set_onoff_action)
                menu_s.popup(QtGui.QCursor.pos())

            else:
                logger.info('none item')

    def set_relay_slot(self, node):
        # data format [node address, netkey_idx, relay, count, interval]
        if node[4]:
            relay_onoff = 0x00
        else:
            relay_onoff = 0x01
        relay_count = 7
        relay_interval = 31
        data = [node[2], node[3], relay_onoff, relay_count, relay_interval]
        self.ncp.send_command("cmd_set_relay",data)

    def set_proxy_slot(self, node):
        if node[5]:
            proxy_onoff = '\x00'
        else:
            proxy_onoff = '\x01'       
        
        data = [node[2],proxy_onoff]
        self.ncp.send_command("cmd_set_proxy",data)

    def set_friendship_slot(self, node):
        if node[6]:
            friendship_onoff = '\x00'
        else:
            friendship_onoff = '\x01'   
        data = [node[2],friendship_onoff]         
        self.ncp.send_command("cmd_set_friendship", data)        

    def set_onoff_slot(self, node):
        mode_id = 0x1001        # mode_id depend on, it is 0x1001 if need on/off
        elem_index = 0
        server_address = node[2]
        tid = 0
        transition = 0
        delay = 0
        flags = 0      # If nonzero client expects a response from the server
        rsq_type = 0

        if self.remote_set_state == 0:
            parameters = '\x00'   #length data
            self.remote_set_state = 1
        else:
            parameters = '\x01'   #length data
            self.remote_set_state = 0

        data = [mode_id, elem_index, server_address, tid, transition, delay, flags, rsq_type, parameters]
        self.ncp.send_command("cmd_remote_set", data)

    def deselect_all_slot(self):
        logger.debug("Deselect all items")

        for index_row in range(0, self.unGroupedNodesWidget.rowCount()):
            for index_column in range(0, self.unGroupedNodesWidget.columnCount()):
                table_item = self.unGroupedNodesWidget.item(index_row, index_column)
                if table_item:
                    self.unGroupedNodesWidget.item(index_row, index_column).setCheckState(QtCore.Qt.Unchecked)
                else:
                    logger.info("None item")    
    
    def select_all_slot(self):
        logger.debug("Select all items")

        for index_row in range(0, self.unGroupedNodesWidget.rowCount()):
            for index_column in range(0, self.unGroupedNodesWidget.columnCount()):
                table_item = self.unGroupedNodesWidget.item(index_row, index_column)
                if table_item:
                    self.unGroupedNodesWidget.item(index_row, index_column).setCheckState(QtCore.Qt.Checked)
                else:
                    logger.info("None item")
# End of main window class


# Main Function
if __name__ == '__main__':
    Program = QApplication(sys.argv)
    Window = MainWindow()
    Window.show()
    Program.exec_()
