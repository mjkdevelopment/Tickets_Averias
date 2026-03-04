import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'main.dart'; // To access kPanelBaseUrl and WebViewScreen

class WaitingRoomScreen extends StatefulWidget {
  final String fcmToken;
  
  const WaitingRoomScreen({super.key, required this.fcmToken});

  @override
  State<WaitingRoomScreen> createState() => _WaitingRoomScreenState();
}

class _WaitingRoomScreenState extends State<WaitingRoomScreen> {
  Timer? _timer;
  bool _isLoading = false;
  String _message = 'Esperando aprobación del administrador...';

  @override
  void initState() {
    super.initState();
    // Iniciar polling
    _checkStatus();
    _timer = Timer.periodic(const Duration(seconds: 5), (timer) {
      _checkStatus();
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _checkStatus() async {
    if (_isLoading) return;
    
    setState(() {
      _isLoading = true;
    });

    try {
      final url = Uri.parse(
        'https://majestiksolutions.pythonanywhere.com/api/device/status/',
      );

      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'fcm_token': widget.fcmToken,
        }),
      );

      if (response.statusCode >= 200 && response.statusCode < 300) {
        final data = jsonDecode(response.body);
        final bool isApproved = data['aprobado'] ?? false;
        
        if (isApproved) {
          _timer?.cancel();
          // Guardar estado en SharedPreferences
          final prefs = await SharedPreferences.getInstance();
          await prefs.setBool('device_approved', true);
          
          if (!mounted) return;
          // Redirigir al webview
          Navigator.of(context).pushReplacement(
            MaterialPageRoute(
               builder: (_) => const WebViewScreen(initialUrl: kPanelBaseUrl),
            ),
          );
        }
      } else if (response.statusCode == 404) {
        setState(() {
          _message = 'El dispositivo fue eliminado. Por favor reinicia la aplicación.';
        });
        _timer?.cancel();
      }
    } catch (e) {
      debugPrint("Error polling status: $e");
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: const SystemUiOverlayStyle(
        statusBarColor: Colors.transparent,
        statusBarIconBrightness: Brightness.dark,
        systemNavigationBarColor: Colors.transparent,
        systemNavigationBarIconBrightness: Brightness.dark,
      ),
      child: Scaffold(
        backgroundColor: const Color(0xFFFAFAF9), // stone-50
        body: Stack(
          children: [
            // Background blobs ligeros (colores const, sin blur)
            const Positioned(
              top: -100,
              left: -50,
              child: _BlobCircle(size: 350, color: Color(0x40F97316)), // Primary 25%
            ),
            const Positioned(
              bottom: -50,
              right: -100,
              child: _BlobCircle(size: 450, color: Color(0x33FBBF24)), // Amber 20%
            ),
            const Positioned(
              top: 250,
              right: -50,
              child: _BlobCircle(size: 250, color: Color(0x26F43F5E)), // Rose 15%
            ),
            // Fondo semi-transparente
            Positioned.fill(
              child: Container(color: const Color(0xD9FAFAF9)), // stone-50 ~85%
            ),

            // Main Glass Card Content (sin BackdropFilter — rendimiento)
            Center(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 32.0),
                child: Container(
                  decoration: BoxDecoration(
                    color: const Color(0x99FFFFFF), // white 60%
                    borderRadius: BorderRadius.circular(32),
                    border: Border.all(color: const Color(0xCCFFFFFF), width: 1.5), // white 80%
                    boxShadow: const [
                      BoxShadow(
                        color: Color(0x1AF97316), // orange 10%
                        blurRadius: 30,
                        spreadRadius: 5,
                      )
                    ],
                  ),
                  padding: const EdgeInsets.symmetric(horizontal: 32.0, vertical: 48.0),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(
                        width: 80,
                        height: 80,
                        decoration: BoxDecoration(
                          color: const Color(0xFFFFF7ED), // orange-50
                          shape: BoxShape.circle,
                          border: Border.all(color: const Color(0xFFFFEDD5), width: 2), // orange-100
                        ),
                        child: const Center(
                          child: SizedBox(
                            width: 36,
                            height: 36,
                            child: CircularProgressIndicator(
                              color: Color(0xFFF97316), // Primary
                              strokeWidth: 4,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 32),
                      const Text(
                        'En Revisión',
                        style: TextStyle(
                          fontSize: 28,
                          fontWeight: FontWeight.w900,
                          color: Color(0xFF1C1917), // stone-900
                          letterSpacing: -0.5,
                        ),
                      ),
                      const SizedBox(height: 16),
                      Text(
                        _message,
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w500,
                            color: Color(0xFF57534E), // stone-500
                            height: 1.5,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

/// Widget ligero para los blobs de fondo — const, sin repaint
class _BlobCircle extends StatelessWidget {
  final double size;
  final Color color;
  const _BlobCircle({required this.size, required this.color});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: DecoratedBox(
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: color,
        ),
      ),
    );
  }
}
