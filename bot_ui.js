// Interface language is independent of learning and explanation languages.
export const UI_LANGUAGES = new Set(['ar', 'en']);
export const INTERVALS = [30, 60, 120, 180, 360, 720, 1440];
const copy = {
  ar: {
    welcome: '🎬 اتعلّم تعبيرات حقيقية من مشاهد الأفلام، بالوتيرة المناسبة ليك.\n\n/start — إعداد الاشتراك\n/language — لغة البوت\n/learn — لغة التعلّم\n/level — المستوى\n/explain — لغة الشرح\n/interval — مواعيد الرسائل\n/today — آخر تعبير\n/stop — إيقاف الاشتراك',
    setup_ui: 'أهلاً بيك 🎬\nاتعلّم لغة من مشهد، خطوة بخطوة.\n\nاختار لغة البوت أولاً — دي لغة القوائم، مش اللغة اللي هتتعلمها.\nChoose your bot language to get started.',
    setup_learn: '١ من ٤ · لغة التعلّم 🌍\nاختار اللغة اللي حابب تتعلم تعبيراتها من الأفلام:',
    setup_level: '٢ من ٤ · مستواك 📚\nاختار المستوى الأقرب ليك. تقدر تغيّره بعدين:',
    setup_explain: '٣ من ٤ · لغة الشرح 💬\nتحب نشرح لك معنى التعبيرات بأي لغة؟',
    setup_interval: '٤ من ٤ · مواعيد الرسائل ⏰\nتحب يوصلك تعبير ومشهد كل قد إيه؟\nاختار من الأزرار: من نص ساعة لحد ٢٤ ساعة.',
    review: 'كل حاجة جاهزة؟ 🎬\n\n🌍 لغة التعلّم: {learn}\n📚 المستوى: {level}\n💬 لغة الشرح: {explain}\n⏰ رسالة كل {interval}\n\nراجع اختياراتك، وبعدها أكّد الاشتراك. الإرسال مش هيبدأ قبل التأكيد.',
    back: 'الخطوة اللي قبلها ↩️', confirm: 'تأكيد الاشتراك ✅', restart: 'اختيار من الأول ↩️',
    done_halfhour: 'اشتراكك جاهز ✅\nالرسائل هتكون مستحقة على رأس الساعة وعند الدقيقة ٣٠. أول استحقاق عند أقرب موعد قادم.\nالوصول ممكن يتأخر حسب الكرون وتجهيز المشهد.\n\nلتعديل اختياراتك: /help',
    saved_interval_halfhour: 'تم الحفظ ✅\nالرسائل مستحقة على رأس الساعة وعند الدقيقة ٣٠، بدايةً من أقرب موعد قادم. الوصول ممكن يتأخر حسب التشغيل والتجهيز.',
    done: 'اشتراكك جاهز ✅\nأول رسالة هتكون مستحقة بعد {interval}. وصولها ممكن يتأخر حسب تجهيز المشهد.\n\nلتعديل اختياراتك: /help',
    missing: 'الاختيار ده انتهى أو اشتراكك متوقف. ابدأ من /start 🎬',
    invalid: 'الاختيار غير صالح. استخدم الأزرار الظاهرة.',
    subscribe: 'خلّينا نجهّز اشتراكك الأول 🎬\nاضغط /start',
    learn: '🌍 اختار لغة التعلّم الجديدة:', explain: '💬 اختار لغة الشرح الجديدة:',
    interval: '⏰ اختار الوقت بين الرسائل من الأزرار.\nأقل مدة نص ساعة، وأقصى مدة ٢٤ ساعة.',
    level: '📚 مستواك الحالي: {level}\nاختار المستوى الجديد:',
    saved_level: 'تم حفظ مستواك: {value} ✅', saved_learn: 'تم حفظ لغة التعلّم: {value} ✅',
    saved_explain: 'تم حفظ لغة الشرح: {value} ✅', saved_interval: 'تم الحفظ ✅\nرسالة كل {value}.',
    saved_ui: 'تم تغيير لغة البوت للعربية ✅', choose_ui: 'اختار لغة القوائم والرسائل:',
    stopped: 'تم إيقاف اشتراكك 🌿\nلما تحب ترجع، اضغط /start.',
    today: '🎬 آخر تعبير لمستوى {level}\n\n{phrase}\n\n🎞 من: {title}',
    empty: 'لسه مفيش تعبير متاح لمستوى {level} باللغة المختارة. جرّب تاني بعدين ⏳',
    buttons: 'اختار من الأزرار 👇 مش محتاج تكتب عدد الدقايق.',
    unknown: 'محتاج مساعدة؟ اضغط /help للقائمة، أو /start لإعداد اشتراكك.',
    levels: ['A2 · أساسي', 'B1 · متوسط', 'B2 · فوق المتوسط', 'C1 · متقدم', 'C2 · متمكن'],
    intervals: ['نص ساعة', 'ساعة', 'ساعتين', '٣ ساعات', '٦ ساعات', '١٢ ساعة', '٢٤ ساعة'],
  },
  en: {
    welcome: '🎬 Learn real expressions from movie scenes, at your own pace.\n\n/start — Set up your subscription\n/language — Bot language\n/learn — Learning language\n/level — Level\n/explain — Explanation language\n/interval — Message frequency\n/today — Latest expression\n/stop — Pause subscription',
    setup_ui: 'Welcome 🎬\nLearn a language, one scene at a time.\n\nChoose the bot language first. This controls menus, not the language you will learn.\nاختار لغة البوت للبدء.',
    setup_learn: '1 of 4 · Learning language 🌍\nWhich language would you like to learn through movie expressions?',
    setup_level: '2 of 4 · Your level 📚\nChoose the closest match. You can change it later:',
    setup_explain: '3 of 4 · Explanation language 💬\nWhich language should we use to explain expressions?',
    setup_interval: '4 of 4 · Message frequency ⏰\nHow often would you like an expression and a scene?\nChoose a button: from 30 minutes to 24 hours.',
    review: 'Ready to begin? 🎬\n\n🌍 Learning language: {learn}\n📚 Level: {level}\n💬 Explanation language: {explain}\n⏰ One message every {interval}\n\nReview your choices, then confirm. Delivery will not start until you confirm.',
    back: 'Previous step ↩️', confirm: 'Confirm subscription ✅', restart: 'Choose again ↩️',
    done_halfhour: 'You’re all set ✅\nMessages are due at :00 and :30, starting at the next clock slot.\nDelivery may be delayed by the scheduler and scene preparation.\n\nTo change settings: /help',
    saved_interval_halfhour: 'Saved ✅\nMessages are due at :00 and :30, starting at the next clock slot. Actual delivery may be delayed.',
    done: 'You’re all set ✅\nYour first message will be due in {interval}. Delivery may take longer while we prepare a scene.\n\nTo change your settings: /help',
    missing: 'This selection has expired or your subscription is paused. Start with /start 🎬',
    invalid: 'Invalid selection. Please use the buttons shown.',
    subscribe: 'Let’s set up your subscription first 🎬\nTap /start',
    learn: '🌍 Choose your new learning language:', explain: '💬 Choose your new explanation language:',
    interval: '⏰ Choose the time between messages using the buttons.\nFrom 30 minutes to 24 hours.',
    level: '📚 Current level: {level}\nChoose a new level:',
    saved_level: 'Level saved: {value} ✅', saved_learn: 'Learning language saved: {value} ✅',
    saved_explain: 'Explanation language saved: {value} ✅', saved_interval: 'Saved ✅\nOne message every {value}.',
    saved_ui: 'Bot language changed to English ✅', choose_ui: 'Choose the language for menus and bot messages:',
    stopped: 'Your subscription is paused 🌿\nWhen you’re ready, tap /start to return.',
    today: '🎬 Latest expression for {level}\n\n{phrase}\n\n🎞 From: {title}',
    empty: 'No expression is available for {level} in your chosen language yet. Try again later ⏳',
    buttons: 'Please choose a button below 👇 No need to type a number of minutes.',
    unknown: 'Need a hand? Tap /help for the menu, or /start to set up your subscription.',
    levels: ['A2 · Elementary', 'B1 · Intermediate', 'B2 · Upper intermediate', 'C1 · Advanced', 'C2 · Proficient'],
    intervals: ['30 minutes', '1 hour', '2 hours', '3 hours', '6 hours', '12 hours', '24 hours'],
  },
};
export function text(lang, key, values = {}) {
  return copy[lang === 'en' ? 'en' : 'ar'][key].replace(/\{(\w+)\}/g, (_, name) => values[name] ?? '—');
}
export function intervalLabel(minutes, lang) {
  const index = INTERVALS.indexOf(Number(minutes));
  if (index !== -1) return copy[lang === 'en' ? 'en' : 'ar'].intervals[index];
  // Existing custom preferences remain readable until the user chooses a preset.
  return `${minutes} ${lang === 'en' ? 'minutes' : 'دقيقة'}`;
}
export const validInterval = value => INTERVALS.some(minutes => String(minutes) === value);
export const uiKeyboard = (kind = 'ui') => ({ inline_keyboard: [[
  { text: 'العربية', callback_data: `${kind}:ar` }, { text: 'English', callback_data: `${kind}:en` },
]] });
export const levelKeyboard = (kind, lang) => ({ inline_keyboard: ['A2', 'B1', 'B2', 'C1', 'C2'].map((level, i) => [
  { text: copy[lang === 'en' ? 'en' : 'ar'].levels[i], callback_data: `${kind}:${level}` },
]) });
export const intervalKeyboard = (kind, lang) => ({ inline_keyboard: INTERVALS.map(minutes => [
  { text: intervalLabel(minutes, lang), callback_data: `${kind}:${minutes}` },
]) });
