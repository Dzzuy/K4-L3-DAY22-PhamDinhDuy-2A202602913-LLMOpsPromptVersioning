# Báo cáo Lab Day 22 — LLMOps và Prompt Versioning

**Học viên:** Phạm Đình Duy<br>
**MSSV:** 2A202602913<br>
**Repo:** [K4-L3-DAY22-PhamDinhDuy-2A202602913-LLMOpsPromptVersioning](https://github.com/Dzzuy/K4-L3-DAY22-PhamDinhDuy-2A202602913-LLMOpsPromptVersioning)<br>
**LangSmith project:** URL lưu trong [`evidence/LangSmithURL.txt`](evidence/LangSmithURL.txt). [Trace mẫu công khai](https://smith.langchain.com/public/fdfebbfb-92f1-490c-be7c-d2b573679503/r/01a119e9-6399-7440-bc7d-90760141fa9b?start_time=2026-10-08T05%3A08%3A08.217785Z). [Project](https://smith.langchain.com/o/bcadaffe-703a-43db-b490-1ab2ed4bb607/projects/p/5a1fdc71-6aa5-4fbb-aae5-feb11d06154b) (quyền truy cập công khai chưa được xác nhận).

## 1. Mục tiêu và luồng hệ thống

Lab xây một hệ thống hỏi đáp trên `data/knowledge_base.txt`. Tài liệu được chia thành đoạn, chuyển thành embedding và lập chỉ mục FAISS. Với mỗi câu hỏi, retriever lấy ba đoạn gần nghĩa nhất và đưa vào prompt cho LLM. LangSmith ghi trace của quá trình này. Hai prompt V1/V2 được quản lý trên Prompt Hub và phân phối bằng hash của `request_id`. RAGAS so sánh chất lượng câu trả lời. Guardrails kiểm tra đầu ra để che PII và sửa JSON lỗi.

Luồng chính: **câu hỏi → retriever → ba đoạn context → prompt → LLM → câu trả lời → trace/đánh giá/kiểm tra đầu ra**.

## 2. Thực hiện và bằng chứng

| Phase | Công việc và ý nghĩa | Bằng chứng |
|---|---|
| 1. RAG + tracing | Chia tài liệu thành 107 chunks (`chunk_size=500`, `chunk_overlap=50`), tạo FAISS và truy xuất `k=3`. Chạy 50 câu hỏi; trace giúp xem lỗi đến từ truy xuất hay sinh câu trả lời. | [Ảnh LangSmith](evidence/01_langsmith_traces.png), `src/01_langsmith_rag_pipeline.py` |
| 2. Prompt Hub + A/B | Đẩy và kéo hai prompt có hành vi khác nhau. Hash MD5 định tuyến 50 request ổn định: V1=19, V2=31. | [Ảnh Prompt Hub](evidence/02_prompt_hub.png), [log A/B](evidence/02_ab_routing_log.txt) |
| 3. RAGAS | Chạy cùng 50 cặp QA qua **mỗi** prompt, giữ context dưới dạng `list[str]`, chấm bốn chỉ số. | [Ảnh điểm mới](evidence/03_ragas_scores.png), [JSON report](evidence/03_ragas_report.json), [log chạy](evidence/03_ragas_run_log.txt). |
| 4. Guardrails | Tự viết hai validator. `FailResult(fix_value=...)` làm Guardrails thay output; PII sạch giữ nguyên, PII bị che; JSON lỗi được sửa hoặc trả JSON dự phòng. | [PII log](evidence/04_pii_demo_log.txt), [JSON log](evidence/04_json_demo_log.txt), `tests/test_guardrails_validators.py` |

LangSmith API đã xác nhận 50 root traces `rag-query` và 50 root traces `ab-rag-query`. Trace mẫu có retriever, prompt, LLM và parser. Chat và embeddings chạy qua OpenRouter; cấu hình này dùng cùng `OPENROUTER_API_KEY`, không dùng OpenAI key riêng.

## 3. Kết quả RAGAS và nhận xét

| Chỉ số | V1 | V2 | Ý nghĩa |
|---|---:|---:|---|
| Faithfulness | **0.9643** | **0.9423** | Mức độ câu trả lời bám vào context. Cả hai vượt ngưỡng bonus 0.9. |
| Answer relevancy | **0.9126** | 0.9055 | Mức độ trả lời đúng trọng tâm câu hỏi. |
| Context recall | 1.0000 | 1.0000 | Context tìm được bao phủ thông tin của đáp án chuẩn. |
| Context precision | 0.9417 | 0.9417 | Mức độ liên quan của các đoạn context được truy xuất. |

V1 cao hơn ở faithfulness và answer relevancy; context recall hòa, còn context precision gần như bằng nhau (chênh lệch dưới 0.00000000001). **Giả thuyết:** V1 yêu cầu trả lời ngắn và trực tiếp nên tạo ít mệnh đề thiếu bằng chứng hơn V2. Sau khi V2 được sửa để chỉ nêu kết luận và một chi tiết có trong context, faithfulness của V2 tăng từ 0.8929 ở lần chạy trước lên 0.9423 trong lần chạy này. Đây là so sánh hai lượt chạy có tính ngẫu nhiên của LLM, chưa phải chứng minh quan hệ nhân quả. Cả hai dùng cùng tài liệu, retriever và tập câu hỏi. **Tiêu chí bonus +3 faithfulness ≥0.9 ở cả hai phiên bản: đạt trong lần đo này.**

## 4. Reflection: điều học được và giới hạn

- **Quan sát được mới gỡ lỗi được:** Một câu trả lời sai có thể do retriever lấy sai đoạn hoặc do LLM diễn giải sai đoạn đúng. Trace thể hiện cả hai khâu.
- **Prompt là thành phần cần quản lý phiên bản:** Push/pull giúp biết bản nào đã chạy. Hash của `request_id` giữ cách phân nhóm ổn định giữa các lần chạy; phân phối không bắt buộc chính xác 25/25.
- **Đánh giá cần dữ liệu đúng cấu trúc:** RAGAS cần câu hỏi, câu trả lời, đáp án chuẩn và danh sách các context riêng biệt. Điểm tổng hợp hữu ích để so sánh nhưng không thay thế việc xem những câu cụ thể bị chấm thấp.
- **Validation phải sửa output thật:** Việc chỉ phát hiện PII không đủ. Với `OnFailAction.FIX`, `FailResult(fix_value=...)` là phần quyết định đầu ra được thay bằng chuỗi an toàn.
- **Giới hạn hiện tại:** Regex PII chưa bao phủ mọi định dạng và không xác minh checksum số thẻ. Sửa JSON bằng cách thay mọi dấu nháy đơn là giải pháp cho test case lab, có thể làm sai chuỗi chứa dấu nháy hợp lệ. Điểm RAGAS phụ thuộc LLM evaluator nên có thể thay đổi khi chạy lại. Lab dùng dữ liệu giả và tài liệu cố định; kết quả chưa chứng minh chất lượng trên dữ liệu thực tế.

## 5. AI usage — công khai để review

Tôi có sử dụng Codex để hỗ trợ viết code, tìm lỗi và kiểm tra lại các phần đã làm. Tôi cũng dùng ChatGPT để hỏi thêm những chỗ chưa hiểu. Tôi chủ yếu tự đọc yêu cầu từng checkpoint và trong các function code rồi trao đổi với Codex để Codex triển khai. Sau đó tôi xem lại code, chạy thử và kiểm tra kết quả. Phần cấu hình môi trường, LangSmith, kiểm tra traces, prompts và chụp evidence tôi đều tự thực hiện, kiểm tra traces cũng có sự hỗ trợ của Codex. Tôi dùng AI như một công cụ hỗ trợ lập trình để làm việc nhanh hơn, không chỉ giao toàn bộ bài cho AI làm. Tôi vẫn cần hiểu code đang làm gì và kiểm tra xem kết quả có đúng yêu cầu hay không.

## 6. Kiểm tra đã chạy

- Phase 1: 50/50 câu trả lời; LangSmith có 50 `rag-query` root traces với các bước con cần thiết.
- Phase 2: push/pull hai prompt thành công; 50 `ab-rag-query` root traces; routing 19/31.
- Phase 3: 50 cặp QA cho cả V1 và V2; báo cáo JSON có đủ bốn điểm hữu hạn cho mỗi phiên bản. Faithfulness V1=0.9643 và V2=0.9423, đều đạt ngưỡng bonus 0.9.
- Phase 4: 6 case PII và 5 case JSON chạy; hai test hồi quy pass; `run_all.py --step 4` pass.
- `pip check`, kiểm tra cú pháp liên quan và `git diff --check` pass. Chưa chạy lại toàn bộ `run_all.py` trong **một** lượt sau khi ghim dependencies vì Phase 3 tốn nhiều API calls và khoảng 20 phút; từng phase đã được kiểm tra riêng.

## 7. Trước khi nộp

Xem [SUBMISSION.md](SUBMISSION.md) để đối chiếu 7 file evidence, kiểm tra `.env` không bị Git theo dõi, rà bí mật trong code/log/ảnh, và nộp **cả URL GitHub repo lẫn URL LangSmith project** trên LMS. Ảnh RAGAS hiện có thể hiện V1=0.9643 và V2=0.9423; ảnh Prompt Hub đã được thay bằng bản che email. Kiểm tra quyền truy cập LangSmith bằng cửa sổ ẩn danh nếu muốn nhận điểm thưởng link công khai.
