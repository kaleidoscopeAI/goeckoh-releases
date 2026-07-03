import 'dart:io';
import 'package:flutter/foundation.dart';
import 'model_manager.dart';
import '../config.dart';

// Stub classes since llama_cpp has compatibility issues
class LlamaProcessor {
  void unload() {}
}

class ContextParams {
  final String model;
  final int ctx;
  final int threads;
  const ContextParams({
    required this.model,
    required this.ctx,
    required this.threads,
  });
}

class EchoBrain {
  LlamaProcessor? _llama;
  bool _isLoaded = false;
  bool _useProductionMode = false;

  static String get systemPrompt => Prompts.systemPrompt;

  Future<void> initialize() async {
    // Check if we should use production mode (requires downloaded model)
    final modelPath = await ModelManager().getModelPath(ModelConfig.llamaFile);
    final hasModel = await File(modelPath).exists();

    if (hasModel && !kIsWeb) {
      debugPrint('EchoBrain: Initializing Production Mode (Native LLM)');
      try {
        // Initialize Llama.cpp FFI
        _useProductionMode = true;
        _isLoaded = true;
      } catch (e) {
        debugPrint('Production Load Failed, falling back to Demo: $e');
        _useProductionMode = false;
      }
    } else {
      debugPrint('EchoBrain: Demo mode enabled (Web or No Model)');
      _isLoaded = true;
      _useProductionMode = false;
    }
  }

  Stream<String> process(String input) async* {
    if (!_isLoaded) {
      yield " [System Initializing...]";
      return;
    }

    if (_useProductionMode) {
      // Real LLM Inference would go here via FFI
      yield " [Analyzing...] ";
      await Future.delayed(const Duration(milliseconds: 500));
      yield "Reflecting: \"$input\"";
    } else {
      // Demo mode: Simple echo with acknowledgment
      yield "I hear you saying: ";
      await Future.delayed(const Duration(milliseconds: 100));
      
      // Simple emotional mirroring logic
      final lowerInput = input.toLowerCase();
      if (lowerInput.contains('help') || lowerInput.contains('stressed') || 
          lowerInput.contains('anxious') || lowerInput.contains('worried')) {
        yield "\"$input\". Take a deep breath. You're not alone.";
      } else if (lowerInput.contains('happy') || lowerInput.contains('great') || 
                 lowerInput.contains('good')) {
        yield "\"$input\". That's wonderful to hear!";
      } else {
        yield "\"$input\". I'm here with you.";
      }
    }
  }

  void dispose() {
    _llama?.unload();
  }
}
