# Risk Score Calculation

Tài liệu này mô tả cách tính điểm rủi ro (risk score) trong hệ thống phát hiện gian lận.

## Tổng quan

Mỗi rule trong hệ thống sẽ đánh giá một khía cạnh cụ thể của giao dịch và trả về một điểm rủi ro từ 0.0 đến 1.0:
- 0.0: Rủi ro thấp nhất
- 1.0: Rủi ro cao nhất

## Trọng số của các Rule

Mỗi rule có một trọng số (weight) riêng trong việc tính toán điểm rủi ro tổng thể:

- Amount Rule: 30% (0.3)
- Location Rule: 25% (0.25)
- Merchant Rule: 25% (0.25)
- Device Rule: 20% (0.2)

## Cách tính Risk Score

### 1. Amount Rule
- Risk score = amount / max_amount (được giới hạn ở 1.0)
- Ví dụ: Giao dịch 4000 USD với max_amount = 10000 USD
  - Risk score = 4000/10000 = 0.4
  - Final score = 0.4 * 0.3 = 0.12

### 2. Location Rule
- Risk score dựa trên bảng điểm rủi ro của từng quốc gia
- Ví dụ: Giao dịch từ Nga (RU)
  - Risk score = 0.7 (high risk)
  - Final score = 0.7 * 0.25 = 0.175

### 3. Merchant Rule
- Kết hợp điểm rủi ro của category và country:
  - 70% từ category risk
  - 30% từ country risk
- Ví dụ: Merchant category "gaming" (0.6) ở Nga (0.7)
  - Risk score = (0.6 * 0.7) + (0.7 * 0.3) = 0.63
  - Final score = 0.63 * 0.25 = 0.1575

### 4. Device Rule
- Risk score dựa trên loại thiết bị và browser
- Ví dụ: Mobile device
  - Risk score = 0.2 (low-medium risk)
  - Final score = 0.2 * 0.2 = 0.04

## Ngưỡng Rủi ro

Mỗi rule có ngưỡng rủi ro riêng để xác định giao dịch có đáng ngờ hay không:

- Amount Rule: > 1.0 (vượt quá max_amount)
- Location Rule: >= 0.7 (high risk countries)
- Merchant Rule: >= 0.6 (high risk merchants)
- Device Rule: >= 0.8 (suspicious devices)

## Các trường hợp đặc biệt

1. **Blocked Entities**
   - Nếu một thực thể bị chặn (country, merchant category, device), risk score sẽ là 1.0
   - Giao dịch sẽ bị đánh dấu là gian lận

2. **Missing Information**
   - Nếu thiếu thông tin, sử dụng default_risk_score (thường là 0.8)
   - Điều này khuyến khích việc cung cấp đầy đủ thông tin

3. **Invalid Data**
   - Ví dụ: currency không hợp lệ
   - Risk score = 1.0 và giao dịch bị đánh dấu là gian lận

## Ví dụ Tính toán Tổng thể

Một giao dịch có thể được đánh giá như sau:

```
Amount: 4000 USD (score: 0.4 * 0.3 = 0.12)
Location: RU (score: 0.7 * 0.25 = 0.175)
Merchant: Gaming in RU (score: 0.63 * 0.25 = 0.1575)
Device: Mobile (score: 0.2 * 0.2 = 0.04)

Final Risk Score = 0.12 + 0.175 + 0.1575 + 0.04 = 0.4925
```

Trong ví dụ này, mặc dù có một số yếu tố rủi ro cao (location và merchant), nhưng tổng thể giao dịch vẫn ở mức rủi ro trung bình do các yếu tố khác có rủi ro thấp hơn. 