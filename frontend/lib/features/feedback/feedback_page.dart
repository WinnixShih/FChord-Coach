import 'package:flutter/material.dart';
import '../../providers/infer_provider.dart';

class FeedbackPage extends StatelessWidget {
  final InferResult result;

  const FeedbackPage({super.key, required this.result});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      margin: const EdgeInsets.all(16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              _errorLabel(result.errorType),
              style: theme.textTheme.titleMedium
                  ?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            LinearProgressIndicator(
              value: result.confidence,
              backgroundColor: Colors.grey[300],
            ),
            Text(
              '信心度：${(result.confidence * 100).toStringAsFixed(0)}%',
              style: theme.textTheme.bodySmall,
            ),
            const SizedBox(height: 12),
            Text(result.suggestion, style: theme.textTheme.bodyMedium),
          ],
        ),
      ),
    );
  }

  String _errorLabel(String errorType) => switch (errorType) {
        'correct' => '手型正確',
        'index_not_barring' => '食指未橫壓',
        'thumb_position' => '拇指位置不對',
        'ring_pinky_curl' => '無名指/小指未彎曲',
        'wrist_angle' => '手腕角度不對',
        _ => errorType,
      };
}
