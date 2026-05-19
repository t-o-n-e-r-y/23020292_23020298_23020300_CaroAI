"""
main.py
-------
File chạy chính của chương trình Caro AI.

Nhiệm vụ:
- Tạo giao diện bằng pygame.
- Hiển thị menu chọn chế độ chơi.
- Vẽ bàn cờ, X đỏ, O xanh lam.
- Hiển thị panel thông tin AI bên phải.
- Hiển thị ô điểm Eval nổi bật ở góc trái.
- Hiển thị khung lượt đi bên trái; bỏ bảng nhật ký điểm phía dưới để giao diện gọn hơn.
- Gọi AI khi đến lượt máy.
"""

import sys
import os
import threading
import pygame

try:
    from .config import *
except ImportError:
    from config import *
try:
    from .game import (
    create_board,
    copy_board,
    make_move,
    undo_move,
    is_valid_move,
    get_game_result,
    switch_player,
    PLAYER_X,
    PLAYER_O,
    PLAYER_NAMES,
)
    from .ai import get_ai_move, create_ai_stats
    from .evaluation import evaluate_board, build_eval_history_entry, format_score
except ImportError:
    from game import (
        create_board,
        copy_board,
        make_move,
        undo_move,
        is_valid_move,
        get_game_result,
        switch_player,
        PLAYER_X,
        PLAYER_O,
        PLAYER_NAMES,
    )
    from ai import get_ai_move, create_ai_stats
    from evaluation import evaluate_board, build_eval_history_entry, format_score


# ============================================================
# Hàm: get_color_by_name(color_name)
# Mục đích:
#   - Chuyển tên màu dùng trong nhật ký đánh giá thành mã màu RGB.
#
# Kiến thức sử dụng:
#   - Ánh xạ dữ liệu mức đánh giá sang màu hiển thị trên giao diện.
#
# Tham số:
#   - color_name: chuỗi tên màu như "green", "blue", "orange", "red".
#
# Giá trị trả về:
#   - Tuple màu RGB.
# ============================================================
def get_color_by_name(color_name):
    if color_name == "green":
        return GREEN_COLOR
    if color_name == "blue":
        return BLUE_COLOR
    if color_name == "red":
        return RED_COLOR
    if color_name == "orange":
        return ORANGE_COLOR
    return TEXT_COLOR


# ============================================================
# Hàm: draw_text(surface, text, font, color, pos, center=False)
# Mục đích:
#   - Hàm tiện ích để vẽ chữ lên màn hình.
#
# Kiến thức sử dụng:
#   - pygame.font render chữ thành surface rồi blit lên màn hình.
#
# Tham số:
#   - surface: màn hình hoặc vùng vẽ.
#   - text: nội dung cần vẽ.
#   - font: font chữ.
#   - color: màu chữ.
#   - pos: tọa độ vẽ.
#   - center: nếu True thì pos là tâm của chữ.
#
# Giá trị trả về:
#   - Rect của chữ sau khi vẽ, dùng để kiểm tra click nếu cần.
# ============================================================
def draw_text(surface, text, font, color, pos, center=False):
    text_surface = font.render(str(text), True, color)
    rect = text_surface.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    surface.blit(text_surface, rect)
    return rect


# ============================================================
# Hàm: format_move_display(move)
# Mục đích:
#   - Chuyển tọa độ nội bộ dạng chỉ số mảng 0-based thành dạng người dùng 1-based.
#   - Ví dụ: (4, 5) trong code sẽ hiển thị thành (5, 6).
#
# Kiến thức sử dụng:
#   - Trong Python list dùng chỉ số từ 0, còn người chơi thường đọc bàn cờ từ 1.
#
# Tham số:
#   - move: tuple (row, col), chuỗi trạng thái, hoặc None.
#
# Giá trị trả về:
#   - Chuỗi đã format để hiển thị trên giao diện.
# ============================================================
def format_move_display(move):
    if move is None:
        return "--"
    if isinstance(move, str):
        return move
    if isinstance(move, (tuple, list)) and len(move) == 2:
        return f"({move[0] + 1}, {move[1] + 1})"
    return str(move)


# ============================================================
# Hàm: get_last_move(state)
# Mục đích:
#   - Lấy nước đi cuối cùng trong lịch sử để tô nền xanh lá nhạt.
#
# Giá trị trả về:
#   - Tuple (row, col) hoặc None nếu chưa có nước đi.
# ============================================================
def get_last_move(state):
    if not state.get("move_history"):
        return None
    return state["move_history"][-1].get("move")


# ============================================================
# Hàm: get_ai_current_thinking_move(state)
# Mục đích:
#   - Lấy ô AI đang xét hiện tại để tô tím nhạt trên bàn cờ.
#   - Dữ liệu này được cập nhật từ luồng AI thông qua dict ai_stats dùng chung.
# ============================================================
def get_ai_current_thinking_move(state):
    if not state.get("ai_thinking"):
        return None
    move = state.get("ai_stats", {}).get("current_move")
    if isinstance(move, (tuple, list)) and len(move) == 2:
        return tuple(move)
    return None


# ============================================================
# Hàm: draw_round_rect(surface, rect, fill, border=None, radius=10, width=1)
# Mục đích:
#   - Vẽ một hình chữ nhật bo góc dùng cho panel, badge, button.
#
# Kiến thức sử dụng:
#   - pygame.draw.rect với border_radius để tạo giao diện hiện đại.
#
# Tham số:
#   - surface: màn hình cần vẽ.
#   - rect: pygame.Rect.
#   - fill: màu nền.
#   - border: màu viền, có thể None.
#   - radius: độ bo góc.
#   - width: độ dày viền.
#
# Giá trị trả về:
#   - Không trả về.
# ============================================================
def draw_round_rect(surface, rect, fill, border=None, radius=10, width=1):
    pygame.draw.rect(surface, fill, rect, border_radius=radius)
    if border:
        pygame.draw.rect(surface, border, rect, width, border_radius=radius)


