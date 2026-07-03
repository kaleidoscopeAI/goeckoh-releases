import 'package:flutter/material.dart';
import 'dart:math' as math;

class HeartVisualizer extends StatefulWidget {
  final double coherence;
  const HeartVisualizer({super.key, required this.coherence});

  @override
  State<HeartVisualizer> createState() => _HeartVisualizerState();
}

class _HeartVisualizerState extends State<HeartVisualizer> with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 4),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return CustomPaint(
          painter: LatticePainter(
            progress: _controller.value,
            coherence: widget.coherence,
          ),
          child: Container(),
        );
      },
    );
  }
}

class LatticePainter extends CustomPainter {
  final double progress;
  final double coherence;

  LatticePainter({required this.progress, required this.coherence});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.cyanAccent.withOpacity(0.5)
      ..strokeWidth = 1.0;

    const int rows = 16;
    const int cols = 16;
    final cellWidth = size.width / cols;
    final cellHeight = size.height / rows;

    for (int i = 0; i < rows; i++) {
      for (int j = 0; j < cols; j++) {
        final x = j * cellWidth + cellWidth / 2;
        final y = i * cellHeight + cellHeight / 2;

        // Wave effect based on coherence and progress
        final dist = math.sqrt(math.pow(x - size.width / 2, 2) + math.pow(y - size.height / 2, 2));
        final wave = math.sin(progress * 2 * math.pi - dist * 0.05) * (1.0 - coherence) * 10;
        
        final dotPaint = Paint()
          ..color = Color.lerp(Colors.cyanAccent, Colors.purpleAccent, (1.0 - coherence))!
              .withOpacity(0.6 + (math.sin(progress * 2 * math.pi + i) * 0.2));

        canvas.drawCircle(Offset(x, y + wave), 2.0, dotPaint);

        // Draw connections
        if (j < cols - 1) {
          final nextX = (j + 1) * cellWidth + cellWidth / 2;
          canvas.drawLine(Offset(x, y + wave), Offset(nextX, y + wave), paint.withOpacity(0.1 * coherence));
        }
        if (i < rows - 1) {
          final nextY = (i + 1) * cellHeight + cellHeight / 2;
          canvas.drawLine(Offset(x, y + wave), Offset(x, nextY + wave), paint.withOpacity(0.1 * coherence));
        }
      }
    }
  }

  @override
  bool shouldRepaint(LatticePainter oldDelegate) => true;
}
