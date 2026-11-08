# Suginami Sans — エージェント向け

- 最初にREADME.md、docs/PROJECT_STATUS.md、docs/BUILD.md、docs/VALIDATION.mdを読む。説明と作業記録は日本語を基本にする。
- 独立した書体プロジェクトとして維持する。特定の企業・製品のロゴ、専用配置、ブランド用文書・画像・URL・履歴を追加しない。
- ファミリーはSuginami Sans。現在は静的Extended Boldのみ。標準幅・Regular・バリアブル版を存在するものとして扱わない。
- 元の輪郭はsource/glyphs.json、追加記号はsource/additional-glyphs.json、現在の編集用原本はUFO。画像の再トレースや既存書体への置換をしない。
- 広い字形・内側の空間・太い縦線・水平な端部、二階建てa、一階建てgを維持する。通常yはU+0079、y.altは未符号化でss01による切り替え。連続変形軸にはしない。
- 通常はbuild_fonts.pyでUFOからビルドする。make_font_source.pyは新しい出力先にだけ実行する。再生成の適用順はdocs/BUILD.mdに従う。
- Python依存はプロジェクト内の仮想環境と固定requirementsを使う。秘密情報・仮想環境・キャッシュをGitへ追加しない。完成フォント・比較見本は追跡する。
- 字間の調整はspacing-plan.jsonとUFO、光学補正は各planへ保存する。原本JSONは座標系Y下向き、フォントはY上向き。既存の変換を守る。
- validate.py、validate_fonts.py、make_proofs.pyで字形・Unicode・ss01・字幅・輪郭方向・塗り・重なり・行メトリクス・小サイズを検証し、コマンドと結果・未検証事項を記録する。
- 2026-11-08、ユーザーがSIL Open Font License 1.1と一般公開を承認。OFL.txtを維持し、再配布には著作権表示と全文を含める。予約フォント名はなし。権利者表記はKouki Ojima。ライセンスの変更・追加制限や、別の非公開リポジトリの公開をこの承認から推測しない。
- このリポジトリのhttps://github.com/ojimpo/suginami-sans.gitへの通常pushは承認済み。force push、共有者や公開範囲の変更は含まない。
