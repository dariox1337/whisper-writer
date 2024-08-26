import numpy as np
from typing import Dict, Any

from transcription_backend.transcription_backend_base import TranscriptionBackendBase
from config_manager import ConfigManager


class FasterWhisperBackend(TranscriptionBackendBase):
    def __init__(self):
        self.WhisperModel = None
        self.config = None
        self.model = None

    def initialize(self, options: Dict[str, Any]):
        try:
            from faster_whisper import WhisperModel
            self.WhisperModel = WhisperModel
        except ImportError:
            ConfigManager.log_print("Failed to import faster_whisper. Make sure it's installed.")
            return

        self.config = options
        self._load_model()

    def _load_model(self):
        ConfigManager.log_print('Creating Faster Whisper model...')
        compute_type = self.config.get('compute_type', 'default')
        model_path = self.config.get('model_path', '')
        device = self.config.get('device', 'auto')
        model_name = self.config.get('model', 'base')

        if model_path:
            try:
                ConfigManager.log_print(f'Loading model from: {model_path}')
                self.model = self.WhisperModel(model_path,
                                               device=device,
                                               compute_type=compute_type,
                                               download_root=None)
                ConfigManager.log_print('Model loaded successfully from specified path.')
                return
            except Exception as e:
                ConfigManager.log_print(f'Error loading model from path: {e}')
                ConfigManager.log_print('Falling back to online models...')

        # If model_path is empty or failed to load, use online models
        try:
            ConfigManager.log_print(f'Attempting to load {model_name} model...')
            self.model = self.WhisperModel(model_name,
                                           device=device,
                                           compute_type=compute_type)
            ConfigManager.log_print(f'{model_name.capitalize()} model loaded successfully.')
        except Exception as e:
            ConfigManager.log_print(f'Error loading {model_name} model: {e}')
            ConfigManager.log_print('Falling back to base model on CPU...')
            try:
                self.model = self.WhisperModel('base',
                                               device='cpu',
                                               compute_type='default')
                ConfigManager.log_print('Base model loaded successfully on CPU.')
            except Exception as e:
                ConfigManager.log_print(f'Failed to load base model on CPU: {e}')
                ConfigManager.log_print("Failed to initialize any Whisper model.")

    def transcribe_complete(self, audio_data: np.ndarray, sample_rate: int = 16000,
                            channels: int = 1, language: str = 'auto') -> Dict[str, Any]:
        if not self.model:
            ConfigManager.log_print("Model not initialized")
            return {'raw_text': '', 'language': language}

        # Check array type and convert if necessary
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32) / np.iinfo(audio_data.dtype).max

        segments, info = self.model.transcribe(
            audio=audio_data,
            language=language if language != 'auto' else None,
            initial_prompt=self.config.get('initial_prompt'),
            condition_on_previous_text=self.config.get('condition_on_previous_text', True),
            temperature=self.config.get('temperature', 0.0),
            vad_filter=self.config.get('vad_filter', False),
        )

        transcription = ''.join([segment.text for segment in list(segments)]).strip()

        return {
            'raw_text': transcription,
            'language': info.language,
        }

    def transcribe_stream(self, audio_chunk: np.ndarray, sample_rate: int = 16000,
                          channels: int = 1, language: str = 'auto') -> Dict[str, Any]:
        # For now, we'll use the same method as transcribe_complete
        # In a real implementation, you might want to use a streaming-specific method
        return self.transcribe_complete(audio_chunk, sample_rate, channels, language)

    def cleanup(self):
        self.model = None