import matplotlib.pyplot as plt
import numpy as np
from spectral import open_image

folder_path = "D:/Загрузки/ang20200712t223738/ang20200712t223738_rdn_v2y1/"
file_name = "ang20200712t223738_rdn_v2y1_img.hdr"

img = open_image(folder_path + file_name)

print("Размер данных (rows, cols, bands):", img.shape)

# RGB отображение
rgb = img.read_bands((30, 20, 10))
rgb = np.clip(rgb, 0, None)
rgb = rgb / np.max(rgb)

plt.imshow(rgb)
plt.title("AVIRIS RGB preview")
plt.show()

# выбор точки вручную
row = 2166
col = 440

# извлечение спектра
spectrum = img[row, col, :]
spectrum = np.squeeze(spectrum)

patch = img[row-3:row+3, col-3:col+3, :]
spectrum = patch.mean(axis=(0, 1))

# длины волн
wavelengths = np.array(img.metadata['wavelength'], dtype=float)

# график
plt.figure(figsize=(10, 5))
plt.plot(wavelengths, spectrum)

plt.xlabel("Wavelength (nm)")
plt.ylabel("Radiance")
plt.title(f"Spectrum at pixel ({row}, {col})")
plt.grid()

plt.show()
