import 'package:flutter/material.dart';
import '../theme/app_colors.dart';

class ConfidenceBar extends StatelessWidget {
  final double value; // 0.0 ~ 1.0
  final bool isError;

  const ConfidenceBar({super.key, required this.value, required this.isError});

  @override
  Widget build(BuildContext context) {
    final color = isError ? AppColors.error : AppColors.accent;
    final percent = (value * 100).toStringAsFixed(0);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Text(
              '信心度',
              style: TextStyle(
                fontSize: 11,
                color: AppColors.textMuted,
                fontWeight: FontWeight.w400,
              ),
            ),
            const Spacer(),
            Text(
              '$percent%',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w500,
                color: color,
                fontFeatures: const [FontFeature.tabularFigures()],
              ),
            ),
          ],
        ),
        const SizedBox(height: 6),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: value,
            minHeight: 6,
            backgroundColor: color.withValues(alpha: 0.15),
            valueColor: AlwaysStoppedAnimation(color),
          ),
        ),
      ],
    );
  }
}
