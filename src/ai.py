"""
ai.py
-----
File AI đã được rút gọn để dễ đọc và dễ giải thích trong báo cáo.

Ý tưởng chính:
- Vẫn giữ lõi Minimax / Alpha-Beta.
- Chỉ dùng luật cứng cho 2 tình huống chắc chắn: AI thắng ngay, hoặc người thắng ngay cần chặn.
- Các chiến thuật khác như nước đôi, nước mồi, thủ phản công được đưa vào điểm sắp xếp nước đi.
- Iterative Deepening tìm sâu dần và chỉ dừng khi đã hoàn thành độ sâu tối thiểu hoặc hết thời gian.
"""

import math
import time

try:
    from .config import (
        BOARD_SIZE, WIN_LENGTH, EMPTY, AI_DEPTH, AI_ITERATIVE_MAX_DEPTH,
        AI_MIN_COMPLETED_DEPTH, AI_TIME_LIMIT, AI_MIN_THINK_TIME,
        SEARCH_RADIUS, MAX_CANDIDATE_MOVES, WIN_SCORE,
        ATTACK_WEIGHT, DEFENSE_WEIGHT, FORK_THREAT_SCORE,
        COUNTER_ATTACK_BONUS, AI_STATS_UPDATE_INTERVAL,
    )
    from .game import (
        make_move, undo_move, is_valid_move, check_winner,
        get_candidate_moves, get_occupied_cells,
    )
    from .evaluation import evaluate_board
except ImportError:
    from config import (
        BOARD_SIZE, WIN_LENGTH, EMPTY, AI_DEPTH, AI_ITERATIVE_MAX_DEPTH,
        AI_MIN_COMPLETED_DEPTH, AI_TIME_LIMIT, AI_MIN_THINK_TIME,
        SEARCH_RADIUS, MAX_CANDIDATE_MOVES, WIN_SCORE,
        ATTACK_WEIGHT, DEFENSE_WEIGHT, FORK_THREAT_SCORE,
        COUNTER_ATTACK_BONUS, AI_STATS_UPDATE_INTERVAL,
    )
    from game import (
        make_move, undo_move, is_valid_move, check_winner,
        get_candidate_moves, get_occupied_cells,
    )
    from evaluation import evaluate_board

DIRECTIONS = [(0, 1), (1, 0), (1, 1), (1, -1)]


# ============================================================
# Hàm: create_ai_stats()
# Mục đích:
#   - Tạo bộ thống kê cho panel THÔNG TIN AI.
#   - Các thông tin này giúp người xem biết AI đang xét đến độ sâu nào,
#     đã xét bao nhiêu trạng thái và nước tốt nhất hiện tại là gì.
# ============================================================
def create_ai_stats(algorithm="alphabeta", depth=AI_DEPTH):
    return {
        "algorithm": "Alpha-Beta" if algorithm == "alphabeta" else "Minimax",
        "configured_depth": depth,
        "depth": depth,
        "completed_depth": 0,
        "current_depth": 0,
        "max_depth": AI_ITERATIVE_MAX_DEPTH,
        "min_completed_depth": AI_MIN_COMPLETED_DEPTH,
        "min_think_time": AI_MIN_THINK_TIME,
        "time": 0.0,
        "nodes": 0,
        "cutoffs": 0,
        "candidate_moves": 0,
        "current_move": None,
        "best_move": None,
        "best_score": 0,
        "timeout": False,
        "note": "",
        "_last_ui_update": 0.0,
    }


# ============================================================
# Hàm: inside()
# Mục đích:
#   - Kiểm tra tọa độ có nằm trong bàn cờ không.
#   - Viết ngắn để các hàm phân tích chuỗi dễ đọc hơn.
# ============================================================
def inside(r, c):
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE


# ============================================================
# Hàm: time_up()
# Mục đích:
#   - Kiểm tra AI đã quá thời gian tối đa chưa.
#   - Dùng trong Minimax/Alpha-Beta để tránh treo giao diện.
# ============================================================
def time_up(start_time, limit):
    return time.perf_counter() - start_time >= limit


