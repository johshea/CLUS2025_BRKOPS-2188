terraform {
  required_providers {
    meraki = {
      source = "cisco-open/meraki"
      version = "1.0.7-beta"
    }
  }
}

provider "meraki" {
  api_key = var.meraki_api_key
}