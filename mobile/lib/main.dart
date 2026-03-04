import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:url_launcher/url_launcher.dart';

import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'wizard.dart';
import 'waiting_room.dart';

/// Handler para mensajes en background (incluye teléfono bloqueado)
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  debugPrint('🔔 [BACKGROUND] Mensaje: ${message.messageId}');
}

// Plugin global de notificaciones locales
final FlutterLocalNotificationsPlugin flutterLocalNotificationsPlugin =
    FlutterLocalNotificationsPlugin();

/// Callback cuando se toca una notificación local (foreground)
void _onDidReceiveNotificationResponse(NotificationResponse response) {
  final payload = response.payload;
  if (payload != null && payload.isNotEmpty) {
    debugPrint('🔔 [LOCAL TAP] Payload: $payload');
    final ctx = navigatorKey.currentContext;
    if (ctx != null) {
      Navigator.of(ctx).push(
        MaterialPageRoute(
          builder: (_) => WebViewScreen(initialUrl: payload),
        ),
      );
    }
  }
}

Future<void> _initLocalNotifications() async {
  const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');

  const initSettings = InitializationSettings(
    android: androidSettings,
  );

  await flutterLocalNotificationsPlugin.initialize(
    initSettings,
    onDidReceiveNotificationResponse: _onDidReceiveNotificationResponse,
  );
}

Future<void> _showForegroundNotification(RemoteMessage message) async {
  const androidDetails = AndroidNotificationDetails(
    'botija_tickets_channel', // id del canal
    'Botija Tickets', // nombre del canal
    channelDescription: 'Notificaciones de tickets',
    importance: Importance.max,
    priority: Priority.high,
  );

  const notificationDetails = NotificationDetails(android: androidDetails);

  // Pasar ticket_url como payload para que al tocar abra el ticket
  final ticketUrl = message.data['ticket_url'] ?? '';

  await flutterLocalNotificationsPlugin.show(
    message.hashCode,
    message.notification?.title ?? 'Nuevo ticket',
    message.notification?.body ?? 'Se ha creado un nuevo ticket',
    notificationDetails,
    payload: ticketUrl,
  );
}

/// Clave global para navegar desde callbacks de FCM
final GlobalKey<NavigatorState> navigatorKey = GlobalKey<NavigatorState>();

/// URL base del panel web
const String kPanelBaseUrl =
    'https://majestiksolutions.pythonanywhere.com/tickets/';

/// Versión actual de la app (debe coincidir con config/app_version.py en el server)
const String kAppVersion = '1.0.2';

/// URL de la API de versión
const String kVersionApiUrl =
    'https://majestiksolutions.pythonanywhere.com/api/app/version/';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Inicializar Firebase
  await Firebase.initializeApp();

  // Registrar handler de mensajes en background
  FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);

  // Inicializar notificaciones locales (para foreground)
  await _initLocalNotifications();

  runApp(const MyApp());
}

class MyApp extends StatefulWidget {
  const MyApp({super.key});

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  bool _isInit = false;
  bool _isEnrolled = false;
  bool _isApproved = false;
  bool _needsUpdate = false;
  String? _downloadUrl;
  String? _fcmToken;

  /// Para manejar el caso en el que la app se abre desde una notificación
  /// cuando todavía no existe el Navigator
  String? _pendingInitialUrl;

  @override
  void initState() {
    super.initState();
    _initializeApp();
  }

