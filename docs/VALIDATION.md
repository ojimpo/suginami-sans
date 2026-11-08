# 検証記録

実行日：2026-11-08（日本時間）。Python 3.12.14、fontTools 4.61.1、skia-pathops 0.9.2、HarfBuzzのPythonバインディング0.57.0、FreeTypeのPythonバインディング2.5.1、Pillow 13.0.0。固定依存はrequirements-font.txtです。

以下は今回この環境で実行した検証です。ルートから、依存を導入したプロジェクト内の仮想環境のPythonで実行します。

```sh
python scripts/build_fonts.py
python scripts/validate.py
python scripts/validate_fonts.py
python scripts/compare_font_versions.py
python scripts/check_reproducibility.py
python scripts/make_proofs.py
node scripts/verify_specimen.cjs
python scripts/package_release.py
```

- JSONの98エントリー（97輪郭＋space）、印字可能ASCII、Unicode重複なし、有限境界、全輪郭の閉鎖を確認。
- UFO/OTF/TTFの99グリフ・97 Unicode、ss01によるy/y.alt切り替え、全テーブル再コンパイル、字幅、行メトリクス、輪郭方向、nonzero/evenoddの面積一致、再整理時の面積を確認。
- 初期JSONから新規UFOを作り、字間・小サイズ補正・追加記号・リリース補正を順に適用。99グリフの輪郭命令・字幅・Unicode・グリフ順・features・groups・kerningが一致し、OTF/TTFがバイト一致。
- FreeTypeの97輪郭×2形式×12/16/24/48/96px、970件の穴数検査で変化0。
- a/s/%/@×2形式×12〜16px×縦横1/4pxずつの16位置、640件の穴数検査で変化0。
- 識別文字列・代替y・カーニング例・記号を5サイズ・2形式・通常/反転の160配置でクリッピングなし。反転は同じ字形マスクの前景と背景を交換する方式。
- 明示したファイルだけを配布ZIPへ収録し、CRCと全メンバーの読み戻しを照合。
- Microsoft Edge 157.0.4341.42／Playwright 1.62.1で、見出し・リード・187語の3段落を表示。本文16／24／32pxと行間1.3／1.6／1.9の操作を確認。
- OTF／TTFの通常y・ss01・kernオン／オフの実測幅がHarfBuzzの期待値と0.04px以内で一致。
- 改行入力、サイズ、未収録警告、HTML文字列の文字としての表示、反転時の本文コントラスト、全設定のリセットを確認。
- 1440／768／390pxでページ全体の横はみ出しなし。97輪郭の字形タイルを確認。ブラウザエラーとリクエスト失敗は0。
- 配布ZIPを展開したHTML見本でも同じ7項目の実ブラウザ検証に成功。HTML・CSS・JavaScript・フォントの相対パスと画像リンクを確認。
- OFL公開版0.106では、UFOと全nameレコードのcopyright／OFL全文／URL、版0.106を検証。予約フォント名はなし。
- OTF／TTFの全99字形の輪郭命令・字幅・Unicode、hhea/OS/2/GSUB/GPOS/hmtx/maxp/postが0.105と一致。版と著作権・ライセンスのメタデータ以外に変更なし。

機械可読記録はFONT_BUILD.json、STATIC_VALIDATION.json、REPRODUCIBILITY.json、RASTER_VALIDATION.json、SPECIMEN_BUILD.json、BROWSER_SPECIMEN_VALIDATION.json、PACKAGE_BROWSER_VALIDATION.json、RELEASE_PACKAGE.jsonです。画像見本はproofs/specimen.png、対話見本はproofs/index.htmlです。見本はscripts/specimen.pyとscripts/specimen/から再生成できます。

ブラウザ検証は任意のNode.js環境へPlaywrightを導入し、Microsoft Edgeを利用します。別のブラウザを使う場合はSPECIMEN_BROWSER_CHANNELを設定します。Pythonのフォントビルド依存には追加しません。配布物を作り直す場合は、対象ファイルと一致するブラウザ検証記録が必要です。

検証は指定したサイズ・位置・レンダラーでの結果です。穴数はalpha閾値128の4近傍背景による検査で、あらゆる描画環境を保証しません。ヒンティング、独立した厳密な曲線自己交差判定、WindowsへインストールしたWord/Adobe等での動作は未検証です。I/lは同形です。可変版・別スタイルは未設計です。

公開時のライセンス・旧版比較はOFL_VALIDATION.json、公開範囲・Release添付の認証なし取得はGITHUB_RELEASE.jsonに記録します。過去の「バイト不変」は0.105の見本整備時の結果で、0.106のバイナリにはOFLの全文等が追加されています。
