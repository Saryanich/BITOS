# -*- coding: utf-8 -*-
import os, sys, time, shutil, zipfile, subprocess, platform

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_DIR = os.path.join(BASE_PATH, "system", "Temp", "updates")

def main():
    print("=" * 50)
    print("УСТАНОВКА ОБНОВЛЕНИЯ BITOS")
    print("=" * 50)
    
    # Ждем чтобы основная программа закрылась
    print("\nОжидание 10 секунд...")
    for i in range(10, 0, -1):
        print(f"Осталось {i} сек...", end='\r')
        time.sleep(1)
    print("\n")
    
    # Ищем zip файл обновления (берём самый свежий по времени изменения,
    # а не по алфавитной сортировке имён — иначе можно взять не тот файл)
    zip_files = [f for f in os.listdir(TEMP_DIR) if f.endswith('.zip')]
    if not zip_files:
        print("❌ Файл обновления не найден!")
        input("Нажмите Enter для выхода...")
        sys.exit(1)
    
    zip_candidates = [os.path.join(TEMP_DIR, f) for f in zip_files]
    zip_path = max(zip_candidates, key=os.path.getmtime)
    print(f"📦 Найден файл: {os.path.basename(zip_path)}")
    
    # Извлекаем архив
    extract_path = os.path.join(TEMP_DIR, "extracted")
    if os.path.exists(extract_path):
        shutil.rmtree(extract_path)
    os.makedirs(extract_path)
    
    print("📦 Извлечение обновления...")
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(extract_path)
    
    # Находим корневую папку модульного проекта. Архив может содержать
    # директорию репозитория (например, BITOS-main/bitos/).
    code_path = extract_path
    candidates = []
    for root, dirs, files in os.walk(extract_path):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git")]
        if "server" in dirs and "ui" in dirs:
            candidates.append(root)
            break
    if candidates:
        code_path = candidates[0]
    else:
        for item in os.listdir(extract_path):
            full_path = os.path.join(extract_path, item)
            if os.path.isdir(full_path) and ("BITOS" in item or "06V" in item or item.lower() == "bitos"):
                code_path = full_path
                break

    print(f"📁 Папка с кодом: {os.path.basename(code_path)}")
    
    # Копируем файлы (пропускаем System для сохранения настроек)
    print("\n⚙️ Установка файлов...")
    updated = 0
    errors = 0
    
    for item in os.listdir(code_path):
        if item.lower() == 'system':
            print(f"  ⏭ Пропущено: {item}/ (настройки сохранены)")
            continue
        
        src = os.path.join(code_path, item)
        dst = os.path.join(BASE_PATH, item)
        
        try:
            # Удаляем старый файл/папку
            if os.path.exists(dst):
                if os.path.isdir(dst):
                    shutil.rmtree(dst)
                else:
                    os.remove(dst)
            
            # Копируем новый
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
            
            print(f"  ✅ {item}")
            updated += 1
        except Exception as e:
            print(f"  ❌ {item}: {e}")
            errors += 1
    
    print(f"\n{'=' * 50}")
    print(f"✅ Установлено: {updated} файлов")
    if errors > 0:
        print(f"❌ Ошибок: {errors}")
    print(f"{'=' * 50}")
    
    # Удаляем архив и временные файлы
    try:
        os.remove(zip_path)
        if os.path.exists(extract_path):
            shutil.rmtree(extract_path)
    except:
        pass
    
    # Перезагрузка
    print("\n🔄 Перезагрузка через 5 секунд...")
    time.sleep(5)
    
    try:
        if platform.system() == "Windows":
            subprocess.Popen(["shutdown", "/r", "/t", "3", "/f"], shell=True)
        else:
            subprocess.Popen(["reboot"])
    except Exception as e:
        print(f"❌ Не удалось перезагрузить: {e}")
        print("Пожалуйста, перезагрузите систему вручную.")
        input("Нажмите Enter для выхода...")
    
    sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        input("\nНажмите Enter для выхода...")
        sys.exit(1)