# ============================================================
# Hàm: safe_update_stats()
# Mục đích:
#   - Cập nhật thông tin AI cho giao diện nhưng không cập nhật quá dày.
#   - Nếu cập nhật current_move ở mọi node, pygame sẽ giật/nhấp nháy.
# ============================================================
def safe_update_stats(stats, **kwargs):
    now = time.perf_counter()
    if now - stats.get("_last_ui_update", 0.0) >= AI_STATS_UPDATE_INTERVAL:
        stats.update(kwargs)
        stats["_last_ui_update"] = now


# ============================================================
# Hàm: count_win_moves()
# Mục đích:
#   - Đếm các nước mà player đánh vào là thắng ngay.
#   - Dùng để phát hiện chặn thắng, nước đôi/fork.
# ============================================================
def count_win_moves(board, player, moves=None, stop_at=99):
    if moves is None:
        moves = get_candidate_moves(board, radius=SEARCH_RADIUS, max_moves=MAX_CANDIDATE_MOVES)
    wins = []
    for r, c in moves:
        make_move(board, r, c, player)
        ok = check_winner(board, player)
        undo_move(board, r, c)
        if ok:
            wins.append((r, c))
            if len(wins) >= stop_at:
                break
    return wins


# ============================================================
# Hàm: find_immediate_winning_move()
# Mục đích:
#   - Tìm nước thắng ngay cho player.
#   - Đây là luật chiến thuật chắc chắn, không làm mất bản chất Minimax.
# ============================================================
def find_immediate_winning_move(board, player):
    wins = count_win_moves(board, player, stop_at=1)
    return wins[0] if wins else None


# ============================================================
# Hàm: line_info_after_move()
# Mục đích:
#   - Giả sử player đánh tại move, đếm chuỗi dài nhất và số đầu mở.
#   - Dùng để nhận diện tạo 3 khi chơi 4, tạo 4 khi chơi 5.
# ============================================================
def line_info_after_move(board, move, player):
    r, c = move
    best_len = 1
    best_open = 0
    for dr, dc in DIRECTIONS:
        length = 1
        rr, cc = r + dr, c + dc
        while inside(rr, cc) and board[rr][cc] == player:
            length += 1
            rr += dr
            cc += dc
        open_a = inside(rr, cc) and board[rr][cc] == EMPTY
        rr, cc = r - dr, c - dc
        while inside(rr, cc) and board[rr][cc] == player:
            length += 1
            rr -= dr
            cc -= dc
        open_b = inside(rr, cc) and board[rr][cc] == EMPTY
        open_ends = int(open_a) + int(open_b)
        if length > best_len or (length == best_len and open_ends > best_open):
            best_len = length
            best_open = open_ends
    return best_len, best_open


# ============================================================
# Hàm: move_pattern_score()
# Mục đích:
#   - Chấm nhanh giá trị chiến thuật của một nước nếu player đánh vào đó.
#   - Tổng quát theo WIN_LENGTH:
#       + chơi 4: chuỗi 3 là critical.
#       + chơi 5: chuỗi 4 là critical.
# ============================================================
def move_pattern_score(board, move, player):
    r, c = move
    if not is_valid_move(board, r, c):
        return -math.inf
    make_move(board, r, c, player)
    if check_winner(board, player):
        undo_move(board, r, c)
        return WIN_SCORE
    length, open_ends = line_info_after_move(board, move, player)
    # Sau khi đặt quân, nếu người đó có từ 2 nước thắng ở lượt sau => fork.
    next_wins = count_win_moves(board, player, stop_at=2)
    undo_move(board, r, c)

    critical = WIN_LENGTH - 1
    setup = WIN_LENGTH - 2
    score = 0
    if len(next_wins) >= 2:
        score += FORK_THREAT_SCORE
    if length >= critical and open_ends == 2:
        score += 260_000
    elif length >= critical and open_ends == 1:
        score += 120_000
    elif length >= setup and open_ends == 2:
        score += 18_000 if WIN_LENGTH >= 5 else 8_000
    elif length >= setup and open_ends == 1:
        score += 2_500
    return score


