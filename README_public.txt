数字タッチ！ 全国ランキング公開版

同梱ファイル
- app_public.py       ゲーム本体
- requirements.txt    Pythonの依存ライブラリ
- Procfile            ホスティング用の起動設定

ローカルで起動する
1. Python 3.10以上をインストール
2. コマンドプロンプトで、このフォルダに移動
3. 次を実行
   py -m pip install -r requirements.txt
   py app_public.py
4. ブラウザで http://127.0.0.1:5000 を開く

全国公開する場合（例：Render + PostgreSQL）
1. GitHubに新しいリポジトリを作成し、この3ファイルをアップロードする。
2. PostgreSQLのホスティングサービス（例：Neon）でデータベースを作り、接続文字列を取得する。
3. Renderで New > Web Service からGitHubリポジトリを選ぶ。
4. Build Command: pip install -r requirements.txt
   Start Command: gunicorn app_public:app
5. Renderの環境変数に DATABASE_URL を追加し、手順2のPostgreSQL接続文字列を設定する。
6. デプロイ完了後に発行された https://... のURLを開き、スマホでも動作確認する。

注意
- DATABASE_URLを設定しない場合はローカルSQLiteを使います。クラウドの一時ファイルシステムにSQLiteで保存すると、再デプロイ等で記録が消えることがあるため、全国公開ではPostgreSQLを設定してください。
- ランキングは公開され、入力したニックネームも公開表示されます。個人情報や本名は入力しないでください。
- 現在の不正対策は簡易的です。大規模なランキング運用には追加のサーバー側検証・レート制限が必要です。
- Xで共有する際は、デプロイ後の公開URLを投稿してください。公開URLがまだない段階では、他の人は遊べません。
