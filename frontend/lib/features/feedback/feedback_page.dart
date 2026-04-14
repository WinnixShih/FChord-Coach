import 'package:flutter/material.dart';
import '../../providers/infer_provider.dart';
import '../../shared/theme/app_colors.dart';
import '../../shared/widgets/confidence_bar.dart';
import '../../shared/widgets/status_chip.dart';

class FeedbackPage extends StatelessWidget {
  final InferResult result;

  const FeedbackPage({super.key, required this.result});

  @override
  Widget build(BuildContext context) {
    final isCorrect = result.errorType == 'correct';
    final label = _errorLabel(result.errorType);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        // Chip
        isCorrect
            ? StatusChip.correct(label: label)
            : StatusChip.error(label: label),

        const SizedBox(height: 16),

        // ConfidenceBar
        ConfidenceBar(value: result.confidence, isError: !isCorrect),

        const SizedBox(height: 16),

        // AI 建議
        const Text(
          'AI 建議',
          style: TextStyle(
            fontSize: 11,
            color: AppColors.textMuted,
            fontWeight: FontWeight.w400,
          ),
        ),
        const SizedBox(height: 6),
        Text(
          result.suggestion,
          style: const TextStyle(
            fontSize: 14,
            color: AppColors.textPrimary,
            height: 1.6,
          ),
        ),
      ],
    );
  }

  String _errorLabel(String errorType) => switch (errorType) {
        'correct' => '手型正確 ✓',
        'index_not_barring' => '食指未橫壓',
        'thumb_position' => '拇指位置不對',
        'ring_pinky_curl' => '無名指／小指未彎曲',
        'wrist_angle' => '手腕角度不對',
        _ => errorType,
      };
}
