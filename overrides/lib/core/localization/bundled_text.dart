import 'package:easy_localization/easy_localization.dart';

import 'bundled_zh.g.dart';

/// Exact-match display translation for factory-bundled text only.
/// Unknown text is returned verbatim. This never rewrites storage or requests.
String bundledTextInLanguage(String source, String language) =>
    language == 'zh' ? (bundledChineseText[source] ?? source) : source;

String bundledText(String source) => bundledTextInLanguage(
  source,
  'glaze_bundled_locale'.tr(),
);

/// A controller may show a Chinese rendering while its working item retains
/// the original prompt. Only a real text edit should replace that original.
String preserveUneditedBundledText(
  String original,
  String displayed,
  String edited,
) => edited == displayed ? original : edited;
