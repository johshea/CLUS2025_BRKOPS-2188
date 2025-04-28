variable "network_id" {
  description = "Network ID for traffic shaping"
  type        = string
}

variable "default_client_bw_up" {
  description = "Default client upload bandwidth limit (Kbps)"
  type        = number
  default     = 0
}

variable "default_client_bw_down" {
  description = "Default client download bandwidth limit (Kbps)"
  type        = number
  default     = 0
}

variable "default_rules_enabled" {
  description = "Use Meraki's default shaping rules"
  type        = bool
  default     = true
}

variable "shaping_rules" {
  description = "Custom traffic shaping rules"
  type = list(object({
    definitions = list(object({
      type  = string
      value = string
    }))
    per_client_bandwidth_limits = object({
      limit_up   = number
      limit_down = number
    })
    dscp_tag_value = optional(number)
    priority       = optional(string)
  }))
  default = []
}
