# Suginami Sans Extended Bold 0.105 — 使い方

OTFまたはTTFのどちらか一方をインストールします。ファミリー名はアプリにより「Suginami Sans」または「Suginami Sans Extended」、スタイルは「Extended Bold」または「Bold」と表示されます。

## 同梱の見本

`specimen.png` は、見出し・リード・187語の3段落、英大小文字・数字・記号、yの比較、カーニング、サイズ別見本をまとめた画像です。

操作できる見本は `specimen/index.html` をブラウザで開いてください。本文は16／24／32px、行間は1.3／1.6／1.9で比較できます。自由入力は4,096文字までで、改行・OTF／TTF・代替y・カーニング・白黒反転を切り替えられます。未収録文字には警告が出ます。リセットは本文設定も含めて初期状態へ戻します。

ローカルファイルからのフォント読み込みがブラウザで制限される場合は、展開先で `python -m http.server 8766 --bind 127.0.0.1` を実行し、`http://127.0.0.1:8766/specimen/` を開いてください。Pythonはサーバーを使う場合だけ必要です。

## 収録文字と字形の切り替え

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
