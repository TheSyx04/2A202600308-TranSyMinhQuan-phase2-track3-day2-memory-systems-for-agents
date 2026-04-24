# BENCHMARK - Multi-Memory Agent (bản cá nhân)

Mục tiêu: so sánh no-memory và with-memory trên 10 multi-turn conversations.
Lưu ý: dữ liệu benchmark trong file JSON dùng câu không dấu để tiện so khớp tự động.

| # | Category | Scenario | Turns | No-memory result | With-memory result | Prompt chars | Prompt words | Pass? |
|---|----------|----------|------:|------------------|--------------------|-------------:|-------------:|-------|
| 1 | profile_recall | Nhớ tên người dùng sau nhiều turn | 6 | Mình không có dữ liệu lịch sử để trả lời chính xác. | Bạn tên là Minh Châu. | 1000 | 167 | Pass |
| 2 | profile_recall | Nhớ nghề nghiệp sau hội thoại dài | 5 | Mình không có dữ liệu lịch sử để trả lời chính xác. | Bạn đang làm QA automation ở công ty fintech. | 1000 | 163 | Pass |
| 3 | profile_recall | Nhớ sở thích công cụ làm việc | 4 | Mình không có dữ liệu lịch sử để trả lời chính xác. | Sở thích đã lưu: Neovim hơn VS Code khi code backend. | 1000 | 167 | Pass |
| 4 | conflict_update | Cập nhật fact profile bị mâu thuẫn | 3 | Mình không chắc vì không có memory profile. | Thông tin mới nhất: bạn dị ứng đậu nành. | 782 | 127 | Pass |
| 5 | episodic_recall | Nhớ kết quả task vừa hoàn thành | 3 | Mình không nhớ được sự kiện trước đó khi không bật memory. | Episode gần đây: Sáng nay tôi sửa xong bug login redirect. \| Kết quả là user đăng nhập không bị đẩy về trang cũ nữa. (outcome=completed_or_reported). | 1000 | 170 | Pass |
| 6 | episodic_recall | Nhớ sự kiện on-call gần đây | 4 | Mình không nhớ được sự kiện trước đó khi không bật memory. | Episode gần đây: Đêm qua tôi đã xử lý xong sự cố API 503. \| Nguyên nhân là timeout chuỗi gọi service nội bộ. \| Tôi đặt retry 2 lần và mở rộng timeout lên 8 giây. (outcome=completed_or_reported). | 1000 | 167 | Pass |
| 7 | semantic_retrieval | Lấy kiến thức semantic về Docker | 3 | Có thể cần xem lại cấu hình kết nối DB. | Khi app chạy trong Docker Compose, kết nối database nên dùng tên service (ví dụ: db) thay vì localhost. | 1000 | 160 | Pass |
| 8 | semantic_retrieval | Lấy kiến thức semantic về conflict handling | 3 | No-memory mode: trả lời dựa trên câu hỏi hiện tại. | Gợi ý từ semantic memory: Khi user sửa thông tin profile, giá trị mới nhất cần overwrite giá trị cũ để tránh memory mâu thuẫn. | 1000 | 165 | Pass |
| 9 | trim_budget | Kiểm thử trim context với hội thoại dài | 10 | Cần có cơ chế quản lý context budget. | Ưu tiên trim theo thứ tự: profile quan trọng, episodic mới nhất, semantic liên quan, rồi đến recent conversation. | 1000 | 171 | Pass |
| 10 | mixed_recall | Kết hợp profile + episodic + semantic | 5 | No-memory mode: trả lời dựa trên câu hỏi hiện tại. | Bạn là Bảo Trân và tôi làm SRE. Episode gần đây: Tôi vừa fix xong cảnh báo CPU đột biến trên service billing. \| Nguyên nhân là retry policy quá nóng gây request burst. \| Tôi đã giảm retry và thêm jitter.. Guideline timeout: Nếu API timeout bất thường, ưu tiên thêm timeout rõ ràng, retry có giới hạn, và exponential backoff để tránh quá tải. | 1000 | 160 | Pass |

Tổng kết: 10/10 scenario đạt expectation with-memory.

## Coverage check

- profile_recall: scenario 1, 2, 3
- conflict_update: scenario 4
- episodic_recall: scenario 5, 6
- semantic_retrieval: scenario 7, 8
- trim_budget: scenario 9
- mixed_recall: scenario 10