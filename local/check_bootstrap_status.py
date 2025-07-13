#!/usr/bin/env python3
"""
Проверка статуса bootstrap обучения
"""

import os
import sys
import json
from pathlib import Path

try:
    import requests
except ImportError:
    print("❌ Требуется установить requests: pip install requests")
    sys.exit(1)

def check_qdrant_status():
    """Проверка статуса Qdrant коллекций"""
    qdrant_url = os.getenv('QDRANT_URL', 'http://localhost:6333')
    
    try:
        response = requests.get(f'{qdrant_url}/collections', timeout=5)
        if response.status_code == 200:
            collections = response.json()
            print('🔍 Qdrant коллекции:')
            for collection in collections.get('result', {}).get('collections', []):
                name = collection.get('name')
                print(f'  • {name}')
                # Получаем информацию о коллекции
                info_response = requests.get(f'{qdrant_url}/collections/{name}', timeout=5)
                if info_response.status_code == 200:
                    info = info_response.json()
                    vectors_count = info.get('result', {}).get('vectors_count', 0)
                    points_count = info.get('result', {}).get('points_count', 0)
                    print(f'    Векторов: {vectors_count}, Документов: {points_count}')
        else:
            print('❌ Qdrant недоступен')
    except Exception as e:
        print(f'❌ Ошибка проверки статуса Qdrant: {e}')

def check_local_files():
    """Проверка локальных файлов"""
    print()
    print('📁 Локальные файлы:')
    
    bootstrap_dir = Path('./local/bootstrap')
    if bootstrap_dir.exists():
        file_count = len(list(bootstrap_dir.rglob('*.*')))
        print(f'  Файлов в bootstrap/: {file_count}')
        for category_dir in bootstrap_dir.iterdir():
            if category_dir.is_dir():
                category_files = len(list(category_dir.rglob('*.*')))
                print(f'  • {category_dir.name}/: {category_files} файлов')
    else:
        print('  Bootstrap директория не найдена')

def main():
    """Основная функция"""
    print("📊 Статус bootstrap обучения:")
    print()
    
    # Проверяем Qdrant
    check_qdrant_status()
    
    # Проверяем локальные файлы
    check_local_files()

if __name__ == "__main__":
    main() 