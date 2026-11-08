# 作業状況

更新：2026-11-08（日本時間）

静的Extended Bold 0.105。全99グリフ・97 Unicode、印字可能ASCII95文字とen/em dash、未符号化y.altを収録しています。標準幅・Regular・バリアブル化は保留です。

書体単独のソース・ビルド・検証・使用見本を、このリポジトリだけで扱えるよう整備しました。既存の0.105のOTF/TTFはバイト不変です。内部のUFO独自メタデータは書体固有の名前空間へ整理し、輪郭・字幅・カーニング・ss01は維持しています。

一般向けライセンスと公開範囲の変更は未決定です。今回の準備ではprivateを維持します。利用方法はREADME、実行記録はVALIDATION.mdを参照してください。

## 文章見本とReleaseの整備

2026-11-08、フォントのバイナリを維持したまま見本を更新。見出し・リードと187語の3段落、本文サイズ・行間の比較、自由入力、通常y／ss01、カーニング、形式切替、反転、未収録警告、リセットを整備しました。生成ソースはscripts/specimen/、画像・HTMLはproofs/です。

GitHub Release v0.105へ、OTF／TTF・見本付きZIP・PNG・SHA256SUMSの5点を添付します。実行結果と配布後の確認はVALIDATION.mdとGITHUB_RELEASE.jsonへ記録します。Aboutにはfont/typeface/typography/opentype/truetype/fonttoolsのトピックを設定しました。
