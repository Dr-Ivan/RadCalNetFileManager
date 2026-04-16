import os
import datetime
import numpy as np
import matplotlib.pyplot as plt

from RadCalNetFileDownloader import download_radcalnet_files
from FileParser import read_radcalnet_by_date


USERNAME = "ivanderevyanko05@gmail.com"
PASSWORD = "1DPSi16e5o"

SITE = "RVUS"                 # "RVUS" для Railroad Valley
DATE = "2025-05-29"           # YYYY-MM-DD
OUTPUT_DIR = "./radcalnet_data"


if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

print("Скачивание данных RadCalNet...")

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

target_time = datetime.time(12, 0, 0)

parsed_data = read_radcalnet_by_date(
    date=datetime.datetime.strptime(DATE, "%Y-%m-%d").date(),
    folder=OUTPUT_DIR,
    target_utc_time=target_time,
    site=SITE
)

print("Парсинг выполнен.")
print("Использованное время UTC:", parsed_data["UTC"])


rc_dict = parsed_data["Radiance"]  

wavelengths = np.array(list(rc_dict.keys()), dtype=float)
values = np.array(list(rc_dict.values()), dtype=float)


idx = np.argsort(wavelengths)
wavelengths = wavelengths[idx]
values = values[idx]


plt.figure(figsize=(10, 5))
plt.plot(wavelengths, values)

plt.xlabel("Wavelength (nm)")
plt.ylabel("Radiance")
plt.title(f"RadCalNet Spectrum ({SITE}, {DATE})")
plt.grid()

plt.show()