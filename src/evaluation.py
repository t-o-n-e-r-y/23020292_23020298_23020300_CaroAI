"""
evaluation.py
-------------
File chứa hàm đánh giá trạng thái bàn cờ cho AI.

Bản này đã cải tiến so với bản cũ:
- Không chỉ đếm các đoạn 4 ô đơn giản.
- Có đánh giá chuỗi liên tiếp, số đầu mở, nước thắng ngay và thế nguy hiểm.
- Điểm phòng thủ của người chơi được nhân mạnh hơn để AI biết chặn tốt hơn.
"""

try:
    from .config import (
        BOARD_SIZE,
        WIN_LENGTH,
        EMPTY,
        WIN_SCORE,
        MOVE_VERY_GOOD,
        MOVE_GOOD,
        MOVE_NORMAL_LOW,
        MOVE_BAD,
        DEFENSE_WEIGHT,
        OPEN_THREE_SCORE,
        CLOSED_THREE_SCORE,
        OPEN_TWO_SCORE,
    )
    from .game import check_winner, is_inside_board, get_candidate_moves
except ImportError:
    from config import (
        BOARD_SIZE,
        WIN_LENGTH,
        EMPTY,
        WIN_SCORE,
        MOVE_VERY_GOOD,
        MOVE_GOOD,
        MOVE_NORMAL_LOW,
        MOVE_BAD,
        DEFENSE_WEIGHT,
        OPEN_THREE_SCORE,
        CLOSED_THREE_SCORE,
        OPEN_TWO_SCORE,
    )
    from game import check_winner, is_inside_board, get_candidate_moves

DIRECTIONS = [(0, 1), (1, 0), (1, 1), (1, -1)]


# ============================================================
# Hàm: get_all_windows(board)
# Mục đích:
#   - Lấy toàn bộ đoạn WIN_LENGTH ô liên tiếp theo 4 hướng.
#   - Hàm này phục vụ đánh giá nhanh các mẫu 3/4, 2/4.
#
# Kiến thức sử dụng:
#   - Duyệt ma trận theo vector hướng.
#   - Trong Caro 4 thắng, mỗi đoạn 4 ô là một cửa sổ chiến thắng tiềm năng.
#
# Tham số:
#   - board: bàn cờ hiện tại.
#
# Giá trị trả về:
#   - Danh sách window, mỗi window là list các giá trị ô.
# ============================================================
def get_all_windows(board):
    windows = []
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            for dr, dc in DIRECTIONS:
                cells = []
                ok = True
                for step in range(WIN_LENGTH):
                    nr = row + dr * step
                    nc = col + dc * step
                    if not is_inside_board(nr, nc):
                        ok = False
                        break
                    cells.append(board[nr][nc])
                if ok:
                    windows.append(cells)
    return windows


# ============================================================
# Hàm: score_window(window, player, opponent)
# Mục đích:
#   - Chấm điểm một đoạn 4 ô cho một người chơi.
#   - Đây là lớp heuristic thứ nhất: phát hiện các mẫu gần thắng.
#
# Kiến thức sử dụng:
#   - Hàm đánh giá heuristic trong tìm kiếm độ sâu hữu hạn.
#
# Tham số:
#   - window: list gồm 4 ô.
#   - player: quân đang được chấm.
#   - opponent: quân đối thủ.
#
# Giá trị trả về:
#   - Điểm của window đối với player.
# ============================================================
def score_window(window, player, opponent):
    p = window.count(player)
    o = window.count(opponent)
    e = window.count(EMPTY)

    if p > 0 and o > 0:
        return 0

    # Dùng WIN_LENGTH tổng quát để chương trình chạy đúng cả luật 4 thắng và 5 thắng.
    # Nếu WIN_LENGTH = 4 thì mẫu nguy hiểm nhất là 3 quân + 1 ô trống.
    # Nếu WIN_LENGTH = 5 thì mẫu nguy hiểm nhất là 4 quân + 1 ô trống.
    if p >= WIN_LENGTH:
        return WIN_SCORE
    if p == WIN_LENGTH - 1 and e == 1:
        return 140_000
    if p == WIN_LENGTH - 2 and e == 2:
        # Threat trung gian: 2 mở khi chơi 4, hoặc 3 mở khi chơi 5.
        return 18_000 if WIN_LENGTH >= 5 else 3_200
    if p == WIN_LENGTH - 3 and e == 3:
        return 500
    return 0


