# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: SCP404
- Members: Nguyễn Tuấn Phong (2A202603712), Lê Hoàng Sơn (2A202603662), Kim Đức Thắng (2A202603702)
- Provider/model: OpenAI `gpt-4o-mini` (`--provider openai`), temperature 0

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

> 1–2 câu mô tả agent dùng để làm gì (cho team khác hiểu nhanh).

Ví dụ: "Research agent: tìm tin theo từ khóa / theo tài khoản, đọc URL, tổng hợp thành digest, và gửi lên Telegram khi được xác nhận."

**Link dùng thử (deploy):**

> Dán link public để team khác mở thử ngay. Cách deploy nhanh bằng Cloudflare Tunnel xem README. Nếu deploy Vercel/Streamlit Cloud thì dán link đó.
>
> URL: 

## A2. Tool agent có

> Liệt kê các tool agent đang dùng (gồm tool mới nhóm tự thêm). Mỗi tool 1 dòng: tên + làm được gì.

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | hỏi lại người dùng khi thiếu thông tin | không |
|  |  |  |
|  |  |  |

## A3. Câu hỏi mẫu để thử

> 3–5 câu hỏi/yêu cầu mẫu để team khác tự thử agent ngay.

1.
2.
3.

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

Mọi run đều trên `data/eval_base.json` (20 case: 14 single turn, 6 multi turn). Mỗi version chỉ đổi **một** artifact để kiểm chứng **một** giả thuyết; hash trong cột Artifact Version cho thấy file nào đổi.

| Version | Changed Artifact | Artifact Version | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---|---:|---:|---|
| v0 | baseline (starter) | `v0+peb1c8179815b+t5b22a2476d41` | — | — | case 0.65 · routing 0.75 · args 0.65 · multi 1.0 | `runs/v0_B_base_openai_20261110T101806863676.json` |
| v1 | `system_prompt.md` | `v1+p718eda401f27+t5b22a2476d41` | Prompt starter cố ý bảo "đoán thay vì hỏi", "gửi ngay", "chỉ 1 tool". Thay bằng rule an toàn (clarify khi thiếu info, xác nhận trước khi send, từ chối out-of-scope, cho phép nhiều tool) sẽ sửa R08/R10/R11/R12/R14 | 0.65 | case **0.95** · routing 1.0 · args 0.95 · multi 1.0 | `runs/v1_B_base_openai_20261110T101915429959.json` |
| v2 | `tools.yaml` | `v2+p718eda401f27+t58b949f3cad1` | Description tool mơ hồ làm model bỏ sót args (R11 thiếu `response_type`). Viết lại description (làm gì / khi nào dùng / khi nào không) + convention args + `response_type` bắt buộc | 0.95 | case **0.90** ⬇ · routing 0.9 · args 0.9 · multi 0.83 | `runs/v2_B_base_openai_20261110T110749592420.json` |
| v3 | `system_prompt.md` | `v3+p3c4f06917491+t58b949f3cad1` | v2 gây regression: R01 hỏi lại thừa, M06 gọi lại tool user đã huỷ. Thêm routing rules ("tên người đã biết → tự map handle, không hỏi lại") + rule multi-turn "chỉ theo intent hiện tại, bỏ phần đã huỷ" | 0.90 | case **1.0** · routing 1.0 · args 1.0 · multi 1.0 | `runs/v3_B_base_openai_20261110T111803928857.json` |
| v4 | `tools.yaml` (+4 tool mới: `wikipedia`, `hackernews`, `github_repo`, `datetime_now`) | `v4+p3c4f06917491+t92f0376be02d` | Tăng từ 10 lên 14 tool có thể làm nhiễu routing; nếu description tool mới nói rõ khi nào dùng/không dùng thì base không bị regression | 1.0 | case **1.0** · routing 1.0 · args 1.0 · multi 1.0 | `runs/v4_B_base_openai_20261110T115937405999.json` |

Nhận xét:

