# Vercelデプロイ手順

## 前提条件

- Vercelアカウント（[https://vercel.com/signup](https://vercel.com/signup)）
- Gitリポジトリ（GitHub推奨）

## デプロイ方法

### 方法1: Vercel CLIを使用（推奨）

1. **Vercel CLIでログイン**
   ```bash
   cd /Users/motoki/projects/polyseek_sentient
   npx vercel login
   ```
   ブラウザが開くので、Vercelアカウントでログインしてください。

2. **デプロイ実行**
   ```bash
   npx vercel --prod
   ```
   初回デプロイ時は、いくつかの質問に答える必要があります：
   - Set up and deploy? **Yes**
   - Which scope? **あなたのアカウントを選択**
   - Link to existing project? **No**（初回の場合）
   - What's your project's name? **polyseek-sentient**（または任意の名前）
   - In which directory is your code located? **./**（デフォルト）

3. **環境変数の設定**
   デプロイ後、Vercelダッシュボードで環境変数を設定してください：
   - [Vercel Dashboard](https://vercel.com/dashboard) → プロジェクトを選択 → Settings → Environment Variables

   必要な環境変数：
   ```
   GOOGLE_API_KEY=your-google-api-key
   # または
   OPENAI_API_KEY=your-openai-api-key
   # または
   OPENROUTER_API_KEY=your-openrouter-api-key
   ```

   オプションの環境変数：
   ```
   NEWS_API_KEY=your-news-api-key
   REDDIT_CLIENT_ID=your-reddit-client-id
   REDDIT_CLIENT_SECRET=your-reddit-client-secret
   X_BEARER_TOKEN=your-x-bearer-token
   LITELLM_MODEL_ID=gemini/gemini-2.0-flash-001
   CORS_ORIGINS=https://your-domain.com
   ```

### 方法2: GitHub経由でデプロイ（推奨）

1. **GitHubリポジトリにプッシュ**
   ```bash
   git init
   git add .
   git commit -m "Initial commit for Vercel deployment"
   git remote add origin https://github.com/your-username/polyseek_sentient.git
   git push -u origin main
   ```

2. **Vercelダッシュボードでインポート**
   - [Vercel Dashboard](https://vercel.com/dashboard) にアクセス
   - "Add New..." → "Project" をクリック
   - GitHubリポジトリを選択
   - プロジェクトをインポート

3. **環境変数の設定**
   - プロジェクト設定 → Environment Variables で環境変数を追加
   - Production、Preview、Development それぞれに設定可能

4. **デプロイ**
   - "Deploy" ボタンをクリック
   - デプロイが完了すると、URLが表示されます

## 設定ファイル

### `vercel.json`
- Python APIエンドポイント（`/api/*`）を `api/index.py` にルーティング
- 静的ファイル（フロントエンド）を `frontend/` から配信
- Python 3.9 ランタイムを使用

### `api/index.py`
- FastAPIアプリをインポートしてエクスポート
- Vercelが自動的に検出します

## トラブルシューティング

### ビルドエラー

1. **Pythonパスの問題**
   - `vercel.json` の `env.PYTHONPATH` が `src` に設定されているか確認
   - `api/index.py` のインポートパスが正しいか確認

2. **依存関係のインストールエラー**
   - `requirements.txt` がプロジェクトルートにあるか確認
   - Python バージョンが 3.9+ であることを確認

3. **モジュールインポートエラー**
   - `src/polyseek_sentient/` ディレクトリ構造を確認
   - `api/index.py` のインポートパスを確認

### ランタイムエラー

1. **環境変数が設定されていない**
   - Vercelダッシュボードで環境変数を確認
   - Production環境に設定されているか確認

2. **APIエンドポイントが見つからない**
   - フロントエンドの `API_BASE_URL` 設定を確認
   - Vercelのルーティング設定を確認

### デバッグ方法

1. **Vercelログの確認**
   - Vercelダッシュボード → プロジェクト → "Logs" タブ
   - ビルドログとランタイムログを確認

2. **ローカルでテスト**
   ```bash
   npx vercel dev
   ```
   ローカル環境でVercelの動作をシミュレートできます

## カスタムドメインの設定

1. Vercelダッシュボード → プロジェクト → Settings → Domains
2. ドメインを追加
3. DNS設定を更新

## 継続的デプロイ

GitHubリポジトリに接続している場合：
- `main` ブランチへのプッシュ → 本番環境にデプロイ
- その他のブランチ → プレビューデプロイ

## 参考リンク

- [Vercel Documentation](https://vercel.com/docs)
- [Vercel Python Runtime](https://vercel.com/docs/runtimes/python)
- [FastAPI on Vercel](https://vercel.com/guides/deploying-fastapi-with-vercel)