# ============================================================
# Hàm: tactical_move_score()
# Mục đích:
#   - Chấm một nước của AI theo cả tấn công và phòng thủ.
#   - Điểm đặc biệt: nếu một nước vừa chặn được nguy cơ của người,
#     vừa tạo critical threat/fork cho AI thì cộng combo thủ phản công.
# ============================================================
def tactical_move_score(board, move, ai_player, human_player, last_human_move=None):
    if move is None:
        return -math.inf
    r, c = move
    if not is_valid_move(board, r, c):
        return -math.inf

    # attack_score: nếu AI đánh nước này thì AI mạnh lên bao nhiêu.
    attack_score = move_pattern_score(board, move, ai_player)
    # defense_score: nếu người được đánh nước này thì nguy hiểm cỡ nào.
    defense_score = move_pattern_score(board, move, human_player)

    # So sánh số nước thắng của người trước/sau khi AI đánh để biết có chặn thật không.
    before_win = len(count_win_moves(board, human_player, stop_at=2))
    before_fork = count_fork_creating_moves(board, human_player, limit=12, stop_at=2)
    make_move(board, r, c, ai_player)
    after_win = len(count_win_moves(board, human_player, stop_at=2))
    after_fork = count_fork_creating_moves(board, human_player, limit=12, stop_at=2)
    undo_move(board, r, c)

    blocks = max(0, before_win - after_win) * 180_000 + max(0, before_fork - after_fork) * 120_000
    combo = COUNTER_ATTACK_BONUS if blocks > 0 and attack_score >= 100_000 else 0

    # Bám sát nước người vừa đánh, tránh lỗi AI nhảy giữa bàn quá xa khi người đi góc/cạnh.
    near_bonus = 0
    if last_human_move:
        dist = abs(r - last_human_move[0]) + abs(c - last_human_move[1])
        if dist <= 2:
            near_bonus = 10_000 - dist * 2_000
        elif len(get_occupied_cells(board)) <= 2:
            near_bonus = -60_000

    return attack_score * ATTACK_WEIGHT + defense_score * DEFENSE_WEIGHT + blocks + combo + near_bonus


# ============================================================
# Hàm: count_fork_creating_moves()
# Mục đích:
#   - Đếm số nước mà player đánh vào sẽ tạo ít nhất 2 nước thắng ở lượt sau.
#   - Đây là bản anti-fork nhẹ, chỉ dùng ở tầng gốc để không làm AI quá chậm.
# ============================================================
def count_fork_creating_moves(board, player, limit=18, stop_at=99):
    moves = get_candidate_moves(board, radius=SEARCH_RADIUS, max_moves=limit)
    count = 0
    for move in moves:
        r, c = move
        make_move(board, r, c, player)
        wins = count_win_moves(board, player, stop_at=2)
        undo_move(board, r, c)
        if len(wins) >= 2:
            count += 1
            if count >= stop_at:
                break
    return count


# ============================================================
# Hàm: get_search_moves()
# Mục đích:
#   - Sinh và sắp xếp nước đi ứng viên cho AI.
#   - Tầng đầu ưu tiên nhiều nước hơn; tầng sâu có thể truyền limit nhỏ hơn.
# ============================================================
def get_search_moves(board, ai_player, human_player, last_human_move=None, limit=None):
    if limit is None:
        limit = MAX_CANDIDATE_MOVES
    moves = set(get_candidate_moves(board, radius=SEARCH_RADIUS, max_moves=MAX_CANDIDATE_MOVES))

    # Đầu ván: nếu người đi góc/cạnh, chỉ xét gần người chơi để không nhảy giữa bàn quá xa.
    occupied = get_occupied_cells(board)
    if last_human_move and len(occupied) <= 2:
        lr, lc = last_human_move
        near = []
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                nr, nc = lr + dr, lc + dc
                if is_valid_move(board, nr, nc):
                    near.append((nr, nc))
        if near:
            moves = set(near)

    ordered = sorted(
        moves,
        key=lambda m: tactical_move_score(board, m, ai_player, human_player, last_human_move),
        reverse=True,
    )
    return ordered[:limit]


