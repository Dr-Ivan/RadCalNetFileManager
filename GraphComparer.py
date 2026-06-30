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


def parse_aviris_datetime(filename):
    pattern = r"ang(\d{8})t(\d{6})"
    match = re.search(pattern, filename)

    if not match:
        raise ValueError("Ошибка парсинга даты")

    return datetime.datetime.strptime(
        match.group(1) + match.group(2),
        "%Y%m%d%H%M%S"
    )


def find_uniform_bright_patch(
        img,
        band=40,
        window=20,
        step=20
    ):

    """
    Поиск однородного яркого участка.

    band - спектральный канал
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

            if np.any(~np.isfinite(patch)):
                continue
            
            if np.any(patch <= 0):
                continue

            mean = np.mean(patch)
            std = np.std(patch)

            score = std / mean - 0.1 * mean

            if best_score is None or score < best_score:
                best_score = score
                best_pos = (r + window // 2, c + window // 2)

    return best_pos


img = open_image(
    os.path.join(
        AVIRIS_FOLDER,
        AVIRIS_FILE
    )
)
print("Размер данных:", img.shape)

# Поиск точки
row, col = find_uniform_bright_patch(img)
print(
    f"Автоматически выбрана точка:"
    f" row={row}, col={col}"
)

# RGB preview
rgb = img.read_bands((30, 20, 10))
rgb = np.clip(rgb, 0, None)
rgb = rgb / np.max(rgb)
plt.figure(figsize=(8, 8))
plt.imshow(rgb)
plt.scatter(col, row, c="red", s=80)
plt.title("AVIRIS RGB preview")
plt.show()

# Спектр AVIRIS
patch = img[row-5:row+5, col-5:col+5, :]
av_spectrum = patch.mean(axis=(0, 1))
av_wl = np.array(
    img.metadata["wavelength"],
    dtype=float
)

# FWHM каналов AVIRIS
av_fwhm = np.array(
    img.metadata["fwhm"],
    dtype=float
)

# Удаление мусора
valid_av = (np.isfinite(av_spectrum) & (av_spectrum > 0))

av_wl = av_wl[valid_av]
av_spectrum = av_spectrum[valid_av]
av_fwhm = av_fwhm[valid_av]


print("\nAVIRIS:")
print("min =", np.min(av_spectrum))
print("max =", np.max(av_spectrum))


# Время AVIRIS
aviris_dt = parse_aviris_datetime(AVIRIS_FILE)
DATE = aviris_dt.strftime("%Y-%m-%d")
target_time = aviris_dt.time()
print("\nДата:", DATE)
print("Время AVIRIS:", target_time)

# Скачивание RADCALNET
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

# Чтение RADCALNET
parsed_data = read_radcalnet_by_date(
    date=datetime.datetime.strptime(
        DATE,
        "%Y-%m-%d"
    ).date(),
    folder=OUTPUT_DIR,
    target_utc_time=target_time,
    site=SITE
)

print("Использованное время RadCalNet:", parsed_data["UTC"])
rc_dict = parsed_data["Reflectance"]

rc_wl = np.array(
    list(rc_dict.keys()),
    dtype=float
)

rc_spec = np.array(
    list(rc_dict.values()),
    dtype=float
)

# Сортировка
idx = np.argsort(rc_wl)
rc_wl = rc_wl[idx]
rc_spec = rc_spec[idx]

# Удаление fill values
valid_rc = (
    np.isfinite(rc_spec)
    & (rc_spec > 0)
    & (rc_spec < 9990)
)

rc_wl = rc_wl[valid_rc]
rc_spec = rc_spec[valid_rc]

print("\nRadCalNet:")
print("min =", np.min(rc_spec))
print("max =", np.max(rc_spec))


rc_spec = rc_spec * 1000.0

print("\nRadCalNet после перевода единиц:")

print("min =", np.min(rc_spec))
print("max =", np.max(rc_spec))

# Только общий спектральный диапазон AVIRIS и RadCalNet
valid_range = (
    (av_wl >= rc_wl.min()) &
    (av_wl <= rc_wl.max())
)

av_wl = av_wl[valid_range]
av_spectrum = av_spectrum[valid_range]
av_fwhm = av_fwhm[valid_range]

print("\nОбщий спектральный диапазон:")
print(f"{av_wl.min():.1f} - {av_wl.max():.1f} нм")


# Приведение шкалы длин волн - интерполяция RadCalNet в каналы AVIRIS
rc_resampled = np.interp(
    av_wl,
    rc_wl,
    rc_spec
)

print("\nResampled RadCalNet:")
print("min =", np.min(rc_resampled))
print("max =", np.max(rc_resampled))


# Калибровочный коэффициент gain(lambda) = RadCalNet / AVIRIS
valid_gain = (av_spectrum > 0)
gain = np.zeros_like(av_spectrum)
gain[valid_gain] = (rc_resampled[valid_gain] / av_spectrum[valid_gain])

print("\nGain:")
print("min =", np.min(gain))
print("max =", np.max(gain))

# Калибровка AVIRIS
calibrated_aviris = (av_spectrum * gain)

print("\nCalibrated AVIRIS:")
print("min =", np.min(calibrated_aviris))
print("max =", np.max(calibrated_aviris))


# График Gain
plt.figure(figsize=(12, 6))
plt.plot(
    av_wl,
    gain,
    linewidth=2
)

plt.xlabel("Wavelength (nm)")
plt.ylabel("Gain")

plt.title(f"Calibration Gain ({SITE}, {DATE})")
plt.grid()
plt.show()


# График калиброванного спектра
plt.figure(figsize=(12, 6))

plt.plot(
    av_wl,
    rc_resampled,
    label="RadCalNet",
    color="red",
    linewidth=2,
    linestyle="-"
)

plt.plot(
    av_wl,
    calibrated_aviris,
    label="AVIRIS after calibration",
    color="black",
    linewidth=2,
    linestyle="--"
)


plt.plot(
    av_wl,
    av_spectrum,
    label="AVIRIS before calibration",
    linewidth=2,
    linestyle="-"
)

plt.xlabel("Wavelength (nm)")
plt.ylabel("Radiance")
plt.title(f"Calibrated AVIRIS vs RadCalNet ({SITE}, {DATE})")

plt.legend()
plt.grid()
plt.show()
