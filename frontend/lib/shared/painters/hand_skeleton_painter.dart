import 'package:flutter/material.dart';

/// 在相機畫面上繪製 21 個 MediaPipe 手部關節的骨架 overlay。
///
/// 設計規範（DESIGN.md）：
/// - 正常節點 / 連線：#52B788，opacity 0.85，strokeWidth 1.5dp
/// - 掌心橫向連線：虛線，opacity 0.5
/// - 錯誤關節：額外畫 #E07A2F 圓圈，radius 5dp，strokeWidth 1.5dp
class HandSkeletonPainter extends CustomPainter {
  final List<Map<String, double>> landmarks;
  final String? errorType;

  const HandSkeletonPainter({required this.landmarks, this.errorType});

  // 手指段連線（不含掌心橫線）
  static const _fingerConnections = [
    [0, 1], [1, 2], [2, 3], [3, 4],   // 拇指
    [0, 5], [5, 6], [6, 7], [7, 8],   // 食指
    [0, 9], [9, 10], [10, 11], [11, 12], // 中指
    [0, 13], [13, 14], [14, 15], [15, 16], // 無名指
    [0, 17], [17, 18], [18, 19], [19, 20], // 小指
  ];

  // 掌心橫向連線（虛線）
  static const _palmConnections = [
    [5, 9], [9, 13], [13, 17],
  ];

  // error_type → 需高亮的關節 index
  static const _errorJoints = <String, Set<int>>{
    'index_not_barring': {5, 6, 7, 8},
    'thumb_position': {1, 2, 3, 4},
    'ring_pinky_curl': {13, 14, 15, 16, 17, 18, 19, 20},
    'wrist_angle': {0},
  };

  static const _skeletonColor = Color(0xFF52B788);
  static const _errorColor = Color(0xFFE07A2F);

  @override
  void paint(Canvas canvas, Size size) {
    if (landmarks.length != 21) return;

    final linePaint = Paint()
      ..color = _skeletonColor.withValues(alpha: 0.85)
      ..strokeWidth = 1.5
      ..style = PaintingStyle.stroke;

    final palmPaint = Paint()
      ..color = _skeletonColor.withValues(alpha: 0.5)
      ..strokeWidth = 1.5
      ..style = PaintingStyle.stroke;

    final dotPaint = Paint()
      ..color = _skeletonColor
      ..style = PaintingStyle.fill;

    final errorRingPaint = Paint()
      ..color = _errorColor
      ..strokeWidth = 1.5
      ..style = PaintingStyle.stroke;

    final errorJoints = _errorJoints[errorType] ?? const <int>{};

    // 手指連線
    for (final conn in _fingerConnections) {
      canvas.drawLine(
        _toOffset(landmarks[conn[0]], size),
        _toOffset(landmarks[conn[1]], size),
        linePaint,
      );
    }

    // 掌心橫向連線（虛線）
    for (final conn in _palmConnections) {
      _drawDashedLine(
        canvas,
        _toOffset(landmarks[conn[0]], size),
        _toOffset(landmarks[conn[1]], size),
        palmPaint,
      );
    }

    // 關節點 + 錯誤高亮圈
    for (var i = 0; i < 21; i++) {
      final pos = _toOffset(landmarks[i], size);
      canvas.drawCircle(pos, 3, dotPaint);
      if (errorJoints.contains(i)) {
        canvas.drawCircle(pos, 5, errorRingPaint);
      }
    }
  }

  Offset _toOffset(Map<String, double> lm, Size size) =>
      Offset((lm['x'] ?? 0) * size.width, (lm['y'] ?? 0) * size.height);

  void _drawDashedLine(Canvas canvas, Offset p1, Offset p2, Paint paint) {
    const dashLen = 6.0;
    const gapLen = 4.0;

    final dist = (p2 - p1).distance;
    if (dist == 0) return;

    final dx = (p2.dx - p1.dx) / dist;
    final dy = (p2.dy - p1.dy) / dist;
    var traveled = 0.0;
    var drawing = true;

    while (traveled < dist) {
      final segEnd = (traveled + (drawing ? dashLen : gapLen)).clamp(0.0, dist);
      if (drawing) {
        canvas.drawLine(
          Offset(p1.dx + dx * traveled, p1.dy + dy * traveled),
          Offset(p1.dx + dx * segEnd, p1.dy + dy * segEnd),
          paint,
        );
      }
      traveled = segEnd;
      drawing = !drawing;
    }
  }

  @override
  bool shouldRepaint(HandSkeletonPainter old) =>
      old.landmarks != landmarks || old.errorType != errorType;
}
