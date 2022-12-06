import sys
import os
import time
import logging
import Queue
import struct
from PySide import QtGui, QtCore
from enum import Enum, IntEnum

sys.path.insert(0, '..')
import bgapi

COM_PORT = 'COM52'
API_XML = '../apixml/gecko-mesh-1.3-ga.xml'
# The default value of the response timeout is 1s
RESPONSE_TIMEOUT = 20

import threading
from threading import Timer

STATE_NONE = 0
STATE_BIND = 20
STATE_PUB = 30
STATE_SUB = 40
STATE_CONFIG = 50

VENDOR_GRP_ADDR = 0xC003

LIGHT_ID = 0x1000  # Generic On/Off Server
SWITCH_ID = 0x1001  # Generic On/Off Client

DIM_LIGHT_ID = 0x1300  # Light Lightness Server
DIM_SWITCH_ID = 0x1302  # Light Lightness Client

RETRY_PROV_TIMERS = 5
PROVISION_RETRY_INTERVAL = 3

RETRY_FACTORY_REST_TIMERS = 5
FACTORY_RESET_INTERVAL = 3

RETRY_ADD_TO_GROUP_TIMERS = 5
ADD_TO_GROUP_INTERVAL = 3


# Specifies the State to which a Configuration Client/Server command/event applies
mesh_client_models = [
    0x1001,  # Generic OnOff Client
    0x1003,  # Generic Level Client
    # 0x1005,    #Generic Default Transition Time Client
    # 0x1008,    #Generic Power OnOff Client
    # 0x100B,    #Generic Power Level Client
    # 0x100D,    #Generic Battery Client
    # 0x1010,    #Generic Location Client
    # 0x1014,    #Generic Client Property Server
    # 0x1015,    #Generic Property Client
    # 0x1102,    #Sensor Client
    # 0x1202,    #Time Client
    # 0x1205,    #Scene Client
    # 0x1208,    #Scheduler Client
    0x1302,  # Light Lightness Client
    0x1305,  # Light CTL Client
    0x1309,  # Light HSL Client
    0x130E,  # Light xyL Client
    0x1311,  # Light LC Client
]

mesh_server_models = [
    0x1000,  # Generic OnOff Server
    0x1002,  # Generic Level Server
    # 0x1004,    #Generic Default Transition Time Server
    # 0x1006,    #Generic Power OnOff Server
    # 0x1007,    #Generic Power OnOff Setup Server
    # 0x1009,    #Generic Power Level Server
    # 0x100A,    #Generic Power Level Setup Server
    # 0x100C,    #Generic Battery Server
    # 0x100E,    #Generic Location Server
    # 0x100F,    #Generic Location Setup Server
    # 0x1011,    #Generic Admin Property Server
    # 0x1012,    #Generic Manufacturer Property Server
    # 0x1013,    #Generic User Property Server
    # 0x1014,    #Generic Client Property Server
    # 0x1100,    #Sensor Server
    # 0x1101,    #Sensor Setup Server
    # 0x1200,    #Time Server
    # 0x1201,    #Time Setup Server
    # 0x1203,    #Scene Server
    # 0x1204,    #Scene Setup Server
    # 0x1206,    #Scheduler Server
    # 0x1207,    #Scheduler Setup Server
    0x1300,  # Light Lightness Server
    # 0x1301,    #Light Lightness Setup Server
    0x1303,  # Light CTL Server
    # 0x1304,    #Light CTL Setup Server
    0x1306,  # Light CTL Temperature Server
    0x1307,  # Light HSL Server
    # 0x1308,    #Light HSL Setup Server
    0x130A,  # Light HSL Hue Server
    0x130B,  # Light HSL Saturation Server
    0x130C,  # Light xyL Server
    # 0x130D,    #Light xyL Setup Server
    0x130F,  # Light LC Server
    # 0x1310,    #Light LC Setup Server
]


class LeGapAddressType(IntEnum):
    public = 0  # Public address
    random = 1  # Random address
    public_identity = 2  # Public identity address resolved by stack
    random_identity = 3  # Random identity address resolved by stack


class LeGapPhyType(IntEnum):
    phy_1m = 1  # LE 1M PHY
    phy_2m = 2  # LE 2M PHY
    phy_coded = 4  # LE Coded PHY


class MeshNodeConfigState(IntEnum):
    mesh_node_dcd = 32776  # 0x8008
    mesh_node_beacon = 32777  # 0x8009
    mesh_node_default_ttl = 32780  # 0x800C
    mesh_node_friendship = 32783  # 0x800F
    mesh_node_gatt_proxy = 32786  # 0x8012
    mesh_node_key_refresh = 32789  # 0x8015
    mesh_node_relay = 32803  # 0x8023
    mesh_node_identity = 32834  # 0x8042
    mesh_node_appkey_delete = 0x8000    # Cheng, no user guide address it


class EventTimerType(IntEnum):
    t_provision_gatt_device = 1
    t_factory_reset = 2
    t_add_to_group = 3


class MeshGenericClientGetStateType(IntEnum):
    on_off = 0  # Generic on/off get request
    on_power_up = 1  # Generic on power up get request
    level = 2  # Generic level get request
    power_level = 3  # Generic power level get request
    power_level_last = 4  # Generic power level last get request
    power_level_default = 5  # Generic power level default get request
    power_level_range = 6  # Generic power level range get request
    transition_time = 6  # Generic transition time get request
    battery = 8  # Generic battery get request
    location_global = 9  # Generic global location get request
    location_local = 10  # Generic local location get request
    property_user = 11  # Generic user property get request
    property_admin = 12  # Generic admin property get request
    property_manuf = 13  # Generic Manufacturer property get request
    property_list_user = 14  # Generic user property list get request
    property_list_admin = 15  # Generic admin property list get request
    property_list_manuf = 16  # Generic Manufacturer property list get request
    property_list_client = 17  # Generic client property list get request
    lightness_actual = 128  # Light actual lightness get request
    lightness_linear = 129  # Light linear lightness get request
    lightness_last = 130  # Light last lightness get request
    lightness_default = 131  # Light default lightness get request
    lightness_range = 132  # Light lightness range get request#


