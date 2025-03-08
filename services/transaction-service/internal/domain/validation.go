package domain

// TransactionLimits định nghĩa các giới hạn cho giao dịch
type TransactionLimits struct {
	MaxAmount      float64 // Số tiền tối đa cho một giao dịch
	DailyLimit     float64 // Giới hạn giao dịch trong ngày
	MonthlyLimit   float64 // Giới hạn giao dịch trong tháng
	Currency       string  // Loại tiền tệ áp dụng
	AllowedTime    TimeWindow
	AllowedDevices []string // Danh sách thiết bị được phép
}

// TimeWindow định nghĩa khung thời gian cho phép giao dịch
type TimeWindow struct {
	StartHour int // Giờ bắt đầu (0-23)
	EndHour   int // Giờ kết thúc (0-23)
	Timezone  string
}

// MerchantRules định nghĩa các quy tắc cho merchant
type MerchantRules struct {
	AllowedCategories []string          // Danh sách category được phép
	BlockedCategories []string          // Danh sách category bị chặn
	RiskScores       map[string]float64 // Risk score cho từng category
	CountryRisks     map[string]float64 // Risk score cho từng quốc gia
}

// LocationRules định nghĩa các quy tắc cho location
type LocationRules struct {
	BlockedCountries []string          // Danh sách quốc gia bị chặn
	RiskScores      map[string]float64 // Risk score cho từng quốc gia
	VelocityLimit   float64            // Giới hạn khoảng cách di chuyển (km/h)
}

// DeviceRules định nghĩa các quy tắc cho thiết bị
type DeviceRules struct {
	BlockedDevices    []string          // Danh sách thiết bị bị chặn
	BlockedBrowsers   []string          // Danh sách browser bị chặn
	BlockedOS         []string          // Danh sách OS bị chặn
	RiskScores       map[string]float64 // Risk score cho từng loại thiết bị
	RequireMFA       bool              // Yêu cầu xác thực 2 lớp
	MaxDevicesPerDay int               // Số thiết bị tối đa trong ngày
}

// ValidationError định nghĩa chi tiết lỗi validation
type ValidationError struct {
	Field   string // Trường dữ liệu có lỗi
	Code    string // Mã lỗi
	Message string // Thông báo lỗi
	Details string // Chi tiết thêm về lỗi
}

// ValidationResult chứa kết quả validation
type ValidationResult struct {
	IsValid  bool              // Kết quả validation
	Errors   []ValidationError // Danh sách lỗi
	RiskScore float64          // Điểm đánh giá rủi ro
	Metadata  map[string]interface{} // Thông tin bổ sung
}

// Validation error codes
const (
	ErrCodeAmountLimit       = "AMOUNT_LIMIT_EXCEEDED"
	ErrCodeDailyLimit       = "DAILY_LIMIT_EXCEEDED"
	ErrCodeMonthlyLimit     = "MONTHLY_LIMIT_EXCEEDED"
	ErrCodeInvalidCurrency  = "INVALID_CURRENCY"
	ErrCodeInvalidTime      = "INVALID_TIME"
	ErrCodeBlockedMerchant  = "BLOCKED_MERCHANT"
	ErrCodeBlockedLocation  = "BLOCKED_LOCATION"
	ErrCodeVelocityLimit    = "VELOCITY_LIMIT_EXCEEDED"
	ErrCodeBlockedDevice    = "BLOCKED_DEVICE"
	ErrCodeDeviceLimit      = "DEVICE_LIMIT_EXCEEDED"
	ErrCodeHighRisk         = "HIGH_RISK_TRANSACTION"
)

// Risk score thresholds
const (
	LowRiskThreshold    = 0.3
	MediumRiskThreshold = 0.6
	HighRiskThreshold   = 0.8
)

// Default validation rules
var (
	DefaultTransactionLimits = TransactionLimits{
		MaxAmount:    10000.0,
		DailyLimit:   50000.0,
		MonthlyLimit: 200000.0,
		Currency:     "USD",
		AllowedTime: TimeWindow{
			StartHour: 0,
			EndHour:   23,
			Timezone:  "UTC",
		},
	}

	DefaultMerchantRules = MerchantRules{
		BlockedCategories: []string{
			"gambling",
			"adult",
			"weapons",
		},
		RiskScores: map[string]float64{
			"retail":      0.1,
			"travel":      0.3,
			"electronics": 0.4,
			"gaming":      0.6,
		},
	}

	DefaultLocationRules = LocationRules{
		BlockedCountries: []string{
			"NK", // North Korea
			"IR", // Iran
			"CU", // Cuba
		},
		RiskScores: map[string]float64{
			"US": 0.1,  // USA - Low risk
			"GB": 0.1,  // UK - Low risk
			"RU": 0.7,  // Russia - High risk
			"CN": 0.6,  // China - Medium-high risk
		},
		VelocityLimit: 800.0, // km/h
	}

	DefaultDeviceRules = DeviceRules{
		RequireMFA:       true,
		MaxDevicesPerDay: 3,
		BlockedBrowsers: []string{
			"unknown",
			"tor",
		},
		RiskScores: map[string]float64{
			"mobile":     0.2,
			"tablet":     0.3,
			"desktop":    0.1,
			"unknown":    0.9,
		},
	}
) 