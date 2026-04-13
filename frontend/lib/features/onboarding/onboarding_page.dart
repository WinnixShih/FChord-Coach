import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../permission/permission_gate.dart';

const _kOnboardingDoneKey = 'onboarding_done';

class OnboardingPage extends StatefulWidget {
  const OnboardingPage({super.key});

  @override
  State<OnboardingPage> createState() => _OnboardingPageState();
}

class _OnboardingPageState extends State<OnboardingPage> {
  final _controller = PageController();
  int _currentPage = 0;

  static const _slides = [
    _Slide(
      icon: Icons.back_hand_outlined,
      title: '擺出 F 和弦',
      body: '用左手在吉他上擺出 F 和弦的指型，\n將手放在前鏡頭前。',
    ),
    _Slide(
      icon: Icons.scatter_plot_outlined,
      title: '即時骨架分析',
      body: 'App 每 2 秒自動拍照分析，\n綠色骨架會疊加在你的手部畫面上。',
    ),
    _Slide(
      icon: Icons.tips_and_updates_outlined,
      title: 'AI 即時建議',
      body: '底部顯示錯誤類型與 AI 文字建議，\n依建議調整指型，直到手型正確。',
    ),
  ];

  Future<void> _finish() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_kOnboardingDoneKey, true);
    if (!mounted) return;
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (_) => const PermissionGate()),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isLast = _currentPage == _slides.length - 1;

    return Scaffold(
      backgroundColor: const Color(0xFFF7F5F1),
      body: SafeArea(
        child: Column(
          children: [
            // 跳過按鈕
            Align(
              alignment: Alignment.topRight,
              child: TextButton(
                onPressed: _finish,
                child: const Text(
                  '跳過',
                  style: TextStyle(color: Color(0xFF6C6C70), fontSize: 14),
                ),
              ),
            ),

            // 說明卡
            Expanded(
              child: PageView.builder(
                controller: _controller,
                itemCount: _slides.length,
                onPageChanged: (i) => setState(() => _currentPage = i),
                itemBuilder: (_, i) => _SlideView(slide: _slides[i]),
              ),
            ),

            // 點點指示器
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(
                _slides.length,
                (i) => AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  margin: const EdgeInsets.symmetric(horizontal: 4),
                  width: _currentPage == i ? 20 : 8,
                  height: 8,
                  decoration: BoxDecoration(
                    color: _currentPage == i
                        ? const Color(0xFF2D6A4F)
                        : const Color(0xFF2D6A4F).withValues(alpha: 0.25),
                    borderRadius: BorderRadius.circular(4),
                  ),
                ),
              ),
            ),

            const SizedBox(height: 32),

            // 按鈕
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 32),
              child: SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: isLast
                      ? _finish
                      : () => _controller.nextPage(
                            duration: const Duration(milliseconds: 300),
                            curve: Curves.easeOut,
                          ),
                  style: FilledButton.styleFrom(
                    backgroundColor: const Color(0xFF2D6A4F),
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                  ),
                  child: Text(
                    isLast ? '開始練習' : '下一步',
                    style: const TextStyle(fontSize: 16),
                  ),
                ),
              ),
            ),

            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }
}

class _SlideView extends StatelessWidget {
  final _Slide slide;
  const _SlideView({required this.slide});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 40),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(slide.icon, size: 80, color: const Color(0xFF2D6A4F)),
          const SizedBox(height: 32),
          Text(
            slide.title,
            style: const TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.w600,
              color: Color(0xFF1C1C1E),
            ),
          ),
          const SizedBox(height: 16),
          Text(
            slide.body,
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 15,
              color: Color(0xFF6C6C70),
              height: 1.7,
            ),
          ),
        ],
      ),
    );
  }
}

class _Slide {
  final IconData icon;
  final String title;
  final String body;
  const _Slide({required this.icon, required this.title, required this.body});
}

/// 啟動時檢查是否已看過 onboarding，回傳對應的首頁 widget。
Future<Widget> resolveHomePage() async {
  final prefs = await SharedPreferences.getInstance();
  final done = prefs.getBool(_kOnboardingDoneKey) ?? false;
  return done ? const PermissionGate() : const OnboardingPage();
}
