#!/usr/bin/env python3
"""
Парсер прокси из API Telega
"""

import requests
import json
import time
import random
from datetime import datetime
from typing import List, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

# БЛОК 1: Одиночный запрос к API
def fetch_proxies_single(request_id: int) -> List[str]:
    url = "https://api.telega.info/v1/auth/proxy"
    headers = {
        "User-Agent": "DAHL-Mobile-App",
        "Accept": "application/json",
        "Accept-Encoding": "gzip"
    }
    
    try:
        # ⏱️ ЗАДЕРЖКА 1: Тайм-аут ожидания ответа от сервера (секунды)
        # ⚠️ ИЗМЕНЯЙТЕ ЭТО ЗНАЧЕНИЕ: больше = дольше ждём, но выше шанс получить ответ
        # ⚠️ меньше = быстрее отваливаемся, но можем пропустить медленные прокси
        response = requests.get(url, headers=headers, timeout=10)  # ← ИЗМЕНЯЙТЕ ТУТ (сейчас 10 сек)
        response.raise_for_status()
        data = response.json()
        
        if isinstance(data, dict) and 'proxies' in data:
            proxies = data['proxies']
        else:
            return []
        
        cleaned = []
        for p in proxies:
            if isinstance(p, str):
                p = p.replace('tcp://', '').replace('http://', '').replace('https://', '')
                p = p.strip()
                if p:
                    cleaned.append(p)
        return cleaned
    except Exception as e:
        print(f"⚠️ Запрос #{request_id} failed: {str(e)[:50]}")
        return []

# БЛОК 2: Множественные запросы и сбор уникальных прокси
def fetch_proxies_multiple(num_requests: int = 25, max_workers: int = 5) -> Set[str]:
    all_proxies = set()
    successful_requests = 0
    
    print(f"\n🚀 Отправляем {num_requests} запросов к API...")
    print(f"⚡ Параллельных потоков: {max_workers}")
    print("-" * 50)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_request = {
            executor.submit(fetch_proxies_single, i): i 
            for i in range(num_requests)
        }
        
        for future in as_completed(future_to_request):
            request_id = future_to_request[future]
            try:
                # ⏱️ ЗАДЕРЖКА 2: Тайм-аут обработки future (секунды)
                # ⚠️ ИЗМЕНЯЙТЕ ЭТО ЗНАЧЕНИЕ: должно быть БОЛЬШЕ чем timeout в запросе
                # ⚠️ сейчас 15 сек (на 5 сек больше timeout=10)
                proxies = future.result(timeout=15)  # ← ИЗМЕНЯЙТЕ ТУТ (сейчас 15 сек)
                if proxies:
                    successful_requests += 1
                    before = len(all_proxies)
                    all_proxies.update(proxies)
                    after = len(all_proxies)
                    print(f"✅ Запрос #{request_id}: +{len(proxies)} прокси, новых: {after - before}, всего: {after}")
                else:
                    print(f"❌ Запрос #{request_id}: нет прокси")
                
                # ⏱️ ЗАДЕРЖКА 3: Пауза между запросами (секунды)
                # ⚠️ ИЗМЕНЯЙТЕ ЭТИ ЗНАЧЕНИЯ: 
                # ⚠️ меньше = быстрее, но выше риск бана
                # ⚠️ больше = медленнее, но безопаснее для API
                # ⚠️ random.uniform(0.1, 0.3) = случайная задержка от 0.1 до 0.3 сек
                time.sleep(random.uniform(0.1, 0.3))  # ← ИЗМЕНЯЙТЕ ТУТ (сейчас 0.1-0.3 сек)
                
            except Exception as e:
                print(f"⚠️ Запрос #{request_id}: ошибка - {str(e)[:50]}")
    
    print("-" * 50)
    print(f"📊 Успешных запросов: {successful_requests}/{num_requests}")
    print(f"📊 Уникальных прокси собрано: {len(all_proxies)}")
    return all_proxies

