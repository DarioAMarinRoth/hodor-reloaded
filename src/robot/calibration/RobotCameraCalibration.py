import cv2
import numpy as np
import glob
import os
import json

from robot.settings.RobotSettings import RobotSettings


class RobotCameraCalibration:
    def __init__(self, settings: RobotSettings):
        self.__video_id = settings.video_device_id
        self.__video_capture = cv2.VideoCapture(settings.video_device_id)
        self.__video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, settings.video_frame_width)
        self.__video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.video_frame_height)
        self.__calibration_success = False
        self.__camera_matrix = None
        self.__dist_coeffs = None
        self.__rvecs = None
        self.__tvecs = None
        self.__fx = 0
        self.__fy = 0
        self.__cx = 0
        self.__cy = 0

    def close(self):
        self.__video_capture.release()

    def calibrate_from_scratch(self):
        self.__acquire_dataset__()
        self.__perform_calibration__()

    def calibrate_from_dataset(self):
        # TODO: dir path como parametro
        self.__perform_calibration__()

    def __acquire_dataset__(self):
        dataset_length = 20
        image_count = 0

        print("# -------------------------------------------------- #")
        print("# ----- Adquisición del dataset de calibración ----- #")
        print("# -------------------------------------------------- #")
        print("Presione 'p' para guardar el frame actual o 'q' para detener la adquisición")
        print("Nota: la adquisición se detendrá automáticamente después de {} adquisiciones".format(dataset_length))

        if not os.path.isdir('calibration_data'):
            os.mkdir('calibration_data')

        while image_count < dataset_length:
            ret, frame = self.__video_capture.read()

            cv2.imshow('Camera', frame)
            pressed_key = cv2.waitKey(1)

            if pressed_key == ord('p'):
                cv2.imwrite('./calibration_data/calibration-frame-{}.jpg'.format(image_count), frame)
                print('[INFO] Frame capturado')
                image_count += 1
                continue

            if pressed_key == ord('q'):
                print('[INFO] Adquisición detenida')
                break

    def __perform_calibration__(self):
        """"https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html"""

        # Dimensiones del tablero de ajedrez
        ROW_COUNT = 9
        COLUMN_COUNT = 6

        # 3d point in real world space
        world_points = []
        # 2d points in image plane.
        plane_points = []

        objp = np.zeros((ROW_COUNT * COLUMN_COUNT, 3), np.float32)
        objp[:, :2] = np.mgrid[0:ROW_COUNT, 0:COLUMN_COUNT].T.reshape(-1, 2)

        frame_img_paths = glob.glob('./calibration_data/*.jpg')

        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

        proper_calibration_frame_count = 0
        img_size = None

        for frame_img_path in frame_img_paths:
            img = cv2.imread(frame_img_path)
            img_grayscale = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            chessboard_found, corners = cv2.findChessboardCorners(img_grayscale, (ROW_COUNT, COLUMN_COUNT), None)

            if chessboard_found:
                proper_calibration_frame_count += 1
                world_points.append(objp)

                corners_acc = cv2.cornerSubPix(img_grayscale, corners, (11, 11), (-1, -1), criteria)
                plane_points.append(corners_acc)

                if not img_size:
                    img_size = img_grayscale.shape[::-1]

                img = cv2.drawChessboardCorners(img, (ROW_COUNT, COLUMN_COUNT),
                                                corners_acc, chessboard_found)
                cv2.imshow('Chessboard', img)
                cv2.waitKey(0)
            else:
                print("[WRN] Tablero no encontrado en imagen: {}".format(frame_img_path))

        cv2.destroyAllWindows()

        if proper_calibration_frame_count < 1:
            raise Exception("[ERR] No se encontraron suficientes frames adecuados para la calibración de la cámara")

        ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(world_points, plane_points, img_size,
                                                                            None, None)

        if not ret:
            raise Exception("[ERR] Ocurrió un error al realizar la calibración")

        self.__camera_matrix = camera_matrix
        self.__dist_coeffs = dist_coeffs
        self.__rvecs = rvecs
        self.__tvecs = tvecs

        self.__calibration_success = True

        self.__set_parameters_from_matrix__()

        print("[INFO] Calibración finalizada. Parámetros de cámara:")
        print("f: ({}, {})".format(self.__fx, self.__fy))
        print("c: ({}, {})".format(self.__cx, self.__cy))

    def save_calibration(self, file_path: str):
        if not self.__calibration_success:
            print(
                "[ERR] La cámara aún no ha sido calibrada, por lo tanto no se puede guardar su configuración de calibración")
            return

        calibration_data = {
            "camera_matrix": self.__camera_matrix.tolist(),
            "fx": self.__fx,
            "fy": self.__fy,
            "cx": self.__cx,
            "cy": self.__cy
        }

        json_calibration_data = json.dumps(calibration_data)

        with open(file_path, "w") as outfile:
            outfile.write(json_calibration_data)

        print("[INFO] Calibración {} guardada exitosamente".format(file_path))

    def __set_parameters_from_matrix__(self):
        self.__fx = self.__camera_matrix[0][0]
        self.__fy = self.__camera_matrix[1][1]
        self.__cx = self.__camera_matrix[0][2]
        self.__cy = self.__camera_matrix[1][2]
