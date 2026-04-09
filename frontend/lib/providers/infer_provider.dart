import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../shared/api_client.dart';

class InferResult {
  final String errorType;
  final double confidence;
  final String suggestion;

  const InferResult({
    required this.errorType,
    required this.confidence,
    required this.suggestion,
  });

  factory InferResult.fromJson(Map<String, dynamic> json) => InferResult(
        errorType: json['error_type'] as String,
        confidence: (json['confidence'] as num).toDouble(),
        suggestion: json['suggestion'] as String,
      );
}

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());

class InferNotifier extends AsyncNotifier<InferResult?> {
  @override
  Future<InferResult?> build() async => null;

  Future<void> infer(List<Map<String, double>> landmarks) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() async {
      final json = await ref.read(apiClientProvider).infer(landmarks);
      return InferResult.fromJson(json);
    });
  }
}

final inferProvider = AsyncNotifierProvider<InferNotifier, InferResult?>(
  InferNotifier.new,
);
