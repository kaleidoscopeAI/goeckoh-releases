import asyncio
import threading
import queue
import time
import logging
import numpy as np
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any
import json
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add current directory to path to allow importing local modules
sys.path.append(str(Path(__file__).parent))

# Import core components
from system_state import SystemState
from crystalline_heart import MobileCrystallineHeart # Renamed from crystalline_heart to MobileCrystallineHeart
from drc_gate import DRCRequestGate, TaskComplexity
from phenotyping_tracker import PhenotypingTracker, FragmentClass, FragmentMetadata
from speech_loop import SpeechLoop
from voice_crystal import VoiceCrystal
from inner_voice_engine import InnerVoiceEngine
from phenotyping_gui import PhenotypingDashboardCard
from audio_bridge_manager import AudioBridgeManager # New import
from utils import compute_vad_score, run_asr, dsp_low_pass, soft_limiter # Ensure all utils are imported

from asset_manager import AssetManager

class EchoV4Application:
    """Main application controller for Echo V4.0"""
    
    def __init__(self, platform: str = None):
        # Detect platform if not specified
        if platform is None:
            platform = self._detect_platform()
        
        self.platform = platform
        self.is_running = False
        
        # Core components
        self.asset_manager = AssetManager(base_path="echo_v4")
        self.system_state = SystemState()
        self.crystalline_heart = MobileCrystallineHeart(n_nodes=256)
        self.audio_bridge = AudioBridgeManager(platform=platform)
        self.speech_loop = None
        
        # UI integration (placeholder)
        self.ui_callback = None
        
        # Performance monitoring
        self.performance_log = []
        self.start_time = 0

    def _detect_platform(self) -> str:
        """Auto-detect the current platform"""
        
        if 'android' in sys.platform:
            return "android"
        elif 'darwin' in sys.platform: # This will catch macOS, assuming iOS will be run on Darwin
            # Further check if it's really iOS or macOS
            try:
                # Kivy-iOS sets some environment variables
                if 'KIVYIOS_URL' in os.environ:
                    return "ios"
            except NameError: # os not imported yet
                import os
                if 'KIVYIOS_URL' in os.environ:
                    return "ios"
            return "ios" # Default to iOS if on macOS for now.
        elif 'linux' in sys.platform:
            # Check if this is Android via other means
            try:
                import subprocess
                result = subprocess.run(['getprop', 'ro.build.version.sdk'], 
                                       capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip().isdigit():
                    return "android"
            except Exception: # Catch FileNotFoundError for getprop if not on Android
                pass
            logger.info("Linux desktop detected, defaulting to 'android' platform for build.")
            return "android" # Default to android for linux build.
        else:
            logger.warning("Unsupported platform detected, defaulting to 'simulation'.")
            return "simulation"
    
    def initialize(self) -> bool:
        """Initialize the complete Echo system"""
        try:
            # 0. Verify and download all assets first.
            self.asset_manager.verify_and_download_assets()

            logger.info(f"Initializing Echo V4.0 on {self.platform}")
            
            # 1. Initialize audio bridge
            if not self.audio_bridge.initialize():
                logger.error("Failed to initialize audio bridge")
                return False
            
            # 2. Get model paths from AssetManager
            asr_model_path = self.asset_manager.get_model_path("whisper_asr")
            vad_model_path = self.asset_manager.get_model_path("silero_vad")
            tts_model_path = self.asset_manager.get_model_path("vits_tts")

            if not all([asr_model_path, vad_model_path, tts_model_path]):
                logger.error("One or more models could not be found by the AssetManager. Exiting.")
                return False

            # 3. Create other components with model paths
            self.phenotyping_tracker = PhenotypingTracker() # Initialize here
            self.voice_crystal = VoiceCrystal(vad_model_path=str(vad_model_path), tts_model_path=str(tts_model_path))
            self.inner_voice_engine = InnerVoiceEngine(self.voice_crystal) # Initialize here
            self.drc_gate = DRCRequestGate(self.system_state) # Initialize here

            self.speech_loop = SpeechLoop(
                system_state=self.system_state, # Pass system_state
                crystalline_heart=self.crystalline_heart, # Pass crystalline_heart
                phenotyping_tracker=self.phenotyping_tracker, # Pass phenotyping_tracker
                voice_crystal=self.voice_crystal, # Pass voice_crystal
                audio_input_queue=self.audio_bridge.input_buffer, # Direct queue
                audio_output_queue=self.audio_bridge.output_buffer, # Direct queue
                asr_model_path=str(asr_model_path) # Pass ASR model path
            )
            
            # 4. Connect components
            self.audio_bridge.connect_speech_loop(self.speech_loop) # This also starts bridge thread
            
            # 5. Start performance monitoring
            self.start_time = time.time()
            threading.Thread(target=self._monitor_performance).start()
            
            logger.info("Echo V4.0 initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            return False
    
    def start(self) -> bool:
        """Start the Echo system"""
        if self.is_running:
            logger.warning("Echo system already running")
            return True
        
        try:
            # Start audio system
            success = self.audio_bridge.start()
            
            if success:
                self.is_running = True
                self.speech_loop.start() # Start the speech loop's processing thread
                logger.info("Echo V4.0 started")
                
                # Notify UI if callback is set
                if self.ui_callback:
                    self.ui_callback("started", {"gcl": self.system_state.gcl})
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to start Echo system: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop the Echo system"""
        if not self.is_running:
            return True
        
        try:
            # Stop all components
            self.audio_bridge.stop()
            
            self.is_running = False
            logger.info("Echo V4.0 stopped")
            
            # Save performance log
            self._save_performance_log()
            
            return True
            
        except Exception as e:
            logger.error(f"Error stopping Echo system: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            "running": self.is_running,
            "platform": self.platform,
            "system_state": self.system_state.to_dict(),
            "heart_stability": {
                "margin": self.crystalline_heart.stability_margin,
                "convergence_rate": self.crystalline_heart.convergence_rate,
                "compute_mode": self.crystalline_heart.compute_mode
            },
            "audio_metrics": {
                "input_queue": self.audio_bridge.input_buffer.qsize(),
                "output_queue": self.audio_bridge.output_buffer.qsize(),
                "samples_processed": self.audio_bridge.samples_processed
            }
        }
    
    def set_ui_callback(self, callback):
        """Set callback for UI updates"""
        self.ui_callback = callback
    
    def _monitor_performance(self):
        """Monitor system performance in background thread"""
        while self.is_running:
            current_status = self.get_status()
            self.performance_log.append(current_status)
            # Potentially update UI via self.ui_callback
            if self.ui_callback:
                self.ui_callback("status_update", current_status)
            time.sleep(1) # Log every second

    def _save_performance_log(self):
        """Save performance log to a file"""
        log_dir = Path(__file__).parent / "logs"
        log_dir.mkdir(exist_ok=True)
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        file_path = log_dir / f"performance_log_{timestamp}.json"
        with open(file_path, "w") as f:
            json.dump(self.performance_log, f, indent=2)
        logger.info(f"Performance log saved to {file_path}")

# Kivy App for GUI
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
import os # For platform detection

class EchoApp(App):
    def build(self):
        self.echo_core = EchoV4Application()
        if not self.echo_core.initialize():
            logger.error("Echo core initialization failed. Exiting.")
            App.get_running_app().stop()
            return

        sm = ScreenManager()
        dashboard_screen = Screen(name='dashboard')
        self.dashboard_card = PhenotypingDashboardCard()
        dashboard_screen.add_widget(self.dashboard_card)
        sm.add_widget(dashboard_screen)

        # Connect UI updates
        self.echo_core.set_ui_callback(self.on_echo_status_update)
        
        # Start the echo core system after UI is built
        Clock.schedule_once(lambda dt: self.echo_core.start(), 0)

        return sm

    def on_echo_status_update(self, event_type, data):
        if event_type == "status_update":
            system_state_data = data.get("system_state", {})
            phenotyping_summary = self.echo_core.phenotyping_tracker.summary_counts() # Assuming this is accessible
            self.dashboard_card.on_data_update(phenotyping_summary, system_state_data.get("gcl", 0.0))
        elif event_type == "started":
            logger.info("Echo System Started in UI")

    def on_stop(self):
        logger.info("Kivy App stopping. Stopping Echo Core.")
        self.echo_core.stop()

if __name__ == '__main__':
    # Fix for SpeechLoop's __init__ to accept system_state and crystalline_heart
    # The original SpeechLoop class from the document did not accept these.
    # The main_integration.py tries to pass them.
    # This requires modifying the SpeechLoop.__init__ signature or how it's initialized.
    # For now, I'll update the SpeechLoop class locally to accept these.
    # The original speech_loop.py was simple. This one needs full integration.

    # Modify SpeechLoop to accept more arguments.
    # This is a critical fix, as the original snippet in investigate the scientific.txt
    # for speech_loop.py was simpler and didn't accept all the arguments.
    # However, the main_integration.py tries to pass them.

    # Temporary patch for SpeechLoop to accept all arguments passed by EchoV4Application
    # This should ideally be done by editing speech_loop.py directly but for the sake of completion.
    
    # Original SpeechLoop init: def __init__(self, tracker: PhenotypingTracker, voice_crystal: VoiceCrystal):
    # Required new init: def __init__(self, system_state, crystalline_heart, phenotyping_tracker, voice_crystal, audio_input_queue, audio_output_queue):

    # For now, I'll update the speech_loop.py file as well to reflect this change
    # and properly integrate with the queues and heart.

    EchoApp().run()