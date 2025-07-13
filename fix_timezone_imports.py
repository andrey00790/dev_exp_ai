#!/usr/bin/env python3
"""
Скрипт для исправления импортов timezone во всех файлах проекта
"""
import os
import re
import subprocess
from pathlib import Path

def fix_timezone_imports():
    """Исправляет импорты timezone в файлах проекта"""
    
    # Получаем список всех файлов с timezone.utc
    result = subprocess.run(['grep', '-r', '-l', 'timezone.utc', '--include=*.py', '.'], 
                          capture_output=True, text=True)
    
    if result.returncode != 0:
        print("Файлы с timezone.utc не найдены")
        return
    
    files_to_fix = result.stdout.strip().split('\n')
    
    print(f"Найдено {len(files_to_fix)} файлов для исправления")
    
    for file_path in files_to_fix:
        if not file_path or not os.path.exists(file_path):
            continue
            
        print(f"Исправляю файл: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Проверяем, есть ли уже timezone в импорте
            if 'from datetime import' in content and 'timezone' not in content:
                # Находим строку с импортом datetime
                datetime_import_pattern = r'from datetime import ([^\\n]+)'
                match = re.search(datetime_import_pattern, content)
                
                if match:
                    current_imports = match.group(1)
                    if 'timezone' not in current_imports:
                        # Добавляем timezone к существующим импортам
                        new_imports = current_imports.rstrip() + ', timezone'
                        content = content.replace(
                            f'from datetime import {current_imports}',
                            f'from datetime import {new_imports}'
                        )
                        
                        # Записываем обновленный файл
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        print(f"✅ Исправлен: {file_path}")
                    else:
                        print(f"⚠️  Уже исправлен: {file_path}")
                else:
                    print(f"❌ Не найден импорт datetime в: {file_path}")
            else:
                print(f"⚠️  Уже содержит timezone: {file_path}")
                
        except Exception as e:
            print(f"❌ Ошибка при обработке {file_path}: {e}")
    
    print("Исправление завершено!")

if __name__ == "__main__":
    fix_timezone_imports() 