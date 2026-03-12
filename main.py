from XMLparser import parse_resurs_p_metadata
from RadCalNetFileDownloader import download_radcalnet_files
from CheckDataAvailability import analyze_radcalnet_file
from FileParser import read_radcalnet_by_date

import os
import datetime
import re

def files_for_date(folder, site, date_str):
    """
    Возвращает список файлов RadCalNet за конкретную дату.
    date_str: 'YYYY-MM-DD'
    """
    date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    year = date.year
    doy = (date - datetime.date(year, 1, 1)).days + 1

    pattern = re.compile(
        rf"^{site}\d*_?{year}_{doy:03d}_.*\.(input|output)$"
    )

    result = []
    for fname in os.listdir(folder):
        if pattern.match(fname):
            result.append(os.path.join(folder, fname))

    return result



if __name__ == "__main__":
    xml_file = input("Введите путь к XML файлу (для запуска на тестовом файле введите пустую строку): ")
    out_path = input("Введите путь к папке для сохранения файлов (для запуска с путем './radcalnet_data' введите пустую строку): ")

    if not xml_file:
        xml_file = "0041_0102_20858_1_00977_01_L1A.xml"

    if not out_path:
        out_path = "./radcalnet_data"

    if os.path.exists(xml_file):
        metadata = parse_resurs_p_metadata(xml_file)
        if metadata:
            print(f"Дата съемки: {metadata['date']}")
            print(f"Время съемки: {metadata['time']}")
            print(f"Полная дата-время: {metadata['datetime']}")
            print(f"Поиск на сайте по: {metadata['date_only']}")

            # Параметры скачивания
            USERNAME = "ivanderevyanko05@gmail.com"
            PASSWORD = "1DPSi16e5o"
            OUTPUT_DIR = out_path # Директория для сохранения
            START_DATE = metadata['date_only']       # Начальная дата
            STOP_DATE = metadata['date_only']        # Конечная дата  
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

            print("\nСкачивание завершено.\n")

            print("Проверка доступности данных в скачанных файлах RadCalNet.\n")

            date_only = metadata['date_only']
            files = files_for_date(OUTPUT_DIR, SITE, date_only)

            if not files:
                print(f"Файлы RadCalNet за дату {date_only} не найдены.")
                print("ДАННЫЕ НЕДОСТУПНЫ")
            else:
                statuses = []

                for file_path in sorted(files):
                    status = analyze_radcalnet_file(file_path)
                    statuses.append(status)
                    print(f"{os.path.basename(file_path)}: {status}")

                print("\nИТОГ ПО ДАТЕ:")

                if all("ПОЛНОСТЬЮ" in s for s in statuses):
                    print(f"Данные RadCalNet за дату {date_only} ДОСТУПНЫ ПОЛНОСТЬЮ")
                elif any("ЧАСТИЧНО" in s for s in statuses):
                    print(f"Данные RadCalNet за дату {date_only} ДОСТУПНЫ ЧАСТИЧНО")
                else:
                    print(f"Данные RadCalNet за дату {date_only} НЕДОСТУПНЫ")


                if any("ПОЛНОСТЬЮ" in s or "ЧАСТИЧНО" in s for s in statuses):

                    print("\nЗапуск парсинга RadCalNet файлов...\n")

                    try:
                        parsed_data = read_radcalnet_by_date(
                            date = metadata['datetime'].date(),
                            folder = OUTPUT_DIR,
                            target_utc_time = metadata['datetime'].time(),
                            site = SITE
                        )

                        print("Парсинг успешно выполнен.\n")

                        print("Полученные ключи:")
                        print(parsed_data.keys())

                        print("\nUTC выбранного измерения:")
                        print(parsed_data["UTC"])

                        print("\n\nВсе полученные данные: ")
                        print(parsed_data)
                        
                    except Exception as e:
                        print("Ошибка при парсинге RadCalNet:")
                        print(e)

    else:
        print(f"Файл {xml_file} не найден")


