variable "network_id" {
  description = "Network ID to configure VLANs"
  type        = string
}

variable "vlans" {
  description = "List of VLAN configurations"
  type = list(object({
    id           = number
    name         = string
    subnet       = string
    appliance_ip = string
  }))
}
