# MRシステム - 商品情報管理アプリ

## 概要

商品パッケージの画像をアップロードするだけで、AIが自動的に商品情報を抽出・登録するWebアプリケーションです。

## システム構成

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   フロントエンド   │────▶│   バックエンド    │────▶│   データベース    │
│    (Vercel)     │     │    (Render)     │     │  (PostgreSQL)   │
│    Next.js 14   │     │  Python FastAPI │     │                 │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │ Gemini   │ │DuckDuckGo│ │Cloudinary│
              │   API    │ │  Search  │ │  画像    │
              │(AI抽出)  │ │(価格検索) │ │ストレージ │
              └──────────┘ └──────────┘ └──────────┘
```

## 主な機能

### 1. 画像アップロード＆AI自動抽出
- 商品パッケージの画像をアップロード
- Google Gemini AIが画像から以下の情報を自動抽出：
  - 商品名
  - 内容量
  - 製造者/販売者
  - 原材料
  - 栄養成分表示
  - 商品の訴求ポイント
  - カテゴリー自動分類

### 2. 価格情報自動検索
- 商品名と製造者名からDuckDuckGo検索を実行
- 市場価格情報を自動取得

### 3. 商品管理
- 商品一覧表示
- カテゴリー別フィルタリング
- 商品情報の編集・削除
- 複数画像の管理

## 技術スタック

### フロントエンド
| 技術 | 用途 |
|------|------|
| Next.js 14 | Reactフレームワーク |
| TypeScript | 型安全な開発 |
| Tailwind CSS | スタイリング |
| Vercel | ホスティング |

### バックエンド
| 技術 | 用途 |
|------|------|
| Python 3.12 | プログラミング言語 |
| FastAPI | Web APIフレームワーク |
| Render | ホスティング |

### データベース・ストレージ
| 技術 | 用途 |
|------|------|
| PostgreSQL | 本番データベース（Render） |
| SQLite | ローカル開発用データベース |
| Cloudinary | 画像ストレージ（本番） |

### AI・外部API
| 技術 | 用途 |
|------|------|
| Google Gemini API | 画像からの情報抽出 |
| DuckDuckGo Search | 価格情報検索 |

## カテゴリー一覧

| カテゴリー | 説明 |
|-----------|------|
| Chocolate | チョコレート |
| Gummy | グミ |
| Cookie | クッキー |
| Snack | スナック菓子 |
| Donut | ドーナツ |
| Jelly | ゼリー |
| Noodle | 麺類 |
| Supplement | サプリメント |
| Beverage | 飲料 |
| Protein | プロテイン |
| Other | その他 |

## ディレクトリ構成

```
02_アプリ開発/
├── frontend/                 # フロントエンド（Next.js）
│   ├── src/
│   │   ├── app/             # ページコンポーネント
│   │   ├── components/      # UIコンポーネント
│   │   └── types/           # TypeScript型定義
│   ├── next.config.mjs      # Next.js設定
│   └── package.json
│
├── backend/                  # バックエンド（FastAPI）
│   ├── main.py              # APIエンドポイント
│   ├── database.py          # データベース操作
│   ├── schemas.py           # Pydanticスキーマ
│   ├── services/
│   │   ├── gemini_extractor.py  # AI抽出処理
│   │   ├── searcher.py          # 価格検索
│   │   └── image_uploader.py    # 画像アップロード
│   └── requirements.txt
│
└── products.db              # ローカル開発用SQLiteデータベース
```

## 環境変数

### バックエンド（Render）
| 変数名 | 説明 |
|--------|------|
| GEMINI_API_KEY | Google Gemini APIキー |
| DATABASE_URL | PostgreSQL接続URL |
| CLOUDINARY_URL | Cloudinary接続URL |
| ALLOWED_ORIGINS | CORS許可オリジン |

### フロントエンド（Vercel）
| 変数名 | 説明 |
|--------|------|
| NEXT_PUBLIC_API_URL | バックエンドAPIのURL |

## アクセスURL

| 環境 | URL |
|------|-----|
| フロントエンド（本番） | https://mr-system-mu.vercel.app |
| バックエンド（本番） | https://mr-system-backend.onrender.com |
| フロントエンド（ローカル） | http://localhost:3000 |
| バックエンド（ローカル） | http://localhost:8000 |

## ローカル開発手順

### バックエンド起動
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### フロントエンド起動
```bash
cd frontend
npm install
npm run dev
```

## 無料枠の制限

| サービス | 制限 |
|---------|------|
| Render | 月750時間、15分無アクセスでスリープ |
| Vercel | 帯域幅100GB/月 |
| Cloudinary | 25GB ストレージ、25GB 帯域幅/月 |
