import 'dart:math';
import 'dart:typed_data';

class AudioUtils {
  // Simple energy-based VAD.
  static double calculateRMS(Uint8List pcmData) {
    double sum = 0;
    for (int i = 0; i < pcmData.length; i += 2) {
      if (i + 1 >= pcmData.length) break;
      final byte1 = pcmData[i];
      final byte2 = pcmData[i + 1];
      int sample = (byte2 << 8) | byte1;
      if (sample > 32767) sample -= 65536;
      sum += sample * sample;
    }
    if (pcmData.isEmpty) return 0;
    return sqrt(sum / (pcmData.length / 2));
  }

  // Add standard WAV header to raw PCM data for Whisper.
  static Uint8List createWavFile(List<Uint8List> chunks, int sampleRate) {
    final totalSize = chunks.fold<int>(0, (p, e) => p + e.length);
    final buffer = Uint8List(44 + totalSize);
    final view = ByteData.view(buffer.buffer);

    _writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + totalSize, Endian.little);
    _writeString(view, 8, 'WAVE');

    _writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, Endian.little);
    view.setUint16(20, 1, Endian.little);
    view.setUint16(22, 1, Endian.little);
    view.setUint32(24, sampleRate, Endian.little);
    view.setUint32(28, sampleRate * 2, Endian.little);
    view.setUint16(32, 2, Endian.little);
    view.setUint16(34, 16, Endian.little);

    _writeString(view, 36, 'data');
    view.setUint32(40, totalSize, Endian.little);

    var offset = 44;
    for (final chunk in chunks) {
      buffer.setRange(offset, offset + chunk.length, chunk);
      offset += chunk.length;
    }
    return buffer;
  }

  static void _writeString(ByteData view, int offset, String value) {
    for (int i = 0; i < value.length; i++) {
      view.setUint8(offset + i, value.codeUnitAt(i));
    }
  }
}
