# Вбудовані модулі TML

Мова TML надає набір модулів для взаємодії з системою, мишею, клавіатурою та іншими ресурсами.

## mouse
Керування курсором миші.
- `mouse.move(x, y)` — перемістити курсор у координати (x, y). Також приймає об'єкт Vector.
- `mouse.move_rel(dx, dy)` — перемістити відносно поточної позиції.
- `mouse.smooth_move(x, y, duration)` — плавне переміщення за вказаний час.
- `mouse.smooth_move_rel(dx, dy, duration)` — плавне відносне переміщення.
- `mouse.move_bezier(p1, p2, p3, duration)` — переміщення по кривій Безьє (p1, p2 — контрольні точки, p3 — ціль).
- `mouse.click(button)` — натиснути кнопку (`left`, `right`, `middle`).
- `mouse.double_click(button)` — подвійний клік.
- `mouse.press(button)` / `mouse.release(button)` — затиснути/відпустити кнопку.
- `mouse.scroll(dx, dy)` — прокрутка.
- `mouse.pos` — повертає вектор з поточними координатами `{x, y}`.
- `mouse.x` / `mouse.y` — поточні координати окремо.

## key / keyboard
Керування клавіатурою.
- `key.type("text")` — надрукувати текст.
- `key.press(key_code)` — затиснути клавішу.
- `key.release(key_code)` — відпустити клавішу.
- `key.tap(key_code)` — натиснути та відпустити клавішу.
- Доступні константи клавіш: 
    - Алфавіт: `K_A`...`K_Z`
    - Цифри: `K_0`...`K_9`
    - Функціональні: `K_F1`...`K_F12`
    - Спеціальні: `K_ENTER`, `K_ESC`, `K_SPACE`, `K_TAB`, `K_BACKSPACE`, `K_DELETE`, `K_INSERT`
    - Навігація: `K_UP`, `K_DOWN`, `K_LEFT`, `K_RIGHT`, `K_HOME`, `K_END`, `K_PAGE_UP`, `K_PAGE_DOWN`
    - Модифікатори: `K_CTRL`, `K_SHIFT`, `K_ALT`, `K_CAPS_LOCK`

## screen
Робота з екраном та пошук зображень.
- `screen.size()` — повертає розмір екрану (вектор `{x, y}`).
- `screen.get_color(x, y)` — повертає колір пікселя як вектор `{R, G, B}`.
- `screen.find_color(target_color, x, y, w, h, tolerance)` — знайти піксель певного кольору в області.
- `screen.wait_for_color(target_color, x, y, timeout, tolerance)` — чекати, поки піксель набуде кольору.
- `screen.find_image("path.png", confidence)` — знайти зображення на екрані. Повертає центр або `None`.
- `screen.wait_for_image("path.png", timeout, confidence)` — чекати появи зображення.
- `screen.find_all_images("path.png", confidence)` — знайти всі входження зображення.
- `screen.set_brightness(level)` — встановити яскравість монітора (0-100).
- `screen.get_brightness()` — отримати поточну яскравість.
- `screen.monitor_on()` / `screen.monitor_off()` — увімкнути/вимкнути монітор.
- `screen.mute()` / `screen.unmute()` — вимкнути/увімкнути системний звук.

## window / win
Керування вікнами Windows.
- `window.get_active()` — отримати активне вікно.
- `window.get_all()` — список усіх відкритих вікон.
- `window.get_by_title("Title")` — знайти вікно за точним заголовком.
- `window.find("Title")` — знайти всі вікна, що містять рядок у заголовку.
- Методи об'єкта вікна: `activate()`, `minimize()`, `maximize()`, `restore()`, `close()`, `move(x, y)`, `resize(w, h)`.
- Властивості вікна: `title`, `x`, `y`, `width`, `height`, `is_active`.

## time
Робота з часом.
- `time.sleep(seconds)` — затримка (аналог глобальної `sleep`).
- `time.time()` — поточний час у секундах (Unix timestamp).
- `time.time_ms()` — час у мілісекундах.
- `time.time_str()` — поточний час у форматі "YYYY-MM-DD HH:MM:SS".
- `time.perfcount()` — високоточний лічильник часу.

