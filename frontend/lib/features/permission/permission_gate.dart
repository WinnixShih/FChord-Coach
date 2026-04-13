import 'package:flutter/material.dart';
import 'package:permission_handler/permission_handler.dart';

import '../camera/camera_page.dart';

/// 相機權限守門員。
/// - granted → 直接顯示 CameraPage
/// - 未詢問 / denied → 說明畫面 + 請求按鈕
/// - permanentlyDenied → 引導至系統設定
class PermissionGate extends StatefulWidget {
  const PermissionGate({super.key});

  @override
  State<PermissionGate> createState() => _PermissionGateState();
}

class _PermissionGateState extends State<PermissionGate>
    with WidgetsBindingObserver {
  _PermissionStatus _status = _PermissionStatus.loading;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _checkPermission();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  // 從系統設定返回時重新檢查（使用者可能在設定裡開了權限）
  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) _checkPermission();
  }

  Future<void> _checkPermission() async {
    final status = await Permission.camera.status;
    if (!mounted) return;
    setState(() => _status = _toStatus(status));
  }

  Future<void> _requestPermission() async {
    final status = await Permission.camera.request();
    if (!mounted) return;
    setState(() => _status = _toStatus(status));
  }

  _PermissionStatus _toStatus(PermissionStatus s) {
    if (s.isGranted) return _PermissionStatus.granted;
    if (s.isPermanentlyDenied) return _PermissionStatus.permanentlyDenied;
    return _PermissionStatus.denied;
  }

  @override
  Widget build(BuildContext context) {
    if (_status == _PermissionStatus.granted) {
      return const CameraPage();
    }
    return Scaffold(
      backgroundColor: const Color(0xFFF7F5F1),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(
                Icons.camera_alt_outlined,
                size: 64,
                color: Color(0xFF2D6A4F),
              ),
              const SizedBox(height: 24),
              const Text(
                '需要相機權限',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w600,
                  color: Color(0xFF1C1C1E),
                ),
              ),
              const SizedBox(height: 12),
              Text(
                _status == _PermissionStatus.permanentlyDenied
                    ? '相機權限已被拒絕。\n請前往系統設定，手動開啟相機存取權限。'
                    : 'FChord Coach 需要相機來即時分析你的手部姿勢，幫助你矯正 F 和弦指型。',
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 14,
                  color: Color(0xFF6C6C70),
                  height: 1.6,
                ),
              ),
              const SizedBox(height: 32),
              if (_status == _PermissionStatus.loading)
                const CircularProgressIndicator(color: Color(0xFF2D6A4F))
              else
                SizedBox(
                  width: double.infinity,
                  child: FilledButton(
                    onPressed: _status == _PermissionStatus.permanentlyDenied
                        ? openAppSettings
                        : _requestPermission,
                    style: FilledButton.styleFrom(
                      backgroundColor: const Color(0xFF2D6A4F),
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14),
                      ),
                    ),
                    child: Text(
                      _status == _PermissionStatus.permanentlyDenied
                          ? '前往系統設定'
                          : '允許使用相機',
                      style: const TextStyle(fontSize: 16),
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

enum _PermissionStatus { loading, granted, denied, permanentlyDenied }
