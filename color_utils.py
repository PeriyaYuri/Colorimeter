import cv2
import numpy as np

def normalize_lab(lab_color):
    """
    Нормализация значений L*a*b* из формата OpenCV в стандартный диапазон:
    L: 0..100
    a: -128..127
    b: -128..127
    """
    l = (lab_color[0] * 100.0) / 255.0
    a = lab_color[1] - 128.0
    b = lab_color[2] - 128.0
    return np.array([l, a, b])

def get_dominant_color_lab(frame, x, y, w, h):
    """Получение доминантного цвета в L*a*b* пространстве"""
    # Извлекаем область интереса
    roi = frame[y:y+h, x:x+w]
    
    # Конвертируем в L*a*b*
    lab_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB)
    
    # Вычисляем среднее значение цвета
    avg_color = np.mean(lab_roi, axis=(0,1))
    
    # Нормализуем значения в правильный диапазон
    return normalize_lab(avg_color)

def compare_colors_lab(color1, color2):
    """
    Сравнение цветов в L*a*b* пространстве
    Возвращает разницу по каждому каналу и общую разницу (Delta E)
    """
    # Вычисляем разницу для каждого компонента
    l_diff = abs(color1[0] - color2[0])
    a_diff = abs(color1[1] - color2[1])
    b_diff = abs(color1[2] - color2[2])
    
    # Вычисляем Delta E (CIE76)
    # Более точные формулы: CIE94 или CIEDE2000, но CIE76 достаточно для базового сравнения
    delta_e = np.sqrt(l_diff**2 + a_diff**2 + b_diff**2)
    
    return l_diff, a_diff, b_diff, delta_e

def get_color_name(l, a, b):
    """
    Получение приблизительного названия цвета на основе координат L*a*b*
    """
    if l > 90:
        return "Белый"
    elif l < 20:
        return "Черный"
    
    # Определяем базовый цвет по координатам a* и b*
    if abs(a) < 10 and abs(b) < 10:
        if l > 80:
            return "Белый"
        elif l < 20:
            return "Черный"
        else:
            return "Серый"
    
    hue = np.arctan2(b, a) * 180 / np.pi
    
    if hue < 0:
        hue += 360
        
    if hue >= 315 or hue < 45:
        return "Красный"
    elif hue < 75:
        return "Желтый"
    elif hue < 165:
        return "Зеленый"
    elif hue < 195:
        return "Голубой"
    elif hue < 285:
        return "Синий"
    else:
        return "Фиолетовый"