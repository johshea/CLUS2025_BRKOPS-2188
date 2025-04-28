variable "api_key" {
  description = "API key for Meraki"
  type        = string
  sensitive   = true
}

variable "org_id" {
  description = "Meraki Organization ID"
  type        = string
}
