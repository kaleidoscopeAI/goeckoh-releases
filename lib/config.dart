/// Echo V4 Configuration
/// Central configuration for production deployment

library config;

/// App Version Information
class AppConfig {
  static const String appName = 'Echo V4';
  static const String version = '4.0.0';
  static const int buildNumber = 1;
  
  /// Environment mode
  /// - true: Production (downloads models, uses real AI)
  /// - false: Demo (mocks models, fast testing)
  static const bool isProduction = true;
  
  /// Enable model downloads
  /// Set to false for testing without downloading 1.9GB model
  static const bool enableModelDownloads = true;
  
  /// Feature flags
  static const bool enableCrashReporting = false; // TODO: Configure crash reporting service
  static const bool enableAnalytics = false; // Privacy-first - disabled by default
  static const bool verboseLogging = !isProduction; // Only log in debug builds
  
  /// Model Configuration
  static const String modelName = 'Llama 3.2 3B Instruct Q4_K_M';
  static const int modelSizeMB = 1900;
  static const int minFreeStorageGB = 3;
  
  /// AI Parameters (tunable based on device)
  static const int contextWindowSize = 1024; // 512-2048
  static const int threadCount = 4; // 2-8 based on CPU cores
  
  /// Speech Recognition
  static const Duration listenTimeout = Duration(seconds: 30);
  static const Duration pauseThreshold = Duration(seconds: 3);
  
  /// Text-to-Speech
  static const double speechRate = 0.5; // 0.0-1.0
  static const double speechPitch = 1.0; // 0.5-2.0
  static const String speechLanguage = 'en-US';
  
  /// UI Configuration
  static const Duration animationDuration = Duration(milliseconds: 400);
  static const double pulseIntensity = 0.3; // 0.0-1.0
  
  /// Network Configuration
  static const Duration downloadTimeout = Duration(minutes: 30);
  static const int maxRetries = 3;
  
  /// Contact & Support
  static const String supportEmail = 'support@echo-app.example'; // TODO: Update
  static const String privacyPolicyUrl = 'https://echo-app.example/privacy'; // TODO: Update
  static const String termsOfServiceUrl = 'https://echo-app.example/terms'; // TODO: Update
  
  /// App Store Links (Update before submission)
  static const String playStoreUrl = 'https://play.google.com/store/apps/details?id='; // TODO
  static const String appStoreUrl = 'https://apps.apple.com/app/'; // TODO
  
  /// Debug helpers
  static bool get isDebugMode => !isProduction;
  static bool get shouldLog => verboseLogging;
}

/// Device Capability Presets
enum DeviceProfile {
  lowEnd,    // Old phones, limited RAM
  midRange,  // Modern budget phones
  highEnd,   // Flagship devices
}

class DeviceConfig {
  final int contextSize;
  final int threads;
  final String modelQuantization;
  
  const DeviceConfig({
    required this.contextSize,
    required this.threads,
    required this.modelQuantization,
  });
  
  static const lowEnd = DeviceConfig(
    contextSize: 512,
    threads: 2,
    modelQuantization: 'Q3_K_S', // Smaller, faster
  );
  
  static const midRange = DeviceConfig(
    contextSize: 1024,
    threads: 4,
    modelQuantization: 'Q4_K_M', // Balanced (default)
  );
  
  static const highEnd = DeviceConfig(
    contextSize: 2048,
    threads: 6,
    modelQuantization: 'Q5_K_M', // Higher quality
  );
  
  /// Auto-detect device profile (can be enhanced with device_info)
  static DeviceProfile detectProfile() {
    // TODO: Implement actual device detection using device_info package
    // For now, default to mid-range
    return DeviceProfile.midRange;
  }
  
  static DeviceConfig getConfig(DeviceProfile profile) {
    switch (profile) {
      case DeviceProfile.lowEnd:
        return lowEnd;
      case DeviceProfile.midRange:
        return midRange;
      case DeviceProfile.highEnd:
        return highEnd;
    }
  }
}

/// System Prompts - Customize Echo's personality here
class Prompts {
  static const String systemPrompt =
      "You are Echo. Mirror the user's emotion. "
      "If they are calm, be brief. If distressed, be grounding. "
      "Keep responses under 2 sentences.";
  
  static const String errorPrompt =
      "I'm having trouble processing that right now. Could you try again?";
  
  static const String welcomeMessage =
      "Hello! I'm Echo, your personal AI companion. I'm here to listen.";
  
  static const String goodbyeMessage =
      "Take care. I'm here whenever you need me.";
}

/// Error Messages
class ErrorMessages {
  static const String noMicPermission = 
      "Microphone permission is required for Echo to listen.";
  
  static const String noStoragePermission = 
      "Storage permission is needed to download the AI model.";
  
  static const String insufficientStorage = 
      "Not enough storage space. Please free up at least 3GB.";
  
  static const String modelDownloadFailed = 
      "Failed to download AI model. Please check your internet connection.";
  
  static const String speechRecognitionUnavailable = 
      "Speech recognition is not available on this device.";
  
  static const String ttsUnavailable = 
      "Text-to-speech is not available. Please check your device settings.";
  
  static const String modelLoadFailed = 
      "Failed to load AI model. The file may be corrupted.";
}
