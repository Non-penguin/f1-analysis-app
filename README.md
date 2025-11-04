# F1データ解析プロジェクト
F1のレース、予選、スプリントにおける各ドライバーのラップタイム、コンパウンドなどのデータを比較するwebアプリケーション。Dockerを用いるため、下記のコマンドを実行するだけでアプリケーションをセットアップ可能。

セットアップと実行方法

1.リポジトリのクローン

 git clone https://github.com/Non-penguin/f1-analysis-app
 
 cd f1-analysis

2.Dockerイメージのビルドと実行

docker-compose up

上記のコマンドを実行してもビルドできない場合は、sudoで実行

バッググラウンドで実行したい場合は、-d オプションで起動

3.アプリケーションにアクセス

  http://localhost:8501  にアクセス

使用技術
- Python 3.10
- Streamlit
- fastf1
- Pandas
- Matplotlib
- Docker
