-- Add currency category to practical_info_categories
INSERT INTO practical_info_categories (
    id,
    name,
    description,
    icon,
    created_at,
    updated_at
) VALUES (
    'currency',
    '{"en": "Currency & Money", "ar": "العملة والمال"}',
    '{"en": "Information about Egyptian currency, exchange rates, and money matters", "ar": "معلومات عن العملة المصرية وأسعار الصرف والأمور المالية"}',
    'money-bill-wave',
    NOW(),
    NOW()
);

-- Insert practical info for currency
INSERT INTO practical_info (
    category_id,
    title,
    content,
    related_destination_ids,
    tags,
    is_featured
) VALUES (
    'currency',
    '{"en": "Currency Information for Egypt", "ar": "معلومات العملة في مصر"}',
    '{"en": "# Currency Information for Egypt\n\nThe official currency of Egypt is the Egyptian Pound (EGP), often abbreviated as LE or E£.\n\n## Egyptian Pound Basics\n- **Symbol**: £E or ج.م\n- **Code**: EGP\n- **Denominations**: \n  - **Coins**: 25 pt, 50 pt, 1 LE\n  - **Notes**: 5, 10, 20, 50, 100, 200 LE\n\n## Currency Exchange\n- **Best places to exchange**: Banks, official exchange offices, and some hotels\n- **Airports**: Exchange services available but rates are typically less favorable\n- **Documentation**: Bring your passport when exchanging currency\n- **Receipts**: Keep exchange receipts if you plan to convert back to your currency when leaving\n\n## ATMs and Banking\n- **ATM availability**: Widely available in cities and tourist areas\n- **Withdrawal limits**: Typically 2,000-3,000 LE per transaction\n- **Bank cards**: Visa and Mastercard are widely accepted\n- **Fees**: Check with your bank about foreign transaction fees\n- **Banking hours**: Sunday to Thursday, 8:30 AM to 2:00 PM\n\n## Credit Cards\n- **Acceptance**: Major hotels, restaurants, and shops in tourist areas accept credit cards\n- **Local markets**: Small shops and markets typically only accept cash\n- **Notify your bank**: Inform your bank of your travel plans to prevent card blocks\n\n## Tipping (Baksheesh)\n- **Restaurants**: 10-15% if service charge is not included\n- **Hotel staff**: 5-10 LE for porters, 10-20 LE per day for housekeeping\n- **Tour guides**: 50-100 LE per day depending on group size\n- **Taxi drivers**: Rounding up the fare is sufficient\n\n## Money-Saving Tips\n- **Compare rates**: Check multiple exchange offices for the best rates\n- **Avoid street exchangers**: Stick to official establishments\n- **Small denominations**: Keep small bills handy for taxis, tips, and small purchases\n- **Bargaining**: Expected in markets and with taxis, but not in established stores\n\n## Current Exchange Rates\n*As of May 2025:*\n- 1 USD ≈ 48 EGP\n- 1 EUR ≈ 52 EGP\n- 1 GBP ≈ 61 EGP\n\nExchange rates fluctuate, so check current rates before your trip.", "ar": "# معلومات العملة في مصر\n\nالعملة الرسمية في مصر هي الجنيه المصري (EGP)، ويختصر غالبًا بـ LE أو E£.\n\n## أساسيات الجنيه المصري\n- **الرمز**: £E أو ج.م\n- **الرمز الدولي**: EGP\n- **الفئات**: \n  - **العملات المعدنية**: 25 قرش، 50 قرش، 1 جنيه\n  - **الأوراق النقدية**: 5، 10، 20، 50، 100، 200 جنيه\n\n## صرف العملات\n- **أفضل الأماكن للصرف**: البنوك، مكاتب الصرافة الرسمية، وبعض الفنادق\n- **المطارات**: خدمات الصرافة متوفرة ولكن الأسعار عادة أقل تفضيلاً\n- **الوثائق**: أحضر جواز سفرك عند صرف العملات\n- **الإيصالات**: احتفظ بإيصالات الصرف إذا كنت تخطط لتحويل الأموال مرة أخرى إلى عملتك عند المغادرة\n\n## أجهزة الصراف الآلي والخدمات المصرفية\n- **توفر أجهزة الصراف الآلي**: متوفرة على نطاق واسع في المدن والمناطق السياحية\n- **حدود السحب**: عادة 2000-3000 جنيه مصري لكل معاملة\n- **بطاقات البنوك**: فيزا وماستركارد مقبولة على نطاق واسع\n- **الرسوم**: تحقق من بنكك بشأن رسوم المعاملات الأجنبية\n- **ساعات عمل البنوك**: من الأحد إلى الخميس، 8:30 صباحًا إلى 2:00 مساءً\n\n## بطاقات الائتمان\n- **القبول**: الفنادق والمطاعم والمتاجر الكبرى في المناطق السياحية تقبل بطاقات الائتمان\n- **الأسواق المحلية**: المتاجر الصغيرة والأسواق عادة تقبل النقد فقط\n- **إخطار البنك**: أبلغ بنكك بخطط سفرك لمنع حظر البطاقة\n\n## البقشيش (الإكرامية)\n- **المطاعم**: 10-15% إذا لم تكن رسوم الخدمة مشمولة\n- **موظفو الفندق**: 5-10 جنيه للحمالين، 10-20 جنيه يوميًا لخدمة الغرف\n- **المرشدون السياحيون**: 50-100 جنيه يوميًا حسب حجم المجموعة\n- **سائقو سيارات الأجرة**: تقريب المبلغ لأعلى يكفي\n\n## نصائح لتوفير المال\n- **قارن الأسعار**: تحقق من عدة مكاتب صرافة للحصول على أفضل الأسعار\n- **تجنب الصرافين في الشوارع**: التزم بالمؤسسات الرسمية\n- **الفئات الصغيرة**: احتفظ بالأوراق النقدية الصغيرة لسيارات الأجرة والبقشيش والمشتريات الصغيرة\n- **المساومة**: متوقعة في الأسواق وسيارات الأجرة، ولكن ليس في المتاجر الثابتة\n\n## أسعار الصرف الحالية\n*اعتبارًا من مايو 2025:*\n- 1 دولار أمريكي ≈ 48 جنيه مصري\n- 1 يورو ≈ 52 جنيه مصري\n- 1 جنيه إسترليني ≈ 61 جنيه مصري\n\nتتقلب أسعار الصرف، لذا تحقق من الأسعار الحالية قبل رحلتك."}',
    ARRAY['egypt'],
    ARRAY['currency', 'money', 'Egyptian pound', 'exchange rates', 'banking', 'ATM', 'tipping'],
    true
);
