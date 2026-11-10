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

**Research agent** nhận yêu cầu bằng tiếng Việt hoặc tiếng Anh, tự chọn đúng tool trong 14 tool, rồi trả về kết quả có nguồn: tweet theo tài khoản hoặc chủ đề, tin tức web, nội dung một URL, paper arXiv, chính sách nội bộ, kiến thức Wikipedia, bài hot trên Hacker News, thông tin repo GitHub và giờ hiện tại. Agent có thể gộp kết quả thành bản tin (digest) và gửi lên Telegram, nhưng chỉ sau khi người dùng xác nhận.

**Điểm khác biệt (đã đo bằng eval thật, không phải cảm giác):**
- **Biết hỏi lại thay vì đoán.** Thiếu tài khoản hoặc URL thì agent dùng `clarify`, không bịa. Người dùng đã nói tên (ví dụ "Sam Altman") thì agent tự đổi sang handle `sama` và không hỏi lại.
- **Không tự ý gửi.** Muốn gửi Telegram, agent hỏi xác nhận (có/không) trước; `send` chỉ chạy khi `confirmed=true`.
- **Biết từ chối.** Yêu cầu ngoài phạm vi (giải toán, viết code) thì không gọi tool nào.
- **Hiểu hội thoại nhiều lượt.** Nếu người dùng đổi ý ("bỏ Twitter, chuyển sang web"), agent bỏ phần đã huỷ.
- **Tool được kiểm thử.** Tool chạy offline qua `pytest`, có kiểm tra input biên (rỗng, âm, sai kiểu) để không tốn API khi model gửi sai args.

**Kết quả trên base eval (20 case, `gpt-4o-mini`):** từ 65% (v0) lên **100% (v3, v4)** sau 3 vòng tối ưu prompt và tool declaration.

**Link dùng thử (deploy):**

**https://k5-l3a-day03-scp404-promptfunctioncalling-tooldesignmcp.streamlit.app/**

Deploy trên Streamlit Community Cloud từ nhánh `main`, main file `starter_v0/app.py`.
API key được cấu hình qua Streamlit Secrets, không nằm trong repository.
Chạy local: `streamlit run app.py` trong `starter_v0/`.

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | Hỏi lại người dùng khi thiếu thông tin, hoặc xin xác nhận (có/không) trước khi gửi | không |
| timeline | Lấy các bài đăng gần đây của **một tài khoản** X/Twitter | không |
| social_search | Tìm bài đăng X/Twitter **theo chủ đề/từ khoá** (mới nhất hoặc nổi bật) | không |
| lookup | Tìm kiếm web và tin tức, lọc theo khoảng thời gian (ngày/tuần/tháng/năm) | không |
| fetch | Đọc và lấy nội dung đầy đủ của **một URL** | không |
| format | Gộp các kết quả đã có thành bản tin markdown (brief, sections, bullets, thread…) | không |
| send | Gửi nội dung lên kênh Telegram, **chỉ sau khi người dùng xác nhận** | không |
| policy | Tra cứu chính sách nội bộ của công ty (quyền riêng tư, trích dẫn nguồn, đăng bài…) | không |
| papers | Tìm bài báo khoa học trên arXiv | không |
| paper_text | Tải PDF một paper arXiv và trích text để đọc/tóm tắt | không |
| **wikipedia** | Tóm tắt một bài Wikipedia (tiếng Anh hoặc tiếng Việt) | **có** |
| **hackernews** | Lấy bài top hoặc mới nhất trên Hacker News | **có** |
| **github_repo** | Thông tin một repo GitHub: sao, fork, issue, ngôn ngữ, license | **có** |
| **datetime_now** | Cho biết ngày giờ hiện tại ở một múi giờ | **có** |

Bốn tool mới đều dùng API miễn phí, không cần key.

## A3. Câu hỏi mẫu để thử

