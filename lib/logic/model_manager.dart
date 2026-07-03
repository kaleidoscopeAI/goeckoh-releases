import 'dart:io';
import 'package:dio/dio.dart';
import 'package:path_provider/path_provider.dart';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../config.dart';

class ModelConfig {
  // Llama 3.2 3B Instruct (Quantized Q4_K_M for balance of speed/smarts)
  static const String llamaUrl =
      "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf";
  static const String llamaFile = "llama_3.2_3b_q4.gguf";
  static const String llamaVersion = "1.0";
  
  // Expected file size (~1.9GB) for validation
  static const int llamaExpectedSize = 1900000000;
}

class ModelManager {
  final Dio _dio = Dio();

  Future<String> getModelPath(String filename) async {
    final dir = await getApplicationDocumentsDirectory();
    return "${dir.path}/$filename";
  }

  Future<bool> checkModels(
    Function(String status, double progress) onUpdate,
  ) async {
    if (!AppConfig.enableModelDownloads) {
      // Demo mode - create placeholder files
      onUpdate("Demo Mode: Skipping model downloads...", 0.5);
      await Future.delayed(const Duration(seconds: 1));
      
      final llamaPath = await getModelPath(ModelConfig.llamaFile);
      if (!await File(llamaPath).exists()) {
        await File(llamaPath).create(recursive: true);
        await File(llamaPath).writeAsString("demo_placeholder");
      }
      
      onUpdate("Demo mode ready!", 1.0);
      await Future.delayed(const Duration(milliseconds: 500));
      return true;
    }

    final prefs = await SharedPreferences.getInstance();

    // Check Llama model
    final llamaPath = await getModelPath(ModelConfig.llamaFile);
    final llamaExists = await File(llamaPath).exists();
    final storedVersion = prefs.getString('llama_version');
    
    bool needsDownload = !llamaExists || storedVersion != ModelConfig.llamaVersion;
    
    if (llamaExists && !needsDownload) {
      // Verify file integrity
      final file = File(llamaPath);
      final size = await file.length();
      if (size < ModelConfig.llamaExpectedSize * 0.9) {
        // File is corrupted or incomplete
        debugPrint('Model file corrupted (size: $size), re-downloading...');
        needsDownload = true;
        await file.delete();
      }
    }

    if (needsDownload) {
      try {
        await _download(
          ModelConfig.llamaUrl,
          llamaPath,
          "Brain (Llama 3.2 3B)",
          onUpdate,
        );
        await prefs.setString('llama_version', ModelConfig.llamaVersion);
      } catch (e) {
        onUpdate("Download failed: $e", 1.0);
        debugPrint('Model download error: $e');
        return false;
      }
    } else {
      onUpdate("Models already downloaded", 1.0);
    }

    return true;
  }

  Future<void> _download(
    String url,
    String savePath,
    String label,
    Function(String, double) onUpdate,
  ) async {
    try {
      debugPrint('Downloading $label from $url');
      
      await _dio.download(
        url,
        savePath,
        onReceiveProgress: (received, total) {
          if (total != -1) {
            final progress = received / total;
            final receivedMB = received / (1024 * 1024);
            final totalMB = total / (1024 * 1024);
            onUpdate(
              "Downloading $label\n${receivedMB.toStringAsFixed(1)}MB / ${totalMB.toStringAsFixed(1)}MB",
              progress,
            );
          } else {
            onUpdate("Downloading $label...", 0.0);
          }
        },
        options: Options(
          receiveTimeout: AppConfig.downloadTimeout,
          sendTimeout: AppConfig.downloadTimeout,
        ),
      );
      
      onUpdate("Verifying $label...", 1.0);
      
      // Verify file was downloaded completely
      final file = File(savePath);
      if (!await file.exists()) {
        throw Exception('Download failed - file not found');
      }
      
      final size = await file.length();
      debugPrint('Downloaded $label - Size: ${size / (1024 * 1024)} MB');
      
      onUpdate("$label ready!", 1.0);
      await Future.delayed(const Duration(milliseconds: 500));
      
    } catch (e) {
      debugPrint("Download failed: $e");
      final file = File(savePath);
      if (await file.exists()) await file.delete();
      rethrow;
    }
  }

  Future<void> clearModels() async {
    final prefs = await SharedPreferences.getInstance();
    final llamaPath = await getModelPath(ModelConfig.llamaFile);
    
    final file = File(llamaPath);
    if (await file.exists()) {
      await file.delete();
    }
    
    await prefs.remove('llama_version');
    debugPrint('Models cleared');
  }
}
