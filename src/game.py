"""
game.py
-------
File chứa luật chơi và các thao tác trên bàn cờ Caro.

File này không phụ thuộc vào giao diện và không cài đặt thuật toán AI.
Nhiệm vụ của nó là quản lý trạng thái bàn cờ, kiểm tra nước đi,
kiểm tra thắng/thua/hòa và sinh các nước đi hợp lệ.
"""

try:
    from .config import BOARD_SIZE, WIN_LENGTH, EMPTY, PLAYER_X, PLAYER_O, PLAYER_NAMES, SEARCH_RADIUS, MAX_CANDIDATE_MOVES
except ImportError:
    from config import BOARD_SIZE, WIN_LENGTH, EMPTY, PLAYER_X, PLAYER_O, PLAYER_NAMES, SEARCH_RADIUS, MAX_CANDIDATE_MOVES


# ============================================================
# Hàm: create_board()
# Mục đích:
#   - Tạo một bàn cờ rỗng kích thước BOARD_SIZE x BOARD_SIZE.
#   - Mỗi ô ban đầu có giá trị EMPTY, nghĩa là chưa có quân.
#
# Kiến thức sử dụng:
#   - Biểu diễn trạng thái trò chơi bằng mảng hai chiều.
#   - Trong bài toán tìm kiếm đối kháng, mỗi bàn cờ là một trạng thái.
#
# Tham số:
#   - Không có.
#
# Giá trị trả về:
#   - board: danh sách hai chiều biểu diễn bàn cờ.
# ============================================================
def create_board():
    return [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


# ============================================================
# Hàm: copy_board(board)
# Mục đích:
#   - Tạo bản sao độc lập của bàn cờ.
#   - AI dùng bản sao để thử nước đi mà không làm thay đổi bàn thật.
#
# Kiến thức sử dụng:
#   - Sao chép mảng hai chiều.
#   - Tránh lỗi tham chiếu khi mô phỏng trạng thái trong Minimax.
#
# Tham số:
#   - board: bàn cờ cần sao chép.
#
# Giá trị trả về:
#   - Một bàn cờ mới có nội dung giống board.
# ============================================================
def copy_board(board):
    return [row[:] for row in board]


# ============================================================
# Hàm: is_inside_board(row, col)
# Mục đích:
#   - Kiểm tra tọa độ có nằm trong phạm vi bàn cờ hay không.
#
# Kiến thức sử dụng:
#   - Kiểm tra biên của mảng hai chiều.
#
# Tham số:
#   - row: chỉ số hàng.
#   - col: chỉ số cột.
#
# Giá trị trả về:
#   - True nếu tọa độ nằm trong bàn cờ.
#   - False nếu tọa độ vượt ra ngoài.
# ============================================================
def is_inside_board(row, col):
    return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE


# ============================================================
# Hàm: is_valid_move(board, row, col)
# Mục đích:
#   - Kiểm tra một nước đi có hợp lệ không.
#   - Nước đi hợp lệ khi tọa độ nằm trong bàn cờ và ô đó đang trống.
#
# Kiến thức sử dụng:
#   - Kiểm tra điều kiện hợp lệ của hành động trong không gian trạng thái.
#
# Tham số:
#   - board: bàn cờ hiện tại.
#   - row: hàng muốn đánh.
#   - col: cột muốn đánh.
#
# Giá trị trả về:
#   - True nếu có thể đánh vào ô đó.
#   - False nếu không hợp lệ.
# ============================================================
def is_valid_move(board, row, col):
    return is_inside_board(row, col) and board[row][col] == EMPTY


# ============================================================
# Hàm: make_move(board, row, col, player)
# Mục đích:
#   - Đặt quân của player vào ô (row, col) nếu nước đi hợp lệ.
#
# Kiến thức sử dụng:
#   - Cập nhật trạng thái trò chơi sau một hành động.
#
# Tham số:
#   - board: bàn cờ hiện tại.
#   - row: hàng cần đánh.
#   - col: cột cần đánh.
#   - player: quân cần đặt, PLAYER_X hoặc PLAYER_O.
#
# Giá trị trả về:
#   - True nếu đặt quân thành công.
#   - False nếu ô không hợp lệ hoặc đã có quân.
#
# Ghi chú:
#   - Hàm này thay đổi trực tiếp board.
# ============================================================
def make_move(board, row, col, player):
    if not is_valid_move(board, row, col):
        return False
    board[row][col] = player
    return True


# ============================================================
# Hàm: undo_move(board, row, col)
# Mục đích:
#   - Hoàn tác một nước đi bằng cách đưa ô (row, col) về EMPTY.
#
# Kiến thức sử dụng:
#   - Quay lui trạng thái, rất thường gặp trong Minimax.
#
# Tham số:
#   - board: bàn cờ hiện tại.
#   - row: hàng cần hoàn tác.
#   - col: cột cần hoàn tác.
#
# Giá trị trả về:
#   - Không trả về. Hàm sửa trực tiếp board.
# ============================================================
def undo_move(board, row, col):
    if is_inside_board(row, col):
        board[row][col] = EMPTY


# ============================================================
# Hàm: get_valid_moves(board)
# Mục đích:
#   - Lấy toàn bộ ô trống trên bàn cờ.
#
# Kiến thức sử dụng:
#   - Sinh hành động hợp lệ trong không gian trạng thái.
#
# Tham số:
#   - board: bàn cờ hiện tại.
#
# Giá trị trả về:
#   - Danh sách các nước đi dạng tuple (row, col).
# ============================================================
def get_valid_moves(board):
    moves = []
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if board[row][col] == EMPTY:
                moves.append((row, col))
    return moves


# ============================================================
# Hàm: get_occupied_cells(board)
# Mục đích:
#   - Lấy danh sách tất cả các ô đã có quân X hoặc O.
#
# Kiến thức sử dụng:
#   - Duyệt mảng hai chiều để tìm các trạng thái không rỗng.
#
# Tham số:
#   - board: bàn cờ hiện tại.
#
# Giá trị trả về:
#   - Danh sách các ô đã có quân dạng (row, col).
# ============================================================
def get_occupied_cells(board):
    cells = []
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if board[row][col] != EMPTY:
                cells.append((row, col))
    return cells


# ============================================================
# Hàm: get_candidate_moves(board, radius=None, max_moves=None)
# Mục đích:
#   - Sinh danh sách nước đi ứng viên cho AI.
#   - Thay vì xét toàn bộ bàn, AI chỉ xét ô trống nằm gần quân đã đánh.
#   - Có thể truyền radius/max_moves riêng cho benchmark hoặc thuật toán.
#
# Kiến thức sử dụng:
#   - Heuristic sinh nước đi để giảm hệ số phân nhánh của Minimax/Alpha-Beta.
#   - Ưu tiên các ô gần trung tâm và gần cụm quân hiện có.
#
# Tham số:
#   - board: bàn cờ hiện tại.
#   - radius: bán kính xét quanh các quân đã có. Nếu None thì dùng SEARCH_RADIUS.
#   - max_moves: số nước ứng viên tối đa. Nếu None thì dùng MAX_CANDIDATE_MOVES.
#
# Giá trị trả về:
#   - Danh sách nước đi ứng viên dạng [(row, col), ...].
# ============================================================
def get_candidate_moves(board, radius=None, max_moves=None):
    if radius is None:
        radius = SEARCH_RADIUS
    if max_moves is None:
        max_moves = MAX_CANDIDATE_MOVES

    occupied = get_occupied_cells(board)
    if not occupied:
        center = BOARD_SIZE // 2
        return [(center, center)]

    candidate_set = set()
    for row, col in occupied:
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                nr = row + dr
                nc = col + dc
                if is_valid_move(board, nr, nc):
                    candidate_set.add((nr, nc))

    center = BOARD_SIZE // 2

    def priority(move):
        r, c = move
        # Ưu tiên ô gần trung tâm và gần nhiều quân đã có.
        center_distance = abs(r - center) + abs(c - center)
        neighbor_count = 0
        for rr, cc in occupied:
            if abs(rr - r) <= 1 and abs(cc - c) <= 1:
                neighbor_count += 1
        return (-neighbor_count, center_distance, r, c)

    candidates = sorted(candidate_set, key=priority)
    return candidates[:max_moves]


# ============================================================
# Hàm: count_direction(board, row, col, player, dr, dc)
# Mục đích:
#   - Đếm số quân liên tiếp của player bắt đầu từ (row, col)
#     theo hướng (dr, dc).
#
# Kiến thức sử dụng:
#   - Duyệt theo vector hướng trên ma trận.
#   - Kiểm tra chuỗi quân liên tiếp trong trò chơi Caro.
#
# Tham số:
#   - board: bàn cờ hiện tại.
#   - row, col: ô bắt đầu.
#   - player: quân cần đếm.
#   - dr, dc: hướng duyệt.
#
# Giá trị trả về:
#   - Số quân liên tiếp theo hướng đã cho.
# ============================================================
def count_direction(board, row, col, player, dr, dc):
    count = 0
    r, c = row, col
    while is_inside_board(r, c) and board[r][c] == player:
        count += 1
        r += dr
        c += dc
    return count


# ============================================================
# Hàm: check_winner(board, player)
# Mục đích:
#   - Kiểm tra xem player đã thắng hay chưa.
#   - Theo đề bài, thắng khi có WIN_LENGTH quân liên tiếp theo hàng ngang,
#     hàng dọc hoặc một trong hai đường chéo.
#
# Kiến thức sử dụng:
#   - Kiểm tra trạng thái kết thúc trong trò chơi hai người.
#   - Duyệt 4 hướng chính trên bàn cờ.
#
# Tham số:
#   - board: bàn cờ hiện tại.
#   - player: quân cần kiểm tra, PLAYER_X hoặc PLAYER_O.
#
# Giá trị trả về:
#   - True nếu player có đủ WIN_LENGTH quân liên tiếp.
#   - False nếu chưa thắng.
#
# Ghi chú:
#   - Không xét luật chặn hai đầu, đúng theo yêu cầu đề bài.
# ============================================================
def check_winner(board, player):
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if board[row][col] != player:
                continue
            for dr, dc in directions:
                if count_direction(board, row, col, player, dr, dc) >= WIN_LENGTH:
                    return True
    return False


# ============================================================
# Hàm: is_draw(board)
# Mục đích:
#   - Kiểm tra bàn cờ đã đầy chưa.
#
# Kiến thức sử dụng:
#   - Trạng thái hòa trong game Caro xảy ra khi không còn ô trống
#     và không có người thắng.
#
# Tham số:
#   - board: bàn cờ hiện tại.
#
# Giá trị trả về:
#   - True nếu bàn cờ đầy.
#   - False nếu vẫn còn ô trống.
# ============================================================
def is_draw(board):
    return all(board[row][col] != EMPTY for row in range(BOARD_SIZE) for col in range(BOARD_SIZE))


# ============================================================
# Hàm: get_game_result(board)
# Mục đích:
#   - Kiểm tra trạng thái tổng quát của ván cờ.
#
# Kiến thức sử dụng:
#   - Xác định trạng thái kết thúc: X thắng, O thắng, hòa hoặc đang chơi.
#
# Tham số:
#   - board: bàn cờ hiện tại.
#
# Giá trị trả về:
#   - "X_WIN" nếu X thắng.
#   - "O_WIN" nếu O thắng.
#   - "DRAW" nếu hòa.
#   - "ONGOING" nếu ván cờ chưa kết thúc.
# ============================================================
def get_game_result(board):
    if check_winner(board, PLAYER_X):
        return "X_WIN"
    if check_winner(board, PLAYER_O):
        return "O_WIN"
    if is_draw(board):
        return "DRAW"
    return "ONGOING"


# ============================================================
# Hàm: switch_player(current_player)
# Mục đích:
#   - Đổi lượt chơi giữa X và O.
#
# Kiến thức sử dụng:
#   - Quản lý lượt trong trò chơi hai người.
#
# Tham số:
#   - current_player: người chơi hiện tại.
#
# Giá trị trả về:
#   - PLAYER_O nếu hiện tại là PLAYER_X.
#   - PLAYER_X nếu hiện tại là PLAYER_O.
# ============================================================
def switch_player(current_player):
    return PLAYER_O if current_player == PLAYER_X else PLAYER_X


# ============================================================
# Hàm: get_opponent(player)
# Mục đích:
#   - Lấy quân đối thủ của player.
#
# Kiến thức sử dụng:
#   - Xác định cặp người chơi trong game đối kháng.
#
# Tham số:
#   - player: PLAYER_X hoặc PLAYER_O.
#
# Giá trị trả về:
#   - Quân đối thủ.
# ============================================================
def get_opponent(player):
    return switch_player(player)
