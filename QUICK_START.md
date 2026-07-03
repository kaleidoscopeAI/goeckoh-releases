# Quick Start - Echo V4

## 🚀 Fastest Way to Run

### Option 1: Android Emulator (Recommended for Testing)

```bash
# 1. Set Flutter path
export PATH="$HOME/flutter/bin:$PATH"

# 2. Start Android emulator from Android Studio
# Or list available emulators:
flutter emulators

# 3. Run the app
cd /home/jacob/Desktop/Goeckoh_Mobile_Master
flutter run
```

### Option 2: Physical Android Device

```bash
# 1. Enable USB debugging on your phone
# 2. Connect via USB
# 3. Run:
export PATH="$HOME/flutter/bin:$PATH"
cd /home/jacob/Desktop/Goeckoh_Mobile_Master
flutter run
```

### Option 3: Build APK to Install

```bash
export PATH="$HOME/flutter/bin:$PATH"
cd /home/jacob/Desktop/Goeckoh_Mobile_Master
flutter build apk --release

# APK will be at:
# build/app/outputs/flutter-apk/app-release.apk
```

## ⚙️ Current Configuration

The app is set to **DEMO MODE** by default:
- ✅ No large downloads needed
- ✅ Fast testing
- ✅ Mock AI responses
- ⚠️  Not full production AI

To enable full AI, edit `lib/config.dart`:
```dart
static const bool isProduction = true;
static const bool enableModelDownloads = true;
```

## 🐛 If Something Goes Wrong

```bash
# Clean and rebuild
flutter clean
flutter pub get
flutter run

# Check what's wrong
flutter doctor
flutter analyze
```

## 📝 What You'll See

1. **Splash Screen**: "Initializing Neural Core..."
2. **Permission Request**: Allow microphone access
3. **Main Interface**: Animated circle showing app state
   - Grey = Idle
   - Cyan = Listening
   - Purple = Thinking  
   - Green = Speaking

## 🎤 How to Use

1. Speak into your device
2. App listens and transcribes
3. AI processes (demo mode = simple echo)
4. Response is spoken back

## ✅ Success Looks Like

- App launches without crashing
- You can grant microphone permission
- Interface shows animated circle
- Speaking triggers state changes

That's it! You're running Echo V4.