# ============================================================
# Hàm: terminal_score()
# Mục đích:
#   - Trả điểm nếu trạng thái đã kết thúc; None nếu chưa kết thúc.
#   - Cộng/trừ depth để AI thích thắng sớm và tránh thua sớm.
# ============================================================
def terminal_score(board, ai_player, human_player, depth_left):
    if check_winner(board, ai_player):
        return WIN_SCORE + depth_left
    if check_winner(board, human_player):
        return -WIN_SCORE - depth_left
    if not get_candidate_moves(board, radius=SEARCH_RADIUS, max_moves=1):
        return 0
    return None


# ============================================================
# Hàm: minimax()
# Mục đích:
#   - Minimax thuần dùng cho chế độ so sánh thuật toán.
# ============================================================
def minimax(board, depth, maximizing, ai_player, human_player, stats, start_time, limit, last_human_move=None):
    stats["nodes"] += 1
    if time_up(start_time, limit):
        stats["timeout"] = True
        return evaluate_board(board, ai_player, human_player)
    t = terminal_score(board, ai_player, human_player, depth)
    if t is not None:
        return t
    if depth <= 0:
        return evaluate_board(board, ai_player, human_player)

    player = ai_player if maximizing else human_player
    best = -math.inf if maximizing else math.inf
    moves = get_search_moves(board, ai_player, human_player, last_human_move, limit=30 if depth <= 2 else 18)
    for r, c in moves:
        make_move(board, r, c, player)
        score = minimax(board, depth - 1, not maximizing, ai_player, human_player, stats, start_time, limit, last_human_move)
        undo_move(board, r, c)
        best = max(best, score) if maximizing else min(best, score)
        if stats.get("timeout"):
            break
    return best


# ============================================================
# Hàm: alphabeta()
# Mục đích:
#   - Minimax cải tiến bằng Alpha-Beta pruning.
#   - Vẫn chọn nước theo nguyên lý MAX-MIN, nhưng bỏ qua nhánh không cần xét.
# ============================================================
def alphabeta(board, depth, alpha, beta, maximizing, ai_player, human_player, stats, start_time, limit, last_human_move=None):
    stats["nodes"] += 1
    if time_up(start_time, limit):
        stats["timeout"] = True
        return evaluate_board(board, ai_player, human_player)
    t = terminal_score(board, ai_player, human_player, depth)
    if t is not None:
        return t
    if depth <= 0:
        return evaluate_board(board, ai_player, human_player)

    player = ai_player if maximizing else human_player
    moves = get_search_moves(board, ai_player, human_player, last_human_move, limit=30 if depth <= 2 else 18)
    if maximizing:
        value = -math.inf
        for r, c in moves:
            make_move(board, r, c, player)
            value = max(value, alphabeta(board, depth - 1, alpha, beta, False, ai_player, human_player, stats, start_time, limit, last_human_move))
            undo_move(board, r, c)
            alpha = max(alpha, value)
            if beta <= alpha:
                stats["cutoffs"] += 1
                break
            if stats.get("timeout"):
                break
        return value
    value = math.inf
    for r, c in moves:
        make_move(board, r, c, player)
        value = min(value, alphabeta(board, depth - 1, alpha, beta, True, ai_player, human_player, stats, start_time, limit, last_human_move))
        undo_move(board, r, c)
        beta = min(beta, value)
        if beta <= alpha:
            stats["cutoffs"] += 1
            break
        if stats.get("timeout"):
            break
    return value


# ===================================================================
# Hàm: root_search()
# Mục đích:
#   - Tìm nước tốt nhất ở tầng gốc cho một độ sâu cụ thể.
#   - Tầng gốc cập nhật current_move/best_move để giao diện hiển thị.
# ===================================================================
def root_search(board, depth, algorithm, ai_player, human_player, stats, start_time, limit, last_human_move=None):
    best_move = None
    best_score = -math.inf
    alpha = -math.inf
    beta = math.inf

    moves = get_search_moves(board, ai_player, human_player, last_human_move, limit=MAX_CANDIDATE_MOVES)
    stats["candidate_moves"] = len(moves)

    for move in moves:
        if time_up(start_time, limit):
            stats["timeout"] = True
            break

        r, c = move
        safe_update_stats(stats, current_move=move, current_depth=depth, time=time.perf_counter() - start_time)

        make_move(board, r, c, ai_player)

        if algorithm == "minimax":
            score = minimax(
                board, depth - 1, False,
                ai_player, human_player,
                stats, start_time, limit,
                last_human_move
            )
        else:
            score = alphabeta(
                board, depth - 1,
                alpha, beta,
                False,
                ai_player, human_player,
                stats, start_time, limit,
                last_human_move
            )

        undo_move(board, r, c)

        if score > best_score or best_move is None:
            best_score = score
            best_move = move
            stats["best_move"] = move
            stats["best_score"] = score

        if algorithm == "alphabeta":
            alpha = max(alpha, best_score)

        if stats.get("timeout"):
            break

    return best_move, best_score, not stats.get("timeout")