| # | Câu thử | Agent nên làm gì |
|---|---|---|
| 1 | "Giới thiệu về Alan Turing" | Gọi `wikipedia` |
| 2 | "Bây giờ là mấy giờ ở Tokyo?" | Gọi `datetime_now` với múi giờ Asia/Tokyo |
| 3 | "Repo psf/requests có bao nhiêu sao?" | Gọi `github_repo` |
| 4 | "Top 3 bài trên Hacker News hôm nay" | Gọi `hackernews` với `limit=3` |
| 5 | "Tóm tắt 5 tweet mới nhất" _(không nói của ai)_ | **Hỏi lại** bằng `clarify`, không tự đoán tài khoản |
| 6 | "Tweet mới nhất của Sam Altman" | Gọi `timeline` với handle `sama`, không hỏi lại |
| 7 | "Tin tức AI hôm nay và mọi người trên Twitter đang bàn gì về AI?" | Gọi `lookup` (news) và `social_search` cùng lúc |
| 8 | "Gửi bản tin này lên Telegram" | **Xin xác nhận** trước, chưa gửi ngay |
| 9 | "Giải giúp mình nguyên hàm của x^2" | **Từ chối**, không gọi tool (ngoài phạm vi) |

Mẹo thử khó: hỏi "Repo langchain có bao nhiêu sao?" (thiếu owner, agent nên hỏi lại), hoặc đổi ý giữa chừng ("Bỏ Twitter, chỉ tìm trên web thôi").

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Các số liệu dưới đây được lấy từ `artifacts/version_log.csv` và `runs/*.json`.

Mọi run đều trên `data/eval_base.json` (20 case: 14 single turn, 6 multi turn). Mỗi version chỉ đổi **một** artifact để kiểm chứng **một** giả thuyết; hash trong cột Artifact Version cho thấy file nào đổi.

| Version | Changed Artifact | Artifact Version | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---|---:|---:|---|
| v0 | baseline (starter) | `v0+peb1c8179815b+t5b22a2476d41` | — | — | case 0.65 · routing 0.75 · args 0.65 · multi 1.0 | `runs/v0_B_base_openai_20261110T101806863676.json` |
| v1 | `system_prompt.md` | `v1+p718eda401f27+t5b22a2476d41` | Prompt starter cố ý bảo "đoán thay vì hỏi", "gửi ngay", "chỉ 1 tool". Thay bằng rule an toàn (clarify khi thiếu info, xác nhận trước khi send, từ chối out-of-scope, cho phép nhiều tool) sẽ sửa R08/R10/R11/R12/R14 | 0.65 | case **0.95** · routing 1.0 · args 0.95 · multi 1.0 | `runs/v1_B_base_openai_20261110T101915429959.json` |
| v2 | `tools.yaml` | `v2+p718eda401f27+t58b949f3cad1` | Description tool mơ hồ làm model bỏ sót args (R11 thiếu `response_type`). Viết lại description (làm gì / khi nào dùng / khi nào không) + convention args + `response_type` bắt buộc | 0.95 | case **0.90** ⬇ · routing 0.9 · args 0.9 · multi 0.83 | `runs/v2_B_base_openai_20261110T110749592420.json` |
| v3 | `system_prompt.md` | `v3+p3c4f06917491+t58b949f3cad1` | v2 gây regression: R01 hỏi lại thừa, M06 gọi lại tool user đã huỷ. Thêm routing rules ("tên người đã biết → tự map handle, không hỏi lại") + rule multi-turn "chỉ theo intent hiện tại, bỏ phần đã huỷ" | 0.90 | case **1.0** · routing 1.0 · args 1.0 · multi 1.0 | `runs/v3_B_base_openai_20261110T111803928857.json` |
| v4 | `tools.yaml` (+4 tool mới: `wikipedia`, `hackernews`, `github_repo`, `datetime_now`) | `v4+p3c4f06917491+t92f0376be02d` | Tăng từ 10 lên 14 tool có thể làm nhiễu routing; nếu description tool mới nói rõ khi nào dùng/không dùng thì base không bị regression | 1.0 | case **1.0** · routing 1.0 · args 1.0 · multi 1.0 | `runs/v4_B_base_openai_20261110T115937405999.json` |
| v5 | `system_prompt.md`, `tools.yaml`, `eval_group.json` | `v5+pa483b9698876+te34a8319a8a0` | G02 cần truyền rõ `kind=top`; G10 cần source items trong context trước khi gọi `format` | 0.80 | case **0.90** · routing 0.90 · args 0.90 · multi 1.0 | `runs/v5_B_group_openai_20261110T142404965024.json` |
| v6 | `system_prompt.md` | `v6+pc48c9591a114+te34a8319a8a0` | Không lặp lại cùng tool với cùng args trong một request, sửa duplicate `github_repo` ở G03 | 0.90 | case **1.0** · routing 1.0 · args 1.0 · multi 1.0 | `runs/v6_B_group_openai_20261110T142456849983.json` |

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

