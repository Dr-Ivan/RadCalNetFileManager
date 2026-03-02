import xml.etree.ElementTree as ET
from datetime import datetime
import os



def parse_resurs_p_metadata(xml_file_path):
    """
    Парсит XML-файл метаданных Ресурс-П и извлекает дату и время съемки

    Args:
        xml_file_path (str): Путь к XML-файлу

    Returns:
        dict: Словарь с датой и временем съемки или None в случае ошибки
    """
    try:
        # Парсинг XML-файла
        tree = ET.parse(xml_file_path)
        root = tree.getroot()

        imaging_date = None
        imaging_time = None

        # Поиск во всей структуре XML
        for elem in root.iter():
            if elem.tag == 'IMAGING_DATE':
                imaging_date = elem.text
            elif elem.tag == 'IMAGING_TIME':
                imaging_time = elem.text

        if imaging_date and imaging_time:
            # Создать объект datetime
            datetime_str = f"{imaging_date}T{imaging_time}"
            imaging_datetime = datetime.fromisoformat(datetime_str)

            return {
                'date': imaging_date,
                'time': imaging_time,
                'datetime': imaging_datetime,
                'date_only': imaging_date # для поиска по сайту
            }
        else:
            print("Не удалось найти дату и время съемки в XML-файле")
            return None

    except ET.ParseError as e:
        print(f"Ошибка парсинга XML: {e}")
        return None
    except Exception as e:
        print(f"Общая ошибка: {e}")
        return None


# тестовый запуск
if __name__ == "__main__":
    xml_file = input("Введите путь к XML файлу (для запуска на тестовом файле введите пустую строку): ")

    if not xml_file:
        xml_file = "0041_0102_20858_1_00977_01_L1A.xml"

    if os.path.exists(xml_file):
        metadata = parse_resurs_p_metadata(xml_file)
        if metadata:
            print(f"Дата съемки: {metadata['date']}")
            print(f"Время съемки: {metadata['time']}")
            print(f"Полная дата-время: {metadata['datetime']}")
            print(f"Поиск на сайте по: {metadata['date_only']}")
    else:
        print(f"Файл {xml_file} не найден")