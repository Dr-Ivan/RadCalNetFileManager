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

# Второй снимок для проверки калибровки
TEST_AVIRIS_FOLDER = "D:/Загрузки/ang20200712t223219/ang20200712t223219_rdn_v2y1/"
TEST_AVIRIS_FILE = "ang20200712t223219_rdn_v2y1_img.hdr"



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


def load_aviris_scene(folder, filename):
    """
    Загружает сцену AVIRIS и извлекает спектр выбранной точки.
    """

    img = open_image(os.path.join(folder, filename))

    print("Размер данных:", img.shape)

    row, col = find_uniform_bright_patch(img)

    print(
        f"Автоматически выбрана точка:"
        f" row={row}, col={col}"
    )

    rgb = img.read_bands((30, 20, 10))
    rgb = np.clip(rgb, 0, None)
    rgb = rgb / np.max(rgb)

    plt.figure(figsize=(8, 8))
    plt.imshow(rgb)
    plt.scatter(col, row, c="red", s=80)
    plt.title("AVIRIS RGB preview")
    plt.show()

    patch = img[
        row-5:row+5,
        col-5:col+5,
        :
    ]

    spectrum = patch.mean(axis=(0, 1))

    wavelength = np.array(
        img.metadata["wavelength"],
        dtype=float
    )

    fwhm = np.array(
        img.metadata["fwhm"],
        dtype=float
    )

    valid = (
        np.isfinite(spectrum)
        &
        (spectrum > 0)
    )

    return (
        spectrum[valid],
        wavelength[valid],
        fwhm[valid],
        parse_aviris_datetime(filename)
    )


def load_radcalnet(date, target_time):
    """
    Загружает и подготавливает данные RadCalNet.
    """

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    download_radcalnet_files(
        username=USERNAME,
        password=PASSWORD,
        output_dir=OUTPUT_DIR,
        start_date=date,
        stop_date=date,
        fmt="ascii",
        site=SITE
    )

    parsed = read_radcalnet_by_date(
        date=datetime.datetime.strptime(
            date,
            "%Y-%m-%d"
        ).date(),
        folder=OUTPUT_DIR,
        target_utc_time=target_time,
        site=SITE
    )

    rc_dict = parsed["Reflectance"]

    wl = np.array(
        list(rc_dict.keys()),
        dtype=float
    )

    spec = np.array(
        list(rc_dict.values()),
        dtype=float
    )

    idx = np.argsort(wl)

    wl = wl[idx]
    spec = spec[idx]

    valid = (
        np.isfinite(spec)
        &
        (spec > 0)
        &
        (spec < 9990)
    )

    wl = wl[valid]
    spec = spec[valid]

    spec *= 1000.0

    return wl, spec, parsed["UTC"]


def plot_gain(wavelength, gain):

    plt.figure(figsize=(12, 6))

    plt.plot(
        wavelength,
        gain,
        linewidth=2
    )

    plt.title(f"Calibration Gain ({SITE}, {DATE})")

    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Gain")

    plt.grid()

    plt.show()


def plot_calibration(
        wavelength,
        radcalnet,
        aviris_before,
        aviris_after,
        title):

    plt.figure(figsize=(12, 6))

    plt.plot(
        wavelength,
        radcalnet,
        label="RadCalNet",
        color="red",
        linewidth=2
    )

    plt.plot(
        wavelength,
        aviris_after,
        "--",
        color="black",
        linewidth=2,
        label="AVIRIS after calibration"
    )

    plt.plot(
        wavelength,
        aviris_before,
        linewidth=2,
        label="AVIRIS before calibration"
    )

    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Radiance")

    plt.title(title)

    plt.grid()
    plt.legend()

    plt.show()



(
    av_spectrum,
    av_wl,
    av_fwhm,
    aviris_dt
) = load_aviris_scene(
    AVIRIS_FOLDER,
    AVIRIS_FILE
)

# Время AVIRIS
aviris_dt = parse_aviris_datetime(AVIRIS_FILE)
DATE = aviris_dt.strftime("%Y-%m-%d")
target_time = aviris_dt.time()
print("\nДата:", DATE)
print("Время AVIRIS:", target_time)

rc_wl, rc_spec, used_time = load_radcalnet(
    DATE,
    target_time
)

print("Использованное время RadCalNet:", used_time)

print("\nRadCalNet:")
print("min =", np.min(rc_spec))
print("max =", np.max(rc_spec))


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


plot_gain(
    av_wl,
    gain
)

plot_calibration(
    av_wl,
    rc_resampled,
    av_spectrum,
    calibrated_aviris,
    f"Calibrated AVIRIS vs RadCalNet ({SITE}, {DATE})"
)





# Проверка калибровки на втором снимке AVIRIS
(
    av2_spectrum,
    av2_wl,
    av2_fwhm,
    aviris2_dt
) = load_aviris_scene(
    TEST_AVIRIS_FOLDER,
    TEST_AVIRIS_FILE
)

DATE2 = aviris2_dt.strftime("%Y-%m-%d")
target_time2 = aviris2_dt.time()

print("\nДата второго снимка:", DATE2)
print("Время второго снимка:", target_time2)

rc2_wl, rc2_spec, used_time2 = load_radcalnet(
    DATE2,
    target_time2
)

print("Использованное время RadCalNet:", used_time2)

print("\nRadCalNet (второй снимок):")
print("min =", np.min(rc2_spec))
print("max =", np.max(rc2_spec))


# Только общий спектральный диапазон
valid_range = (
    (av2_wl >= rc2_wl.min()) &
    (av2_wl <= rc2_wl.max())
)

av2_wl = av2_wl[valid_range]
av2_spectrum = av2_spectrum[valid_range]
av2_fwhm = av2_fwhm[valid_range]

print("\nОбщий спектральный диапазон:")
print(f"{av2_wl.min():.1f} - {av2_wl.max():.1f} нм")


# Приведение RadCalNet ко второй спектральной сетке AVIRIS
rc2_resampled = np.interp(
    av2_wl,
    rc2_wl,
    rc2_spec
)

print("\nResampled RadCalNet:")
print("min =", np.min(rc2_resampled))
print("max =", np.max(rc2_resampled))



# Применение ранее вычисленных коэффициентов
# Перенос gain на спектральную сетку второго снимка
gain2 = np.interp(
    av2_wl,
    av_wl,
    gain
)

print("\nПеренесенный Gain:")
print("min =", np.min(gain2))
print("max =", np.max(gain2))


# Калибровка второго снимка
calibrated_aviris2 = av2_spectrum * gain2

print("\nCalibrated AVIRIS:")
print("min =", np.min(calibrated_aviris2))
print("max =", np.max(calibrated_aviris2))


plot_calibration(
    av2_wl,
    rc2_resampled,
    av2_spectrum,
    calibrated_aviris2,
    f"Validation of calibration for {SITE}"
)

rmse = np.sqrt(np.mean((calibrated_aviris2 - rc2_resampled) ** 2))
mae = np.mean(np.abs(calibrated_aviris2 - rc2_resampled))

print("\nErrors of calibration:")
print(f"RMSE = {rmse:.3f}")
print(f"MAE = {mae:.3f}")