# ============================================================
# Hàm: evaluate_lines_for_player(board, player, opponent)
# Mục đích:
#   - Tính tổng điểm từ các window 4 ô của player.
#   - Đồng thời thống kê số mẫu 4, 3, 2, 1 quân để giải thích trong báo cáo.
#
# Kiến thức sử dụng:
#   - Pattern-based evaluation: đánh giá bàn cờ thông qua các mẫu quân.
#
# Tham số:
#   - board: bàn cờ hiện tại.
#   - player: quân cần chấm.
#   - opponent: quân đối thủ.
#
# Giá trị trả về:
#   - total_score: tổng điểm.
#   - detail: dict thống kê số mẫu.
# ============================================================
def evaluate_lines_for_player(board, player, opponent):
    total_score = 0
    detail = {"four": 0, "three": 0, "two": 0, "one": 0}

    for window in get_all_windows(board):
        p = window.count(player)
        o = window.count(opponent)
        e = window.count(EMPTY)
        if p > 0 and o > 0:
            continue

        total_score += score_window(window, player, opponent)
        if p == 4:
            detail["four"] += 1
        elif p == 3 and e == 1:
            detail["three"] += 1
        elif p == 2 and e == 2:
            detail["two"] += 1
        elif p == 1 and e == 3:
            detail["one"] += 1

    return total_score, detail


# ============================================================
# Hàm: count_contiguous(board, row, col, player, dr, dc)
# Mục đích:
#   - Đếm chuỗi quân liên tiếp của player đi qua ô (row, col) theo một hướng.
#   - Đồng thời xác định hai đầu của chuỗi có mở hay không.
#
# Kiến thức sử dụng:
#   - Đánh giá thế cờ dựa trên chuỗi liên tiếp và đầu mở.
#   - Trong Caro, chuỗi 3 có đầu mở là tình huống rất nguy hiểm vì sắp thắng.
#
# Tham số:
#   - board: bàn cờ hiện tại.
#   - row, col: vị trí quân đang xét.
#   - player: quân cần đếm.
#   - dr, dc: hướng duyệt.
#
# Giá trị trả về:
#   - (length, open_ends): độ dài chuỗi và số đầu mở.
# ============================================================
def count_contiguous(board, row, col, player, dr, dc):
    length = 1

    r, c = row + dr, col + dc
    while is_inside_board(r, c) and board[r][c] == player:
        length += 1
        r += dr
        c += dc
    open_1 = is_inside_board(r, c) and board[r][c] == EMPTY

    r, c = row - dr, col - dc
    while is_inside_board(r, c) and board[r][c] == player:
        length += 1
        r -= dr
        c -= dc
    open_2 = is_inside_board(r, c) and board[r][c] == EMPTY

    return length, int(open_1) + int(open_2)


# ============================================================
# Hàm: score_chain(length, open_ends)
# Mục đích:
#   - Quy đổi một chuỗi liên tiếp thành điểm heuristic.
#   - Chuỗi càng dài và càng nhiều đầu mở thì càng nguy hiểm.
#
# Kiến thức sử dụng:
#   - Heuristic trong game đối kháng: ưu tiên thế có khả năng thắng gần.
#
# Tham số:
#   - length: độ dài chuỗi liên tiếp.
#   - open_ends: số đầu mở, 0/1/2.
#
# Giá trị trả về:
#   - Điểm của chuỗi.
# ============================================================
def score_chain(length, open_ends):
    # Tổng quát theo WIN_LENGTH:
    # - Chơi 4: chuỗi 3 là critical threat.
    # - Chơi 5: chuỗi 4 là critical threat.
    critical = WIN_LENGTH - 1
    secondary = WIN_LENGTH - 2

    if length >= WIN_LENGTH:
        return WIN_SCORE
    if length >= critical:
        if open_ends >= 2:
            return OPEN_THREE_SCORE
        if open_ends == 1:
            return CLOSED_THREE_SCORE
        return 0
    if length >= secondary:
        if open_ends >= 2:
            return OPEN_TWO_SCORE if WIN_LENGTH == 4 else 45_000
        if open_ends == 1:
            return 1_800 if WIN_LENGTH == 4 else 18_000
        return 0
    if length == 1:
        if open_ends >= 2:
            return 120
        if open_ends == 1:
            return 35
    return 0


