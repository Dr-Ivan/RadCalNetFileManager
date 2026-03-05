import os
import datetime
import requests

 # Функция для парсинга имени файла
def parse_name(filename):
    site_instrument, year, doy, version = filename.split('_')
    return (site_instrument, int(year), int(doy), version)


def download_radcalnet_files(username, password, output_dir, start_date, stop_date, fmt='nc', site='LCFR'):
    """
    Функция для скачивания файлов с RadCalNet
    
    Параметры:
    - username: логин
    - password: пароль  
    - output_dir: директория для сохранения файлов
    - start_date: начальная дата в формате 'YYYY-MM-DD'
    - stop_date: конечная дата в формате 'YYYY-MM-DD'
    - fmt: формат файлов ('ascii' или 'nc')
    - site: сайт (по умолчанию 'LCFR' - La Crau)
    """
    
    url_base = "https://www.radcalnet.org/api/json/"
    
    # Сессия с аутентификацией
    session = requests.session()
    session.auth = (username, password)
    
    # Список доступных сайтов
    r = session.get(url_base)
    r.raise_for_status()
    sites = [filename['name'] for filename in r.json()]
    
    if site not in sites:
        raise ValueError(f"Сайт {site} не найден. Доступные сайты: {', '.join(sites)}")
    
    if fmt.lower() not in ('ascii', 'nc'):
        raise ValueError("Формат должен быть 'ascii' или 'nc'")
    
    # Даты в datetime объекты
    date1 = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    date2 = datetime.datetime.strptime(stop_date, '%Y-%m-%d')
    
    if date1 > date2:
        raise ValueError("Начальная дата не может быть больше конечной")
    
    # Поддиректория в зависимости от формата
    subdir = {'ascii': '/data/', 'nc': '/datanc/'}
    url = url_base + site + subdir[fmt.lower()]
    
    # Список всех файлов для сайта
    r = session.get(url)
    r.raise_for_status()
    filelist = [file['name'] for file in r.json()]
    
    # Фильтр файлов по датам
    wanted_files = []
    doy1 = (date1 - datetime.datetime(date1.year, 1, 1, 0, 0)).days + 1
    doy2 = (date2 - datetime.datetime(date2.year, 1, 1, 0, 0)).days + 1
    
    for filename in filelist:
        try:
            site_instrument, year, doy, version = parse_name(filename)
            if date1.year == date2.year:
                if year == date1.year and doy1 <= doy <= doy2:
                    wanted_files.append(filename)
            elif date1.year == year and doy1 <= doy:
                wanted_files.append(filename)
            elif date2.year == year and doy <= doy2:
                wanted_files.append(filename)
            elif date1.year < year < date2.year:
                wanted_files.append(filename)
        except:
            continue  # Пропуск файлов с неподдерживаемым форматом имени
    
    # Скачивание
    for filename in wanted_files:
        dest = os.path.join(output_dir, filename)
        if not os.path.isfile(dest):
            print(f"Скачиваю: {filename}")
            with session.get(url + filename, stream=True) as r:
                r.raise_for_status()
                with open(dest + '.new', 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                os.rename(dest + '.new', dest)
                print(f"Сохранен: {dest}")
        else:
            print(f"Файл уже существует: {filename}")




# Скачивание
if __name__ == "__main__":

    # Параметры скачивания
    USERNAME = "ivanderevyanko05@gmail.com"
    PASSWORD = "1DPSi16e5o"
    OUTPUT_DIR = "./radcalnet_data" # Директория для сохранения
    START_DATE = "2024-05-09"       # Начальная дата
    STOP_DATE = "2024-05-09"        # Конечная дата  
    FORMAT = "ascii"                # Формат: 'ascii' или 'nc'
    SITE = "LCFR"                   # Сайт: La Crau

    # Создать директорию если не существует
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    download_radcalnet_files(
        username=USERNAME,
        password=PASSWORD, 
        output_dir=OUTPUT_DIR,
        start_date=START_DATE,
        stop_date=STOP_DATE,
        fmt=FORMAT,
        site=SITE
    )