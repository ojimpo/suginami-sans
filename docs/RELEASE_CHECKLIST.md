# 静的Release 0.105 — 2026-11-08

対象は書体単独のprivateリポジトリです。今回は見本と配布物の整備で、フォントのバイナリ・輪郭・字幅は変更しません。Release作成はユーザーの依頼に基づきます。

- ソース・UFO・OTF/TTFの検証：PASS。
- 初期JSONからの再生成とバイト一致：PASS。
- FreeType 970件＋640件、穴数変化0：PASS。
- 文章・サイズ・行間・形式・ss01・kern・入力・反転・リセット、3画面幅：実ブラウザでPASS。
- PNGのレイアウト、反転時の本文とモバイル表示：画像を確認。
- 配布ZIP：明示したファイルだけを収録。CRCと全メンバーを読み戻して確認。
- GitHub About：説明とfont/typeface/typography/opentype/truetype/fonttoolsを設定・確認。
- 公開範囲：private。ライセンス追加なし。ブランド素材は含めない。

CIは設定していないため、今回の確認はローカルでの実行結果です。配布ZIP内の見本の検証結果はPACKAGE_BROWSER_VALIDATION.json、Releaseの対象コミット・添付内容・再ダウンロード照合はGITHUB_RELEASE.jsonへ記録します。

配布後：v0.105を確定し、draft=false／prerelease=false／privateを確認しました。5添付を再ダウンロードし、全SHA-256がローカル配布物と一致しました。配布物は連続生成でもハッシュ一致です。

添付ファイルの欠落・ハッシュ不一致・見本のフォント読込失敗が見つかった場合はReleaseをドラフトへ戻し、配布物と検証を修正します。既存のフォントとソースの履歴は保持します。
