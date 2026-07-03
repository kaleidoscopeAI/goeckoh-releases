import hashlib
import json
import logging
import os
import requests
import threading
from pathlib import Path
from tqdm import tqdm

logger = logging.getLogger(__name__)

# --- Model Manifest ---
# This defines the models the application needs, their download URLs, and expected checksums.
MODEL_MANIFEST = {
    "whisper_asr": {
        "filename": "sherpa-onnx-whisper-tiny.en.tar.bz2",
        "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-tiny.en.tar.bz2",
        "sha256": "44a7f45aa8ac82531dde317c46f3458c2111b269b82186834468d4a301c38a22",
        "type": "asr",
        "destination": "models/asr"
    },
    "silero_vad": {
        "filename": "silero_vad.onnx",
        "url": "https://github.com/snakers4/silero-vad/raw/master/silero_vad.onnx",
        "sha256": "b48f2c2535000969541a043c73f5636dc45330364d262590742f9e42e47635b7", # NOTE: This is a placeholder hash and should be verified.
        "type": "vad",
        "destination": "models/vad"
    },
    "vits_tts": {
        "filename": "en_US-lessac-medium.onnx.tar.gz",
        "url": "https://github.com/rhasspy/piper-voices/releases/download/v1.0.0/en_US-lessac-medium.onnx.tar.gz",
        "sha256": "f30741eb1626f264879b69e5d43e5362145b4129598270549c4709d85459345c",
        "type": "tts",
        "destination": "models/tts"
    },
    # Add other models like Llama 3B here if needed
}

class AssetManager:
    """
    Manages the download, verification, and lifecycle of large AI model assets.
    Replicates the logic from the robust model_manager.dart.
    """
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.models_root = self.base_path / "models"
        self.lock = threading.Lock()

    def verify_and_download_assets(self):
        """
        Checks all models in the manifest, downloads if missing or corrupt.
        This should be called on application startup.
        """
        logger.info("Verifying all required assets...")
        for model_name, details in MODEL_MANIFEST.items():
            destination_dir = self.base_path / details["destination"]
            destination_dir.mkdir(parents=True, exist_ok=True)
            
            # The final expected file is often inside the archive, let's assume a simple case for now
            # where we check for the archive file itself. More robust logic would check for the extracted contents.
            archive_path = destination_dir / details["filename"]
            
            if self._is_file_valid(archive_path, details["sha256"]):
                logger.info(f"'{model_name}' is already downloaded and valid.")
                # We should also check for extraction here
            else:
                logger.warning(f"'{model_name}' is missing or corrupt. Downloading...")
                self._download_file(details["url"], archive_path)
                
                # After download, verify again
                if not self._is_file_valid(archive_path, details["sha256"]):
                    raise RuntimeError(f"Failed to download or verify {model_name}. Checksum mismatch.")
                
                # If valid, extract the archive
                self._extract_archive(archive_path, destination_dir)
        
        logger.info("All assets are verified and ready.")

    def _is_file_valid(self, file_path: Path, expected_hash: str) -> bool:
        """Checks if a file exists and its SHA256 hash matches the expected one."""
        if not file_path.exists():
            return False
        
        with self.lock:
            try:
                hasher = hashlib.sha256()
                with open(file_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hasher.update(chunk)
                
                actual_hash = hasher.hexdigest()
                if actual_hash == expected_hash:
                    return True
                else:
                    logger.warning(f"Hash mismatch for {file_path.name}: Expected {expected_hash}, got {actual_hash}")
                    return False
            except Exception as e:
                logger.error(f"Error while checking file hash for {file_path.name}: {e}")
                return False

    def _download_file(self, url: str, destination: Path):
        """Downloads a file with a progress bar."""
        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                
                with open(destination, "wb") as f, tqdm(
                    desc=destination.name,
                    total=total_size,
                    unit='iB',
                    unit_scale=True,
                    unit_divisor=1024,
                ) as bar:
                    for chunk in r.iter_content(chunk_size=8192):
                        size = f.write(chunk)
                        bar.update(size)
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download {url}: {e}")
            if destination.exists():
                os.remove(destination) # Clean up partial download
            raise

    def _extract_archive(self, archive_path: Path, destination_dir: Path):
        """Extracts tar.gz or tar.bz2 archives."""
        logger.info(f"Extracting {archive_path.name}...")
        try:
            if str(archive_path).endswith('.tar.gz'):
                import tarfile
                with tarfile.open(archive_path, "r:gz") as tar:
                    tar.extractall(path=destination_dir)
            elif str(archive_path).endswith('.tar.bz2'):
                import tarfile
                with tarfile.open(archive_path, "r:bz2") as tar:
                    tar.extractall(path=destination_dir)
            else:
                logger.warning(f"Unsupported archive format for {archive_path.name}")
                return

            logger.info(f"Successfully extracted {archive_path.name} to {destination_dir}")
            # Optionally, remove archive after extraction
            # os.remove(archive_path)

        except Exception as e:
            logger.error(f"Failed to extract {archive_path.name}: {e}")
            raise
            
    def get_model_path(self, model_name: str) -> Optional[Path]:
        """Gets the path to a model's key file/directory after download and extraction."""
        if model_name not in MODEL_MANIFEST:
            logger.error(f"Model '{model_name}' not found in manifest.")
            return None
        
        details = MODEL_MANIFEST[model_name]
        # This is a simplification. The actual file path inside the archive would be needed.
        # For now, we return the destination directory.
        model_dir = self.base_path / details["destination"]
        
        # A more robust implementation would return the specific .onnx or model file.
        # e.g., for whisper, it might be model_dir / "tiny.en" / "tiny.en.onnx"
        
        # Let's assume the main file is named after the model for now
        # In a real scenario, the manifest would contain the extracted file name.
        if model_dir.exists():
            return model_dir
        
        return None

if __name__ == '__main__':
    # Example usage:
    logging.basicConfig(level=logging.INFO)
    asset_manager = AssetManager(base_path="echo_v4") # Assuming it runs from parent dir
    asset_manager.verify_and_download_assets()
    
    asr_path = asset_manager.get_model_path("whisper_asr")
    tts_path = asset_manager.get_model_path("vits_tts")
    
    print(f"ASR Model Path: {asr_path}")
    print(f"TTS Model Path: {tts_path}")