# ============================================================
# Hàm: evaluate_chains_for_player(board, player)
# Mục đích:
#   - Tính điểm theo chuỗi liên tiếp và đầu mở cho player.
#   - Bản này giúp AI đỡ bỏ sót thế nguy hiểm như 3 quân mở đầu.
#
# Kiến thức sử dụng:
#   - Pattern evaluation nâng cao hơn cách chỉ xét window 4 ô.
#
# Tham số:
#   - board: bàn cờ hiện tại.
#   - player: quân cần đánh giá.
#
# Giá trị trả về:
#   - Tổng điểm chuỗi của player.
# ============================================================
def evaluate_chains_for_player(board, player):
    total = 0
    seen = set()

    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if board[row][col] != player:
                continue
            for dr, dc in DIRECTIONS:
                key = (row, col, dr, dc)
                if key in seen:
                    continue

                # Chỉ chấm từ đầu chuỗi để tránh cộng quá nhiều lần.
                prev_r, prev_c = row - dr, col - dc
                if is_inside_board(prev_r, prev_c) and board[prev_r][prev_c] == player:
                    continue

                length, open_ends = count_contiguous(board, row, col, player, dr, dc)
                total += score_chain(length, open_ends)

                for k in range(length):
                    seen.add((row + dr * k, col + dc * k, dr, dc))

    return total


# ============================================================
# Hàm: count_threats(board, player, opponent)
# Mục đích:
#   - Đếm số nước đi mà player có thể thắng ngay ở lượt kế tiếp.
#   - Nếu có nhiều hơn một nước thắng ngay, đó là thế nước đôi rất mạnh.
#
# Kiến thức sử dụng:
#   - Nhận diện threat/fork: một nước tạo nhiều mối đe dọa cùng lúc.
#
# Tham số:
#   - board: bàn cờ hiện tại.
#   - player: quân cần kiểm tra threat.
#   - opponent: quân đối thủ, giữ để cùng kiểu tham số với các hàm khác.
#
# Giá trị trả về:
#   - Số ô mà player đánh vào sẽ thắng ngay.
# ============================================================
def count_threats(board, player, opponent=None):
    threats = 0
    # Chỉ cần kiểm tra những ô ứng viên gần khu vực đang đánh.
    # Việc này nhanh hơn rất nhiều so với quét toàn bộ bàn ở mỗi lần evaluate.
    for row, col in get_candidate_moves(board, max_moves=None):
        if board[row][col] != EMPTY:
            continue
        board[row][col] = player
        if check_winner(board, player):
            threats += 1
        board[row][col] = EMPTY
    return threats


# ============================================================
# Hàm: center_bonus(board, player)
# Mục đích:
#   - Cộng điểm nhẹ cho quân gần trung tâm.
#   - Điểm này chỉ là phụ, không được lớn hơn điểm threat.
#
# Kiến thức sử dụng:
#   - Heuristic vị trí: trung tâm thường linh hoạt hơn ở nhiều hướng.
#
# Tham số:
#   - board: bàn cờ hiện tại.
#   - player: quân cần tính điểm.
#
# Giá trị trả về:
#   - Điểm thưởng vị trí.
# ============================================================
def center_bonus(board, player):
    center = BOARD_SIZE // 2
    bonus = 0
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if board[row][col] == player:
                distance = abs(row - center) + abs(col - center)
                bonus += max(0, 18 - distance * 2)
    return bonus


