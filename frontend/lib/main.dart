import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'features/onboarding/onboarding_page.dart';

void main() {
  runApp(const ProviderScope(child: FChordCoachApp()));
}

class FChordCoachApp extends StatelessWidget {
  const FChordCoachApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'F Chord Coach',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      home: FutureBuilder<Widget>(
        future: resolveHomePage(),
        builder: (context, snapshot) {
          if (!snapshot.hasData) {
            return const Scaffold(
              backgroundColor: Color(0xFFF7F5F1),
            );
          }
          return snapshot.data!;
        },
      ),
    );
  }
}