# ============================================================
# Hàm: init_fonts()
# Mục đích:
#   - Khởi tạo các font dùng trong giao diện.
#
# Kiến thức sử dụng:
#   - Quản lý nhiều kích thước font để giao diện dễ đọc.
#
# Tham số:
#   - Không có.
#
# Giá trị trả về:
#   - dict chứa các font.
# ============================================================
def init_fonts():
    # Ưu tiên load trực tiếp file font .ttf để pygame render tiếng Việt đúng dấu.
    # Trên một số máy, pygame.font.SysFont("Arial") vẫn có thể rơi về font fallback
    # không đủ dấu, làm chữ thành "Lut bn", "Ván mi". Vì vậy bản này kiểm tra
    # C:/Windows/Fonts trước, rồi mới fallback sang SysFont.
    def get_font(size, bold=False):
        font_group = FONT_PATHS["bold"] if bold else FONT_PATHS["regular"]
        for font_path in font_group:
            if os.path.exists(font_path):
                return pygame.font.Font(font_path, size)

        for name in FONT_CANDIDATES:
            matched = pygame.font.match_font(name, bold=bold)
            if matched:
                return pygame.font.Font(matched, size)

        # Fallback cuối cùng. Thường chỉ dùng khi máy thiếu toàn bộ font phổ biến.
        return pygame.font.SysFont("Arial", size, bold=bold)

    return {
        "title": get_font(28, bold=True),
        "big": get_font(28, bold=True),
        "eval_label": get_font(16, bold=True),
        "eval_value": get_font(23, bold=True),
        "medium": get_font(20),
        "medium_bold": get_font(20, bold=True),
        "small": get_font(16),
        "small_bold": get_font(16, bold=True),
        "history": get_font(16),
        "history_bold": get_font(16, bold=True),
        "piece": get_font(int(CELL_SIZE * 0.70), bold=True),
    }


# ============================================================
# Hàm: init_game_state()
# Mục đích:
#   - Tạo trạng thái ban đầu của game.
#
# Kiến thức sử dụng:
#   - Gom toàn bộ dữ liệu động của game vào một dict để dễ truyền qua các hàm.
#
# Tham số:
#   - Không có.
#
# Giá trị trả về:
#   - state: dict chứa trạng thái game.
# ============================================================
def init_game_state():
    return {
        "screen": "menu",
        "board": create_board(),
        "mode": "pve",
        "algorithm": "alphabeta",
        "first": "human",
        "current_player": PLAYER_X,
        "human_player": PLAYER_X,
        "ai_player": PLAYER_O,
        "game_over": False,
        "winner": None,
        "move_history": [],
        "eval_history": [],
        "history_scroll": 0,
        "current_eval": 0,
        "ai_stats": create_ai_stats("alphabeta"),
        "ai_stats_lock": threading.Lock(),
        "ai_thinking": False,
        "ai_thread": None,
        "ai_result": None,
        "ai_score_before": 0,
        "message": "",
        "buttons": {},
    }


# ============================================================
# Hàm: setup_new_game(state)
# Mục đích:
#   - Thiết lập lại bàn cờ theo lựa chọn ở menu.
#
# Kiến thức sử dụng:
#   - Quản lý chế độ người-người và người-máy.
#   - Xác định quân của người và AI theo lựa chọn ai đi trước.
#
# Tham số:
#   - state: trạng thái game.
#
# Giá trị trả về:
#   - Không trả về, cập nhật trực tiếp state.
# ============================================================
def setup_new_game(state):
    state["board"] = create_board()
    state["game_over"] = False
    state["winner"] = None
    state["move_history"] = []
    state["eval_history"] = []
    state["history_scroll"] = 0
    state["ai_stats"] = create_ai_stats(state["algorithm"])
    state["ai_thinking"] = False
    state["ai_thread"] = None
    state["ai_result"] = None
    state["ai_score_before"] = 0
    state["message"] = ""

    if state["mode"] == "pve":
        if state["first"] == "ai":
            state["ai_player"] = PLAYER_X
            state["human_player"] = PLAYER_O
            state["current_player"] = PLAYER_X
        else:
            state["human_player"] = PLAYER_X
            state["ai_player"] = PLAYER_O
            state["current_player"] = PLAYER_X
        state["current_eval"] = evaluate_board(state["board"], state["ai_player"], state["human_player"])
    else:
        state["current_player"] = PLAYER_X
        state["current_eval"] = 0

    state["screen"] = "game"


