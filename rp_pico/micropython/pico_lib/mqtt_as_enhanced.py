import re
import uasyncio as asyncio

from .mqtt_as import MQTTClient, config
from .settings_base import Settings_Base
from .logging_enhanced import Logger_Enhanced
_logger =  Logger_Enhanced.get_logger_for_module(__name__) 

class _Wifi_Settings(Settings_Base):
    def __init__(self) -> None:
        super().__init__()
        self.ssid = ''
        self.password = ''

class _Mqtt_Settings(Settings_Base):
    def __init__(self) -> None:
        super().__init__()
        self.host = ''
        self.port = 1833
        self.use_clean_session = True
        self.use_ssl = False
        self.username = ''
        self.password = ''
        self.client_cert_file_path = ''
        self.private_key_file_path = ''

class MQTTClient_enhanced(MQTTClient):

    def __init__(self, app_settings_path = 'config/app_settings.json', app_secrets_path = 'secret/app_secrets.json'):
        self._app_settings_path = app_settings_path
        self._app_secrets_path = app_secrets_path
        self._connection_state_changed_handler = None
        self._connection_established_handler = None

        self._wifi_settings = _Wifi_Settings()
        self._wifi_settings.load(__name__, [app_settings_path, app_secrets_path], 'wifi')
        _logger.info(self._wifi_settings.get_settings_as_text(intro_text = f'Settings for mqtt/wifi:'))

        self._mqtt_settings = _Mqtt_Settings()
        self._mqtt_settings.load(__name__, [app_settings_path, app_secrets_path], 'mqtt')
        _logger.info(self._mqtt_settings.get_settings_as_text(intro_text = f'Settings for mqtt:'))

        # dict: subscribed topic (may include # and +) -> handler
        self._topic_to_handler = dict()
        # dict: subscribed topic (may include # and +) -> subscribed topic as regex (compiled)
        self._topic_to_regex = dict()

        # config[] is defined as global variable in mqtt_as, here we change only some values.
        config = self._init_config_of_mqtt_client()
        super().__init__(config)

    def _init_config_of_mqtt_client(self):
        wifi = self._wifi_settings
        mqtt = self._mqtt_settings
        config['ssid'] = wifi.ssid
        config['wifi_pw'] = wifi.password
        config['server'] = mqtt.host
        config['port'] = mqtt.port
        config['clean'] = mqtt.use_clean_session
        config['user'] = mqtt.username
        config['password'] = mqtt.password
        config['ssl'] = mqtt.use_ssl
        if mqtt.use_ssl:
            _logger.debug(f'Loading client certificate/key: {mqtt.client_cert_file_path}/{mqtt.private_key_file_path}.')
            with open(mqtt.client_cert_file_path, 'rb') as f:
                certData = f.read()
            with open(mqtt.private_key_file_path, 'rb') as f:
                keyData = f.read()
            _logger.info(f'Loaded client certificate/key: {mqtt.client_cert_file_path}/{mqtt.private_key_file_path}.')
            config['ssl_params'] = { 'do_handshake': True, 'key': keyData, 'cert': certData }
        # Register coroutines / callbacks
        config['wifi_coro'] = self._on_connection_state_changed
        config['connect_coro'] = self._on_connection_established
        config['subs_cb'] = self._on_message_received
        return config

    async def connect(self, check_connection = True):
        try:
            _logger.info('Connecting to broker ...')
            await super().connect(quick = check_connection)
        except BaseException as err:
            _logger.error(f"Exception while connecting to broker '{self._mqtt_settings.host}', port {self._mqtt_settings.port}. Exception: {err}, {type(err)}.")
            raise
        else:
            _logger.info(f"connect(): Connection to MQTT broker '{self._mqtt_settings.host}'', port {self._mqtt_settings.port} established.")

    def register_connection_state_changed_handler(self, handler):
        self._connection_state_changed_handler = handler
        _logger.info(f"Registered 'connection state changed handler': {handler.__name__}().")

    def register_connection_established_handler(self, handler):
        self._connection_established_handler = handler
        _logger.info(f"Registered 'connection established handler': {handler.__name__}().")

    def get_host(self):
        return self._mqtt_settings.host
    
    async def _on_connection_established(self, client):
        _logger.info(f"_on_broker_connected(): Connection to MQTT broker '{client.server}', port {client.port} established.")
        if self._connection_established_handler:
            await self._connection_established_handler(client)
        else:
            _logger.warning("No 'connection established handler' registered!")

    async def subscribe(self, topic, handler):
        _logger.info(f'Subscribing for topic \'{topic}\' ...')
        if topic in self._topic_to_handler:
            del self._topic_to_handler[topic]
            await super().unsubscribe(topic)
        self._topic_to_handler[topic] = handler
        self._topic_to_regex[topic] = self._compile_regex(topic)
        await super().subscribe(topic)

    def dprint(self, msg, *args):
        '''Override dprint() of MQTT_base class in module mqtt_as to use logger.'''
        if self.DEBUG:
            _logger.info('mqtt_as: ' + (msg % args))

    def _on_message_received(self, topic, msg, retained):
        try:
            _logger.info(f'Received message for topic: \'{topic.decode()}\' Message: \'{msg.decode()}\' Retained: {retained}')
            topic_patterns = self._find_matching_topic_patterns(topic.decode())
            if topic_patterns:
                for tp in topic_patterns:
                    handler = self._topic_to_handler[tp]
                    if handler:
                        _logger.debug(f'Calling subscription handler \'{handler.__name__}()\' for topic \'{topic.decode()}\' ...')
                        ret = handler(topic, msg, retained)
                        _logger.debug(f'Subscription handler \'{handler.__name__}()\' returned with \'{ret}\'.')
                    else:
                        _logger.error(f'Found no subscription handler topic for topic \'{topic.decode()}\'.')
            else:
                _logger.error(f'Found no subscription for topic \'{topic.decode()}\'.')
        except BaseException as err:
            _logger.error(f'_on_message_received(): Unexpected {err}, {type(err)}')

    async def _on_connection_state_changed(self, state):
        if state:
            _logger.info('Connection to MQTT broker is UP.')
        else:
            _logger.warning('Connection to MQTT broker is DOWN.')
        if self._connection_state_changed_handler:
            await self._connection_state_changed_handler(state)

    def _compile_regex(self, topic):
        topic_pattern = '^' + topic.replace('/', '\/').replace('+', r'[^\/]*').replace('#', '.*') + '$'
        _logger.debug(f'================>> Compiling topic_pattern regex \'{topic_pattern}\' ...')
        return re.compile(topic_pattern)

    def _find_matching_topic_patterns(self, topic):
        topic_patterns = []
        _logger.debug(f'================>> Searching matching topic_pattern(s) for topic \'{topic}\' in topic_patterns {self._topic_to_regex.keys()} ...')
        for topic_pattern in self._topic_to_regex:
            if self._topic_to_regex[topic_pattern].match(topic):
                topic_patterns.append(topic_pattern)
        _logger.debug(f'================>>     Found topic_pattern(s) {topic_patterns} for topic \'{topic}\'.')
        return topic_patterns