- Bước nhảy lớn nhất (0.65 → 0.95) đến từ việc **bỏ chỉ dẫn xấu trong prompt**, không phải từ việc mô tả tool.
- v2 là một ví dụ regression thật: làm `clarify` "mạnh" hơn thì sửa được R11 nhưng model trở nên quá thận trọng (hỏi lại cả khi đã có tên người). Bài học: mỗi rule "hãy làm X" cần đi kèm ranh giới "khi nào KHÔNG làm X".
- v4 xác nhận thêm tool không làm hỏng routing cũ khi mỗi tool có mục "KHÔNG DÙNG khi…" chỉ sang tool đúng.

## B2. Failure Analysis

Lấy từ `results[*].result.actual_tool_calls` và `failures` trong run JSON. Bảng phẳng: `analysis/base_runs.csv`.

| Case ID | Version | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|---|
| R10_missing_handle | v0 | missing_info | `timeline(screenname="sama")` | "Tóm tắt 5 tweet mới nhất" không nói của ai → model tự đoán Sam Altman (đúng như prompt starter bảo) | v1: rule "không đoán, gọi `clarify(response_type="text")`" |
| R11_missing_url | v0 | missing_info | `fetch(url="https://example.com/article")` | "Tóm tắt bài viết này" không có link → model bịa URL | v1: rule không bịa URL, hỏi lại |
| R12_confirm_before_send | v0 | wrong_boundary | `send(text="Bản tin này")` | Gửi Telegram ngay, không hỏi xác nhận | v1: phải `clarify(response_type="yes_no")` trước; `send` chỉ khi `confirmed=true` |
| R08_out_of_scope | v0 | out_of_scope | `send(text="Nguyên hàm của x^2 là…")` | Câu toán ngoài phạm vi, model còn dùng `send` để "trả lời" | v1: out-of-scope → không gọi tool; v2: `send` "KHÔNG BAO GIỜ dùng để trả lời" |
| R14_out_of_scope_coding | v0 | out_of_scope | `send(text="def fibonacci…")` | Như R08 với yêu cầu viết code | Như R08 |
| R03_web_news_routing | v0 | wrong_tool (observed: wrong_arg_value) | `lookup(query="AI news", topic="news", timeframe="day")` | Đúng tool nhưng `query` thêm chữ "news" (eval mong `"AI"`) | v2: mô tả `lookup.query` "chỉ chủ đề cốt lõi, không thêm news/hôm nay" |
| R13_parallel_web_and_tweets | v0 | wrong_tool (observed: wrong_arg_value) | `lookup(query="AI news", timeframe="day")` + `social_search(query="AI")` | Thiếu `topic="news"`, query sai | v1: cho phép nhiều tool; v2: convention `topic`/`query` |
| R11_missing_url | v1 | missing_info (observed: wrong_arg_value) | `clarify(question="…URL…")` | Đúng tool nhưng thiếu `response_type` (eval mong `"text"`) | v2: `response_type` vào `required` + mô tả khi nào text / yes_no |
| R01_user_tweets_routing | v2 | wrong_tool (observed: extra/missing tool) | `clarify("Bạn muốn xem tweet mới nhất của Sam Altman?")` | **Regression**: đã có tên nhưng vẫn hỏi lại — do mô tả `clarify` v2 quá mạnh | v3: routing rule "tên người đã biết KHÔNG phải thiếu info, tự map → `sama`" |
| M06_switch_tool | v2 | wrong_tool (observed: extra_tool_call) | `lookup(OpenAI, news)` + `social_search(OpenAI)` | **Regression**: user đã nói "Bỏ Twitter" nhưng model vẫn gọi `social_search` | v3: rule multi-turn "chỉ theo intent hiện tại, DROP phần user đã huỷ" |

Phân loại nguyên nhân v0 (7 case fail): 5/7 do **prompt** (chỉ dẫn xấu cố ý), 2/7 do **convention args** chưa có trong tool declaration.

## B3. Team Eval Cases

List the 10 cases added to `data/eval_group.json` (5 single turn + 5 multi turn).

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
|  |  |  |  |

## B4. Live Chat Evidence

Use `transcripts/*.transcript.json`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
|  |  |  |  |  |

## B5. Bonus Evidence

