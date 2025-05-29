# LINE Bot ろんな

## 概要
昭和のおばあちゃん風の応答を生成するLINE Bot「ろんな」です。このプロジェクトはAzure Functionsを使用して構築されており、OpenAIのAPIを活用してユーザーとの対話を行います。

## 主な機能
- **昭和のおばあちゃん風応答**: ユーザーのメッセージに対して、関西弁混じりの温かい応答を生成します。
- **コンテキスト保持**: 最新の5メッセージを保持し、会話の流れを維持します。
- **LINE Webhook対応**: LINE Messaging APIを使用してメッセージを受信し、応答を送信します。

## 使用技術
- **Azure Functions**: サーバーレスアーキテクチャでのデプロイ。
- **OpenAI API**: 応答生成に使用。
- **LINE Messaging API**: ユーザーとのメッセージ送受信。

## 必要な環境変数
以下の環境変数を設定してください。
- `LINE_CHANNEL_ACCESS_TOKEN`: LINE Botのアクセストークン。
- `LINE_CHANNEL_SECRET`: LINE Botのチャネルシークレット。
- `OPENAI_API_KEY`: OpenAI APIのキー。

## セットアップ手順
1. **リポジトリをクローン**
```bash
git clone https://github.com/kichouji/line-bot-ronna
cd line-bot-ronna
```

2. **依存関係をインストール**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. **環境変数の設定**
`local.settings.json`に必要な環境変数を設定してください。

4. **Azure Functionsのローカル実行**
```bash
func start
```

5. **デプロイ**
Azure Functionsにデプロイするには、以下のコマンドを使用します。
```bash
func azure functionapp publish <FunctionAppName>
```

## LINE Botの登録手順（要精査）

1. **LINE Developersコンソールにログイン**
   - [LINE Developers](https://developers.line.biz/ja/) にアクセスし、LINEアカウントでログインします。

2. **プロバイダーを作成**
   - プロバイダーを作成していない場合は、新しいプロバイダーを作成します。

3. **チャネルを作成**
   - プロバイダーの下に「Messaging API」チャネルを作成します。
   - 必要な情報を入力し、チャネルを作成します。

4. **チャネル設定を確認**
   - 作成したチャネルの「チャネル基本設定」から以下の情報を取得します。
     - チャネルシークレット
     - チャネルアクセストークン（ロングターム）

5. **Webhook URLを設定**
   - 「Messaging API」設定ページでWebhook URLを設定します。
     - Webhook URLの形式: `https://<FunctionAppName>.azurewebsites.net/api/HttpTrigger1`
   - Webhookの利用を「利用する」に設定します。

6. **環境変数に設定**
   - 取得したチャネルシークレットとアクセストークンを環境変数に設定します。

7. **Botを友だち追加**
   - 「QRコード」または「友だち追加リンク」を使用して、Botを友だちに追加します。

8. **動作確認**
   - LINEアプリでBotにメッセージを送信し、応答が返ってくることを確認します。

## Azureでの環境変数設定

Azure Functionsにデプロイした後、以下の手順で環境変数を設定します。

1. **Azureポータルにログイン**
   - [Azureポータル](https://portal.azure.com/) にアクセスし、アカウントでログインします。

2. **Function Appを選択**
   - デプロイしたFunction Appをリソース一覧から選択します。

3. **「設定」メニューを開く**
   - 左側のメニューから「設定」 > 「構成」を選択します。

4. **新しいアプリケーション設定を追加**
   - 「+ 新しいアプリケーション設定」をクリックし、以下のキーと値を追加します。
     - `LINE_CHANNEL_ACCESS_TOKEN`: LINE Botのアクセストークン
     - `LINE_CHANNEL_SECRET`: LINE Botのチャネルシークレット
     - `OPENAI_API_KEY`: OpenAI APIのキー

5. **保存**
   - 変更を保存し、Function Appを再起動します。

6. **動作確認**
   - 環境変数が正しく設定されていることを確認するため、LINEアプリでBotにメッセージを送信し、応答が返ってくることを確認します。

## ファイル構成
```
line-bot-ronna/
├── function_app.py          # メインのアプリケーションコード
├── host.json               # Azure Functionsのホスト設定
├── local.settings.json     # ローカル環境用の設定
├── requirements.txt        # Python依存関係
└── system_prompt.txt       # システムプロンプト
```

## ライセンス
このプロジェクトはMITライセンスの下で提供されています。詳細は[LICENSE](LICENSE)ファイルをご覧ください。