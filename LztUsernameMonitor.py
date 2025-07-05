import requests
import time
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
import sys

class LolzteamUsernameMonitor:
    def __init__(self):
        self.api_base = "https://prod-api.lolz.live"
        self.session = requests.Session()
        self.config_file = "username_monitor_config.json"
        self.log_file = "username_monitor.log"
        
    def log_message(self, message: str, level: str = "INFO"):
        timestamp = datetime.now(timezone(timedelta(hours=3))).strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
    
    def save_config(self, config: Dict[str, Any]):
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    
    def load_config(self) -> Optional[Dict[str, Any]]:
        if os.path.exists(self.config_file):
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
    
    def setup_configuration(self):
        print("=" * 60)
        print("🔧 LOLZTEAM USERNAME MONITOR - НАСТРОЙКА")
        print("=" * 60)
        
        config = {}
        
        print("\n📋 Шаг 1: API токен")
        while True:
            token = input("Введите ваш API токен: ").strip()
            if token:
                config["api_token"] = token
                break
            print("❌ Токен не может быть пустым!")
        
        print("\n👤 Шаг 2: Ваш User ID")
        while True:
            try:
                user_id = int(input("Введите ваш User ID: ").strip())
                config["user_id"] = user_id
                break
            except ValueError:
                print("❌ User ID должен быть числом!")
        
        print("\n🎯 Шаг 3: Желаемый юзернейм")
        while True:
            username = input("Введите желаемый юзернейм: ").strip()
            if username:
                config["target_username"] = username
                break
            print("❌ Юзернейм не может быть пустым!")
        
        print("\n⏱️ Шаг 4: Интервал проверки")
        while True:
            try:
                interval = int(input("Введите интервал проверки в секундах (минимум 1): ").strip())
                if interval >= 1:
                    config["check_interval"] = interval
                    break
                print("❌ Интервал должен быть не менее 1 секунды!")
            except ValueError:
                print("❌ Интервал должен быть числом!")
        
        print("\n📅 Шаг 5: Режим работы")
        print("1. Постоянная проверка (начать сейчас)")
        print("2. Запланированный запуск (начать с определенной даты)")
        
        while True:
            mode = input("Выберите режим (1 или 2): ").strip()
            if mode == "1":
                config["mode"] = "continuous"
                config["start_time"] = None
                break
            elif mode == "2":
                config["mode"] = "scheduled"
                print("\n📅 Введите дату и время запуска (UTC+3):")
                while True:
                    try:
                        date_str = input("Дата и время (YYYY-MM-DD HH:MM): ").strip()
                        start_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                        start_time = start_time.replace(tzinfo=timezone(timedelta(hours=3)))
                        config["start_time"] = start_time.isoformat()
                        break
                    except ValueError:
                        print("❌ Неверный формат! Используйте YYYY-MM-DD HH:MM")
                break
            else:
                print("❌ Выберите 1 или 2!")
        
        self.save_config(config)
        
        print("\n✅ Конфигурация сохранена!")
        print(f"🎯 Цель: {config['target_username']}")
        print(f"⏱️ Интервал: {config['check_interval']} сек")
        if config['mode'] == 'scheduled':
            print(f"📅 Старт: {config['start_time']}")
        else:
            print("🔄 Режим: Постоянная проверка")
        
        return config
    
    def test_api_connection(self, token: str, user_id: int) -> bool:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = self.session.get(f"{self.api_base}/users/{user_id}", headers=headers)
            if response.status_code == 200:
                self.log_message("✅ API соединение установлено успешно")
                return True
            elif response.status_code == 401:
                self.log_message("❌ Неверный API токен", "ERROR")
                return False
            elif response.status_code == 404:
                self.log_message("❌ Пользователь не найден", "ERROR")
                return False
            else:
                self.log_message(f"❌ Ошибка API: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log_message(f"❌ Ошибка соединения: {e}", "ERROR")
            return False
    
    def check_username_availability(self, token: str, user_id: int, username: str) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        data = {"username": username}
        
        try:
            response = self.session.put(f"{self.api_base}/users/{user_id}", headers=headers, json=data)
            
            result = {
                "status_code": response.status_code,
                "success": False,
                "message": "",
                "response_data": None
            }
            
            try:
                response_data = response.json()
                result["response_data"] = response_data
            except:
                result["response_data"] = response.text
            
            if response.status_code == 200:
                result["success"] = True
                result["message"] = "🎉 ЮЗЕРНЕЙМ УСПЕШНО ЗАНЯТ!"
                self.log_message(f"🎉 SUCCESS! Юзернейм '{username}' успешно занят!", "SUCCESS")
                
            elif response.status_code == 400:
                if isinstance(result["response_data"], dict):
                    if "errors" in result["response_data"]:
                        errors = result["response_data"]["errors"]
                        if "username" in errors:
                            if "taken" in str(errors["username"]).lower():
                                result["message"] = f"❌ Юзернейм '{username}' уже занят"
                            elif "invalid" in str(errors["username"]).lower():
                                result["message"] = f"❌ Юзернейм '{username}' недопустим"
                            else:
                                result["message"] = f"❌ Ошибка юзернейма: {errors['username']}"
                        else:
                            result["message"] = f"❌ Ошибка запроса: {errors}"
                    else:
                        result["message"] = "❌ Неверный запрос (400)"
                else:
                    result["message"] = "❌ Неверный запрос (400)"
                    
            elif response.status_code == 401:
                result["message"] = "❌ Неавторизован - проверьте токен"
                
            elif response.status_code == 403:
                if isinstance(result["response_data"], dict):
                    if "errors" in result["response_data"]:
                        errors = result["response_data"]["errors"]
                        if isinstance(errors, list) and len(errors) > 0:
                            error_msg = errors[0]
                            if "занят" in error_msg.lower():
                                result["message"] = f"⏳ Юзернейм '{username}' пока занят (ожидание освобождения)"
                            else:
                                result["message"] = f"❌ {error_msg}"
                        else:
                            result["message"] = f"❌ Ошибка: {errors}"
                    else:
                        result["message"] = "❌ Доступ запрещен"
                else:
                    result["message"] = "❌ Доступ запрещен"
                
            elif response.status_code == 404:
                result["message"] = "❌ Пользователь не найден"
                
            elif response.status_code == 429:
                result["message"] = "⏳ Превышен лимит запросов - ожидание"
                
            elif response.status_code >= 500:
                result["message"] = f"❌ Ошибка сервера ({response.status_code})"
                
            else:
                result["message"] = f"❌ Неизвестная ошибка ({response.status_code})"
            
            return result
            
        except requests.exceptions.RequestException as e:
            return {
                "status_code": 0,
                "success": False,
                "message": f"❌ Ошибка сети: {e}",
                "response_data": None
            }
    
    def wait_for_scheduled_time(self, start_time_str: str):
        target_time = datetime.fromisoformat(start_time_str)
        current_time = datetime.now(timezone(timedelta(hours=3)))
        
        if current_time >= target_time:
            self.log_message("📅 Время старта уже прошло, начинаем мониторинг")
            return
        
        time_diff = (target_time - current_time).total_seconds()
        self.log_message(f"⏰ Ожидание до {target_time.strftime('%Y-%m-%d %H:%M:%S')} (UTC+3)")
        self.log_message(f"⏳ Осталось: {int(time_diff)} секунд")
        
        while current_time < target_time:
            time.sleep(min(60, time_diff))
            current_time = datetime.now(timezone(timedelta(hours=3)))
            time_diff = (target_time - current_time).total_seconds()
            
            if time_diff > 0:
                if time_diff > 3600:
                    hours = int(time_diff // 3600)
                    minutes = int((time_diff % 3600) // 60)
                    self.log_message(f"⏳ Осталось: {hours}ч {minutes}м")
                elif time_diff > 60:
                    minutes = int(time_diff // 60)
                    self.log_message(f"⏳ Осталось: {minutes}м")
                else:
                    self.log_message(f"⏳ Осталось: {int(time_diff)}с")
    
    def monitor_username(self, config: Dict[str, Any]):
        self.log_message("🚀 Запуск мониторинга юзернейма")
        self.log_message(f"🎯 Цель: {config['target_username']}")
        self.log_message(f"⏱️ Интервал: {config['check_interval']} сек")
        
        if not self.test_api_connection(config["api_token"], config["user_id"]):
            self.log_message("❌ Не удалось подключиться к API", "ERROR")
            return
        
        if config["mode"] == "scheduled" and config["start_time"]:
            self.wait_for_scheduled_time(config["start_time"])
        
        self.log_message("🔄 Начинаем мониторинг...")
        
        attempt_count = 0
        success = False
        
        try:
            while not success:
                attempt_count += 1
                
                self.log_message(f"🔍 Попытка #{attempt_count}: проверка '{config['target_username']}'")
                
                result = self.check_username_availability(
                    config["api_token"],
                    config["user_id"],
                    config["target_username"]
                )
                
                if result["success"]:
                    self.log_message(result["message"], "SUCCESS")
                    self.log_message(f"✅ Мониторинг завершен после {attempt_count} попыток!", "SUCCESS")
                    success = True
                    break
                else:
                    self.log_message(result["message"])
                    
                    if result["status_code"] == 429:
                        self.log_message("⏳ Ожидание 60 секунд из-за лимита...")
                        time.sleep(60)
                    elif result["status_code"] == 0:
                        self.log_message("⏳ Ожидание 30 секунд из-за ошибки сети...")
                        time.sleep(30)
                    elif result["status_code"] >= 500:
                        self.log_message("⏳ Ожидание 10 секунд из-за ошибки сервера...")
                        time.sleep(10)
                    else:
                        time.sleep(config["check_interval"])
                
        except KeyboardInterrupt:
            self.log_message("⏹️ Мониторинг остановлен пользователем")
        except Exception as e:
            self.log_message(f"💥 Критическая ошибка: {e}", "ERROR")
    
    def run(self):
        print("🎯 LOLZTEAM USERNAME MONITOR")
        print("=" * 40)
        
        config = self.load_config()
        
        if config is None:
            print("📋 Конфигурация не найдена. Запуск настройки...")
            config = self.setup_configuration()
        else:
            print("✅ Конфигурация найдена!")
            print(f"🎯 Цель: {config['target_username']}")
            print(f"⏱️ Интервал: {config['check_interval']} сек")
            
            choice = input("\n1. Запустить мониторинг\n2. Перенастроить\nВыбор (1/2): ").strip()
            
            if choice == "2":
                config = self.setup_configuration()
        
        print("\n" + "="*40)
        input("Нажмите Enter для запуска мониторинга...")
        
        self.monitor_username(config)

if __name__ == "__main__":
    monitor = LolzteamUsernameMonitor()
    monitor.run()
