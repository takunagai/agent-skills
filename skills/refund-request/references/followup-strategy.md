# フォローアップ戦略

返金リクエスト送信後、返信がない場合や拒否された場合の段階的エスカレーション戦略。

---

## タイムライン概要

```
Day 0:   初回メール送信
Day 3:   返信なし → フォローアップ #1（リマインダー）
Day 7:   返信なし → フォローアップ #2（エスカレーション示唆）
Day 14:  返信なし → フォローアップ #3（最終通告）
Day 21+: 外部手段に移行
```

---

## メールスレッディングの原則

- **フォローアップメールは、初回メールへの「返信」として送る**（同一スレッドにする）。サポート担当が過去のやりとりを一目で確認できる。
- ただし、Phase 3（最終通告）以降は、**新規メールで送ることも検討**する（件名に「Final Notice」を含めることで緊急性を示す）。

## 自動返信・チケット番号への対応

企業から自動返信を受け取った場合:
- **チケット番号が発行されたら、後続のメール全てにその番号を含める**（件名に `[Ticket #12345]` を追加）
- 自動返信に「○日以内に対応」と記載がある場合、その期限まで待ってからフォローアップする
- 自動返信のみで実質的な返信がない場合は、タイムライン通りフォローアップに進む

---

## Phase 1: フォローアップ #1（3 営業日後）

### 目的
丁寧なリマインダー。メールが埋もれている可能性を考慮。

### テンプレート（英語）

Subject: Follow-up: Refund Request - [Transaction ID]

> Dear [Company Name] Support Team,
>
> I am following up on my refund request sent on [date] regarding Transaction ID [ID].
>
> I understand your team may be busy, but I would appreciate an update on the status of my request. Please let me know if any additional information is needed from my end.
>
> Thank you for your attention.
>
> Best regards,
> [Name]

### テンプレート（日本語）

件名: 【再送】返金リクエストについて - [注文番号]

> [サービス名] サポートチームご担当者様
>
> [日付] にお送りした返金リクエスト（注文番号: [番号]）について、フォローアップのご連絡です。
>
> お忙しいところ恐縮ですが、リクエストの進捗状況をお知らせいただけますと幸いです。追加で必要な情報がありましたら、お知らせください。
>
> よろしくお願いいたします。
> [名前]

---

## Phase 2: フォローアップ #2（7 営業日後）

### 目的
対応の緊急性を高める。別の連絡手段も試す。

### 戦略
- **別のチャネルも併用**: Discord、Twitter/X、ライブチャット、電話等
- **SNS での問い合わせ**は公開されるため、企業の対応が速くなる傾向がある
- **メールには「まだ返信をいただいていない」旨を明記**

### テンプレート（英語）

Subject: Second Follow-up: Refund Request - [Transaction ID] (Awaiting Response)

> Dear Support Team,
>
> This is my second follow-up regarding the refund request I submitted on [date] for Transaction ID [ID]. I have not yet received a response.
>
> I would like to resolve this matter amicably and promptly. If I do not hear back within the next few days, I may need to explore alternative avenues to resolve this issue.
>
> I remain available to provide any information you may need.
>
> Best regards,
> [Name]

### テンプレート（日本語）

件名: 【2回目】返金リクエストについて - [注文番号]（ご返信お待ちしております）

> [サービス名] サポートチームご担当者様
>
> [日付] にお送りした返金リクエスト（注文番号: [番号]）について、2回目のフォローアップです。現時点でまだご返信をいただいておりません。
>
> 円満かつ迅速な解決を希望しておりますが、近日中にご対応いただけない場合は、別の方法での解決を検討せざるを得ない状況です。
>
> 必要な情報がありましたら、いつでもご提供いたします。
>
> よろしくお願いいたします。
> [名前]

---

## Phase 3: フォローアップ #3 / 最終通告（14 営業日後）

### 目的
最終通告。次のステップを明確に予告する。

### 戦略
- **具体的な次のアクション**を予告する（chargeback、消費者保護機関への相談等）
- **期限を設定**する（「X 日以内にご返信がない場合」）
- **トーンは冷静だが毅然とする**

### テンプレート（英語）

Subject: Final Notice: Refund Request - [Transaction ID]

