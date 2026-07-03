# Echo V4.0 - Neuro-Acoustic Mirror

An offline AI voice assistant that mirrors your emotional state using on-device machine learning.

## Features

- 🎤 **Voice Recognition**: Real-time speech-to-text using device capabilities
- 🧠 **Local AI**: Runs Llama 3.2 3B model entirely on-device (no cloud/API)
- 🔊 **Text-to-Speech**: Natural voice responses
- 🎯 **Emotional Mirroring**: Adapts responses based on detected emotional context
- 🔒 **Privacy First**: All processing happens locally - no data leaves your device
- 📱 **Cross-Platform**: Android, iOS, and Web (limited)

## Architecture

```
┌─────────────────────────────────────┐
│         Flutter UI Layer            │
│  (Material Design, State Streams)   │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│       Echo Service (Dart)           │
│  • Speech Recognition (STT)         │
│  • Text-to-Speech (TTS)             │
│  • State Management (RxDart)        │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Echo Brain (Dart + FFI)        │
│  • Llama.cpp bindings               │
│  • Context-aware prompting          │
│  • Token streaming                  │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│    Native C++ (via FFI)             │
│  • Llama 3.2 3B Q4_K_M (~1.9GB)     │
│  • 4-bit quantization               │
│  • Optimized for mobile             │
└─────────────────────────────────────┘
```

## Requirements

### For Development
- Flutter 3.38.5 or higher
- Dart 3.10.4 or higher
- Android Studio (for Android builds)
- Xcode (for iOS builds, macOS only)

### For Android
- Android 8.0 (API 26) or higher
- 3GB+ free storage (for AI model)
- 4GB+ RAM recommended

### For iOS
- iOS 12.0 or higher
- 3GB+ free storage
- iPhone 8 or newer recommended

## Installation

### 1. Clone and Setup

```bash
git clone <repository-url>
cd Goeckoh_Mobile_Master
flutter pub get
```

### 2. Configure Model Downloads

Edit `lib/logic/model_manager.dart`:

```dart
static const bool enableDownloads = true; // Enable production mode
```

For testing without downloading the 1.9GB model:
```dart
static const bool enableDownloads = false; // Demo mode
```

### 3. Run on Android

```bash
# With device connected or emulator running
flutter run

# Or build APK
flutter build apk --release
```

### 4. Run on iOS

```bash
cd ios
pod install
cd ..
flutter run
```

### 5. Run on Web (Limited Features)

```bash
flutter run -d chrome
```

**Note**: Web version runs in demo mode as llama.cpp requires native code (FFI).

## Project Structure

```
lib/
├── main.dart                 # App entry point, UI components
├── logic/
│   ├── echo_service.dart     # Main service orchestration
│   ├── echo_brain.dart       # LLM integration layer
│   ├── model_manager.dart    # Model download & verification
│   └── audio_utils.dart      # Audio processing utilities
│
service.py                    # Android background service (Kivy)
buildozer.spec               # Android build configuration
requirements.txt             # Python dependencies for service
```

## Configuration

### Model Settings

Located in `lib/logic/model_manager.dart`:

```dart
class ModelConfig {
  static const String llamaUrl = "...";  // Model download URL
  static const String llamaFile = "..."; // Local filename
  static const int llamaExpectedSize = 1900000000; // ~1.9GB
}
```

### Brain Behavior

Located in `lib/logic/echo_brain.dart`:

```dart
static const String systemPrompt =
    "You are Echo. Mirror the user's emotion. "
    "If they are calm, be brief. If distressed, be grounding. "
    "Keep responses under 2 sentences.";
```

Modify this to change Echo's personality and response style.

### Context Parameters

```dart
final params = ContextParams(
  model: path,
  ctx: 1024,        // Context window size
  threads: 4,       // CPU threads to use
);
```

Adjust based on device capabilities:
- **ctx**: 512-2048 (higher = more context, slower)
- **threads**: 2-8 (match device CPU cores)

## Platform-Specific Notes

### Android
- Requires microphone and storage permissions
- Background service keeps listening even when minimized
- Uses foreground notification for continuous operation

### iOS
- Requires microphone permission
- Background audio capabilities configured in `ios/Runner/Info.plist`

### Web
- Limited to demo mode (no FFI support)
- Uses `speech_to_text` browser API
- No local AI - fallback to simple pattern matching

## Performance Tuning

### For Lower-End Devices

1. **Use smaller quantization**: Switch to Q3_K_S or Q2_K models
2. **Reduce context window**: Set `ctx: 512`
3. **Fewer threads**: Set `threads: 2`

### For High-End Devices

1. **Larger quantization**: Use Q5_K_M or Q8_0 for better quality
2. **Increase context**: Set `ctx: 2048`
3. **More threads**: Set `threads: 6-8`

## Troubleshooting

### "Speech recognition not available"
- Check microphone permissions
- On Android: Settings → Apps → Echo → Permissions → Microphone
- On iOS: Settings → Privacy → Microphone → Echo

### "Model download failed"
- Ensure stable internet connection
- Check available storage (need ~2GB free)
- Try clearing old models: Settings → Storage → Clear Data

### "App crashes on startup"
- Device may not have enough RAM
- Try enabling demo mode (disable downloads)
- Check logs: `flutter logs`

### Build Issues

**Android Native Build Fails**:
```bash
cd android
./gradlew clean
cd ..
flutter clean
flutter pub get
flutter build apk
```

**iOS Pod Install Fails**:
```bash
cd ios
rm Podfile.lock
rm -rf Pods
pod install --repo-update
cd ..
flutter clean
flutter build ios
```

## Development

### Running Tests

```bash
flutter test
```

### Hot Reload

While running in debug mode:
```
Press 'r' for hot reload
Press 'R' for hot restart
Press 'q' to quit
```

### Debugging

```bash
# Attach debugger
flutter attach

# View logs
flutter logs

# Profile performance
flutter run --profile
```

## Privacy & Security

- ✅ **100% Offline**: No network calls after model download
- ✅ **Local Processing**: All AI inference on-device
- ✅ **No Telemetry**: Zero analytics or tracking
- ✅ **Open Source**: Fully auditable code

## Known Limitations

1. **Model Size**: 1.9GB download required for full features
2. **First Response**: Takes 3-5 seconds to load model context
3. **Battery Usage**: Continuous AI inference is power-intensive
4. **Web Support**: Limited to demo mode (no local AI)

## Roadmap

- [ ] Support for multiple LLM backends (Mistral, Phi, etc.)
- [ ] Voice activity detection (VAD) improvements
- [ ] Conversation history and context memory
- [ ] Custom wake word support
- [ ] Multi-language support
- [ ] Model quantization on-device
- [ ] Desktop app (Linux, macOS, Windows)

## Credits

- **LLM**: [Llama 3.2 3B](https://huggingface.co/meta-llama/Llama-3.2-3B) by Meta
- **Quantization**: [bartowski's GGUF conversion](https://huggingface.co/bartowski)
- **Flutter Package**: [llama_cpp](https://pub.dev/packages/llama_cpp)
- **Speech Recognition**: [speech_to_text](https://pub.dev/packages/speech_to_text)
- **TTS**: [flutter_tts](https://pub.dev/packages/flutter_tts)

## License

[Specify your license here]

## Contributing

Contributions welcome! Please open an issue before major changes.

---

**Built with ❤️ for privacy-conscious AI enthusiasts**
