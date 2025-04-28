variable "network_id" {
  description = "The Meraki Network ID where SSIDs are configured"
  type        = string
}

variable "ssids" {
  description = "List of SSID configurations"
  type = list(object({
    number             = number
    name               = string
    enabled            = bool
    auth_mode          = string
    psk                = optional(string)
    ip_assignment_mode = string
    default_vlan_id    = optional(number)
    radius_servers     = optional(list(object({
      host   = string
      port   = number
      secret = string
    })))
  }))
}
