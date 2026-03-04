import 'dart:convert';

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
    
    setState(() {
      _isInit = true;
    });
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
    if (_isApproved) {
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
