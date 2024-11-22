import cv2
import os

from camera.HodorCamera import HodorCamera
from common.Status import Status
from control.MotorControl import MotorControl
from core.KineticMapEntity import KineticMapEntity
from detection.HodorTagDetector import HodorTagDetector
from scanner.HodorScanner import HodorScanner
from settings.HodorSettings import HodorSettings


class Hodor(KineticMapEntity):
    def __init__(self, settings: HodorSettings):

        self.settings = settings
        self.motor_control = MotorControl(settings)

        super().__init__(self.motor_control)

        self.camera = None
        self.video_device_id = settings.video_device_id
        self.frame_width = settings.video_frame_width
        self.frame_height = settings.video_frame_height
        self.enable_gui = settings.video_enable_gui

        self.tag_size = settings.tag_size
        self.tag_family = settings.tag_family
        self.tag_detector: HodorTagDetector | None = None

        self.__status = Status.INITIALIZING

        print("""##############################################\n
                ####           HODOR ft. VI23            #####\n
                ##############################################""")

    def setup(self):
        self.camera = HodorCamera(self.settings)

        if os.path.exists("calibration.json"):
            self.camera.load_calibration("calibration.json")
            print("[INFO] Calibración cargada")
        else:
            print("[ERR] calibration.json no encontrado. No es posible comenzar la rutina.")
            exit()

        # Inicializar detector de april tags
        self.tag_detector = HodorTagDetector(self.camera, self.tag_size, self.tag_family, enable_gui=self.enable_gui)

        print("[INFO] Inicialización finalizada")

    def loop(self):
        print("[INFO] Iniciando rutina")

        while True:
            while self.is_target_reached():
                self.stop()
                self.set_status(Status.TARGET_REACHED)

            # Encontrar base
            while not self.is_target_found():
                self.find_target()
                self.set_status(Status.FINDING_TARGET)

                if self.is_target_found():
                    self.stop()
                    self.set_status(Status.TARGET_FOUND)

            # Alinearse a la base
            while not self.is_aligned():
                self.set_status(Status.ALIGNING_TO_TARGET)
                self.align_to_target()

                if self.is_aligned():
                    self.stop()
                    self.set_status(Status.ALIGNED_TO_TARGET)

                # Si por algún motivo perdí visión de la base, suspendo la alineación y me detengo
                if not self.is_target_found():
                    self.stop()
                    self.set_status(Status.TARGET_LOST)
                    break

            # Si pierdo visión de la base dejo de moverme
            if not self.is_target_found():
                self.stop()
                self.set_status(Status.TARGET_LOST)
                continue

            # Moverse hacia la base
            self.move_towards_target()
            self.set_status(Status.MOVING_TOWARDS_TARGET)

        print("[INFO] Rutina finalizada")

    def set_status(self, status: Status):
        if self.__status == status:
            return

        self.__status = status
        print("[LOG] Status: " + str(status))

    def is_target_reached(self) -> bool:
        scan = HodorScanner.scan(self.tag_detector)

        if scan is None:
            return False

        return scan.distance <= self.settings.control_tolerance_linear

    def is_target_found(self) -> bool:
        return HodorScanner.scan(self.tag_detector) is not None

    def is_aligned(self) -> bool:
        scan = HodorScanner.scan(self.tag_detector)

        if scan is None:
            return False

        return abs(scan.angle) <= self.settings.control_tolerance_angular

    def find_target(self):
        self.turn_right()

    def align_to_target(self):
        angle = HodorScanner.scan(self.tag_detector).angle

        if angle < 0:
            self.turn_left()
        else:
            self.turn_right()

    def move_towards_target(self):
        self.move_forward()

    def cleanup(self):
        self.camera.close()
        cv2.destroyAllWindows()