class MeshGenericClientSetRequstType(IntEnum):
    on_off = 0  # Generic on/off set request
    on_power_up = 1  # Generic on power up set request
    level = 2  # Generic level set request
    level_delta = 3  # Generic level delta set request
    level_move = 4  # Generic level Move set request
    level_halt = 5  # Generic level halt request
    power_level = 6  # Generic power level set request
    power_level_default = 7  # Generic power level default set request
    power_level_range = 8  # Generic power level range set request
    transition_time = 9  # Generic transition time set request
    location_global = 10  # Generic global location set request
    location_local = 11  # Generic local location set request
    property_user = 12  # Generic user property set request
    property_admin = 13  # Generic admin property set request
    property_manuf = 14  # Generic Manufacturer property set request
    lightness_actual = 128  # Light actual lightness set request
    lightness_linear = 129  # Light linear lightness set request
    lightness_default = 130  # Light default lightness set request
    lightness_range = 131  # Light lightness range set request


logger = logging.getLogger(__name__)


class MeshNCPThread(QtCore.QThread):
    trigger = QtCore.Signal(str, list)

    def __init__(self, com_port, parent=None):
        super(MeshNCPThread, self).__init__(parent)
        self.conn = bgapi.SerialConnector(com_port)
        self.conn.close()  # initially close the connection

        # data format (connection, event_handler, apis, response_timeout=1, log_id=None)
        self.lib = bgapi.BGLib(self.conn, None, [API_XML], RESPONSE_TIMEOUT)
        if not self.lib:
            return

        if self.lib.is_open():
            self.lib.close()

        self.lib.open()
        self.dev = getattr(self.lib, 'gecko')
        self.dev.name = 'Provisioner'
        self.dev.reset = self.prov_dev_reset

        # Initialize key
        self.nwk_idx = 0xFF
        self.appk_idx = 0xFF
        self.node_info = []  # mac addr, uuid, node addr, [models]

        self.pub = []  # node_addr, model, 0xFFFF, pub_addr
        self.sub = []  # node_addr, model, 0xFFFF, sub_addr
        self.bind = []  # node_addr, model, 0xFFFF

        self.scan_state = False
        self.mesh_nodes = []  # Node mac addr and UUID

        self.state = STATE_NONE
        self.connection_handle = 0xFF
        self.prov_uuid = ''

        self.ddb_list = []  # used to store the unicast address of the primary element of the nodes

        self.eventTimer = None
        self.retry_cnt = 0
        self.eventType = None
        self.connection_opened = False

        # message queue for receiving command from GUI
        self.cmd_queue = Queue.Queue()

        logging.basicConfig(
            format='%(asctime)s %(filename)s %(levelname)s - %(message)s',
            level=logging.INFO,
            datefmt='%H:%M:%S')

    def run(self):
        self.reset_ncp()
        logger.setLevel(logging.DEBUG)
        logger.info("BLE Mesh Provisioner!")
        logger.debug("Logger debug output")
        self.handle_events()
        
    def stop(self):
        logger.debug("Disconnect the NCP")
        if self.lib:
            if self.lib.is_open():
                self.lib.close()

    def handle_events(self):
        run = True
        while run:
            if self.cmd_queue.empty() is not True:
                self.cmd_handler()

            evt = self.lib.get_event(0)
            if evt is None:
                continue
            evt_name = (evt._class_name + '_' + evt._msg_name)

            if evt_name == 'system_boot':
                logger.info(evt_name)
                # This command must be issued before any other Bluetooth Mesh commands.
                rsp = self.dev.mesh_prov.init()
                logger.debug("result = %x" % rsp.result)

                if rsp.result:
                    logger.info("Unexpected return value!")
                    self.trigger.emit("unexpected_error_message", rsp.result)
            # elif evt_name == 'le_gap_scan_response':
            #     # logger.info(evt_name)
            #     self.scan_mesh_beacon(evt)

            elif evt_name == 'mesh_prov_initialized':
                logger.debug(evt_name)
                self.create_nwk_app_key(evt)

            elif evt_name == 'mesh_prov_unprov_beacon':
                # logger.debug(evt_name)
                self.parse_mesh_beacon(evt)

            elif evt_name == 'le_connection_opened':
                logger.debug(evt_name)
                logger.debug('Connection to address %s was opened' %
                             evt.address)
                self.connection_handle = evt.connection
                self.connection_opened = True
                self.dev.le_connection.get_rssi(evt.connection)

            elif evt_name == 'le_connection_closed':
                logger.debug(evt_name)
                logger.debug('Connection %d be closed' % evt.connection)
                self.connection_opened = False

            elif evt_name == 'le_connection_rssi':
                logger.debug(evt_name)
                logger.debug('rssi of the connection %d is %d' %
                             (evt.connection, evt.rssi))

                # Start provisioning here, can filter the device with rssi
                rsp = self.dev.mesh_prov.provision_gatt_device(
                    self.nwk_idx, evt.connection, self.prov_uuid)
                logger.debug("result = 0x%x" % rsp.result)

                if rsp.result:
                    logger.info("Unexpected return value!")
                    self.trigger.emit("unexpected_error_message", rsp.result)

            elif evt_name == 'mesh_prov_device_provisioned':
                logger.debug(evt_name)

                # close the connection after provisioned done
                rsp = self.dev.le_connection.close(self.connection_handle)
                logger.debug("Close the connection, result = 0x%x" % rsp.result)
                if rsp.result == 0:
                    self.connection_handle = 0xFF
                    self.prov_uuid = ''

                # logger.info('Address = %x, UUID = %s' % (evt.address, evt.uuid.encode('hex')))
                self.node_info.append(evt.uuid)  # save uuid
                self.node_info.append(evt.address)  # save node address
                # # Enable proxy
                # # self.dev.mesh_prov.set_config(evt.address, mesh_node_gatt_proxy, self.nwk_idx, '\x01')
                # self.dev.mesh_prov.set_config(evt.address, mesh_node_gatt_proxy, self.nwk_idx, '\x01')
                # self.state = STATE_CONFIG
                rsp = self.dev.mesh_prov.get_dcd(evt.address, 0xFF)
                logger.debug("result = %x" % rsp.result)

                if rsp.result:
                    logger.info("Unexpected return value!")
                    self.trigger.emit("unexpected_error_message", rsp.result)

            elif evt_name == 'mesh_prov_provisioning_failed':
                logger.debug(evt_name)
                logger.debug('Provisioning the device %s failed with reason 0x%x' % (
                    evt.uuid, evt.reason))

            elif evt_name == 'mesh_prov_dcd_status':
                logger.debug(evt_name)
                logger.debug("DCD status = %x" % evt.result)
                if evt.result == 0:
                    # Cancel the event timer if device provisioned
                    if self.eventTimer and self.eventTimer.is_alive():
                        logger.debug("Cancel the event timer, Provision done")
                        self.eventTimer.cancel()
                        self.eventType = None
                        self.retry_cnt = 0

                        element_data = self.decode_dcd(evt)
                        self.node_info.append(self.nwk_idx)
                        self.node_info.append(self.appk_idx)
                        # element_data format [[location, sig_cnt, vendor_cnt, sig_models, vendor_models], ... ]
                        self.node_info.append(element_data)
                        self.trigger.emit("prov_node_info", self.node_info)

            elif evt_name == 'mesh_prov_config_status':
                logger.debug(evt_name)
                self.handle_config_status(evt)

            elif evt_name == 'mesh_prov_node_reset':
                # Note that the note reset event may get lost and the node has reset itself.
                logger.debug(evt_name)

                # Cancel the event timer if node be reset
                if self.eventTimer and self.eventTimer.is_alive():
                    logger.debug("Cancel the event timer, factory reset done")
                    self.eventTimer.cancel()
                    self.eventType = None
                    self.retry_cnt = 0

                # After reset the node, need to delete it from the ddb of provisioner.
                for item in self.ddb_list:
                    # Check if the node in the ddb of the provisioner.
                    if evt.address == item[1]:
                        # Double check if the node in the ddb of the provisioner.
                        rsp = self.dev.mesh_prov.ddb_get(item[0])
                        # Delete node information from provisioner database
                        if rsp.result == 0:
                            logger.debug("Delete node 0x%02x from the provisioner database" % evt.address)
                            self.dev.mesh_prov.ddb_delete(item[0])
                            self.trigger.emit("factory_reset_done", [evt.address])
               
            elif evt_name == 'mesh_prov_relay_status':
                logger.debug(evt_name)
                # There is a bug here, that the return value of the Unicast address is incorrect
                if evt:
                    self.trigger.emit("set_relay_info", [
                                      evt.address, evt.netkey_index, evt.value, evt.count, evt.interval])

            elif evt_name == 'mesh_generic_client_server_status':
                logger.debug(evt_name)
                logger.debug("model_id = 0x%04x \
                                elem_index = 0x%04x \
                                client_address = 0x%04x \
                                server_address = 0x%04x \
                                remaining = 0x%d \
                                flags = 0x%x type = 0x%x \
                                parameters = %x" %
                                (evt.model_id, evt.elem_index, evt.client_address, evt.server_address,
                                 evt.remaining, evt.flags, evt.type, evt.parameters))
                self.trigger.emit("client_server_status", [
                                  evt.model_id, evt.elem_index, evt.client_address, evt.server_address,
                                    evt.remaining, evt.flags, evt.type, evt.parameters])

            elif evt_name == 'mesh_prov_ddb_list':
                logger.debug(evt_name)
                logger.debug("address = 0x%02x elements = %d UUID = %s" % (evt.address, evt.elements, evt.uuid))
                # Store the unicast address
                self.ddb_list.append([evt.uuid, evt.address, evt.elements])

    def event_timer_handle(self, *args, **kargs):
        # time.sleep(0.1)
        # logger.info('------------------------------------------')
        # print args
        # print kargs

        # logger.debug('event timer handler be triggered by' % kargs['eventType'])

        # Check if the eventType be included in the kargs.
        if kargs.has_key('eventType'):
            if kargs['eventType'] == EventTimerType.t_provision_gatt_device:

                # Need to retry to provision the device again
                # If any process of le_gap_connect -> le_connection_get_rssi -> mesh_prov_provision_gatt_device failed.

                # timer argument, args[mac address, address_type, initiating_phy, connection_handle]
                # keyword arguements {"eventType":EventTimerType.t_provision_gatt_device}
                self.retry_cnt = self.retry_cnt + 1
                if self.retry_cnt > RETRY_PROV_TIMERS:
                    self.retry_cnt = 0
                    return

                logger.info('Start the %d time provisioning retry' %
                            self.retry_cnt)

                # need to close the connection if the connection opened.
                if self.connection_opened:
                    rsp = self.dev.le_connection.close(args[4])
                    logger.debug("result = %x" % rsp.result)

                    while self.connection_opened:
                        logger.info('Waiting for the connection closed')
                        time.sleep(0.5)

                self.connection_handle = 0xFF
                # Start to provision again.
                self.provision_device(args[0], args[1])

            elif kargs['eventType'] == EventTimerType.t_factory_reset:
                # Need to retry to reset the nodes
                # timer argument, args[node address, uuid, nwk_idx]
                # keyword arguements {"eventType":EventTimerType.t_factory_reset}
                self.retry_cnt = self.retry_cnt + 1
                if self.retry_cnt > RETRY_FACTORY_REST_TIMERS:
                    self.retry_cnt = 0

                    # Note that the note reset event may get lost and the node has reset itself.
                    # So the script need to delete the node from the ddb of provisioner after few times retry.
                    for item in self.ddb_list:
                        # Check if the node in the ddb of the provisioner.
                        if args[0] == item[1]:
                            # Double check if the node in the ddb of the provisioner.
                            rsp = self.dev.mesh_prov.ddb_get(item[0])
                            # Delete node information from provisioner database
                            if rsp.result == 0:
                                logger.debug("Delete node 0x%02x from the provisioner database" % args[0])
                                self.dev.mesh_prov.ddb_delete(item[0])
                                self.trigger.emit("factory_reset_done", [args[0]])
                    return

                logger.info('Start the %d time factory reset retry' %
                            self.retry_cnt)

                # Start to perform the factory reset again.
                self.factory_reset([args[0], args[1]])

            elif kargs['eventType'] == event_timer_type.t_add_to_group:
                # Need to retry to add the node to group

                # timer argument, args[grp]
                # keyword arguements {"eventType":event_timer_type.t_add_to_group}
                self.retry_cnt = self.retry_cnt + 1
                if self.retry_cnt > RETRY_ADD_TO_GROUP_TIMERS:
                    self.retry_cnt = 0
                    return

                logger.info('Start the %d time add to group retry' % self.retry_cnt)

                # Start to perform the add to group again.
                time.sleep(1)
                self.add_node_to_group(args[0])

            else:
                logger.info("Invalid event type!")

    # Creating network and app key if there is not.
    def create_nwk_app_key(self, evt):
        logger.info("networks = 0x%x,  address = 0x%x, ivi = 0x%x"
                    % (evt.networks, evt.address, evt.ivi))
        # Number of network keys the Provisioner has.
        if evt.networks > 0:
            logger.info(
                "Number of network keys the Provisioner has: %x" % evt.networks)
            self.nwk_idx = 0
            self.appk_idx = 0
        else:
            logger.info("Creating a new network key on the Provisioner")
            rsp = self.dev.mesh_prov.create_network('')
            if rsp.result == 0:
                self.nwk_idx = rsp.network_id
                logger.info("Success, net key = %x" % rsp.network_id)
            else:
                logger.info(
                    "Failed to create new network key, result = %x" % rsp.result)

            if rsp.result:
                logger.info("Unexpected return value!")
                self.trigger.emit("unexpected_error_message", rsp.result)

            logger.info("Creating a new app key on the Provisioner")
            rsp = self.dev.mesh_prov.create_appkey(self.nwk_idx, '')
            if rsp.result == 0:
                self.appk_idx = rsp.appkey_index
                logger.info("Success, appkey id = %x" % self.appk_idx)
            else:
                logger.info(
                    "Failed to create new appkey, result = %x" % rsp.result)

            if rsp.result:
                logger.info("Unexpected return value!")
                self.trigger.emit("unexpected_error_message", rsp.result)

        return None
    
    @staticmethod
    def decode_dcd(evt):
        logger.info('DCD: Company ID = %x, Product ID = %x' %
                    (evt.cid, evt.pid))
        # Element Data.Format:
        # [Location(uint16), SIG Model Count (uint8), Vendor Model Count(uint8),
        # [SIG Models(uint16)], [Vendor Models(uint32)]]
        logger.info("Num of Elements = %d, Number of Models = %d" %
                    (evt.elements, evt.models))

        elements_cnt = evt.elements
        # models_cnt = evt.models

        element_data = evt.element_data
        # format [elements_cnt,[location, sig_cnt, vendor_cnt, [sig models], [vendor models]],......]
        element_list = []
        element_list.append(elements_cnt)

        for i in range(elements_cnt):
            location = struct.unpack("<1H", element_data[0:2])

            sig_cnt = ord(element_data[2])
            vendor_cnt = ord(element_data[3])
            logger.debug("SIG Models count = %d, Vendor Models count = %d" % (
                sig_cnt, vendor_cnt))
            # pack_format = str(sig_cnt) + 'H'  # num of SIG models, uint16
            pack_format = str(sig_cnt) + 'H'
            sig_models = list(struct.unpack("<%s" %
                                            pack_format, element_data[4:4+sig_cnt*2]))
            # sig_models.extend(struct.unpack("<%s" % pack_format, element_data[4:4+sig_cnt*2]))

            # pack_format = str(vendor_cnt) + 'I'  # num of vendors models, uint32
            pack_format = str(vendor_cnt) + 'I'
            vendor_models = list(struct.unpack(
                "<%s" % pack_format, element_data[4 + sig_cnt*2:4 + sig_cnt*2 + vendor_cnt*4]))

            element_list.append(
                [location, sig_cnt, vendor_cnt, sig_models, vendor_models])

            element_data = element_data[4 + sig_cnt*2 + vendor_cnt*4:]

            for x in range(len(sig_models)):
                logger.info("SIG Model ID: 0x%4.4x" % sig_models[x])
            for x in range(len(vendor_models)):
                logger.info("Vendor Model ID: 0x%x" % vendor_models[x])

        return element_list

    def parse_mesh_beacon(self, evt):
        # logger.debug('oob_capabilities = %s, uri_hash = %x, bearer = %x, address = %s, address_type = %x, uuid = %s' %
        #     (evt.oob_capabilities, evt.uri_hash, evt.bearer, evt.address, evt.address_type, evt.uuid))

        node = [evt.address, evt.uuid]
        if self.scan_state and (self.mesh_nodes.count(node) == 0):
            self.mesh_nodes.append(node)
            node = [evt.address, evt.uuid, 'rssi']
            self.trigger.emit("unprov_node_info", node)
            logger.debug("emit the unprov node info " + evt.address + ', ' + evt.uuid)            
        return

    # # Scan all un-provisioned mesh beacons.
    # def scan_mesh_beacon(self, evt):
    #     # Screen rssi < 50 device
    #     if evt.rssi < -50:
    #         return
    #     # ADV data: adv_len, adv_type, data(adv_len-1)
    #     data_len = len(evt.data)
    #     i = 0
    #     while data_len > i:
    #         adv_len = ord(evt.data[i])
    #         adv_type = ord(evt.data[i + 1])
    #         if adv_type == 0x16:  # 16-bit UUID
    #             ser_uuid = evt.data[(i+2):(i+4)]  # Service UUID 0x1827
    #             # logger.info(ser_uuid.encode('hex'))
    #             if ser_uuid.encode('hex') == "2718":  # Mesh Provisioning Service
    #                 dev_uuid = evt.data[(i + 4):(i + adv_len - 1)]  # device UUID, remove two bytes OOB
    #                 # Only add device not in the mesh beacon list
    #                 node = [evt.address, dev_uuid]
    #                 if self.mesh_nodes.count(node) == 0:
    #                     self.mesh_nodes.append(node)
    #                     node = [evt.address, dev_uuid, evt.rssi]
    #                     self.trigger.emit("unprov_node_info", node)
    #             elif ser_uuid.encode('hex') == "2818":  # Mesh Proxy Service
    #                 adv_type = evt.data[i+4:-1]
    #                 logger.info(repr(adv_type))
    #         i = i + adv_len + 1
    #     return

    # start_scan - @param: report interval
    def start_scan(self):
        logger.info('Start scanning')
        self.mesh_nodes = []
        # Scanning now
        self.scan_state = True

        rsp = self.dev.mesh_prov.scan_unprov_beacons()
        logger.info("result = %x" % rsp.result)

        if rsp.result:
            logger.info("Unexpected return value!")
            self.trigger.emit("unexpected_error_message", rsp.result)

    # stop_scan - @param: none
    def stop_scan(self):
        logger.info('Currently, no API to stop scanning')
        # Stop scanning. Because there is no API to stop scanning, so just control it with a variable.
        self.scan_state = False

    # provision_device - @param: device UUID without '0x' prefix
    def provision_device(self, mac, uuid):
        # logger.info(uuid)
        logger.info("Start to provision the device mac: %s" % mac)
        self.prov_uuid = uuid
        # Cal cmd_le_gap_connect to connect an advertising device with the specified initating PHY.
        # Address type: Public
        # Initiating PHY: LE 1M PHY
        rsp = self.dev.le_gap.connect(
            mac, LeGapAddressType.public, LeGapPhyType.phy_1m)

        logger.debug("result = %x" % rsp.result)
        if rsp.result == 0:
            self.connection_handle = rsp.connection

            # The provisioning may fail, create a timer which be triggered 5s later to check if
            # the provisioning finished or not.
            # If didn't finish the provisioning, retry the provisioning.
            # Close the connection and re-open the connection again, then the script will try to
            # finish the provisioning automatically.

            # timer argument, args[mac address, address_type, initiating_phy, connection_handle]
            # keyword arguements {"eventType":EventTimerType.t_provision_gatt_device}
            self.eventTimer = Timer(PROVISION_RETRY_INTERVAL,
                                    self.event_timer_handle,
                                    [mac, uuid, LeGapAddressType.public,
                                        LeGapPhyType.phy_1m, self.connection_handle],
                                    {"eventType": EventTimerType.t_provision_gatt_device})
            self.eventTimer.start()

        if rsp.result:
            logger.info("Unexpected return value!")
            self.trigger.emit("unexpected_error_message", rsp.result)
        # rsp = self.dev.mesh_prov.provision_device(self.nwk_idx, uuid)
        # logger.debug("result = %x" % rsp.result)

    def add_dcd(self, node_addr, ele_addr, model, pub_addr, sub_addr):
        self.pub.append([node_addr, ele_addr, model, 0xFFFF, pub_addr])
        self.sub.append([node_addr, ele_addr, model, 0xFFFF, sub_addr])
        self.bind.append([node_addr, ele_addr, model, 0xFFFF])

    # grp: ctrl addr, status addr, [mac addr, uuid, node addr], [models]
    def del_node_from_group(self, node_addr):
        logger.info("delete node from group")
        rsp = self.dev.mesh_prov.appkey_delete(
            node_addr, self.nwk_idx, self.appk_idx)
        if rsp.result == 0:
            logger.info("Delete app key on the node %x successed" % node_addr)
        else:
            logger.info("Delete app key on the node %x failed" % node_addr)

        if rsp.result:
          logger.info("Unexpected return value!")
          self.trigger.emit("unexpected_error_message", rsp.result)

        return

    # grp: ctrl addr, status addr, [mac addr, uuid, node addr, sig_models]
    def add_node_to_group(self, data):
        self.pub = []  # node_addr, model, 0xFFFF, pub_addr
        self.sub = []  # node_addr, model, 0xFFFF, sub_addr
        self.bind = []  # node_addr, model, 0xFFFF

        ctrl_grp = data[0]  # control group address
        stat_grp = data[1]  # status group address

        # node information format from GUI
        # [Mac_address, UUID, Node_address, netkeyIdx, appkeyIdx, element_data]
        # element_data [elements_cnt, [location, sig_cnt, vendor_cnt, [sig models], [vendor models]], [...], [...], ...]
        node = data[2]

        node_addr = node[2]  # get node addr
        ele_addr = node[3]
        models = node[4]  # sig model, sig model,...

        # self.eventTimer = Timer(RETRY_ADD_TO_GROUP_TIMERS,
        #                              self.event_timer_handle,
        #                              [data],
        #                              {"eventType":EventTimerType.t_add_to_group})
        # self.eventTimer.start()

        for model_id in models:
            if model_id in mesh_client_models:
                # As a client model, it should publish to the ctrl group, and subscribe the stat group
                self.add_dcd(node_addr, ele_addr, model_id, ctrl_grp, stat_grp)
            elif model_id in mesh_server_models:
                # As a server model, it should publish to the stat group, and subscribe the ctrl group
                self.add_dcd(node_addr, ele_addr, model_id, stat_grp, ctrl_grp)

            # if model_id == SWITCH_ID:    # 0x1001
            #     # As a switch, it should publish to the ctrl group, and subscribe the stat group
            #     # As a client model, it should publish to the ctrl group, and subscribe the stat group
            #     self.add_dcd(node_addr, model_id, light_ctrl_grp, light_stat_grp)
            # elif model_id == DIM_SWITCH_ID:  # 0x1302
            #     self.add_dcd(node_addr, model_id, light_ctrl_grp, light_stat_grp)
            #     # As a light, it should publish to the stat group, and subscribe the ctrl group
            #     # As a server model, it should publish to the stat group, and subscribe the ctrl group
            # elif model_id == LIGHT_ID:   # 0x1000
            #     self.add_dcd(node_addr, model_id, light_stat_grp, light_ctrl_grp)
            # elif model_id == DIM_LIGHT_ID:   # 0x1300
            #     self.add_dcd(node_addr, model_id, light_stat_grp, light_ctrl_grp)

        rsp = self.dev.mesh_prov.appkey_add(
            node_addr, self.nwk_idx, self.appk_idx)
        if rsp.result == 0:
            logger.info("App key deployed to address %x" % node_addr)
            self.state = STATE_BIND
        else:
            logger.info("App key deployed to address %x failed" % node_addr)

        if rsp.result:
            logger.info("Unexpected return value!")
            self.trigger.emit("unexpected_error_message", rsp.result)

        return

    def handle_config_status(self, evt):
        global node_address
        global sub_address

        logger.info("addr = 0x%x, id = 0x%x, status = 0x%x, data=%s" %
                    (evt.address, evt.id, evt.status, str(evt.data)))

        if evt.id == MeshNodeConfigState.mesh_node_gatt_proxy:
            logger.info("GATT proxy state address 0x%x 0x%x status = 0x%x raw data = %s" % (
                evt.address, evt.id, evt.status, evt.data))
            self.trigger.emit("set_proxy_done", [
                              evt.address, evt.id, evt.status, evt.data])
            return
        elif evt.id == MeshNodeConfigState.mesh_node_friendship:
            logger.info("Configure friendship done 0x%x 0x%x status = 0x%x raw data = %s" % (
                evt.address, evt.id, evt.status, evt.data))
            self.trigger.emit("set_friendship_done", [
                              evt.address, evt.id, evt.status, evt.data])
            return

        # # Cheng add it, no reference manual address it
        elif evt.id == MeshNodeConfigState.mesh_node_appkey_delete:
            logger.info("Delete app key on the node 0x%x successed, id = 0x%x status = 0x%x raw data = %s" % (
                evt.address, evt.id, evt.status, evt.data))
            self.trigger.emit("del_node_from_group_done", [
                              evt.address, evt.id, evt.status, evt.data])
            return

        if self.state == STATE_BIND:
            val = self.bind.pop()
            logger.info("Binding Model 0x%4.4x" % val[2])
            rsp = self.dev.mesh_prov.model_app_bind(val[0],  # Node addr
                                                    val[1],  # Element addr
                                                    self.nwk_idx,
                                                    self.appk_idx,
                                                    val[3],  # VID
                                                    val[2])  # Model

            logger.debug("result = %x" % rsp.result)

            if rsp.result:
                logger.info("Unexpected return value!")
                
            if rsp.result == 0x181:
                logger.info("Retry to bind a model to an application key.")
                time.sleep(3)
                rspx = self.dev.mesh_prov.model_app_bind(val[0],  # Node addr
                                                        val[1],  # Element addr
                                                        self.nwk_idx,
                                                        self.appk_idx,
                                                        val[3],  # VID
                                                        val[2])  # Model                

                logger.debug("result = 0x%x" % rspx.result)
                if rspx.result:
                    logger.info("Unexpected return value!")
                    self.trigger.emit("unexpected_error_message", rspx.result)                    

            if len(self.bind) == 0:
                self.state = STATE_PUB
        elif self.state == STATE_PUB:
            val = self.pub.pop()
            logger.info("Pub set Model 0x%4.4x in GRP 0x%4.4x" %
                        (val[2], val[4]))
            rsp = self.dev.mesh_prov.model_pub_set(val[0],  # Node addr
                                                   val[1],  # Element addr
                                                   self.nwk_idx,
                                                   self.appk_idx,
                                                   val[3],  # VID
                                                   val[2],  # Model
                                                   val[4],  # Grp addr
                                                   3,
                                                   0,
                                                   0)
            logger.debug("result = 0x%x" % rsp.result)
            if rsp.result:
                logger.info("Unexpected return value!")

            if rsp.result == 0x181:
                logger.info("Retry to set the model's publication address, key, and parameters.")
                time.sleep(3)
                rspx = self.dev.mesh_prov.model_pub_set(val[0],  # Node addr
                                       val[1],  # Element addr
                                       self.nwk_idx,
                                       self.appk_idx,
                                       val[3],  # VID
                                       val[2],  # Model
                                       val[4],  # Grp addr
                                       3,
                                       0,
                                       0)
                logger.debug("result = 0x%x" % rspx.result)
                if rspx.result:
                    logger.info("Unexpected return value!")
                    self.trigger.emit("unexpected_error_message", rspx.result)                
               
            if len(self.pub) == 0:
                self.state = STATE_SUB
        elif self.state == STATE_SUB:
            val = self.sub.pop()
            logger.info("Subscription Model 0x%4.4x in GRP 0x%4.4x" %
                        (val[2], val[4]))
            rsp = self.dev.mesh_prov.model_sub_add(val[0],  # Node addr
                                                   val[1],  # Element addr
                                                   self.nwk_idx,
                                                   val[3],  # VID
                                                   val[2],  # Model
                                                   val[4])  # Grp addr
            logger.debug("result = %x" % rsp.result)

            if rsp.result:
                logger.info("Unexpected return value!")
                self.trigger.emit("unexpected_error_message", rsp.result)
                
            if rsp.result == 0x181:
                logger.info("Retry to add an address to a model's subscription list.")
                time.sleep(3)
                rspx = self.dev.mesh_prov.model_sub_add(val[0],  # Node addr
                                                   val[1],  # Element addr
                                                   self.nwk_idx,
                                                   val[3],  # VID
                                                   val[2],  # Model
                                                   val[4])  # Grp addr

                logger.debug("result = 0x%x" % rspx.result)
                if rspx.result:
                    logger.info("Unexpected return value!")
                    self.trigger.emit("unexpected_error_message", rspx.result)                  

            if len(self.sub) == 0:
                node_address = val[0]  # node address
                sub_address = val[4]  # subscription address
                self.state = STATE_NONE
        # elif self.state == STATE_CONFIG:
            # logger.info(repr(evt.data))
            # self.dev.mesh_prov.get_dcd(evt.address, 0xFF)
            # self.statue = STATE_NONE
        elif self.state == STATE_NONE:
            self.trigger.emit("add_node_to_group_done", [
                              node_address, sub_address])

    # prt_dt - @brief: print device table. @param: none
    # prt_gt - @brief: print group (pub/sub) table. @param: none
    # add_idx - @param: device index in scan report
    # sub_add - @param: 0 - device addr, 1 - model id, 2 - sub addr
    # pub_set - @param: 0 - device addr, 1 - model id, 2 - pub addr

    def remote_get(self, data):
        # data format [mode_id, elem_index, server_address, state_type]
        logger.info(data)
        
        # Get the relay status
        # data format [node address, netkey_idx]
        rsp = self.dev.mesh_prov.relay_set(data[0],
                                           data[1])
        logger.debug("result = %x" % rsp.result)

        rsp = self.dev.mesh_generic_client.get(data[0],
                                               data[1],
                                               data[2],
                                               self.appk_idx,
                                               data[3])
        logger.debug("result = %x" % rsp.result)

        if rsp.result:
            logger.info("Unexpected return value!")
            self.trigger.emit("unexpected_error_message", rsp.result)

    def remote_set(self, data):
        # data format [mode_id, elem_index, server_address, tid, transition, delay, flags, type, parameters]
        logger.info(data)
        
        rsp = self.dev.mesh_generic_client.init()
        logger.debug("result = %x" % rsp.result)
        
        rsp = self.dev.mesh_generic_client.set(data[0],
                                               data[1],
                                               data[2],
                                               self.appk_idx,
                                               data[3],
                                               data[4],
                                               data[5],
                                               data[6],
                                               data[7],
                                               data[8])
        logger.debug("result = %x" % rsp.result)

        if rsp.result:
            raise Exception("Unexpected return value!")

    def set_proxy(self, data):
        rsp = self.dev.mesh_prov.set_config(
            data[0], MeshNodeConfigState.mesh_node_gatt_proxy, self.nwk_idx, data[1])
        logger.debug("result = %x" % rsp.result)

        if rsp.result:
            raise Exception("Unexpected return value!")

    def set_friendship(self, data):
        rsp = self.dev.mesh_prov.set_config(
            data[0], MeshNodeConfigState.mesh_node_friendship, self.nwk_idx, data[1])
        logger.debug("result = %x" % rsp.result)

        if rsp.result:
            raise Exception("Unexpected return value!")

    def set_relay(self, data):
        # data format [node address, netkey_idx, relay, count, interval]
        rsp = self.dev.mesh_prov.relay_set(data[0],
                                           data[1],
                                           data[2],
                                           data[3],
                                           data[4])
        logger.debug("result = %x" % rsp.result)

        if rsp.result:
            raise Exception("Unexpected return value!")

    # factory_reset - @param: none
    def factory_reset(self, data):
        # data format [node address, uuid]
        logger.info("Factory Reset Node Address: %x uuid = %s" % (data[0], data[1]))

        # Clear the ddb list
        self.ddb_list = []
        # Cheng debug
        rsp = self.dev.mesh_prov.ddb_list_devices()
        logger.debug("result = %x" % rsp.result)

        rsp = self.dev.mesh_prov.reset_node(
            data[0], self.nwk_idx)  # Node addr, Network key index
        logger.debug("result = %x" % rsp.result)

        if rsp.result:
          logger.info("Unexpected return value!")
          self.trigger.emit("unexpected_error_message", rsp.result)

        self.eventTimer = Timer(FACTORY_RESET_INTERVAL,
                                self.event_timer_handle,
                                [data[0], data[1], self.nwk_idx],
                                {"eventType": EventTimerType.t_factory_reset})
        self.eventTimer.start()

        # pass

    def prov_dev_reset(self):
        self.lib.open()
        self.dev.system.reset(0)
        time.sleep(1)

    def reset_ncp(self):
        self.dev.flash.ps_erase_all()
        self.dev.system.reset(0)
        time.sleep(1)
        # self.dev.system.hello()

    def send_command(self, cmd, data):
        self.cmd_queue.put((cmd, data))

    # Handle all of the commands from GUI
    def cmd_handler(self):
        cmd, data = self.cmd_queue.get()
        if cmd == 'cmd_start_scan':
            self.start_scan()
        elif cmd == 'cmd_stop_scan':
            self.stop_scan()
        elif cmd == 'cmd_provision_device':
            self.node_info = []
            # self.node_info.append(data[0])  # get mac address
            # self.provision_device(data[0], data[1])
            self.node_info.append(data['Mac_address'])  # get mac address
            self.provision_device(data['Mac_address'], data['UUID'])
        elif cmd == 'cmd_add_node_to_group':
            self.add_node_to_group(data)
        elif cmd == 'cmd_del_node_from_group':
            self.del_node_from_group(data)
        elif cmd == 'cmd_factory_reset':
            self.factory_reset(data)
        elif cmd == 'cmd_set_relay':
            self.set_relay(data)
        elif cmd == 'cmd_set_proxy':
            self.set_proxy(data)
        elif cmd == 'cmd_set_friendship':
            self.set_friendship(data)
        elif cmd == 'cmd_remote_set':
            self.remote_set(data)
        elif cmd == 'cmd_remote_get':
            self.remote_get(data)

    def exit(self):
        self.lib.close()

