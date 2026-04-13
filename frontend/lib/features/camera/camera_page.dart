import 'dart:async';
import 'dart:io';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path_provider/path_provider.dart';

import '../../providers/infer_provider.dart';
import '../../services/mediapipe_channel.dart';
import '../../shared/painters/hand_skeleton_painter.dart';
import '../feedback/feedback_page.dart';

class CameraPage extends ConsumerStatefulWidget {
  const CameraPage({super.key});

  @override
  ConsumerState<CameraPage> createState() => _CameraPageState();
}

class _CameraPageState extends ConsumerState<CameraPage>
    with WidgetsBindingObserver {
  CameraController? _controller;
  bool _isInitialized = false;
  bool _isAnalyzing = false;
  Timer? _analysisTimer;
  List<Map<String, double>>? _lastLandmarks;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _initCamera();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _analysisTimer?.cancel();
    _controller?.dispose();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (_controller == null || !_controller!.value.isInitialized) return;
    if (state == AppLifecycleState.inactive) {
      _analysisTimer?.cancel();
      _controller?.dispose();
    } else if (state == AppLifecycleState.resumed) {
      _initCamera();
    }
  }

  Future<void> _initCamera() async {
    final cameras = await availableCameras();
    if (cameras.isEmpty) return;

    // 優先使用前鏡頭（方便使用者看自己的手勢）
    final camera = cameras.firstWhere(
      (c) => c.lensDirection == CameraLensDirection.front,
      orElse: () => cameras.first,
    );

    _controller = CameraController(
      camera,
      ResolutionPreset.medium,
      enableAudio: false,
    );

    try {
      await _controller!.initialize();
      if (!mounted) return;
      setState(() => _isInitialized = true);
      _startAnalysisTimer();
    } on CameraException {
      // 相機初始化失敗（e.g. 權限未授予）
    }
  }

  void _startAnalysisTimer() {
    // 每 2 秒分析一幀：配合 VLM rate limit（2 calls/min）
    _analysisTimer = Timer.periodic(const Duration(seconds: 2), (_) {
      _analyzeCurrentFrame();
    });
  }

  Future<void> _analyzeCurrentFrame() async {
    if (_isAnalyzing || _controller == null || !_controller!.value.isInitialized) {
      return;
    }
    _isAnalyzing = true;

    try {
      // 1. 拍一張靜態照片存到暫存目錄
      final tmpDir = await getTemporaryDirectory();
      final path = '${tmpDir.path}/fchord_frame.jpg';
      final xFile = await _controller!.takePicture();
      await File(xFile.path).copy(path);

      // 2. 透過 MethodChannel 讓 Kotlin 跑 MediaPipe 偵測
      final landmarks = await MediaPipeChannel.detectFromPath(path);
      if (landmarks == null || landmarks.length != 21) {
        _isAnalyzing = false;
        return;
      }

      // 3. 儲存 landmarks 供骨架 overlay 使用（BL-004）
      if (mounted) setState(() => _lastLandmarks = landmarks);

      // 4. 送到後端 /infer
      await ref.read(inferProvider.notifier).infer(landmarks);
    } finally {
      _isAnalyzing = false;
    }
  }

  @override
  Widget build(BuildContext context) {
    final inferState = ref.watch(inferProvider);

    return Scaffold(
      backgroundColor: const Color(0xFF1C1C1E),
      body: Stack(
        children: [
          // ── 相機畫面（佔約 65% 螢幕高度）+ 骨架 Overlay ──
          Positioned.fill(
            child: Column(
              children: [
                Expanded(
                  flex: 65,
                  child: Stack(
                    fit: StackFit.expand,
                    children: [
                      _isInitialized
                          ? CameraPreview(_controller!)
                          : const Center(
                              child: CircularProgressIndicator(
                                color: Color(0xFF52B788),
                              ),
                            ),
                      if (_lastLandmarks != null)
                        CustomPaint(
                          painter: HandSkeletonPainter(
                            landmarks: _lastLandmarks!,
                            errorType: inferState.valueOrNull?.errorType,
                          ),
                        ),
                    ],
                  ),
                ),
                // 底部空間留給 Bottom Sheet
                const Flexible(flex: 35, child: SizedBox()),
              ],
            ),
          ),

          // ── 底部 Bottom Sheet 風格反饋區 ──
          Align(
            alignment: Alignment.bottomCenter,
            child: _FeedbackBottomSheet(inferState: inferState),
          ),
        ],
      ),
    );
  }
}

class _FeedbackBottomSheet extends StatelessWidget {
  const _FeedbackBottomSheet({required this.inferState});

  final AsyncValue<dynamic> inferState;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
      decoration: BoxDecoration(
        color: const Color(0xF2F7F5F1), // 暖奶油白，略透明
        borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.12),
            blurRadius: 24,
            offset: const Offset(0, -4),
          ),
        ],
      ),
      child: inferState.when(
        data: (result) {
          if (result == null) {
            return const _WaitingHint();
          }
          return FeedbackPage(result: result);
        },
        loading: () => const Center(
          child: Padding(
            padding: EdgeInsets.symmetric(vertical: 24),
            child: CircularProgressIndicator(color: Color(0xFF2D6A4F)),
          ),
        ),
        error: (e, _) => Padding(
          padding: const EdgeInsets.symmetric(vertical: 16),
          child: Text(
            '分析失敗：$e',
            style: const TextStyle(color: Color(0xFFE07A2F), fontSize: 14),
          ),
        ),
      ),
    );
  }
}

class _WaitingHint extends StatelessWidget {
  const _WaitingHint();

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.symmetric(vertical: 20),
      child: Text(
        '將手放在鏡頭前，系統每 2 秒自動分析一次',
        textAlign: TextAlign.center,
        style: TextStyle(
          color: Color(0xFF6C6C70),
          fontSize: 14,
        ),
      ),
    );
  }
}
