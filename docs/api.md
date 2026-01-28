# Швидкий довідник TML API

## Миша (`mouse`)
- `move(x, y)` / `move_rel(dx, dy)`
- `smooth_move(x, y, time)` / `move_bezier(p1, p2, p3, time)`
- `click(btn)`, `double_click(btn)`, `press(btn)`, `release(btn)` (btn: `left`, `right`, `middle`)
- `scroll(dx, dy)`
- `pos`, `x`, `y` (властивості)

## Клавіатура (`key` / `keyboard`)
- `type("text")`, `press(key)`, `release(key)`, `tap(key)`
- `is_pressed(key)` — перевірка фізичного натискання
- Константи: `K_A`..`K_Z`, `K_ENTER`, `K_ESC`, `K_SPACE`, `K_CTRL`, `K_SHIFT`, `K_ALT` тощо.

## Екран (`screen`)
- `size()` -> `{x, y}`
- `get_color(x, y)` -> `{R, G, B}`
- `find_color(color, x, y, w, h, tol)`
- `find_image("file", conf)` / `find_all_images`
- `wait_for_color` / `wait_for_image`
- `set_brightness(0-100)` / `get_brightness()`
- `monitor_on()` / `monitor_off()`
- `mute()` / `unmute()` (системний звук)

## Оверлей (`ui`)
- `show()`, `hide()`, `move(x, y)`, `set_size(w, h)`
- `set_text(id, ...)` / `set_template(id, "fmt")`
- `set_color(id, "color")`, `set_font_size(id, size)`
- `anchor("pos")`, `set_bg_opacity(0-255)`, `set_scale(factor)`

## Час та Система
- `time.sleep(sec)`, `time.time()`, `time.time_ms()`, `time.time_str()`
- `system.alert("msg")`, `system.set_clipboard("txt")`, `system.get_clipboard()`
- `system.set_keyboard_layout("en"|"uk"|"ru")`
- `sound.set_volume(0-100)`, `sound.get_volume()`, `sound.beep()`, `sound.play("file")`

## Математика (`math`)
- `sin`, `cos`, `tan`, `sqrt`, `abs`, `floor`, `ceil`, `round`, `pow`, `log`
- `vector(x, y, z)` -> методи: `add`, `sub`, `mul`, `length`, `normalize`, `lerp`
- `lerp(a, b, t)`, `bezier`, `jitter(v, amt)`

## Зберігання (`storage`)
- `read(key, def)`, `write(key, val)`, `has(key)`, `delete(key)`, `clear()`
- `save()`, `set_config(interval, auto_save)`

## Макроси (`macro`)
- `run("name", "path")`, `stop("name")`, `is_running("name")`, `exit()`
