variable "api_key" {
  description = "API key for Meraki"
  type        = string
  sensitive   = true
}

variable "network_id" {
  description = "The network ID to assign VLANs to"
  type        = string
}

variable "network_name" {
  type        = string
  description = ""
}