# class BleMeshGui(QtGui.QMainWindow):
#     def __init__(self, parent=None):
#         super(BleMeshGui, self).__init__(parent)
#         self.text_area = QtGui.QTextBrowser()
#
#         self.scan_button = QtGui.QPushButton('Scan Devices')
#         self.provision_button = QtGui.QPushButton('Provision')
#         self.create_group_button = QtGui.QPushButton('Create Group')
#         self.join_group_button = QtGui.QPushButton('Join Group')
#         self.del_from_group_button = QtGui.QPushButton('Del from Group')
#         self.factory_reset_button = QtGui.QPushButton('Factory Reset')
#         self.set_relay_button = QtGui.QPushButton('Enable Relay')
#         self.set_proxy_button = QtGui.QPushButton('Enable Proxy')
#         self.set_friendship_button = QtGui.QPushButton('Enable Friendship')
#         self.remote_set_button = QtGui.QPushButton('Turn on light')
#         self.remote_get_button = QtGui.QPushButton('Get light status')
#
#         self.scan_button.clicked.connect(self.gui_scan_device)
#         self.provision_button.clicked.connect(self.gui_provision_device)
#         self.create_group_button.clicked.connect(self.gui_create_group)
#         self.join_group_button.clicked.connect(self.gui_join_group)
#         self.del_from_group_button.clicked.connect(self.gui_del_node_from_group)
#         self.factory_reset_button.clicked.connect(self.gui_factory_reset_node)
#         self.set_relay_button.clicked.connect(self.gui_set_relay)
#         self.set_proxy_button.clicked.connect(self.gui_set_proxy)
#         self.set_friendship_button.clicked.connect(self.gui_set_friendship)
#         self.remote_set_button.clicked.connect(self.gui_remote_set)
#         self.remote_get_button.clicked.connect(self.gui_remote_get)
#
#         central_widget = QtGui.QWidget()
#         self.setCentralWidget(central_widget)
#
#         button_group = QtGui.QGroupBox(central_widget)
#         button_layout = QtGui.QVBoxLayout()
#         button_layout.addWidget(self.scan_button)
#         button_layout.addWidget(self.provision_button)
#         button_layout.addWidget(self.create_group_button)
#         button_layout.addWidget(self.join_group_button)
#         button_layout.addWidget(self.del_from_group_button)
#         button_layout.addWidget(self.factory_reset_button)
#         button_layout.addWidget(self.set_relay_button)
#         button_layout.addWidget(self.set_proxy_button)
#         button_layout.addWidget(self.set_friendship_button)
#         button_layout.addWidget(self.remote_set_button)
#         button_layout.addWidget(self.remote_get_button)
#         button_group.setLayout(button_layout)
#
#         central_layout = QtGui.QHBoxLayout()
#         central_layout.addWidget(self.text_area)
#         central_layout.addWidget(button_group)
#
#         central_widget.setLayout(central_layout)
#
#         self.setWindowTitle("BLE Mesh Tool")
#         self.setFixedSize(1000, 600)
#
#         font = QtGui.QFont('Courier New', 10)
#         font.setFixedPitch(1)
#         self.setFont(font)
#
#         self.ncp = MeshNCPThread(self)
#         self.ncp.trigger.connect(self.update_text)
#         self.ncp.start()
#
#         self.scan_state = 0
#         self.remote_set_state = 0
#
#         # All of the lists be used to stored the unicast address of the nodes.
#         # For GUI case, the address be transfer from GUI.
#         self.unprov_nodes = []  # mac address, uuid.
#         self.prov_nodes = []  # mac addr, uuid, node addr, [models]
#         self.node_addr = []
#         self.relay_node_addr = []
#         self.factory_reset_node_addr = []
#         self.remote_server_addr = []
#         self.proxy_node_addr = []
#         self.friendship_addr = []
#         self.del_from_group_addr = []
#
#         self.mesh_groups = []  # name, ctrl addr, status addr, [node], [node], ...
#         self.grp_addr = 0xC000
#
#     def gui_scan_device(self):
#         # if self.scan_state == 0:
#         #     self.scan_state = 1
#             # self.scan_button.setText("Stop Scan")
#         self.ncp.send_command("cmd_start_scan", [])
#         # else:
#         #     self.scan_state = 0
#         #     self.scan_button.setText("Scan Devices")
#         #     self.ncp.send_command("stop_scan", [])
#
#     def gui_provision_device(self):
#         if len(self.unprov_nodes) == 0:
#             # self.text_area.append('No unprovisioned device found!')
#             return
#         node = self.unprov_nodes.pop()
#         # data format [mac addr, uuid, node address]
#         # print 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
#         # print node
#         self.ncp.send_command("cmd_provision_device", node)
#         # The mesh_prov_scan_unprov_beacons will be stopped while start mesh_prov_provision_device
#         # self.scan_state = 0
#
#     def gui_factory_reset_node(self):
#         if len(self.factory_reset_node_addr) == 0:
#             return
#         addr = self.factory_reset_node_addr.pop()
#         self.ncp.send_command("cmd_factory_reset",[addr])
#         # self.text_area.append("Nodes Factory Reset")
#
#     def gui_set_relay(self):
#         if len(self.relay_node_addr) == 0:
#             return
#         addr = self.relay_node_addr.pop()
#         # node = [addr, 0x01, 7, 5]
#         node = [addr, 0x0, 7, 5]
        # data format [node address, netkey_idx, relay, count, interval]
