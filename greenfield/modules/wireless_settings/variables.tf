variable "network_id" {
  description = "Network ID for wireless settings"
  type        = string
}

variable "meshing_enabled" {
  description = "Enable wireless meshing"
  type        = bool
  default     = false
}

variable "ipv6_bridge_enabled" {
  description = "Enable IPv6 bridging"
  type        = bool
  default     = false
}

variable "location_analytics_enabled" {
  description = "Enable location analytics"
  type        = bool
  default     = false
}

variable "led_lights_on" {
  description = "LED lights enabled"
  type        = bool
  default     = true
}

variable "upgrade_strategy" {
  description = "AP upgrade strategy"
  type        = string
  default     = "minimizeUpgradeTime"
}
