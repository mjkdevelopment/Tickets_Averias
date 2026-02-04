import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:http/http.dart' as http;
import 'package:webview_flutter/webview_flutter.dart';

/// Handler para mensajes en background (incluye teléfono bloqueado)
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  debugPrint('🔔 [BACKGROUND] Mensaje: ${message.messageId}');
}

// Plugin global de notificaciones locales
final FlutterLocalNotificationsPlugin flutterLocalNotificationsPlugin =
    FlutterLocalNotificationsPlugin();

Future<void> _initLocalNotifications() async {
  const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');

  const initSettings = InitializationSettings(
    android: androidSettings,
  );

  await flutterLocalNotificationsPlugin.initialize(initSettings);
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

  await flutterLocalNotificationsPlugin.show(
    message.hashCode,
    message.notification?.title ?? 'Nuevo ticket',
    message.notification?.body ?? 'Se ha creado un nuevo ticket',
    notificationDetails,
  );
}

/// Clave global para navegar desde callbacks de FCM
final GlobalKey<NavigatorState> navigatorKey = GlobalKey<NavigatorState>();

/// URL base del panel web
const String kPanelBaseUrl =
    'https://majestiksolutions.pythonanywhere.com/tickets/';

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
  String? _token;
  final TextEditingController _usernameController = TextEditingController();
  bool _isRegistering = false;
  String? _registerMessage;

  /// Para manejar el caso en el que la app se abre desde una notificación
  /// cuando todavía no existe el Navigator
  String? _pendingInitialUrl;

  @override
  void initState() {
    super.initState();
    _initFCM();
  }

  Future<void> _initFCM() async {
    final messaging = FirebaseMessaging.instance;

    // Pedir permisos (Android 13+ y iOS)
    await messaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );

    // Obtener FCM token de este dispositivo
    final token = await messaging.getToken();
    setState(() => _token = token);
    debugPrint('📱 FCM token: $token');

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

  Future<void> _registerDeviceOnServer() async {
    final username = _usernameController.text.trim();

    if (username.isEmpty || _token == null) {
      setState(() {
        _registerMessage =
            'Escribe el nombre de usuario y espera a que aparezca el token.';
      });
      return;
    }

    setState(() {
      _isRegistering = true;
      _registerMessage = null;
    });

    try {
      final url = Uri.parse(
        'https://majestiksolutions.pythonanywhere.com/api/register-device/',
      );

      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'username': username,
          'fcm_token': _token,
        }),
      );

      if (!mounted) return;

      if (response.statusCode >= 200 && response.statusCode < 300) {
        setState(() {
          _registerMessage =
              '✅ Dispositivo registrado correctamente para el usuario "$username".';
        });
      } else {
        setState(() {
          _registerMessage =
              '❌ Error (${response.statusCode}): ${response.body}';
        });
      }
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _registerMessage = '❌ Error de red: $e';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isRegistering = false;
        });
      }
    }
  }

  @override
  void dispose() {
    _usernameController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Botija Tickets',
      navigatorKey: navigatorKey,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFFFF6600)),
        useMaterial3: true,
      ),
      home: Builder(
        builder: (context) {
          // Si hay una URL pendiente de abrir (app lanzada desde notificación)
          if (_pendingInitialUrl != null) {
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

          return HomeScreen(
            token: _token,
            usernameController: _usernameController,
            isRegistering: _isRegistering,
            registerMessage: _registerMessage,
            onRegisterDevice: _registerDeviceOnServer,
          );
        },
      ),
    );
  }
}

class HomeScreen extends StatelessWidget {
  final String? token;
  final TextEditingController usernameController;
  final bool isRegistering;
  final String? registerMessage;
  final Future<void> Function() onRegisterDevice;

  const HomeScreen({
    super.key,
    required this.token,
    required this.usernameController,
    required this.isRegistering,
    required this.registerMessage,
    required this.onRegisterDevice,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Botija Tickets'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // LOGO + título
            Center(
              child: Column(
                children: [
                  Image.asset(
                    'assets/botija_logo.png',
                    height: 80,
                  ),
                  const SizedBox(height: 12),
                  const Text(
                    'Notificaciones y acceso rápido',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // Tarjeta de token / registro
            Card(
              elevation: 2,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Token de este dispositivo:',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    SelectableText(
                      token ?? 'Obteniendo token...',
                      style: const TextStyle(fontSize: 12),
                    ),
                    const SizedBox(height: 16),
                    const Divider(),
                    const SizedBox(height: 8),
                    const Text(
                      'Registrar este dispositivo en el servidor Django:',
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      controller: usernameController,
                      decoration: const InputDecoration(
                        labelText:
                            'Usuario (igual que en la web: erick, malvin, etc.)',
                        border: OutlineInputBorder(),
                      ),
                    ),
                    const SizedBox(height: 8),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        onPressed: isRegistering ? null : onRegisterDevice,
                        icon: isRegistering
                            ? const SizedBox(
                                width: 16,
                                height: 16,
                                child:
                                    CircularProgressIndicator(strokeWidth: 2),
                              )
                            : const Icon(Icons.save),
                        label: Text(
                          isRegistering
                              ? 'Registrando...'
                              : 'Registrar dispositivo en Botija Tickets',
                        ),
                      ),
                    ),
                    if (registerMessage != null) ...[
                      const SizedBox(height: 8),
                      Text(
                        registerMessage!,
                        style: const TextStyle(fontSize: 13),
                      ),
                    ],
                  ],
                ),
              ),
            ),

            const SizedBox(height: 16),

            // Tarjeta para abrir el panel web
            Card(
              elevation: 2,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Panel web de Botija Tickets',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Desde aquí puedes abrir el sistema web de tickets dentro de la app. '
                      'Inicia sesión una vez y la sesión quedará guardada en el WebView.',
                    ),
                    const SizedBox(height: 12),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        onPressed: () {
                          Navigator.of(context).push(
                            MaterialPageRoute(
                              builder: (_) => const WebViewScreen(
                                initialUrl: kPanelBaseUrl,
                              ),
                            ),
                          );
                        },
                        icon: const Icon(Icons.open_in_browser),
                        label: const Text('Abrir Botija Tickets'),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
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
      appBar: AppBar(
        title: const Text('Botija Tickets'),
        actions: [
          IconButton(
            onPressed: () => _controller.reload(),
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: Stack(
        children: [
          WebViewWidget(controller: _controller),
          if (_isLoading)
            const Center(
              child: CircularProgressIndicator(),
            ),
        ],
      ),
    );
  }
}
