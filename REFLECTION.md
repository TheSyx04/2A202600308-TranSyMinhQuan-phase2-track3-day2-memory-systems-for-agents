# Reflection - Privacy & Limitations (bản cá nhân)

## 1) Điều tôi thấy hiệu quả nhất trong bài này

Điểm mạnh nhất của agent hiện tại là kết hợp được 4 lớp memory theo đúng vai trò. Trong đó:
- Profile memory giúp trả lời các câu hỏi “bạn nhớ tôi là ai/làm gì không”.
- Episodic memory giúp bám được các việc vừa hoàn tất.
- Semantic memory giúp trả lời các câu hỏi cần kiến thức nền (Docker, timeout, retry).

Nếu chỉ chọn một loại “tạo khác biệt rõ nhất”, tôi chọn semantic memory, vì nó giúp agent không bị bó buộc trong lịch sử chat.

## 2) Memory nhạy cảm/rủi ro nhất

Tôi đánh giá long-term profile là nhạy cảm nhất, đặc biệt các field liên quan sức khỏe như dị ứng. Nếu retrieve nhầm người dùng hoặc dữ liệu cũ chưa được sửa, câu trả lời có thể gây hiểu lầm nghiêm trọng hơn các lỗi kỹ thuật thông thường.

## 3) Rủi ro riêng tôi quan sát trong lúc làm

- Rủi ro 1: benchmark probe có thể vô tình bị hệ thống hiểu như fact mới và ghi đè profile.
	- Tôi đã chặn bằng rule bỏ qua update khi input là câu hỏi (`?`).
- Rủi ro 2: episodic summary chứa thông tin vận hành nội bộ (incident, timeout, retry).
	- Nếu log này bị lộ ra ngoài phạm vi cho phép thì vẫn là rò rỉ thông tin.
- Rủi ro 3: semantic retrieval theo keyword có thể lấy trúng đoạn “liên quan một phần” nhưng chưa đúng ngữ cảnh.

## 4) Consent, TTL, deletion nên làm thế nào

Với bản lab này tôi chưa triển khai đầy đủ policy, nhưng cách đúng nên là:
- Consent: chỉ bật lưu profile khi user đồng ý rõ.
- TTL: episode nên có hạn lưu để tránh tích lũy dữ liệu nhạy cảm.
- Deletion: xóa đồng bộ tại profile store, episodic store và short-term RAM.
- Verification: sau khi xóa phải có bước kiểm tra lại từng backend.

## 5) Limitation kỹ thuật hiện tại

- Semantic retrieval mới là keyword fallback, chưa phải vector search thật.
- Trim budget đang theo số ký tự, chưa theo tokenizer thực tế.
- Fact extraction còn rule-based, chưa có confidence scoring.
- Backend JSON phù hợp demo/lab, chưa phù hợp tải lớn và ghi đồng thời.

## 6) Nếu scale lớn thì điểm nghẽn ở đâu

Khi tăng số user, tôi dự đoán bottleneck xuất hiện theo thứ tự:
1. Ghi file JSON liên tục gây chậm I/O và khó tránh race condition.
2. Keyword retrieval giảm precision khi corpus lớn.
3. Không có hệ metric rõ (hit-rate, false-recall, stale-memory) nên khó tuning.

## 7) Hướng nâng cấp tôi muốn làm tiếp

- Chuyển profile/episodic sang DB có transaction.
- Nâng semantic memory sang embeddings + FAISS/Chroma.
- Áp dụng tokenizer thật để kiểm soát budget sát chi phí.
- Thêm cơ chế quản trị dữ liệu: consent flag, TTL policy, hard-delete workflow.
