from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.lang import Builder
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.button import MDRectangleFlatButton
from kivy.properties import StringProperty, NumericProperty

Builder.load_string('''
<PhenotypingDashboardCard>:
    orientation: 'vertical'
    padding: "10dp"
    spacing: "10dp"
    size_hint_y: None
    height: "250dp"

    MDLabel:
        text: "Phenotyping Dashboard"
        halign: "center"
        font_style: "H5"

    MDBoxLayout:
        orientation: 'horizontal'
        MDLabel:
            text: "Clear Speech:"
        MDLabel:
            id: clear_speech_count
            text: root.clear_speech_count_text
            halign: "right"
    MDBoxLayout:
        orientation: 'horizontal'
        MDLabel:
            text: "Ambiguous:"
        MDLabel:
            id: ambiguous_count
            text: root.ambiguous_count_text
            halign: "right"
    MDBoxLayout:
        orientation: 'horizontal'
        MDLabel:
            text: "Nonverbal:"
        MDLabel:
            id: nonverbal_count
            text: root.nonverbal_count_text
            halign: "right"
    MDBoxLayout:
        orientation: 'horizontal'
        MDLabel:
            text: "Gestures:"
        MDLabel:
            id: gestures_count
            text: root.gestures_count_text
            halign: "right"
    MDBoxLayout:
        orientation: 'horizontal'
        MDLabel:
            text: "GCL:"
        MDProgressBar:
            id: gcl_progress
            value: root.gcl_value * 100
''')

class PhenotypingDashboardCard(MDCard):
    clear_speech_count_text = StringProperty("0")
    ambiguous_count_text = StringProperty("0")
    nonverbal_count_text = StringProperty("0")
    gestures_count_text = StringProperty("0")
    gcl_value = NumericProperty(0.0)

    def on_data_update(self, data: dict, gcl: float):
        self.clear_speech_count_text = str(data.get('clear_speech', 0))
        self.ambiguous_count_text = str(data.get('ambiguous', 0))
        self.nonverbal_count_text = str(data.get('nonverbal', 0))
        self.gestures_count_text = str(data.get('gestures', 0))
        self.gcl_value = gcl