#         self.ncp.send_command("cmd_set_relay",node)
#         # self.text_area.append("set relay" + str(node))
#
#     def gui_set_proxy(self):
#         if len(self.proxy_node_addr) == 0:
#             return
#         addr = self.proxy_node_addr.pop()
#         self.ncp.send_command("cmd_set_proxy", addr)
#
#     def gui_set_friendship(self):
#         if len(self.friendship_addr) == 0:
#             return
#         addr = self.friendship_addr.pop()
#         self.ncp.send_command("cmd_set_friendship", addr)
#
#
#     def gui_remote_get(self):
#         for i in range(len(self.remote_server_addr)):
#             mode_id = 0x1001        # mode_id depend on, it is 0x1001 if need on/off
#             elem_index = 0
#             server_address = self.remote_server_addr[i]
#             state_type = 0
#
#             node = [mode_id, elem_index, server_address, state_type]
#             self.ncp.send_command("cmd_remote_get", node)
#
#
#     def gui_remote_set(self):
#         if self.remote_set_state == 0:
#             self.remote_set_state = 1
#             self.remote_set_button.setText("Turn off light")
#         else:
#             self.remote_set_state = 0
#             self.remote_set_button.setText("Turn on light")
#
#         for i in range(len(self.remote_server_addr)):
#             mode_id = 0x1001        # mode_id depend on, it is 0x1001 if need on/off
#             elem_index = 0
#             server_address = self.remote_server_addr[i]
#             tid = 0
#             transition = 0
#             delay = 0
#             flags = 0      #If nonzero client expects a response from the server
#             rsq_type = 0
#
#             if self.remote_set_state == 0:
#                 parameters = '\x00\x01'   #length data
#             else:
#                 parameters = '\x01\x00'   #length data
#
#             node = [mode_id, elem_index, server_address, tid, transition, delay, flags, rsq_type, parameters]
#             self.ncp.send_command("cmd_remote_set", node)
#
#     def nodes_list(self):
#         for i in range(len(self.prov_nodes)):
#             node = self.prov_nodes[i]
#             self.text_area.append(str(node))
#
#     def gui_create_group(self):
#         name = 'Livingroom'
#         for val in self.mesh_groups:
#             if val[0] == name:
#                 logger.info("Group exist")
#                 return
#         grp = [name, self.grp_addr, self.grp_addr + 1]
#         self.grp_addr += 2
#         self.mesh_groups.append(grp)  # group name, ctrl addr, status addr
#
#         self.text_area.append("Create Livingroom")
#
#     def gui_join_group(self):
#         name = 'Livingroom'
#         if len(self.mesh_groups) == 0:
#             self.text_area.append("There is no group!")
#             return
#         if len(self.prov_nodes) == 0:
#             return
#         node = self.prov_nodes.pop()
#         for i in range(len(self.mesh_groups)):
#             if self.mesh_groups[i][0] == name:  # Checking name
#                 self.mesh_groups[i].append(node)
#                 self.ncp.send_command("cmd_add_node_to_group", [self.mesh_groups[i][1],  # Ctrl
#                                                      self.mesh_groups[i][2],  # Status
#                                                      node])
#                 self.text_area.append(str(self.mesh_groups[i]))
#                 return
#
#     def gui_del_node_from_group(self):
#         # del node from group
#         if len(self.del_from_group_addr) == 0:
#             return
#         addr = self.del_from_group_addr.pop()
#         self.ncp.send_command("cmd_del_node_from_group", addr)
#
#     def update_text(self, message, data):
#         if message == 'unprov_node_info':  # mac address, UUID, rssi
#             self.unprov_nodes.append([data[0], data[1]])
#             self.text_area.append(data[0] + ', ' + data[1].encode('hex') + ', ' + str(data[2]))
#         elif message == 'prov_node_info':  # mac addr, uuid, node addr, [models]
#             self.node_addr.append(data[2])
#
#             # temp solution for serial process in the cmd script,gui should handle which node should be reset or relay
#             self.relay_node_addr.append(data[2])
#             self.factory_reset_node_addr.append(data[2])
#             self.proxy_node_addr.append(data[2])
#             self.friendship_addr.append(data[2])
#             self.del_from_group_addr.append(data[2])
#
#             # cheng, temp test, control either onoff or lightness, do not control at the same time
#             if (LIGHT_ID in data[3]): #or (DIM_LIGHT_ID in data[3]):
#                 self.remote_server_addr.append(data[2])
#             # ------------------------------------------------------
#
#             self.prov_nodes.append(data)
#             self.text_area.append(str(data))
#             self.gui_provision_device()
#         elif message == 'add_node_to_group_done':  # node address
#             # self.text_area.append(str(data) + 'Joined the living room.')
#             self.text_area.append(str(data) + 'Joined the living room.')
#             self.gui_join_group()
#
#         elif message == 'del_node_from_group_done':
#             self.text_area.append(str(data) + 'Del app key successed.')
#             self.gui_del_node_from_group()
#
#         elif message == 'factory_reset_done':
#             self.text_area.append(str(data) + ' factory reset done')
#             self.gui_factory_reset_node()
#
#         elif message == 'set_relay_info':
#             self.text_area.append('relay status' + str(data))
#             self.gui_set_relay()
#         elif message == 'set_proxy_done':
#             self.text_area.append('proxy status' + str(data))
#         elif message == 'set_friendship_done':
#             self.text_area.append('friend status' + str(data))
#         elif message == 'client_server_status':
#             self.text_area.append('status' + str(data))
#
#
# # Main Function
# if __name__ == '__main__':
#     app = QtGui.QApplication(sys.argv)
#     mainWin = BleMeshGui()
#     mainWin.show()
#     os._exit(app.exec_())
