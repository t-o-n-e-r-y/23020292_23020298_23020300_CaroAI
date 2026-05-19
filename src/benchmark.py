"""
benchmark.py
------------
File thực nghiệm so sánh Minimax và Alpha-Beta cho bài tập lớn Cờ Caro.

Cách chạy:
    python benchmark.py

Cách đổi độ sâu:
    Sửa trong config.py:
        BENCHMARK_DEPTH = 2
    hoặc:
        BENCHMARK_DEPTH = 3

Ý tưởng:
- Mỗi lần chạy chỉ kiểm thử một độ sâu duy nhất.
- Chạy Minimax và Alpha-Beta trên cùng các trạng thái bàn cờ.
- Dùng cùng độ sâu, cùng hàm đánh giá, cùng trạng thái.
- Đo nước đi, điểm đánh giá, số node, số nhánh cắt và thời gian.
- In bảng kết quả giống dạng console trong báo cáo.
- Có xử lý nhanh nước thắng ngay / chặn thắng ngay để phản ánh đúng logic AI chơi thật.
"""

import time
import copy
import csv

try:
    from .config import BOARD_SIZE, EMPTY, BENCHMARK_DEPTH, BENCHMARK_TIME_LIMIT, WIN_SCORE
    from .ai import create_ai_stats, root_search, find_immediate_winning_move
    from .evaluation import evaluate_board
except ImportError:
    from config import BOARD_SIZE, EMPTY, BENCHMARK_DEPTH, BENCHMARK_TIME_LIMIT, WIN_SCORE
    from ai import create_ai_stats, root_search, find_immediate_winning_move
    from evaluation import evaluate_board


AI_PLAYER = "O"
HUMAN_PLAYER = "X"
OUTPUT_CSV = f"benchmark_depth_{BENCHMARK_DEPTH}.csv"


