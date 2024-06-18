import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QVBoxLayout, QWidget, QPushButton, QSlider, QLabel, QHBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QCheckBox, QStyle, QLineEdit
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QGraphicsVideoItem
from PyQt5.QtCore import Qt, QTimer, QRectF, QUrl, QSizeF
from PyQt5.QtGui import QPen, QBrush, QIcon, QFontDatabase, QFont
from moviepy.editor import VideoFileClip, vfx

class VideoEditor(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('영상데이터 편집기 v1.0')
        self.setWindowIcon(QIcon('resources/faviconV2.jpg'))
        self.setGeometry(100, 100, 800, 600)

        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        
        self.graphicsView = QGraphicsView(self)
        self.scene = QGraphicsScene(self)
        self.graphicsView.setScene(self.scene)
        self.graphicsView.setFixedSize(800, 450)

        self.videoItem = QGraphicsVideoItem()
        self.videoItem.setSize(QSizeF(800, 450))
        self.scene.addItem(self.videoItem)
        self.mediaPlayer.setVideoOutput(self.videoItem)

        self.playButton = QPushButton('재생', self)
        self.playButton.setEnabled(False)
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playButton.clicked.connect(self.playVideo)

        self.pauseButton = QPushButton('일시정지', self)
        self.pauseButton.setEnabled(False)
        self.pauseButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        self.pauseButton.clicked.connect(self.pauseVideo)

        self.stopButton = QPushButton('정지', self)
        self.stopButton.setEnabled(False)
        self.stopButton.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stopButton.clicked.connect(self.stopVideo)

        self.openButton = QPushButton('폴더에서 가져오기', self)
        self.openButton.clicked.connect(self.openFile)

        self.saveButton = QPushButton('자르기', self)
        self.saveButton.setEnabled(False)
        self.saveButton.clicked.connect(self.saveCut)

        self.clearButton = QPushButton('지우기', self)
        self.clearButton.setEnabled(False)
        self.clearButton.clicked.connect(self.clearVideo)

        self.drawBoxCheckBox = QCheckBox('박스 그리기', self)
        self.drawBoxCheckBox.setChecked(True)
        self.drawBoxCheckBox.stateChanged.connect(self.toggleDrawBox)

        self.positionSlider = QSlider(Qt.Horizontal, self)
        self.positionSlider.setRange(0, 0)
        self.positionSlider.sliderMoved.connect(self.setPosition)

        self.currentTimeLabel = QLabel('0:00.0', self)
        self.totalTimeLabel = QLabel('0:00.0', self)
        self.fpsInfoLabel = QLabel('현재 영상의 FPS: N/A', self)  # FPS 정보를 표시할 레이블 추가

        self.fpsLabel = QLabel('FPS:', self)
        self.fpsInput = QLineEdit(self)
        self.fpsInput.setPlaceholderText('변환할 FPS 입력')
        self.convertButton = QPushButton('변환', self)
        self.convertButton.setEnabled(False)
        self.convertButton.clicked.connect(self.convertFPS)

        layout = QVBoxLayout()
        layout.addWidget(self.graphicsView, stretch=5)

        controlLayout = QHBoxLayout()
        controlLayout.addWidget(self.playButton)
        controlLayout.addWidget(self.pauseButton)
        controlLayout.addWidget(self.stopButton)
        controlLayout.addWidget(self.positionSlider)
        controlLayout.addWidget(self.currentTimeLabel)
        controlLayout.addWidget(self.totalTimeLabel)
        
        layout.addLayout(controlLayout)

        fpsLayout = QHBoxLayout()
        fpsLayout.addWidget(self.fpsLabel)
        fpsLayout.addWidget(self.fpsInput)
        fpsLayout.addWidget(self.convertButton)

        layout.addLayout(fpsLayout)
        layout.addWidget(self.fpsInfoLabel)  # FPS 정보를 표시할 레이블 추가
        layout.addWidget(self.openButton)
        layout.addWidget(self.saveButton)
        layout.addWidget(self.clearButton)
        layout.addWidget(self.drawBoxCheckBox)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.startTime = 0
        self.endTime = 0
        self.videoFile = None
        self.cropRect = None
        self.drawingBox = True
        self.clip = None

        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.updatePosition)
        self.timer.start()

        self.graphicsView.setMouseTracking(True)
        self.graphicsView.viewport().installEventFilter(self)
        self.dragStart = None
        self.dragRect = None

        self.mediaPlayer.positionChanged.connect(self.positionChanged)
        self.mediaPlayer.durationChanged.connect(self.durationChanged)

    def openFile(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi *.mov)")
        if fileName != '':
            self.videoFile = fileName

            self.clip = VideoFileClip(fileName)
            self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(fileName)))
            self.playButton.setEnabled(True)
            self.pauseButton.setEnabled(True)
            self.stopButton.setEnabled(True)
            self.saveButton.setEnabled(False)
            self.clearButton.setEnabled(True)
            self.drawBoxCheckBox.setEnabled(True)
            self.convertButton.setEnabled(True)

            self.positionSlider.setRange(0, int(self.clip.duration * 1000))
            self.endTime = int(self.clip.duration * 1000)
            self.totalTimeLabel.setText(self.formatTime(self.clip.duration))
            self.fpsInfoLabel.setText(f'FPS: {self.clip.fps}')  # FPS 정보를 표시

    def playVideo(self):
        self.mediaPlayer.play()

    def pauseVideo(self):
        self.mediaPlayer.pause()

    def stopVideo(self):
        self.mediaPlayer.stop()
        self.positionSlider.setValue(0)
        self.currentTimeLabel.setText('0:00.0')

    def setPosition(self, position):
        self.mediaPlayer.setPosition(position)

    def updatePosition(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            position = self.mediaPlayer.position()
            self.positionSlider.setValue(position)
            self.currentTimeLabel.setText(self.formatTime(position / 1000))

    def formatTime(self, seconds):
        mins, secs = divmod(seconds, 60)
        return f'{int(mins)}:{secs:04.1f}'

    def convertFPS(self):
        if self.videoFile:
            fps = self.fpsInput.text()
            if fps:
                new_clip = self.clip.set_fps(float(fps))
                new_clip = new_clip.without_audio()
                new_filename = 'converted_video.mp4'
                new_clip.write_videofile(
                    new_filename,
                    codec='libx264',
                    audio_codec='aac',
                    preset='ultrafast',  # CFR 설정을 위한 추가 옵션
                    ffmpeg_params=['-vsync', 'cfr']  # CFR 설정
                )
                self.loadConvertedVideo(new_filename)

    def loadConvertedVideo(self, filename):
        self.clip = VideoFileClip(filename)
        self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(filename)))
        self.playButton.setEnabled(True)
        self.pauseButton.setEnabled(True)
        self.stopButton.setEnabled(True)
        self.saveButton.setEnabled(False)
        self.clearButton.setEnabled(True)
        self.drawBoxCheckBox.setEnabled(True)
        self.convertButton.setEnabled(True)

        self.positionSlider.setRange(0, int(self.clip.duration * 1000))
        self.endTime = int(self.clip.duration * 1000)
        self.totalTimeLabel.setText(self.formatTime(self.clip.duration))
        self.fpsInfoLabel.setText(f'FPS: {self.clip.fps}')  # 변환된 영상의 FPS 정보도 업데이트

    def saveCut(self):
        if self.videoFile and self.cropRect:
            x1, y1, x2, y2 = self.cropRect
            new_clip = self.clip.fx(vfx.crop, x1=x1, y1=y1, x2=x2, y2=y2)
            new_clip.write_videofile(
                'cut_video.mp4',
                codec='libx264',
                audio_codec='aac',
                preset='ultrafast',  # CFR 설정을 위한 추가 옵션
                ffmpeg_params=['-vsync', 'cfr']  # CFR 설정
            )

    def clearVideo(self):
        self.videoFile = None
        self.clip = None
        self.playButton.setEnabled(False)
        self.pauseButton.setEnabled(False)
        self.stopButton.setEnabled(False)
        self.saveButton.setEnabled(False)
        self.clearButton.setEnabled(False)
        self.positionSlider.setRange(0, 0)
        self.currentTimeLabel.setText('0:00.0')
        self.totalTimeLabel.setText('0:00.0')
        self.fpsInfoLabel.setText('FPS: N/A')  # FPS 정보 초기화
        self.scene.clear()
        self.scene.addItem(self.videoItem)
        self.drawBoxCheckBox.setChecked(False)

    def toggleDrawBox(self, state):
        self.drawingBox = state == Qt.Checked

    def eventFilter(self, source, event):
        if self.drawingBox and source is self.graphicsView.viewport():
            if event.type() == event.MouseButtonPress:
                self.dragStart = self.graphicsView.mapToScene(event.pos())
                if self.dragRect:
                    self.scene.removeItem(self.dragRect)
                    self.dragRect = None
                return True
            elif event.type() == event.MouseMove and self.dragStart:
                if self.dragRect:
                    self.scene.removeItem(self.dragRect)
                currentPos = self.graphicsView.mapToScene(event.pos())
                rect = QRectF(self.dragStart, currentPos).normalized()
                rect = rect.intersected(self.videoItem.boundingRect())
                self.dragRect = QGraphicsRectItem(rect)
                self.dragRect.setPen(QPen(Qt.red, 2, Qt.SolidLine))
                self.dragRect.setBrush(QBrush(Qt.transparent))
                self.scene.addItem(self.dragRect)
                return True
            elif event.type() == event.MouseButtonRelease and self.dragStart:
                endPos = self.graphicsView.mapToScene(event.pos())
                x1, y1 = self.dragStart.x(), self.dragStart.y()
                x2, y2 = endPos.x(), endPos.y()
                self.cropRect = (x1, y1, x2, y2)
                self.dragStart = None
                self.saveButton.setEnabled(True)
                return True
        return super().eventFilter(source, event)

    def positionChanged(self, position):
        self.positionSlider.setValue(position)
        self.currentTimeLabel.setText(self.formatTime(position / 1000))

    def durationChanged(self, duration):
        self.positionSlider.setRange(0, duration)
        self.totalTimeLabel.setText(self.formatTime(duration / 1000))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    fontDB = QFontDatabase()
    fontDB.addApplicationFont('resources/D2Coding.ttf')
    app.setFont(QFont('D2Coding'))
    
    editor = VideoEditor()
    editor.show()
    sys.exit(app.exec_())
