# ================= GRAPHICS CONFIG =================
from kivy.config import Config
Config.set('graphics', 'multisamples', '0')
Config.set('graphics', 'minimum_width', '360')
Config.set('graphics', 'minimum_height', '640')

import os
import time
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.uix.image import Image
from plyer import battery, notification


# ================= BATTERY SCREEN =================
class BatteryScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        Window.clearcolor = (0.05, 0.08, 0.15, 1)

        layout = BoxLayout(
            orientation="vertical",
            padding=40,
            spacing=20
        )

        # ===== LOGO =====
        if os.path.exists("logo.png"):
            logo = Image(
                source="logo.png",
                size_hint=(1, 0.35),
                allow_stretch=True,
                keep_ratio=True
            )
            layout.add_widget(logo)

        # ===== LABELS =====
        self.status_label = Label(
            text="Checking Battery Status...",
            font_size=22
        )

        self.time_label = Label(
            text="Estimating charge time...",
            font_size=18,
            color=(0.3, 0.8, 1, 1)
        )

        layout.add_widget(self.status_label)
        layout.add_widget(self.time_label)

        self.add_widget(layout)

        # ===== ALARM =====
        self.alarm = None
        if os.path.exists("alarm.mp3"):
            self.alarm = SoundLoader.load("alarm.mp3")
            if self.alarm:
                self.alarm.volume = 1.0

        self.prev_percent = None
        self.charge_start_time = None

        self.startup_notified = False
        self.full_notified = False
        self.last_hourly_notification = 0

        self.alarm_event = None


    def on_enter(self):
        self.update_battery(0)
        Clock.schedule_interval(self.update_battery, 5)

    # ===== TOUCH TO STOP ALARM =====
    def on_touch_down(self, touch):
        if self.alarm:
            self.alarm.stop()
        return super().on_touch_down(touch)

    # ===== NOTIFICATION FUNCTION =====
    def send_notification(self, title, message):
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="Charging Save Pro",
                timeout=5
            )
        except Exception as e:
            print("Notification Error:", e)

    # ===== STOP ALARM AFTER 1 MIN =====
    def stop_alarm(self, dt):
        if self.alarm:
            self.alarm.stop()

    # ===== MAIN BATTERY UPDATE =====
    def update_battery(self, dt):
        try:
            status = battery.status
            percent = status.get('percentage', 0)
            is_charging = status.get('isCharging', False)

            charging_text = "Charging" if is_charging else "Discharging"
            self.status_label.text = f"Battery: {percent}% [{charging_text}]"

            current_time = time.time()

            # ===== APP START NOTIFICATION =====
            if not self.startup_notified:
                self.send_notification(
                    "Charging Save Pro",
                    f"Battery: {percent}% ({charging_text})"
                )
                self.startup_notified = True
                self.last_hourly_notification = current_time

            # ===== HOURLY (1.5 HOUR) NOTIFICATION =====
            if current_time - self.last_hourly_notification >= 5400:
                self.send_notification(
                    "Battery Update",
                    f"Battery is {percent}% ({charging_text})"
                )
                self.last_hourly_notification = current_time

            # ===== FULL CHARGE =====
            if is_charging and percent >= 100:

                self.status_label.text = "⚡ FULLY CHARGED! UNPLUG NOW."

                if not self.full_notified:

                    # 1️⃣ Notification
                    self.send_notification(
                        "Battery Full",
                        "Please unplug your charger."
                    )

                    # 2️⃣ 1 second baad alarm
                    if self.alarm:
                        Clock.schedule_once(lambda dt: self.alarm.play(), 1)

                        # Alarm 1 minute baad band
                        Clock.schedule_once(self.stop_alarm, 60)

                    self.full_notified = True
            else:
                self.full_notified = False

            # ===== TIME ESTIMATION =====
            if is_charging and percent < 100:
                if self.prev_percent is not None and percent > self.prev_percent:
                    elapsed = time.time() - self.charge_start_time
                    rate = elapsed / (percent - self.prev_percent)
                    remaining = (rate * (100 - percent)) / 60
                    self.time_label.text = f"Estimated Full in: {int(remaining)} mins"

                if self.prev_percent != percent:
                    self.prev_percent = percent
                    self.charge_start_time = time.time()
            else:
                self.time_label.text = "Estimating charge time..."
                self.prev_percent = None

        except:
            self.status_label.text = "Battery Data Unavailable"


# ================= MAIN APP =================
class ChargingSavePro(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(BatteryScreen(name="battery"))
        sm.current = "battery"
        return sm


if __name__ == "__main__":
    ChargingSavePro().run()
