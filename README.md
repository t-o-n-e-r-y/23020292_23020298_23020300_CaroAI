# Caro AI

## 1\. Giới thiệu

Đây là chương trình chơi cờ Caro bằng Python và pygame. Chương trình hỗ trợ:

* Người chơi đấu với người chơi.
* Người chơi đấu với máy.
* Máy chọn nước đi bằng Minimax hoặc Alpha-Beta pruning.
* Bàn cờ cấu hình được trong `src/config.py`, ví dụ 11x11 hoặc 15x15.
* Luật thắng 4 quân liên tiếp, không xét luật chặn hai đầu.
* Hiển thị thông tin AI: số trạng thái đã xét, số nhánh bị cắt, thời gian chạy, nước ứng viên, nước đang xét và nước tốt nhất.
* Hiển thị điểm Evaluation hiện tại và nhật ký đánh giá nước đi.

## 2\. Cài đặt

Mở terminal trong thư mục project và chạy:

```bash
pip install -r requirements.txt
```

## 3\. Chạy game

```bash
python src/main.py
```

Ở màn hình Ván mới, chọn:

* Chơi với Người hoặc Máy.
* Nếu chơi với Máy, chọn người đi trước hoặc máy đi trước.
* Chọn thuật toán Minimax hoặc Alpha-Beta.

## 4\. Chạy benchmark

```bash
python src/benchmark.py
```

File benchmark sẽ chạy Minimax và Alpha-Beta trên nhiều trạng thái bàn cờ khác nhau, sau đó in ra bảng kết quả gồm:

* Trạng thái test.
* Thuật toán.
* Độ sâu.
* Nước đi được chọn.
* Điểm đánh giá.
* Số trạng thái đã xét.
* Số nhánh bị cắt.
* Thời gian chạy.

## 5\. Cấu hình quan trọng

Các tham số chính nằm trong `src/config.py`:

```python
BOARD\\\_SIZE = 11
WIN\\\_LENGTH = 4
CELL\\\_SIZE = 50
AI\\\_DEPTH = 3
AI\\\_TIME\\\_LIMIT = 15
SEARCH\\\_RADIUS = 2
MAX\\\_CANDIDATE\\\_MOVES = 20
```

Ý nghĩa:

* `BOARD\\\_SIZE`: kích thước bàn cờ, có thể đổi thành 15.
* `WIN\\\_LENGTH`: số quân liên tiếp để thắng, theo đề là 4.
* `CELL\\\_SIZE`: độ rộng mỗi ô cờ.
* `AI\\\_DEPTH`: độ sâu tìm kiếm của AI.
* `AI\\\_TIME\\\_LIMIT`: thời gian tối đa AI suy nghĩ mỗi nước.
* `SEARCH\\\_RADIUS`: phạm vi AI xét nước đi quanh các ô đã có quân.
* `MAX\\\_CANDIDATE\\\_MOVES`: số nước ứng viên tối đa AI xét ở mỗi tầng để giảm thời gian chạy.

## 6\. Cấu trúc thư mục

```text
src/
├── main.py          # giao diện pygame, menu, bàn cờ, panel AI, nhật ký đánh giá
├── config.py        # cấu hình toàn bộ project
├── game.py          # luật chơi, kiểm tra thắng/hòa, sinh nước đi
├── ai.py            # Minimax, Alpha-Beta, thống kê AI
├── evaluation.py    # hàm đánh giá bàn cờ và nhật ký điểm
└── benchmark.py     # thực nghiệm so sánh thuật toán
```

## 