  Future<void> _initializeApp() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _isEnrolled = prefs.getBool('device_enrolled') ?? false;
      _isApproved = prefs.getBool('device_approved') ?? false;
    });

    final messaging = FirebaseMessaging.instance;
    _fcmToken = await messaging.getToken();

    // Mensajes cuando la app está ABIERTA (foreground)
    FirebaseMessaging.onMessage.listen((RemoteMessage message) async {
      debugPrint('🔔 [FOREGROUND] Mensaje: ${message.messageId}');
      await _showForegroundNotification(message);
    });

    // Cuando el usuario toca una notificación y la app estaba en background
    FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
      debugPrint(
          '🔔 [CLICK NOTIFICACIÓN - onMessageOpenedApp] Datos: ${message.data}');
      _handleNotificationTap(message.data);
    });

    // Cuando la app estaba completamente cerrada y se abre desde la notificación
    final initialMessage = await messaging.getInitialMessage();
    if (initialMessage != null) {
      debugPrint(
          '🔔 [CLICK NOTIFICACIÓN - getInitialMessage] Datos: ${initialMessage.data}');
      _handleNotificationTap(initialMessage.data);
    }

    // Verificar si hay actualización disponible
    await _checkForUpdate();
    
    setState(() {
      _isInit = true;
    });
  }

  Future<void> _checkForUpdate() async {
    try {
      final response = await http.get(Uri.parse(kVersionApiUrl)).timeout(
        const Duration(seconds: 5),
      );
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final serverVersion = data['version'] as String;
        final downloadUrl = data['download_url'] as String;

        if (serverVersion != kAppVersion) {
          debugPrint('⚠️ App desactualizada: local=$kAppVersion server=$serverVersion');
          setState(() {
            _needsUpdate = true;
            _downloadUrl = downloadUrl;
          });
        } else {
          debugPrint('✅ App actualizada: $kAppVersion');
        }
      }
    } catch (e) {
      debugPrint('ℹ️ No se pudo verificar versión: $e');
      // Si falla la verificación, no bloquear al usuario
    }
  }

  void _handleNotificationTap(Map<String, dynamic> data) {
    final url = (data['ticket_url'] ?? '') as String;

    if (url.isEmpty) {
      debugPrint('ℹ️ Notificación sin ticket_url en data.');
      return;
    }

    final ctx = navigatorKey.currentContext;
    if (ctx != null) {
      Navigator.of(ctx).push(
        MaterialPageRoute(
          builder: (_) => WebViewScreen(initialUrl: url),
        ),
      );
    } else {
      // Guardamos para abrirla después, cuando haya contexto
      _pendingInitialUrl = url;
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!_isInit) {
      return MaterialApp(
        home: Scaffold(
          body: Center(child: CircularProgressIndicator(color: const Color(0xFFF97316))),
        )
      );
    }

    Widget homeWidget;
    if (_needsUpdate) {
      homeWidget = UpdateRequiredScreen(downloadUrl: _downloadUrl ?? '');
    } else if (_isApproved) {
      homeWidget = const WebViewScreen(initialUrl: kPanelBaseUrl);
    } else if (_isEnrolled) {
      homeWidget = WaitingRoomScreen(fcmToken: _fcmToken!);
    } else {
      homeWidget = const OnboardingWizard();
    }

    return MaterialApp(
      title: 'Botija Tickets',
      navigatorKey: navigatorKey,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFFF97316)), // Sunset Orange 
        useMaterial3: true,
      ),
      home: Builder(
        builder: (context) {
          if (_pendingInitialUrl != null && _isApproved) {
            final url = _pendingInitialUrl!;
            _pendingInitialUrl = null;

            WidgetsBinding.instance.addPostFrameCallback((_) {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => WebViewScreen(initialUrl: url),
                ),
              );
            });
          }
          return homeWidget;
        },
      ),
    );
  }
}

/// Pantalla con WebView embebido
class WebViewScreen extends StatefulWidget {
  final String initialUrl;

  const WebViewScreen({super.key, required this.initialUrl});

  @override
  State<WebViewScreen> createState() => _WebViewScreenState();
}

class _WebViewScreenState extends State<WebViewScreen> {
  late final WebViewController _controller;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();

    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(
        NavigationDelegate(
          onPageStarted: (_) {
            setState(() {
              _isLoading = true;
            });
          },
          onPageFinished: (_) {
            setState(() {
              _isLoading = false;
            });
          },
        ),
      )
      ..loadRequest(Uri.parse(widget.initialUrl));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          // Safely avoid the native status bar at top (iOS/Android notch) and bottom nav
          SafeArea(
            child: WebViewWidget(controller: _controller),
          ),
          if (_isLoading)
            const Center(
              child: CircularProgressIndicator(color: Color(0xFFF97316)),
            ),
        ],
      ),
    );
  }
}

/// Pantalla de actualización obligatoria
class UpdateRequiredScreen extends StatelessWidget {
  final String downloadUrl;

  const UpdateRequiredScreen({super.key, required this.downloadUrl});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Color(0xFFFFF7ED), Color(0xFFFFEDD5), Color(0xFFFED7AA)],
          ),
        ),
        child: SafeArea(
          child: Center(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 32),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  // Icon
                  Container(
                    width: 90,
                    height: 90,
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [Color(0xFFF97316), Color(0xFFEA580C)],
                      ),
                      borderRadius: BorderRadius.circular(24),
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0xFFF97316).withOpacity(0.3),
                          blurRadius: 24,
                          offset: const Offset(0, 8),
                        ),
                      ],
                    ),
                    child: const Icon(
                      Icons.system_update,
                      size: 44,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 32),

                  // Title
                  const Text(
                    'Actualización Disponible',
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.w800,
                      color: Color(0xFF1C1917),
                      letterSpacing: -0.5,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 12),

                  // Description
                  const Text(
                    'Hay una nueva versión de la app disponible. Por favor actualiza para continuar.',
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w500,
                      color: Color(0xFF78716C),
                      height: 1.5,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 8),

                  // Version info
                  Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 16, vertical: 8),
                    decoration: BoxDecoration(
                      color: const Color(0xFFFFF7ED),
                      border: Border.all(color: const Color(0xFFFDBA74)),
                      borderRadius: BorderRadius.circular(999),
                    ),
                    child: Text(
                      'Tu versión: $kAppVersion',
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                        color: Color(0xFF9A3412),
                      ),
                    ),
                  ),
                  const SizedBox(height: 36),

                  // Download button
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: () async {
                        final uri = Uri.parse(downloadUrl);
                        if (await canLaunchUrl(uri)) {
                          await launchUrl(uri,
                              mode: LaunchMode.externalApplication);
                        }
                      },
                      icon: const Icon(Icons.download, color: Colors.white),
                      label: const Text(
                        'Descargar Actualización',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                          color: Colors.white,
                        ),
                      ),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFFF97316),
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16),
                        ),
                        elevation: 4,
                        shadowColor:
                            const Color(0xFFF97316).withOpacity(0.3),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