Nhóm đã thêm 10 case vào `data/eval_group.json` (5 single turn + 5 multi turn).

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01–G05 | tool mới và clarify khi thiếu owner | wikipedia, hackernews, github_repo, datetime_now, clarify | v6: 5/5 PASS |
| G06–G10 | chuyển intent, xác nhận send, format multi-turn | wikipedia, github_repo, send/no_tool, format | v6: 5/5 PASS |

Group eval v3 ban đầu đạt 8/10: G02 thiếu `kind="top"` và G10 chưa có
source items trong context. v5 đạt 9/10; v6 thêm chống duplicate tool call
và đạt **10/10**, mọi metric đều 1.0.

## B4. Live Chat Evidence

Use `transcripts/*.transcript.json`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| v4 turn 1–4 | Alan Turing; giờ Tokyo; repo `psf/requests`; top 3 Hacker News | `wikipedia`, `datetime_now`, `github_repo`, `hackernews` | `v4_openai_20261110T114813855626.transcript.json` | 4 lượt hoàn tất, có tool results và câu trả lời có nguồn |
| v6 turn 1–9 | Điện thoại thông minh đầu tiên; giá vàng; đọc URL; repo GitHub; thiếu URL rồi bổ sung | `wikipedia`, `lookup`, `fetch`, `github_repo`, `clarify`, `fetch` | `v6_openai_20261110T145643174517.transcript.json` | Multi-turn thiếu thông tin hoạt động: hỏi URL ở turn 8, nhận URL và fetch ở turn 9 |
| v6 turn 1–6 | Chat UI mới: câu hỏi thường, kiến thức, và đọc URL | `fetch` ở turn 6; các lượt khác trả lời trực tiếp | `v6_openai_20261110T150755414747.transcript.json` | 6 lượt được lưu thành transcript riêng |
| v6 turn 7 | Yêu cầu gửi nội dung trang GitHub lên Telegram | `clarify(response_type="yes_no")` → `send(confirmed=true)` | `v6_openai_20261110T150755414747.transcript.json` | Agent hỏi xác nhận trước; chỉ gọi `send` sau khi người dùng đồng ý |

Ghi chú: transcript ghi nhận `send` với `confirmed=true`. Sau đó đã kiểm tra tích hợp
Telegram thật bằng bot/channel test và xác nhận tin nhắn được gửi thành công. Token và
chat ID không được ghi vào report, transcript hoặc repository.

## B5. Bonus Evidence

Các bonus đã làm và bằng chứng tương ứng:

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | `tests/test_tools_todo.py`, `transcripts/v6_openai_20261110T150755414747.transcript.json`, kiểm tra bot/channel thật | Live chat hỏi `yes_no`, sau đó chỉ gọi `send` với `confirmed=true`; unit test kiểm tra POST; bot test gửi thành công tới channel | Không gửi nếu chưa xác nhận; giữ token/chat ID ngoài source control |
| arXiv/company policy | `tests/test_tools_todo.py` | policy có trust boundary; arXiv được đăng ký | Cần nguồn/network khi chạy live |
| UI | `app.py`, `poster.html`, `transcripts/v6_openai_20261110T150755414747.transcript.json` | Streamlit UI có lịch sử chat, nút tạo chat mới, lưu transcript sau mỗi lượt và hiển thị tool dưới tin nhắn | Đã deploy public tại https://k5-l3a-day03-scp404-promptfunctioncalling-tooldesignmcp.streamlit.app/; key để trong Streamlit Secrets; transcript trên cloud không lưu lâu dài (mất khi app restart) |
| Tool unit tests (`tests/`) | `tests/test_tools_todo.py`, `tests/test_tools_new.py`, `tests/test_tools_regression.py` | Test core stubs, 4 tool mới và 6 nhóm regression boundary | Mọi test offline; cần cài dependency từ `requirements.txt` |

Tool unit tests: toàn bộ suite hiện đạt `156 passed, 0 failed, 0 skipped`.
Regression suite đã ghi nhận 6 nhóm bug boundary; ví dụ B4 (input rỗng vẫn gọi API trả phí)
được unit test bắt nhưng eval routing không bắt được.

### Challenge+: bug tìm được bằng input biên (Sơn)

Cách làm: viết script gọi từng tool với input mà model hay gửi (`limit=0/-1/"abc"/999`, `max_results="5"`, query/URL rỗng, `@handle`, item `None`/chuỗi trong `items`), mock HTTP và ghi lại tool làm gì. Sau đó viết regression test trước (`tests/test_tools_regression.py`, 36 case, **30 case fail** trên code gốc), rồi mới sửa tool. Sau khi sửa, 36/36 pass.

