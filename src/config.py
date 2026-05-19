"""
config.py
---------
File cấu hình tập trung cho toàn bộ project Caro AI.

Ý tưởng chính:
- Muốn đổi kích thước bàn, độ sâu AI, thời gian suy nghĩ, màu sắc hoặc bố cục
  thì chỉ sửa ở đây.
- Các file khác import cấu hình từ file này để tránh sửa nhiều nơi.
"""

# ============================================================
# CẤU HÌNH BÀN CỜ
# ============================================================

BOARD_SIZE = 11                 # Có thể đổi thành 15 nếu muốn bàn 15x15.
WIN_LENGTH = 4                  # Đề yêu cầu 4 quân liên tiếp là thắng.
CELL_SIZE = 45                  # Ô cờ cố định; phóng to cửa sổ chỉ căn giữa layout.

# ============================================================
# CẤU HÌNH AI
# ============================================================

AI_DEPTH = 4                        # Độ sâu nền: AI chắc chắn cố hoàn thành ít nhất mức này nếu còn thời gian.
AI_ITERATIVE_MAX_DEPTH = 8          # Iterative Deepening sẽ thử tăng dần đến độ sâu này hoặc dừng khi hết giờ.
AI_MIN_COMPLETED_DEPTH = 3          # Không đánh vội: cố hoàn thành tối thiểu depth 3, trừ khi hết 15s hoặc có thắng/chặn thắng ngay.
ENABLE_ITERATIVE_DEEPENING = True   # Cho phép AI tìm depth 1 -> 2 -> 3... trong giới hạn thời gian.
AI_TIME_LIMIT = 15                  # Mỗi nước AI nghĩ tối đa 15 giây.
AI_MIN_THINK_TIME = 7.0             # AI cố suy nghĩ ít nhất 7 giây để tận dụng thời gian và hoàn thành độ sâu tối thiểu.
AI_STATS_UPDATE_INTERVAL = 0.10     # Giới hạn tần suất cập nhật UI từ AI để pygame không bị giật.
SEARCH_RADIUS = 2                   # Chỉ xét ô trống gần quân đã đánh trong bán kính này.
MAX_CANDIDATE_MOVES = 42            # Giữ đủ nước ứng viên nhưng tránh quá rộng làm giảm độ sâu.
WIN_SCORE = 1_000_000

# Trọng số chiến thuật. Bản v6 ưu tiên phòng thủ mạnh hơn tấn công,
# vì người chơi thường dùng nước giả / nước mồi để tạo nước đôi.
DEFENSE_WEIGHT = 1.35               # Không để AI phòng thủ quá mức.
ATTACK_WEIGHT = 2.20                # Ưu tiên tấn công khi có thế 3/thế ép rõ ràng.
FORK_THREAT_SCORE = 320_000
OPEN_THREE_SCORE = 230_000
CLOSED_THREE_SCORE = 100_000
OPEN_TWO_SCORE = 2_500
ANTI_FORK_SCORE = 360_000           # Điểm ưu tiên cho nước làm giảm nguy cơ người tạo nước đôi sau 1-2 nước.
COUNTER_ATTACK_BONUS = 180_000      # Điểm thưởng cho nước vừa chặn vừa tạo threat mạnh cho AI.


# Cấu hình benchmark riêng để chạy thực nghiệm nhanh hơn.
BENCHMARK_DEPTH = 3
BENCHMARK_TIME_LIMIT = 999

# ============================================================
# GIÁ TRỊ QUÂN CỜ
# ============================================================

EMPTY = 0
PLAYER_X = 1
PLAYER_O = 2

PLAYER_NAMES = {
    PLAYER_X: "X",
    PLAYER_O: "O",
}

# ============================================================
# CỬA SỔ VÀ BỐ CỤC
# ============================================================

WINDOW_WIDTH = 1300
WINDOW_HEIGHT = 600
PANEL_WIDTH = 420
MARGIN = 35
HISTORY_HEIGHT = 0

