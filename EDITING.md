# Chỉnh sửa nội dung trang EquiVLA

Toàn bộ chữ, số, bảng, ảnh, video của trang nằm trong **`content.json`**.
`index.html` là file **sinh tự động** — đừng sửa trực tiếp, sẽ bị ghi đè.

```bash
# sửa content.json rồi:
python3 build.py            # -> ghi đè index.html

python3 build.py -o preview.html   # xem thử, không đụng index.html
```

Không cần cài gì thêm (chỉ dùng thư viện chuẩn của Python 3).

## Cú pháp inline dùng trong mọi trường text

| Viết | Kết quả |
|---|---|
| `**đậm**` | **đậm** |
| `*nghiêng*` | *nghiêng* |
| `@@92.6%@@` | đậm, màu accent xanh |
| `##+18pp##` | đậm, màu xanh lá (số cải thiện) |
| `` `z^{eq}` `` | font mono màu accent, `^{...}` = superscript |
| `$...$`, `$$...$$` | công thức LaTeX (MathJax) — **không bị đụng tới** |

HTML thô cũng chèn được nếu cần trường hợp đặc biệt.

> **Lưu ý JSON:** dấu `\` trong LaTeX phải viết đôi — `\\rho`, `\\approx`, `\;`.

## Bố cục `content.json`

| Khoá | Nội dung |
|---|---|
| `theme` | Bảng màu dùng chung (`accent`, `green`, …). Đổi ở đây là đổi cả trang. |
| `nav` | Tên thương hiệu + các link trên thanh điều hướng |
| `hero` | Badge, tiêu đề, tagline, tác giả, venue, các nút |
| `stats` | 3 thẻ số liệu (số thẻ tuỳ ý, lưới tự co giãn) |
| `abstract` | Danh sách đoạn văn |
| `method`, `results` | Danh sách **block** có thứ tự — đổi thứ tự / thêm / xoá thoải mái |
| `video_section` | Video tổng quan |
| `footer` | Chân trang |

### Bật nút Paper / Code / Video

Điền `href`; nút tự chuyển từ trạng thái mờ "soon" sang link thật:

```json
{ "icon": "📄", "label": "Paper", "note": null,
  "href": "https://arxiv.org/abs/...", "variant": "primary" }
```

### Các loại block

| `type` | Dùng cho | Trường chính |
|---|---|---|
| `paragraph` | đoạn văn | `text`, `variant` (`body`/`card`/`caption`/`note`/`footnote`/`small`/`boxed`/`guarantee`), `margin_bottom` |
| `heading` | tiêu đề phụ | `text`, `size` |
| `list` | danh sách gạch đầu dòng | `items`, `color`, `margin_bottom` |
| `table` | bảng kết quả | `columns`, `rows`, `min_width`, `padding` |
| `card` | khối viền (EquiPerceptor / EquiActor) | `icon`, `title`, `subtitle`, `blocks` |
| `callout` | hộp nền xám viền xanh trái | `blocks` |
| `highlight_box` | hộp gradient xanh | `title`, `blocks` |
| `math` | công thức hiển thị riêng dòng | `tex` |
| `defs` | 2 ô định nghĩa cạnh nhau | `items[].term`, `items[].desc` |
| `figure_pdf` | nhúng PDF hình | `src`, `aspect_ratio`, `caption` |
| `task_gallery` | lưới ảnh theo task | `rows[].columns`, `rows[].items[]`, `caption` |
| `video_grid` | lưới video một task | `title`, `columns`, `videos` |

### Sửa bảng

`columns` khai báo cột, `rows` là dữ liệu — khớp nhau qua `key`:

```json
{ "key": "avg", "label": "Avg ↑", "emphasis": true }
```

Tuỳ chọn cột: `align`, `emphasis` (in đậm), `color` (`accent`/`green`),
`weight`, `style: "muted-small"`.

Tuỳ chọn dòng: `"highlight": true` (nền xanh nhạt — dòng EquiVLA),
`"total": true` (dòng Average, viền xanh đậm).

Một ô riêng lẻ có thể ghi đè:

```json
"delta": { "text": "+35pp", "bold": true }
"delta": { "text": "0pp", "muted": true }
```

## Thêm task / video mới

Thêm một phần tử vào `results.blocks`:

```json
{ "type": "video_grid", "title": "Task mới", "columns": 2,
  "videos": ["video/task_moi/episode_000001.mp4"] }
```

và một `items[]` vào `task_gallery` tương ứng. Số ảnh trong `images` quyết
định số cột của lưới ảnh nhỏ (2 ảnh → 2 cột, 3 ảnh → 3 cột).