> Dear Support Team,
>
> I am writing for the third time regarding my refund request submitted on [date] for Transaction ID [ID], totaling [amount]. Despite multiple follow-ups, I have not received a substantive response.
>
> I have made every effort to resolve this matter directly with your team. However, if I do not receive a response within 5 business days, I will have no choice but to:
> - File a chargeback / dispute with my credit card provider
> - [Report to the relevant consumer protection agency / File a complaint with [platform name, e.g., BBB, PayPal, App Store]]
>
> I sincerely hope we can resolve this without escalation. I remain willing to work with you on a fair resolution.
>
> Best regards,
> [Name]

### テンプレート（日本語）

件名: 【最終通告】返金リクエスト - [注文番号]

> [サービス名] サポートチームご担当者様
>
> [日付] に送信した返金リクエスト（注文番号: [番号]、金額: [金額]）について、3回目のご連絡です。複数回のフォローアップにもかかわらず、実質的なご返信をいただいておりません。
>
> 直接の解決に向けて最善を尽くしてまいりましたが、5営業日以内にご対応いただけない場合は、以下の措置を取らざるを得ません:
> - クレジットカード会社への chargeback（異議申し立て）
> - [消費者保護機関への相談 / [プラットフォーム名] への報告]
>
> エスカレーションなく解決できることを心から願っております。公正な解決に向けて、引き続き協力する用意があります。
>
> よろしくお願いいたします。
> [名前]

---

## Phase 4: 外部手段（21 日以降）

フォローアップが全て無視された場合、または返金を明確に拒否された場合の選択肢。

### 選択肢 A: Chargeback（クレジットカード異議申し立て）

**概要**: クレジットカード会社に取引の異議申し立てを行い、強制的に返金させる。

**手順**:
1. カード会社に電話またはオンラインで dispute を提出
2. 必要書類を用意:
   - 取引明細
   - 返金リクエストメールの控え（全フォローアップ含む）
   - 企業の返金ポリシー（自分が条件を満たしていることの証拠）
   - 未使用の証拠（該当する場合）
3. カード会社が調査（通常 30-90 日）
4. 結果に基づき返金 or 却下

**注意点**:
- Chargeback を行うとアカウントが ban される可能性が高い
- 今後そのサービスを使う予定がある場合は慎重に
- Chargeback の期限はカード会社によるが、通常 60-120 日以内
- Chargeback は「正当な理由」が必要。使い倒した後の chargeback は不正行為になりうる

### 選択肢 B: 決済プラットフォーム経由の dispute

**PayPal の場合**:
- PayPal Resolution Center から dispute を開始
- 購入後 180 日以内

**App Store / Google Play の場合**:
- 各プラットフォームの返金フォームから申請
- App Store: reportaproblem.apple.com
- Google Play: play.google.com/store/account/orderhistory

### 選択肢 C: 消費者保護機関への相談

**日本**: 
- 国民生活センター（消費者ホットライン: 188）
- 越境消費者センター（CCJ）: 海外事業者とのトラブル

**米国**:
- FTC (Federal Trade Commission)
- BBB (Better Business Bureau)
- 州の Attorney General

**EU**:
- European Consumer Centre (ECC)

### 選択肢 D: SNS での公開（最終手段）

- Trustpilot、Twitter/X、Reddit 等でレビューを投稿
- 事実のみを記載し、感情的な表現は避ける
- 企業のサポートが SNS をモニタリングしている場合、対応が速くなることがある

---

## 返金拒否への対応

企業が返金を明確に拒否した場合:

### 拒否理由別の対応策

| 拒否理由 | 対応策 |
|---------|--------|
| 「返金期限を過ぎています」 | ポリシーの期限を再確認。期限内なら証拠を提示。期限外でも「善意の対応」を求める |
| 「サービスを使用しています」 | 使用量が極めて少ないことを具体的に示す（ログイン回数等） |
| 「ポリシー上返金不可です」 | ポリシーの例外条項を確認。上位サポート（マネージャー）へのエスカレーションを依頼 |
| 「返金手続きに時間がかかります」 | 具体的な期限を確認し、その期限を記録する |

### エスカレーション依頼テンプレート（英語）

> "I appreciate your response, but I respectfully disagree with this decision. Could you please escalate this matter to a supervisor or manager who may have the authority to review my case further?"

### エスカレーション依頼テンプレート（日本語）

> 「ご返信ありがとうございます。恐れ入りますが、今回のご判断には同意しかねます。上位の担当者様にエスカレーションしていただき、改めてご検討いただくことは可能でしょうか」
