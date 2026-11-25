import warnings
import math
from datetime import datetime
from pathlib import Path

from PIL import Image

# Предупреждалку убираем, чтоб не портить вывод лишней краснотой
warnings.filterwarnings("ignore", message=".*getdata is deprecated.*", category=DeprecationWarning)

# Пути, параметры редактора
BASE_DIR = Path(__file__).resolve().parent / "Lab2_Media"
INPUT_DIR = BASE_DIR / "data" / "input"
OUTPUT_DIR = BASE_DIR / "data" / "output"
LOG_FILE = BASE_DIR / "logs" / "history.txt"

SIGMA = 1.5
FILTER_NAME = f"Гаусс (sigma={SIGMA}) + Серый мир"
# Записи в журнал
def write_log(filename, filter_name, status):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] Файл: {filename} | Фильтр: {filter_name} | Статус: {status}\n"
    try:
        with open(LOG_FILE, "a", encoding="UTF-8") as log:
            log.write(line)
    except OSError as e:
        print(f"Предупреждение: не удалось записать журнал ({e})")
# Ядро Гаусса
def gaussian_kernel(sigma):
    radius = max(1, math.ceil(3 * sigma))
    weights = [math.exp(-(x * x) / (2 * sigma * sigma))
    for x in range(-radius, radius + 1)]
    total = sum(weights)
    return radius, [w / total for w in weights]
# Фильтр Гаусса
def gaussian_blur(image, sigma):
    radius, kernel = gaussian_kernel(sigma)
    width, height = image.size
    src = list(image.getdata())
    temp = []
    for y in range(height):
        row_start = y * width
        for x in range(width):
            r = g = b = 0.0
            for k in range(-radius, radius + 1):
                xx = min(max(x + k, 0), width - 1)
                weight = kernel[k + radius]
                pr, pg, pb = src[row_start + xx]
                r += pr * weight
                g += pg * weight
                b += pb * weight
            temp.append((r, g, b))
    out = []
    for y in range(height):
        for x in range(width):
            r = g = b = 0.0
            for k in range(-radius, radius + 1):
                yy = min(max(y + k, 0), height - 1)
                weight = kernel[k + radius]
                pr, pg, pb = temp[yy * width + x]
                r += pr * weight
                g += pg * weight
                b += pb * weight
            out.append((round(r), round(g), round(b)))

    result = Image.new("RGB", (width, height))
    result.putdata(out)
    return result
# Серый и гнусный мир
def gray_world(image):
    pixels = list(image.getdata())
    n = len(pixels)
    avg_r = sum(p[0] for p in pixels) / n
    avg_g = sum(p[1] for p in pixels) / n
    avg_b = sum(p[2] for p in pixels) / n
    gray = (avg_r + avg_g + avg_b) / 3

    k_r = gray / avg_r if avg_r > 0 else 1.0
    k_g = gray / avg_g if avg_g > 0 else 1.0
    k_b = gray / avg_b if avg_b > 0 else 1.0

    corrected = [(min(255, round(p[0] * k_r)), min(255, round(p[1] * k_g)), min(255, round(p[2] * k_b))) for p in pixels]

    print(f"Средние каналы до: R={avg_r:.1f} G={avg_g:.1f} B={avg_b:.1f}")
    print(f"Коэффициенты: kR={k_r:.3f} kG={k_g:.3f} kB={k_b:.3f}")

    result = Image.new("RGB", image.size)
    result.putdata(corrected)
    return result
# Сама функция обработки
def main():
    filename = input("Введите имя файла с расширением (.jpg, .png): ").strip()
    if not filename:
        print("Ошибка: имя файла не введено")
        write_log(filename, FILTER_NAME, "Имя файла не указано")
        return
    path = INPUT_DIR / filename
    print(f"Пробуем открыть файл по пути: {path}")
    try:
        with open(path, "r+b") as f:
            image = Image.open(f).convert("RGB")
    except PermissionError:
        print(f"Ошибка: Нет прав на чтение файла {filename}. Обратитесь к администратору")
        write_log(filename, FILTER_NAME, "Ошибка доступа")
        return
    except FileNotFoundError:
        print("Ошибка: Файл не найден")
        write_log(filename, FILTER_NAME, "Файл не найден")
        return
    except OSError as e:
        print(f"Ошибка: не удалось прочитать изображение ({e})")
        write_log(filename, FILTER_NAME, "Ошибка чтения")
        return
    print("Файл открыт. Идёт обработка, подождите несколько секунд...")
    blurred = gaussian_blur(image, SIGMA)
    balanced = gray_world(blurred)
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        result_path = OUTPUT_DIR / "result.jpg"
        balanced.save(result_path, "JPEG", quality=95)
    except OSError as e:
        print(f"Ошибка: не удалось сохранить результат ({e})")
        write_log(filename, FILTER_NAME, "Ошибка сохранения")
        return
    print(f"Готово! Результат сохранён по пути: {result_path}")
    write_log(filename, FILTER_NAME, "Успешно")
# Херь, чтобы мейн запускался в принципе
if __name__ == "__main__":
    main()