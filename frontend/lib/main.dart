import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'features/camera/camera_page.dart';

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
      home: const CameraPage(),
    );
  }
}
