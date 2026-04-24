# Lab #17 - Multi-Memory Agent (Skeleton LangGraph Flow)

## 1) Mục tiêu bài làm

Bài này triển khai một agent có đầy đủ 4 lớp memory:
- short-term memory
- long-term profile memory
- episodic memory
- semantic memory

Flow được thiết kế theo hướng LangGraph skeleton:
1. Nhận user input
2. Save/update memory (profile + episodic)
3. Router retrieve memory từ 4 backend vào `MemoryState`
4. Inject memory sections vào assembled prompt
5. Trim theo memory budget
6. Sinh câu trả lời with-memory

## 2) Cấu trúc thư mục

- `src/agent.py`: `MultiMemoryAgent`, `MemoryState`, `retrieve_memory`, prompt injection
- `src/memory_backends.py`: 4 backend memory và interface lưu/lấy
- `src/benchmark.py`: chạy 10 multi-turn conversations và sinh `BENCHMARK.md`
- `data/profile_store.json`: long-term profile store
- `data/episodes.json`: episodic log
- `data/semantic_corpus.json`: semantic knowledge corpus
- `data/benchmark_conversations.json`: 10 benchmark scenarios
- `BENCHMARK.md`: kết quả benchmark no-memory vs with-memory
- `REFLECTION.md`: privacy + limitations

## 3) Thiết kế memory

### 3.1 Short-term memory
- Kiểu: in-memory deque theo user
- Mục đích: giữ recent turns
- Interface: `add_message`, `get_recent`, `clear`

### 3.2 Long-term profile memory
- Kiểu: JSON KV store
- Mục đích: lưu facts profile bền vững
- Conflict policy: key trùng thì overwrite bằng giá trị mới nhất (có `updated_at`)
- Interface: `get_profile`, `update_fact`, `bulk_update`, `reset`

### 3.3 Episodic memory
- Kiểu: JSON list
- Mục đích: lưu sự kiện/task đã hoàn tất có kết quả
- Interface: `add_episode`, `get_recent`, `reset`

### 3.4 Semantic memory
- Kiểu: keyword retrieval từ corpus
- Mục đích: bổ sung tri thức ngoài hội thoại
- Interface: `retrieve(query, top_k)`

## 4) State/router và prompt injection

`MemoryState` gồm:
- `messages`
- `user_profile`
- `episodes`
- `semantic_hits`
- `memory_budget`
- `assembled_prompt`

Hàm `retrieve_memory(state, user_id, query)` sẽ:
- lấy profile từ profile store
- lấy episodes gần đây
- semantic retrieve theo query
- lấy recent conversation
- đóng gói thành 4 section: PROFILE, EPISODIC, SEMANTIC, RECENT
- trim theo memory budget

## 5) Save/update memory + conflict handling

- Profile extraction cập nhật các facts: name, occupation, preference, allergy
- Nếu user sửa fact allergy, giá trị mới overwrite giá trị cũ
- Episodic save kích hoạt bởi các marker completion/outcome
- Tránh lưu sai từ câu hỏi probe bằng cách bỏ qua input có dấu `?`

Test bắt buộc conflict:
- Tôi dị ứng sữa bò
- Tôi nói nhầm, tôi dị ứng đậu nành mới đúng
- Kết quả profile cuối cùng: `allergy = đậu nành`

## 6) Benchmark

Script benchmark:
- Chạy 10 multi-turn scenarios
- Mỗi scenario có no-memory baseline và with-memory result
- Chấm pass theo expected keywords
- Sinh `BENCHMARK.md` tự động

Nhóm test đã bao phủ:
- profile recall
- conflict update
- episodic recall
- semantic retrieval
- trim/token budget
- mixed recall

## 7) Cách chạy

Yêu cầu:
- Python 3.10+

Chạy benchmark:
- `python src/benchmark.py`

Kết quả:
- Sinh file `BENCHMARK.md` ở thư mục gốc

## 8) Ghi chú

Bài này ưu tiên clarity của memory architecture và benchmark flow.
Semantic retrieval hiện tại dùng keyword fallback để giữ bài gọn, phù hợp với phạm vi lab 2 giờ.
