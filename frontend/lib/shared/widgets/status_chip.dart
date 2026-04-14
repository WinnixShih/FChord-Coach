import 'package:flutter/material.dart';
import '../theme/app_colors.dart';

class StatusChip extends StatelessWidget {
  final String label;
  final bool isError;

  const StatusChip.correct({super.key, required this.label}) : isError = false;
  const StatusChip.error({super.key, required this.label}) : isError = true;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
      decoration: BoxDecoration(
        color: isError ? AppColors.errorBg : AppColors.accentBg,
        borderRadius: BorderRadius.circular(100),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 13,
          fontWeight: FontWeight.w500,
          color: isError ? AppColors.error : AppColors.accent,
        ),
      ),
    );
  }
}
