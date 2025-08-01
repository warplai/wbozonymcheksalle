import requests
import threading
import time
from tkinter import *
from tkinter import ttk, messagebox
from datetime import datetime


class MarketplaceManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Управление акциями на маркетплейсах")
        self.root.geometry("1200x800")

        # Переменные
        self.ozon_api_key = StringVar()
        self.ozon_client_id = StringVar()
        self.wb_api_key = StringVar()
        self.ym_api_key = StringVar()
        self.ym_campaign_id = StringVar()

        self.running = False
        self.auto_remove_enabled = BooleanVar(value=True)
        self.manual_remove_enabled = BooleanVar(value=False)
        self.logs = []
        self.last_run_time = None
        self.active_marketplaces = {
            'ozon': BooleanVar(value=False),
            'wb': BooleanVar(value=False),
            'ym': BooleanVar(value=False)
        }

        # Создание интерфейса
        self.create_widgets()

    def create_widgets(self):
        # Notebook для разных маркетплейсов
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=BOTH, expand=True, padx=10, pady=5)

        # Фрейм для Ozon
        ozon_frame = Frame(self.notebook)
        self.notebook.add(ozon_frame, text="Ozon")
        self.create_ozon_widgets(ozon_frame)

        # Фрейм для Wildberries
        wb_frame = Frame(self.notebook)
        self.notebook.add(wb_frame, text="Wildberries")
        self.create_wb_widgets(wb_frame)

        # Фрейм для Яндекс.Маркета
        ym_frame = Frame(self.notebook)
        self.notebook.add(ym_frame, text="Яндекс.Маркет")
        self.create_ym_widgets(ym_frame)

        # Фрейм параметров (только для Ozon и ЯМ)
        params_frame = LabelFrame(self.root, text="Параметры удаления (Ozon/ЯМ)", padx=10, pady=10)
        params_frame.pack(fill=X, padx=10, pady=5)

        Checkbutton(params_frame, text="Удалять товары добавленные автоматически",
                    variable=self.auto_remove_enabled).pack(anchor=W)
        Checkbutton(params_frame, text="Удалять товары добавленные вручную",
                    variable=self.manual_remove_enabled).pack(anchor=W)

        # Кнопки управления
        btn_frame = Frame(self.root)
        btn_frame.pack(fill=X, padx=10, pady=5)

        self.start_btn = Button(btn_frame, text="Запустить", command=self.toggle_service)
        self.start_btn.pack(side=LEFT, padx=5)

        Button(btn_frame, text="Проверить сейчас", command=self.run_once).pack(side=LEFT, padx=5)
        Button(btn_frame, text="Очистить логи", command=self.clear_logs).pack(side=LEFT, padx=5)

        # Логи
        log_frame = LabelFrame(self.root, text="Логи выполнения", padx=10, pady=10)
        log_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)

        self.log_text = Text(log_frame, height=15, state=DISABLED)
        self.log_text.pack(fill=BOTH, expand=True)

        scrollbar = Scrollbar(self.log_text)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_text.yview)

        # Таблица для WB
        self.wb_tree_frame = Frame(self.root)
        self.wb_tree_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)

        self.wb_tree = ttk.Treeview(self.wb_tree_frame,
                                    columns=('nmId', 'vendorCode', 'price', 'discount', 'discountedPrice'),
                                    show='headings')
        self.wb_tree.heading('nmId', text='Артикул WB')
        self.wb_tree.heading('vendorCode', text='Артикул продавца')
        self.wb_tree.heading('price', text='Цена')
        self.wb_tree.heading('discount', text='Скидка %')
        self.wb_tree.heading('discountedPrice', text='Цена со скидкой')

        self.wb_tree.column('nmId', width=100)
        self.wb_tree.column('vendorCode', width=150)
        self.wb_tree.column('price', width=100)
        self.wb_tree.column('discount', width=80)
        self.wb_tree.column('discountedPrice', width=120)

        self.wb_tree.pack(fill=BOTH, expand=True)

        # Статус бар
        self.status_var = StringVar(value="Готов к работе")
        status_bar = Label(self.root, textvariable=self.status_var, bd=1, relief=SUNKEN, anchor=W)
        status_bar.pack(fill=X, padx=10, pady=5)

    def create_ozon_widgets(self, parent):
        settings_frame = LabelFrame(parent, text="Настройки подключения Ozon", padx=10, pady=10)
        settings_frame.pack(fill=X, padx=10, pady=5)

        Label(settings_frame, text="API Key:").grid(row=0, column=0, sticky=W)
        Entry(settings_frame, textvariable=self.ozon_api_key, width=50).grid(row=0, column=1, padx=5, pady=2)

        Label(settings_frame, text="Client ID:").grid(row=1, column=0, sticky=W)
        Entry(settings_frame, textvariable=self.ozon_client_id, width=50).grid(row=1, column=1, padx=5, pady=2)

        Checkbutton(settings_frame, text="Активен", variable=self.active_marketplaces['ozon']).grid(row=2, column=0,
                                                                                                    columnspan=2,
                                                                                                    sticky=W)

    def create_wb_widgets(self, parent):
        settings_frame = LabelFrame(parent, text="Настройки подключения Wildberries", padx=10, pady=10)
        settings_frame.pack(fill=X, padx=10, pady=5)

        Label(settings_frame, text="API Key:").grid(row=0, column=0, sticky=W)
        Entry(settings_frame, textvariable=self.wb_api_key, width=50).grid(row=0, column=1, padx=5, pady=2)

        Checkbutton(settings_frame, text="Активен", variable=self.active_marketplaces['wb']).grid(row=1, column=0,
                                                                                                  columnspan=2,
                                                                                                  sticky=W)

    def create_ym_widgets(self, parent):
        settings_frame = LabelFrame(parent, text="Настройки подключения Яндекс.Маркет", padx=10, pady=10)
        settings_frame.pack(fill=X, padx=10, pady=5)

        Label(settings_frame, text="API Key:").grid(row=0, column=0, sticky=W)
        Entry(settings_frame, textvariable=self.ym_api_key, width=50).grid(row=0, column=1, padx=5, pady=2)

        Label(settings_frame, text="ID кампании:").grid(row=1, column=0, sticky=W)
        Entry(settings_frame, textvariable=self.ym_campaign_id, width=50).grid(row=1, column=1, padx=5, pady=2)

        Checkbutton(settings_frame, text="Активен", variable=self.active_marketplaces['ym']).grid(row=2, column=0,
                                                                                                  columnspan=2,
                                                                                                  sticky=W)

    def toggle_service(self):
        if not self.running:
            if not self.validate_credentials():
                return

            self.running = True
            self.start_btn.config(text="Остановить")
            self.status_var.set("Сервис запущен - проверка каждые 3 минуты")
            self.log("Сервис автоматического удаления запущен")
            threading.Thread(target=self.run_service, daemon=True).start()
        else:
            self.running = False
            self.start_btn.config(text="Запустить")
            self.status_var.set("Сервис остановлен")
            self.log("Сервис автоматического удаления остановлен")

    def run_service(self):
        while self.running:
            self.run_once()
            for i in range(1800):  # 30 минут
                if not self.running:
                    return
                time.sleep(1)

    def run_once(self):
        try:
            self.last_run_time = datetime.now()
            self.status_var.set(f"Проверка акций... {self.last_run_time.strftime('%H:%M:%S')}")

            # Проверяем Ozon
            if self.active_marketplaces['ozon'].get():
                ozon_removed = self.process_ozon()
                self.log(f"[Ozon] Удалено товаров: {ozon_removed}")

            # Проверяем Wildberries (только мониторинг)
            if self.active_marketplaces['wb'].get():
                self.process_wildberries()

            # Проверяем Яндекс.Маркет
            if self.active_marketplaces['ym'].get():
                ym_removed = self.process_yandex_market()
                self.log(f"[ЯМ] Удалено товаров: {ym_removed}")

            self.status_var.set(f"Готово. Последняя проверка: {self.last_run_time.strftime('%H:%M:%S')}")

        except Exception as e:
            self.log(f"Ошибка: {str(e)}")
            messagebox.showerror("Ошибка", str(e))

    def process_ozon(self):
        """Обработка акций Ozon (удаление товаров)"""
        try:
            promotions = self.get_ozon_promotions()
            self.log(f"[Ozon] Найдено акций: {len(promotions)}")

            removed = 0
            for promo in promotions:
                items = self.get_ozon_promo_items(promo['id'])
                items_to_remove = self.filter_items(items)

                for item in items_to_remove:
                    if self.remove_from_ozon_promo(promo['id'], item['id']):
                        removed += 1
            return removed
        except Exception as e:
            self.log(f"[Ozon] Ошибка: {str(e)}")
            return 0

    def process_wildberries(self):
        """Мониторинг акций Wildberries (без удаления)"""
        try:
            # Очищаем предыдущие данные
            for i in self.wb_tree.get_children():
                self.wb_tree.delete(i)

            items = self.get_wb_items_with_discounts()
            self.log(f"[WB] Найдено товаров с акциями: {len(items)}")

            # Заполняем таблицу
            for item in items:
                price = item['sizes'][0]['price'] if item.get('sizes') else 0
                discounted_price = item['sizes'][0]['discountedPrice'] if item.get('sizes') else 0

                self.wb_tree.insert('', 'end', values=(
                    item.get('nmID', ''),
                    item.get('vendorCode', ''),
                    f"{price:.2f} ₽",
                    f"{item.get('discount', 0)}%",
                    f"{discounted_price:.2f} ₽"
                ))

            return len(items)
        except Exception as e:
            self.log(f"[WB] Ошибка: {str(e)}")
            return 0

    def process_yandex_market(self):
        """Обработка акций Яндекс.Маркет (удаление товаров)"""
        try:
            campaigns = self.get_ym_campaigns()
            self.log(f"[ЯМ] Найдено кампаний: {len(campaigns)}")

            removed = 0
            for campaign in campaigns:
                offers = self.get_ym_campaign_offers(campaign['id'])
                offers_to_remove = self.filter_ym_offers(offers)

                for offer in offers_to_remove:
                    if self.remove_from_ym_campaign(campaign['id'], offer['offerId']):
                        removed += 1
            return removed
        except Exception as e:
            self.log(f"[ЯМ] Ошибка: {str(e)}")
            return 0

    # Методы для Ozon (оставляем без изменений)
    def get_ozon_promotions(self):
        """Получаем список акций Ozon"""
        url = "https://api-seller.ozon.ru/v1/actions"
        headers = {
            "Client-Id": self.ozon_client_id.get().strip(),
            "Api-Key": self.ozon_api_key.get().strip(),
            "Content-Type": "application/json"
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json().get('result', [])
        except Exception as e:
            self.log(f"[Ozon] Ошибка при получении акций: {str(e)}")
            return []

    def get_ozon_promo_items(self, action_id):
        """Получаем товары в акции Ozon"""
        url = "https://api-seller.ozon.ru/v1/actions/products"
        headers = {
            "Client-Id": self.ozon_client_id.get().strip(),
            "Api-Key": self.ozon_api_key.get().strip(),
            "Content-Type": "application/json"
        }
        payload = {"action_id": action_id, "limit": 1000}
        try:
            response = requests.post(url, headers=headers, json=payload)
            result = response.json().get('result', {})
            products = result.get('products', [])
            for product in products:
                product['add_mode'] = product.get('add_mode', 'UNKNOWN')
            return products
        except Exception as e:
            self.log(f"[Ozon] Ошибка при получении товаров: {str(e)}")
            return []

    def remove_from_ozon_promo(self, action_id, product_id):
        """Удаляем товар из акции Ozon"""
        url = "https://api-seller.ozon.ru/v1/actions/products/deactivate"
        headers = {
            "Client-Id": self.ozon_client_id.get().strip(),
            "Api-Key": self.ozon_api_key.get().strip(),
            "Content-Type": "application/json"
        }
        payload = {"action_id": action_id, "product_ids": [product_id]}
        try:
            response = requests.post(url, headers=headers, json=payload)
            return response.status_code == 200
        except Exception as e:
            self.log(f"[Ozon] Ошибка при удалении товара: {str(e)}")
            return False

    # Методы для Wildberries (только мониторинг)
    def get_wb_items_with_discounts(self):
        """Получаем товары Wildberries с акциями"""
        url = "https://discounts-prices-api.wildberries.ru/api/v2/list/goods/filter"
        headers = {"Authorization": self.wb_api_key.get().strip()}
        params = {"limit": 1000, "offset": 0}

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            if 'data' not in data or 'listGoods' not in data['data']:
                self.log("[WB] Неверный формат ответа API")
                return []

            items = data['data']['listGoods']
            # Фильтруем товары с ненулевой скидкой
            return [item for item in items if item.get('discount', 0) > 0]

        except Exception as e:
            self.log(f"[WB] Ошибка при получении товаров: {str(e)}")
            return []

    # Методы для Яндекс.Маркета (оставляем без изменений)
    def get_ym_campaigns(self):
        """Получаем список акций Яндекс.Маркет"""
        url = f"https://api.partner.market.yandex.ru/v2/campaigns/{self.ym_campaign_id.get().strip()}/offers/mapping.json"
        headers = {"Authorization": f"OAuth oauth_token=\"{self.ym_api_key.get().strip()}\", oauth_client_id=\"\""}
        try:
            response = requests.get(url, headers=headers)
            return response.json().get('result', {}).get('campaigns', [])
        except Exception as e:
            self.log(f"[ЯМ] Ошибка при получении кампаний: {str(e)}")
            return []

    def get_ym_campaign_offers(self, campaign_id):
        """Получаем товары в акции Яндекс.Маркет"""
        url = f"https://api.partner.market.yandex.ru/v2/campaigns/{campaign_id}/offers.json"
        headers = {"Authorization": f"OAuth oauth_token=\"{self.ym_api_key.get().strip()}\", oauth_client_id=\"\""}
        try:
            response = requests.get(url, headers=headers)
            return response.json().get('result', {}).get('offers', [])
        except Exception as e:
            self.log(f"[ЯМ] Ошибка при получении товаров: {str(e)}")
            return []

    def remove_from_ym_campaign(self, campaign_id, offer_id):
        """Удаляем товар из акции Яндекс.Маркет"""
        url = f"https://api.partner.market.yandex.ru/v2/campaigns/{campaign_id}/offers/{offer_id}/discount/delete.json"
        headers = {
            "Authorization": f"OAuth oauth_token=\"{self.ym_api_key.get().strip()}\", oauth_client_id=\"\"",
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(url, headers=headers)
            return response.status_code == 200
        except Exception as e:
            self.log(f"[ЯМ] Ошибка при удалении товара: {str(e)}")
            return False

    # Общие методы
    def filter_items(self, items):
        """Фильтр товаров для Ozon"""
        filtered = []
        for item in items:
            add_mode = item.get('add_mode', 'UNKNOWN')
            if self.auto_remove_enabled.get() and add_mode == 'AUTO':
                filtered.append(item)
            elif self.manual_remove_enabled.get() and add_mode == 'MANUAL':
                filtered.append(item)
        return filtered

    def filter_ym_offers(self, offers):
        """Фильтр товаров для Яндекс.Маркет"""
        return [offer for offer in offers if offer.get('discount', 0) > 0]

    def validate_credentials(self):
        """Проверка учетных данных"""
        valid = False

        if self.active_marketplaces['ozon'].get():
            if not self.ozon_api_key.get() or not self.ozon_client_id.get():
                messagebox.showerror("Ошибка", "Введите API Key и Client ID для Ozon")
                return False

            try:
                test_url = "https://api-seller.ozon.ru/v1/actions"
                headers = {
                    "Client-Id": self.ozon_client_id.get().strip(),
                    "Api-Key": self.ozon_api_key.get().strip(),
                    "Content-Type": "application/json"
                }
                response = requests.get(test_url, headers=headers)
                valid = response.status_code == 200
            except Exception as e:
                messagebox.showerror("Ошибка", f"Неверные учетные данные Ozon: {str(e)}")
                return False

        if self.active_marketplaces['wb'].get():
            if not self.wb_api_key.get():
                messagebox.showerror("Ошибка", "Введите API Key для Wildberries")
                return False

            try:
                test_url = "https://discounts-prices-api.wildberries.ru/api/v2/list/goods/filter"
                headers = {"Authorization": self.wb_api_key.get().strip()}
                params = {"limit": 1}
                response = requests.get(test_url, headers=headers, params=params)
                valid = response.status_code == 200
            except Exception as e:
                messagebox.showerror("Ошибка", f"Неверные учетные данные Wildberries: {str(e)}")
                return False

        if self.active_marketplaces['ym'].get():
            if not self.ym_api_key.get() or not self.ym_campaign_id.get():
                messagebox.showerror("Ошибка", "Введите API Key и ID кампании для Яндекс.Маркет")
                return False

            try:
                test_url = f"https://api.partner.market.yandex.ru/v2/campaigns/{self.ym_campaign_id.get().strip()}/offers/mapping.json"
                headers = {
                    "Authorization": f"OAuth oauth_token=\"{self.ym_api_key.get().strip()}\", oauth_client_id=\"\""}
                response = requests.get(test_url, headers=headers)
                valid = response.status_code == 200
            except Exception as e:
                messagebox.showerror("Ошибка", f"Неверные учетные данные Яндекс.Маркет: {str(e)}")
                return False

        if not any(var.get() for var in self.active_marketplaces.values()):
            messagebox.showerror("Ошибка", "Выберите хотя бы один активный маркетплейс")
            return False

        return valid

    def log(self, message):
        """Логирование сообщений"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        self.logs.append(log_message)

        self.log_text.config(state=NORMAL)
        self.log_text.insert(END, log_message + "\n")
        self.log_text.config(state=DISABLED)
        self.log_text.see(END)

    def clear_logs(self):
        """Очистка логов"""
        self.logs = []
        self.log_text.config(state=NORMAL)
        self.log_text.delete(1.0, END)
        self.log_text.config(state=DISABLED)


if __name__ == "__main__":
    root = Tk()
    app = MarketplaceManager(root)
    root.mainloop()