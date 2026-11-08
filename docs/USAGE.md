# Suginami Sans Extended Bold 0.105 — 使い方

OTFまたはTTFのどちらか一方をインストールします。ファミリー名はアプリにより「Suginami Sans」または「Suginami Sans Extended」、スタイルは「Extended Bold」または「Bold」と表示されます。

印字可能ASCII95文字とen/em dash、未符号化の代替yを収録しています。日本語・アクセント付き文字は未収録です。Iとlは同形です。ヒンティングは未実装です。

通常のyはU+0079です。スタイルセット1（ss01、フォント内では「Logo y」）で代替yへ切り替わります。別のUnicodeや専用キーは使いません。ss01に対応しないアプリでは通常yが表示されます。

```css
@font-face {
  font-family: "Suginami Sans";
  src: url("SuginamiSans-ExtendedBold.otf") format("opentype");
  font-style: normal;
  font-weight: 700;
}
.suginami { font-family: "Suginami Sans", sans-serif; font-weight: 700; font-kerning: normal; font-synthesis: none; }
.alternate-y { font-feature-settings: "ss01" 1; }
```

```html
<span class="suginami">Type freely</span>
<span class="suginami alternate-y">Type freely</span>
```

ss01は適用範囲内のすべてのyへ作用します。コピー・検索時の文字列は通常のyのままです。任意の字間調整を加えなければ、フォント内のベアリングとカーニングを使います。

一般向けの公開・配布ライセンスは未決定です。
