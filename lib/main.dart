import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:permission_handler/permission_handler.dart';
import 'logic/model_manager.dart';
import 'logic/echo_service.dart';

void main() {
  runApp(const EchoApp());
}

class EchoApp extends StatelessWidget {
  const EchoApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Echo V4',
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: const Color(0xFF0A0A0A),
        colorScheme: const ColorScheme.dark(primary: Colors.cyanAccent),
      ),
      home: const BootstrapScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class BootstrapScreen extends StatefulWidget {
  const BootstrapScreen({super.key});
  @override
  State<BootstrapScreen> createState() => _BootstrapScreenState();
}

class _BootstrapScreenState extends State<BootstrapScreen> {
  String _status = "Initializing Neural Core...";
  double _progress = 0.0;
  final ModelManager _manager = ModelManager();
  bool _hasError = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _boot();
  }

  Future<void> _boot() async {
    // Request permissions (skip storage on web)
    try {
      if (kIsWeb) {
        final micStatus = await Permission.microphone.request();
        if (!micStatus.isGranted) {
          setState(() {
            _hasError = true;
            _errorMessage = "Microphone permission is required";
          });
          return;
        }
      } else {
        final statuses = await [
          Permission.microphone,
          Permission.storage,
        ].request();
        
        if (!statuses[Permission.microphone]!.isGranted) {
          setState(() {
            _hasError = true;
            _errorMessage = "Microphone permission is required";
          });
          return;
        }
      }
    } catch (e) {
      setState(() {
        _hasError = true;
        _errorMessage = "Permission error: $e";
      });
      return;
    }

    // Check/download models
    try {
      await _manager.checkModels((status, prog) {
        if (mounted) {
          setState(() {
            _status = status;
            _progress = prog;
          });
        }
      });
      
      if (mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (_) => const EchoInterface()),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _hasError = true;
          _errorMessage = e.toString();
          _status = "Setup failed";
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(40.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.psychology, size: 64, color: Colors.cyanAccent),
              const SizedBox(height: 30),
              Text(
                _status,
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: _hasError ? Colors.redAccent : Colors.white,
                  fontSize: 16,
                ),
              ),
              if (_errorMessage != null) ...[
                const SizedBox(height: 10),
                Text(
                  _errorMessage!,
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    color: Colors.redAccent,
                    fontSize: 12,
                  ),
                ),
              ],
              const SizedBox(height: 20),
              if (!_hasError) ...[
                LinearProgressIndicator(
                  value: _progress,
                  color: Colors.cyanAccent,
                  backgroundColor: Colors.grey[800],
                ),
                const SizedBox(height: 10),
                Text(
                  '${(_progress * 100).toInt()}%',
                  style: TextStyle(color: Colors.grey[400], fontSize: 12),
                ),
              ] else ...[
                ElevatedButton(
                  onPressed: () {
                    setState(() {
                      _hasError = false;
                      _errorMessage = null;
                      _status = "Retrying...";
                      _progress = 0.0;
                    });
                    _boot();
                  },
                  child: const Text('Retry'),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class EchoInterface extends StatefulWidget {
  const EchoInterface({super.key});
  @override
  State<EchoInterface> createState() => _EchoInterfaceState();
}

class _EchoInterfaceState extends State<EchoInterface> with SingleTickerProviderStateMixin {
  final EchoService _service = EchoService();
  String? _errorMessage;
  late AnimationController _pulseController;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    )..repeat(reverse: true);
    _initService();
  }

  Future<void> _initService() async {
    try {
      await _service.initialize();
      await _service.startSession();
    } catch (e) {
      setState(() {
        _errorMessage = "Failed to start: $e";
      });
    }
  }

  @override
  void dispose() {
    _service.stopSession();
    _service.dispose();
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_errorMessage != null) {
      return Scaffold(
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 64, color: Colors.redAccent),
              const SizedBox(height: 20),
              Text(_errorMessage!, style: const TextStyle(color: Colors.redAccent)),
              const SizedBox(height: 20),
              ElevatedButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Go Back'),
              ),
            ],
          ),
        ),
      );
    }

    return Scaffold(
      body: StreamBuilder<EchoState>(
        stream: _service.stateStream,
        initialData: EchoState.IDLE,
        builder: (context, snapshot) {
          final state = snapshot.data!;
          Color glow;
          String label;
          double size;
          IconData icon;

          switch (state) {
            case EchoState.LISTENING:
              glow = Colors.cyanAccent;
              label = "Listening";
              size = 200;
              icon = Icons.mic;
              break;
            case EchoState.THINKING:
              glow = Colors.purpleAccent;
              label = "Reasoning";
              size = 180;
              icon = Icons.psychology;
              break;
            case EchoState.SPEAKING:
              glow = Colors.greenAccent;
              label = "Speaking";
              size = 220;
              icon = Icons.volume_up;
              break;
            default:
              glow = Colors.grey;
              label = "Idle";
              size = 150;
              icon = Icons.pause_circle_outline;
          }

          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                AnimatedBuilder(
                  animation: _pulseController,
                  builder: (context, child) {
                    return AnimatedContainer(
                      duration: const Duration(milliseconds: 400),
                      curve: Curves.easeInOut,
                      width: size + (_pulseController.value * 20),
                      height: size + (_pulseController.value * 20),
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: Colors.black,
                        border: Border.all(color: glow.withOpacity(0.5), width: 2),
                        boxShadow: [
                          BoxShadow(
                            color: glow.withOpacity(0.3 + (_pulseController.value * 0.2)),
                            blurRadius: 40 + (_pulseController.value * 20),
                            spreadRadius: 10 + (_pulseController.value * 10),
                          ),
                        ],
                      ),
                      child: Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(icon, size: 48, color: glow),
                            const SizedBox(height: 10),
                            Text(
                              label,
                              style: TextStyle(
                                color: glow,
                                fontWeight: FontWeight.bold,
                                letterSpacing: 1.2,
                                fontSize: 18,
                              ),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
                const SizedBox(height: 40),
                if (kIsWeb)
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.orange.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.orange.withOpacity(0.3)),
                    ),
                    child: const Text(
                      '⚠️ Web Demo Mode\nFor full AI features, use Android/iOS',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: Colors.orange, fontSize: 12),
                    ),
                  ),
              ],
            ),
          );
        },
      ),
    );
  }
}
