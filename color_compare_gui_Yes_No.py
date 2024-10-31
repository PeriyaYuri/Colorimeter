import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from color_utils import get_dominant_color_lab, compare_colors_lab, get_color_name

class ColorComparisonApp:
    def __init__(self, window):
        self.window = window
        self.window.title("Сравнение цветов (L*a*b*)")
        self.window.geometry("1000x800")

        # Инициализация камеры
        self.cap = cv2.VideoCapture(1)
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Настройка регионов
        self.region_width = self.frame_width // 4
        self.region_height = self.frame_height // 4
        self.region = {
            'x': self.frame_width // 3,
            'y': self.frame_height // 3,
            'w': self.region_width,
            'h': self.region_height
        }

        # Сохраненные данные эталона
        self.reference_frame = None
        self.reference_color = None
        
        # Пороговые значения по умолчанию
        self.threshold_l = tk.DoubleVar(value=5.0)  # Допуск для L (0-100)
        self.threshold_a = tk.DoubleVar(value=5.0)  # Допуск для a (-128 to 127)
        self.threshold_b = tk.DoubleVar(value=5.0)  # Допуск для b (-128 to 127)
        self.threshold_e = tk.DoubleVar(value=10.0) # Допуск для общей разницы (Delta E)
        
        # Создание элементов интерфейса
        self.create_widgets()

        # Запуск обновления видео
        self.update_video()

    def create_widgets(self):
        # Основной контейнер
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Видео фрейм
        self.video_label = ttk.Label(main_frame)
        self.video_label.pack(pady=10)

        # Кнопки управления
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=5)

        self.capture_btn = ttk.Button(
            control_frame, 
            text="Сделать эталонный снимок", 
            command=self.capture_reference
        )
        self.capture_btn.pack(side=tk.LEFT, padx=5)

        self.clear_btn = ttk.Button(
            control_frame, 
            text="Очистить эталон", 
            command=self.clear_reference
        )
        self.clear_btn.pack(side=tk.LEFT, padx=5)

        # Фрейм с пороговыми значениями
        threshold_frame = ttk.LabelFrame(main_frame, text="Допустимые отклонения", padding=8)
        threshold_frame.pack(fill=tk.X, pady=5)

        # L* порог (0-100)
        ttk.Label(threshold_frame, text="L* допуск (0-100):").grid(row=0, column=0, padx=5)
        ttk.Entry(threshold_frame, textvariable=self.threshold_l, width=8).grid(row=0, column=1, padx=5)

        # a* порог (-128 to 127)
        ttk.Label(threshold_frame, text="a* допуск (-128..127):").grid(row=0, column=2, padx=5)
        ttk.Entry(threshold_frame, textvariable=self.threshold_a, width=8).grid(row=0, column=3, padx=5)

        # b* порог (-128 to 127)
        ttk.Label(threshold_frame, text="b* допуск (-128..127):").grid(row=0, column=4, padx=5)
        ttk.Entry(threshold_frame, textvariable=self.threshold_b, width=8).grid(row=0, column=5, padx=5)

        # Delta E порог
        ttk.Label(threshold_frame, text="Дельта общая ΔE допуск:").grid(row=0, column=6, padx=5)
        ttk.Entry(threshold_frame, textvariable=self.threshold_e, width=8).grid(row=0, column=7, padx=5)

        # Фрейм с информацией о цветах
        info_frame = ttk.LabelFrame(main_frame, text="Информация о цветах", padding=8)
        info_frame.pack(fill=tk.X, pady=5)

        # Метки для отображения информации
        self.reference_label = ttk.Label(info_frame, text="Эталонный цвет: не задан")
        self.reference_label.grid(row=0, column=0, padx=5, pady=2)

        self.current_color_label = ttk.Label(info_frame, text="Текущий цвет: ")
        self.current_color_label.grid(row=1, column=0, padx=5, pady=2)

        self.diff_label = ttk.Label(info_frame, text="Разница: ")
        self.diff_label.grid(row=2, column=0, padx=5, pady=2)

        self.status_label = ttk.Label(info_frame, text="Статус: ", font=('Arial', 12, 'bold'))
        self.status_label.grid(row=3, column=0, padx=5, pady=5)

        # Кнопка выхода
        exit_button = ttk.Button(main_frame, text="Выход", command=self.on_closing)
        exit_button.pack(pady=1)

    def check_thresholds(self, l_diff, a_diff, b_diff, delta_e):
        """Проверка на соответствие пороговым значениям"""
        if (l_diff <= self.threshold_l.get() and 
            a_diff <= self.threshold_a.get() and 
            b_diff <= self.threshold_b.get() and 
            delta_e <= self.threshold_e.get()):
            return True, "СООТВЕТСТВУЕТ", 'green'
        return False, "НЕ СООТВЕТСТВУЕТ", 'red'

    def capture_reference(self):
        """Захват эталонного кадра"""
        ret, frame = self.cap.read()
        if ret:
            self.reference_frame = frame.copy()
            self.reference_color = get_dominant_color_lab(frame, **self.region)
            color_name = get_color_name(*self.reference_color)
            self.reference_label.config(
                text=f"Эталонный цвет: L: {self.reference_color[0]:.1f},  a: {self.reference_color[1]:.1f}, "
                     f" b: {self.reference_color[2]:.1f} ({color_name})"
            )

    def clear_reference(self):
        """Очистка эталонного кадра"""
        self.reference_frame = None
        self.reference_color = None
        self.reference_label.config(text="Эталонный цвет: не задан")
        self.status_label.config(text="Статус: ")

    def update_video(self):
        ret, frame = self.cap.read()
        if ret:
            # Получение текущего цвета
            current_color = get_dominant_color_lab(frame, **self.region)
            color_name = get_color_name(*current_color)
            
            # Отрисовка прямоугольника
            cv2.rectangle(frame, 
                         (self.region['x'], self.region['y']), 
                         (self.region['x'] + self.region['w'], 
                          self.region['y'] + self.region['h']), 
                         (0, 255, 0), 2)

            # Обновление информации о текущем цвете
            self.current_color_label.config(
                text=f"Текущий цвет: L: {current_color[0]:.1f},  a: {current_color[1]:.1f}, "
                     f" b: {current_color[2]:.1f} ({color_name})"
            )

            # Сравнение с эталоном, если он существует
            if self.reference_color is not None:
                l_diff, a_diff, b_diff, delta_e = compare_colors_lab(self.reference_color, current_color)
                self.diff_label.config(
                    text=f"Разница: ΔL: {l_diff:.1f},  Δa: {a_diff:.1f},  Δb: {b_diff:.1f},  ΔE: {delta_e:.1f}"
                )
                
                # Проверка на соответствие пороговым значениям
                _, status_text, status_color = self.check_thresholds(l_diff, a_diff, b_diff, delta_e)
                self.status_label.config(text=f"Статус: {status_text}", foreground=status_color)

            # Конвертация изображения для отображения
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

        # Планирование следующего обновления
        self.window.after(10, self.update_video)

    def on_closing(self):
        self.cap.release()
        self.window.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ColorComparisonApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()