# БЛОК 3: Сохранение прокси в файл (только новые)
def save_proxies(proxies: Set[str], filename: str = 'proxies_new.txt', num_requests: int = 25):
    sorted_proxies = sorted(list(proxies))
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"# Telega Proxy List\n")
        f.write(f"# Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Всего запросов: {num_requests}\n")
        f.write(f"# Уникальных прокси: {len(sorted_proxies)}\n")
        f.write("#" + "="*50 + "\n\n")
        for proxy in sorted_proxies:
            f.write(f"{proxy}\n")
    print(f"\n✅ Сохранено {len(sorted_proxies)} прокси в {filename}")
    return sorted_proxies

# БЛОК 4: Загрузка существующих прокси из файла
def load_existing_proxies(filename: str = 'proxies.txt') -> Set[str]:
    existing = set()
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    existing.add(line)
        print(f"📂 Загружено {len(existing)} существующих прокси из {filename}")
    except FileNotFoundError:
        print(f"📂 Файл {filename} не найден, создаем новый")
    return existing

# БЛОК 5: Объединение новых прокси с существующими
def merge_and_save(new_proxies: Set[str], filename: str = 'proxies.txt', num_requests: int = 25):
    existing = load_existing_proxies(filename)
    all_proxies = existing.union(new_proxies)
    sorted_proxies = sorted(list(all_proxies))
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"# Telega Proxy List\n")
        f.write(f"# Дата обновления: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Всего запросов: {num_requests}\n")
        f.write(f"# Всего уникальных: {len(sorted_proxies)}\n")
        f.write(f"# Новых добавлено: {len(new_proxies)}\n")
        f.write("#" + "="*50 + "\n\n")
        for proxy in sorted_proxies:
            f.write(f"{proxy}\n")
    
    print(f"\n✅ Итоговый файл {filename}:")
    print(f"   - Было: {len(existing)} прокси")
    print(f"   - Добавлено: {len(new_proxies)} новых")
    print(f"   - Всего: {len(sorted_proxies)} уникальных")
    return sorted_proxies

# БЛОК 6: Главная функция
def main():
    # ========== НАСТРОЙКИ (меняйте здесь) ==========
    NUM_REQUESTS = 25      # ← количество запросов
    MAX_WORKERS = 5        # ← количество параллельных потоков
    
    # ⏱️ ЗАДЕРЖКИ НАСТРАИВАЮТСЯ В БЛОКАХ ВЫШЕ:
    # - Тайм-аут ответа: строка 31 (сейчас 10 сек)
    # - Тайм-аут future: строка 75 (сейчас 15 сек)  
    # - Пауза между запросами: строка 92 (сейчас 0.1-0.3 сек)
    # ===============================================
    
    print("="*60)
    print(f"🚀 Telega Proxy Parser - {NUM_REQUESTS} запросов")
    print("="*60)
    print(f"📍 API: https://api.telega.info/v1/auth/proxy")
    print(f"🔧 User-Agent: DAHL-Mobile-App")
    print(f"📊 Параметры: {NUM_REQUESTS} запросов, удаление дубликатов")
    print("="*60)
    
    # Основной сбор прокси
    unique_proxies = fetch_proxies_multiple(num_requests=NUM_REQUESTS, max_workers=MAX_WORKERS)
    
    if not unique_proxies:
        print("\n❌ Не удалось получить ни одного прокси!")
        exit(1)
    
    # Сохранение результатов
    save_proxies(unique_proxies, 'proxies_new.txt', num_requests=NUM_REQUESTS)
    all_proxies = merge_and_save(unique_proxies, 'proxies.txt', num_requests=NUM_REQUESTS)
    
    # Итоговая статистика
    print(f"\n📊 Итог: {len(all_proxies)} уникальных прокси")
    if all_proxies:
        print("\n📋 Список:")
        for proxy in list(all_proxies)[:20]:
            print(f"   • {proxy}")
    
    print("\n✨ Файлы: proxies.txt (с накоплением) и proxies_new.txt (новые)")

if __name__ == "__main__":
    main()
