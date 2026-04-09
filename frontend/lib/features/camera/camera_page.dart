import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/infer_provider.dart';
import '../feedback/feedback_page.dart';

class CameraPage extends ConsumerWidget {
  const CameraPage({super.key});

  static final _fakeLandmarks = List.generate(
    21,
    (_) => <String, double>{'x': 0.5, 'y': 0.5, 'z': 0.0},
  );

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final inferState = ref.watch(inferProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('F Chord Coach')),
      body: SingleChildScrollView(
        child: Column(
          children: [
            Container(
              height: 300,
              color: Colors.black,
              child: const Center(
                child: Text(
                  '相機預覽（Slice 2 實作）',
                  style: TextStyle(color: Colors.white54),
                ),
              ),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: inferState.isLoading
                  ? null
                  : () =>
                      ref.read(inferProvider.notifier).infer(_fakeLandmarks),
              child: inferState.isLoading
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text('分析（假 landmarks）'),
            ),
            inferState.when(
              data: (result) =>
                  result != null ? FeedbackPage(result: result) : const SizedBox.shrink(),
              loading: () => const Padding(
                padding: EdgeInsets.all(16),
                child: CircularProgressIndicator(),
              ),
              error: (e, _) => Padding(
                padding: const EdgeInsets.all(16),
                child: Text('錯誤：$e',
                    style: const TextStyle(color: Colors.red)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
