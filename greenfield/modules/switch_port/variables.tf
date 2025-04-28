variable "ports" {
  description = "Switch port configurations"
  type = list(object({
    device_serial     = string
    port_id           = number
    name              = optional(string)
    tags              = optional(list(string))
    enabled           = optional(bool)
    type              = optional(string)
    vlan              = optional(number)
    voice_vlan        = optional(number)
    allowed_vlans     = optional(string)
    poe_enabled       = optional(bool)
    isolation_enabled = optional(bool)
    rstp_enabled      = optional(bool)
    stp_guard         = optional(string)
  }))
}
