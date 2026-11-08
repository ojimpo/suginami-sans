# 引き継ぎ

最初にREADME.md、PROJECT_STATUS.md、BUILD.md、VALIDATION.md、DESIGN_SPEC.mdを確認してください。このリポジトリ単独で、既存のフォントの利用・ビルド・検証・初期JSONからの再生成ができます。

静的Extended Bold 0.106を維持します。0.105からの変更は版とOFLライセンスのメタデータです。通常の編集はUFO、ビルドはscripts/build_fonts.pyです。原本輪郭の再トレース、既存書体への置換、未設計スタイルの合成は行いません。通常yはU+0079、代替yは未符号化y.altで、ss01による切り替えです。

新しいUFOを初期JSONから作る場合はBUILD.mdの順序に従います。新規パスで再生成し、既存UFOを上書きしません。基準入力のハッシュ、全99グリフ・字幅・Unicode・カーニング、OTF/TTFのバイト一致を照合するcheck_reproducibility.pyも利用できます。

2026-11-08、ユーザーがSIL Open Font License 1.1の適用と一般公開を承認しました。OFL.txtとLICENSING.mdを維持してください。実行したコマンドと結果、未検証事項をPROJECT_STATUS.mdとVALIDATION.mdへ追記してください。
