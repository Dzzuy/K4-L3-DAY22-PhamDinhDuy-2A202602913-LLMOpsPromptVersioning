# Phân tích RAGAS V1 và V2

Thí nghiệm dùng cùng 50 cặp câu hỏi–đáp án chuẩn, cùng kho tài liệu, cách chia đoạn và retriever `k=3` cho cả hai prompt. Mỗi phiên bản được chấm bằng bốn chỉ số RAGAS; kết quả chi tiết ở `03_ragas_report.json`.

| Chỉ số | V1 | V2 |
|---|---:|---:|
| Faithfulness | 0.9643 | 0.9423 |
| Answer relevancy | 0.9126 | 0.9055 |
| Context recall | 1.0000 | 1.0000 |
| Context precision | 0.9417 | 0.9417 |

V1 cao hơn ở faithfulness và answer relevancy; hai phiên bản hòa ở context recall và gần như bằng nhau ở context precision. **Cả hai vượt ngưỡng faithfulness 0.9, đạt tiêu chí bonus +3 trong lượt đo này.** Một cách giải thích hợp lý là prompt V1 yêu cầu trả lời ngắn và trực tiếp nên tạo ít mệnh đề có nguy cơ không được context hỗ trợ. Prompt V2 đã được sửa để chỉ nêu một chi tiết hỗ trợ có trong context; điểm V2 tăng từ 0.8929 ở lượt trước lên 0.9423 ở lượt này. Đây là suy luận từ thiết kế prompt và điểm tổng hợp, chưa phải phân tích nhân quả cho từng câu. Context recall giống nhau phù hợp với việc cả hai dùng cùng retriever và tập câu hỏi.

Các điểm được tạo bằng RAGAS với LLM evaluator, nên có thể thay đổi khi chạy lại hoặc đổi model. Log chạy thực tế nằm trong `03_ragas_run_log.txt`.
