import cv2
import pytesseract
import re
import os
import difflib

# ---------------------------------------------------------
tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
tessdata_path = r'C:\Program Files\Tesseract-OCR\tessdata'
os.environ['TESSDATA_PREFIX'] = tessdata_path

if os.path.exists(tesseract_path):
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
else:
    print(f"ВНИМАНИЕ! Не найден файл {tesseract_path}")
# ---------------------------------------------------------

def format_time(seconds):
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"

def clean_text(text):
    """Очищает текст, но ТЕПЕРЬ СОХРАНЯЕТ переносы строк для абзацев"""
    # Оставляем кириллицу, латиницу, цифры, знаки препинания И переносы строк (\n)
    text = re.sub(r'[^а-яА-ЯёЁa-zA-Z0-9\s.,:;!?\-"\'()\[\]\n]', '', text)
    # Убираем лишние пробелы в строках, но оставляем \n
    text = re.sub(r'[ \t]+', ' ', text)
    # Убираем слишком много пустых строк подряд (больше двух)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def is_similar(text1, text2, ratio=0.8):
    if not text1 or not text2:
        return False
    return difflib.SequenceMatcher(None, text1, text2).ratio() > ratio

def extract_text_from_video(video_path, output_txt_path):
    print(f"Открываю видео: {video_path}")
    cap = cv2.VideoCapture(video_path)
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        print("Не удалось определить FPS видео. Проверьте файл.")
        return

    last_text = ""
    
    with open(output_txt_path, 'w', encoding='utf-8') as f:
        print(f"Начинаю анализ (ПОЛНЫЙ ЭКРАН). Это может занять больше времени...\n")
        
        current_frame = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            if current_frame % int(fps) == 0:
                current_time_sec = current_frame / fps
                
                # --- ИЗМЕНЕНИЕ: БОЛЬШЕ НЕТ ОБРЕЗКИ КАДРА ---
                # Используем весь кадр (frame) целиком
                
                # Улучшение картинки
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                # Увеличение картинки для четкости мелкого шрифта (газеты)
                gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
                _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
                thresh = cv2.bitwise_not(thresh)

                # --- ИЗМЕНЕНИЕ: PSM 3 (Автоматическое распознавание страницы) ---
                custom_config = r'--oem 3 --psm 3'
                
                try:
                    raw_text = pytesseract.image_to_string(thresh, lang='rus', config=custom_config)
                except Exception as e:
                    print(f"\nКритическая ошибка Tesseract: {e}")
                    return
                
                text = clean_text(raw_text)
                
                if text and len(text) > 2:
                    if not is_similar(text, last_text, ratio=0.85):
                        time_str = format_time(current_time_sec)
                        
                        # --- ИЗМЕНЕНИЕ: КРАСИВЫЙ ФОРМАТ ЗАПИСИ ---
                        # Если текст длинный (несколько строк), пишем время сверху, а текст под ним
                        if '\n' in text:
                            block = f"\n[{time_str}]\n{text}\n"
                        else:
                            # Если это просто короткий субтитр, пишем в одну строку
                            block = f"[{time_str}] {text}\n"
                        
                        print(block, end="")
                        f.write(block)
                        f.flush()
                        
                        last_text = text
                    
            current_frame += 1

    cap.release()
    print(f"\nГотово! Реплики сохранены в {output_txt_path}")

if __name__ == "__main__":
    print("=== Извлечение текста со всего экрана ===")
    
    VIDEO_PATH = r"C:\Users\bykov\tlou.mp4"
    
    VIDEO_PATH = VIDEO_PATH.strip('\"\'')
    
    if os.path.exists(VIDEO_PATH):
        output_name = f"{os.path.splitext(VIDEO_PATH)[0]}_реплики.txt"
        extract_text_from_video(VIDEO_PATH, output_name)
    else:
        print(f"Ошибка: Файл по пути '{VIDEO_PATH}' не найден!")