def empty_board():
    return [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


def place(board, moves):
    for r, c, player in moves:
        board[r][c] = player
    return board


def build_test_states():
    states = []

    b1 = empty_board()
    place(b1, [
        (5, 5, HUMAN_PLAYER),
    ])
    states.append({
        "name": "Đầu ván",
        "board": b1,
        "last_human_move": (5, 5),
    })

    b2 = empty_board()
    place(b2, [
        (5, 5, HUMAN_PLAYER), (5, 6, AI_PLAYER),
        (6, 5, HUMAN_PLAYER), (4, 5, AI_PLAYER),
        (6, 6, HUMAN_PLAYER), (4, 6, AI_PLAYER),
        (7, 5, HUMAN_PLAYER), (3, 5, AI_PLAYER),
    ])
    states.append({
        "name": "Giữa ván",
        "board": b2,
        "last_human_move": (7, 5),
    })

    b3 = empty_board()
    place(b3, [
        (5, 4, AI_PLAYER), (5, 5, AI_PLAYER), (5, 6, AI_PLAYER),
        (4, 4, HUMAN_PLAYER), (6, 4, HUMAN_PLAYER),
        (4, 5, HUMAN_PLAYER),
    ])
    states.append({
        "name": "AI có thể thắng ngay",
        "board": b3,
        "last_human_move": (4, 5),
    })

    b4 = empty_board()
    place(b4, [
        (6, 3, HUMAN_PLAYER), (6, 4, HUMAN_PLAYER), (6, 5, HUMAN_PLAYER),
        (5, 5, AI_PLAYER), (4, 5, AI_PLAYER),
        (7, 7, AI_PLAYER),
    ])
    states.append({
        "name": "Người sắp thắng",
        "board": b4,
        "last_human_move": (6, 5),
    })

    b5 = empty_board()
    place(b5, [
        (5, 5, HUMAN_PLAYER), (5, 6, HUMAN_PLAYER),
        (6, 5, HUMAN_PLAYER),
        (4, 4, AI_PLAYER), (4, 5, AI_PLAYER),
        (3, 4, AI_PLAYER),
        (6, 6, HUMAN_PLAYER), (3, 5, AI_PLAYER),
    ])
    states.append({
        "name": "Hai bên cùng tấn công",
        "board": b5,
        "last_human_move": (6, 6),
    })

    b6 = empty_board()
    place(b6, [
        (3, 3, HUMAN_PLAYER), (7, 3, AI_PLAYER),
        (6, 5, HUMAN_PLAYER), (7, 7, AI_PLAYER),
        (5, 5, HUMAN_PLAYER), (4, 4, AI_PLAYER),
        (5, 6, HUMAN_PLAYER), (7, 4, AI_PLAYER),
        (6, 4, HUMAN_PLAYER), (4, 5, AI_PLAYER),
        (7, 6, HUMAN_PLAYER), (6, 3, AI_PLAYER),
    ])
    states.append({
        "name": "Nhiều nhánh",
        "board": b6,
        "last_human_move": (7, 6),
    })

    return states


def quick_tactical_result(test_board, state_name, algorithm, start):
    """
    Kiểm tra nhanh giống logic trong get_ai_move():
    1. Nếu AI thắng ngay thì chọn nước thắng ngay.
    2. Nếu người chơi sắp thắng thì chọn nước chặn ngay.

    Mục đích:
    - Tránh tình huống benchmark bắt thuật toán tìm kiếm sâu trong khi game thật sẽ đi ngay.
    - Làm thời gian của các trạng thái chắc chắn trở nên hợp lý hơn.
    """
    algorithm_name = "Minimax" if algorithm == "minimax" else "Alpha-Beta"

    win_move = find_immediate_winning_move(test_board, AI_PLAYER)
    if win_move is not None:
        elapsed = time.perf_counter() - start
        return {
            "state": state_name,
            "algorithm": algorithm_name,
            "depth": BENCHMARK_DEPTH,
            "move": win_move,
            "score": WIN_SCORE,
            "nodes": 0,
            "cutoffs": 0,
            "time": elapsed,
            "completed": True,
            "note": "AI thắng ngay",
        }

    block_move = find_immediate_winning_move(test_board, HUMAN_PLAYER)
    if block_move is not None:
        elapsed = time.perf_counter() - start
        return {
            "state": state_name,
            "algorithm": algorithm_name,
            "depth": BENCHMARK_DEPTH,
            "move": block_move,
            "score": evaluate_board(test_board, AI_PLAYER, HUMAN_PLAYER),
            "nodes": 0,
            "cutoffs": 0,
            "time": elapsed,
            "completed": True,
            "note": "AI chặn thắng ngay",
        }

    return None


def run_algorithm(board, state_name, algorithm, last_human_move=None):
    test_board = copy.deepcopy(board)
    stats = create_ai_stats(algorithm=algorithm, depth=BENCHMARK_DEPTH)

    start = time.perf_counter()

    quick_result = quick_tactical_result(test_board, state_name, algorithm, start)
    if quick_result is not None:
        return quick_result

    move, score, completed = root_search(
        board=test_board,
        depth=BENCHMARK_DEPTH,
        algorithm=algorithm,
        ai_player=AI_PLAYER,
        human_player=HUMAN_PLAYER,
        stats=stats,
        start_time=start,
        limit=BENCHMARK_TIME_LIMIT,
        last_human_move=last_human_move,
    )

    elapsed = time.perf_counter() - start

    return {
        "state": state_name,
        "algorithm": "Minimax" if algorithm == "minimax" else "Alpha-Beta",
        "depth": BENCHMARK_DEPTH,
        "move": move,
        "score": score,
        "nodes": stats.get("nodes", 0),
        "cutoffs": stats.get("cutoffs", 0),
        "time": elapsed,
        "completed": completed,
        "note": "Tìm kiếm",
    }


def print_main_table(rows):
    print("=" * 148)
    print(
        f"{'Trạng thái':<28}"
        f"{'Thuật toán':<16}"
        f"{'Depth':<8}"
        f"{'Nước đi':<14}"
        f"{'Điểm':<16}"
        f"{'Nodes':<14}"
        f"{'Cutoffs':<12}"
        f"{'Time(s)':<12}"
        f"{'Complete':<10}"
        f"{'Ghi chú':<18}"
    )
    print("=" * 148)

    for r in rows:
        print(
            f"{r['state']:<28}"
            f"{r['algorithm']:<16}"
            f"{r['depth']:<8}"
            f"{str(r['move']):<14}"
            f"{int(r['score']):<16}"
            f"{r['nodes']:<14}"
            f"{r['cutoffs']:<12}"
            f"{r['time']:<12.6f}"
            f"{str(r['completed']):<10}"
            f"{r.get('note', ''):<18}"
        )

    print("=" * 148)


def analyze_pairs(rows):
    analysis = []

    for i in range(0, len(rows), 2):
        minimax = rows[i]
        alphabeta = rows[i + 1]

        same_move = minimax["move"] == alphabeta["move"]

        node_diff = minimax["nodes"] - alphabeta["nodes"]
        if minimax["nodes"] > 0:
            node_percent = node_diff / minimax["nodes"] * 100
        else:
            node_percent = 0

        time_diff = minimax["time"] - alphabeta["time"]
        if minimax["time"] > 0:
            time_percent = time_diff / minimax["time"] * 100
        else:
            time_percent = 0

        if minimax["nodes"] == 0 and alphabeta["nodes"] == 0:
            comment = "Tình huống chắc chắn, AI xử lý nhanh bằng luật thắng/chặn ngay."
        elif node_diff > 0:
            comment = "Alpha-Beta giảm số trạng thái đã xét nhờ cắt nhánh."
        elif node_diff == 0:
            comment = "Số node bằng nhau, có thể do độ sâu thấp hoặc chưa phát sinh điều kiện cắt nhánh rõ."
        else:
            comment = "Alpha-Beta xét nhiều node hơn, cần xem lại thứ tự duyệt nước hoặc đặc điểm trạng thái."

        analysis.append({
            "state": minimax["state"],
            "same_move": same_move,
            "node_diff": node_diff,
            "node_percent": node_percent,
            "time_diff": time_diff,
            "time_percent": time_percent,
            "cutoffs": alphabeta["cutoffs"],
            "comment": comment,
        })

    return analysis


def print_analysis_table(analysis):
    print("\n")
    print("=" * 148)
    print("BẢNG PHÂN TÍCH SO SÁNH MINIMAX VÀ ALPHA-BETA")
    print("=" * 148)
    print(
        f"{'Trạng thái':<28}"
        f"{'Cùng nước?':<14}"
        f"{'Giảm node':<14}"
        f"{'Giảm node (%)':<16}"
        f"{'Cutoffs':<12}"
        f"{'Giảm time (%)':<16}"
        f"{'Nhận xét':<40}"
    )
    print("-" * 148)

    for r in analysis:
        print(
            f"{r['state']:<28}"
            f"{str(r['same_move']):<14}"
            f"{r['node_diff']:<14}"
            f"{r['node_percent']:<16.2f}"
            f"{r['cutoffs']:<12}"
            f"{r['time_percent']:<16.2f}"
            f"{r['comment']:<40}"
        )

    print("=" * 148)


def save_csv(rows, analysis):
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)

        writer.writerow(["BẢNG KẾT QUẢ THỰC NGHIỆM"])
        writer.writerow([
            "Trạng thái", "Thuật toán", "Depth", "Nước đi",
            "Điểm", "Nodes", "Cutoffs", "Time(s)", "Completed", "Ghi chú"
        ])

        for r in rows:
            writer.writerow([
                r["state"],
                r["algorithm"],
                r["depth"],
                r["move"],
                r["score"],
                r["nodes"],
                r["cutoffs"],
                r["time"],
                r["completed"],
                r.get("note", ""),
            ])

        writer.writerow([])
        writer.writerow(["BẢNG PHÂN TÍCH SO SÁNH"])
        writer.writerow([
            "Trạng thái",
            "Alpha-Beta cùng nước với Minimax?",
            "Giảm node",
            "Giảm node (%)",
            "Cutoffs",
            "Giảm time (%)",
            "Nhận xét",
        ])

        for r in analysis:
            writer.writerow([
                r["state"],
                r["same_move"],
                r["node_diff"],
                r["node_percent"],
                r["cutoffs"],
                r["time_percent"],
                r["comment"],
            ])

    print(f"\nĐã lưu file kết quả: {OUTPUT_CSV}")