| # | Tool | Input biên | Hành vi gốc (bug) | Hậu quả thực tế | Sửa |
|---|---|---|---|---|---|
| B1 | timeline, social_search | `limit=-1` | `items[:-1]` bỏ item cuối, trả 7/8 item | User xin "5 tweet" nhưng nhận số lượng vô nghĩa; `limit=999` không có trần | `clamp_int`: <1 → mặc định 5, >20 → 20 |
| B2 | timeline, social_search | `limit="abc"` | `int()` raise **sau** khi đã gọi RapidAPI | Tốn 1 request có quota rồi mới trả lỗi | Chuẩn hoá `limit` trước khi gọi HTTP, giá trị lạ → mặc định |
| B3 | lookup | `max_results=0/-1/999` | Gửi nguyên `-1`/`999` lên Tavily (`0` bị `or 5` che) | Tavily trả 400 hoặc tốn credit | Chuẩn hoá về 1..20 |
| B4 | lookup, timeline, social_search, fetch | `query=""`, `screenname=""`, `url=""`, `"ftp://x"` | Vẫn gọi API trả phí | Tốn credit Tavily/Firecrawl/RapidAPI cho request vô nghĩa | Trả error dict `ValueError`, **không gọi HTTP** |
| B5 | timeline, social_search | `"@sama"`, `search_type="top"` | Gửi nguyên `@sama` và `top` (sai hoa/thường) | API không tìm thấy hoặc trả sai | Bỏ `@`; `search_type` chuẩn hoá về `Top`/`Latest` |
| B6 | format | `items=[None, "text"]`, `summary=123`, `section=None` | **Raise `AttributeError`** (không trả error dict); `section=None` in ra `## None`; item thiếu url thành `"- s - "` | Agent loop có thể crash giữa chừng; bản tin xấu | Bỏ item không phải dict, ép `summary` về chuỗi, bỏ dấu ` - ` thừa |

Không phải bug (đã kiểm tra): `max_results="5"` và `limit="3"` (chuỗi số) vẫn chạy đúng vì có `int()`; `policy top_k=0` cho 3 kết quả (mặc định) và `top_k=-1` cho 1 kết quả, chấp nhận được.

Ví dụ lỗi eval không bắt được: B4. Model gọi `fetch(url="")` hoặc `lookup(query="")` đúng tên tool nên eval chấm PASS, nhưng code vẫn gọi API trả phí với đầu vào rỗng. Chỉ unit test (assert `calls == []`) mới bắt được.

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

Local model challenge chưa chạy trong workspace này; không có Ollama/model local để
ghi run JSON hoặc metric đáng tin cậy.

| Version | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
|---|---|---|---|---|---|---|---|
| v3 | openai | v3 | v3 prompt/tools | 1.0 | 1.0 | 1.0 | `runs/v3_B_base_openai_20261110T111803928857.json` |
| v3-local-1 | chưa chạy | — | — | — | — | — | — |
| v3-local-2 | chưa chạy | — | — | — | — | — | — |
| v4-local | chưa chạy | — | — | — | — | — | — |
| v5-local | chưa chạy | — | — | — | — | — | — |

Lỗi đặc thù của model nhỏ (đếm từ run JSON):

| Failure Pattern | Count | Example Case | Fix Tried | Helped? |
|---|---|---|---|---|
| wrong / hallucinated tool | N/A | — | — | — |
| invalid JSON args (`_invalid_json_arguments`) | N/A | — | — | — |
| no tool call / answered directly | N/A | — | — | — |
| missed `clarify` | N/A | — | — | — |
| repeated / unnecessary calls | N/A | — | — | — |

- Cái gì giúp model nhỏ gọi tool đúng hơn nhất? Bằng chứng?
- Bản prompt tối ưu cho local chạy trên model cloud thì sao?
- Khi nào nhóm sẽ chọn model local thay vì cloud cho agent này?

Các câu hỏi B7 chưa có kết quả vì nhóm chưa chạy Ollama. Do đó chưa kết luận
prompt cloud có tương đương prompt local hay chưa; nếu cần chạy offline trong
tương lai, sẽ ưu tiên model local cho dữ liệu nhạy cảm hoặc khi cần giảm chi phí,
sau khi đo lại routing và argument accuracy trên cùng dataset.