# ============================================================
# Hàm: evaluate_board(board, ai_player, human_player)
# Mục đích:
#   - Tính điểm tổng của bàn cờ theo góc nhìn AI.
#   - Dùng trong Minimax và Alpha-Beta.
#
# Kiến thức sử dụng:
#   - Heuristic evaluation: điểm AI trừ điểm người.
#   - Tăng trọng số phòng thủ để AI biết chặn tốt hơn.
#
# Tham số:
#   - board: bàn cờ hiện tại.
#   - ai_player: quân của AI.
#   - human_player: quân của người chơi.
#
# Giá trị trả về:
#   - score > 0: lợi cho AI; score < 0: lợi cho người.
# ============================================================
def evaluate_board(board, ai_player, human_player):
    if check_winner(board, ai_player):
        return WIN_SCORE
    if check_winner(board, human_player):
        return -WIN_SCORE

    ai_line_score, _ = evaluate_lines_for_player(board, ai_player, human_player)
    human_line_score, _ = evaluate_lines_for_player(board, human_player, ai_player)

    ai_chain_score = evaluate_chains_for_player(board, ai_player)
    human_chain_score = evaluate_chains_for_player(board, human_player)

    ai_threats = count_threats(board, ai_player, human_player)
    human_threats = count_threats(board, human_player, ai_player)

    ai_score = ai_line_score + ai_chain_score + center_bonus(board, ai_player)
    human_score = human_line_score + human_chain_score + center_bonus(board, human_player)

    # Nước đôi: nhiều threat thắng ngay cùng lúc cực kỳ nguy hiểm.
    if ai_threats >= 2:
        ai_score += 260_000 * ai_threats
    elif ai_threats == 1:
        ai_score += 95_000

    if human_threats >= 2:
        human_score += 520_000 * human_threats
    elif human_threats == 1:
        human_score += 240_000

    # Bản v6: phòng thủ mạnh hơn rõ rệt. Khi người có 3 mở, nước đôi hoặc
    # nhiều hướng tấn công, điểm âm sẽ rất lớn để Minimax/Alpha-Beta ưu tiên chặn.
    return int(ai_score - human_score * DEFENSE_WEIGHT)


# ============================================================
# Hàm: evaluate_board_detailed(board, ai_player, human_player)
# Mục đích:
#   - Trả điểm tổng và thông tin chi tiết dùng cho nhật ký đánh giá.
#
# Kiến thức sử dụng:
#   - Phân tách điểm tổng thành điểm tấn công/phòng thủ để báo cáo dễ hiểu.
#
# Tham số:
#   - board: bàn cờ hiện tại.
#   - ai_player: quân của AI.
#   - human_player: quân của người.
#
# Giá trị trả về:
#   - dict gồm total_score, ai_score, human_score, details.
# ============================================================
def evaluate_board_detailed(board, ai_player, human_player):
    ai_line_score, ai_detail = evaluate_lines_for_player(board, ai_player, human_player)
    human_line_score, human_detail = evaluate_lines_for_player(board, human_player, ai_player)
    ai_chain = evaluate_chains_for_player(board, ai_player)
    human_chain = evaluate_chains_for_player(board, human_player)
    ai_threats = count_threats(board, ai_player, human_player)
    human_threats = count_threats(board, human_player, ai_player)

    total_score = evaluate_board(board, ai_player, human_player)
    return {
        "total_score": total_score,
        "ai_score": ai_line_score + ai_chain + center_bonus(board, ai_player),
        "human_score": human_line_score + human_chain + center_bonus(board, human_player),
        "details": {
            "ai_four": ai_detail["four"],
            "ai_three": ai_detail["three"],
            "ai_two": ai_detail["two"],
            "ai_one": ai_detail["one"],
            "human_four": human_detail["four"],
            "human_three": human_detail["three"],
            "human_two": human_detail["two"],
            "human_one": human_detail["one"],
            "ai_threats": ai_threats,
            "human_threats": human_threats,
        },
    }


