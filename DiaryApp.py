import sys
import os
import cv2
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QTextEdit,
    QMainWindow,
    QDesktopWidget,
    QCalendarWidget,
)
from PyQt5.QtGui import QPixmap, QImage, QTextCharFormat, QIcon, QFontDatabase, QFont
from PyQt5.QtCore import QTimer, QUrl, Qt, QDate
from PyQt5.QtMultimedia import QAudioRecorder, QAudioEncoderSettings

selected_date = "20231127"


class DiaryFormApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.is_recording = False

        # =========== Widgets ===========
        # 사진(존재하면 해당 날짜 이미지/없으면 기본 이미지)
        self.image_label_img = QLabel()
        # if
        file_path = "./static/default_image.png"
        pixmap = QPixmap(file_path)
        pixmap = pixmap.scaledToWidth(400)
        self.image_label_img.setPixmap(pixmap)
        # 비디오
        self.image_label_video = QLabel()
        self.video_capture = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # 30ms마다 프레임 업데이트
        self.captured_image_path = None  #
        # 버튼들
        self.camera_button = QPushButton("사진촬영")
        self.camera_button.clicked.connect(self.capture_image)
        self.mic_button = QPushButton("음성 녹음 ●")
        self.mic_button.clicked.connect(self.toggle_recording)
        self.play_button = QPushButton("음성 재생 ▶")
        # - 파일유무에 따라 활성화처리
        self.play_button.setEnabled(False)
        self.trans_button = QPushButton("오디오 → 텍스트 변환")
        self.list_button = QPushButton("목록")
        self.save_button = QPushButton("오늘도 고생했어요 :)")
        # 캘린더
        self.calendar_widget = QCalendarWidget(self)
        self.calendar_widget.setVerticalHeaderFormat(0)  # vertical header 숨기기
        # - 일기쓴 날 표시
        fm = QTextCharFormat()
        fm.setForeground(Qt.blue)
        fm.setBackground(Qt.yellow)
        holidays = ["20231118", "20231126", "20231110", "20231105", "20231102"]
        for dday in holidays:
            dday2 = QDate.fromString(dday, "yyyyMMdd")
            self.calendar_widget.setDateTextFormat(dday2, fm)
        # 상태표시
        self.status_label = QLabel()
        # 텍스트에디터
        self.text_edit = QTextEdit()

        # ========== left vbox =========
        # 사진-미리보기-촬영버튼-녹음버튼-상태메세지표시
        left_vbox = QVBoxLayout()
        left_vbox.addWidget(self.image_label_img)
        left_vbox.addWidget(self.image_label_video)
        left_vbox.addWidget(self.camera_button)
        button_vbox = QHBoxLayout()
        button_vbox.addWidget(self.mic_button)
        button_vbox.addWidget(self.play_button)
        left_vbox.addLayout(button_vbox)
        left_vbox.addWidget(self.trans_button)
        left_vbox.addWidget(self.status_label)

        # ========== right vbox ==========
        # 일기목록캘린더-텍스트인풋-저장버튼
        right_vbox = QVBoxLayout()
        right_vbox.addWidget(self.calendar_widget)
        right_vbox.addWidget(self.text_edit)
        right_vbox.addWidget(self.save_button)

        # ========== outer hbox ==========
        hbox = QHBoxLayout()
        hbox.addLayout(left_vbox)
        hbox.addLayout(right_vbox)

        widget = QWidget()
        widget.setLayout(hbox)
        widget.setStyleSheet("background: white; color: #7743DB;")
        self.setCentralWidget(widget)

        # ========== 스타일시트 적용 ==========
        button_style = (
            "color: white; background: #C3ACD0; padding:10px; border-radius:4px;"
        )
        button_style_point = (
            "color: white; background: #7743DB; padding:10px; border-radius:4px;"
        )
        self.camera_button.setStyleSheet(button_style)
        self.mic_button.setStyleSheet(button_style)
        self.play_button.setStyleSheet(button_style)
        self.trans_button.setStyleSheet(button_style)
        self.list_button.setStyleSheet(button_style)
        self.save_button.setStyleSheet(button_style_point)
        self.text_edit.setStyleSheet(
            "color: black; background: #FFFBF5; padding:10px; border-radius:4px; border: 1px solid #C3ACD0"
        )
        # - 폰트 설정
        font_path = "./static/NotoSansKR-SemiBold.ttf"
        font_id = QFontDatabase.addApplicationFont(font_path)
        font_name = QFontDatabase.applicationFontFamilies(font_id)[0]
        custom_font = QFont(font_name)
        custom_font.setPointSize(11)  # 폰트 크기 설정
        self.camera_button.setFont(custom_font)
        self.mic_button.setFont(custom_font)
        self.play_button.setFont(custom_font)
        self.trans_button.setFont(custom_font)
        self.list_button.setFont(custom_font)
        self.save_button.setFont(custom_font)
        self.status_label.setFont(custom_font)
        self.text_edit.setFont(custom_font)
        self.calendar_widget.setFont(custom_font)
        # widget.setFont(custom_font)

        # ========== 창이름 및 사이즈 설정 ==========
        self.setWindowTitle("Face Diary")
        self.setWindowIcon(QIcon("./static/icon.png"))
        self.setGeometry(800, 900, 800, 900)
        self.center()
        self.show()

    # 화면의 가운데로 띄우기
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # ========== 기능1. 카메라 ==========
    # 미리보기
    def update_frame(self):
        ret, frame = self.video_capture.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            q_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            pixmap = pixmap.scaledToWidth(400)
            self.image_label_video.setPixmap(pixmap)

    # 캡쳐
    def capture_image(self):
        ret, frame = self.video_capture.read()
        if ret:
            file_name = f"img_{selected_date}.jpg"
            file_path = os.path.join("./data/img/", file_name)
            cv2.imwrite(file_path, frame)
            self.status_label.setText("이미지가 캡쳐되었습니다. " + file_name)

            # 이미지 띄우기
            pixmap = QPixmap(file_path)
            pixmap = pixmap.scaledToWidth(400)
            self.image_label_img.setPixmap(pixmap)

    # ========== 기능2. 오디오 ==========
    def toggle_recording(self):
        file_name = f"audio_{selected_date}.wav"
        file_path = os.path.join("./data/audio/", file_name)
        if not self.is_recording:
            self.audio_recorder = QAudioRecorder()
            audio_settings = QAudioEncoderSettings()
            audio_settings.setCodec("audio/pcm")
            self.audio_recorder.setAudioSettings(audio_settings)
            self.audio_recorder.setOutputLocation(QUrl.fromLocalFile(file_path))

            self.audio_recorder.record()
            self.is_recording = True
            self.status_label.setText("녹음 중 입니다.")
            self.mic_button.setText("녹음 중지 ■")
        else:
            self.audio_recorder.stop()
            self.is_recording = False
            self.status_label.setText("오디오가 저장되었습니다. " + file_name)
            self.mic_button.setText("음성 녹음 ●")
            self.play_button.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = DiaryFormApp()

    sys.exit(app.exec_())