MIN_WINDOW_WIDTH = BOARD_SIZE * CELL_SIZE + PANEL_WIDTH + MARGIN * 4 + 260
MIN_WINDOW_HEIGHT = BOARD_SIZE * CELL_SIZE + MARGIN * 3 + 80

EVAL_BOX_WIDTH = 190
EVAL_BOX_HEIGHT = 78
MOVE_LIST_WIDTH = 230
FPS = 60                         # FPS giao diện; tăng lên 60 để màn hình mượt hơn khi AI chạy thread.
MOVE_LIST_HEIGHT = 300

# ============================================================
# FONT CHỮ
# ============================================================

# Ưu tiên các font phổ biến trên Windows, nét dễ nhìn và hỗ trợ tiếng Việt.
# Arial/Tahoma thường nhìn rõ trong pygame hơn Segoe UI ở nhiều máy.
FONT_CANDIDATES = ["Arial", "Tahoma", "Verdana", "Segoe UI", "Calibri", "DejaVu Sans"]

# Đường dẫn font ưu tiên. Cách này xử lý tốt lỗi pygame render sai tiếng Việt
# trên Windows khi SysFont tự chọn nhầm font không đủ dấu.
FONT_PATHS = {
    "regular": [
        r"C:/Windows/Fonts/arial.ttf",
        r"C:/Windows/Fonts/tahoma.ttf",
        r"C:/Windows/Fonts/segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ],
    "bold": [
        r"C:/Windows/Fonts/arialbd.ttf",
        r"C:/Windows/Fonts/tahomabd.ttf",
        r"C:/Windows/Fonts/segoeuib.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ],
}

# ============================================================
# MÀU SẮC
# ============================================================

BACKGROUND_COLOR = (255, 255, 255)
BOARD_COLOR = (255, 255, 255)
GRID_COLOR = (35, 35, 35)

X_COLOR = (220, 40, 40)       # X màu đỏ.
O_COLOR = (20, 115, 220)      # O màu xanh lam.

TEXT_COLOR = (20, 24, 35)
MUTED_TEXT_COLOR = (100, 105, 115)
BORDER_COLOR = (210, 218, 230)
PANEL_BG_COLOR = (255, 255, 255)
ROW_ALT_COLOR = (246, 248, 251)
BLUE_COLOR = (20, 115, 220)
GREEN_COLOR = (20, 150, 75)
ORANGE_COLOR = (225, 140, 20)
RED_COLOR = (220, 40, 40)
GRAY_COLOR = (150, 150, 150)

BUTTON_BG_COLOR = (255, 255, 255)
BUTTON_BORDER_COLOR = (20, 115, 220)
BUTTON_TEXT_COLOR = (20, 115, 220)

# Màu nền phụ để trực quan hóa nước đi.
LAST_MOVE_BG_COLOR = (210, 245, 215)      # Xanh lá nhạt: ô vừa được đánh.
AI_THINKING_BG_COLOR = (238, 224, 255)    # Tím nhạt: ô AI đang xét trong lúc suy nghĩ.
MOVE_LIST_BG_COLOR = (250, 252, 255)      # Nền khung lượt đi bên trái.

# ============================================================
# NGƯỠNG XẾP LOẠI NƯỚC ĐI
# ============================================================

MOVE_VERY_GOOD = 150
MOVE_GOOD = 60
MOVE_NORMAL_LOW = -40
MOVE_BAD = -120

# ============================================================
# Hàm: get_board_pixel_size()
# Mục đích:
#   - Tính kích thước bàn cờ theo pixel.
#
# Kiến thức sử dụng:
#   - Tính layout dựa trên cấu hình tập trung.
#
# Tham số:
#   - Không có.
#
# Giá trị trả về:
#   - BOARD_SIZE * CELL_SIZE.
# ============================================================
def get_board_pixel_size():
    return BOARD_SIZE * CELL_SIZE
