import os
import re
import datetime
import numpy as np
import matplotlib.pyplot as plt
from spectral import open_image

from RadCalNetFileDownloader import download_radcalnet_files
from FileParser import read_radcalnet_by_date



# ПАРАМЕТРЫ
USERNAME = "ivanderevyanko05@gmail.com"
PASSWORD = "1DPSi16e5o"

SITE = "RVUS"
OUTPUT_DIR = "./radcalnet_data"

AVIRIS_FOLDER = "D:/Загрузки/ang20200712t223738/ang20200712t223738_rdn_v2y1/"
AVIRIS_FILE = "ang20200712t223738_rdn_v2y1_img.hdr"




def normalize(x):
    return (x - np.min(x)) / (np.max(x) - np.min(x))


def parse_aviris_datetime(filename):
    pattern = r"ang(\d{8})t(\d{6})"
    match = re.search(pattern, filename)

    if not match:
        raise ValueError("Ошибка парсинга даты")

    return datetime.datetime.strptime(
        match.group(1) + match.group(2),
        "%Y%m%d%H%M%S"
    )


def find_uniform_bright_patch(img, band=420, window=20, step=20):
    """
    Автоматически ищет однородный яркий участок.
    
    band - спектральный канал (например 420nm)
    window - размер окна
    step - шаг сканирования
    """

    band_data = img.read_band(band)

    best_score = None
    best_pos = (0, 0)

    rows, cols = band_data.shape

    for r in range(0, rows - window, step):
        for c in range(0, cols - window, step):

            patch = band_data[r:r+window, c:c+window]

            if np.any(patch <= 0):
                continue

            mean = np.mean(patch)
            std = np.std(patch)

            # метрика
            score = std / mean - 0.1 * mean

            if best_score is None or score < best_score:
                best_score = score
                best_pos = (r + window // 2, c + window // 2)

    return best_pos

img = open_image(os.path.join(AVIRIS_FOLDER, AVIRIS_FILE))


# точка полигона (автоматический поиск)
row, col = find_uniform_bright_patch(img)
print(f"Автоматически выбрана точка: row={row}, col={col}")

print("Размер данных:", img.shape)

# RGB preview
rgb = img.read_bands((30, 20, 10))
rgb = np.clip(rgb, 0, None)
rgb = rgb / np.max(rgb)
plt.scatter(col, row)
plt.imshow(rgb)
plt.title("AVIRIS RGB preview")
plt.show()



patch = img[row-5:row+5, col-5:col+5, :]
av_spectrum = patch.mean(axis=(0, 1))

av_wl = np.array(img.metadata['wavelength'], dtype=float)


aviris_dt = parse_aviris_datetime(AVIRIS_FILE)
DATE = aviris_dt.strftime("%Y-%m-%d")

# только дневное время
target_time = datetime.time(15, 0, 0)

print("Дата:", DATE)


if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

download_radcalnet_files(
    username=USERNAME,
    password=PASSWORD,
    output_dir=OUTPUT_DIR,
    start_date=DATE,
    stop_date=DATE,
    fmt="ascii",
    site=SITE
)

parsed_data = read_radcalnet_by_date(
    date=datetime.datetime.strptime(DATE, "%Y-%m-%d").date(),
    folder=OUTPUT_DIR,
    target_utc_time=target_time,
    site=SITE
)

print("Использованное время:", parsed_data["UTC"])


rc_dict = parsed_data["Radiance"]

rc_wl = np.array(list(rc_dict.keys()), dtype=float)
rc_spec = np.array(list(rc_dict.values()), dtype=float)

# сортировка
idx = np.argsort(rc_wl)
rc_wl = rc_wl[idx]
rc_spec = rc_spec[idx]


mask = (rc_spec > 0) & (rc_spec < 1000)
rc_wl = rc_wl[mask]
rc_spec = rc_spec[mask]

if len(rc_spec) == 0 or np.std(rc_spec) < 1e-6:
    raise ValueError("RadCalNet данные пустые или константные!")


av_interp = np.interp(rc_wl, av_wl, av_spectrum)

rc_spec_norm = normalize(rc_spec)
av_interp_norm = normalize(av_interp)


plt.figure(figsize=(10, 5))

plt.plot(rc_wl, rc_spec_norm, label="RadCalNet", linewidth=2)
plt.plot(rc_wl, av_interp_norm, label="AVIRIS", linestyle="--")

plt.xlabel("Wavelength (nm)")
plt.ylabel("Radiance")
plt.title(f"AVIRIS vs RadCalNet ({SITE}, {DATE})")

plt.legend()
plt.grid()

plt.show()
