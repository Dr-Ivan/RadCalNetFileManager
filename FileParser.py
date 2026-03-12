import datetime as dt
import os
import re

# Перевод в минуты
def to_minutes(t):
    return t.hour * 60 + t.minute

# Возвращает индекс времени, ближайшего к target_time
def _closest_time_index(times, target_time):
    target = to_minutes(target_time)
    diffs = [abs(to_minutes(t) - target) for t in times]
    return diffs.index(min(diffs))

# Извлекает из файла  metadata (dict), spectrum (dict: wavelength -> value)
def _parse_radcalnet_file(path, column_index):
    metadata = {}
    spectrum = {}

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    number_re = re.compile(r"[-+]?\d*\.\d+|\d+")
    wavelength_re = re.compile(r"^\s*(\d{3,4})\s+")

    in_spectrum = False

    for line in lines:
        line = line.strip()

        # спектр 
        wl_match = wavelength_re.match(line)
        if wl_match:
            in_spectrum = True
            parts = number_re.findall(line)
            wavelength = int(parts[0])
            if 400 <= wavelength <= 1000:
                try:
                    spectrum[wavelength] = float(parts[column_index + 1])
                except IndexError:
                    spectrum[wavelength] = None
            continue

        if in_spectrum:
            continue

        # заголовочные поля 
        if ":" in line:
            key, values = line.split(":", 1)
            values = number_re.findall(values)
            if values and column_index < len(values):
                metadata[key.strip()] = values[column_index]

    return metadata, spectrum


# Структурированные данные RadCalNet
def read_radcalnet_by_date(
    date,
    folder,
    target_utc_time,
    site = "LCFR"
):
    
    year = date.year
    doy = date.timetuple().tm_yday

    # поиск файлов
    input_file = None
    output_file = None

    for fname in os.listdir(folder):
        if not fname.startswith(site):
            continue
        if f"_{year}_{doy:03d}_" not in fname:
            continue
        if fname.endswith(".input"):
            input_file = os.path.join(folder, fname)
        if fname.endswith(".output"):
            output_file = os.path.join(folder, fname)

    if not input_file or not output_file:
        raise FileNotFoundError("Файлы .input/.output не найдены")

    # UTC из input 
    with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.startswith("UTC"):
                times = [
                    dt.datetime.strptime(t, "%H:%M").time()
                    for t in line.split()[1:]
                ]
                break
        else:
            raise ValueError("Строка UTC не найдена")

    col_idx = _closest_time_index(times, target_utc_time)

    # данные
    meta_in, spectrum_radiance = _parse_radcalnet_file(input_file, col_idx)
    meta_out, spectrum_reflectance = _parse_radcalnet_file(output_file, col_idx)

    # итоговая структура
    result = {
        "Year": year,
        "DOY": doy,
        "UTC": times[col_idx],
        "Site": site,
        "Radiance": spectrum_radiance,
        "Reflectance": spectrum_reflectance,
    }

    # общие метаданные
    for k in meta_in:
        if k not in result:
            result[k] = meta_in[k]

    return result


if __name__=="__main__":
    data = read_radcalnet_by_date(
        date=dt.date(2024, 1, 4), # год, месяц, день
        folder="./radcalnet_data",
        target_utc_time=dt.time(14, 15)  # UTC
    )

    # Тестовый вывод
    print(data["UTC"])
    print(data["Radiance"][400], data["Reflectance"][400])
    print(data["Radiance"])

    print("Все полученные ключи: ")
    print(data.keys())

    print("Все полученные данные: ")
    print(data)
