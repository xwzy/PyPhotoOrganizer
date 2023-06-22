import os
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QLabel,
    QPushButton,
    QFileDialog,
    QSplitter,
    QListWidgetItem,
    QComboBox,
)
from PyQt5.QtGui import QKeySequence
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QStandardPaths, Qt
from PyQt5.QtCore import QObject, pyqtSignal

from PIL import Image
from PIL.ExifTags import TAGS


class PhotoOrganizer(QMainWindow):
    image_list = []
    current_index = 0

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Photo Organizer")
        self.directory = QStandardPaths.writableLocation(
            QStandardPaths.DesktopLocation
        )  # 默认为用户桌面路径
        self.raw_formats = [
            "CR3",
            "CR2",
            "NEF",
            "ARW",
            "ORF",
            "RW2",
            "DNG",
            "RAF",
            "SRW",
            "PEF",
            "MOS",
            "CRW",
            "SRF",
            "MRW",
            "DCR",
            "ERF",
            "RAW",
        ]

        # 创建主窗口部件
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)

        # 创建主窗口布局
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        # 创建顶部布局
        top_layout = QHBoxLayout()

        # 创建当前文件夹路径标签
        self.folder_label = QLabel()
        self.folder_label.setText("Current Folder:")
        top_layout.addWidget(self.folder_label)

        # 创建当前文件名标签
        self.filename_label = QLabel()
        self.filename_label.setText("Current File:")
        top_layout.addWidget(self.filename_label)

        main_layout.addLayout(top_layout)

        # 创建 QSplitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # 创建左侧列表部件
        self.list_widget = QListWidget()
        self.list_widget.setMinimumWidth(200)  # 设置列表最小宽度
        splitter.addWidget(self.list_widget)
        self.list_widget.currentRowChanged.connect(self.display_image)

        # 创建右侧图片显示部件
        self.image_label = QLabel()
        self.image_label.setMinimumSize(700, 700)  # 设置图片展示区域的最小大小
        splitter.addWidget(self.image_label)

        # 创建底部布局
        bottom_layout = QHBoxLayout()

        # 创建选择文件夹按钮
        self.select_folder_button = QPushButton("Select Folder")
        self.select_folder_button.clicked.connect(self.select_folder)
        bottom_layout.addWidget(self.select_folder_button)

        # 创建全部保留按钮
        self.keep_all_button = QPushButton("Keep All(Q)")
        self.keep_all_button.clicked.connect(self.keep_all)
        self.keep_all_button.setShortcut(QKeySequence("Q"))  # 添加快捷键 Q
        bottom_layout.addWidget(self.keep_all_button)

        # 创建仅保留raw按钮
        self.keep_jpg_button = QPushButton("Keep JPG(W)")
        self.keep_jpg_button.clicked.connect(self.keep_jpg)
        self.keep_jpg_button.setShortcut(QKeySequence("W"))  # 添加快捷键 W
        bottom_layout.addWidget(self.keep_jpg_button)

        # 创建全部删除按钮
        self.delete_all_button = QPushButton("Delete All(E)")
        self.delete_all_button.clicked.connect(self.delete_all)
        self.delete_all_button.setShortcut(QKeySequence("E"))  # 添加快捷键 E
        bottom_layout.addWidget(self.delete_all_button)

        # 创建下拉框用于选择raw文件后缀
        self.raw_formats_combo = QComboBox()
        self.raw_formats_combo.addItems(self.raw_formats)
        self.raw_formats_combo.currentTextChanged.connect(self.on_raw_format_changed)
        bottom_layout.addWidget(self.raw_formats_combo)

        main_layout.addLayout(bottom_layout)

        # 获取屏幕的尺寸
        screen_geometry = QApplication.desktop().screenGeometry()

        # 计算主窗口的居中位置
        x = (screen_geometry.width() - 1200) // 2
        y = (screen_geometry.height() - 800) // 2

        # 设置主窗口的位置和大小
        self.setGeometry(x, y, 1200, 800)
        self.select_folder_button.click()

    def on_raw_format_changed(self, new_text):
        self.load_photos()

    def select_folder(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Folder")
        if directory:
            self.directory = directory  # 更新成员变量 directory
            self.load_photos()

    def load_photos(self):
        self.image_list = []
        self.list_widget.clear()

        # 遍历目录，读取所有raw文件
        # 使用成员变量 directory，并按升序排序
        raw_format = self.raw_formats_combo.currentText().lower()
        for file_name in sorted(os.listdir(self.directory)):
            if file_name.lower().endswith(".jpg"):
                self.image_list.append(file_name)
                list_item = QListWidgetItem(file_name)
                raw_format = self.raw_formats_combo.currentText().upper()
                raw_path = os.path.join(
                    self.directory, os.path.splitext(file_name)[0] + "." + raw_format
                )
                if os.path.exists(raw_path):
                    list_item.setText(file_name + " [" + raw_format + "]")
                self.list_widget.addItem(list_item)

        if self.image_list and len(self.image_list) > 0 and self.current_index == 0:
            self.display_image(0)

    def display_image(self, index):
        if index == -1:
            return
        if index < 0 or index >= len(self.image_list):
            index = 0
        self.current_index = index

        image_name = self.image_list[index]
        image_path = os.path.join(self.directory, image_name)
        pixmap = QPixmap(image_path)
        self.image_label.setPixmap(pixmap.scaledToWidth(self.image_label.width()))

        # Get and display EXIF information
        exif_info = self.get_exif_info(image_path)

        if exif_info:
            file_size = get_file_size(image_path)
            capture_time = exif_info.get("DateTimeOriginal", "")
            dimensions = exif_info.get("ExifImageWidth", ""), exif_info.get(
                "ExifImageHeight", ""
            )
            iso = exif_info.get("ISOSpeedRatings", "")
            exposure_time = exif_info.get("ExposureTime", "")
            aperture = exif_info.get("FNumber", "")

            # Handle missing EXIF information
            file_size = file_size if file_size else "N/A"
            capture_time = capture_time if capture_time else "N/A"
            dimensions = (
                f"{dimensions[0]} x {dimensions[1]}" if all(dimensions) else "N/A"
            )
            iso = iso if iso else "N/A"
            exposure_time = exposure_time if exposure_time else "N/A"
            aperture = aperture if aperture else "N/A"

            # Update the labels in the top layout
            self.folder_label.setText("Current Folder:" + self.directory)
            self.filename_label.setText(
                f"Current File: {image_name} \nSize: {file_size}, Capture Time: {capture_time}, Dimensions: {dimensions} \nISO: {iso}, Exposure Time: {exposure_time}, Aperture: {aperture}"
            )
        else:
            # If no EXIF information is available, display the image name only
            self.folder_label.setText("Current Folder:" + self.directory)
            self.filename_label.setText("Current File:" + image_name)

    def get_exif_info(self, image_path):
        try:
            with Image.open(image_path) as img:
                exif_data = img._getexif()
                if exif_data is not None:
                    exif_info = {}
                    for tag_id, value in exif_data.items():
                        tag_name = TAGS.get(tag_id, tag_id)
                        exif_info[tag_name] = value
                    return exif_info
        except (IOError, AttributeError, KeyError, IndexError):
            pass

        return None

    def keep_all(self):
        if self.current_index + 1 == len(self.image_list):
            self.display_message("Finish organizing photos")
        else:
            self.list_widget.setCurrentRow(self.current_index + 1)

    def keep_jpg(self):
        image_name = self.image_list[self.current_index]
        raw_path = os.path.join(self.directory, image_name)
        raw_format = self.raw_formats_combo.currentText().upper()
        raw_path = os.path.splitext(raw_path)[0] + "." + raw_format
        if os.path.exists(raw_path):
            os.remove(raw_path)

        tmp_index = self.current_index + 1
        self.load_photos()
        if tmp_index == len(self.image_list):
            self.display_message("Finish organizing photos")
        else:
            self.list_widget.setCurrentRow(tmp_index)

    def delete_all(self):
        image_name = self.image_list[self.current_index]
        jpg_path = os.path.join(self.directory, image_name)
        raw_format = self.raw_formats_combo.currentText().upper()
        raw_path = os.path.splitext(jpg_path)[0] + "." + raw_format
        if os.path.exists(jpg_path):
            os.remove(jpg_path)
        if os.path.exists(raw_path):
            os.remove(raw_path)

        tmp_index = self.current_index
        self.load_photos()
        if tmp_index == len(self.image_list):
            self.display_message("Finish organizing photos")
        else:
            self.list_widget.setCurrentRow(tmp_index)

    def display_message(self, message):
        self.image_label.setText(message)


def get_file_size(file_path):
    size_bytes = os.path.getsize(file_path)
    size_units = ["Bytes", "KB", "MB", "GB", "TB"]

    size = size_bytes
    unit_index = 0
    while size >= 1024 and unit_index < len(size_units) - 1:
        size /= 1024
        unit_index += 1

    size_formatted = "{:.2f}".format(size)
    size_with_unit = f"{size_formatted} {size_units[unit_index]}"

    return size_with_unit


if __name__ == "__main__":
    app = QApplication([])
    app.setStyle("Fusion")
    window = PhotoOrganizer()
    window.show()
    app.exec_()
