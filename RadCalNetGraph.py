import os
import re
import datetime
import numpy as np
import matplotlib.pyplot as plt

from RadCalNetFileDownloader import download_radcalnet_files
from FileParser import read_radcalnet_by_date


def parse_aviris_datetime(filename):
    pattern = r"ang(\d{8})t(\d{6})"
    match = re.search(pattern, filename)

    if not match:
        raise ValueError("Не удалось извлечь дату из имени AVIRIS файла")

    date_str = match.group(1)
    time_str = match.group(2)

    return datetime.datetime.strptime(date_str + time_str, "%Y%m%d%H%M%S")



USERNAME = "ivanderevyanko05@gmail.com"
PASSWORD = "1DPSi16e5o"

SITE = "RVUS"                 # "RVUS" для Railroad Valley
DATE = "2025-05-29"           # YYYY-MM-DD
OUTPUT_DIR = "./radcalnet_data"

AVIRIS_FILE = "ang20200712t223738_rdn_v2y1_img.hdr"


# Дата и время из AVIRIS 
aviris_dt = parse_aviris_datetime(AVIRIS_FILE)

DATE = aviris_dt.strftime("%Y-%m-%d")

# В вечернее и ночное время данных нет
if aviris_dt.hour < 9 or aviris_dt.hour > 15:
    target_time = datetime.time(12, 0, 0)
else:
    target_time = aviris_dt.time()

print("Дата AVIRIS:", aviris_dt)
print("Дата для RadCalNet:", DATE)
print("Время UTC:", target_time)


#  Скачивание 
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

print("\nСкачивание данных RadCalNet...")

download_radcalnet_files(
    username=USERNAME,
    password=PASSWORD,
    output_dir=OUTPUT_DIR,
    start_date=DATE,
    stop_date=DATE,
    fmt="ascii",
    site=SITE
)

print("Скачивание завершено.\n")


#  парсинг 
parsed_data = read_radcalnet_by_date(
    date=datetime.datetime.strptime(DATE, "%Y-%m-%d").date(),
    folder=OUTPUT_DIR,
    target_utc_time=target_time,
    site=SITE
)

print("Парсинг выполнен.")
print("Использованное время UTC:", parsed_data["UTC"])


#  спектр 
rc_dict = parsed_data["Radiance"]

wavelengths = np.array(list(rc_dict.keys()), dtype=float)
values = np.array(list(rc_dict.values()), dtype=float)

idx = np.argsort(wavelengths)
wavelengths = wavelengths[idx]
values = values[idx]


#  график 
plt.figure(figsize=(10, 5))
plt.plot(wavelengths, values)

plt.xlabel("Wavelength (nm)")
plt.ylabel("Radiance")
plt.title(f"RadCalNet Spectrum ({SITE}, {DATE})")
plt.grid()

plt.show()