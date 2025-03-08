package service

import (
	"context"
	"fmt"
	"math"

	"transaction-service/internal/domain"
)

// TransactionValidator thực hiện kiểm tra tính hợp lệ của giao dịch
type TransactionValidator struct {
	txLimits      domain.TransactionLimits
	merchantRules domain.MerchantRules
	locationRules domain.LocationRules
	deviceRules   domain.DeviceRules
}

// NewTransactionValidator tạo một validator mới với các rules mặc định
func NewTransactionValidator() *TransactionValidator {
	return &TransactionValidator{
		txLimits:      domain.DefaultTransactionLimits,
		merchantRules: domain.DefaultMerchantRules,
		locationRules: domain.DefaultLocationRules,
		deviceRules:   domain.DefaultDeviceRules,
	}
}

// ValidateTransaction thực hiện tất cả các validation rules
func (v *TransactionValidator) ValidateTransaction(ctx context.Context, tx *domain.Transaction) (*domain.ValidationResult, error) {
	result := &domain.ValidationResult{
		IsValid:   true,
		RiskScore: 0,
		Metadata:  make(map[string]interface{}),
	}

	// Validate amount và currency
	if err := v.validateAmountAndCurrency(tx, result); err != nil {
		return result, err
	}

	// Validate merchant
	if err := v.validateMerchant(tx, result); err != nil {
		return result, err
	}

	// Validate location
	if err := v.validateLocation(tx, result); err != nil {
		return result, err
	}

	// Validate device
	if err := v.validateDevice(tx, result); err != nil {
		return result, err
	}

	// Tính toán final risk score
	result.RiskScore = v.calculateFinalRiskScore(tx, result)
	if result.RiskScore >= domain.HighRiskThreshold {
		result.IsValid = false
		result.Errors = append(result.Errors, domain.ValidationError{
			Field:   "risk_score",
			Code:    domain.ErrCodeHighRisk,
			Message: "Transaction risk score is too high",
			Details: fmt.Sprintf("Risk score %.2f exceeds threshold %.2f", result.RiskScore, domain.HighRiskThreshold),
		})
	}

	return result, nil
}

// validateAmountAndCurrency kiểm tra giới hạn số tiền và loại tiền tệ
func (v *TransactionValidator) validateAmountAndCurrency(tx *domain.Transaction, result *domain.ValidationResult) error {
	// Kiểm tra currency
	if tx.Currency != v.txLimits.Currency {
		result.IsValid = false
		result.Errors = append(result.Errors, domain.ValidationError{
			Field:   "currency",
			Code:    domain.ErrCodeInvalidCurrency,
			Message: "Invalid currency",
			Details: fmt.Sprintf("Currency %s is not supported. Expected %s", tx.Currency, v.txLimits.Currency),
		})
	}

	// Kiểm tra amount limit
	if tx.Amount > v.txLimits.MaxAmount {
		result.IsValid = false
		result.Errors = append(result.Errors, domain.ValidationError{
			Field:   "amount",
			Code:    domain.ErrCodeAmountLimit,
			Message: "Transaction amount exceeds limit",
			Details: fmt.Sprintf("Amount %.2f exceeds maximum %.2f", tx.Amount, v.txLimits.MaxAmount),
		})
	}

	// TODO: Kiểm tra daily limit
	// TODO: Kiểm tra monthly limit

	return nil
}

// validateMerchant kiểm tra các quy tắc về merchant
func (v *TransactionValidator) validateMerchant(tx *domain.Transaction, result *domain.ValidationResult) error {
	if tx.MerchantID == "" {
		result.Metadata["merchant_risk_score"] = 0.8 // High risk for unknown merchant
		result.RiskScore += 0.8 * 0.25 // Merchant score có trọng số 25%
		return nil
	}

	// Kiểm tra blocked categories
	merchantCategory := ""
	if tx.Metadata != nil {
		if cat, ok := tx.Metadata["merchant_category"].(string); ok {
			merchantCategory = cat
		}
	}

	for _, blocked := range v.merchantRules.BlockedCategories {
		if merchantCategory == blocked {
			result.IsValid = false
			result.Errors = append(result.Errors, domain.ValidationError{
				Field:   "merchant_category",
				Code:    domain.ErrCodeBlockedMerchant,
				Message: "Merchant category is blocked",
				Details: fmt.Sprintf("Category %s is not allowed", merchantCategory),
			})
			break
		}
	}

	// Tính merchant risk score
	if score, ok := v.merchantRules.RiskScores[merchantCategory]; ok {
		result.Metadata["merchant_risk_score"] = score
		result.RiskScore += score * 0.25 // Merchant score có trọng số 25%
	} else {
		result.Metadata["merchant_risk_score"] = 0.8 // High risk for unknown category
		result.RiskScore += 0.8 * 0.25
	}

	return nil
}

