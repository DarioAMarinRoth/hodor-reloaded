import json
import codecs
import os

from robot.console.RobotLogger import RobotLogger


class RobotSettings:
    def __init__(self):
        # Video
        self.video_device_id: int = 8
        self.video_frame_width: int = 1280
        self.video_frame_height: int = 720

        # April Tags
        self.tag_far_size: int = 120
        self.tag_far_id: int = 1
        self.tag_close_size: int = 60
        self.tag_close_id: int = 0
        self.tag_family: str = "tag36h11"
        self.tag_threshold_distance: int = 2000
        self.tag_threshold_sample_size: int = 5

        # Motors
        self.motor_enable_movement: bool = False
        self.motor_movement_threshold_distance: int = 1000

        # Control
        self.control_tolerance_linear: int = 400
        self.control_tolerance_angular: int = 10

        # Video Stream
        self.video_stream_enable: bool = False
        self.video_stream_ip: str = "0.0.0.0"
        self.video_stream_port: int = 8089
        self.video_compression_level: int = 90

    @staticmethod
    def read_from_file(file_path: str):
        settings = RobotSettings()

        if not os.path.exists(file_path):
            RobotLogger.warning(
                "No se pudo encontrar el archivo " + file_path + ". Se utilizará la configuración por defecto")
            return settings

        settings_json_str = codecs.open(file_path, 'r', encoding='utf-8').read()
        settings_json = json.loads(settings_json_str)

        # Video
        settings.video_device_id = settings_json["video"]["device_id"]
        settings.video_frame_width = settings_json["video"]["frame_width"]
        settings.video_frame_height = settings_json["video"]["frame_height"]

        # April Tags
        settings.tag_far_size = settings_json["tag"]["far_size"]
        settings.tag_far_id = settings_json["tag"]["far_id"]
        settings.tag_close_size = settings_json["tag"]["close_size"]
        settings.tag_close_id = settings_json["tag"]["close_id"]
        settings.tag_threshold_distance = settings_json["tag"]["threshold_distance"]
        settings.tag_threshold_sample_size = settings_json["tag"]["threshold_sample_size"]
        settings.tag_family = settings_json["tag"]["family"]

        # Motors
        settings.motor_enable_movement = settings_json["motor"]["enable_movement"]
        settings.motor_movement_threshold_distance = settings_json["motor"]["movement_threshold_distance"]

        # Control
        settings.control_tolerance_linear = settings_json["control"]["tolerance"]["linear"]
        settings.control_tolerance_angular = settings_json["control"]["tolerance"]["angular"]

        # Video Stream
        settings.video_stream_enable = settings_json["video_stream"]["enable"]
        settings.video_stream_ip = settings_json["video_stream"]["ip"]
        settings.video_stream_port = settings_json["video_stream"]["port"]
        settings.video_compression_level = settings_json["video_stream"]["compression_level"]

        RobotLogger.info(file_path + " cargado")

        return settings