# ============================================================
# Hàm: calculate_layout(window_width, window_height)
# Mục đích:
#   - Tính vị trí bàn cờ, panel AI và bảng nhật ký dựa trên kích thước cửa sổ.
#   - CELL_SIZE giữ cố định, khi phóng to cửa sổ thì cụm giao diện được căn giữa.
#
# Kiến thức sử dụng:
#   - Tính toán layout cố định nhưng căn giữa theo cửa sổ.
#
# Tham số:
#   - window_width: chiều rộng cửa sổ.
#   - window_height: chiều cao cửa sổ.
#
# Giá trị trả về:
#   - dict chứa tọa độ và kích thước các vùng giao diện.
# ============================================================
def calculate_layout(window_width, window_height):
    board_px = BOARD_SIZE * CELL_SIZE
    top_bar_height = 50
    left_status_width = 230

    main_content_width = left_status_width + MARGIN + board_px + MARGIN + PANEL_WIDTH
    main_content_height = board_px

    start_x = max(MARGIN, (window_width - main_content_width) // 2)
    start_y = max(top_bar_height + MARGIN, (window_height - main_content_height + top_bar_height) // 2)

    status_x = start_x
    status_y = start_y
    board_x = status_x + left_status_width + MARGIN
    board_y = start_y
    panel_x = board_x + board_px + MARGIN
    panel_y = board_y

    history_x = start_x
    history_y = board_y + board_px + MARGIN
    history_w = main_content_width

    return {
        "top_bar_height": top_bar_height,
        "status_x": status_x,
        "status_y": status_y,
        "board_x": board_x,
        "board_y": board_y,
        "board_size_px": board_px,
        "panel_x": panel_x,
        "panel_y": panel_y,
        "panel_width": PANEL_WIDTH,
        "panel_height": board_px,
        "history_x": history_x,
        "history_y": history_y,
        "history_width": history_w,
        "history_height": HISTORY_HEIGHT,
    }


# ============================================================
# Hàm: draw_top_bar(screen, fonts, width)
# Mục đích:
#   - Vẽ thanh tiêu đề trên cùng của ứng dụng.
#
# Kiến thức sử dụng:
#   - Tạo giao diện desktop đơn giản bằng pygame.
#
# Tham số:
#   - screen: màn hình pygame.
#   - fonts: dict font.
#   - width: chiều rộng cửa sổ.
#
# Giá trị trả về:
#   - Không trả về.
# ============================================================
def draw_top_bar(screen, fonts, width):
    pygame.draw.line(screen, BORDER_COLOR, (0, 50), (width, 50), 1)
    draw_text(screen, "Menu", fonts["small_bold"], TEXT_COLOR, (36, 25), center=True)
    draw_text(screen, "Caro AI", fonts["title"], TEXT_COLOR, (width // 2, 25), center=True)
    draw_text(screen, "-    □    ×", fonts["medium_bold"], TEXT_COLOR, (width - 120, 25), center=True)


# ============================================================
# Hàm: draw_top_status(screen, state, layout, fonts)
# Mục đích:
#   - Vẽ ô hiển thị lượt hiện tại và ô Eval ở góc trái.
#
# Kiến thức sử dụng:
#   - Hiển thị trạng thái trò chơi trực quan cho người chơi.
#   - Eval giúp biết thế cờ đang nghiêng về AI hay người.
#
# Tham số:
#   - screen: màn hình pygame.
#   - state: trạng thái game.
#   - layout: tọa độ giao diện.
#   - fonts: dict font.
#
# Giá trị trả về:
#   - Không trả về.
# ============================================================
def draw_top_status(screen, state, layout, fonts):
    x = layout["status_x"]
    y = layout["status_y"]

    if state["mode"] == "pve":
        is_ai_turn = state["current_player"] == state["ai_player"] and not state["game_over"]
        turn_text = "Lượt AI" if is_ai_turn else "Lượt bạn"
    else:
        turn_text = f"Lượt {PLAYER_NAMES[state['current_player']]}"

    turn_rect = pygame.Rect(x, y, 110, 34)
    draw_round_rect(screen, turn_rect, PANEL_BG_COLOR, BORDER_COLOR, 7)
    pygame.draw.circle(screen, BLUE_COLOR, (x + 18, y + 17), 7)
    draw_text(screen, turn_text, fonts["small_bold"], BLUE_COLOR, (x + 36, y + 8))

    eval_rect = pygame.Rect(x, y + 48, EVAL_BOX_WIDTH, EVAL_BOX_HEIGHT)
    draw_round_rect(screen, eval_rect, PANEL_BG_COLOR, (120, 170, 255), 8)

    # Ô Eval được tách thành 2 dòng để không bị vỡ giao diện khi điểm heuristic lớn.
    # Dòng 1 là nhãn, dòng 2 là điểm rút gọn hoặc kết quả ván.
    if state["mode"] == "pvp":
        eval_value = "--"
    elif state["game_over"]:
        if state["winner"] == state.get("ai_player"):
            eval_value = "AI thắng"
        elif state["winner"] == state.get("human_player"):
            eval_value = "Bạn thắng"
        else:
            eval_value = "Hòa"
    else:
        eval_value = format_score(state["current_eval"])

    draw_text(screen, "Eval", fonts["eval_label"], BLUE_COLOR, (eval_rect.centerx, eval_rect.y + 18), center=True)
    draw_text(screen, eval_value, fonts["eval_value"], BLUE_COLOR, (eval_rect.centerx, eval_rect.y + 49), center=True)


# ============================================================
# Hàm: draw_move_list_panel(screen, state, layout, fonts)
# Mục đích:
#   - Vẽ bảng nhỏ bên trái hiển thị lịch sử lượt đi gần nhất.
#   - Mỗi dòng cho biết X/O đi ô nào và điểm tác động của nước đi đó.
#
# Kiến thức sử dụng:
#   - Lưu vết nước đi giúp người chơi kiểm tra lại diễn biến ván cờ.
#   - Điểm hiển thị lấy từ nhật ký evaluation, còn tọa độ được đổi sang hệ 1-based.
#
# Tham số:
#   - screen, state, layout, fonts: dữ liệu giao diện và trạng thái game.
#
# Giá trị trả về:
#   - Không trả về.
# ============================================================
def draw_move_list_panel(screen, state, layout, fonts):
    x = layout["status_x"]
    y = layout["status_y"] + 140
    rect = pygame.Rect(x, y, MOVE_LIST_WIDTH, MOVE_LIST_HEIGHT)
    draw_round_rect(screen, rect, MOVE_LIST_BG_COLOR, BORDER_COLOR, 8)

    draw_text(screen, "LƯỢT ĐI", fonts["small_bold"], TEXT_COLOR, (x + 14, y + 12))
    pygame.draw.line(screen, BORDER_COLOR, (x + 14, y + 38), (rect.right - 14, y + 38), 1)

    # Chỉ hiện vài nước cuối để bảng gọn, còn bảng dưới vẫn giữ nhật ký đầy đủ.
    moves = state.get("move_history", [])[-8:]
    start_turn = max(1, len(state.get("move_history", [])) - len(moves) + 1)
    row_y = y + 50
    for idx, item in enumerate(moves):
        turn = start_turn + idx
        player = item.get("player")
        move = item.get("move")
        piece = PLAYER_NAMES.get(player, "?")
        piece_color = X_COLOR if player == PLAYER_X else O_COLOR

        # Điểm nước đi lấy từ eval_history nếu đang chơi với máy.
        score_text = ""
        score_color = MUTED_TEXT_COLOR
        if state.get("mode") == "pve" and len(state.get("eval_history", [])) >= turn:
            entry = state["eval_history"][turn - 1]
            score_text = format_score(entry.get("player_impact", 0))
            if entry.get("player_impact", 0) >= 0:
                score_color = GREEN_COLOR
            else:
                score_color = RED_COLOR

        draw_text(screen, f"{turn}.", fonts["history"], MUTED_TEXT_COLOR, (x + 12, row_y))
        draw_text(screen, piece, fonts["history_bold"], piece_color, (x + 44, row_y))
        draw_text(screen, format_move_display(move), fonts["history"], TEXT_COLOR, (x + 78, row_y))
        if score_text:
            draw_text(screen, score_text, fonts["history"], score_color, (x + 158, row_y))
        row_y += 28


# ============================================================
# Hàm: draw_board(screen, board, layout, fonts)
# Mục đích:
#   - Vẽ bàn cờ, số hàng/cột, các điểm sao và quân X/O.
#
# Kiến thức sử dụng:
#   - Vẽ lưới bằng pygame.draw.line.
#   - Biểu diễn trạng thái bàn cờ bằng giao diện trực quan.
#
# Tham số:
#   - screen: màn hình pygame.
#   - board: bàn cờ hiện tại.
#   - layout: tọa độ bàn cờ.
#   - fonts: dict font.
#
# Giá trị trả về:
#   - Không trả về.
# ============================================================
def draw_board(screen, board, layout, fonts, state=None):
    x = layout["board_x"]
    y = layout["board_y"]
    board_px = layout["board_size_px"]

    pygame.draw.rect(screen, BOARD_COLOR, (x, y, board_px, board_px))

    # Vẽ số cột và số hàng.
    for i in range(BOARD_SIZE):
        draw_text(screen, str(i + 1), fonts["small"], TEXT_COLOR, (x + i * CELL_SIZE + CELL_SIZE // 2, y - 18), center=True)
        draw_text(screen, str(i + 1), fonts["small"], TEXT_COLOR, (x - 18, y + i * CELL_SIZE + CELL_SIZE // 2), center=True)

    # Vẽ lưới.
    for i in range(BOARD_SIZE + 1):
        pygame.draw.line(screen, GRID_COLOR, (x, y + i * CELL_SIZE), (x + board_px, y + i * CELL_SIZE), 1)
        pygame.draw.line(screen, GRID_COLOR, (x + i * CELL_SIZE, y), (x + i * CELL_SIZE, y + board_px), 1)

    # Không vẽ điểm sao trên bàn cờ để giao diện sạch và đúng yêu cầu người dùng.

    # Tô nền xanh lá nhạt cho ô vừa đi và tím nhạt cho ô AI đang xét.
    # Nền được vẽ sau lưới, sau đó vẽ lại viền ô để vẫn nhìn rõ đường kẻ.
    if state is not None:
        last_move = get_last_move(state)
        thinking_move = get_ai_current_thinking_move(state)
        for move, color in [(last_move, LAST_MOVE_BG_COLOR), (thinking_move, AI_THINKING_BG_COLOR)]:
            if move is None:
                continue
            r, c = move
            if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
                cell_rect = pygame.Rect(x + c * CELL_SIZE + 1, y + r * CELL_SIZE + 1, CELL_SIZE - 1, CELL_SIZE - 1)
                pygame.draw.rect(screen, color, cell_rect)
                pygame.draw.rect(screen, GRID_COLOR, (x + c * CELL_SIZE, y + r * CELL_SIZE, CELL_SIZE, CELL_SIZE), 1)

    # Vẽ quân cờ.
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if board[row][col] != EMPTY:
                draw_piece(screen, row, col, board[row][col], layout, fonts)


# ============================================================
# Hàm: draw_piece(screen, row, col, player, layout, fonts)
# Mục đích:
#   - Vẽ quân cờ tại một ô dưới dạng chữ X đỏ hoặc O xanh lam.
#
# Kiến thức sử dụng:
#   - Biểu diễn quân cờ bằng ký hiệu thay vì hình tròn.
#
# Tham số:
#   - screen: màn hình pygame.
#   - row, col: vị trí quân.
#   - player: PLAYER_X hoặc PLAYER_O.
#   - layout: tọa độ bàn cờ.
#   - fonts: dict font.
#
# Giá trị trả về:
#   - Không trả về.
# ============================================================
def draw_piece(screen, row, col, player, layout, fonts):
    x = layout["board_x"] + col * CELL_SIZE + CELL_SIZE // 2
    y = layout["board_y"] + row * CELL_SIZE + CELL_SIZE // 2
    if player == PLAYER_X:
        draw_text(screen, "X", fonts["piece"], X_COLOR, (x, y), center=True)
    else:
        draw_text(screen, "O", fonts["piece"], O_COLOR, (x, y), center=True)


# ============================================================
# Hàm: screen_to_board_pos(mouse_pos, layout)
# Mục đích:
#   - Chuyển tọa độ chuột thành tọa độ hàng/cột trên bàn cờ.
#
# Kiến thức sử dụng:
#   - Chuyển đổi hệ tọa độ màn hình sang hệ tọa độ ma trận.
#
# Tham số:
#   - mouse_pos: tuple (x, y) của chuột.
#   - layout: tọa độ bàn cờ.
#
# Giá trị trả về:
#   - (row, col) nếu click trong bàn cờ.
#   - None nếu click ngoài bàn cờ.
# ============================================================
def screen_to_board_pos(mouse_pos, layout):
    mx, my = mouse_pos
    x = layout["board_x"]
    y = layout["board_y"]
    board_px = layout["board_size_px"]

    if not (x <= mx < x + board_px and y <= my < y + board_px):
        return None

    col = (mx - x) // CELL_SIZE
    row = (my - y) // CELL_SIZE
    return int(row), int(col)


# ============================================================
# Hàm: draw_ai_panel(screen, state, layout, fonts)
# Mục đích:
#   - Vẽ panel thông tin AI ở bên phải bàn cờ.
#
# Kiến thức sử dụng:
#   - Trực quan hóa thông tin thuật toán: node, cutoffs, thời gian, độ sâu.
#
# Tham số:
#   - screen: màn hình pygame.
#   - state: trạng thái game.
#   - layout: tọa độ panel.
#   - fonts: dict font.
#
# Giá trị trả về:
#   - Không trả về.
# ============================================================
def draw_ai_panel(screen, state, layout, fonts):
    panel_rect = pygame.Rect(layout["panel_x"], layout["panel_y"], layout["panel_width"], layout["panel_height"])
    draw_round_rect(screen, panel_rect, PANEL_BG_COLOR, BORDER_COLOR, 10)

    x = panel_rect.x + 22
    y = panel_rect.y + 24
    draw_text(screen, "THÔNG TIN AI", fonts["medium_bold"], TEXT_COLOR, (x, y))
    pygame.draw.line(screen, BORDER_COLOR, (x, y + 34), (panel_rect.right - 22, y + 34), 1)

    # Copy stats ra một dict riêng trước khi vẽ để tránh luồng AI cập nhật giữa lúc pygame render.
    # Cách này giúp giao diện ổn định hơn, giảm hiện tượng nháy/đen khi AI đang tìm sâu.
    stats = dict(state.get("ai_stats", {}))
    if state.get("ai_thinking") and not stats.get("current_move"):
        stats["current_move"] = "Đang tính..."

    depth_done = stats.get("completed_depth", 0)
    depth_current = stats.get("current_depth", stats.get("depth", AI_DEPTH))
    depth_max = stats.get("max_depth", AI_ITERATIVE_MAX_DEPTH)

    rows = [
        ("Thuật toán", stats.get("algorithm", "--")),
        ("Độ sâu cấu hình", stats.get("configured_depth", AI_DEPTH)),
        ("Độ sâu hoàn thành", depth_done),
        ("Độ sâu đang xét", depth_current),
        ("Độ sâu tối đa", depth_max),
        ("Thời gian", f"{stats.get('time', 0.0):.2f}s"),
        ("Thời gian tối thiểu", f"{stats.get('min_think_time', AI_MIN_THINK_TIME):.1f}s"),
        ("Trạng thái đã xét", stats.get("nodes", 0)),
        ("Nhánh bị cắt", stats.get("cutoffs", 0)),
        ("Nước ứng viên", stats.get("candidate_moves", 0)),
        ("AI đang suy nghĩ", format_move_display(stats.get("current_move") or "--")),
        ("Nước tốt nhất hiện tại", format_move_display(stats.get("best_move") or "--")),
    ]

    row_y = y + 60
    row_gap = 30 if BOARD_SIZE <= 11 else 28
    colon_x = panel_rect.x + 220
    value_x = panel_rect.x + 245
    for label, value in rows:
        draw_text(screen, label, fonts["small"], TEXT_COLOR, (x, row_y))
        draw_text(screen, ":", fonts["small"], TEXT_COLOR, (colon_x, row_y))
        draw_text(screen, str(value), fonts["small"], TEXT_COLOR, (value_x, row_y))
        row_y += row_gap

    # Nút Ván mới và Đi lại.
    # Đặt nút theo kích thước panel thay vì tọa độ cứng để không bị vỡ khi đổi BOARD_SIZE.
    button_y = min(panel_rect.bottom - 62, row_y + 28)
    button_width = max(120, (panel_rect.width - 70) // 2)
    button_height = 42
    new_btn = pygame.Rect(panel_rect.x + 24, button_y, button_width, button_height)
    undo_btn = pygame.Rect(new_btn.right + 22, button_y, button_width, button_height)
    state["buttons"]["new_game"] = new_btn
    state["buttons"]["undo"] = undo_btn

    draw_round_rect(screen, new_btn, BUTTON_BG_COLOR, BUTTON_BORDER_COLOR, 8, 2)
    draw_text(screen, "Ván mới", fonts["small_bold"], BUTTON_TEXT_COLOR, new_btn.center, center=True)

    draw_round_rect(screen, undo_btn, BUTTON_BG_COLOR, BUTTON_BORDER_COLOR, 8, 2)
    draw_text(screen, "Đi lại", fonts["small_bold"], BUTTON_TEXT_COLOR, undo_btn.center, center=True)


# ============================================================
# Hàm: draw_eval_history_panel(screen, state, layout, fonts)
# Mục đích:
#   - Vẽ bảng nhật ký điểm đánh giá phía dưới.
#
# Kiến thức sử dụng:
#   - Lưu lịch sử điểm trước/sau mỗi nước đi để phân tích hành vi.
#   - Giao diện dạng bảng có thanh cuộn.
#
# Tham số:
#   - screen: màn hình pygame.
#   - state: trạng thái game.
#   - layout: tọa độ bảng.
#   - fonts: dict font.
#
# Giá trị trả về:
#   - Không trả về.
# ============================================================
def draw_eval_history_panel(screen, state, layout, fonts):
    rect = pygame.Rect(layout["history_x"], layout["history_y"], layout["history_width"], layout["history_height"])
    draw_round_rect(screen, rect, PANEL_BG_COLOR, BORDER_COLOR, 8)

    x = rect.x + 20
    y = rect.y + 14
    draw_text(screen, "NHẬT KÝ ĐIỂM ĐÁNH GIÁ", fonts["medium_bold"], TEXT_COLOR, (x, y))
    pygame.draw.line(screen, BORDER_COLOR, (x, y + 30), (rect.right - 36, y + 30), 1)

    header_y = y + 42
    columns = [
        ("#", x + 80),
        ("Bên đi", x + 135),
        ("Nước đi", x + 300),
        ("Điểm trước -> sau", x + 430),
        ("Δ (Thay đổi)", x + 640),
        ("Đánh giá", x + 800),
    ]
    for title, cx in columns:
        draw_text(screen, title, fonts["history_bold"], TEXT_COLOR, (cx, header_y))

    pygame.draw.line(screen, BORDER_COLOR, (x, header_y + 24), (rect.right - 36, header_y + 24), 1)

    visible_rows = 4
    row_h = 27
    start = max(0, min(state["history_scroll"], max(0, len(state["eval_history"]) - visible_rows)))
    end = min(len(state["eval_history"]), start + visible_rows)

    row_y = header_y + 32
    for display_index, entry in enumerate(state["eval_history"][start:end]):
        if display_index % 2 == 1:
            pygame.draw.rect(screen, ROW_ALT_COLOR, (x, row_y - 3, rect.width - 58, row_h))

        dot_color = BLUE_COLOR if entry["mover"] == "AI" else GRAY_COLOR
        pygame.draw.circle(screen, dot_color, (x + 28, row_y + 10), 6)

        draw_text(screen, f"{entry['turn']}.", fonts["history"], TEXT_COLOR, (x + 80, row_y))
        draw_text(screen, entry["mover"], fonts["history"], TEXT_COLOR, (x + 135, row_y))
        move_row, move_col = entry["move"]
        draw_text(screen, f"({move_row + 1},{move_col + 1})", fonts["history"], TEXT_COLOR, (x + 300, row_y))
        draw_text(screen, f"{format_score(entry['score_before'])} -> {format_score(entry['score_after'])}", fonts["history"], TEXT_COLOR, (x + 430, row_y))

        impact_color = GREEN_COLOR if entry["player_impact"] >= 0 and entry["mover"] == "AI" else RED_COLOR
        if entry["mover"] != "AI":
            impact_color = RED_COLOR if entry["player_impact"] >= 0 else GREEN_COLOR
        draw_text(screen, format_score(entry["player_impact"]), fonts["history"], impact_color, (x + 650, row_y))

        color = get_color_by_name(entry["color_name"])
        draw_text(screen, entry["icon"], fonts["history_bold"], color, (x + 805, row_y))
        draw_text(screen, entry["label"], fonts["history"], color, (x + 830, row_y))
        row_y += row_h

    # Thanh cuộn dọc.
    scroll_x = rect.right - 22
    pygame.draw.line(screen, BORDER_COLOR, (scroll_x, header_y + 30), (scroll_x, rect.bottom - 18), 4)
    if len(state["eval_history"]) > visible_rows:
        track_h = rect.bottom - 18 - (header_y + 30)
        thumb_h = max(24, int(track_h * visible_rows / len(state["eval_history"])))
        max_scroll = len(state["eval_history"]) - visible_rows
        thumb_y = header_y + 30 + int((track_h - thumb_h) * start / max_scroll)
        pygame.draw.line(screen, GRAY_COLOR, (scroll_x, thumb_y), (scroll_x, thumb_y + thumb_h), 5)


# ============================================================
# Hàm: draw_menu(screen, state, fonts, width, height)
# Mục đích:
#   - Vẽ màn hình chọn ván mới.
#
# Kiến thức sử dụng:
#   - Xây dựng giao diện menu bằng các nút bo góc.
#
# Tham số:
#   - screen: màn hình pygame.
#   - state: trạng thái game.
#   - fonts: dict font.
#   - width, height: kích thước cửa sổ.
#
# Giá trị trả về:
#   - Không trả về, nhưng cập nhật vùng button trong state.
# ============================================================
def draw_menu(screen, state, fonts, width, height):
    draw_top_bar(screen, fonts, width)
    card = pygame.Rect(width // 2 - 260, height // 2 - 230, 520, 460)
    draw_round_rect(screen, card, PANEL_BG_COLOR, BORDER_COLOR, 12)
    draw_text(screen, "Ván mới", fonts["title"], TEXT_COLOR, (card.centerx, card.y + 34), center=True)

    state["buttons"].clear()
    y = card.y + 82
    x = card.x + 45

    draw_text(screen, "Chơi với", fonts["medium"], TEXT_COLOR, (x, y))
    y += 34
    state["buttons"]["mode_pvp"] = draw_option(screen, fonts, x, y, 190, 42, "Người", state["mode"] == "pvp")
    state["buttons"]["mode_pve"] = draw_option(screen, fonts, x + 220, y, 190, 42, "Máy", state["mode"] == "pve")

    y += 70
    if state["mode"] == "pve":
        draw_text(screen, "Ai đi trước", fonts["medium"], TEXT_COLOR, (x, y))
        y += 34
        state["buttons"]["first_human"] = draw_option(screen, fonts, x, y, 190, 42, "Người", state["first"] == "human")
        state["buttons"]["first_ai"] = draw_option(screen, fonts, x + 220, y, 190, 42, "Máy", state["first"] == "ai")

        y += 70
        draw_text(screen, "Thuật toán", fonts["medium"], TEXT_COLOR, (x, y))
        y += 34
        state["buttons"]["alg_minimax"] = draw_option(screen, fonts, x, y, 190, 42, "Minimax", state["algorithm"] == "minimax")
        state["buttons"]["alg_ab"] = draw_option(screen, fonts, x + 220, y, 190, 42, "Alpha-Beta", state["algorithm"] == "alphabeta")
        y += 70

    start_btn = pygame.Rect(card.centerx - 105, card.bottom - 72, 210, 46)
    state["buttons"]["start"] = start_btn
    draw_round_rect(screen, start_btn, BLUE_COLOR, BLUE_COLOR, 10)
    draw_text(screen, "Bắt đầu", fonts["medium_bold"], (255, 255, 255), start_btn.center, center=True)


# ============================================================
# Hàm: draw_option(screen, fonts, x, y, w, h, text, selected)
# Mục đích:
#   - Vẽ một lựa chọn trong menu.
#
# Kiến thức sử dụng:
#   - Tạo trạng thái selected/unselected bằng màu viền và chấm tròn.
#
# Tham số:
#   - screen, fonts: đối tượng giao diện.
#   - x, y, w, h: vị trí và kích thước.
#   - text: nội dung lựa chọn.
#   - selected: lựa chọn có đang được chọn không.
#
# Giá trị trả về:
#   - Rect của lựa chọn để xử lý click.
# ============================================================
def draw_option(screen, fonts, x, y, w, h, text, selected):
    rect = pygame.Rect(x, y, w, h)
    border = BLUE_COLOR if selected else BORDER_COLOR
    draw_round_rect(screen, rect, PANEL_BG_COLOR, border, 8, 2 if selected else 1)
    pygame.draw.circle(screen, BLUE_COLOR if selected else BORDER_COLOR, (x + 20, y + h // 2), 8)
    draw_text(screen, text, fonts["small_bold"], TEXT_COLOR, (x + 40, y + 11))
    return rect


# ============================================================
# Hàm: draw_main_screen(screen, state, layout, fonts, width)
# Mục đích:
#   - Vẽ toàn bộ màn hình game chính.
#
# Kiến thức sử dụng:
#   - Chia giao diện thành các vùng: top bar, status, board, panel AI và khung lượt đi bên trái.
#
# Tham số:
#   - screen: màn hình pygame.
#   - state: trạng thái game.
#   - layout: tọa độ giao diện.
#   - fonts: dict font.
#   - width: chiều rộng cửa sổ.
#
# Giá trị trả về:
#   - Không trả về.
# ============================================================
def draw_main_screen(screen, state, layout, fonts, width):
    draw_top_bar(screen, fonts, width)
    draw_top_status(screen, state, layout, fonts)
    draw_move_list_panel(screen, state, layout, fonts)
    draw_board(screen, state["board"], layout, fonts, state)
    draw_ai_panel(screen, state, layout, fonts)

    if state["message"]:
        msg_rect = pygame.Rect(layout["board_x"], layout["board_y"] + layout["board_size_px"] + 6, layout["board_size_px"], 22)
        draw_text(screen, state["message"], fonts["small_bold"], RED_COLOR, msg_rect.center, center=True)


# ============================================================
# Hàm: add_move_and_eval_history(state, mover_name, move, score_before, score_after)
# Mục đích:
#   - Thêm một dòng lịch sử nước đi và một dòng nhật ký điểm đánh giá.
#
# Kiến thức sử dụng:
#   - Lưu vết quá trình chơi để có thể undo và phân tích nước đi.
#
# Tham số:
#   - state: trạng thái game.
#   - mover_name: tên bên đi.
#   - move: nước đi (row, col).
#   - score_before: điểm trước nước đi.
#   - score_after: điểm sau nước đi.
#
# Giá trị trả về:
#   - Không trả về.
# ============================================================
def add_move_and_eval_history(state, mover_name, move, score_before, score_after):
    turn = len(state["move_history"]) + 1
    state["move_history"].append({"player": state["current_player"], "move": move})
    if state["mode"] == "pve":
        entry = build_eval_history_entry(turn, mover_name, move, score_before, score_after)
        state["eval_history"].append(entry)
        state["history_scroll"] = max(0, len(state["eval_history"]) - 4)


# ============================================================
# Hàm: update_game_result(state)
# Mục đích:
#   - Kiểm tra sau mỗi nước đi xem ván cờ đã kết thúc chưa.
#
# Kiến thức sử dụng:
#   - Xác định trạng thái kết thúc: X thắng, O thắng, hòa hoặc tiếp tục.
#
# Tham số:
#   - state: trạng thái game.
#
# Giá trị trả về:
#   - Không trả về, cập nhật state.
# ============================================================
def update_game_result(state):
    result = get_game_result(state["board"])
    if result == "X_WIN":
        state["game_over"] = True
        state["winner"] = PLAYER_X
        state["message"] = "X thắng!"
    elif result == "O_WIN":
        state["game_over"] = True
        state["winner"] = PLAYER_O
        state["message"] = "O thắng!"
    elif result == "DRAW":
        state["game_over"] = True
        state["winner"] = None
        state["message"] = "Hòa!"


# ============================================================
# Hàm: handle_game_click(state, mouse_pos, layout)
# Mục đích:
#   - Xử lý khi người chơi click vào bàn cờ.
#
# Kiến thức sử dụng:
#   - Chuyển tọa độ click thành nước đi.
#   - Cập nhật trạng thái game theo luật chơi.
#
# Tham số:
#   - state: trạng thái game.
#   - mouse_pos: tọa độ chuột.
#   - layout: tọa độ giao diện.
#
# Giá trị trả về:
#   - Không trả về.
# ============================================================
def handle_game_click(state, mouse_pos, layout):
    if state["game_over"] or state.get("ai_thinking"):
        return

    # Nếu đang chơi với máy và đến lượt AI thì không nhận click của người.
    if state["mode"] == "pve" and state["current_player"] == state["ai_player"]:
        return

    pos = screen_to_board_pos(mouse_pos, layout)
    if pos is None:
        return

    row, col = pos
    if not is_valid_move(state["board"], row, col):
        return

    if state["mode"] == "pve":
        score_before = evaluate_board(state["board"], state["ai_player"], state["human_player"])
    else:
        score_before = 0

    make_move(state["board"], row, col, state["current_player"])

    if state["mode"] == "pve":
        score_after = evaluate_board(state["board"], state["ai_player"], state["human_player"])
        state["current_eval"] = score_after
        add_move_and_eval_history(state, "Người", (row, col), score_before, score_after)
    else:
        state["move_history"].append({"player": state["current_player"], "move": (row, col)})

    update_game_result(state)
    if not state["game_over"]:
        state["current_player"] = switch_player(state["current_player"])


# ============================================================
# Hàm: start_ai_thinking(state)
# Mục đích:
#   - Khởi động luồng riêng để AI suy nghĩ sau khi nước người đã hiện lên bàn.
#   - Nhờ vậy giao diện không bị tình trạng người click xong phải chờ AI nghĩ xong
#     mới thấy cả hai nước xuất hiện cùng lúc.
#
# Kiến thức sử dụng:
#   - Threading: chạy thuật toán AI ở luồng phụ, pygame vẫn tiếp tục vẽ giao diện.
#   - Copy bàn cờ để AI tính toán trên bản sao, tránh sửa trực tiếp bàn thật trong thread.
#
# Tham số:
#   - state: trạng thái game.
#
# Giá trị trả về:
#   - Không trả về, cập nhật state.
# ============================================================
def start_ai_thinking(state):
    if state["mode"] != "pve" or state["game_over"] or state["current_player"] != state["ai_player"]:
        return
    if state.get("ai_thinking"):
        return

    state["ai_thinking"] = True
    state["ai_result"] = None
    state["ai_score_before"] = evaluate_board(state["board"], state["ai_player"], state["human_player"])
    state["ai_stats"] = create_ai_stats(state["algorithm"])
    state["ai_stats"]["current_move"] = "Đang tính..."
    state["ai_stats"]["configured_depth"] = AI_DEPTH
    state["ai_stats"]["max_depth"] = AI_ITERATIVE_MAX_DEPTH
    state["ai_stats"]["min_think_time"] = AI_MIN_THINK_TIME
    state["message"] = "AI đang suy nghĩ..."

    board_snapshot = copy_board(state["board"])
    algorithm = state["algorithm"]
    ai_player = state["ai_player"]
    human_player = state["human_player"]

    # Lấy nước người vừa đánh để AI ưu tiên phân tích/chặn quanh khu vực đó.
    last_human_move = None
    for item in reversed(state.get("move_history", [])):
        if item.get("player") == human_player:
            last_human_move = item.get("move")
            break

    def worker():
        result = get_ai_move(board_snapshot, algorithm, ai_player, human_player, last_human_move=last_human_move, external_stats=state["ai_stats"])
        state["ai_result"] = result
        state["ai_thinking"] = False

    thread = threading.Thread(target=worker, daemon=True)
    state["ai_thread"] = thread
    thread.start()


# ============================================================
# Hàm: apply_ai_result(state)
# Mục đích:
#   - Khi luồng AI tính xong, hàm này lấy kết quả và đặt quân AI lên bàn thật.
#
# Kiến thức sử dụng:
#   - Đồng bộ kết quả từ luồng phụ về vòng lặp chính của pygame.
#
# Tham số:
#   - state: trạng thái game.
#
# Giá trị trả về:
#   - Không trả về, cập nhật trực tiếp state.
# ============================================================
def apply_ai_result(state):
    result = state.get("ai_result")
    if result is None:
        return

    state["ai_result"] = None
    state["ai_stats"] = result["stats"]
    move = result["move"]
    state["message"] = ""

    if move is None or state["game_over"]:
        return

    row, col = move
    if not is_valid_move(state["board"], row, col):
        # Phòng trường hợp hiếm khi trạng thái đã thay đổi trong lúc AI nghĩ.
        return

    make_move(state["board"], row, col, state["ai_player"])
    score_after = evaluate_board(state["board"], state["ai_player"], state["human_player"])
    state["current_eval"] = score_after
    add_move_and_eval_history(state, "AI", (row, col), state.get("ai_score_before", 0), score_after)

    update_game_result(state)
    if not state["game_over"]:
        state["current_player"] = switch_player(state["current_player"])


# ============================================================
# Hàm: process_ai_turn(state)
# Mục đích:
#   - Hàm giữ lại để tương thích với code cũ.
#   - Bản mới không xử lý AI đồng bộ nữa mà gọi start_ai_thinking().
#
# Kiến thức sử dụng:
#   - Tách thao tác khởi động suy nghĩ và áp dụng kết quả.
#
# Tham số:
#   - state: trạng thái game.
#
# Giá trị trả về:
#   - Không trả về.
# ============================================================
def process_ai_turn(state):
    start_ai_thinking(state)


# ============================================================
# Hàm: undo_last_move(state)
# Mục đích:
#   - Thực hiện chức năng Đi lại.
#
# Kiến thức sử dụng:
#   - Quay lui trạng thái bàn cờ.
#   - Với chế độ người-máy, thường cần hoàn tác 2 nước: AI và người.
#
# Tham số:
#   - state: trạng thái game.
#
# Giá trị trả về:
#   - Không trả về.
# ============================================================
def undo_last_move(state):
    if state.get("ai_thinking"):
        return
    if not state["move_history"]:
        return

    undo_count = 1
    if state["mode"] == "pve" and len(state["move_history"]) >= 2:
        undo_count = 2

    for _ in range(undo_count):
        if not state["move_history"]:
            break
        last = state["move_history"].pop()
        row, col = last["move"]
        undo_move(state["board"], row, col)
        if state["eval_history"]:
            state["eval_history"].pop()

    state["game_over"] = False
    state["winner"] = None
    state["message"] = ""

    if state["mode"] == "pve":
        state["current_player"] = state["human_player"]
        state["current_eval"] = evaluate_board(state["board"], state["ai_player"], state["human_player"])
    else:
        if state["move_history"]:
            state["current_player"] = switch_player(state["move_history"][-1]["player"])
        else:
            state["current_player"] = PLAYER_X

    state["history_scroll"] = max(0, len(state["eval_history"]) - 4)


# ============================================================
# Hàm: handle_menu_click(state, mouse_pos)
# Mục đích:
#   - Xử lý các nút trên màn hình menu.
#
# Kiến thức sử dụng:
#   - Kiểm tra click trong Rect của pygame.
#
# Tham số:
#   - state: trạng thái game.
#   - mouse_pos: tọa độ chuột.
#
# Giá trị trả về:
#   - Không trả về.
# ============================================================
def handle_menu_click(state, mouse_pos):
    buttons = state["buttons"]
    if buttons.get("mode_pvp") and buttons["mode_pvp"].collidepoint(mouse_pos):
        state["mode"] = "pvp"
    elif buttons.get("mode_pve") and buttons["mode_pve"].collidepoint(mouse_pos):
        state["mode"] = "pve"
    elif buttons.get("first_human") and buttons["first_human"].collidepoint(mouse_pos):
        state["first"] = "human"
    elif buttons.get("first_ai") and buttons["first_ai"].collidepoint(mouse_pos):
        state["first"] = "ai"
    elif buttons.get("alg_minimax") and buttons["alg_minimax"].collidepoint(mouse_pos):
        state["algorithm"] = "minimax"
    elif buttons.get("alg_ab") and buttons["alg_ab"].collidepoint(mouse_pos):
        state["algorithm"] = "alphabeta"
    elif buttons.get("start") and buttons["start"].collidepoint(mouse_pos):
        setup_new_game(state)


# ============================================================
# Hàm: handle_game_buttons(state, mouse_pos)
# Mục đích:
#   - Xử lý click vào nút Ván mới và Đi lại trên panel AI.
#
# Kiến thức sử dụng:
#   - Tách xử lý nút khỏi xử lý click bàn cờ để code dễ đọc.
#
# Tham số:
#   - state: trạng thái game.
#   - mouse_pos: tọa độ chuột.
#
# Giá trị trả về:
#   - True nếu đã click vào nút.
#   - False nếu không click nút nào.
# ============================================================
def handle_game_buttons(state, mouse_pos):
    buttons = state["buttons"]
    if buttons.get("new_game") and buttons["new_game"].collidepoint(mouse_pos):
        state["screen"] = "menu"
        return True
    if buttons.get("undo") and buttons["undo"].collidepoint(mouse_pos):
        undo_last_move(state)
        return True
    return False


# ============================================================
# Hàm: main()
# Mục đích:
#   - Điểm bắt đầu của chương trình.
#   - Khởi tạo pygame và chạy vòng lặp chính.
#
# Kiến thức sử dụng:
#   - Game loop trong pygame: xử lý sự kiện, cập nhật logic, vẽ màn hình.
#
# Tham số:
#   - Không có.
#
# Giá trị trả về:
#   - Không trả về.
# ============================================================
def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Caro AI")
    clock = pygame.time.Clock()
    fonts = init_fonts()
    state = init_game_state()
    running = True

    while running:
        width, height = screen.get_size()
        layout = calculate_layout(width, height)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                new_w = max(event.w, MIN_WINDOW_WIDTH)
                new_h = max(event.h, MIN_WINDOW_HEIGHT)
                screen = pygame.display.set_mode((new_w, new_h), pygame.RESIZABLE)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if state["screen"] == "menu":
                        handle_menu_click(state, event.pos)
                    else:
                        if not handle_game_buttons(state, event.pos):
                            handle_game_click(state, event.pos, layout)
                elif event.button in (4, 5):
                    # Bảng nhật ký phía dưới đã được bỏ để giao diện gọn; cuộn chuột hiện không cần xử lý.
                    pass

        # Nếu AI đã nghĩ xong ở luồng phụ, áp dụng nước đi vào bàn cờ thật.
        if state["screen"] == "game" and state.get("ai_result") is not None:
            apply_ai_result(state)

        # Nếu đến lượt AI, chỉ khởi động suy nghĩ. Bàn cờ đã được vẽ liên tục ở vòng lặp chính,
        # nên nước người vừa đánh hiện lên ngay, không phải đợi AI nghĩ xong.
        if state["screen"] == "game" and state["mode"] == "pve" and state["current_player"] == state["ai_player"] and not state["game_over"]:
            start_ai_thinking(state)

        screen.fill(BACKGROUND_COLOR)
        width, height = screen.get_size()
        layout = calculate_layout(width, height)
        if state["screen"] == "menu":
            draw_menu(screen, state, fonts, width, height)
        else:
            draw_main_screen(screen, state, layout, fonts, width)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
