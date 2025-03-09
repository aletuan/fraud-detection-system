# Implementation Plan

## Rules

### Location Rule

The location rule will detect fraudulent transactions based on the transaction location and associated risks.

#### Configuration
- Blocked countries: NK (North Korea), IR (Iran), CU (Cuba)
- Risk scores by country:
  - Low risk (0.1-0.2): US, GB, DE, FR
  - Medium risk (0.3-0.5): Standard countries
  - High risk (0.6-0.7): CN, RU
  - Very high risk (0.8+): Unknown countries
- Weight: 25% in risk calculation
- Default risk score: 0.8 for unknown locations

#### Risk Score Calculation
- Use country-based risk score
- Mark as fraudulent if:
  - Country is blocked
  - Risk score >= 0.7 (high risk threshold)
- Future: Add velocity check between consecutive transactions

### Merchant Rule

The merchant rule will detect fraudulent transactions based on merchant category and location.

#### Configuration
- Blocked categories: gambling, adult, weapons
- Risk scores by category:
  - Low risk (0.1): retail
  - Medium risk (0.3-0.4): travel, electronics
  - High risk (0.6+): gaming
  - Very high risk (0.8): unknown categories
- Country risk scores: Same as location rule
- Weight: 25% in risk calculation
- Default risk score: 0.8 for unknown merchants

#### Risk Score Calculation
- Combined score = (category_risk * 0.7) + (country_risk * 0.3)
- Mark as fraudulent if:
  - Category is blocked
  - Combined risk score >= 0.6 (high risk threshold)

### Device Rule

The device rule will detect fraudulent transactions based on device characteristics.

#### Configuration
- Device type risk scores:
  - Desktop: 0.1 (low risk)
  - Mobile: 0.3 (medium risk)
  - Unknown: 0.8 (high risk)
- Blocked browsers and OS
- Weight: 25% in risk calculation
- Default risk score: 0.8 for unknown devices

#### Risk Score Calculation
- Use device type risk score
- Mark as fraudulent if:
  - Browser is blocked
  - OS is blocked
  - Risk score >= 0.8 (high risk threshold)

### Amount Rule

The amount rule will detect fraudulent transactions based on transaction amount.

#### Configuration
- Currency: USD
- Amount limits:
  - Max single transaction: $10,000
  - Max daily total: $50,000
  - Max monthly total: $100,000
- Weight: 25% in risk calculation

#### Risk Score Calculation
- Calculate amount ratio = amount / max_amount
- Risk levels:
  - Low: < $1,000 (0.2)
  - Medium: $1,000 - $5,000 (0.4)
  - High: $5,000 - $10,000 (0.6)
  - Very high: > $10,000 (0.8)

### Velocity Rule

The velocity rule will detect fraudulent transactions based on transaction velocity (frequency and amount) within specified time windows.

#### Configuration
- Time windows: 5 minutes and 1 hour
- Transaction count limits:
  - Max 3 transactions in 5 minutes
  - Max 10 transactions in 1 hour
- Amount limits:
  - Max $5000 in 5 minutes
  - Max $20000 in 1 hour
- Weight: 20% in risk calculation
- Default risk score for fraudulent transactions: 0.8

#### Risk Score Calculation
1. For first transaction:
   - Risk score = 0.0
   - Reason = "Low velocity risk"

2. For subsequent transactions:
   - Calculate count ratio = transactions_in_window / max_transactions
   - Calculate amount ratio = amount_in_window / max_amount
   - Risk score = max(count_ratio, amount_ratio) * weight

3. Risk levels:
   - Very high: >= 0.15 (75% * 0.2)
   - High: >= 0.10 (50% * 0.2)
   - Medium: >= 0.06 (30% * 0.2)
   - Low: < 0.06

#### Implementation Details
1. Transaction History:
   - Keep track of transactions within the maximum time window
   - Clean old transactions when evaluating new ones

2. Evaluation Process:
   - Check transaction count limits for each time window
   - Check amount limits for each time window
   - Mark as fraudulent if any limit is exceeded
   - Calculate risk score based on shortest time window

3. Custom Rules Support:
   - Allow custom time windows
   - Allow custom transaction count limits
   - Allow custom amount limits
   - Allow custom weight and default risk score

## Overall Risk Score

The final risk score is calculated by combining all rule scores:
1. Base score = sum of weighted rule scores
2. Additional factors:
   - Missing information penalty: +0.3 per missing field
   - Unknown information penalty: +0.2 per unknown field
3. Final score = min(1.0, base_score + penalties)

Mark transaction as fraudulent if:
- Any rule marks it as fraudulent
- Final risk score >= 0.8 