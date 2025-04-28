variable "network_id" {
  description = "Meraki Network ID for MX firewall rules"
  type        = string
}

variable "firewall_rules" {
  description = "List of firewall rule objects"
  type = list(object({
    comment        = string
    policy         = string
    protocol       = string
    src_cidr       = string
    src_port       = string
    dest_cidr      = string
    dest_port      = string
    syslog_enabled = bool
  }))
}

variable "syslog_default_rule" {
  description = "Log default rule to syslog"
  type        = bool
  default     = false
}
