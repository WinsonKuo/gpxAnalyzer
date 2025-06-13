# gpxAnalyzer

這個專案提供 `gpx_analyzer.py` 腳本，可以讀取 GPX 檔案並繪製距離高度關係圖。
程式會將 X 軸切成每 100 公尺的區間計算平均坡度，
並在曲線下方以垂直色條呈現坡度難度，同時將 GPX 中的 waypoint 以名稱標示在圖上。
## 使用方式

```bash
python3 gpx_analyzer.py <path_to_gpx_file>
```

執行後會以視窗顯示分析結果。
