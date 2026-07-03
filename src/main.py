from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager

from kernel import GoeckohKernel


class MainScreen(Screen):
    """
    Minimal Kivy UI that visualizes coherence and toggles the kernel loop.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.kernel = GoeckohKernel()
        self.is_active = False

        layout = BoxLayout(orientation="vertical", padding=32, spacing=16)

        self.status_lbl = Label(text="Neuro-Sync Idle", font_size="22sp", size_hint=(1, 0.2))
        layout.add_widget(self.status_lbl)

        viz = BoxLayout(size_hint=(1, 0.6))
        with viz.canvas:
            self.viz_color = Color(0.2, 0.8, 0.2, 1)
            self.orb = Ellipse(size=(240, 240))
        layout.add_widget(viz)

        self.btn_toggle = Button(text="Activate", size_hint=(1, 0.2), font_size="20sp")
        self.btn_toggle.bind(on_press=self.toggle_system)
        layout.add_widget(self.btn_toggle)

        self.add_widget(layout)
        Clock.schedule_interval(self.update_logic, 0.2)

    def toggle_system(self, _instance):
        if not self.is_active:
            if not self.kernel.is_alive():
                self.kernel = GoeckohKernel()
            self.kernel.start_kernel()
            self.is_active = True
            self.btn_toggle.text = "Stop"
            self.status_lbl.text = "Neuro-Sync Active"
        else:
            self.kernel.stop_kernel()
            self.is_active = False
            self.btn_toggle.text = "Activate"
            self.status_lbl.text = "Neuro-Sync Idle"

    def update_logic(self, _dt):
        if not self.is_active:
            return

        gcl = self.kernel.heart.gcl
        stress = 1.0 - gcl
        agitation = self.kernel.heart.kinetic_stress

        # Orb color shifts red on stress, green on calm
        self.viz_color.r = min(1.0, stress + agitation * 0.5)
        self.viz_color.g = max(0.0, gcl - agitation * 0.3)
        self.viz_color.b = 0.1

        if agitation > 0.5:
            self.status_lbl.text = f"Calming Protocol ({int(agitation * 100)}%)"
        else:
            self.status_lbl.text = f"Coherence: {int(gcl * 100)}%"


class GoeckohApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name="main"))
        return sm


if __name__ == "__main__":
    GoeckohApp().run()