Only fill if your team did bonus.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) |  |  |  |
| arXiv/company policy |  |  |  |
| UI |  |  |  |
| Tool unit tests (`tests/`) | `pytest` output; `tests/test_tools_todo.py` | Điền 9 stub: clarify (choice + options), format (sections gom nhóm, thread đánh số, items rỗng ở cả 5 template), send (confirmed → đúng 1 POST với token/chat_id/text; thiếu env → error dict, không gọi mạng), policy (query rỗng/stopword, lọc `policy_area`, dòng injection vào `untrusted_text` chứ không vào `facts`) | Mọi test offline: `conftest.py` chặn HTTP thật, xoá env key trước mỗi test |

Tool unit tests: số test đã viết, số bug tìm được trong tool có sẵn (nếu có), và một ví dụ lỗi mà unit test bắt được nhưng eval không bắt được.

## B6. Reflection

**Which fixes belonged in `system_prompt.md`?**
Các quy tắc **hành vi và ranh giới** áp dụng chung cho mọi tool: không đoán / không bịa (R10, R11), xác nhận trước hành động có side effect (R12), từ chối out-of-scope (R08, R14), được gọi nhiều tool song song (R13), và cách xử lý hội thoại nhiều lượt: giữ lại chi tiết cũ, áp dụng lời sửa, bỏ phần đã huỷ (M06). Routing giữa các tool gần nghĩa (timeline vs social_search, lookup vs fetch) cũng hiệu quả hơn khi đặt trong prompt (v3 sửa R01).

**Which fixes belonged in `tools.yaml`?**
Những gì gắn với **một tool cụ thể**: convention của args (handle không `@`, `query` gọn không thêm "news", `topic=news`, bảng quy đổi `timeframe`, `search_type=Top` cho "nổi bật"), args bắt buộc (`clarify.response_type`), và guardrail riêng của `send` (`confirmed=true`). Bằng chứng: R11 chỉ sửa được khi thêm `response_type` vào `required` ở v2, không sửa được bằng prompt ở v1.

**Which failure needed manual review instead of automatic grading?**
- R03/R13 ở v0: model gọi `lookup(query="AI news")` là hành vi hợp lý, kết quả search gần như giống `query="AI"`, nhưng eval so sánh chuỗi chính xác nên chấm FAIL. Cần người xem để phân biệt "sai thật" và "khác cách viết".
- R01 ở v2: `clarify` với câu hỏi xác nhận lại không gây hại nhưng làm phiền user. Lỗi UX kiểu này chỉ đánh giá được bằng mắt.
- Nội dung câu trả lời cuối (tóm tắt có đúng nguồn không, có bịa không) hoàn toàn không được eval chấm, vì eval chỉ chấm tool call. Cần đọc transcript `chat.py`.
- Đúng tool và đúng args vẫn có thể cho kết quả sai nếu code của tool lỗi. Đó là lý do cần unit test (B5).

**What would you improve next?**
- Chạy mỗi version 2–3 lần để đo độ dao động. Ở temperature 0, `gpt-4o-mini` vẫn không hoàn toàn deterministic, nên R03 PASS ở v1 có thể là may.
- Viết thêm eval case cho 4 tool mới và các ranh giới khó (ví dụ "repo langchain" thiếu owner → clarify; "hôm nay thứ mấy" → `datetime_now` chứ không phải `lookup`).
- Eval chấm args mềm hơn (so khớp keyword thay vì chuỗi chính xác) để giảm false fail.
- Thử prompt ngắn hơn cho model local (B7).

## B7. Small Local Model Challenge (bonus)

Only fill if your team did the local model challenge.

| Version | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
|---|---|---|---|---|---|---|---|
| v3 | (cloud) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v4-local |  |  |  |  |  |  |  |
| v5-local |  |  |  |  |  |  |  |

Lỗi đặc thù của model nhỏ (đếm từ run JSON):

| Failure Pattern | Count | Example Case | Fix Tried | Helped? |
|---|---|---|---|---|
| wrong / hallucinated tool |  |  |  |  |
| invalid JSON args (`_invalid_json_arguments`) |  |  |  |  |
| no tool call / answered directly |  |  |  |  |
| missed `clarify` |  |  |  |  |
| repeated / unnecessary calls |  |  |  |  |

- Cái gì giúp model nhỏ gọi tool đúng hơn nhất? Bằng chứng?
- Bản prompt tối ưu cho local chạy trên model cloud thì sao?
- Khi nào nhóm sẽ chọn model local thay vì cloud cho agent này?