def print_report_summary(analysis):
    total = len(analysis)
    same_count = sum(1 for r in analysis if r["same_move"])

    searchable = [r for r in analysis if not (r["node_diff"] == 0 and r["cutoffs"] == 0 and "chắc chắn" in r["comment"])]
    if searchable:
        avg_node_percent = sum(r["node_percent"] for r in searchable) / len(searchable)
        avg_time_percent = sum(r["time_percent"] for r in searchable) / len(searchable)
    else:
        avg_node_percent = 0
        avg_time_percent = 0

    print("\n")
    print("=" * 130)
    print("TÓM TẮT NHẬN XÉT CHO BÁO CÁO")
    print("=" * 130)
    print(f"- Độ sâu thực nghiệm: {BENCHMARK_DEPTH}")
    print(f"- Số trạng thái kiểm thử: {total}")
    print(f"- Alpha-Beta chọn cùng nước với Minimax: {same_count}/{total}")
    print(f"- Tỷ lệ giảm node trung bình ở các trạng thái cần tìm kiếm: {avg_node_percent:.2f}%")
    print(f"- Tỷ lệ giảm thời gian trung bình ở các trạng thái cần tìm kiếm: {avg_time_percent:.2f}%")
    print(
        "- Nhận xét: Alpha-Beta giữ nguyên nguyên lý lựa chọn của Minimax "
        "nhưng sử dụng điều kiện beta <= alpha để cắt bỏ các nhánh không cần thiết. "
        "Với các trạng thái có nước thắng ngay hoặc cần chặn thắng ngay, chương trình xử lý "
        "bằng luật chiến thuật trực tiếp nên số node bằng 0 và thời gian rất nhỏ. "
        "Với các trạng thái còn phải tìm kiếm, số node và thời gian phản ánh hiệu quả thực tế "
        "của Minimax và Alpha-Beta ở cùng độ sâu."
    )
    print("=" * 130)


def main():
    states = build_test_states()
    rows = []

    print(f"\nĐang chạy benchmark với BENCHMARK_DEPTH = {BENCHMARK_DEPTH}")
    print("Mỗi trạng thái sẽ chạy Minimax trước, sau đó chạy Alpha-Beta.\n")

    for state in states:
        print(f"Đang chạy trạng thái: {state['name']} - Minimax...", flush=True)
        minimax_result = run_algorithm(
            board=state["board"],
            state_name=state["name"],
            algorithm="minimax",
            last_human_move=state["last_human_move"],
        )
        rows.append(minimax_result)

        print(f"Đang chạy trạng thái: {state['name']} - Alpha-Beta...", flush=True)
        alphabeta_result = run_algorithm(
            board=state["board"],
            state_name=state["name"],
            algorithm="alphabeta",
            last_human_move=state["last_human_move"],
        )
        rows.append(alphabeta_result)

    analysis = analyze_pairs(rows)

    print()
    print_main_table(rows)
    print_analysis_table(analysis)
    save_csv(rows, analysis)
    print_report_summary(analysis)


if __name__ == "__main__":
    main()
