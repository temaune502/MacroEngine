class UIWrapper:
    def __init__(self, runtime_instance):
        self.runtime = runtime_instance
        self._last_values = {}

    def _get_overlay(self):
        if self.runtime and self.runtime.controller:
            return self.runtime.controller.get_overlay(self.runtime.name)
        return None

    def set_text(self, label_id, *args):
        label_id = str(label_id)
        if self._last_values.get(label_id) == args: return
        self._last_values[label_id] = args
        overlay = self._get_overlay()
        if overlay:
            val = args[0] if len(args) == 1 else list(args)
            overlay.signals.update_text.emit(label_id, val)

    def set_template(self, label_id, template_string):
        overlay = self._get_overlay()
        if overlay: overlay.signals.set_template.emit(str(label_id), str(template_string))

    def show(self):
        overlay = self._get_overlay()
        if overlay: overlay.signals.show_overlay.emit(True)

    def hide(self):
        overlay = self._get_overlay()
        if overlay: overlay.signals.show_overlay.emit(False)

    def move(self, x, y):
        overlay = self._get_overlay()
        if overlay: overlay.signals.move_overlay.emit(int(x), int(y))

    def set_size(self, w, h):
        overlay = self._get_overlay()
        if overlay: overlay.signals.resize_overlay.emit(int(w), int(h))

    def set_font_size(self, label_id, size):
        overlay = self._get_overlay()
        if overlay: overlay.signals.set_font_size.emit(str(label_id), int(size))

    def set_scale(self, factor):
        overlay = self._get_overlay()
        if overlay: overlay.signals.set_scale.emit(float(factor))

    def set_color(self, label_id, color):
        overlay = self._get_overlay()
        if overlay: overlay.signals.set_color.emit(str(label_id), str(color))

    def set_bg_opacity(self, opacity):
        overlay = self._get_overlay()
        if overlay: overlay.signals.set_bg_opacity.emit(int(opacity))

    def anchor(self, position):
        overlay = self._get_overlay()
        if overlay: overlay.signals.set_anchor.emit(str(position))

    def clear(self): pass
