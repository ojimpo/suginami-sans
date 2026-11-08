# 作業状況

更新：2026-11-08（日本時間）

静的Extended Bold 0.106。全99グリフ・97 Unicode、印字可能ASCII95文字とen/em dash、未符号化y.altを収録しています。標準幅・Regular・バリアブル化は保留です。

書体単独のソース・ビルド・検証・使用見本を、このリポジトリだけで扱えるよう整備しました。既存の0.105のOTF/TTFはバイト不変です。内部のUFO独自メタデータは書体固有の名前空間へ整理し、輪郭・字幅・カーニング・ss01は維持しています。

2026-11-08、ユーザーがSIL Open Font License 1.1の適用と一般公開を承認。権利者表記はKouki Ojima、予約フォント名はなし。OFL.txt、フォントのメタデータ、UFO、利用文書、見本と配布物へ反映しました。利用方法はREADME、ライセンスはLICENSING.md、実行記録はVALIDATION.mdを参照してください。

## OFL公開版0.106

0.106は版・copyright・OFLのメタデータ更新です。0.105と99字形の輪郭命令、全字幅、Unicode、GSUB/GPOS、縦メトリクス等の一致を確認しました。フォントバイナリはメタデータにより変わるため、SHA-256は更新します。初期JSONからの再生成も両形式でバイト一致です。

新規ReleaseはOTF／TTF・OFL.txt・見本付きZIP・PNG・SHA256SUMSの6添付です。旧0.105のタグと添付5点は維持し、ReleaseにOFL.txtと追記を追加します。公開後の状態はGITHUB_RELEASE.json、旧作成時の記録はGITHUB_RELEASE_0105.jsonです。

一般公開完了：[v0.106](https://github.com/ojimpo/suginami-sans/releases/tag/v0.106)、対象コミットe65d320b318f69bee0afc58d6e0fabf7f6dfec27。リポジトリはpublic、Releaseはdraft=false／prerelease=false、GitHubのライセンス認識はOFL-1.1です。認証なしのAPIとOFL取得、全添付6点の再ダウンロードでSHA-256一致を確認しました。旧0.105の5添付とタグは不変で、OFL適用の案内とOFL.txtを追加済みです。別の非公開リポジトリの公開範囲は変更していません。

## 文章見本とReleaseの整備（0.105作成時の記録）

2026-11-08、フォントのバイナリを維持したまま見本を更新。見出し・リードと187語の3段落、本文サイズ・行間の比較、自由入力、通常y／ss01、カーニング、形式切替、反転、未収録警告、リセットを整備しました。生成ソースはscripts/specimen/、画像・HTMLはproofs/です。

GitHub Release [v0.105](https://github.com/ojimpo/suginami-sans/releases/tag/v0.105) を作成し、OTF／TTF・見本付きZIP・PNG・SHA256SUMSの5点を添付しました。対象コミットはce56bf21f3e506dd8e5e08765b8a78940d4d15f5。全添付の再ダウンロードでSHA-256一致を確認し、draft=false／prerelease=false／privateを再確認しました。実行結果と配布後の確認はVALIDATION.mdとGITHUB_RELEASE.jsonへ記録しています。Aboutにはfont/typeface/typography/opentype/truetype/fonttoolsのトピックを設定しました。
