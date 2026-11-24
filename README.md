# 金文字形全編 · GoldenDict 詞典

將 [jinwen-glyph-search](https://github.com/fangquinlan/jinwen-glyph-search) 的字形資料編譯成一份可離線檢索的 GoldenDict 詞典（MDict 格式）：

- 查詢**字頭**，瀏覽其在商周金文裡的全部寫法；
- 查詢**構件**，反查所有以其為一級構件的字頭。

## 成品規模

| 項目 | 數量 |
| --- | --- |
| 字頭詞條 | 5,617 |
| 構件詞條（本身不是字頭） | 695 |
| 子字頭別名 | 927 |
| 索引頁 | 1（「未編碼字頭一覽」） |
| 詞條總數 | 7,240 |
| 字形記錄 | 35,816 |
| `.mdd` 資源 | 37,860（35,816 字形 + 2,044 內嵌字） |
| 成品體積 | `.mdx` 1.68 MB + `.mdd` 219.6 MB |

## 功能

**字頭詞條**：標題列為字頭 + IDS 分解 + 字形總數，下方按原書頁序排列字形卡片，每張含字形圖（112×112）、器名、子字頭、時期、著錄（集成／銘圖／銘續／銘三）、分編·組號·PDF 頁·原書頁。

**構件檢索**：詞條正文之後附「構件」區，列出所有以本字為一級構件的字頭（含本字自身），20 條一頁。本身不是字頭的構件（如 `辶`、`亻`、`刂`）也獨立成詞條，只顯示構件區。

**未編碼字**：器名與字頭中含有大量沒有 Unicode 編碼的字形（2,046 個碼位），構建時預先轉成小圖嵌入正文，因此不需要安裝任何字型。

**人工標註**：上游 216 筆諧聲域／聲首／義符／詞義／備註，寫入對應字形卡片的「補註」條。

## 構建詞典

需要 Python 3.12+。

```bash
pip install -r requirements.txt

python _tools/fetch_repo.py                      # 下載上游資料（約 107 MB）
python _tools/build_mdx.py --out _build          # 產生源文本與 PNG（約 2 分鐘）
python _tools/pack.py \
    --src _build/source.txt --src _build/component.txt \
    --src _build/alias.txt --src _build/index.txt \
    --img _build/staging --out ./金文字形全編 --title "金文字形全編"
python _tools/check.py                           # 校驗
python _tools/test_build.py                      # 單元測試
```

把生成的 `.mdx` 與同名 `.mdd` 放進 GoldenDict 的詞典目錄，重新掃描詞典即可（GoldenDict 或 GoldenDict-ng 均可）。

## 校驗

構建腳本自帶校驗，成品已通過：

- 詞條內 `<img>` 引用 45,606 次，對 `.mdd` 資源缺失 **0**
- `entry://` 內部連結 9,765 次，失效 **0**
- `@@@LINK` 別名 927 條，斷鏈 **0**
- 每條詞條只有一組 `<style>`，樣式外洩 **0**；`<div>` 開閉全平衡

## 資料來源與致謝

- **上游倉庫**：[fangquinlan/jinwen-glyph-search](https://github.com/fangquinlan/jinwen-glyph-search)（字形檢索網站與整理後的資料）
- **原論文**：邱培強《金文字形全編》，碩士論文，吉林大學，2025。DOI: [10.27162/d.cnki.gjlin.2025.007505](https://doi.org/10.27162/d.cnki.gjlin.2025.007505)
- **字形圖像來源**（據原論文）：《殷周金文集成》《商周青銅器銘文暨圖像集成》及其《續編》《三編》

本倉庫與上游倉庫作者、論文作者及吉林大學均無隸屬關係，本項目僅為資料格式轉換的技術實踐。

## 使用 DeepSeek

本倉庫的資料分析、構建腳本、校驗腳本與文檔，均在 **DeepSeek** 的輔助下完成。

## 權利聲明

- 上游倉庫**沒有開源授權**，其 README 明確要求不得將資料或圖像用於超出合理引用、研究、教學之外的再發布或商業用途。
- 引用相關字形資料時，請標註原論文與相應著錄來源。
- 本倉庫的代碼部分採用 MIT 授權；該授權不涉及任何字形資料的權利。