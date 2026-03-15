#!/usr/bin/env python3
"""
Text-to-Speech Settings Widget
Handles TTS settings like voice, rate, volume, etc.
"""

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QSlider, QLabel, 
    QComboBox, QLineEdit, QPushButton
)
from PyQt6.QtCore import Qt

from Settings.base_settings_widget import BaseSettingsWidget

class TTSSettingsWidget(BaseSettingsWidget):
    """Text-to-Speech settings tab widget"""
    
    def setup_ui(self):
        """Create the TTS settings UI"""
        layout = QVBoxLayout(self)
        
        # TTS Rate Group
        rate_group, rate_layout = self.create_group_box("Speech Rate", QHBoxLayout)
        
        self.tts_rate = QSlider(Qt.Orientation.Horizontal)
        self.tts_rate.setRange(50, 300)
        self.tts_rate.setValue(150)
        self.tts_rate_label = QLabel("150")
        self.tts_rate.valueChanged.connect(self.on_rate_changed)
        
        rate_layout.addWidget(QLabel("Slow"))
        rate_layout.addWidget(self.tts_rate)
        rate_layout.addWidget(QLabel("Fast"))
        rate_layout.addWidget(self.tts_rate_label)
        
        # TTS Volume Group  
        volume_group, volume_layout = self.create_group_box("Speech Volume", QHBoxLayout)
        
        self.tts_volume = QSlider(Qt.Orientation.Horizontal)
        self.tts_volume.setRange(0, 100)
        self.tts_volume.setValue(100)
        self.tts_volume_label = QLabel("100%")
        self.tts_volume.valueChanged.connect(self.on_volume_changed)
        
        volume_layout.addWidget(QLabel("Quiet"))
        volume_layout.addWidget(self.tts_volume)
        volume_layout.addWidget(QLabel("Loud"))
        volume_layout.addWidget(self.tts_volume_label)
        
        # TTS Voice Selection Group
        voice_group, voice_layout = self.create_group_box("Voice Selection", QFormLayout)
        
        self.tts_voice_combo = QComboBox()
        self.tts_voice_combo.currentTextChanged.connect(self.on_settings_changed)
        self.populate_voices()
        
        voice_layout.addRow("Select Voice:", self.tts_voice_combo)
        
        # Test TTS section
        test_group, test_layout = self.create_group_box("Voice Testing", QVBoxLayout)
        
        test_input_layout = QHBoxLayout()
        self.test_text_edit = QLineEdit("This is a test of text-to-speech.")
        self.test_text_edit.setPlaceholderText("Enter text to test...")
        
        self.test_button = self.create_styled_button("Test Voice", "Test the selected voice settings")
        self.test_button.clicked.connect(self.test_tts_voice)
        
        test_input_layout.addWidget(self.test_text_edit)
        test_input_layout.addWidget(self.test_button)
        test_layout.addLayout(test_input_layout)
        
        # Add groups to main layout
        layout.addWidget(rate_group)
        layout.addWidget(volume_group)
        layout.addWidget(voice_group)
        layout.addWidget(test_group)
        layout.addStretch()
        
    def populate_voices(self):
        """Populate the voice combo box with available system voices"""
        self.tts_voice_combo.addItem("System Default")
        
        try:
            import pyttsx3
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            
            for voice in voices:
                # Clean up voice names for better display
                voice_name = voice.name.split(' - ')[0]  # Remove language part
                if 'Microsoft' in voice_name:
                    # Extract just the voice name
                    clean_name = voice_name.replace('Microsoft ', '').replace(' Desktop', '')
                    self.tts_voice_combo.addItem(clean_name, voice.id)
                else:
                    self.tts_voice_combo.addItem(voice.name, voice.id)
            engine.stop()
            
        except Exception as e:
            self.logger.error("TTSSettings", f"Error loading TTS voices: {str(e)}")
            # Add some common fallback voices
            self.tts_voice_combo.addItem("David")
            self.tts_voice_combo.addItem("Zira")
            self.tts_voice_combo.addItem("Mark")
            
    def load_settings(self):
        """Load TTS settings from the controller"""
        # Speech rate
        rate = int(self.get_setting("tts", "rate", 150))
        self.tts_rate.setValue(rate)
        self.tts_rate_label.setText(str(rate))
        
        # Speech volume
        volume = float(self.get_setting("tts", "volume", 1.0))
        volume_percent = int(volume * 100)
        self.tts_volume.setValue(volume_percent)
        self.tts_volume_label.setText(f"{volume_percent}%")
        
        # Voice selection
        saved_voice = self.get_setting("tts", "voice", "System Default")
        
        # Try to find the voice by data (voice ID) first, then by text
        voice_index = -1
        for i in range(self.tts_voice_combo.count()):
            if self.tts_voice_combo.itemData(i) == saved_voice:
                voice_index = i
                break
                
        if voice_index < 0:
            voice_index = self.tts_voice_combo.findText(saved_voice)
            
        if voice_index >= 0:
            self.tts_voice_combo.setCurrentIndex(voice_index)
            
    def save_settings(self):
        """Save TTS settings to the controller"""
        # Speech rate
        self.set_setting("tts", "rate", self.tts_rate.value())
        
        # Speech volume (convert percentage to 0.0-1.0)
        volume = self.tts_volume.value() / 100.0
        self.set_setting("tts", "volume", volume)
        
        # Voice selection - save the voice ID if available, otherwise the display text
        current_index = self.tts_voice_combo.currentIndex()
        voice_data = self.tts_voice_combo.itemData(current_index)
        if voice_data:
            self.set_setting("tts", "voice", voice_data)
        else:
            self.set_setting("tts", "voice", self.tts_voice_combo.currentText())
            
    def on_rate_changed(self, value):
        """Handle rate slider change"""
        self.tts_rate_label.setText(str(value))
        self.on_settings_changed()
        
    def on_volume_changed(self, value):
        """Handle volume slider change"""
        self.tts_volume_label.setText(f"{value}%")
        self.on_settings_changed()
        
    def test_tts_voice(self):
        """Test the current TTS settings"""
        test_text = self.test_text_edit.text().strip()
        if not test_text:
            test_text = "This is a test of text-to-speech."
            
        try:
            import pyttsx3
            engine = pyttsx3.init()
            
            # Set rate
            engine.setProperty('rate', self.tts_rate.value())
            
            # Set volume
            volume = self.tts_volume.value() / 100.0
            engine.setProperty('volume', volume)
            
            # Set voice if not default
            current_index = self.tts_voice_combo.currentIndex()
            if current_index > 0:  # Not "System Default"
                voice_id = self.tts_voice_combo.itemData(current_index)
                if voice_id:
                    engine.setProperty('voice', voice_id)
            
            # Speak the text
            engine.say(test_text)
            engine.runAndWait()
            engine.stop()
            
        except Exception as e:
            self.logger.error("TTSSettings", f"Error testing TTS voice: {str(e)}")
            self.show_warning_message("TTS Test Error", f"Failed to test voice: {str(e)}")
            
    def on_settings_changed(self):
        """Handle settings change"""
        self.settings_changed.emit()
