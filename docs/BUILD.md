# ビルドと再生成

通常の編集原本は `source/SuginamiSans-ExtendedBold.ufo/` です。`scripts/build_fonts.py` はUFOを読み、同じ入力から同じOTF/TTFを生成します。通常のビルドで以下の再生成は不要です。

## 初期JSONから別のUFOを作る

ルートで実行します。既存UFOへの上書きは拒否します。次のnew.ufoは存在しないパスを選びます。

```sh
python scripts/make_font_source.py --output work/new.ufo
python scripts/apply_spacing.py --ufo work/new.ufo --report work/new-spacing.json
python scripts/apply_small_size.py --ufo work/new.ufo --report work/new-small-size.json
python scripts/add_symbols.py --ufo work/new.ufo
python scripts/apply_release_size.py --ufo work/new.ufo --report work/new-release-size.json
```

依存を導入したプロジェクト内の仮想環境のPythonで実行してください。これらの処理は監査JSONも出力します。`make_font_source.py` は `docs/OUTLINE_NORMALIZATION.json` を更新するため、作業後に差分を確認します。

元の輪郭・座標はglyphs.json、追加3記号はadditional-glyphs.jsonに保存しています。文字原本はY下向き、ベースライン204。フォントは `(204 - y) * (700 / 286)` でY上向きへ変換します。SVG pathごとのfill-ruleを処理し、塗り領域を和集合にしてから変換します。

現在採用するメトリクスはUPM1000、capHeight700、ascender850、descender-250、lineGap0。一般の文字組みの字幅・space250・46カーニングルール（展開後88ペア）はspacing-plan.jsonとUFOに保存しています。全文章に対する最終評価済みの値という意味ではありません。

small-size-plan.jsonは%と@、release-size-plan.jsonはa/s/%/@の既存曲線への光学補正を保持します。原本JSON自体の輪郭を補正済みのものへ置き換えません。UFOへの手編集を再生成へ含めたい場合は、対応する計画やソースへ明示的に反映します。

`source/input-checksums.json` はこのリポジトリの基準入力を照合します。入力を意図して編集した場合は再評価した上でハッシュを更新します。特定の過去コミットや外部アートワークは必要ありません。

## 見本の編集と配布

画像見本の生成はscripts/specimen.py、HTML／CSS／JavaScriptと原稿はscripts/specimen/です。原稿は独自の英文187語・3段落で、すべて収録文字を使います。編集後はmake_proofs.pyで画像とHTMLを更新し、任意のNode.js＋PlaywrightとMicrosoft Edgeで `node scripts/verify_specimen.cjs` を実行します。今回の固定確認版はPlaywright 1.62.1です。必要なら `npm install --no-save --package-lock=false playwright@1.62.1` で作業用に導入できます。

package_release.pyは、フォントの静的検証・画像検証・再現性・現在の見本と一致するブラウザ検証記録がすべて成功した場合にだけ配布物を作ります。ZIP内のHTML見本はspecimen/へ収録し、フォントの相対パスを配布配置に合わせます。
