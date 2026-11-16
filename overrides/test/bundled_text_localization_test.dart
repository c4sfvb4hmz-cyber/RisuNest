import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:glaze_flutter/core/localization/bundled_text.dart';
import 'package:glaze_flutter/shared/widgets/generic_editor.dart';

class _TestLoader extends AssetLoader {
  const _TestLoader();
  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async => {
    'glaze_bundled_locale': locale.languageCode,
  };
}

void main() {
  const original =
      "Write {{char}}'s next reply in a fictional chat between {{char}} and {{user}}.";
  const chinese = '在 {{char}} 与 {{user}} 的虚构对话中，撰写 {{char}} 的下一条回复。';

  test('factory text is translated only in Chinese', () {
    expect(bundledTextInLanguage(original, 'zh'), chinese);
    expect(bundledTextInLanguage(original, 'en'), original);
    expect(bundledTextInLanguage(original, 'ru'), original);
    expect(bundledTextInLanguage('my custom prompt {{user}}', 'zh'),
        'my custom prompt {{user}}');
  });

  test('display translation does not replace an unedited original', () {
    expect(preserveUneditedBundledText(original, chinese, chinese), original);
    expect(preserveUneditedBundledText(original, chinese, '用户明确修改的内容'),
        '用户明确修改的内容');
  });

  testWidgets('preset editor shows Chinese but saves original unedited body',
      (tester) async {
    SharedPreferences.setMockInitialValues({});
    await EasyLocalization.ensureInitialized();
    Map<String, dynamic>? changed;
    late BuildContext localeContext;
    await tester.pumpWidget(ProviderScope(
      child: EasyLocalization(
        supportedLocales: const [Locale('zh'), Locale('en')],
        startLocale: const Locale('zh'),
        fallbackLocale: const Locale('en'),
        path: 'test-assets',
        assetLoader: const _TestLoader(),
        saveLocale: false,
        child: Builder(builder: (context) {
          localeContext = context;
          return MaterialApp(
            locale: context.locale,
            localizationsDelegates: context.localizationDelegates,
            supportedLocales: context.supportedLocales,
            home: Scaffold(
              body: GenericEditor(
                localizeBundledText: true,
                item: const {'name': 'Main Prompt', 'content': original},
                config: const [
                  GenericEditorSection(fields: [
                    GenericEditorField(key: 'name', label: '名称'),
                    GenericEditorField(
                      key: 'content', label: '内容', type: 'textarea', rows: 3),
                  ]),
                ],
                onChanged: (value) => changed = Map.from(value),
              ),
            ),
          );
        }),
      ),
    ));
    await tester.pumpAndSettle();
    expect(find.text('主提示词'), findsOneWidget);
    expect(find.text(chinese), findsOneWidget);
    expect(changed, isNull);

    await tester.enterText(find.byType(TextField).first, '我编辑的名称');
    expect(changed?['content'], original);
    expect(changed?['name'], '我编辑的名称');

    await localeContext.setLocale(const Locale('en'));
    await tester.pumpAndSettle();
    expect(find.text(original), findsOneWidget);
    expect(changed?['content'], original);
    expect(tester.takeException(), isNull);
  });
}