# ============================================================
# Hàm: search_with_iterative_deepening()
# Mục đích:
#   - Tìm kiếm sâu dần: depth 1 -> 2 -> 3...
#   - Chỉ cho phép dừng bình thường khi đã hoàn thành tối thiểu depth 3
#     và đã nghĩ đủ AI_MIN_THINK_TIME; nếu quá 15 giây thì bắt buộc dừng.
# ============================================================
def search_with_iterative_deepening(board, algorithm, ai_player, human_player, stats, start_time, limit, last_human_move=None):
    fallback = get_search_moves(board, ai_player, human_player, last_human_move, limit=1)
    best_move = fallback[0] if fallback else None
    best_score = tactical_move_score(board, best_move, ai_player, human_player, last_human_move) if best_move else 0

    for depth in range(1, AI_ITERATIVE_MAX_DEPTH + 1):
        stats["current_depth"] = depth
        stats["timeout"] = False
        move, score, completed = root_search(board, depth, algorithm, ai_player, human_player, stats, start_time, limit, last_human_move)
        if completed and move is not None:
            best_move, best_score = move, score
            stats["completed_depth"] = depth
            stats["best_move"] = best_move
            stats["best_score"] = best_score
        elapsed = time.perf_counter() - start_time
        if elapsed >= limit:
            break
        if stats["completed_depth"] >= AI_MIN_COMPLETED_DEPTH and elapsed >= AI_MIN_THINK_TIME:
            break
    # Nếu đã hoàn thành depth tối thiểu nhưng chưa đủ min time, chờ nhẹ để người xem thấy AI suy nghĩ.
    while time.perf_counter() - start_time < AI_MIN_THINK_TIME and not time_up(start_time, limit):
        time.sleep(0.02)
    stats["time"] = time.perf_counter() - start_time
    stats["current_move"] = None
    return best_move, best_score


# ============================================================
# Hàm: get_ai_move()
# Mục đích:
#   - Hàm duy nhất main.py gọi để lấy nước đi của AI.
#   - Trước khi tìm sâu, xử lý thắng ngay/chặn thắng ngay.
#   - Sau đó dùng Iterative Deepening + Minimax/Alpha-Beta.
# ============================================================
def get_ai_move(board, algorithm, ai_player, human_player, depth=AI_DEPTH, time_limit=AI_TIME_LIMIT, last_human_move=None, external_stats=None):
    stats = external_stats if external_stats is not None else create_ai_stats(algorithm, depth)
    if external_stats is not None:
        stats.clear()
        stats.update(create_ai_stats(algorithm, depth))
    start = time.perf_counter()

    win_move = find_immediate_winning_move(board, ai_player)
    if win_move is not None:
        stats.update({"best_move": win_move, "completed_depth": AI_MIN_COMPLETED_DEPTH, "time": time.perf_counter() - start, "note": "AI thắng ngay."})
        return {"move": win_move, "score": WIN_SCORE, "stats": stats}

    block_move = find_immediate_winning_move(board, human_player)
    if block_move is not None:
        stats.update({"best_move": block_move, "completed_depth": AI_MIN_COMPLETED_DEPTH, "time": time.perf_counter() - start, "note": "AI chặn thắng ngay."})
        return {"move": block_move, "score": evaluate_board(board, ai_player, human_player), "stats": stats}

    move, score = search_with_iterative_deepening(board, algorithm, ai_player, human_player, stats, start, time_limit, last_human_move)
    stats["time"] = time.perf_counter() - start
    stats["best_move"] = move
    stats["best_score"] = score
    return {"move": move, "score": score, "stats": stats}
