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
# along with PD Analyzer.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-

from PySide import QtCore, QtGui
from PySide.QtGui import *


class UiNewGroupDialog(object):
    def setup_ui(self, new_group_dialog):
        new_group_dialog.setObjectName("new_group_dialog")
        new_group_dialog.resize(300, 150)

        self.buttonBox = QtGui.QDialogButtonBox(new_group_dialog)
        self.buttonBox.setGeometry(QtCore.QRect(30, 100, 200, 30))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(
            QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")

        self.editBox = QtGui.QTextEdit(new_group_dialog)
        self.editBox.setGeometry(QtCore.QRect(60, 50, 180, 30))
        self.editBox.setText("Living Room")
        self.editBox.setObjectName("newGroupEditBox")

        self.label = QtGui.QLabel(new_group_dialog)
#         self.label.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.label.setGeometry(QtCore.QRect(20, 10, 200, 30))
        self.label.setText("Input the Group Name")
#         self.label.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

        self.retranslate_ui(new_group_dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(
            "accepted()"), new_group_dialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(
            "rejected()"), new_group_dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(new_group_dialog)

    def retranslate_ui(self, new_group_dialog):
        new_group_dialog.setWindowTitle(QtGui.QApplication.translate(
            "new_group_dialog", "New Group", None, QtGui.QApplication.UnicodeUTF8))

class UiAddToGroup(object):
    def setup_ui(self, add_to_group):
        add_to_group.setObjectName("add_to_group")
        add_to_group.resize(300, 150)

        self.buttonBox = QtGui.QDialogButtonBox(add_to_group)
        self.buttonBox.setGeometry(QtCore.QRect(50, 100, 200, 30))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(
            QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")

        self.functionalityListComboBox = QtGui.QComboBox(add_to_group)
        self.functionalityListComboBox.setGeometry(QtCore.QRect(60, 50, 180, 30))
        self.functionalityListComboBox.setMaximumHeight(50)
        # self.groupListComboBox.setGeometry(QtCore.QRect(110, 60, 151, 21))
        self.functionalityListComboBox.setAutoFillBackground(True)
        self.functionalityListComboBox.setEditable(False)
        self.functionalityListComboBox.setMaxVisibleItems(20)
        self.functionalityListComboBox.setInsertPolicy(QtGui.QComboBox.InsertAtBottom)
        self.functionalityListComboBox.setSizeAdjustPolicy(
            QtGui.QComboBox.AdjustToContents)
        self.functionalityListComboBox.setObjectName("functionalityListComboBox")

        self.label = QtGui.QLabel(add_to_group)
#         self.label.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.label.setGeometry(QtCore.QRect(20, 10, 200, 30))
        self.label.setText("Select the functionality to form the group")
#         self.label.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

        self.retranslate_ui(add_to_group)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(
            "accepted()"), add_to_group.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(
            "rejected()"), add_to_group.reject)
        QtCore.QMetaObject.connectSlotsByName(add_to_group)

    def retranslate_ui(self, new_group_dialog):
        new_group_dialog.setWindowTitle(QtGui.QApplication.translate(
            "add_to_group", "Add Nodes to Group", None, QtGui.QApplication.UnicodeUTF8))

