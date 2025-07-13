#!/usr/bin/env python3
"""
Comprehensive timezone imports fix script
"""
import os
import re
import subprocess
from pathlib import Path

def fix_timezone_imports():
    """Исправляет все импорты datetime, добавляя timezone где необходимо"""
    
    # Получаем все файлы с импортом datetime без timezone
    result = subprocess.run([
        'grep', '-r', '-l', 'from datetime import.*datetime', '--include=*.py', '.'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print("Файлы с datetime не найдены")
        return
    
    files_with_datetime = result.stdout.strip().split('\n')
    fixed_count = 0
    
    for file_path in files_with_datetime:
        if not file_path or not os.path.exists(file_path):
            continue
        
        # Пропускаем файлы venv
        if 'venv/' in file_path:
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Проверяем, используется ли timezone.utc в файле
            if 'timezone.utc' in content or 'timezone.' in content:
                # Ищем строки с импортом datetime
                lines = content.split('\n')
                modified = False
                
                for i, line in enumerate(lines):
                    if 'from datetime import' in line and 'datetime' in line and 'timezone' not in line:
                        # Добавляем timezone к импорту
                        if line.strip().endswith('datetime'):
                            lines[i] = line + ', timezone'
                            modified = True
                        elif ', datetime' in line and not line.strip().endswith('timezone'):
                            lines[i] = line + ', timezone'
                            modified = True
                        elif 'datetime,' in line and 'timezone' not in line:
                            lines[i] = line.replace('datetime,', 'datetime, timezone,')
                            modified = True
                
                if modified:
                    # Записываем обновленный файл
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(lines))
                    
                    print(f"✅ Исправлен: {file_path}")
                    fixed_count += 1
                else:
                    print(f"⚠️  Уже исправлен: {file_path}")
            else:
                print(f"➖ Не использует timezone: {file_path}")
                
        except Exception as e:
            print(f"❌ Ошибка при обработке {file_path}: {e}")
    
    print(f"\nИсправление завершено! Обработано файлов: {fixed_count}")

if __name__ == "__main__":
    fix_timezone_imports() 