# ============================================================
# Hàm: get_current_eval_score(board, ai_player, human_player)
# Mục đích:
#   - Lấy điểm hiện tại để hiển thị ô Eval.
#
# Kiến thức sử dụng:
#   - Dùng chung hàm evaluate_board để UI và AI thống nhất cách hiểu điểm.
#
# Tham số:
#   - board, ai_player, human_player.
#
# Giá trị trả về:
#   - Điểm eval hiện tại.
# ============================================================
def get_current_eval_score(board, ai_player, human_player):
    return evaluate_board(board, ai_player, human_player)


# ============================================================
# Hàm: classify_move(player_impact)
# Mục đích:
#   - Xếp loại nước đi dựa trên tác động điểm đối với bên vừa đi.
#
# Kiến thức sử dụng:
#   - Chuyển số điểm heuristic thành nhãn dễ hiểu.
#
# Tham số:
#   - player_impact: tác động của nước đi theo góc nhìn bên vừa đi.
#
# Giá trị trả về:
#   - dict gồm label, icon, color_name.
# ============================================================
def classify_move(player_impact):
    if player_impact >= MOVE_VERY_GOOD:
        return {"label": "Rất hay", "icon": "*", "color_name": "blue"}
    if player_impact >= MOVE_GOOD:
        return {"label": "Tốt", "icon": "+", "color_name": "green"}
    if player_impact >= MOVE_NORMAL_LOW:
        return {"label": "Bình thường", "icon": "o", "color_name": "orange"}
    if player_impact >= MOVE_BAD:
        return {"label": "Chưa tốt", "icon": "!", "color_name": "orange"}
    return {"label": "Sai lầm", "icon": "x", "color_name": "red"}


# ============================================================
# Hàm: build_eval_history_entry(turn, mover_name, move, score_before, score_after)
# Mục đích:
#   - Tạo một dòng nhật ký đánh giá nước đi.
#
# Kiến thức sử dụng:
#   - Điểm eval tính theo AI, nên nếu người đi thì tác động tốt cho người là -delta.
#
# Tham số:
#   - turn: số lượt.
#   - mover_name: "Người" hoặc "AI".
#   - move: nước đi (row, col).
#   - score_before, score_after: điểm trước/sau.
#
# Giá trị trả về:
#   - dict chứa dữ liệu để vẽ bảng lịch sử.
# ============================================================
def build_eval_history_entry(turn, mover_name, move, score_before, score_after):
    delta = score_after - score_before
    player_impact = delta if mover_name == "AI" else -delta
    result = classify_move(player_impact)
    return {
        "turn": turn,
        "mover": mover_name,
        "move": move,
        "score_before": score_before,
        "score_after": score_after,
        "delta": delta,
        "player_impact": player_impact,
        "label": result["label"],
        "icon": result["icon"],
        "color_name": result["color_name"],
    }


# ============================================================
# Hàm: format_score(score)
# Mục đích:
#   - Rút gọn điểm quá lớn để giao diện không bị vỡ.
#
# Kiến thức sử dụng:
#   - Biểu diễn dữ liệu số trên UI.
#
# Tham số:
#   - score: điểm cần hiển thị.
#
# Giá trị trả về:
#   - Chuỗi điểm có dấu + nếu dương.
# ============================================================
def format_score(score):
    try:
        score = int(score)
    except (TypeError, ValueError):
        return str(score)

    # Không hiển thị trực tiếp số quá dài trên giao diện, vì các điểm heuristic
    # có thể lên rất lớn khi xuất hiện nhiều threat. Đây chỉ là cách rút gọn
    # khi vẽ UI, không làm thay đổi điểm thật mà Minimax/Alpha-Beta dùng.
    sign = "+" if score > 0 else ""
    abs_score = abs(score)

    if abs_score >= 1_000_000:
        value = score / 1_000_000
        return f"{value:+.1f}M"
    if abs_score >= 100_000:
        value = round(score / 1000)
        return f"{value:+.0f}K"
    if abs_score >= 10_000:
        value = round(score / 1000, 1)
        return f"{value:+.1f}K"
    return f"{sign}{score}"
