from scene import *
import numpy as np
from itertools import product
import time
from PIL import Image, ImageFilter, ImageEnhance
import io

# ================== CONFIG ==================
MAX_MODES = 12
RESOLUTION = 720
PAUSE_TIME = 2.0
FADE_DURATION = 0.85


class ChladniScene(Scene):
    def setup(self):
        self.background_color = '#1e1e1e'
        
        self.modes = self._generate_modes()
        self.current_mode_idx = 0
        self.last_switch_time = time.time()
        self.pattern_images = None
        self.is_fading = False
        
        # Two plates for smooth crossfade
        self.plate_current = SpriteNode(color=(1, 1, 1), size=(1290, 1290))
        self.plate_next = SpriteNode(color=(1, 1, 1), size=(1290, 1290))
        
        self.plate_current.position = self.size/2
        self.plate_next.position = self.size/2
        self.plate_next.alpha = 0
        
        self.add_child(self.plate_current)
        self.add_child(self.plate_next)
        
        self.mode_label = LabelNode("Loading ultra-crisp patterns...", 
                                   font=('Helvetica', 26), 
                                   position=(self.size.w/2, self.size.h - 90),
                                   color='white')
        self.add_child(self.mode_label)
        
        self.info_label = LabelNode("Chladni Plate • SDF • Tap to change mode", 
                                   font=('Helvetica', 22),
                                   position=(self.size.w/2, 50), 
                                   color='#aaaaaa')
        self.add_child(self.info_label)
        
        self.pattern_images = self._precompute_patterns()
        self.update_pattern(immediate=True)
    
    def _generate_modes(self):
        seen = set()
        modes = []
        for m, n in product(range(1, MAX_MODES + 1), repeat=2):
            if m >= n and (m, n) not in seen:
                seen.add((m, n))
                freq = 142.0 * (m**2 + n**2) / 13.0
                modes.append((round(freq), m, n))
        return sorted(modes, key=lambda x: x[0])
    
    def _precompute_patterns(self):
        print(f"Precomputing {len(self.modes)} ultra-crisp SDF patterns...")
        patterns = {}
        size = RESOLUTION
        
        x = np.linspace(0, 1, size)
        y = np.linspace(0, 1, size)
        X, Y = np.meshgrid(x, y)
        
        for _, m, n in self.modes:
            Z = (np.sin(m * np.pi * X) * np.sin(n * np.pi * Y) + 
                 np.sin(n * np.pi * X) * np.sin(m * np.pi * Y))
            
            # Signed Distance Field style for crisp lines
            Z_norm = Z / np.max(np.abs(Z))
            line_width = 0.027
            distance = np.abs(Z_norm)
            sdf = np.clip((distance - line_width) / 0.017, -1, 1)
            
            img_array = (255 * (1 - (sdf * 0.5 + 0.5))).astype(np.uint8)
            
            pil_img = Image.fromarray(img_array, mode='L')
            pil_img = pil_img.filter(ImageFilter.SHARPEN)
            enhancer = ImageEnhance.Contrast(pil_img)
            pil_img = enhancer.enhance(4.0)
            
            buffer = io.BytesIO()
            pil_img.save(buffer, format='PNG')
            ui_img = ui.Image.from_data(buffer.getvalue())
            buffer.close()
            
            patterns[(m, n)] = ui_img
        
        print("✅ Ultra-crisp patterns ready!")
        return patterns
    
    def update_pattern(self, immediate=False):
        if self.pattern_images is None or self.is_fading:
            return
        
        freq, m, n = self.modes[self.current_mode_idx]
        self.mode_label.text = f"Frequency: {freq} Hz\nMode (m={m}, n={n})"
        
        next_texture = Texture(self.pattern_images[(m, n)])
        
        if immediate:
            self.plate_current.texture = next_texture
            self.plate_next.alpha = 0
            return
        
        # Smooth crossfade
        self.is_fading = True
        self.plate_next.texture = next_texture
        self.plate_next.alpha = 0
        
        self.plate_next.run_action(Action.fade_to(1, FADE_DURATION, TIMING_EASE_IN_OUT))
        self.plate_current.run_action(Action.fade_to(0, FADE_DURATION, TIMING_EASE_IN_OUT))
        
        def finish_fade():
            self.plate_current.texture = self.plate_next.texture
            self.plate_current.alpha = 1.0
            self.plate_next.alpha = 0.0
            self.is_fading = False
        
        self.run_action(Action.sequence(
            Action.wait(FADE_DURATION),
            Action.call(finish_fade)
        ))
    
    def update(self):
        if self.pattern_images is None or self.is_fading:
            return
        
        if time.time() - self.last_switch_time > PAUSE_TIME:
            self.current_mode_idx = (self.current_mode_idx + 1) % len(self.modes)
            self.last_switch_time = time.time()
            self.update_pattern()
    
    def touch_began(self, touch):
        if self.pattern_images is None or self.is_fading:
            return
        self.current_mode_idx = (self.current_mode_idx + 1) % len(self.modes)
        self.last_switch_time = time.time()
        self.update_pattern()


# ================== RUN ==================
if __name__ == '__main__':
    print("🚀 Chladni Plate — Ultra Crisp SDF Visuals")
    run(ChladniScene(), show_fps=False)
