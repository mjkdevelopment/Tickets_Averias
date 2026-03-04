import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'waiting_room.dart';
import 'main.dart'; // For navigatorKey

class OnboardingWizard extends StatefulWidget {
  const OnboardingWizard({super.key});

  @override
  State<OnboardingWizard> createState() => _OnboardingWizardState();
}

class _OnboardingWizardState extends State<OnboardingWizard> {
  final PageController _pageController = PageController();
  final TextEditingController _usernameController = TextEditingController();
  int _currentPage = 0;
  bool _isLoading = false;
  String? _errorMessage;
  String? _fcmToken;

  @override
  void dispose() {
    _pageController.dispose();
    _usernameController.dispose();
    super.dispose();
  }

  void _nextPage() {
    _pageController.nextPage(
      duration: const Duration(milliseconds: 400),
      curve: Curves.easeInOutCubic,
    );
  }

  Future<void> _requestPermissions() async {
    setState(() { _isLoading = true; });
    final messaging = FirebaseMessaging.instance;
    await messaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );
    final token = await messaging.getToken();
    setState(() {
      _fcmToken = token;
      _isLoading = false;
    });
    _nextPage();
  }

  Future<void> _enrollDevice() async {
    final username = _usernameController.text.trim();
    if (username.isEmpty) {
      setState(() { _errorMessage = 'Por favor ingresa tu nombre de usuario.'; });
      return;
    }
    if (_fcmToken == null) {
      setState(() { _errorMessage = 'Token no disponible. Intenta abrir la app de nuevo.'; });
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final url = Uri.parse(
        'https://majestiksolutions.pythonanywhere.com/api/device/enroll/',
      );

      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'username': username,
          'fcm_token': _fcmToken,
        }),
      );

      if (!mounted) return;

      if (response.statusCode >= 200 && response.statusCode < 300) {
        final data = jsonDecode(response.body);
        final bool isApproved = data['aprobado'] ?? false;

        final prefs = await SharedPreferences.getInstance();
        await prefs.setBool('device_enrolled', true);
        
        if (isApproved) {
           await prefs.setBool('device_approved', true);
           if (!mounted) return;
           Navigator.of(context).pushReplacement(
              MaterialPageRoute(builder: (_) => const WebViewScreen(initialUrl: kPanelBaseUrl)),
           );
        } else {
           if (!mounted) return;
           Navigator.of(context).pushReplacement(
              MaterialPageRoute(builder: (_) => WaitingRoomScreen(fcmToken: _fcmToken!)),
           );
        }
      } else {
        setState(() {
          _errorMessage = 'Error ${response.statusCode}: El usuario no existe o hubo un problema.';
        });
      }
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _errorMessage = 'Error de conexión: $e';
      });
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
            // Background blobs ligeros (const, sin blur)
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

          // Main Content
          SafeArea(
            child: PageView(
              controller: _pageController,
              physics: const NeverScrollableScrollPhysics(),
              onPageChanged: (int page) {
                setState(() { _currentPage = page; });
              },
              children: [
                // Screen 1: Welcome
                _buildPage(
                  title: 'Botija Tickets',
                  content: 'Bienvenido al sistema premium de administración y tickets de averías.',
                  imageAsset: 'assets/botija_logo.png',
                  buttonText: 'Empezar',
                  onPressed: _nextPage,
                ),
                // Screen 2: Permissions
                _buildPage(
                  title: 'Notificaciones',
                  content: 'Necesitamos enviarte alertas rápidas para cuando se te asignen tickets de avería operativos.',
                  iconData: Icons.notifications_active_rounded,
                  iconColor: const Color(0xFFF59E0B), // amber-500
                  buttonText: 'Conceder Permisos',
                  onPressed: _requestPermissions,
                  isLoading: _isLoading,
                ),
                // Screen 3: Enrollment
                _buildEnrollmentPage(),
              ],
            ),
          ),
          
          // Page Indicators
          Positioned(
            bottom: 40,
            left: 0,
            right: 0,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(3, (index) => _buildIndicator(index == _currentPage)),
            ),
          ),
        ],
      ),
      ),
    );
  }

  Widget _buildIndicator(bool isActive) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      margin: const EdgeInsets.symmetric(horizontal: 4.0),
      height: 8.0,
      width: isActive ? 24.0 : 8.0,
      decoration: BoxDecoration(
        color: isActive ? const Color(0xFFF97316) : Colors.black26,
        borderRadius: BorderRadius.circular(4.0),
      ),
    );
  }

  Widget _buildPage({
    required String title,
    required String content,
    String? imageAsset,
    IconData? iconData,
    Color? iconColor,
    required String buttonText,
    required VoidCallback onPressed,
    bool isLoading = false,
  }) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 24.0),
        child: Container(
          decoration: BoxDecoration(
            color: const Color(0xF2FFFFFF), // white 95%
            borderRadius: BorderRadius.circular(32),
            border: Border.all(color: const Color(0xCCFFFFFF), width: 1.5), // white 80%
            boxShadow: const [
              BoxShadow(
                color: Color(0x14F97316), // orange 8%
                blurRadius: 30,
                spreadRadius: 5,
              )
            ]
          ),
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 48.0),
          child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (imageAsset != null) 
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: const BoxDecoration(
                        color: Color(0xCCFFFFFF), // white 80%
                        shape: BoxShape.circle,
                        boxShadow: [
                          BoxShadow(
                            color: Color(0x0D000000), // black 5%
                            blurRadius: 20,
                            spreadRadius: 5,
                          )
                        ]
                      ),
                      child: Image.asset(imageAsset, height: 100),
                    ),
                  if (iconData != null) 
                    Container(
                      padding: const EdgeInsets.all(24),
                      decoration: const BoxDecoration(
                        color: Color(0xCCFFFFFF), // white 80%
                        shape: BoxShape.circle,
                        boxShadow: [
                          BoxShadow(
                            color: Color(0x0D000000), // black 5%
                            blurRadius: 20,
                            spreadRadius: 5,
                          )
                        ]
                      ),
                      child: Icon(iconData, size: 80, color: iconColor ?? const Color(0xFFF97316)),
                    ),
                  const SizedBox(height: 48),
                  Text(
                    title,
                    style: const TextStyle(
                      fontSize: 28, 
                      fontWeight: FontWeight.w900,
                      color: Color(0xFF1C1917), // stone-900
                      letterSpacing: -0.5,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    content,
                    style: const TextStyle(
                      fontSize: 16, 
                      fontWeight: FontWeight.w500,
                      color: Color(0xFF57534E), // stone-500
                      height: 1.5,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 48),
                  SizedBox(
                    width: double.infinity,
                    height: 56,
                    child: ElevatedButton(
                      onPressed: isLoading ? null : onPressed,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF1C1917), // stone-900
                        foregroundColor: Colors.white,
                        elevation: 8,
                        shadowColor: Colors.black45,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                      ),
                      child: isLoading
                          ? const CircularProgressIndicator(color: Colors.white)
                          : Text(
                              buttonText, 
                              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                            ),
                    ),
                  )
                ],
              ),
            ),
          ),
        ),
      );
  }

  Widget _buildEnrollmentPage() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 24.0),
        child: Container(
          decoration: BoxDecoration(
            color: const Color(0xF2FFFFFF), // white 95%
            borderRadius: BorderRadius.circular(32),
            border: Border.all(color: const Color(0xCCFFFFFF), width: 1.5), // white 80%
            boxShadow: const [
              BoxShadow(
                color: Color(0x14F97316), // orange 8%
                blurRadius: 30,
                spreadRadius: 5,
              )
            ]
          ),
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 48.0),
          child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      padding: const EdgeInsets.all(20),
                      decoration: const BoxDecoration(
                        color: Color(0xCCFFFFFF), // white 80%
                        shape: BoxShape.circle,
                        boxShadow: [
                          BoxShadow(
                            color: Color(0x0D000000), // black 5%
                            blurRadius: 20,
                            spreadRadius: 5,
                          )
                        ]
                      ),
                      child: const Icon(Icons.person_add_rounded, size: 70, color: Color(0xFFF97316)),
                    ),
                    const SizedBox(height: 32),
                    const Text(
                      'Inscripción de Equipo',
                      style: TextStyle(
                        fontSize: 26, 
                        fontWeight: FontWeight.w900,
                        color: Color(0xFF1C1917),
                        letterSpacing: -0.5,
                      ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 12),
                    const Text(
                      'Ingresa el nombre de usuario que usas para entrar en el panel web de tickets.',
                      style: TextStyle(
                        fontSize: 15, 
                        fontWeight: FontWeight.w500,
                        color: Color(0xFF57534E),
                        height: 1.5,
                      ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 32),
                    Container(
                      decoration: BoxDecoration(
                        color: const Color(0xCCFFFFFF), // white 80%
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: const Color(0xFFD6D3D1)), // stone-300
                      ),
                      child: TextField(
                        controller: _usernameController,
                        style: const TextStyle(fontWeight: FontWeight.w600, color: Color(0xFF1C1917)),
                        decoration: InputDecoration(
                          hintText: 'ej. malvin, erick',
                          hintStyle: const TextStyle(color: Color(0xFFA8A29E)),
                          border: InputBorder.none,
                          contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                          prefixIcon: const Icon(Icons.person, color: Color(0xFFA8A29E)),
                        ),
                      ),
                    ),
                    if (_errorMessage != null) ...[
                      const SizedBox(height: 16),
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFEF2F2), // red-50
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: const Color(0xFFFECACA)), // red-200
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.error_outline, color: Color(0xFFEF4444), size: 20),
                            const SizedBox(width: 8),
                            Expanded(child: Text(_errorMessage!, style: const TextStyle(color: Color(0xFFB91C1C), fontSize: 13, fontWeight: FontWeight.bold))),
                          ],
                        ),
                      ),
                    ],
                    const SizedBox(height: 32),
                    SizedBox(
                      width: double.infinity,
                      height: 56,
                      child: ElevatedButton(
                        onPressed: _isLoading ? null : _enrollDevice,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFFF97316), // Primary
                          foregroundColor: Colors.white,
                          elevation: 8,
                          shadowColor: const Color(0x80F97316), // orange 50%,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                        ),
                        child: _isLoading
                            ? const CircularProgressIndicator(color: Colors.white)
                            : const Text(
                                'Solicitar Acceso', 
                                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                              ),
                      ),
                    )
                  ],
                ),
              ),
            ),
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
