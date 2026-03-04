import re
import os

# список обязательных метеопараметров
REQUIRED_METEO = ["P", "T", "WV", "O3", "AOD", "Ang", "Type"]
# "Zen", "Azi", "esd" только в OUTPUT - они мешают проверке INPUT


def analyze_radcalnet_file(path):
    if not os.path.exists(path):
        return "Файл не найден.\nДАННЫЕ НЕДОСТУПНЫ"

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    number_re = re.compile(r"[-+]?\d*\.\d+|\d+")
    wavelength_re = re.compile(r"^\s*\d{3,4}\s+")

    meteo_lines = {}   
    spectrum_rows = 0
    spectrum_numbers = 0
    in_spectrum = False

    for line in lines:
        line_strip = line.strip()

        # начало спектрального блока
        if wavelength_re.match(line_strip):
            in_spectrum = True

        if not in_spectrum:
            # строки вида "P:" "T:" "WV:" ...
            if ":" in line_strip:
                key = line_strip.split(":")[0].strip()
                if key in REQUIRED_METEO:
                    meteo_lines[key] = line_strip.split(":", 1)[1]
        else:
            # спектральная строка
            nums = number_re.findall(line_strip)
            if nums:
                spectrum_rows += 1
                spectrum_numbers += len(nums)

    meteo_present = len(meteo_lines)
    missing_meteo_keys = [k for k in REQUIRED_METEO if k not in meteo_lines]

    # пустые или отсутствующие секции -> частичные
    full_meteo = True
    if missing_meteo_keys:
        full_meteo = False

    # проверка значений (9999 -> признак отсутствующих данных)
    for key, raw in meteo_lines.items():
        nums = number_re.findall(raw)
        if any(n == "9999" for n in nums):
            full_meteo = False
            break

    # анализ полученных показателей
    full_spectrum = (spectrum_rows >= 30 and spectrum_numbers >= 100)

    # статус 
    if full_meteo and full_spectrum:
        return "ДАННЫЕ ДОСТУПНЫ ПОЛНОСТЬЮ"

    if meteo_present > 0 or spectrum_rows > 0:
        return "ДАННЫЕ ДОСТУПНЫ ЧАСТИЧНО"

    return "ДАННЫЕ НЕДОСТУПНЫ"


if __name__=="__main__":
    status = analyze_radcalnet_file("./radcalnet_data/LCFR01_2024_130_v00.06.input")
    print(f"Статус данных RadCalNet: {status}")

    status = analyze_radcalnet_file("./radcalnet_data/LCFR01_2024_130_v04.06.output")
    print(f"Статус данных RadCalNet: {status}")