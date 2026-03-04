import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:url_launcher/url_launcher.dart';
import 'package:dio/dio.dart';
import 'package:open_filex/open_filex.dart';
import 'package:path_provider/path_provider.dart';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:webview_flutter_android/webview_flutter_android.dart';
import 'package:file_picker/file_picker.dart';
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
const String kAppVersion = '1.0.7';

/// URL de la API de versión
const String kVersionApiUrl =
    'https://majestiksolutions.pythonanywhere.com/api/app/version/';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Modo inmersivo: oculta completamente la barra de navegación Android
  // El usuario puede deslizar hacia arriba para verla temporalmente
  SystemChrome.setEnabledSystemUIMode(
    SystemUiMode.immersiveSticky,
  );

  // Barras de sistema transparentes para experiencia inmersiva
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.dark,
    systemNavigationBarColor: Colors.transparent,
    systemNavigationBarIconBrightness: Brightness.dark,
    systemNavigationBarDividerColor: Colors.transparent,
  ));

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

    // Navegar al ticket pendiente después de que el widget tree esté listo
    if (_pendingInitialUrl != null && _isApproved && !_needsUpdate) {
      final url = _pendingInitialUrl!;
      _pendingInitialUrl = null;
      WidgetsBinding.instance.addPostFrameCallback((_) {
        final ctx = navigatorKey.currentContext;
        if (ctx != null) {
          Navigator.of(ctx).push(
            MaterialPageRoute(
              builder: (_) => WebViewScreen(initialUrl: url),
            ),
          );
        }
      });
    }
  }

  Future<void> _checkForUpdate() async {
    try {
      final response = await http.get(Uri.parse(kVersionApiUrl)).timeout(
        const Duration(seconds: 15),
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

class _WebViewScreenState extends State<WebViewScreen> with WidgetsBindingObserver {
  late final WebViewController _controller;
  bool _isLoading = true;

  /// CSS que se inyecta en el WebView para deshabilitar efectos pesados
  /// y mejorar el rendimiento en dispositivos Android de gama media/baja.
  static const String _perfCss = '''(function(){
    var b=document.querySelector('.fixed.pointer-events-none');
    if(b)b.style.display='none';
    if(document.getElementById('_wvp'))return;
    var s=document.createElement('style');
    s.id='_wvp';
    s.textContent=
      '.glass{backdrop-filter:none!important;-webkit-backdrop-filter:none!important;background:rgba(255,255,255,0.97)!important}'
      +'.neon-snake::before{display:none!important}'
      +'.alert-pulse,.badge-pulse{animation:none!important}'
      +'.animate-fade-in-up{animation:none!important;opacity:1!important}'
      +'.card-hover,.card-hover *{transition:none!important}'
      +'.flex.overflow-x-auto{flex-wrap:wrap!important;overflow-x:visible!important;overflow:visible!important}'
      +'.mix-blend-multiply{mix-blend-mode:normal!important;filter:none!important}'
      +'.blur-3xl{filter:none!important;-webkit-filter:none!important}'
      +'.filter{filter:none!important;-webkit-filter:none!important}'
      +'nav.absolute{backdrop-filter:none!important;-webkit-backdrop-filter:none!important;background:rgba(255,255,255,0.98)!important}';
    document.head.appendChild(s);
    document.documentElement.style.webkitTapHighlightColor='transparent';
  })();''';

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);

    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..enableZoom(false)
      ..setNavigationDelegate(
        NavigationDelegate(
          onPageStarted: (_) {
            if (mounted) setState(() { _isLoading = true; });
          },
          onPageFinished: (_) {
            if (mounted) setState(() { _isLoading = false; });
            // Inyectar CSS ligero para rendimiento móvil
            _controller.runJavaScript(_perfCss);
            // Re-aplicar modo inmersivo después de cada carga de página
            SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersiveSticky);
          },
        ),
      )
      ..loadRequest(Uri.parse(widget.initialUrl));

    // Habilitar selección de archivos (input type="file") en Android WebView
    if (_controller.platform is AndroidWebViewController) {
      (_controller.platform as AndroidWebViewController).setOnShowFileSelector(
        (FileSelectorParams params) async {
          try {
            // Determinar si acepta solo imágenes
            final acceptsImages = params.acceptTypes.any(
              (t) => t.contains('image'),
            );

            final result = await FilePicker.platform.pickFiles(
              type: acceptsImages ? FileType.image : FileType.any,
              allowMultiple: params.mode == FileSelectorMode.openMultiple,
            );

            if (result == null || result.files.isEmpty) return [];

            return result.files
                .where((f) => f.path != null)
                .map((f) => Uri.file(f.path!).toString())
                .toList();
          } catch (e) {
            debugPrint('Error al seleccionar archivo: $e');
            return [];
          }
        },
      );
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      // Re-aplicar modo inmersivo al volver del fondo
      SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersiveSticky);
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
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
        body: Stack(
          children: [
            // Edge-to-edge: SafeArea solo en top para evitar overlap con notch/status bar
            SafeArea(
              bottom: false, // Permitir contenido hasta el borde inferior
              child: WebViewWidget(controller: _controller),
            ),
            if (_isLoading)
              const Center(
                child: CircularProgressIndicator(color: Color(0xFFF97316)),
              ),
            // Indicador de versión no invasivo
            Positioned(
              bottom: MediaQuery.of(context).padding.bottom + 4,
              right: 8,
              child: IgnorePointer(
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: const Color(0x33000000), // negro 20%
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: const Text(
                    'v$kAppVersion',
                    style: TextStyle(
                      fontSize: 9,
                      color: Color(0x99FFFFFF), // blanco 60%
                      fontWeight: FontWeight.w500,
                    ),
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

/// Pantalla de actualización obligatoria con descarga y barra de progreso
class UpdateRequiredScreen extends StatefulWidget {
  final String downloadUrl;

  const UpdateRequiredScreen({super.key, required this.downloadUrl});

  @override
  State<UpdateRequiredScreen> createState() => _UpdateRequiredScreenState();
}

class _UpdateRequiredScreenState extends State<UpdateRequiredScreen> {
  bool _isDownloading = false;
  double _progress = 0.0;
  String _statusText = '';
  String? _errorText;

  Future<void> _downloadAndInstall() async {
    setState(() {
      _isDownloading = true;
      _progress = 0.0;
      _statusText = 'Iniciando descarga...';
      _errorText = null;
    });

    try {
      // Usar HTTP en vez de HTTPS para evitar problemas de descarga en Android
      String url = widget.downloadUrl;
      if (url.startsWith('https://')) {
        url = url.replaceFirst('https://', 'http://');
      }

      // Obtener directorio temporal
      final dir = await getTemporaryDirectory();
      final filePath = '${dir.path}/mjk_tickets.apk';

      // Eliminar APK anterior si existe
      final oldFile = File(filePath);
      if (await oldFile.exists()) {
        await oldFile.delete();
      }

      // Descargar con Dio y progreso
      final dio = Dio();
      await dio.download(
        url,
        filePath,
        onReceiveProgress: (received, total) {
          if (total > 0 && mounted) {
            setState(() {
              _progress = received / total;
              final mb = (received / 1024 / 1024).toStringAsFixed(1);
              final totalMb = (total / 1024 / 1024).toStringAsFixed(1);
              _statusText = 'Descargando $mb / $totalMb MB';
            });
          }
        },
      );

      if (!mounted) return;

      setState(() {
        _statusText = 'Descarga completa. Abriendo instalador...';
        _progress = 1.0;
      });

      // Abrir el APK para instalar
      final result = await OpenFilex.open(filePath, type: 'application/vnd.android.package-archive');

      if (result.type != ResultType.done && mounted) {
        setState(() {
          _errorText = 'No se pudo abrir el instalador. Ve a Archivos y abre mjk_tickets.apk manualmente.';
          _isDownloading = false;
        });
      }
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _errorText = 'Error al descargar: $e';
        _isDownloading = false;
      });
    }
  }

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
                      boxShadow: const [
                        BoxShadow(
                          color: Color(0x4DF97316),
                          blurRadius: 24,
                          offset: Offset(0, 8),
                        ),
                      ],
                    ),
                    child: Icon(
                      _isDownloading ? Icons.downloading : Icons.system_update,
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
                  Text(
                    _isDownloading
                        ? _statusText
                        : 'Hay una nueva versión de la app disponible. Por favor actualiza para continuar.',
                    style: const TextStyle(
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
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
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
                  const SizedBox(height: 24),

                  // Barra de progreso
                  if (_isDownloading) ...[
                    ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: LinearProgressIndicator(
                        value: _progress,
                        minHeight: 12,
                        backgroundColor: const Color(0xFFFFEDD5),
                        valueColor: const AlwaysStoppedAnimation<Color>(Color(0xFFF97316)),
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '${(_progress * 100).toStringAsFixed(0)}%',
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w800,
                        color: Color(0xFFF97316),
                      ),
                    ),
                    const SizedBox(height: 24),
                  ],

                  // Error message
                  if (_errorText != null) ...[
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: const Color(0xFFFEF2F2),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: const Color(0xFFFECACA)),
                      ),
                      child: Text(
                        _errorText!,
                        style: const TextStyle(color: Color(0xFFB91C1C), fontSize: 13, fontWeight: FontWeight.w600),
                        textAlign: TextAlign.center,
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],

                  // Download button
                  if (!_isDownloading || _errorText != null)
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        onPressed: _downloadAndInstall,
                        icon: const Icon(Icons.download, color: Colors.white),
                        label: Text(
                          _errorText != null ? 'Reintentar Descarga' : 'Descargar Actualización',
                          style: const TextStyle(
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
                          shadowColor: const Color(0x4DF97316),
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