// validateLocation kiểm tra các quy tắc về location
func (v *TransactionValidator) validateLocation(tx *domain.Transaction, result *domain.ValidationResult) error {
	if tx.Location == nil {
		result.Metadata["location_risk_score"] = 0.8 // High risk for unknown location
		result.RiskScore += 0.8 * 0.25 // Location score có trọng số 25%
		return nil
	}

	// Kiểm tra blocked countries
	for _, blocked := range v.locationRules.BlockedCountries {
		if tx.Location.Country == blocked {
			result.IsValid = false
			result.Errors = append(result.Errors, domain.ValidationError{
				Field:   "location.country",
				Code:    domain.ErrCodeBlockedLocation,
				Message: "Country is blocked",
				Details: fmt.Sprintf("Transactions from %s are not allowed", tx.Location.Country),
			})
			break
		}
	}

	// TODO: Implement velocity check
	// Cần thêm thông tin về giao dịch trước đó để tính toán velocity

	// Tính location risk score
	if score, ok := v.locationRules.RiskScores[tx.Location.Country]; ok {
		result.Metadata["location_risk_score"] = score
		result.RiskScore += score * 0.25 // Location score có trọng số 25%
	} else {
		result.Metadata["location_risk_score"] = 0.8 // High risk for unknown country
		result.RiskScore += 0.8 * 0.25
	}

	return nil
}

// validateDevice kiểm tra các quy tắc về thiết bị
func (v *TransactionValidator) validateDevice(tx *domain.Transaction, result *domain.ValidationResult) error {
	if tx.DeviceInfo == nil {
		result.Metadata["device_risk_score"] = 0.8 // High risk for unknown device
		result.RiskScore += 0.8 * 0.25 // Device score có trọng số 25%
		return nil
	}

	// Kiểm tra blocked browsers
	for _, blocked := range v.deviceRules.BlockedBrowsers {
		if tx.DeviceInfo.BrowserType == blocked {
			result.IsValid = false
			result.Errors = append(result.Errors, domain.ValidationError{
				Field:   "device_info.browser_type",
				Code:    domain.ErrCodeBlockedDevice,
				Message: "Browser is blocked",
				Details: fmt.Sprintf("Browser %s is not allowed", tx.DeviceInfo.BrowserType),
			})
			break
		}
	}

	// Kiểm tra blocked OS
	for _, blocked := range v.deviceRules.BlockedOS {
		if tx.DeviceInfo.DeviceOS == blocked {
			result.IsValid = false
			result.Errors = append(result.Errors, domain.ValidationError{
				Field:   "device_info.device_os",
				Code:    domain.ErrCodeBlockedDevice,
				Message: "Operating system is blocked",
				Details: fmt.Sprintf("OS %s is not allowed", tx.DeviceInfo.DeviceOS),
			})
			break
		}
	}

	// TODO: Implement device limit per day check
	// Cần thêm thông tin về số lượng thiết bị đã sử dụng trong ngày

	// Tính device risk score
	deviceType := "unknown"
	if tx.DeviceInfo.IsMobile {
		deviceType = "mobile"
	} else {
		deviceType = "desktop"
	}

	if score, ok := v.deviceRules.RiskScores[deviceType]; ok {
		result.Metadata["device_risk_score"] = score
		result.RiskScore += score * 0.25 // Device score có trọng số 25%
	} else {
		result.Metadata["device_risk_score"] = 0.8 // High risk for unknown device type
		result.RiskScore += 0.8 * 0.25
	}

	return nil
}

// calculateFinalRiskScore tính toán điểm rủi ro cuối cùng
func (v *TransactionValidator) calculateFinalRiskScore(tx *domain.Transaction, result *domain.ValidationResult) float64 {
	// Tính toán risk score dựa trên số tiền giao dịch
	amountRatio := tx.Amount / v.txLimits.MaxAmount
	amountRiskScore := math.Min(1.0, amountRatio) * 0.3 // Amount score có trọng số 30%
	result.Metadata["amount_risk_score"] = amountRiskScore

	// Tính toán risk score dựa trên thông tin thiếu
	missingInfoScore := 0.0
	if tx.MerchantID == "" {
		missingInfoScore += 0.3 // Merchant info missing
	}
	if tx.Location == nil {
		missingInfoScore += 0.3 // Location info missing
	}
	if tx.DeviceInfo == nil {
		missingInfoScore += 0.3 // Device info missing
	}
	result.Metadata["missing_info_score"] = missingInfoScore

	// Tính toán risk score dựa trên các thông tin không xác định
	unknownInfoScore := 0.0
	if tx.DeviceInfo != nil {
		if tx.DeviceInfo.DeviceType == "unknown" {
			unknownInfoScore += 0.2
		}
		if tx.DeviceInfo.DeviceOS == "unknown" {
			unknownInfoScore += 0.2
		}
	}
	result.Metadata["unknown_info_score"] = unknownInfoScore

	// Tổng hợp các risk score
	totalScore := result.RiskScore + amountRiskScore + (missingInfoScore * 0.3) + (unknownInfoScore * 0.2)
	return math.Min(1.0, totalScore)
} 