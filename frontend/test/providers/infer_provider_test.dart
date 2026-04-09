import 'package:flutter_test/flutter_test.dart';
import 'package:fchord_coach/providers/infer_provider.dart';

void main() {
  group('InferResult.fromJson', () {
    test('parses all fields correctly', () {
      final result = InferResult.fromJson({
        'error_type': 'index_not_barring',
        'confidence': 0.91,
        'suggestion': '食指壓平！',
      });
      expect(result.errorType, 'index_not_barring');
      expect(result.confidence, closeTo(0.91, 1e-6));
      expect(result.suggestion, '食指壓平！');
    });

    test('handles integer confidence', () {
      final result = InferResult.fromJson({
        'error_type': 'correct',
        'confidence': 1,
        'suggestion': '很棒！',
      });
      expect(result.confidence, 1.0);
    });
  });
}