## math
Математичні функції та вектори.
- `math.sin(x)`, `math.cos(x)`, `math.tan(x)`, `math.sqrt(x)`, `math.abs(x)`.
- `math.floor(x)`, `math.ceil(x)`, `math.round(x, n)`.
- `math.pow(x, y)`, `math.log(x, base)`.
- `math.pi`, `math.e`.
- `math.vector(x, y, z=0)` — створення об'єкта Vector.
- Методи об'єкта Vector: `add(v)`, `sub(v)`, `mul(s)`, `length()`, `normalize()`, `lerp(v, t)`.
- `math.lerp(a, b, t)` — лінійна інтерполяція.
- `math.bezier(p0, p1, p2, t)` — квадратична крива Безьє.
- `math.bezier3(p0, p1, p2, p3, t)` — кубічна крива Безьє.
- `math.jitter(vector, amount)` — додає випадкове зміщення до вектора.

## random
Генерація випадкових значень.
- `random.random()` — випадкове число від 0 до 1.
- `random.randint(min, max)` — випадкове ціле число.
- `random.uniform(min, max)` — випадкове число з плаваючою крапкою.
- `random.choice(list)` — випадковий елемент зі списку.
- `random.shuffle(list)` — перемішати список.

## storage
Постійне сховище даних (зберігається між запусками макросу).
- `storage.write(key, value)` — записати значення.
- `storage.read(key, default)` — прочитати значення.
- `storage.has(key)` — чи існує ключ.
- `storage.delete(key)` — видалити ключ.
- `storage.clear()` — очистити все сховище макросу.
- `storage.save()` — примусово зберегти дані на диск зараз.
- `storage.set_config(interval, auto_save)` — налаштувати автозбереження (інтервал у сек та булеве значення).

## net
Робота з мережею.
- `net.get(url)` — GET запит (повертає текст відповіді).
- `net.post(url, data_dict)` — POST запит (повертає статус-код).
- `net.discord_webhook(url, message)` — відправити повідомлення у Discord.

## ui
Керування HUD-оверлеєм (інформаційне вікно поверх усіх вікон).
- `ui.show()` / `ui.hide()` — показати або сховати оверлей.
- `ui.set_text(label_id, value1, value2, ...)` — встановити текст для мітки.
- `ui.set_template(label_id, "Шаблон {0}")` — встановити шаблон форматування.
- `ui.set_color(label_id, color)` — встановити колір тексту (наприклад, `"red"` або `"#FF0000"`).
- `ui.set_font_size(label_id, size)` — встановити розмір шрифту мітки.
- `ui.move(x, y)` / `ui.set_size(w, h)` — позиція та розмір оверлея.
- `ui.anchor(pos)` — прив'язка до кута (`"top_left"`, `"top_right"`, `"bottom_left"`, `"bottom_right"`, `"top_center"`, `"bottom_center"`).
- `ui.set_bg_opacity(opacity)` — прозорість фону (0-255).
- `ui.set_scale(factor)` — масштабування всього оверлея.

## sound
Звукові ефекти.
- `sound.beep(freq, duration)` — системний сигнал.
- `sound.play("file.wav")` — відтворити звуковий файл.
- `sound.set_volume(level)` — встановити гучність системи (0-100).
- `sound.get_volume()` — отримати поточну гучність.

## system
Системні функції.
- `system.set_clipboard("text")` — записати в буфер обміну.
- `system.get_clipboard()` — прочитати з буфера обміну.
- `system.alert("message")` — показати вікно з повідомленням.
- `system.set_keyboard_layout(lang_id)` — змінити розкладку ('en', 'uk', 'ru').
- `system.get_keyboard_layout()` — отримати ID поточної розкладки.

## macro
Керування іншими макросами.
- `macro.run("name", "path.tml")` — запустити інший макрос.
- `macro.stop("name")` — зупинити макрос.
- `macro.is_running("name")` — чи запущений макрос.
- `macro.exit()` — зупинити поточний макрос.

## tick
Інформація про поточний цикл виконання.
- `tick.delta` — час у секундах, що пройшов з моменту попереднього виклику `on_tick`. Корисно для плавної анімації та розрахунків швидкості.

## Інструменти розробника та Аналіз

### Статичний аналізатор
Перед компіляцією TML проводить статичний аналіз коду, щоб виявити помилки до запуску:
- **Перевірка типів**: Аналізатор попереджає про неможливі операції (наприклад, додавання числа до рядка).
- **Невизначені змінні**: Попередження, якщо ви намагаєтесь використати змінну, яка не була оголошена через `let` або не є вбудованою.
- **Аргументи функцій**: Перевірка кількості переданих параметрів.

### Дизасемблер (Disassembler)
Для глибокого аналізу та відладки можна переглянути байт-код скомпільованого макросу.
1. Запустіть макрос, щоб він скомпілювався у `.cache`.
2. Використайте утиліту `disassembler.py`:
```bash
python disassembler.py .cache/your_macro_hash.bin
```
Це виведе список низькорівневих інструкцій (Opcodes), які виконуються віртуальною машиною.
