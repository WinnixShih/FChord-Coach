import 'package:flutter/services.dart';

class MediaPipeChannel {
  static const _channel = MethodChannel('fchord/mediapipe');

  /// 傳入 JPEG 圖片路徑，回傳 21 個手部關節座標（正規化 0~1）。
  /// 偵測不到手或發生錯誤時回傳 null。
  static Future<List<Map<String, double>>?> detectFromPath(
      String imagePath) async {
    try {
      final result = await _channel.invokeMethod<List<dynamic>>(
        'detect',
        {'path': imagePath},
      );
      if (result == null) return null;

      return result.map((e) {
        final m = Map<String, dynamic>.from(e as Map);
        return {
          'x': (m['x'] as num).toDouble(),
          'y': (m['y'] as num).toDouble(),
          'z': (m['z'] as num).toDouble(),
        };
      }).toList();
    } on PlatformException {
      return null;
    }
  }
}
