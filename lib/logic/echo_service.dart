import 'dart:async';
import 'dart:typed_data';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter_tts/flutter_tts.dart';
import 'package:record/record.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'audio_utils.dart';
import 'echo_brain.dart';
import '../config.dart';

enum EchoState { LISTENING, THINKING, SPEAKING, IDLE }

class EchoService {
  final AudioRecorder _recorder = AudioRecorder();
  final stt.SpeechToText _speech = stt.SpeechToText();
  final FlutterTts _tts = FlutterTts();
  final EchoBrain _brain = EchoBrain();

  final _stateController = StreamController<EchoState>.broadcast();
  Stream<EchoState> get stateStream => _stateController.stream;

  static const int sampleRate = 16000;
  static const double vadThreshold = 80.0;
  static const int silenceFramesTrigger = 15;

  bool _isSessionActive = false;
  bool _speechAvailable = false;
  String _recognizedText = "";

  Future<void> initialize() async {
    await _brain.initialize();
    await _tts.setLanguage(AppConfig.speechLanguage);
    await _tts.setSpeechRate(AppConfig.speechRate);
    await _tts.setPitch(AppConfig.speechPitch);
    
    // Initialize speech recognition
    _speechAvailable = await _speech.initialize(
      onError: (error) => debugPrint('Speech error: $error'),
      onStatus: (status) => debugPrint('Speech status: $status'),
    );
  }

  Future<void> startSession() async {
    if (!_speechAvailable) {
      debugPrint('Speech recognition not available');
      return;
    }
    
    _isSessionActive = true;
    await _startListeningLoop();
  }

  void stopSession() {
    _isSessionActive = false;
    _speech.stop();
    _recorder.stop();
    _stateController.add(EchoState.IDLE);
  }

  Future<void> _startListeningLoop() async {
    _stateController.add(EchoState.LISTENING);
    _recognizedText = "";
    
    // Start speech recognition with updated API
    await _speech.listen(
      onResult: (result) {
        if (result.finalResult && result.recognizedWords.isNotEmpty) {
          _recognizedText = result.recognizedWords;
          _executeTurn();
        }
      },
      listenFor: AppConfig.listenTimeout,
      pauseFor: AppConfig.pauseThreshold,
      listenOptions: stt.SpeechListenOptions(
        partialResults: false,
        cancelOnError: false,
        listenMode: stt.ListenMode.confirmation,
      ),
    );
  }

  Future<void> _executeTurn() async {
    if (_recognizedText.trim().isEmpty) {
      if (_isSessionActive) {
        await _startListeningLoop();
      }
      return;
    }

    _stateController.add(EchoState.THINKING);
    await _speech.stop();
    
    try {
      final text = _recognizedText;
      if (text.trim().length > 2) {
        var responseBuffer = "";
        await for (final token in _brain.process(text)) {
          responseBuffer += token;
        }
        
        _stateController.add(EchoState.SPEAKING);
        await _tts.speak(responseBuffer);
        await _tts.awaitSpeakCompletion(true);
      }
    } catch (e) {
      debugPrint("Turn Error: $e");
    }
    
    _recognizedText = "";
    if (_isSessionActive) {
      await Future.delayed(const Duration(milliseconds: 500));
      await _startListeningLoop();
    }
  }

  void dispose() {
    _stateController.close();
    _speech.stop();
    _recorder.stop();
  }
}

// Add debugPrint helper for web compatibility
void debugPrint(String message) {
  if (kIsWeb || !AppConfig.shouldLog) return;
  // ignore: avoid_print
  print('[Echo] $message');
}
