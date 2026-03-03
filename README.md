### <span style="color: #32CD32">✔</span> Структура проєкту

```
web_scraper_group_6/
│
├── .venv/                     # Віртуальне оточення Python
│
├── src/                       # Основна директорія з вихідним кодом
│   ├── main.py                # Основний файл з точкою входу
│   ├── scraper.py             # Логіка скрапінгу
│   ├── models.py              # Моделі даних
│   └── utils/                 # Допоміжні модулі
│       ├── logger.py          # Налаштування логування
│       ├── file_handlers.py   # Робота з файлами
│       └── selenium_utils.py  # Selenium WebDriver утиліти
│
├── data/                      # Директорія для збережених даних
│   └── products.csv           # Експортовані дані
│
├── logs/                      # Логи роботи скрапера
│   └── parser.log
│
├── requirements.txt           # Залежності проекту
└── README.md                  # Документація проекту
```