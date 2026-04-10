import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fchord_coach/main.dart';

void main() {
  testWidgets('App smoke test — renders without crash', (WidgetTester tester) async {
    await tester.pumpWidget(const ProviderScope(child: FChordCoachApp()));
    expect(find.byType(ProviderScope), findsOneWidget);
  });
}
